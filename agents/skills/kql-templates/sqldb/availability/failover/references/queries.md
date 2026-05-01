# Kusto Queries for HA Failover Debugging

## Query Parameter Placeholders

Replace these placeholders with actual values (provided by agent from previous skills):
- `{StartTime}`: Start timestamp (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp
- `{Duration}`: Duration (e.g., `1h`, `101m`, `4h + 30m`) - See [Kusto Timespan Format](../../../copilot-instructions.md#kusto-timespan-format)
- `{LogicalServerName}`: Logical server name
- `{LogicalDatabaseName}`: Logical database name
- `{ClusterName}`: From get-db-info skill (tenant_ring_name)
- `{AppName}`: From get-db-info skill (sql_instance_name)
- `{PrimaryNodeName}`: Node name to analyze
- `{physical_database_id}`: From get-db-info skill
- `{fabric_partition_id}`: From get-db-info skill
- `{logical_database_id}`: From get-db-info skill

**Note**: Parameters like ClusterName, AppName, physical_database_id, fabric_partition_id, and logical_database_id 
are obtained from the `get-db-info` skill. See [../../Common/get-db-info/SKILL.md](../../Common/get-db-info/SKILL.md) for details.

---

## HA106 - Identify Delete Primary Replica (GP without ZR)

Only for GP without ZR where DeleteReplica means deleting primary and failover.

```kql
let StartTimeExt=datetime({StartTime}) -1h;
let DurationExt={Duration}+2h;
let NodeMapping=materialize (
WinFabLogs
| where ETWTimestamp between (StartTimeExt..DurationExt)
| where EventType =~ 'NodeLoads'
| where ClusterName =~ '{ClusterName}'
| project Text
| extend lines = split(Text, ')\r\t')
| mv-expand lines
| project lines
| where lines matches regex  '_DB|_MN|_WF|_GW'
| parse lines with SFNodeId:string ' ' NodeName:string ' ' *
| distinct NodeName, SFNodeId
);
WinFabLogs
| where ETWTimestamp between (StartTimeExt..DurationExt)
| where ClusterName =~ '{ClusterName}'
| where EventType =~ 'FTUpdate'
| where Text contains '{physical_database_id}'
| where Text contains 'DeleteReplica'
| extend NodeIdToDelete=extract(@'DeleteReplica->([0-9a-f]{32})', 1, Text)
| project ETWTimestamp, TaskName, EventType,NodeIdToDelete, Text
| join kind=inner 
(NodeMapping)
on $left.NodeIdToDelete==$right.SFNodeId
| project ETWTimestamp, NodeNameToDelete=NodeName, NodeIdToDelete
```

---

## HA107 - Identify New Primary (GP without ZR)

Only for GP without ZR. Do NOT use for other app types.

```kql
let StartTime=datetime({StartTime});
let StartTimeExt=StartTime - 1h;
let EndTimeExt=(StartTime + Duration) + 2h;
let NodeMapping=materialize (
WinFabLogs
| where ETWTimestamp between (StartTimeExt..EndTimeExt)
| where EventType =~ 'NodeLoads'
| where ClusterName =~ '{tenant_ring_name}'
| project Text
| extend lines = split(Text, ')\r\t')
| mv-expand lines
| project lines
| where lines matches regex  '_DB|_MN|_WF|_GW'
| parse lines with SFNodeId:string ' ' NodeName:string ' ' *
| distinct NodeName, SFNodeId
);
WinFabLogs
| where ETWTimestamp between (StartTimeExt..EndTimeExt)
| where ClusterName =~ '{tenant_ring_name}'
| where EventType in ('OperationOperational', 'FTUpdate', 'Operation')
| where Text contains '{physical_database_id}'
| where  Text contains "AddPrimary"
| extend activity_id = extract('ActivityId: ([a-zA-Z0-9-]+)', 1, Text)
| extend activity_id = iff(isnotempty(activity_id), activity_id, extract('ActivityDescription=([a-zA-Z0-9-]+)', 1, Text))
| extend activity_id = iif(isnotempty(activity_id), activity_id, extract('DecisionId: ([a-zA-Z0-9-]+)\r', 1, Text))
| extend activity_id = iif(isnotempty(activity_id), activity_id, extract('EventInstanceId: ([a-zA-Z0-9-]+)\r', 1, Text))
| extend activity_id = iif(isnotempty(activity_id), activity_id, extract('EventInstanceId ([a-zA-Z0-9-]+)', 1, Text))
| extend activity_id = iif(isnotempty(activity_id), activity_id, extract('Actions: ([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', 1, Text))
| extend TargetNodeIdFromOperationOrOperationOperational = extract(@'TargetNode: ([^\s\r\n]+)', 1, Text)
| where isnotempty( activity_id)
| extend TargetNodeIdFromFTUpdate = extract(@'AddPrimary.*?=>([0-9a-f]{32})', 1, Text)
| extend TargetNodeId = case (isnotempty(TargetNodeIdFromFTUpdate), TargetNodeIdFromFTUpdate, isnotempty(TargetNodeIdFromOperationOrOperationOperational), TargetNodeIdFromOperationOrOperationOperational, 'Other')
| where TargetNodeId != 'Other'
| summarize ETWTimestamp=min(ETWTimestamp) by activity_id, NewPrimaryNodeId=TargetNodeId
| join kind=inner 
(
    NodeMapping
) on $left.NewPrimaryNodeId == $right.SFNodeId
| project ETWTimestamp, NewPrimaryNodeId, NewPrimaryNodeName=NodeName
```

---

## HA108 - Find Old & New Primary (GP with ZR and BC)

Look for ReconfigurationStartedOperational event in WinFabLogs.

```kql
WinFabLogs
| where ETWTimestamp  between (datetime({StartTime})..(datetime({StartTime}) + {Duration}))
| where ClusterName =~ '{tenant_ring_name}'
| where Text contains '{fabric_partition_id}'
| where TaskName =~'FM'
| where EventType in ('ReconfigurationStartedOperational')
| extend activity_id = extract('ActivityId: ([a-zA-Z0-9-]+)', 1, Text)
| extend OldPrimaryNodeName = extract(@'OldPrimaryNodeName:\s*(\S+)', 1, Text)
| extend NewPrimaryNodeName = extract(@'NewPrimaryNodeName:\s*(\S+)', 1, Text)
| where NewPrimaryNodeName != OldPrimaryNodeName
| project ETWTimestamp, TaskName, EventType, OldPrimaryNodeName, NewPrimaryNodeName
| order by ETWTimestamp asc
```

---

## HA140 - Failover Events

SqlFailovers only includes completed failovers.

```kql
SqlFailovers
| where FailoverStartTime between (datetime({StartTime})..{Duration})
| where logical_server_name =~ '{LogicalServerName}' and logical_database_name =~ "{LogicalDatabaseName}"
| project FailoverStartTime, FailoverEndTime, ReconfigurationType, CRMAction, OldPrimary, NewPrimary
```

---

## HA200 - LoginOutages Impact Assessment

```kql
LoginOutages
| where outageStartTime between (datetime({StartTime})..{Duration})
| where logical_server_name =~ "{LogicalServerName}" and database_name =~ "{LogicalDatabaseName}"
| project outageStartTime, outageEndTime, durationSeconds, OutageType, OutageReasonLevel1, OutageReasonLevel2, OutageReasonLevel3, OwningTeam
| order by outageStartTime asc
```

---

## HA1020 - DeactivateNode

Monitor node deactivation events during failover.

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})-1h..{Duration}+1h)
| where ClusterName =~ '{ClusterName}'
| where Text contains '{fabric_partition_id}' or Id =~ '{fabric_partition_id}'
| where EventType == 'DeactivateNode' and TaskName == 'FM'
| extend DBNodeName = extract(@"NodeName=\s*([\d\w_]+)", 1, Text), Phase = extract(@"Phase=\s*(\S+)", 1, Text), SafetyCheck = extract(@"SafetyCheck=\s*(\S+),", 1, Text)
| project ETWTimestamp, TaskName, EventType, DBNodeName, Phase, SafetyCheck, Text
| order by ETWTimestamp asc
```

---

## HA1000 - Image Download Event

Download Manager - Image download event.

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})-1h..{Duration}+1h)
| where ClusterName =~ '{ClusterName}'
| where EventType =~ 'DownloadManager'
| where Text contains '{AppName}'
| where isnotnull(NodeName) and NodeName != ''
| where isnotnull(ETWTimestamp) and ETWTimestamp > datetime(2020-01-01)
| summarize arg_max(ETWTimestamp,*) by NodeName
| where isnotnull(ETWTimestamp) and ETWTimestamp > datetime(2020-01-01)
| project ETWTimestamp, ClusterName, NodeName, Id, EventType='ImageDownloaded', TaskName, Text
```

