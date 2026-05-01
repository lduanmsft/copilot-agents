# Kusto Queries for Error 40613 State 127 Diagnostics

## Query Parameter Placeholders

Replace these placeholders with actual values:
- `{StartTime}`: Start timestamp (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp
- `{LogicalServerName}`: Logical server name
- `{LogicalDatabaseName}`: Logical database name
- `{ClusterName}`: From MonLogin query STATE127-100
- `{AppName}`: From MonLogin query STATE127-100
- `{DBNodeName}`: Node where database is hosted / where errors are occurring (from STATE127-100)
- `{physical_database_id}`: From get-db-info skill
- `{fabric_partition_id}`: From SqlFailovers query STATE127-200 (`PartitionId` column), or from get-db-info skill
- `{sql_database_id}`: Obtained from get-db-info skill. Required to isolate one DB when AppName is shared (elastic pool).

---

## STATE127-100 - Error Volume and Duration

Identifies error 40613 state 127 occurrences and calculates duration. If no errors, finish analysis.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonLogin
| where originalEventTimestamp between (StartTime .. EndTime)
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| where error == 40613 and state == 127
| where package =~ "sqlserver" or package =~ "xdbhost"
| where event == 'process_login_finish'
| summarize 
    ErrorCount = count(),
    FirstError = min(originalEventTimestamp),
    LastError = max(originalEventTimestamp)    
    by bin(originalEventTimestamp, 1m), NodeName, logical_server_name, database_name, package, instance_name, error, state, AppName, ClusterName
| summarize
    TotalErrorCount = sum(ErrorCount),
    OverallFirstError = min(FirstError),
    OverallLastError = max(LastError),
    AppName = any(AppName),
    ClusterName = any(ClusterName)
    by logical_server_name, database_name, NodeName, error, state
| extend OverallDurationSeconds = datetime_diff('second', OverallLastError, OverallFirstError)
| order by OverallFirstError asc
```

**Assessment:**
- If `OverallDurationSeconds < 60`: Expected transient warmup, send canned RCA
- If `OverallDurationSeconds > 300`: Stuck warmup - additional troubleshooting needed

---

## STATE127-110 - Error Summary by Time Window

Aggregates errors to identify persistence patterns.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonLogin
| where originalEventTimestamp between (StartTime .. EndTime)
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| where error == 40613 and state == 127
| where package =~ "sqlserver" or package =~ "xdbhost"
| where event == 'process_login_finish'
| summarize 
    ErrorCount = count(),
    MinTime = min(originalEventTimestamp),
    MaxTime = max(originalEventTimestamp)
    by bin(originalEventTimestamp, 1m)
| order by MinTime asc
| serialize
| extend GapToPrevious = MinTime - prev(MaxTime)
| project originalEventTimestamp, ErrorCount, MinTime, MaxTime, GapToPrevious
```

---

## STATE127-200 - Correlate with SqlFailovers

Checks for failover events during the error window. State 127 should start around FailoverEndTime.

```kql
SqlFailovers
| where (FailoverStartTime <= datetime({EndTime}) and FailoverEndTime >= datetime({StartTime}))
| where logical_server_name =~ "{LogicalServerName}" 
| where logical_database_name =~ "{LogicalDatabaseName}"
| project 
    FailoverStartTime, 
    FailoverEndTime, 
    FailoverDurationSeconds = datetime_diff('second', FailoverEndTime, FailoverStartTime),
    ReconfigurationType, 
    CRMAction, 
    OldPrimary, 
    NewPrimary,
    PartitionId
| order by FailoverStartTime asc
```

**Correlation check:**
- State 127 errors should START around `FailoverEndTime` (when role change completes)
- State 127 errors should STOP when database recovery completes

---

## STATE127-300 - Role Change End Events

Verifies that the role change completed successfully before warmup began.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonFabricApi
| where originalEventTimestamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}" and physical_database_id =~ "{physical_database_id}"
| where event in ("hadr_fabric_api_replicator_begin_change_role", "hadr_fabric_api_replicator_end_change_role")
| project 
    originalEventTimestamp,
    NodeName,
    event,
    new_role_desc,
    current_state_desc,
    result_desc,
    work_id,
    process_id, partition_id, physical_database_id
| order by originalEventTimestamp asc
```

**Verification:**
- Look for `hadr_fabric_api_replicator_end_change_role` with `result_desc` = success
- Confirm `new_role_desc = 'Primary'`
- If no successful end event, escalate to state 126 skill

---

## STATE127-400 - Database Recovery Messages

Checks for database recovery start and completion messages.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonSQLSystemHealth  
| where PreciseTimeStamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where logical_database_guid != '00000000-0000-0000-0000-000000000000'
| where message contains "{physical_database_id}"
| where message has_any ("Starting up database", "Recovery completed", "recovery completed", "Parallel redo")
| extend DatabaseID = toint(extract(@"database ID (\d+)", 1, message))
| where DatabaseID == {sql_database_id}
| project 
    originalEventTimestamp = PreciseTimeStamp,
    NodeName,
    message,
    process_id,logical_database_guid,DatabaseID
| order by originalEventTimestamp asc
```

**Key messages to look for:**
- "Starting up database {physical_database_id}" - Recovery started
- "Recovery completed for database {physical_database_id}" - Recovery finished
- "Parallel redo is started" / "Parallel redo is shutdown" - Redo phase tracking

---

## STATE127-410 - Detailed Recovery Progress

