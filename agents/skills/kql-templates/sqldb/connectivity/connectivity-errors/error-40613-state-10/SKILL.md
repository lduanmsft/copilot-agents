---
name: error-40613-state-10
description: This error occurs when one or more gateway instances is redirecting login connections to a DB node where the SQL instance is unavailable or does not exist. The error means the XDBHost process on the node is unable to find the SQL instance requested by the client. 
---

## Potential causes
There are 5 potential causes for this error: 
1. SQL DB name has special characters, this usually happens if customer in europe region.
2. Instance is not available on the DB node.
3. Client application is sending out the incorrect format of connection string.
4. Some Gateways failed to receive notification from Service Fabric. This was seen between or after a network outage between GW and Service Fabric, latest notification would not be resent to the GW.
5. Old client (old version of .NET/ODBC/etc) might cache the redirection token and use that to connect to the old SQL instance.

Do not draw conclusions until finishing the troubleshooting steps.

## Troubleshooting Steps

### Step 1. Verify special characters of the logical server name and database name

1. Verify if there are special characters of the logical server name and database name.

Sample names with special characters:
"tandlægerneøstergaardpadehovmøller"
"RLB-NÖW-DEMO"

2. If special characters exist, customer DB may be impacted and login connection are being misrouted. Notify the user:

 In the SQLAlias database the lookup_name is encoded as UTF16. The gateway normalizes lookup_name in the login workflow when it is performing a lookup in the SQLAlias database by performing a lowercase conversion of the string using the system locale to do case-insensitive comparison. The C++ API uses only lowercase characters in the locale specified, so it does not need to lowercase characters encoded using different codepages. This differs from the cache_update path because ManagementService performs the lowercase conversion using a managed API that handles all locales, so all characters get lowercased for cache_update. This can result in missed updates, because the cache_update path would create a duplicate entry with the (properly lowercased) lookup_name. When customers attempt to connect, they will be misrouted to the old endpoint as a result.

Prompt user to access this TSG link: https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/gateway/alias-mismatch-tolower-issue

If there is no special character in the logical server name and database name, go to next step.


### Step 2. Verify error time range and targeted DB node.

Sample Kusto Query:
```
	let startTime = datetime(2026-01-21 15:20);
	let endTime = datetime(2026-01-21 16:59);
	let server = "atlas-gdc-perf-nonprod-6321af20";
	let db = "NDOF_TRIP_EXEC";
 MonLogin
	    | where originalEventTimestamp between ((startTime-5m)..(endTime+5m))
	    | where AppTypeName != "Gateway" and event == "process_login_finish"
	//   | where error ==40613 and state ==10
	    | where logical_server_name =~ server and database_name =~ db
| extend instance_id =
    iif(instance_name has @"\",
        tostring(split(instance_name, @"\")[array_length(split(instance_name, @"\")) - 1]),
        tostring(split(instance_name, ".")[0])
    )
| summarize min(TIMESTAMP), max(TIMESTAMP), 40613_10= countif( error ==40613 and state ==10) by DBNode=NodeName, instance_id
```

Note: 
1. The startTime and endTime and server and db are variables which can be input by user.
2. Sample Output:
===
DBNode	instance_id	min_TIMESTAMP	max_TIMESTAMP	40613_10
_DB_26	d0f3882c805f	2026-01-21 15:16:01.6309720	2026-01-21 16:03:42.1943189	1025
_DB_43	c8b163f85b46	2026-01-21 15:53:55.6534927	2026-01-21 17:00:22.7804042	0
===
In this output, the error is only happening on DBNode "_DB_26", and the instance_id is "d0f3882c805f". This means the gateway is redirecting the login connections to this DB node, but the SQL instance with id "d0f3882c805f" is not available on this node, which causes the error. 
Time range of the error is from "2026-01-21 15:55:12" to "2026-01-21 16:03:42", which is around 8 minutes. Only alert when time is over 10 minutes.
"_DB_43" is the new DB node after failover, there is no error on this node, which means the SQL instance with id "c8b163f85b46" is available and healthy on this node.


### Step 3. Verify if all gateways switched to the new DB node almost in the same time range.

