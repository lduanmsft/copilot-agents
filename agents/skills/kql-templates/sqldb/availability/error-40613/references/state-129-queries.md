# Kusto Queries for Error 40613 State 129 Diagnostics

## Query Parameter Placeholders

Replace these placeholders with actual values:
- `{StartTime}`: Start timestamp (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp
- `{LogicalServerName}`: Logical server name
- `{LogicalDatabaseName}`: Logical database name
- `{AppName}`: From MonLogin query STATE129-100
- `{NodeName}`: Node where database is hosted / where errors are occurring (from STATE129-100)
- `{physical_database_id}`: From get-db-info skill

---

## STATE129-100 - Error Volume and Duration

Identifies error 40613 state 129 occurrences and calculates duration. If no errors, finish analysis.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonLogin
| where originalEventTimestamp between (StartTime .. EndTime)
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| where error == 40613 and state == 129
| where package =~ "sqlserver" or package =~ "xdbhost"
| where event == 'process_login_finish'
| summarize 
    ErrorCount = count(),
    FirstError = min(originalEventTimestamp),
    LastError = max(originalEventTimestamp)    
    by bin(originalEventTimestamp, 1m), logical_server_name, database_name, package, instance_name, error, state, AppName, ClusterName
| summarize
    TotalErrorCount = sum(ErrorCount),
    OverallFirstError = min(FirstError),
    OverallLastError = max(LastError),
    AppName = any(AppName),
    ClusterName = any(ClusterName)
    by logical_server_name, database_name, error, state
| extend OverallDurationSeconds = datetime_diff('second', OverallLastError, OverallFirstError)
| order by OverallFirstError asc
```

**Assessment:**
- If `OverallDurationSeconds < 30`: Brief HADR disruption, possibly transient during reconfiguration
- If `OverallDurationSeconds > 300`: Persistent HADR failure — escalate immediately

---

## STATE129-110 - Error Summary by Time Window

Aggregates errors to identify persistence patterns.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonLogin
| where originalEventTimestamp between (StartTime .. EndTime)
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| where error == 40613 and state == 129
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

## STATE129-200 - Correlate with SqlFailovers

Checks for failover events during the error window. State 129 may occur before or during a failover.

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
- If failover found: State 129 may be transient during the extended transition
- If **no failover found**: HADR is down without a failover — more serious condition

---

## STATE129-300 - Role Change Events

Analyzes role change events to determine replica state during the error window.

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
    process_id,
    partition_id,
    physical_database_id
| order by originalEventTimestamp asc
```

**Key indicators:**
- `new_role_desc = 'NONE'` without subsequent change to PRIMARY → stuck transition
- `current_state_desc = 'RESOLVING'` → quorum loss, escalate to quorum-loss skill
- `current_state_desc = 'NOT_AVAILABLE'` → HADR subsystem down
- No events at all → HADR not functioning, check node health
- `result_desc` showing failure → role change failed

---

## STATE129-310 - Replica State Transitions

Tracks HADR replica state changes to understand the full lifecycle during the error.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonFabricApi
| where originalEventTimestamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}" and physical_database_id =~ "{physical_database_id}"
| where event has_any (
    "hadr_fabric_api_replicator_state_change",
    "hadr_fabric_api_replicator_begin_change_role",
    "hadr_fabric_api_replicator_end_change_role",
    "hadr_fabric_api_partition_write_status",
    "hadr_fabric_api_replicator_report_fault"
)
| project 
    originalEventTimestamp,
    NodeName,
    event,
    new_role_desc,
    current_state_desc,
    result_desc,
    work_id,
    process_id
| order by originalEventTimestamp asc
```

**What to look for:**
- Sequence of state transitions (PRIMARY → NONE → RESOLVING → ?)
- `hadr_fabric_api_replicator_report_fault` events indicate replica faults
- Time gaps between events may indicate unresponsive HADR subsystem

---

## STATE129-400 - SQL Error Log Messages

Checks for errors during the HADR unavailability window.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonSQLSystemHealth  
| where PreciseTimeStamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where message contains "{physical_database_id}" or message contains "Error:"
| where message has_any ("Error:", "error", "failed", "timeout", "cannot", "unable", "exception", "HADR", "availability", "replica")
| project 
    originalEventTimestamp = PreciseTimeStamp,
    NodeName,
    message,
    process_id
| order by originalEventTimestamp asc
```

**Look for:**
- HADR-related error messages
- Availability replica state change errors
- Storage or I/O failures
- Page server errors (Hyperscale)

---

## STATE129-410 - Hyperscale / Page Server Messages

**Use for Hyperscale (SQLDB_HS_*) SLOs only.** Checks for Socrates page server related messages.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonSQLSystemHealth  
| where PreciseTimeStamp between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| where message has_any ("page server", "PageServer", "Socrates", "remote storage", "RBPEX", "snapshot", "page read")
| project 
    originalEventTimestamp = PreciseTimeStamp,
    NodeName,
    message,
    process_id
| order by originalEventTimestamp asc
```

**Key messages:**
- Page server connectivity failures
- Remote storage read timeouts
- RBPEX (Resilient Buffer Pool Extension) errors
- Snapshot operation failures

---

## STATE129-500 - LoginOutages Impact Assessment

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
- `OutageReasonLevel1-3`: Root cause categorization (look for HADR, PageServer, Socrates)
- `durationSeconds`: Total impact duration
- `OwningTeam`: May indicate Socrates/Hyperscale team ownership

---

## STATE129-600 - Write Status

Verifies write status changes during the HADR unavailability.

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

**Key indicators:**
- `current_write_status_desc = 'NOT_PRIMARY'` → Replica lost primary status
- `current_write_status_desc = 'RECONFIGURATION_PENDING'` → Reconfiguration in progress
- `current_write_status_desc = 'Granted'` → Write status restored, HADR recovered

---

## STATE129-700 - Full Timeline (Combined View)

Combines key events to show complete HADR unavailability timeline.

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime}) + 1m;
let RoleChanges = 
    MonFabricApi
    | where originalEventTimestamp between (StartTime .. EndTime)
    | where AppName =~ "{AppName}"
    | where physical_database_id =~ "{physical_database_id}"
    | where event in ("hadr_fabric_api_replicator_begin_change_role", "hadr_fabric_api_replicator_end_change_role")
    | project Timestamp = originalEventTimestamp, EventType = event, NodeName, Details = strcat("role=", new_role_desc, " state=", current_state_desc);
let StateChanges = 
    MonFabricApi
    | where originalEventTimestamp between (StartTime .. EndTime)
    | where AppName =~ "{AppName}"
    | where physical_database_id =~ "{physical_database_id}"
    | where event has_any ("hadr_fabric_api_replicator_state_change", "hadr_fabric_api_replicator_report_fault")
    | project Timestamp = originalEventTimestamp, EventType = event, NodeName, Details = strcat("state=", current_state_desc, " result=", result_desc);
let WriteStatus = 
    MonFabricApi
    | where originalEventTimestamp between (StartTime .. EndTime)
    | where AppName =~ "{AppName}"
    | where physical_database_id =~ "{physical_database_id}"
    | where event =~ "hadr_fabric_api_partition_write_status"
    | project Timestamp = originalEventTimestamp, EventType = "WriteStatus", NodeName, Details = current_write_status_desc;
union RoleChanges, StateChanges, WriteStatus
| order by Timestamp asc
```

**Expected timeline for recovery:**
1. State 129 errors begin (HADR not available)
2. Role change or state transition events
3. Replica returns to PRIMARY or SECONDARY state
4. Write status = Granted
5. State 129 errors stop