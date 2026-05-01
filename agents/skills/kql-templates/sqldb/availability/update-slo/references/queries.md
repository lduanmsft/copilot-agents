# Kusto Queries for Update SLO Debugging

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp in UTC (e.g., `2026-01-01 10:00:00`)

**Resource identifiers:**
- `{LogicalServerName}`: Logical server name (e.g., `my-server`)
- `{LogicalDatabaseName}`: Logical database name (e.g., `my-db`)

**Management Service:**
- `{request_id}`: Request identifier for tracking specific operations (extracted from USLO200 results)

**Derived parameters** (extracted during analysis, not provided upfront):
- `{SourceAppName}`: Source database AppName (`database_usage_status = 'Active'` from USLO100)
- `{TargetAppName}`: Target database AppName (`database_usage_status = 'UpdateSloTarget'` from USLO100)

---

## Step 1: Get Management Operation Overview

### USLO200 - Management Operations Overview

**Purpose:** Finds management operations for this database to get the `request_id` for the Update SLO. Uses `MonManagementOperations` (180-day retention) which reliably captures all operations regardless of duration.

**What to look for:**
- `request_id` for the Update SLO operation
- `event` column: success, failure, timeout, or still in progress
- `elapsed_time_milliseconds` for total operation duration

```kql
MonManagementOperations
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where operation_parameters has '{LogicalServerName}' and operation_parameters has '{LogicalDatabaseName}'
| project request_id, operation_type, operation_category, originalEventTimestamp,
    operation_owner_alias, event, process_id, elapsed_time, elapsed_time_milliseconds,
    error_code, error_message, operation_parameters
| order by originalEventTimestamp asc
```

**Expected output:**
- `request_id`: Unique operation ID — use in subsequent queries
- `operation_type`: Should show `UpdateDatabase` or similar for SLO changes
- `event`: `management_operation_success`, `management_operation_failure`, `management_operation_timeout`, `management_operation_user_cancel_start`, `management_operation_interrupt`
- `elapsed_time_milliseconds`: Total duration — convert to hours for readability
- `error_code`: Maps to `sqlerrorcodes.h` in DsMainDev repo
- If no rows appear, extend time window (MonManagementOperations has 180-day retention)

---

## Step 2: Identify Source and Target

### USLO100 - Database Info with Update SLO Source/Target Detection

**Purpose:** Checks for source/target database snapshots to extract AppNames and SLO details. Captures longer-running operations where `MonAnalyticsDBSnapshot` (45-day retention) has time to record the target.

**What to look for:**
- Rows with `database_usage_status = 'UpdateSloTarget'` confirm an Update SLO was captured by the snapshot
- Extract source and target AppNames from `fabric_application_uri`
- Compare `service_level_objective` between source and target to determine upgrade vs downgrade
- **Note:** Fast-completing operations may finish before `MonAnalyticsDBSnapshot` captures them. If empty, proceed with FSM analysis using `request_id` from Step 1

```kql
MonAnalyticsDBSnapshot
| where PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where fabric_application_uri !contains 'fabric:/Worker.Vldb.Storage/'
    and fabric_application_uri !contains 'fabric:/Worker.Vldb.LogReplica/'
| project-reorder PreciseTimeStamp, fabric_application_uri, fabric_partition_id, physical_database_id,
    sql_database_id, state, database_usage_status, physical_database_state, service_level_objective,
    edition, zone_resilient, tenant_ring_name, logical_server_name, logical_database_name
| order by PreciseTimeStamp asc
```

**Expected output:**
- `database_usage_status`: `Active` (source) or `UpdateSloTarget` (target)
- `fabric_application_uri`: Contains AppName — extract for subsequent queries
- `service_level_objective`: SLO value for source and target
- `state`: Database state (e.g., `Ready`, `UpdateSloInProgress`)
- If no `UpdateSloTarget` row exists, the operation may have completed too quickly for snapshot capture — this is normal for fast operations. Use `request_id` from USLO200 to continue analysis

---

## Step 3: Analyze FSM State Transitions

### USLO210 - FSM State Transitions

**Purpose:** Shows FSM state transitions with duration between each state.

**What to look for:**
- Last `new_state` value is the current/stuck state
- States with `duration_h > 1` are 🚩 potentially stuck
- Common stuck states: `CheckingRedoQueueSize`, `KillingLongTransactionsBeforeCopying`, `WaitingForRoleChange`