Sample Kusto Query:
```
	let startTime = datetime(2026-01-21 15:20);
	let endTime = datetime(2026-01-21 16:59);
	let server = "atlas-gdc-perf-nonprod-6321af20";
	let db = "NDOF_TRIP_EXEC";
MonLogin
	    | where originalEventTimestamp between ((startTime-5m)..(endTime+5m))
	    | where AppTypeName =~ "Gateway" and event == "process_login_finish"
	    | where logical_server_name =~ server and database_name =~ db
	| summarize min(originalEventTimestamp),  max(originalEventTimestamp), TotalGWNodes = dcount(strcat(ClusterName, "_", NodeName)) by fabric_node_name, bin(originalEventTimestamp, 3m)
  ```
Note:
1. The startTime and endTime and server and db are variables which can be input by user.
2. Sample Output:
===
fabric_node_name	originalEventTimestamp	min_originalEventTimestamp	max_originalEventTimestamp	TotalGWNodes
DB00000Q\_DB_26	2026-01-21 15:42:00.0000000	2026-01-21 15:43:24.4609738	2026-01-21 15:44:00.8277016	18
DB00000Q\_DB_26	2026-01-21 15:48:00.0000000	2026-01-21 15:48:55.5837010	2026-01-21 15:50:17.2954222	18
DB00000Q\_DB_26	2026-01-21 15:51:00.0000000	2026-01-21 15:53:38.4928240	2026-01-21 15:53:44.2414983	24
DB000017\_DB_43	2026-01-21 15:51:00.0000000	2026-01-21 15:53:53.1990263	2026-01-21 15:53:58.2319535	9
DB000017\_DB_43	2026-01-21 15:54:00.0000000	2026-01-21 15:54:00.7607556	2026-01-21 15:56:50.1840788	48
DB000017\_DB_43	2026-01-21 15:57:00.0000000	2026-01-21 15:57:06.7807941	2026-01-21 15:59:48.8001167	16
===
In this output, we can see after 15:53, there was no gateway nodes trying to route traffic to the old DB node "_DB_26", which means all gateway nodes have switched to the new DB node. 
If it would be a "Gateways failed to receive notification from Service Fabric" problem, we might see a few gateway nodes(1~5) are still routing traffic to the old DB node after 15:53. In this case, notify the user about this finding.

In the event that no results are found within the initial 5-minute extension window, extend the query time range by an additional hour in each direction to ensure we capture any delayed events, and re-run the query.

In the event that no results are found within the extended time range, then execute the following to further investigate:

Sample Kusto Query 2:
```
let startTime = datetime(2026-01-26 10:38);
let endTime = datetime(2026-01-28 12:32);
let server = "spartan-srv-emea-d365opsprod-7e293a6676e5";
let db = "db_d365opsprod_bossard_ax_20251027_02485994_c187";
let firstErrorTime = toscalar(MonLogin
| where originalEventTimestamp between (startTime .. endTime)
| where LogicalServerName =~ server and database_name =~ db
| where event == "process_login_finish"
| where error == 40613 and state == 10 and is_success == 0
| summarize min(originalEventTimestamp));
let appNameList = MonLogin
| where originalEventTimestamp between (startTime .. endTime)
| where logical_server_name =~ server and database_name =~ db
| where package == "sqlserver"
| where event == "process_login_finish"
| summarize by AppName;
let gwNodeList = MonLogin
| where originalEventTimestamp between (firstErrorTime-2h .. firstErrorTime+1h)
| where AppTypeName =~ "Gateway" and event == "process_login_finish"
| where logical_server_name =~ server and database_name =~ db
| summarize by NodeName;
let monRedirectorCounts = MonRedirector
| where originalEventTimestamp between (firstErrorTime-2h .. firstErrorTime+1h)
| where service_name has_any (appNameList)
| where NodeName in~ (gwNodeList)
| where event == "fabric_notify_resolve_change"
| summarize n=count() by NodeName;
gwNodeList
| join kind=leftouter monRedirectorCounts on NodeName
| extend n = coalesce(n, 0)
| project NodeName, n;
```

Note:
1. The `startTime`, `endTime`, `server` and `db` are variables which should match the first query in this step.
2. Sample Output 2:

| NodeName | n   |
|----------|-----|
| _GW_3	   | 134 |
| _GW_20   | 134 |
| _GW_6	   | 134 |
| _GW_26   | 12  |
| _GW_22   | 134 |
| _GW_11   | 134 |
| _GW_14   | 0   |
| _GW_0	   | 134 |
| _GW_5	   | 134 |
| _GW_7	   | 134 |