---

## HA1005 - XDB SQL Launch Setup

XdbLaunchSqlSetupEntryPointLog is part of SQL server launch process.

```kql
MonXdbLaunchSetup
| where TIMESTAMP between (datetime({StartTime})-1d..{Duration}+1d)
| where AppName =~ "{AppName}"
| where NodeName =~ '{PrimaryNodeName}'
| where message_systemmetadata contains "XdbLaunchSqlSetupEntryPointLog"
| project originalEventTimestamp, NodeName, message_systemmetadata
| order by originalEventTimestamp asc
```

---

## HA1010 - CodePackage Activation Event

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})-1h..{Duration}+1h)
| where ClusterName =~ '{ClusterName}'
| where EventType =~ 'HostingHealthManager'
| where Text contains '{AppName}'
| where Text contains ' CodePackageActivation:Code' and Text contains 'The CodePackage was activated successfully'
| where isnotnull(NodeName) and NodeName != ''
| where isnotnull(ETWTimestamp) and ETWTimestamp > datetime(2020-01-01)
| summarize arg_max(ETWTimestamp,*) by NodeName
| where isnotnull(ETWTimestamp) and ETWTimestamp > datetime(2020-01-01)
| project ETWTimestamp, ClusterName, NodeName, Id, EventType='CodePackageActivated', TaskName, Text
```

---

## HA2000 - SQL Process Started Event

SQL Process lifetime - SQL Process starting event.

```kql
MonNodeTraceETW
| where PreciseTimeStamp between (datetime({StartTime})-1h..{Duration}+1h)
| where ClusterName =~ '{ClusterName}'
| where Message has '{AppName}'
| where Message contains 'ServiceManifest Name' and Message contains 'SQL' and Message contains '[InitFabric] Started InitFabric'
| where NodeName =~'{PrimaryNodeName}'
| where isnotnull(Pid) and Pid > 0
| summarize arg_max(PreciseTimeStamp, *) by NodeName, Pid
| project PreciseTimeStamp, EventType='SQLProcessStarted', originalEventTimestamp=PreciseTimeStamp, NodeName, Pid, Message
| order by PreciseTimeStamp asc
```

---

## HA2010 - Tempdb Recovery Completed

Tempdb recovery time.

```kql
MonSQLSystemHealth
| where PreciseTimeStamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}'
| where NodeName =~ '{PrimaryNodeName}'
| where message contains "Recovery completed for database tempdb" 
| project PreciseTimeStamp,  message
| order by PreciseTimeStamp asc
```

---

## HA2020 - SQL Server Ready for Client Connections

```kql
MonSQLSystemHealth
| where PreciseTimeStamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}'
| where NodeName =~ '{PrimaryNodeName}'
| where message contains "SQL Server is now ready for client connections" 
| project PreciseTimeStamp,  message
| order by PreciseTimeStamp asc
```

---

## HA2030 - CFabricReplicaManager Registered service type

CFabricReplicaManager initialization and registration.

```kql
MonSQLSystemHealth
| where PreciseTimeStamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}'
| where NodeName =~ '{PrimaryNodeName}'
| where message contains 'CFabricReplicaManager::Start' and message contains 'Registered service type'
| project PreciseTimeStamp, message
| top 1 by PreciseTimeStamp asc
```

---

## HA2040 - SF requests SQL to Create Replica

Service Fabric requests SQL to create a replica.

```kql
MonFabricApi
| where originalEventTimestamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}'
| where NodeName =~ '{PrimaryNodeName}'
| where event == 'hadr_fabric_api_factory_create_replica'
| where partition_id =~ '{fabric_partition_id}'
| project originalEventTimestamp, NodeName, event
| order by originalEventTimestamp asc
```

---

## HA4000 - SQL Instance Level Error Messages

```kql
let IsRelevantMessage = (s: string)
{
    s !contains 'accepting vlf header' and
    s !contains 'CHadrTransportReplica' and
    s !contains 'CFabricCommonUtils' and
    s !contains 'HADR TRANSPOR' and
    s !contains 'DbMgrPartnerCommitPolicy' and
    s !contains 'AlwaysOn Availability Groups' and
    s !contains 'Querying Property Manager' and
    s !contains 'This is an informational message only'
};
let IsRelevantDatabase = (s: string)
{
s contains '{physical_database_id}'
 or s contains '{LogicalDatabaseName}'
    or s contains '{fabric_partition_id}'
    or s contains '{logical_database_id}'
};
MonSQLSystemHealth
| where PreciseTimeStamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}' and event == 'systemmetadata_written'
| where NodeName =~ '{PrimaryNodeName}'
| extend ErrorStateCode = extract('Error: [0-9]*, Severity: [0-9]*, State: [0-9]*', 0, message)
| extend DisplayMessage = replace('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9]+ [a-zA-Z0-9]* ', '', message)
| extend DisplayMessage = trim(@'[\t\n\f\r ]+', DisplayMessage)
| extend ErrorStateCode = iff(ErrorStateCode != '', ErrorStateCode, '(No specific error code)')
| where ErrorStateCode !contains '(No specific error code)'
| summarize FirstSeenTimestamp=min(PreciseTimeStamp), LastSeenTimeStamp=max(PreciseTimeStamp), ErrorCount=count(), SampleMessage=any(DisplayMessage) by ClusterName, NodeName, AppName, process_id, ErrorStateCode
| extend originalEventTimestamp=FirstSeenTimestamp
| extend EventType='Error'
| order by FirstSeenTimestamp asc
```

---

## HA4010 - SQL Instance Errorlog Gaps

Identify gaps in SQL errorlog.

```kql
let Errormsg=
(MonSQLSystemHealth  
| where PreciseTimeStamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}' and NodeName =~ '{PrimaryNodeName}'
| summarize count() by bin(PreciseTimeStamp, 5min), NodeName, AppName
);
 union Errormsg,(print PreciseTimeStamp=datetime({StartTime}), NodeName='{PrimaryNodeName}', AppName='{AppName}'),  (print PreciseTimeStamp=datetime({StartTime})+{Duration}, NodeName='{PrimaryNodeName}', AppName='{AppName}')