```kql
MonManagement
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where request_id =~ '{request_id}'
| where event =~ "fsm_changed_state"
| order by originalEventTimestamp asc
| extend prev_ts = prev(originalEventTimestamp, 1)
| extend duration_s = (originalEventTimestamp - prev_ts) / 1s
| project originalEventTimestamp, state_machine_type, old_state, new_state,
    round(duration_s), duration_m = round(duration_s/60, 1), duration_h = round(duration_s/3600, 1)
```

**Expected output:**
- `state_machine_type`: `UpdateSloStateMachine`, `LogicalDatabaseStateMachine`, `FabricServiceStateMachine`
- `old_state` / `new_state`: Sequential state transitions
- `duration_m` / `duration_h`: Time spent in each state
- See principles.md for expected timings per state

---

### USLO215 - FSM State Duration Summary

**Purpose:** Summarizes time in each state and transition count — detects retries and slowest states at a glance.

**What to look for:**
- `count_ > 1` for a transition → FSM retried that action multiple times (🚩 investigate via USLO300)
- Longest `duration_h` identifies the bottleneck state
- Filter by `state_machine_type == 'UpdateSloStateMachine'` to focus on SLO change FSM

```kql
MonManagement
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where request_id =~ '{request_id}'
| where isnotempty(action) and isnotempty(old_state)
| summarize min(originalEventTimestamp), max(originalEventTimestamp), count() by state_machine_type, old_state, new_state
| extend duration_s = (max_originalEventTimestamp - min_originalEventTimestamp) / 1s
| extend duration_m = round(duration_s / 60, 1), duration_h = round(duration_s / 3600, 1)
| order by min_originalEventTimestamp asc
```

**Expected output:**
- `state_machine_type` / `old_state` / `new_state`: Each unique state transition
- `count_`: Number of times this transition occurred (>1 = retries)
- `duration_m` / `duration_h`: Total time span for this transition
- Complements USLO210: USLO210 shows the sequential timeline, USLO215 shows the aggregate summary

---

## Step 4: Check for Exceptions and Errors

### USLO300 - Management Exceptions

**Purpose:** Finds exceptions and errors for a specific management operation.

**What to look for:**
- `exception_type = 'System.TimeoutException'` → Fabric operation timed out
- `stack_trace` containing `NodeAgent` → Database unavailable
- `stack_trace` containing `CompleteHekatonSloDowngrade` → Hekaton issue
- `event = 'fsm_executed_action_failed'` → Action execution failure

```kql
MonManagement
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where request_id =~ '{request_id}'
| where strlen(stack_trace) > 0 or strlen(message) > 0 or strlen(exception_type) > 0
| project originalEventTimestamp, request_id, event, fsm_event, action,
    state_machine_type, elapsed_time, keys, old_state, new_state,
    operation_parameters, exception_type, stack_trace, location,
    service_name, cluster_name, message
| order by originalEventTimestamp asc
```

**Expected output:**
- `exception_type`: Type of exception (e.g., `System.TimeoutException`)
- `stack_trace`: Full stack trace — search for `NodeAgent`, `CompleteHekatonSloDowngrade`, `FiniteStateMachineLockTimeoutException`
- `event`: `fsm_executed_action_failed` indicates action failure — check `action` column for which step
- `old_state` / `new_state`: State context when exception occurred

---

## Step 5: Assess Replication and Seeding

### USLO400 - Replication Status (ContinuousCopyV2 mode)

**Purpose:** Checks replication lag between source and target for copy-based Update SLO.

**What to look for:**
- High `replication_lag_sec` → Target cannot keep up with source writes
- `replication_state` issues → Replication pipeline problems
- Correlate with `CheckingRedoQueueSize` stuck state from USLO210

```kql
MonDmContinuousCopyStatus
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where AppName in (tolower('{SourceAppName}'), tolower('{TargetAppName}'))
| project originalEventTimestamp, AppName, partner_server, partner_database,
    replication_state, replication_lag_sec, last_replication, percent_complete
| order by originalEventTimestamp asc
```

**Expected output:**
- `replication_lag_sec`: Lag in seconds — high values during SLO downgrade are common
- `replication_state`: Current replication state
- `percent_complete`: Data copy progress percentage

