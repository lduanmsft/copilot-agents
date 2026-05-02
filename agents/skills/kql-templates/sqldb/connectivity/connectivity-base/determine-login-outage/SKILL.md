---
name: determine-login-outage
description: This skill would verify any outage is logged assoicated with the  input logical server name/database name and time window.
---

## Step 1. Check Outage based on the input logical server name/database name and time window
Use the following kusto query
```
LoginOutages
| where outageStartTime between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ "{LogicalServerName}" and database_name =~ "{LogicalDatabaseName}"
| project outageStartTime, outageEndTime, durationSeconds, OutageType, OutageReasonLevel1, OutageReasonLevel2, OutageReasonLevel3, OwningTeam// , CustomerReadyRcaText, RcaText 
| order by outageStartTime asc
```

## Step 2. Check any DB Node outage or events and time window
Suppose we have identified the target DB node and tenant ring for the login requests in the previous skill **.github/skills/Connectivity/connectivity-base/determine-login-target/SKILL.md**, we can further check if there is any outage or events related to this DB node and tenant ring in the same time window. You can refer the following kusto query:

```
let _TargetTRRing= "tr9591.southcentralus1-a.worker.database.windows.net" ;
let _TargetDBNode = "_DB_31";
let _StartTime= datetime(02/11/2026  05:00:00) ;
let _EndTime= datetime(02/11/2026  06:00:00) ;
cluster('sqlstage.kusto.windows.net').database('sqlazure1').MonSQLInfraHealthEvents 
| where FaultTime  between (_StartTime .._EndTime)
| where ClusterName =~ _TargetTRRing and NodeName =~ _TargetDBNode
```
Note:
1. _TargetTRRing, _TargetDBNode, _StartTime, _EndTime can be replaced based on the output of previous skill **.github/skills/Connectivity/connectivity-base/determine-login-target/SKILL.md** and the input time window.
2. MonSQLInfraHealthEvents is a centrallized cache table for SQL Infra events, so always use cluster('sqlstage.kusto.windows.net').database('sqlazure1').MonSQLInfraHealthEvents to query this table, no matter which cluster/database you are working on.

## Output
If there is any outage or event output from above 2 KQL queries, output to user.