| order by PreciseTimeStamp asc
| serialize 
| extend PreviousTimestamp = prev(PreciseTimeStamp, 1)
| extend GapMins = round((PreciseTimeStamp - PreviousTimestamp)/1min,0)
| where GapMins > 15  
| project 
    GapStart = PreviousTimestamp,
    GapEnd = PreciseTimeStamp,
    GapMins,
    EventType='MonSQLSystemHealthTimeGap',
    NodeName,
    AppName,
    originalEventTimestamp = PreviousTimestamp
| order by GapStart asc
```

---

## HA4020 - User Database Recovery Completed

Check for Recovery completed for database event.

```kql
MonSQLSystemHealth  
| where PreciseTimeStamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}' 
| where NodeName =~ '{PrimaryNodeName}'
| where message contains '{physical_database_id}' and (message contains 'Recovery Completed' )
| project originalEventTimestamp,  NodeName, message, process_id
```

---

## HA5005 - Has its Role Changed to Primary?

Check if replica role changed to Primary.

```kql
MonFabricApi
| where originalEventTimestamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}'
| where NodeName =~ '{PrimaryNodeName}'
| where event in ('hadr_fabric_api_replicator_begin_change_role', 'hadr_fabric_api_replicator_end_change_role')
| where physical_database_id =~ '{physical_database_id}' or service_name contains '{physical_database_id}'
| project originalEventTimestamp, NodeName, event, physical_database_id, current_state_desc, new_role_desc
| order by originalEventTimestamp asc
```

---

## HA400 - Write Status Granted on Primary Node

Query by AppName & physical_database_id.

```kql
MonFabricApi
| where originalEventTimestamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}'
| where physical_database_id =~ '{physical_database_id}'
| where event =~ 'hadr_fabric_api_partition_write_status'
| project originalEventTimestamp, previous_write_status_desc, current_write_status_desc, NodeName
| order by originalEventTimestamp asc
```

---

## HA5000 - MonFabricApi Events

XEvents and fabric API events.

```kql
MonFabricApi
| where originalEventTimestamp between (datetime({StartTime})..{Duration})
| where AppName =~ '{AppName}'
| where NodeName =~ '{PrimaryNodeName}'
| where physical_database_id =~ '{physical_database_id}' or service_name contains '{physical_database_id}'
| where event in ('hadr_fabric_api_replicator_begin_change_role','hadr_fabric_api_replicator_end_change_role', 'hadr_fabric_replica_fault', 'hadr_fabric_api_partition_write_status', 'hadr_fabric_api_factory_create_replica')
| project originalEventTimestamp, NodeName, AppName, event, physical_database_id, current_state_desc, new_role_desc, 
    process_id, work_id, result_desc, fault_type_desc, fault_reason_desc, previous_write_status_desc, current_write_status_desc,
    fabric_replica_id, partition_id, service_type, service_name, initialization_data