This output will be a simple list of all gateway nodes that have been used to connect to the specified database within the extended time range, along with the count of `fabric_notify_resolve_change` notifications each received. In the above example, NodeName _GW_3 was notified 134 times, NodeName _GW_26 was notified 12 times, and NodeName _GW_14 was notified 0 times, indicating that it did not receive any notifications during the specified time range. _GW_14 would be a candidate for further investigation to understand why it did not receive any notifications. _GW_26, having received fewer notifications than the other nodes, might also warrant further investigation to understand the discrepancy in notification distribution.

For each result row, if notifications were received (i.e., n > 0), it means the gateway received the notification from Service Fabric. Inform the user that the gateway was notified by Service Fabric that the database's location changed. The issue likely stems from timing: the gateway received the notification but some connections were already in flight to the old location.

For each result row, if notifications were not received (i.e., n = 0), it means the gateway did not receive the notification from Service Fabric within the time window around the error time. This could indicate a potential issue with the notification mechanism or a delay in Service Fabric sending the notification. Notify the user that the gateway did not receive the notification from Service Fabric within the expected time frame, which could be due to a delay or an issue with the notification mechanism. In such cases, it is recommended to involve or transfer the issue to the availability team for further investigation.


### Step 4. Verify if instance_name is in correct format.

Given the instance_id output from the Step 2, we can run the following Kusto query to verify the format of the instance_name.

Sample Kusto Query:
```
let startTime =  datetime(2026-02-25 13:00);
let endTime = datetime(2026-2-25 15:00);
let instance_id ="b9406d2d19e3";
MonLogin
| where TIMESTAMP between (startTime ..endTime )
| where instance_name contains instance_id
| summarize count() by instance_name, error, state
```

Note: 
1. Replace the startTime and endTime with user input, replace the instance_id with the output from previous step.
2. We don't have server name in this query because some logins do not contain server name with the instance name.
3. Sample Output of instance_name:
```
instance_name:
mft-prod-sqlfg.database.windows.net\b9406d2d19e3	
b9406d2d19e3.tr375.norwayeast1-a.worker.database.windows.net	
mft-prod-sqlfg.database.windows.net\btbi\b9406d2d19e3	
mft-prod-sqlfg.database.windows.net\\b9406d2d19e3	
```

In the output, only "mft-prod-sqlfg.database.windows.net\b9406d2d19e3" and "b9406d2d19e3.tr375.norwayeast1-a.worker.database.windows.net" are in correct format, the other two formats are incorrect, if the wrong format is associated with login error and state WARN the user about this finding.


### Step 5. Verify if health status of the DB node is good during the error time range.

With the output of step 2, we can know the instance_id and the DB nodes. We can put them into the following kusto query to check when did the infomation started to emit and when did it stop emitting, this helps to verify the lifecycle of the instance.

Sample Kusto Query:
```
// For the old DB node which has the error, check when it stop emitting the infomation, which means the instance is not available after that time point.
let startTime = datetime(2026-01-21 15:20);
let endTime = datetime(2026-01-21 16:59);
let instance_id = "d0f3882c805f";
let Node= "_DB_26";
MonSQLSystemHealth
| where originalEventTimestamp between ((startTime - 1h) .. (endTime + 5m))
| where AppName  =~instance_id
| where NodeName =~"_DB_26"
| summarize count() by NodeName, bin(originalEventTimestamp, 1m)

// For the new DB node, check when it started emitting the information, which means the instance is available after that time point.
let startTime = datetime(2026-01-21 15:20);
let endTime = datetime(2026-01-21 16:59);
let instance_id = "c8b163f85b46";
let Node= "_DB_43";
MonSQLSystemHealth
| where originalEventTimestamp between ((startTime - 1h) .. (endTime + 5m))
| where AppName  =~instance_id
| where NodeName =~Node
| summarize count() by NodeName, bin(originalEventTimestamp, 1m)
```
Note: 
1. Replace the instance_id and Node with the output from step 2. replace the startTime and endTime with user input.
2. If there is large gap that old DB node stop emitting the information and the new DB node start emitting the information, this suggests there is an availability issue on the old DB node, which causes the error. If the time gap is very small, which means the old DB node stopped emitting the information and the new DB node started emitting the information almost in the same time, this suggests there is no availability issue on the old DB node, which means it is more likely to be "Gateways failed to receive notification from Service Fabric" problem or "Old client cache issue". In this case, notify the user about this finding.
3. Service fabric will only send notifications after the database primary replica becomes healthy. 
If a database replica has moved to a new node and is unhealthy there is a likely chance that Service Fabric has never sent a notification informing the Gateways of the new location, so the Gateways still redirect/proxy the connection to the old database location. In these scenarios involve or transfer to the availability team.
