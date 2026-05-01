# Kusto Queries for Error 40613 State 126 Diagnostics

## Query Parameter Placeholders

Replace these placeholders with actual values:
- `{StartTime}`: Start timestamp (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp
- `{Duration}`: Duration (e.g., `1h`, `30m`)
- `{LogicalServerName}`: Logical server name
- `{LogicalDatabaseName}`: Logical database name
- `{ClusterName}`: From Monlogin Query STATE126-100
- `{AppName}`: From Monlogin Query STATE126-100
- `{fabric_partition_id}`: From SqlFailovers Query STATE126-200 (`PartitionId` column), or from get-db-info skill (`fabric_partition_id`)
- `{DatabaseId}`: Obtained from get-db-info skill. Required for STATE126-400/410 to isolate one DB when AppName is shared (elastic pool).


---

## STATE126-100 - Error Volume and Duration

Identifies error 40613 state 126 occurrences and calculates duration. If no errors, finish analysis.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonLogin
| where originalEventTimestamp between (StartTime .. EndTime)
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| where error == 40613 and state == 126
| where package =~ "sqlserver" or package =~ "xdbhost"
| summarize 
    ErrorCount = count(),
    FirstError = min(originalEventTimestamp),
    LastError = max(originalEventTimestamp)    
    by bin(originalEventTimestamp, 1m), NodeName,logical_server_name, database_name, package, instance_name, error, state, AppName, ClusterName
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
- If `OverallDurationSeconds < 30`: Expected transient error, Send canned RCA.
- If `OverallDurationSeconds > 120`: Stuck transition - Additional Troubleshooting needed

---

## STATE126-110 - Error Summary by Time Window

Aggregates errors to identify persistence patterns.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonLogin
| where originalEventTimestamp between (StartTime .. EndTime)
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| where error == 40613 and state == 126
| where package =~ "sqlserver" or package =~ "xdbhost"
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

## STATE126-200 - Correlate with SqlFailovers

Checks for failover events during the error window.

```kql
SqlFailovers
| where FailoverStartTime between (datetime({StartTime}) .. datetime({EndTime}))
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
- State 126 errors should occur BETWEEN `FailoverStartTime` and `FailoverEndTime`
- Errors persisting AFTER `FailoverEndTime` indicate a problem

---

## STATE126-300 - Role Change XEvents

Analyzes begin/end role change events to detect stuck transitions.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonFabricApi
| where TIMESTAMP between (StartTime .. EndTime)
| where AppName =~ "{AppName}" and partition_id =~ "{fabric_partition_id}"
| where event in ("hadr_fabric_api_replicator_begin_change_role", "hadr_fabric_api_replicator_end_change_role")
| project 
    PreciseTimeStamp,
    NodeName,
    event,
    new_role_desc,
    current_state_desc,
    result_desc,
    work_id,
    process_id,
    partition_id
| order by PreciseTimeStamp asc
```

**Analysis steps:**
1. Match `begin_change_role` with `end_change_role` by `work_id` and `process_id`
2. Calculate gap between begin and end
3. 🚩 Flag if `begin` has no matching `end` within 60 seconds
4. 🚩 Flag if `result_desc` shows failure

---

## STATE126-400 - Database Recovery Status

Checks if database recovery completed after role change.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonSQLSystemHealth  
| where PreciseTimeStamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where logical_database_guid != '00000000-0000-0000-0000-000000000000'
| where message contains "Recovery completed" or message contains "recovery completed"
| extend DatabaseID = toint(extract(@"database ID (\d+)", 1, message))
| where DatabaseID == {DatabaseId}
| project 
    RecoveryTime = PreciseTimeStamp,
    NodeName,
    message,
    process_id,logical_database_guid,DatabaseID
| order by RecoveryTime asc
```

**If no results:**
- Database recovery may be ongoing or stuck
- Check state 127 skill for warmup issues 
- Look for "Starting up database" messages

---

## STATE126-410 - Recovery Progress Messages

Tracks database startup and recovery progress.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonSQLSystemHealth  
| where PreciseTimeStamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where logical_database_guid != '00000000-0000-0000-0000-000000000000'
| where message has_any ("Starting up database", "Recovery", "redo", "undo", "Parallel redo")
| extend DatabaseID = toint(extract(@"database ID (\d+)", 1, message))
| where DatabaseID == {DatabaseId}
| project PreciseTimeStamp, NodeName, message, process_id,logical_database_guid,DatabaseID
| order by PreciseTimeStamp asc
```

---

## STATE126-500 - LoginOutages Impact Assessment

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