| order by originalEventTimestamp asc
```

---

## HA210 - Management Operation Actual Timing (MANDATORY for CustomerInitiated outages)

**⚠️ CRITICAL**: When LoginOutages (HA200) shows `OutageType = "CustomerInitiated"` with operations like `UpdateLogicalElasticPool`, `FailoverApi`, or other management operations, you **MUST** execute this query to get the **actual** operation start and end times.

**DO NOT** use timestamps embedded in `OutageReasonLevel3` JSON field - those are snapshot times, not the actual operation completion time.

**How to get `{RequestIds}`**: Extract all unique RequestId values from LoginOutages `OutageReasonLevel3` JSON field across all CustomerInitiated outages, e.g.:
```json
{"OperationType":"UpdateLogicalElasticPool","RequestId":"abc123-def4-5678-...","StartTime":"..."}
```

```kql
MonManagementOperations
| where originalEventTimestamp between (datetime({StartTime})-2h..{Duration}+4h)
| where request_id in~ ({RequestIds})
| where event in ('management_operation_start', 'management_operation_success', 'management_operation_failure')
| summarize
    op_start = minif(originalEventTimestamp, event == 'management_operation_start'),
    op_end = minif(originalEventTimestamp, event in ('management_operation_success', 'management_operation_failure')),
    has_success = countif(event == 'management_operation_success') > 0,
    has_failure = countif(event == 'management_operation_failure') > 0,
    elapsed_ms = maxif(tolong(elapsed_time_milliseconds), event in ('management_operation_success', 'management_operation_failure'))
    by operation_type, request_id
