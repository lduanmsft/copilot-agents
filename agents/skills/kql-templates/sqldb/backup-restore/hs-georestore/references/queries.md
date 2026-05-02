# Kusto Query Reference: Hyperscale (VLDB) Geo-Restore Investigation

This file documents all KQL queries used by the `hs-georestore` skill. Do NOT modify, rewrite, or regenerate any query.

## Table of Contents

- [Input Resolution](#input-resolution)
  - [QHGR00A — Find request_id by restoreId](#qhgr00a)
  - [QHGR00B — Find request_id by server/database](#qhgr00b)
- [Verification](#verification)
  - [QHGR05 — Geo-Restore Verification](#qhgr05)
- [Main Trunk](#main-trunk)
  - [QHGR10 — Operation Overview](#qhgr10)
  - [QHGR11 — Resolve Region Kusto Cluster](#qhgr11)
  - [QHGR12 — Restore Request Progress (PIT Extraction)](#qhgr12)
  - [QHGR15 — State Machine Transitions](#qhgr15)
- [Geo-Replication Analysis](#geo-replication-analysis)
  - [QHGR20 — Storage Account Geo-Replication Lag](#qhgr20)

## Format Conventions

- **Parameters**: `{parameter_name}` — substitute at runtime
- **Tool**: All queries via `mcp_sqlops_query_kusto`

---

## Input Resolution

<a id="qhgr00a"></a>
### QHGR00A — Find request_id by restoreId

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

**Analysis**: Use the returned `request_id` to proceed with the investigation. If multiple results, disambiguate per SKILL.md rules.

---

<a id="qhgr00b"></a>
### QHGR00B — Find request_id by server/database name

**Purpose**: Resolve server name (and optionally database name) to `request_id` when no `restoreId` or `request_id` is available.
**When**: Manual ICM or user provides server name only.
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

**Analysis**: If 0 results → widen time range or ask user. If >1 result → filter by `TargetDb` if known, or present to user. If >10 → ask for narrower time range.

---

## Verification

<a id="qhgr05"></a>
### QHGR05 — Geo-Restore Verification

**Purpose**: Confirm the operation is a geo-restore (not a database copy or cross-server restore). Geo-restores have `<IsCrossServerRestore>false</IsCrossServerRestore>` in their operation parameters.
**When**: Immediately after input resolution, before running QHGR10.
**Table**: `MonManagementOperations`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Input resolution (QHGR00A/QHGR00B) |

```kusto
MonManagementOperations
| where request_id == '{request_id}'
| where operation_parameters has '<IsCrossServerRestore>false</IsCrossServerRestore>'
| where event == 'management_operation_start'
| project TIMESTAMP, request_id, operation_type, operation_parameters
| take 1
```

**Analysis**:
- **1 result** → Confirmed geo-restore. Proceed to QHGR10.
- **0 results** → This is NOT a geo-restore (likely a database copy or cross-server restore). Stop and route to the appropriate skill.

---

## Main Trunk

<a id="qhgr10"></a>
### QHGR10 — Operation Overview

**Purpose**: Establish timeline, status, and extract restore-specific IDs. Save variables for subsequent queries.
**When**: Always first (once `request_id` is resolved).
**Table**: `MonManagementOperations`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Input resolution (QHGR00A/QHGR00B) |

```kusto
MonManagementOperations
| where request_id == '{request_id}'
| where event !in ('management_operation_rads_signal', 'management_operation_released', 'management_operation_progress')
| project TIMESTAMP, event, request_id, operation_type, operation_parameters, operation_result, state, error_message
```

**Variables to extract from `operation_parameters` XML:**

| Variable | XML Key | Use |
|----------|---------|-----|
| `restore_id` | `<RestoreId>` | Restore tracking |
| `source_logical_database_id` | `<SourceLogicalDatabaseId>` | Source database identification |
| `source_logical_server_name` | `<SourceLogicalServerName>` | Context, display |
| `source_logical_database_name` | `<SourceLogicalDatabaseName>` | Context, display |
| `target_logical_server_name` | `<TargetLogicalServerName>` | Context, display |
| `target_logical_database_name` | `<TargetLogicalDatabaseName>` | Context, display |
| `target_edition` | `<TargetEdition>` | Edition (Premium, Hyperscale, etc.) |
| `target_slo` | `<TargetServiceLevelObjectiveName>` | SLO identification |
| `point_in_time` | `<PointInTime>` | Requested restore point — compare against geo-replication lag |
| `source_database_dropped_time` | `<SourceDatabaseDroppedTime>` | If set → restoring a deleted/dropped database |
| `restore_start_time` | TIMESTAMP of `management_operation_start` event | Timeline |
| `restore_end_time` | TIMESTAMP of completion event, or `now()` if stuck | Timeline |

> **Note**: `target_logical_database_id` is NOT in `operation_parameters`. It appears in `operation_result` XML of `management_operation_success` event under `<LogicalDatabaseId>`. For stuck restores, use the FSM resolution query from the `hs-restore` skill.

**Analysis**: Determine status (Succeeded / Failed / Cancelled / Stuck) and classify error type (User Error vs System Error) per SKILL.md Step 2 rules.

---

<a id="qhgr11"></a>
### QHGR11 — Resolve Region Kusto Cluster

**Purpose**: Resolve the target logical server name to a region Kusto cluster. This determines which region cluster the restore telemetry resides on, so subsequent queries (QHGR12, QHGR15) can be executed against the correct region instead of fanning out across all production clusters.
**When**: After QHGR10, once `target_logical_server_name` and timestamps are known.
**Table**: `MonLogin`
**Execute on**: `https://sqladhoc.kusto.windows.net/sqlazure1`
**Reference**: Based on [RegionFromHistory.md](../../Common/execute-kusto-query/references/RegionFromHistory.md)

| Parameter | Source |
|-----------|--------|
| `{start_time}` | `restore_start_time` from QHGR10 (or `restore_start_time - 7d` for wider search) |
| `{end_time}` | `restore_end_time` from QHGR10 (or `now()` if stuck) |
| `{target_logical_server_name}` | Extracted from QHGR10 `operation_parameters` XML |

```kusto
let SingleCluster = (clstr: string)
{
    cluster(clstr).database('sqlazure1').MonLogin
    | where originalEventTimestamp between ((datetime({start_time}) - 7d) .. datetime({end_time}))
    | where logical_server_name =~ '{target_logical_server_name}'
        and event == 'process_login_finish'
        and package =~ 'xdbgateway'
    | distinct ClusterName
};
_ExecuteForProdClusters
| take 1
```

**Post-processing**:
1. The result is a connectivity ring FQDN, e.g., `cr10.northcentralus1-a.control.database.windows.net`
2. Extract the region segment from the FQDN: `northcentralus1-a` → strip the suffix after the last `-` → **`northcentralus1`**
3. Save as `{region}` for use in all subsequent queries (QHGR12, QHGR15, QHGR20)

**Examples**:
| ClusterName FQDN | Extracted | Region |
|---|---|---|
| `cr18.eastus2-a.control.database.windows.net` | `eastus2-a` → `eastus2` | `eastus2` |
| `cr1.northeurope1-z.control.database.windows.net` | `northeurope1-z` → `northeurope1` | `northeurope1` |
| `cr10.northcentralus1-a.control.database.windows.net` | `northcentralus1-a` → `northcentralus1` | `northcentralus1` |

**If 0 results**: The server may not have had recent logins. Try using the `source_logical_server_name` instead, or ask the user for the region.

---

<a id="qhgr12"></a>
### QHGR12 — Restore Request Progress (PIT Extraction)

**Purpose**: Extract the Point in Time (PIT), Adjusted Point in Time (Adjusted PIT), and PIT used by xlog to snip log from the restore request progress events. These values show the actual restore point negotiated by the restore plan — which may differ from the requested `<PointInTime>` in `operation_parameters`.
**When**: After QHGR11, once `restore_id` and `{region}` are known.
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{restore_id}` | Extracted from QHGR10 `operation_parameters` XML |
| `{region}` | Resolved from QHGR11 |

```kusto
MonManagement
| where originalEventTimestamp > ago(14d)
| where event contains "restore_request_progress"
    and restore_request_id =~ "{restore_id}"
| project originalEventTimestamp, request_id, restore_request_id,
    message_scrubbed_resource_name, exception_message, stack_trace
| order by originalEventTimestamp asc
```

**Variables to extract from `message_scrubbed_resource_name`:**

The field contains a comma-separated string with the following format:
```
PIT: {datetime},Adjusted PIT: {datetime},PIT used by xlog to snip log would be {datetime}
```

| Variable | Prefix in message | Use |
|----------|--------------------|-----|
| `pit` | `PIT:` | Requested point-in-time from the user/API |
| `adjusted_pit` | `Adjusted PIT:` | Adjusted point-in-time after geo-replication lag consideration |
| `xlog_snip_pit` | `PIT used by xlog to snip log would be` | Actual point-in-time used by xlog to truncate the log — this is the effective restore point |

**Analysis:**
- If `pit` ≠ `adjusted_pit` → The system adjusted the restore point (likely due to geo-replication lag or data availability).
- If `xlog_snip_pit` ≠ `adjusted_pit` → The xlog snip used a different point than the adjusted PIT. This can indicate further adjustment at the storage layer.
- If all three match → Clean restore to exactly the requested point-in-time.
- Check `exception_message` for any errors during the restore request progress.

---

<a id="qhgr15"></a>
### QHGR15 — State Machine Transitions

**Purpose**: Trace all state machine transitions across the Hyperscale restore pipeline — from the restore request through page server provisioning, storage copy, compute database creation, and SQL instance readiness. This gives the full picture of what happened, how long each phase took, and where exceptions occurred.
**When**: After QHGR10, for **all** investigations (success, failure, or stuck). This is the primary diagnostic query for understanding the restore timeline.
**Table**: `MonManagement`

| Parameter | Source |
|-----------|--------|
| `{request_id}` | Input resolution (QHGR00A/QHGR00B) |

```kusto
MonManagement
| where request_id == '{request_id}'
| where state_machine_type in (
    "VldbRestoreRequestStateMachine",
    "VldbPageServerStateMachine",
    "VldbComputeDatabaseStateMachine",
    "AzureStorageCopyManagerStateMachine",
    "AzureStorageCopyRequestStateMachine",
    "PhysicalDatabaseStateMachine",
    "VeryLargeDatabaseStateMachine",
    "SqlInstanceStateMachine")
| where event == "fsm_executed_action" or event == "fsm_log_exception"
| project originalEventTimestamp, state_machine_type,
    old_state, new_state, action, elapsed_time_milliseconds,
    ['keys'], transaction_id, is_stable_state, state,
    message, stack_trace, exception_type
| sort by originalEventTimestamp asc
```

**State Machine Roles:**

| State Machine | What It Tracks |
|---------------|----------------|
| `VldbRestoreRequestStateMachine` | Top-level restore orchestration |
| `VldbPageServerStateMachine` | Page server provisioning and snapshot restore |
| `VldbComputeDatabaseStateMachine` | Compute node database creation |
| `AzureStorageCopyManagerStateMachine` | Orchestrates storage blob copy operations |
| `AzureStorageCopyRequestStateMachine` | Individual storage copy request tracking |
| `PhysicalDatabaseStateMachine` | Physical database lifecycle |
| `VeryLargeDatabaseStateMachine` | VLDB-level orchestration |
| `SqlInstanceStateMachine` | SQL instance readiness |

**Analysis:**
- **Timeline**: Read `originalEventTimestamp` top-to-bottom to understand the execution order.
- **Duration bottlenecks**: Look for large `elapsed_time_milliseconds` values — these indicate slow phases.
- **Exceptions**: Any `fsm_log_exception` event signals an error. Check `exception_type`, `message`, and `stack_trace`.
- **Stuck transitions**: If a state machine stays in a non-stable state (`is_stable_state == false`) without progressing, the restore is stuck at that phase.
- **Success path**: A healthy restore shows `VldbRestoreRequestStateMachine` progressing through states ending in a stable completed state, with page server and storage copy machines each completing normally.

---

## Geo-Replication Analysis

<a id="qhgr20"></a>
### QHGR20 — Storage Account Geo-Replication Lag

**Purpose**: Check the geo-replication last sync time for the storage accounts used by the source database's XLog destage blobs. A large lag indicates that geo-replicated backup data was not yet available at the requested restore point-in-time.
**When**: After QHGR10, only when status is **Failed** or **Slow** with a **System Error** classification (not User Error).
**Table**: `MonBlobClient`

| Parameter | Source |
|-----------|--------|
| `{storage_account_1}` | Storage account name from source DB's XLog destage blob configuration |
| `{storage_account_2}` | (Optional) Additional storage account name |

> **Note**: Replace the `in ()` list with the actual storage account names. Add or remove entries as needed.

```kusto
MonBlobClient
| where event == 'blobclient_get_geo_replication_details_for_storage_account_complete'
    and storage_account_name in ("{storage_account_1}", "{storage_account_2}")
| extend lag = PreciseTimeStamp - todatetime(trim("\\+00:00", geo_replication_last_sync_time))
| summarize arg_max(originalEventTimestamp, lag) by storage_account_name
| project storage_account_name, current_lag = lag
| summarize max(current_lag)
```

**Analysis**:
- **`max_current_lag` > 1 hour** → 🚩 Significant geo-replication lag. Likely root cause if the requested `point_in_time` falls within the lag window.
- **`max_current_lag` between 15 min and 1 hour** → ⚠️ Elevated lag. May contribute to restore issues depending on the requested point-in-time.
- **`max_current_lag` < 15 min** → Geo-replication is healthy. The failure is likely caused by something else — consider escalating to `hs-restore` skill for full pipeline analysis.
- **No results** → Either the storage accounts do not have geo-replication enabled, the event data has aged out, or the storage account names are incorrect. Ask user to verify.