---

### USLO500 - SQL System Health Errors

**Purpose:** Checks for SQL errors on source and target instances during the Update SLO window.

**What to look for:**
- Error 823/824/825 → Disk I/O errors affecting database operations
- Error 9001 → Log errors during recovery
- "Nonqualified transactions are being rolled back" → Rollback stuck (GEODR0004.4)

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where AppName in (tolower('{SourceAppName}'), tolower('{TargetAppName}'))
| where severity >= 14
| summarize count(), FirstSeen=min(originalEventTimestamp), LastSeen=max(originalEventTimestamp)
    by error_number, severity, message=substring(message, 0, 200), AppName
| order by count_ desc
```

**Expected output:**
- `error_number`: SQL error number (823, 824, 825, 9001)
- `count_`: Number of occurrences
- `FirstSeen` / `LastSeen`: Time range of errors — correlate with FSM state transitions
- `message`: Error message text (truncated to 200 chars)

---

## Step 6: Check SLO Transition History

### USLO600 - SLO Transition History

**Purpose:** Shows the SLO value changes over time for the logical database.

**What to look for:**
- Multiple rows with different `service_level_objective` → SLO was changed
- `state` column transitions (e.g., `Ready` → `UpdateSloInProgress` → `Ready`)
- If `state` reverted to `Ready` with original SLO → Update SLO was rolled back

```kql
MonAnalyticsDBSnapshot
| where PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| summarize min(PreciseTimeStamp), max(PreciseTimeStamp)
    by tenant_ring_name, sql_instance_name, logical_server_name, logical_database_name,
    state, edition, service_level_objective
| order by min_PreciseTimeStamp asc, max_PreciseTimeStamp asc
```

**Expected output:**
- `service_level_objective`: SLO value at each time range
- `state`: Database state (`Ready`, `UpdateSloInProgress`, etc.)
- `edition`: Edition (Standard, Premium, GeneralPurpose, BusinessCritical)
- `min_PreciseTimeStamp` / `max_PreciseTimeStamp`: Time range for each SLO value

---

## Step 7: Conditional Deep-Dive Queries

### USLO700 - Fabric Service Drop Status (for GEODR0004.1)

**Purpose:** Confirms physical database drop is stuck. Use only when stuck in `WaitingForSourcePhysicalDatabaseDrop` or `WaitingForLinkAndPhysicalDatabaseDrop`.

**What to look for:**
- `System.TimeoutException: Operation timed out` in stack trace
- Physical database ID extracted from `keys` column

```kql
MonManagement
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where request_id =~ '{request_id}'
| where state_machine_type == "FabricServiceStateMachine" and event == "fsm_executed_action_failed" and action == "TransitionDrop"
| summarize argmax(originalEventTimestamp, stack_trace, keys), request_id = any(request_id)
| where max_originalEventTimestamp_stack_trace contains "System.TimeoutException: Operation timed out"
| extend pdbid = split(split(max_originalEventTimestamp_keys, ",")[1], "/")[4]
| project TSG = 'GEODR0004.1', Details = strcat('Fabric service for physical database ID ', pdbid, ' is stuck in dropping state')
```

**Expected output:**
- `TSG`: `GEODR0004.1` confirming the diagnosis
- `Details`: Physical database ID that is stuck in dropping state
- Mitigation: GEODRSOP0001 (kill SQL processes for all replicas)

---

### USLO800 - FSM Execution Delays (Control Plane Overload Detection)

**Purpose:** Detects if the control plane itself is overloaded, causing delays in FSM execution.

**What to look for:**
- `et > 30000` (30s) per hour per state machine → Control plane overloaded
- High values across many state machines → Systemic issue
- Only this request shows delays → Issue specific to this operation

```kql
MonManagement
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where event == "fsm_executed_action" or event == "fsm_executed_action_failed"
| extend SM = strcat(NodeName, "|", state_machine_type)
| summarize et = sum(elapsed_time_milliseconds) by SM, bin(originalEventTimestamp, 1h)
| where et > 30000
| order by et desc
```

**Expected output:**
- `SM`: NodeName + state machine type combination
- `et`: Total elapsed time in milliseconds per hour bucket
- High `et` across many SMs → Systemic control plane overload
- High `et` for only this request's SM → Issue specific to this operation