| extend duration_sec = iff(isnotempty(op_start) and isnotempty(op_end), datetime_diff('second', op_end, op_start), toint(elapsed_ms / 1000))
| extend Duration = case(
    isempty(op_end), "In progress",
    duration_sec >= 3600, strcat(duration_sec / 3600, "h ", (duration_sec % 3600) / 60, "m"),
    duration_sec >= 60, strcat(duration_sec / 60, "m ", duration_sec % 60, "s"),
    strcat(duration_sec, "s"))
| extend StartTime = iff(isnotempty(op_start), format_datetime(op_start, 'yyyy-MM-dd HH:mm:ss'), "—")
| extend EndTime = iff(isnotempty(op_end), format_datetime(op_end, 'yyyy-MM-dd HH:mm:ss'), "—")
| extend Status = case(has_success, "Success", has_failure, "Failed", "In progress")
| project OperationType = operation_type, RequestId = request_id, StartTime, EndTime, Duration, Status
| order by StartTime asc
```

**Parameter Format for `{RequestIds}`**: Comma-separated, quoted GUIDs, e.g.:
```
'abc123-def4-5678-...', 'xyz789-ghi0-1234-...'
```

**Output columns** — the query already produces one row per operation with the final table columns:

| Column | Description |
|--------|-------------|
| `OperationType` | e.g., `ResumeContinuousCopy`, `GeoDrTargetReseed` |
| `RequestId` | Full GUID |
| `StartTime` | `management_operation_start` timestamp (null if missing) |
| `EndTime` | `management_operation_success` or `_failure` timestamp (null if missing) |
| `Duration` | Human-readable, e.g., `2h 29m`, `85m 58s` |
| `Status` | `Success`, `Failed`, or `In progress` |

**⚠️ Copy the query results directly into the report table.** Do NOT reformat, re-aggregate, or add raw millisecond values.

**If `StartTime` is null**, display `—` in the report table.
**If `EndTime` is null**, the operation is still in progress.

**Example:**
If LoginOutages shows `OutageReasonLevel3` with `"EndTime":"2026-01-14T04:17:00"` but this query shows `EndTime` at `2026-01-14T07:11:29`, the **correct** end time is **07:11:29 UTC**.

---

## HA6005 - Summarize Error Log Entries by Process

Count the number of entries from the SQL Server error log by node and process.

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})-1h..datetime({EndTime})+1h)
| where AppName =~ '{AppName}'
| extend hour_present = toint(hourofday(originalEventTimestamp))
| summarize log_entry_count = count(), earliest_timestamp = min(originalEventTimestamp), latest_timestamp = max(originalEventTimestamp), hours_present = tostring(array_sort_asc(make_set(hour_present))) by ClusterName, NodeName, AppName, process_id
| order by earliest_timestamp asc, latest_timestamp desc, process_id asc
| serialize
| extend gap_from_previous_in_seconds = iif(earliest_timestamp > prev(latest_timestamp), datetime_diff('second', earliest_timestamp, prev(latest_timestamp)), -1);
```

