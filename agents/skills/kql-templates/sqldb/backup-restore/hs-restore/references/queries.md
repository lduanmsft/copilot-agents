# Kusto Query Reference: Hyperscale (VLDB) Restore Investigation

This file documents all KQL queries used by the `hs-restore` skill. Every query is copied verbatim from `investigation-flow.md` — do NOT modify, rewrite, or regenerate any query.

## Table of Contents

- [Input Resolution](#input-resolution)
  - [QHR00A — Find request_id by restoreId](#qhr00a)
  - [QHR00B — Find request_id by server/database](#qhr00b)
  - [QHR00C — Time range heuristics](#qhr00c)
- [Main Trunk](#main-trunk)
  - [QHR10 — Operation Overview](#qhr10)
  - [QHR15 — Target Database Drop Check](#qhr15)
  - [QHR20 — Restore Step Progress](#qhr20)
  - [QHR30 — VldbRestoreMetrics](#qhr30)
- [Shared Queries](#shared-queries)
  - [QHR40A — Exception Counts During Phase](#qhr40a)
  - [QHR40B — Sample Exception Details](#qhr40b)
  - [QHR50 — FSM Throttling](#qhr50)
  - [QHR60 — Replica Creation Delays](#qhr60)
  - [QHR70 — Stuck App Detection (FSM Outliers)](#qhr70)
  - [QHR80 — WinFabLogs Placement Check](#qhr80)
  - [QHR100 — Restore Orchestrator State Flow](#qhr100)
  - [QHR110 — Restore Plan Generation](#qhr110)
  - [QHR120 — Destage Progress — Source DB](#qhr120)
  - [QHR130 — Storage Calls](#qhr130)
- [Branch A: App Creation](#branch-a-app-creation)
  - [QHR90 — App Placement Failures](#qhr90)
- [Branch B: Data Copy](#branch-b-data-copy)
  - [QHR190 — Blob Copy Operations](#qhr190)
- [Branch C: Redo](#branch-c-redo)
  - [QHR140 — Restored Compute ErrorLog](#qhr140)
  - [QHR150 — Recovery Traces](#qhr150)
  - [QHR160 — RBPEX Placement Errors](#qhr160)
  - [QHR170 — Xlog/LogReplica Traces](#qhr170)
  - [QHR180 — Long Page Redo Summary](#qhr180)

## Format Conventions

- **Parameters**: `{parameter_name}` — substitute at runtime
- **Tool**: All queries via `mcp_sqlops_query_kusto`

---

## Input Resolution

<a id="qhr00a"></a>
### QHR00A — Find request_id by restoreId

**Purpose**: Resolve a `restore_id` (restore-specific GUID) to the management operation `request_id`.
**When**: User or ICM provides a `restoreId` but not the `request_id`.
**Table**: `MonManagementOperations`

| Parameter | Source |
|-----------|--------|
| `{start_time}` | User-provided or ICM heuristic (`icm_created - 7d`) |
| `{end_time}` | User-provided or `icm_created` |
| `{restore_id}` | User input or ICM custom fields |

```kusto
MonManagementOperations
| where TIMESTAMP between (datetime({start_time}) .. datetime({end_time}))
| where operation_type == 'CreateRestoreRequest'
| where operation_parameters contains '{restore_id}'
| where event == 'management_operation_start'
| project TIMESTAMP, request_id, operation_type,
    RestoreId = extract('<RestoreId>([^<]+)</RestoreId>', 1, operation_parameters),
    SourceServer = extract('<SourceLogicalServerName>([^<]+)</SourceLogicalServerName>', 1, operation_parameters),
    SourceDb = extract('<SourceLogicalDatabaseName>([^<]+)</SourceLogicalDatabaseName>', 1, operation_parameters),
    TargetServer = extract('<TargetLogicalServerName>([^<]+)</TargetLogicalServerName>', 1, operation_parameters),
    TargetDb = extract('<TargetLogicalDatabaseName>([^<]+)</TargetLogicalDatabaseName>', 1, operation_parameters)
| sort by TIMESTAMP desc
```

**Analysis**: Use the returned `request_id` to proceed with the investigation. If multiple results, disambiguate (see QHR00C).

---

<a id="qhr00b"></a>
### QHR00B — Find request_id by server name

**Purpose**: Resolve server name to `request_id` when no `restoreId` or `request_id` is available.
**When**: Manual ICM or user provides server name only (no database name).
**Table**: `MonManagementOperations`

| Parameter | Source |
|-----------|--------|
| `{start_time}` | ICM heuristic (`icm_created - 7d`) or user-provided |
| `{end_time}` | `icm_created + 1d` or user-provided |
| `{server_name}` | Logical server name |

```kusto
MonManagementOperations
| where TIMESTAMP between (datetime({start_time}) .. datetime({end_time}))
| where operation_type == 'CreateRestoreRequest'
| where operation_parameters contains '{server_name}'
| where event == 'management_operation_start'
| project TIMESTAMP, request_id, operation_type,
    RestoreId = extract('<RestoreId>([^<]+)</RestoreId>', 1, operation_parameters),
    SourceServer = extract('<SourceLogicalServerName>([^<]+)</SourceLogicalServerName>', 1, operation_parameters),
    SourceDb = extract('<SourceLogicalDatabaseName>([^<]+)</SourceLogicalDatabaseName>', 1, operation_parameters),
    TargetServer = extract('<TargetLogicalServerName>([^<]+)</TargetLogicalServerName>', 1, operation_parameters),
    TargetDb = extract('<TargetLogicalDatabaseName>([^<]+)</TargetLogicalDatabaseName>', 1, operation_parameters)
| sort by TIMESTAMP desc
```

**Analysis**: If 0 results → widen time range or ask user. If >1 result → filter by `TargetDb` using QHR00B2, or present to user for selection. If >10 → ask for narrower time range.

---

<a id="qhr00b2"></a>
### QHR00B2 — Find request_id by server and database name

**Purpose**: Resolve server + database name to `request_id` for more precise matching.
**When**: Both server name AND database name are available. Prefer over QHR00B when database name is known.
**Table**: `MonManagementOperations`

| Parameter | Source |
|-----------|--------|
| `{start_time}` | ICM heuristic (`icm_created - 7d`) or user-provided |
| `{end_time}` | `icm_created + 1d` or user-provided |
| `{server_name}` | Logical server name |
| `{database_name}` | Logical database name |

```kusto
MonManagementOperations
| where TIMESTAMP between (datetime({start_time}) .. datetime({end_time}))
| where operation_type == 'CreateRestoreRequest'
| where operation_parameters contains '{server_name}' and operation_parameters contains '{database_name}'
| where event == 'management_operation_start'
| project TIMESTAMP, request_id, operation_type,
    RestoreId = extract('<RestoreId>([^<]+)</RestoreId>', 1, operation_parameters),
    SourceServer = extract('<SourceLogicalServerName>([^<]+)</SourceLogicalServerName>', 1, operation_parameters),
    SourceDb = extract('<SourceLogicalDatabaseName>([^<]+)</SourceLogicalDatabaseName>', 1, operation_parameters),
    TargetServer = extract('<TargetLogicalServerName>([^<]+)</TargetLogicalServerName>', 1, operation_parameters),
    TargetDb = extract('<TargetLogicalDatabaseName>([^<]+)</TargetLogicalDatabaseName>', 1, operation_parameters)
| sort by TIMESTAMP desc
```

**Analysis**: If 0 results → widen time range or ask user. If >1 result → present to user for selection. If >10 → ask for narrower time range.

---

<a id="qhr00c"></a>
### QHR00C — Time Range Heuristics

**Purpose**: Determine appropriate time range for input resolution queries based on input source.
**When**: Always — before running QHR00A or QHR00B.

No KQL query — this is a rule-based decision:

| Source | Start time | End time |
|--------|-----------|----------|
| **Automated ICM** | `icm.impactStartTime - 3d` | `now()` (or `icm.createdDate + 1d`) |
| **Manual ICM** | `icm.createdDate - 7d` | `icm.createdDate + 1d` |
| **User prompt** | Ask user for approximate time | Ask user |

**Disambiguation logic**:
1. If only **1 result** → use it directly.
2. If **multiple results** and ICM has `TargetLogicalDatabaseName` → filter by `TargetDb`.
3. If still **multiple** → present full row to user and ask them to choose.
4. If **>10 results** → ask user to provide a narrower time range.
5. If **0 results** → widen time range, or ask user for more details.
6. If none of the above help → ask the user explicitly to provide the `request_id`.

---

<a id="qhr00d"></a>
### QHR00D — Resolve target_logical_database_id from request_id

**Purpose**: Extract `target_logical_database_id` from FSM transition messages when not directly available.
**When**: Stuck restore investigations where `target_logical_database_id` is needed but unavailable.
**Table**: MonManagement

```kusto
MonManagement
| where request_id == toupper("{request_id}")
| where event contains "fsm_transition"
| where message contains "logical_db_name"
| parse message with * "logical_db_name=" target_logical_database_id "," *
| where isnotempty(target_logical_database_id)
| summarize by target_logical_database_id
| take 1
```

**Analysis**: Returns the `target_logical_database_id` parsed from FSM transition messages. If 0 results → the restore may not have progressed far enough to emit this field; try QHR10 `TargetLogicalDbId` instead.

---

## Main Trunk

<a id="qhr10"></a>
### QHR10 — Operation Overview

**Purpose**: Establish timeline, status, and extract restore-specific IDs. Save variables for all subsequent queries.
**When**: Always first (once `request_id` is resolved).
**Table**: `MonManagementOperations`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 (input resolution) |

```kusto
MonManagementOperations
| where request_id == '{request_id}'
| where event !in ('management_operation_rads_signal', 'management_operation_released', 'management_operation_progress')
| project TIMESTAMP, event, request_id, operation_type, operation_parameters, operation_result, state, error_message
```

**Variables to extract from `operation_parameters` XML:**

| Variable | XML Key | Use |
|----------|---------|-----|
| `restore_id` | `<RestoreId>` | State machine traces, progress, exceptions, blob copy |
| `source_logical_database_id` | `<SourceLogicalDatabaseId>` | Blob copy, destage progress, XStore queries |
| `source_logical_server_name` | `<SourceLogicalServerName>` | Context, display |
| `source_logical_database_name` | `<SourceLogicalDatabaseName>` | Context, display |
| `target_logical_server_name` | `<TargetLogicalServerName>` | Context, display |
| `target_logical_database_name` | `<TargetLogicalDatabaseName>` | Context, display |
| `target_edition` | `<TargetEdition>` | Edition (Premium, Hyperscale, etc.) |
| `target_slo` | `<TargetServiceLevelObjectiveName>` | SLO (HS_Gen5_2, etc.) |
| `point_in_time` | `<PointInTime>` | Requested restore point |
| `source_database_dropped_time` | `<SourceDatabaseDroppedTime>` | If set → restoring a deleted/dropped database |
| `restore_start_time` | TIMESTAMP of `management_operation_start` event | Time-bounded TR queries |
| `restore_end_time` | TIMESTAMP of completion event, or `now()` if stuck | Time-bounded TR queries |

> **Note**: `target_logical_database_id` is NOT in `operation_parameters`. It appears in `operation_result` XML of `management_operation_success` event under `<LogicalDatabaseId>`. For stuck restores, use the FSM resolution query in SKILL.md.

**Analysis**: See `references/knowledge.md` for error classification rules (User Error vs System Error patterns) and status determination logic.

---

<a id="qhr15"></a>
### QHR15 — Target Database Drop Check

**Purpose**: Check if the target logical database was dropped while the restore was in progress — which would cause an obscure restore failure.
**When**: After QHR10, only when the restore **failed** (not needed for succeeded or stuck).
**Table**: `MonManagementOperations`

| Parameter | Source |
|-----------|--------|
| `{restore_start_time}` | QHR10 (TIMESTAMP of `management_operation_start`) |
| `{restore_end_time}` | QHR10 (TIMESTAMP of completion event) |
| `{target_logical_database_name}` | QHR10 (`operation_parameters` XML) |

```kusto
MonManagementOperations
| where TIMESTAMP between (datetime("{restore_start_time}") .. datetime("{restore_end_time}"))
| where operation_parameters contains '{target_logical_database_name}'
| where operation_type in ('DropLogicalDatabase', 'DeleteDatabase')
| project originalEventTimestamp, event, operation_type, operation_parameters
| order by originalEventTimestamp desc
```

**Analysis**:
- **Results present** → 🚩 Target database was dropped during the restore window. Likely root cause. Report drop timestamp, operation type, and caller identity from `operation_parameters`.
- **Empty results** → No target database drop detected. Proceed to QHR20.

---

<a id="qhr20"></a>
### QHR20 — Restore Step Progress

**Purpose**: Trace the restore through its 4 phases to identify where time was spent or where it got stuck.
**When**: After QHR10, regardless of status (Succeeded, Failed, or Stuck).
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 (input resolution) |

```kusto
MonManagement
| where request_id == toupper('{request_id}')
| where message_scrubbed_resource_name != ""
| project TIMESTAMP, message_scrubbed_resource_name
| sort by TIMESTAMP asc
```

**Analysis**: See `references/knowledge.md` for the 4-phase model and phase detection rules. Key milestones:
1. Phase 1 complete: `"Restore plan was created successfully in {N} seconds."`
2. Phase 2 complete: `"Restore target db's apps were created. Beginning to start copy of snapshot and destaged blobs."`
3. Phase 3 complete: `"Copy of {N} page server snapshot and XLog files finished successfully."`
4. Phase 4 complete: `"The database has been restored successfully."`

---

<a id="qhr30"></a>
### QHR30 — VldbRestoreMetrics

**Purpose**: Single-row summary of restore durations per phase, source/target configuration, and redo size. This is the primary metrics query for determining bottleneck phase and branching decisions.
**When**: After QHR10, for any status (Succeeded, Failed, or Stuck).
**Tables**: `MonManagement` + `MonSQLSystemHealth` + `MonAnalyticsDBSnapshot` + `MonManagementOperations`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |
| `{source_logical_database_id}` | QHR10 (`operation_parameters` XML) |
| `{target_logical_database_id}` | QHR10 (`operation_result` XML) or QHR00D (stuck restores) |
| `{restore_id}` | QHR10 (`operation_parameters` XML) |

```kusto
MonManagement
| where request_id == toupper("{request_id}")
| where event contains "restore_request_progress"
| where message_scrubbed_resource_name contains "Restore plan was created successfully"
    or message_scrubbed_resource_name contains "Restore target db's apps were created."
    or message_scrubbed_resource_name contains "page server snapshot and XLog files finished successfully."
    or message_scrubbed_resource_name contains "The database has been restored successfully."
    or message_scrubbed_resource_name contains "Xlog's snipped Bsn was verified."
| project originalEventTimestamp, request_id = toupper(request_id),
    RestoreRequestId = toupper(restore_request_id), message_scrubbed_resource_name
| order by originalEventTimestamp asc
| extend restorePlanGeneratedTime = iff(message_scrubbed_resource_name contains "Restore plan was created successfully", originalEventTimestamp, todatetime(1))
| extend restoreAppsCreatedTime = iff(message_scrubbed_resource_name contains "Restore target db's apps were created.", originalEventTimestamp, todatetime(1))
| extend copyDoneTime = iff(message_scrubbed_resource_name contains "page server snapshot and XLog files finished successfully.", originalEventTimestamp, todatetime(1))
| extend restoreFinishedTime = iff(message_scrubbed_resource_name contains "The database has been restored successfully.", originalEventTimestamp, todatetime(1))
| extend maxPSBSN = 0, xlogBSN = 0
| parse message_scrubbed_resource_name with "Xlog's snipped Bsn was verified. Max PS BSN(" maxPSBSN ") was less than or equal to xlog snip BSN: " xlogBSN ".MinPageServerLsn" *
| extend RedoSizeGB = round(((((tolong(xlogBSN) - tolong(maxPSBSN)) * 512.0) / 1024.0) / 1024.0) / 1024.0, 3)
| project-away message_scrubbed_resource_name
| summarize
    restorePlanGeneratedTime = minif(restorePlanGeneratedTime, restorePlanGeneratedTime != todatetime(1)),
    restoreAppsCreatedTime = max(restoreAppsCreatedTime),
    copyDoneTime = max(copyDoneTime),
    restoreFinishedTime = max(restoreFinishedTime),
    RedoSizeGB = max(RedoSizeGB)
    by RequestId = toupper(request_id), RestoreRequestId
| extend AppCreationTime = iff(isnotempty(restorePlanGeneratedTime) and restoreAppsCreatedTime != todatetime(1),
    datetime_diff('Minute', restoreAppsCreatedTime, restorePlanGeneratedTime), 0)
| extend CopyTime = iff(restoreAppsCreatedTime != todatetime(1) and copyDoneTime != todatetime(1),
    datetime_diff('Minute', copyDoneTime, restoreAppsCreatedTime), 0)
| extend RedoTime = iff(copyDoneTime != todatetime(1) and restoreFinishedTime != todatetime(1),
    datetime_diff('Minute', restoreFinishedTime, copyDoneTime), 0)
| join kind=inner (
    MonSQLSystemHealth
    | where TIMESTAMP > ago(10d)
    | where AppTypeName == "Worker.Vldb.Storage" and event contains "metadata"
        and logical_database_guid == toupper("{target_logical_database_id}")
    | summarize arg_max(TIMESTAMP, instance_rg_size)
        by target_logical_database_id = toupper(logical_database_guid), AppName
    | extend 1TBPS = iff(instance_rg_size == 'SQLDB_HSPS_2', 1, 0)
    | summarize CountOfPS = count(), NumberOf1TBPS = sum(1TBPS)
        by target_logical_database_id
    | project CountOfPS, NumberOf1TBPS,
        RestoreRequestId = toupper("{restore_id}")
) on $left.RestoreRequestId == $right.RestoreRequestId
| join kind=inner (
    MonAnalyticsDBSnapshot
    | where logical_database_id =~ toupper("{source_logical_database_id}")
    | summarize max(TIMESTAMP)
        by active_backup_storage_type, SLO = service_level_objective, logical_database_id
    | project SourceActiveBackupStorageType = active_backup_storage_type,
        SourceSLO = SLO,
        RestoreRequestId2 = toupper("{restore_id}")
) on $left.RestoreRequestId == $right.RestoreRequestId2
| join kind=inner (
    MonManagementOperations
    | where request_id == toupper("{request_id}")
    | where event == "management_operation_start" and operation_type == 'CreateRestoreRequest'
    | extend TargetSLO = tostring(parse_xml(operation_parameters).InputParameters.TargetServiceLevelObjectiveName)
    | extend TargetDBStorageAccountType = tostring(parse_xml(operation_parameters).InputParameters.TargetStorageAccountTypeForBackup)
    | project RequestId = toupper(request_id), TargetSLO, TargetDBStorageAccountType
) on $left.RequestId == $right.RequestId
| project AppCreationTime, CopyTime, RedoTime,
    restorePlanGeneratedTime, restoreAppsCreatedTime, copyDoneTime, restoreFinishedTime,
    CountOfPS, NumberOf1TBPS, SourceActiveBackupStorageType, TargetDBStorageAccountType,
    SourceSLO, TargetSLO
```

**Analysis**: See `references/knowledge.md` for interpretation rules (high latency flags, storage type mismatch, large database flags, redo size). Save `restorePlanGeneratedTime`, `restoreAppsCreatedTime`, `copyDoneTime`, `restoreFinishedTime` for phase time windows.

---

## Shared Queries

<a id="qhr40a"></a>
### QHR40A — Exception Counts During Phase

**Purpose**: Identify exception types during the bottleneck phase.
**When**: All branches (A, B, C). Substitute `{phase_start}` and `{phase_end}` per phase.
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |
| `{phase_start}` | QHR30 phase time windows |
| `{phase_end}` | QHR30 phase time windows |

**Phase Time Windows:**

| Phase | `{phase_start}` | `{phase_end}` |
|-------|-----------------|----------------|
| Pre-plan / Destage (stuck only) | `restore_start_time` (QHR10) | `now()` |
| App Creation (Branch A) | `restorePlanGeneratedTime` | `restoreAppsCreatedTime` (or `now()` if stuck) |
| Data Copy (Branch B) | `restoreAppsCreatedTime` | `copyDoneTime` (or `now()` if stuck) |
| Redo (Branch C) | `copyDoneTime` | `restoreFinishedTime` (or `now()` if stuck) |

```kusto
MonManagement
| where request_id =~ "{request_id}"
| where TIMESTAMP between (datetime("{phase_start}") .. datetime("{phase_end}"))
| where isnotempty(exception_type)
| summarize count() by exception_type
```

**Analysis**: High counts of `TimeoutException` → repeated timeouts. `FiniteStateMachineDeadlockVictimException` → FSM lock contention (transient). Zero rows → no exceptions; delay caused by waiting not errors.

---

<a id="qhr40b"></a>
### QHR40B — Sample Exception Details Per Type

**Purpose**: Get one representative exception per type with message, stack trace, and context.
**When**: After QHR40A shows exceptions. All branches.
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |
| `{phase_start}` | QHR30 phase time windows |
| `{phase_end}` | QHR30 phase time windows |

```kusto
MonManagement
| where request_id =~ "{request_id}"
| where TIMESTAMP between (datetime("{phase_start}") .. datetime("{phase_end}"))
| where isnotempty(exception_type)
| summarize arg_min(TIMESTAMP, exception_message, stack_trace, message) by exception_type
| extend exception_message = substring(exception_message, 0, 500)
| extend stack_trace = substring(stack_trace, 0, 1000)
| extend message = substring(message, 0, 800)
```

**Analysis**: Review `message` first (most actionable — HRESULT codes, FSM keys, PII error IDs). See `references/knowledge.md` for exception pattern reference per phase.

---

<a id="qhr50"></a>
### QHR50 — FSM Throttling

**Purpose**: Check if FSM work-item throttling caused delays — the management service deprioritized work items.
**When**: All branches. Only applies to slow/stuck restores (won't cause outright failure).
**Table**: `MonManagementFSMInternal`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |
| `{phase_start}` | QHR30 phase time windows |
| `{phase_end}` | QHR30 phase time windows |

```kusto
MonManagementFSMInternal
| where request_id =~ "{request_id}"
| where TIMESTAMP between (datetime("{phase_start}") .. datetime("{phase_end}"))
| where event == "fsm_dequeue_work"
| where priority != 1
| project originalEventTimestamp, priority
| summarize min(originalEventTimestamp), max(originalEventTimestamp) by priority
```

**Analysis**:
- **Empty** → No FSM throttling. Priority was normal (1).
- **Results** → Throttling occurred. Duration = `max - min`. Priority > 1 = deprioritized. Duration > 30 min → flag as **"Significant FSM Throttling"**.

---

<a id="qhr60"></a>
### QHR60 — Replica Creation Delays

**Purpose**: Detect stuck ServiceFabric replica creation for HS apps (Page Servers, Compute, XLog). `num_running_replicas` never reaches `num_replicas_wait_for`.
**When**: App Creation (Branch A) and Redo (Branch C) only. Not applicable to Data Copy.
**Table**: `MonFabricClient`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |
| `{phase_start}` | QHR30 phase time windows |
| `{phase_end}` | QHR30 phase time windows |

```kusto
MonFabricClient
| where request_id =~ "{request_id}"
| where TIMESTAMP between (datetime("{phase_start}") .. datetime("{phase_end}"))
| where event contains "debug"
| where num_running_replicas < num_replicas_wait_for
| summarize min(originalEventTimestamp), max(originalEventTimestamp) by min_replica_set_size, target_replica_set_size, num_running_replicas, num_replicas_wait_for, fabric_service_uri, request_id
| project fabric_service_uri, WaitingTimeForReplica = (max_originalEventTimestamp - min_originalEventTimestamp)
| where WaitingTimeForReplica > (30m)
```

**Analysis**:
- **Empty** → No replica creation delays. This ServiceFabric issue is not a factor.
- **Results** → Stuck replicas. Report `fabric_service_uri` (which app) and `WaitingTimeForReplica`. Known mitigation: restart stuck app processes (per ICM 728004373, ICM 738740724).

---

<a id="qhr70"></a>
### QHR70 — Stuck App Detection (FSM Outliers)

**Purpose**: Identify apps with abnormally high FSM state transition counts — churning (repeatedly failing/retrying) rather than progressing.
**When**: All branches.
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |
| `{phase_start}` | QHR30 phase time windows |
| `{phase_end}` | QHR30 phase time windows |

```kusto
MonManagement
| where request_id == "{request_id}"
| where TIMESTAMP between (datetime("{phase_start}") .. datetime("{phase_end}"))
| where state_machine_type == 'FabricServiceStateMachine'
| summarize count_ = count() by state_machine_type, keys
| extend joinKey = 1
| join kind=inner (
    MonManagement
    | where request_id == "{request_id}"
    | where TIMESTAMP between (datetime("{phase_start}") .. datetime("{phase_end}"))
    | where state_machine_type == 'FabricServiceStateMachine'
    | summarize count_ = count() by state_machine_type, keys
    | summarize mean_count = avg(count_), stddev_count = stdev(count_)
    | extend joinKey = 1
) on joinKey
| where stddev_count > 0
| extend zscore = (count_ - mean_count) / stddev_count
| where zscore > 2
| order by count_ desc
| extend tenant_ring = extract(@"^([^,]+)", 1, keys)
| extend app_type = extract(@"fabric:/Worker\.Vldb\.(\w+)", 1, keys)
| extend app_name = extract(@"Worker\.Vldb\.\w+/([^/]+)", 1, keys)
| extend user_db = extract(@"SQL\.UserDb/([a-f0-9\-]+)$", 1, keys)
| project state_machine_type, tenant_ring, app_type, app_name, user_db, Count = count_, zscore = round(zscore, 2)
```

**Analysis**:
- **Empty** → No outliers. All apps behaved normally.
- **Results** → Outlier apps. Save `tenant_ring`, `app_name`, `user_db` for QHR80. Storage = page server, Compute = SQL node, XLog = transaction log.

---

<a id="qhr80"></a>
### QHR80 — WinFabLogs Placement Check

**Purpose**: For each outlier from QHR70, check WinFabLogs for Service Fabric placement failures.
**When**: App Creation (Branch A) and Redo (Branch C) only. Run once per QHR70 outlier row.
**Table**: `WinFabLogs`

| Parameter | Source |
|-----------|--------|
| `{tenant_ring}` | QHR70 outlier row |
| `{app_name}` | QHR70 outlier row |
| `{user_db}` | QHR70 outlier row |
| `{phase_start}` | QHR30 phase time windows |
| `{phase_end}` | QHR30 phase time windows |

```kusto
WinFabLogs
| where ClusterName == '{tenant_ring}'
| where TIMESTAMP between (datetime("{phase_start}") .. datetime("{phase_end}"))
| where Text contains '{app_name}' or Text contains "{user_db}"
| where Text contains "could not be placed"
| summarize
    FirstSeen = min(TIMESTAMP),
    LastSeen = max(TIMESTAMP),
    OccurrenceCount = count(),
    SampleText = take_any(Text)
| extend Duration = LastSeen - FirstSeen
```

**Analysis**:
- **Empty** → No fabric placement failures for this app.
- **Results** → Placement failures confirmed. Duration > 30 min → flag as **"Significant App Placement Issue"**. Common causes: node capacity exhaustion, fault domain constraints, node type mismatch, maintenance windows.

---

<a id="qhr100"></a>
### QHR100 — Restore Orchestrator State Flow

**Purpose**: Complete state-by-state progression of the `VldbRestoreRequestStateMachine`. Time gaps between rows reveal bottleneck phases.
**When**: All branches.
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |

```kusto
MonManagement
| where request_id == toupper("{request_id}")
| where state_machine_type == "VldbRestoreRequestStateMachine"
| where event == "fsm_executed_action"
| where old_state != new_state
| project originalEventTimestamp, old_state, new_state, action, elapsed_time_milliseconds
| sort by originalEventTimestamp asc
```

**Analysis**: Expected ~15–17 rows. State sequence: `RestoreStart` → `PerformingSafetyChecks` → `WaitingForDestaging` → `CreatingRestorePlan` → ... → `Ready`. Gaps between rows = phase durations. If sequence stops mid-way → restore stuck at last state.

---

<a id="qhr110"></a>
### QHR110 — Restore Plan Generation

**Purpose**: Show restore plan details — which page server snapshots were selected, LSN ranges, time coverage.
**When**: All branches.
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{restore_id}` | QHR10 (`operation_parameters` XML) |

```kusto
MonManagement
| where restore_request_id =~ "{restore_id}"
| where event contains "vldb_restore_plan_generation_troubleshooting"
| project TIMESTAMP, restore_request_id, message_systemmetadata
| extend PotentialSnapshotInfo = iif(message_systemmetadata contains "potential snapshot", message_systemmetadata, "")
| extend GeoRestorePlanInfo = iif(message_systemmetadata !contains "potential snapshot", message_systemmetadata, "")
| project TIMESTAMP, restore_request_id, PotentialSnapshotInfo, GeoRestorePlanInfo
| extend PSId = extract('PageServerId: ([0-9]+),',1, PotentialSnapshotInfo)
| extend PageServerId = iff(PSId == "", extract('PageServerId: ([0-9]+) O',1, PotentialSnapshotInfo), PSId)
| extend ReplicaId = extract('ReplicaId: ([0-9]+),',1, PotentialSnapshotInfo)
| extend OldestTxLsn = extract('OldTranLSN: (.*?),',1, PotentialSnapshotInfo)
| extend BeginLsn = extract('BeginLSN: (.*?),',1, PotentialSnapshotInfo)
| extend BeginTime = extract('BeginTime: (.*?),',1, PotentialSnapshotInfo)
| extend EndLsn = extract('EndLSN: (.*?),',1, PotentialSnapshotInfo)
| extend EndTime = extract('EndTime: (.*?),',1, PotentialSnapshotInfo)
| extend SnapshotTime = todatetime(extract('SnapshotTime: (.*?)]',1, PotentialSnapshotInfo))
| project TIMESTAMP, GeoRestorePlanInfo, SnapshotTime, PageServerId, ReplicaId, OldestTxLsn, BeginLsn, BeginTime, EndLsn, EndTime, restore_request_id
```

**Analysis**: One row per page server snapshot. Check snapshot freshness, LSN ranges. Empty → restore never reached `CreatingRestorePlan` state.

---

<a id="qhr120"></a>
### QHR120 — Destage Progress — Source DB

**Purpose**: Track XLog destaging progress for the source database. Slow destaging delays the entire restore.
**When**: All branches. Especially important during `WaitingForDestaging` phase.
**Tables**: `MonSocrates` + `MonXlogSrv`

| Parameter | Source |
|-----------|--------|
| `{source_logical_database_id}` | QHR10 (`operation_parameters` XML) |
| `{restoreStartTime}` | QHR10 (TIMESTAMP of start event) |
| `{restoreFinishedTime}` | QHR30 (`restoreFinishedTime`, or `now()` if still running) |

```kusto
MonSocrates
| where logical_db_id contains "{source_logical_database_id}"
    and AppTypeName == "Vldb.XLog"
| project AppName
| take 1
| join (
    MonXlogSrv
    | where event contains "destage_progress"
    | where originalEventTimestamp >= datetime("{restoreStartTime}")
        and originalEventTimestamp <= datetime("{restoreFinishedTime}")
    | project originalEventTimestamp, AppName, NodeName, collect_current_thread_id,
        first_incomplete_vlf, destage_bsn, last_destaged_bsn_timestamp,
        last_destage_block_bsn, lz_flush_bsn
) on AppName
| project originalEventTimestamp, AppName, NodeName, collect_current_thread_id,
    first_incomplete_vlf, last_destage_block_bsn,
    last_destaged_bsn_timestamp, destage_bsn, lz_flush_bsn
| sort by originalEventTimestamp asc
```

**Analysis**: `destage_bsn` should advance. If stalled → destage bottleneck on source XLog. `NodeName` changes → XLog failover during restore.

---

<a id="qhr130"></a>
### QHR130 — Storage Calls

**Purpose**: Surface Azure Storage API calls — blob copy, snapshot, container operations. Catches slow calls, failures, and unexpected results.
**When**: All branches. Especially useful during Data Copy.
**Table**: `MonBlobClient`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |

```kusto
MonBlobClient
| where request_id =~ "{request_id}"
| where isnotempty(azure_storage_request_id) or isnotempty(azure_storage_client_request_id)
| project originalEventTimestamp, azure_storage_request_id, azure_storage_client_request_id,
    api_name, event, elapsed_time_milliseconds, uri, storage_container_name,
    parameters_with_scrubbed_values_systemmetadata, parameters_with_scrubbed_values_resource_name,
    exception, request_result
| sort by originalEventTimestamp asc
```

**Analysis**: Scan for non-empty `exception` or failed `request_result`. `ServerBusy`/`ThrottlingException` → storage throttling. `elapsed_time_milliseconds > 30000` → slow call. See `references/knowledge.md` for common error patterns.

---

## Branch A: App Creation

<a id="qhr90"></a>
### QHR90 — App Placement Failures (CreationFailed State)

**Purpose**: Check if HS apps entered `CreationFailed` state — PLB failed to place the fabric service on a node.
**When**: Branch A only. After shared queries.
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Layer 0 |
| `{restoreAppsCreatedTime}` | QHR30 |

```kusto
MonManagement
| where request_id =~ "{request_id}"
| where TIMESTAMP < datetime("{restoreAppsCreatedTime}")
| where new_state == 'CreationFailed'
| where isnotempty(keys)
| summarize by TIMESTAMP, keys
| extend tenant_ring = extract(@"^([^,]+)", 1, keys)
| extend app_type = extract(@"fabric:/Worker\.Vldb\.(\w+)", 1, keys)
| extend app_name = extract(@"Worker\.Vldb\.\w+/([^/]+)", 1, keys)
| summarize StartTime = min(TIMESTAMP), EndTime = max(TIMESTAMP) by tenant_ring, app_name, app_type
```

**Analysis**:
- **Empty** → No apps entered CreationFailed. Delays caused by slowness not placement failure.
- **Results** → Placement failures occurred. Duration > 30 min → flag. Common types: Compute (no capacity), Storage (page server nodes full), XLog (xlog nodes full).

---

## Branch B: Data Copy

<a id="qhr190"></a>
### QHR190 — Blob Copy Operations

**Purpose**: Per-page-server blob copy status — source/target blobs, storage accounts, copy status, page server sizes.
**When**: Branch B only. After shared queries.
**Tables**: `MonBlobClient` + `MonSQLXStore`

| Parameter | Source |
|-----------|--------|
| `{source_logical_database_id}` | QHR10 (`operation_parameters` XML) |
| `{target_logical_database_id}` | QHR10 (`operation_result` XML, or FSM resolution for stuck restores) |

```kusto
MonBlobClient
| where event contains "blobclient_copy_blob_from_snapshot"
    and source_file_path_format contains "{source_logical_database_id}"
    and target_file_name contains "{target_logical_database_id}"
| project originalEventTimestamp,
    PageServerId = tostring(split(tostring(split(target_file_name, "_")[1]), ".")[0]),
    status, event, copy_id,
    SourceStorageAccount = tostring(split(tostring(split(uri, "/")[2]), ".")[0]),
    SourceContainer = source_storage_container_name,
    SourceFileName = tostring(split(source_file_path_format, "##")[1]),
    TargetContainer = storage_container_name,
    TargetFileName = target_file_name,
    bytes_copied, completion_time, status_description
| join kind=inner (
    MonSQLXStore
    | where file_path contains "{target_logical_database_id}"
    | where file_path !contains "snapshot" and isnotempty(blob_size) and file_path !contains "ldf"
    | project file_path, blob_size,
        PageServerId = tostring(split(tostring(split(file_path, "_")[1]), ".")[0])
    | distinct PageServerId, blob_size
) on PageServerId
| project originalEventTimestamp, PageServerId = toint(PageServerId), blob_size,
    PageServerSize = iff(isempty(blob_size), "32GB",
        iff(blob_size / (1024 * 1024 * 1024) <= 128, "128GB", "1TB")),
    event, copy_id, SourceStorageAccount,
    SourceContainer, SourceFileName, TargetContainer, TargetFileName, status_description
| sort by originalEventTimestamp asc
```

**Analysis**: Group by `PageServerId`. `status_description = "failed"` → copy failures. Multiple failures for same PS → persistent issue. Cross-region `SourceStorageAccount` → inherently slower.

---

## Branch C: Redo

<a id="qhr140"></a>
### QHR140 — Restored Compute ErrorLog

**Purpose**: SQL error log entries from the restored compute during Redo phase. Catches recovery failures, assertions, engine errors.
**When**: Branch C only. After shared queries.
**Tables**: `MonSocrates` + `MonSQLSystemHealth`

| Parameter | Source |
|-----------|--------|
| `{target_logical_database_id}` | QHR10 (`operation_result` XML or FSM resolution) |
| `{copyDoneTime}` | QHR30 |
| `{restoreFinishedTime}` | QHR30 (or `now()` if stuck) |

```kusto
MonSocrates
| where logical_db_id contains "{target_logical_database_id}"
    and AppTypeName contains "Compute"
| distinct AppName
| join (
    MonSQLSystemHealth
    | where event == "systemmetadata_written"
        and message !contains "Started XE session"
        and message !contains "Extended XE"
        and message !contains "Skip Initialization"
        and message !contains "XE_XML Select nodes for Targets failed"
        and message !contains "Failed to start XE session"
    | project originalEventTimestamp, NodeName, AppName, message, event
) on AppName
| project originalEventTimestamp, NodeName, message, AppName
| where originalEventTimestamp >= datetime("{copyDoneTime}")
    and originalEventTimestamp <= datetime("{restoreFinishedTime}")
| sort by originalEventTimestamp asc
```

**Analysis**: Look for `Recovery is x% complete`. `Error:` / `HRESULT` / `assertion` → engine error. `Cannot recover database` → fatal.

---

<a id="qhr150"></a>
### QHR150 — Recovery Traces

**Purpose**: Detailed recovery trace messages — progress, duration estimates, scan statistics.
**When**: Branch C only.
**Tables**: `MonSocrates` + `MonRecoveryTrace`

| Parameter | Source |
|-----------|--------|
| `{target_logical_database_id}` | QHR10 (`operation_result` XML or FSM resolution) |
| `{copyDoneTime}` | QHR30 |
| `{restoreFinishedTime}` | QHR30 (or `now()` if stuck) |

```kusto
MonSocrates
| where logical_db_id contains "{target_logical_database_id}"
    and AppTypeName contains "Compute"
| distinct AppName
| join (
    MonRecoveryTrace
    | where database_name contains "-"
    | where trace_message contains "recovery"
        or trace_message contains "Estimate"
        or trace_message contains "Scan Stats"
    | project originalEventTimestamp, AppName, NodeName, trace_message,
        database_name, database_id, participant_database_id, coordinator_database_id
) on AppName
| project originalEventTimestamp, NodeName, trace_message, AppName
| where originalEventTimestamp >= datetime("{copyDoneTime}")
    and originalEventTimestamp <= datetime("{restoreFinishedTime}")
| sort by originalEventTimestamp asc
```

**Analysis**: Recovery phases: Analysis → Redo → Undo → Complete. Stalled estimates → recovery struggling. Empty → verify AppName resolution.

---

<a id="qhr160"></a>
### QHR160 — RBPEX Placement Errors

**Purpose**: Detect RBPEX (SSD cache) placement errors on page servers during Redo. Forces fallback to remote storage reads.
**When**: Branch C only.
**Tables**: `MonSQLSystemHealth` + `MonSocrates`

| Parameter | Source |
|-----------|--------|
| `{target_logical_database_id}` | QHR10 (`operation_result` XML or FSM resolution) |
| `{copyDoneTime}` | QHR30 |
| `{restoreFinishedTime}` | QHR30 (or `now()` if stuck) |

```kusto
MonSQLSystemHealth
| where message contains "[Error] Rbpex"
    and event == "systemmetadata_written"
| where originalEventTimestamp >= datetime("{copyDoneTime}")
    and originalEventTimestamp <= datetime("{restoreFinishedTime}")
| project originalEventTimestamp, NodeName, AppName, message
| join kind=leftouter (
    MonSocrates
    | where logical_db_id contains "{target_logical_database_id}"
        and isnotempty(logical_database_name)
        and logical_database_name !contains "master"
    | project AppName, AppTypeName, logical_db_id, logical_database_name
    | distinct *
) on AppName
| project originalEventTimestamp, NodeName, AppName, AppTypeName, message,
    logical_db_id, logical_database_name
| sort by originalEventTimestamp asc
```

**Analysis**: RBPEX errors → SSD cache failures → slow redo from remote reads. Multiple errors on same `NodeName` → node SSD full. Escalate to Storage team if persistent.

---

<a id="qhr170"></a>
### QHR170 — Xlog/LogReplica Traces

**Purpose**: XLog server traces related to restore during Redo. Reveals log delivery issues, BSN gaps.
**When**: Branch C only.
**Tables**: `MonSocrates` + `MonXlogSrv`

| Parameter | Source |
|-----------|--------|
| `{target_logical_database_id}` | QHR10 (`operation_result` XML or FSM resolution) |
| `{copyDoneTime}` | QHR30 |
| `{restoreFinishedTime}` | QHR30 (or `now()` if stuck) |

```kusto
MonSocrates
| where logical_db_id contains "{target_logical_database_id}"
    and AppTypeName contains "log"
| distinct AppName
| join (
    MonXlogSrv
    | where event contains "xlog_output"
        and originalEventTimestamp >= datetime("{copyDoneTime}")
        and originalEventTimestamp <= datetime("{restoreFinishedTime}")
    | where message !contains "UCS Socket Duplication request received"
    | where message contains "restore"
    | project originalEventTimestamp, AppName, NodeName, collect_current_thread_id, message
) on AppName
| project originalEventTimestamp, AppName, NodeName, collect_current_thread_id, message
| sort by originalEventTimestamp asc
```

**Analysis**: Long gaps between rows → XLog stalled. `NodeName` changes → failover during redo. Empty → broaden filter by removing `message contains "restore"`.

---

<a id="qhr180"></a>
### QHR180 — Long Page Redo Summary

**Purpose**: Per-page-server redo summary — log redone (MB), time, read sources (broker/LZ/cache), disk tier.
**When**: Branch C only. Primary query for diagnosing slow redo.
**Tables**: `MonSocrates` + `MonSQLXStore` + `MonSQLSystemHealth`

| Parameter | Source |
|-----------|--------|
| `{target_logical_database_id}` | QHR10 (`operation_result` XML or FSM resolution) |
| `{copyDoneTime}` | QHR30 |
| `{restoreFinishedTime}` | QHR30 (or `now()` if stuck) |

```kusto
MonSocrates
| where originalEventTimestamp >= datetime("{copyDoneTime}")
    and originalEventTimestamp <= datetime("{restoreFinishedTime}")
| where AppTypeName == "Worker.Vldb.Storage"
| where logical_db_id contains "{target_logical_database_id}"
| where event == "rbio_redo_log_progress"
| summarize arg_min(current_bsn, originalEventTimestamp), arg_max(current_bsn, originalEventTimestamp)
    by logical_db_id, AppName, PageServerId = foreign_file_id, start_page_id
| extend RedoLogMB = round((current_bsn1 - current_bsn) * 512 / (1024 * 1024.0), 2),
    RedoTimeMinutes = datetime_diff('minute', originalEventTimestamp1, originalEventTimestamp)
| project AppName, PageServerId, start_page_id,
    minRedoBsn = current_bsn, maxRedoBsn = current_bsn1,
    RedoLogMB, RedoTimeMinutes,
    RedoBeginTime = originalEventTimestamp, RedoEndTime = originalEventTimestamp1
| join (
    MonSocrates
    | where originalEventTimestamp >= datetime("{copyDoneTime}")
        and originalEventTimestamp <= datetime("{restoreFinishedTime}")
    | where AppTypeName == "Worker.Vldb.Storage"
    | where logical_db_id contains "{target_logical_database_id}"
    | where event == "read_xlog_block_stats"
    | project originalEventTimestamp, AppName, NodeName, reads_from_broker, reads_from_lc, reads_from_lz
    | summarize total_reads_from_broker = sum(reads_from_broker),
        total_reads_from_lc = sum(reads_from_lc),
        total_reads_from_lz = sum(reads_from_lz)
        by AppName
) on AppName
| project AppName, PageServerId, start_page_id, minRedoBsn, maxRedoBsn,
    RedoLogMB, RedoTimeMinutes, RedoBeginTime, RedoEndTime,
    total_reads_from_broker, total_reads_from_lz, total_reads_from_lc
| join kind=fullouter (
    MonSQLXStore
    | where file_path contains "{target_logical_database_id}"
    | where file_path !contains "snapshot" and isnotempty(blob_size) and file_path !contains "ldf"
    | extend PageServerId = iff(file_path contains "_F_0x",
        tostring(split(file_path, '_')[2]),
        tostring(split(tostring(split(file_path, "_")[1]), ".")[0]))
    | project file_path, blob_size, PageServerId = tolong(PageServerId)
    | project file_path, PageServerId, blob_size = iff(file_path contains "_F_0x", 128 * 1024 * 1024 * 1024, blob_size)
    | distinct PageServerId, blob_size
    | summarize max(blob_size) by PageServerId
) on PageServerId
| project AppName, PageServerId, start_page_id,
    PageServerSize = iff(isempty(max_blob_size), "32 GB",
        iff(max_blob_size / (1024 * 1024 * 1024) <= 128, "128 GB", "1 TB")),
    RedoBeginTime, RedoEndTime, minRedoBsn, maxRedoBsn,
    RedoLogMB, RedoTimeMinutes,
    total_reads_from_broker, total_reads_from_lz, total_reads_from_lc
| join kind=inner (
    MonSQLSystemHealth
    | where originalEventTimestamp >= datetime("{copyDoneTime}")
        and originalEventTimestamp <= datetime("{restoreFinishedTime}")
    | where AppTypeName == "Worker.Vldb.Storage"
    | where message contains "seedSegmentInternal: Segment seeded"
    | parse message with * ", Source Segment: " segId:int ", RBPEX Segment: " *
    | project originalEventTimestamp, process_id, NodeName, message, segId, AppName,
        ClusterName, code_package_version
    | summarize StartSeeding = min(originalEventTimestamp), EndSeeding = max(originalEventTimestamp)
        by AppName
) on AppName
| project AppName, PageServerId, StartPageId = start_page_id, PageServerSize,
    StartSeeding, EndSeeding, RedoBeginTime, RedoEndTime,
    minRedoBsn, maxRedoBsn, RedoLogMB, RedoTimeMinutes,
    total_reads_from_broker, total_reads_from_lz, total_reads_from_lc
| order by PageServerId asc, StartPageId asc
```

**Analysis**: Longest `RedoTimeMinutes` = bottleneck PS. `total_reads_from_broker` dominates → log cache misses. `RedoLogMB` skewed → uneven distribution. See `references/knowledge.md` for detailed interpretation.