Tracks detailed recovery messages including redo/undo progress.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonSQLSystemHealth  
| where PreciseTimeStamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where logical_database_guid != '00000000-0000-0000-0000-000000000000'
| where message contains "{physical_database_id}"
| where message has_any (
    "Starting up database",
    "Recovery completed",
    "recovery completed",
    "Parallel redo",
    "redo starts",
    "redo done",
    "undo",
    "analysis",
    "Recovery is writing a checkpoint",
    "Database ID"
)
| extend DatabaseID = toint(extract(@"database ID (\d+)", 1, message))
| project 
    originalEventTimestamp = PreciseTimeStamp,
    NodeName,
    message,
    process_id,logical_database_guid,DatabaseID
| order by originalEventTimestamp asc
```

**Recovery phases:**
1. Analysis phase - "analysis" messages
2. Redo phase - "redo starts", "Parallel redo", "redo done"
3. Undo phase - "undo" messages
4. Complete - "Recovery completed"

---

## STATE127-500 - SQL Error Log Messages

Checks for errors or issues during recovery.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonSQLSystemHealth  
| where PreciseTimeStamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where message contains "{physical_database_id}" or message contains "Error:"
| where message has_any ("Error:", "error", "failed", "timeout", "cannot", "unable", "exception")
| project 
    originalEventTimestamp = PreciseTimeStamp,
    NodeName,
    message,
    process_id
| order by originalEventTimestamp asc
```

**Look for:**
- Error messages during recovery
- Timeout issues
- Storage/I/O problems
- Memory issues

---

## STATE127-510 - Tempdb Recovery

Checks for tempdb recovery completion. Tempdb must recover before user databases.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonSQLSystemHealth  
| where PreciseTimeStamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where NodeName =~ "{DBNodeName}"
| where message contains "tempdb"
| where message has_any ("Recovery completed for database tempdb", "Starting up database tempdb", "DropTempObjects")
| project 
    originalEventTimestamp = PreciseTimeStamp,
    NodeName,
    message,
    process_id
| order by originalEventTimestamp asc
```

**Tempdb issues:**
- Slow tempdb recovery delays all user database recovery
- DropTempObjectsOnDBStartup can take long if many temp objects

---

## STATE127-600 - LoginOutages Impact Assessment

Checks platform-reported outage information.

```kql
LoginOutages
| where outageStartTime between (datetime({StartTime}) - 5m .. datetime({EndTime}) + 5m)
| where logical_server_name =~ "{LogicalServerName}" 
| where database_name =~ "{LogicalDatabaseName}"
| project 
    outageStartTime, 
    outageEndTime, 
    durationSeconds,
    OutageType, 
    OutageReasonLevel1, 
    OutageReasonLevel2, 
    OutageReasonLevel3,
    OwningTeam
| order by outageStartTime asc
```

**Key fields to analyze:**
- `OutageType`: Planned vs Unplanned
- `OutageReasonLevel1-3`: Root cause categorization
- `durationSeconds`: Total impact duration

---

## STATE127-700 - Write Status Granted

Verifies that write status was granted after recovery completed.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime}) + 1m;
MonFabricApi
| where originalEventTimestamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where physical_database_id =~ "{physical_database_id}"
| where event =~ "hadr_fabric_api_partition_write_status"
| project 
    originalEventTimestamp, 
    NodeName,
    previous_write_status_desc, 
    current_write_status_desc
| order by originalEventTimestamp asc

```

**Expected flow:**
- `current_write_status_desc = 'Granted'` indicates database is ready for writes
- If write status never granted, role change may not have completed properly

---

## STATE127-800 - Full Timeline (Combined View)

Combines key events to show complete warmup timeline.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime}) + 1m;
let RoleChanges = 
    MonFabricApi
    | where originalEventTimestamp between (StartTime .. EndTime)
    | where AppName =~ "{AppName}"
    | where physical_database_id =~ "{physical_database_id}"
    | where event in ("hadr_fabric_api_replicator_begin_change_role", "hadr_fabric_api_replicator_end_change_role")
    | project Timestamp = originalEventTimestamp, EventType = event, NodeName, Details = new_role_desc;
let RecoveryEvents = 
    MonSQLSystemHealth  
    | where PreciseTimeStamp between (StartTime .. EndTime)
    | where AppName =~ "{AppName}"
    | where message contains "{physical_database_id}"
    | where message has_any ("Starting up database", "Recovery completed")
    | project Timestamp = PreciseTimeStamp, EventType = "Recovery", NodeName, Details = message;
let WriteStatus = 
    MonFabricApi
    | where originalEventTimestamp between (StartTime .. EndTime)
    | where AppName =~ "{AppName}"
    | where physical_database_id =~ "{physical_database_id}"
    | where event =~ "hadr_fabric_api_partition_write_status"
    | project Timestamp = originalEventTimestamp, EventType = "WriteStatus", NodeName, Details = current_write_status_desc;
union RoleChanges, RecoveryEvents, WriteStatus
| order by Timestamp asc
```

**Expected timeline:**
1. `hadr_fabric_api_replicator_begin_change_role` - Role change starts (state 126 begins)
2. `hadr_fabric_api_replicator_end_change_role` - Role change ends (state 126 → 127)
3. `Starting up database` - Recovery begins
4. `Recovery completed` - Recovery ends (state 127 ends)
5. `WriteStatus = Granted` - Database available for writes