**Interpretation**

The `earliest_timestamp` and `latest_timestamp` column values show the timespan during which the SQL Server process (as indicated by the combination of the `NodeName` and `process_id` column values) was recording entries in the SQL Server error log. The `hours_present` column values will provide insight into whether there were gaps in log generation for a single process that lasted more than an hour. For example, the following row would indicate that there was at least an hour ("2026-01-28 12:59:59" to "2026-01-28 14:00:00") in which error log entries were not generated/recorded for the SQL Server process with an ID value of "6836" on the "_DB_27" node.

| ClusterName | NodeName | AppName | process_id | log_entry_count | earliest_timestamp | latest_timestamp | hours_present | gap_from_previous_in_seconds |
| ----------- | -------- | ------- | ---------- | --------------- | ------------------ | ---------------- | ------------- | ---------------------------- |
| tr38588.eastus1-a.worker.database.windows.net | _DB_27 | ba98cc9a9db1 | 6836 | 226721 | 2026-01-28 07:26:19.4840966 | 2026-01-28 16:20:48.9873849 | [7,8,9,10,11,12,14,15,16] | -1 |

Gaps like this are interesting and should be noted.

The `gap_from_previous_in_seconds` column values show the gaps from one row of the output to the next row. Disregard all values of "-1". If the value is more than fifteen minutes (900 seconds), it is interesting and should be noted.

**Future improvements**

It would be helpful if the role of the replicas was joined to this result set and considered when calculating the `gap_from_previous_in_seconds` column values, such that the calculation was from one primary replica to the next primary replica or from one secondary replica to the secondary replica that took over for it.

---

## HA6010 - Service Fabric Process Activations and Process Terminations

List the process activations and terminations.

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})-1h..datetime({EndTime})+1h)
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{NodeName}'
| where Text contains '{AppName}'
| where TaskName =~ 'Hosting' and EventType =~ 'EventDispatcher'
| extend EventName = extract(@'.+ EventName:([^,]*), .+, ApplicationId=([^,]*), .+, ExitCode=([^,]*), ApplicationName=([^,]*), ServicePackageName=([^,]*), .+ApplicationHostId=([^,]+), .+', 1, Text)
| extend fabricApplicationURI = extract(@'.+ EventName:([^,]*), .+, ApplicationId=([^,]*), .+, ExitCode=([^,]*), ApplicationName=([^,]*), ServicePackageName=([^,]*), .+ApplicationHostId=([^,]+), .+', 4, Text)
| extend ApplicationID = extract(@'.+ EventName:([^,]*), .+, ApplicationId=([^,]*), .+, ExitCode=([^,]*), ApplicationName=([^,]*), ServicePackageName=([^,]*), .+ApplicationHostId=([^,]+), .+', 2, Text)
| extend ServicePackageName = extract(@'.+ EventName:([^,]*), .+, ApplicationId=([^,]*), .+, ExitCode=([^,]*), ApplicationName=([^,]*), ServicePackageName=([^,]*), .+ApplicationHostId=([^,]+), .+', 5, Text)
| extend ExitCode = toint(extract(@'.+ EventName:([^,]*), .+, ApplicationId=([^,]*), .+, ExitCode=([^,]*), ApplicationName=([^,]*), ServicePackageName=([^,]*), .+ApplicationHostId=([^,]+), .+', 3, Text))
| extend ApplicationHostID = extract(@'.+ EventName:([^,]*), .+, ApplicationId=([^,]*), .+, ExitCode=([^,]*), ApplicationName=([^,]*), ServicePackageName=([^,]*), .+ApplicationHostId=([^,]+), .+', 6, Text)
| where EventName in~ ('CodePackageActivated', 'CodePackageDeactivated')
| project ETWTimestamp, ClusterName, NodeName, TaskName, EventType, EventName, fabricApplicationURI, ApplicationID, ServicePackageName, ExitCode, ApplicationHostID, Text
| join kind = leftouter (
    WinFabLogs
    | where ETWTimestamp between (datetime({StartTime})-1h..datetime({EndTime})+1h)
    | where ClusterName =~ '{ClusterName}'
    | where NodeName =~ '{NodeName}'
    | where TaskName =~ 'Hosting' and EventType =~ 'ApplicationService'
    | where Text matches regex @'Application Service ([^\s]+) was activated with process id (\d+), ExeName (.+)'
    | extend ApplicationHostID = extract(@'Application Service ([^\s]+) was activated with process id (\d+), ExeName (.+)', 1, Text)
    | extend ProcessID = toint(extract(@'Application Service ([^\s]+) was activated with process id (\d+), ExeName (.+)', 2, Text))
    | extend EXEName = extract(@'Application Service ([^\s]+) was activated with process id (\d+), ExeName (.+)', 3, Text)
    | distinct ClusterName, NodeName, ApplicationHostID, ProcessID, EXEName
) on ClusterName, NodeName, ApplicationHostID
| project ETWTimestamp, ClusterName, NodeName, TaskName, EventType, EventName, fabricApplicationURI, ApplicationHostID, ServicePackageName, ProcessID, EXEName, ExitCode
| order by ETWTimestamp asc;
```

**Interpretation**

The `ExitCode` column is only populated for the "CodePackageDeactivated" event. `ExitCode` column values other than "0" are interesting and should be noted.

Look for patterns in process activations and terminations. For example, check to see whether the SQL Server process is terminating after a fixed period of time, such as every ten minutes, every eleven minutes, or similar. It would be especially relevant if there is a pattern of either the "sqlservr.exe" and/or "XdbLaunchSqlSetup.exe" process terminating repeatedly, at a common interval, and with the same `ExitCode` column values. Summarize any patterns for the user.

---

## HA6015 - First and Last Log Entries from MonXdbLaunchSetup

The "XdbLaunchSqlSetup.exe" process is started first by Service Fabric and will, if successful, launch the SQL Server process. If the SQL Server process isn't running for a period of time, it may be due to problems in the "XdbLaunchSqlSetup.exe" process.

```kql
MonXdbLaunchSetup
| where originalEventTimestamp between (datetime({startTime})-1h..datetime({endTime})+1h)
| where AppName =~ '{appName}'
| summarize LogEntryCount = count(), arg_min(originalEventTimestamp, message_systemmetadata), arg_max(originalEventTimestamp, message_systemmetadata) by ClusterName, NodeName, AppName, process_id
| project EarliestEventTimestamp = originalEventTimestamp, LatestEventTimestamp = originalEventTimestamp1, EntriesTimespanInSeconds = datetime_diff('second', originalEventTimestamp1, originalEventTimestamp), ClusterName, NodeName, AppName, process_id, LogEntryCount, FirstMessage = message_systemmetadata, LastMessage = message_systemmetadata1
| order by EarliestEventTimestamp asc, LatestEventTimestamp desc;
```

**Interpretation**

The `FirstMessage` column values should typically be "=================== XdbLaunchSqlSetupEntryPointLog =================" and the `LastMessage` column values should typically be "Exiting XdbSqlLaunchSetup without exceptions". If the values are different, that is interesting and should be noted.

The `EntriesTimespanInSeconds` column values should typically be less than ten seconds long. If there are durations ten seconds or longer, that is interesting and should be noted.

---

## HA6020 - First and Last Log Entries from MonNodeTraceETW

If the SQL Server process is repeatedly terminating, look for patterns of log entries in the `MonNodeTraceETW` Kusto table.

```kql
MonNodeTraceETW
| where TIMESTAMP between (datetime({startTime})-1h..datetime({endTime})+1h)
| where ClusterName =~ '{tenantRingName}' and NodeName =~ '{nodeName}'
| where Message contains ' CodePackageName "Code" ServiceManifest Name "SQL"'
| where Message has '{appName}'
| extend Message = extract(@' Message : "(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{2}\s+\w+\s+)?(.+?)[\r\n]?"', 2, Message)
| where isnotempty(Message)
| where Message !contains 'Not reporting metrics'
| summarize LogEntryCount = count(), arg_min(TIMESTAMP, Message), arg_max(TIMESTAMP, Message) by ClusterName, NodeName, Pid
| project EarliestEventTimestamp = TIMESTAMP, LatestEventTimestamp = TIMESTAMP1, EntriesTimespanInSeconds = datetime_diff('second', TIMESTAMP1, TIMESTAMP), ClusterName, NodeName, Pid, LogEntryCount, FirstMessage = Message, LastMessage = Message1
| order by EarliestEventTimestamp asc, LatestEventTimestamp desc;
```

**Interpretation**

The `FirstMessage` column values should typically be "[InitFabric] Started InitFabric setup!" and the `LastMessage` column values should typically be "** FabricStatefulServiceFactory::Startup **". If the values are different, that is interesting and should be noted.

---
