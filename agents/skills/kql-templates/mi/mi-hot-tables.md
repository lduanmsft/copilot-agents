# MI Hot Tables — Quick Schema Reference

**Source of truth**: [`mi-tables-reference.md`](mi-tables-reference.md) (785 KB, full schema for 136 tables)
**This file**: 5 most-used tables for ad-hoc investigation queries. Always check here first before writing any custom KQL.

---

## ⚠️ Common Pitfalls (verified 2026-05-02)

| ❌ Wrong (don't use) | ✅ Correct | Notes |
|---|---|---|
| `MonGeoDRFailoverGroups.partner_logical_server_name` | `partner_server_name` | column does not exist on this table |
| `MonManagementOperations.operation_name` | `operation_type` | confusingly close, easy to swap |
| `MonDbSeedTraces.logical_database_name` | `database_name` | DB GUID stored in `database_name`, not logical |
| `MonDmDbHadrReplicaStates.database_name` | `logical_database_name` | opposite convention from MonDbSeedTraces |
| `MonSQLSystemHealth.error_severity` | use `error_id` only | this table has no severity column |
| `where ... has 'FailoverGroup'` | `... has 'failovergroup'` (lowercase) **or** `contains 'FailoverGroup'` | KQL `has` is token-based and case-insensitive only on whole tokens; CamelCase tokens rarely match. Prefer `contains` for type names like `CreateManagedFailoverGroup` |

---

## Cluster URL pattern

CSV: `~/.copilot/agents/skills/kql-templates/shared/SQLClusterMappings.Followers.csv`
- Region naming: `[SQL] {RegionDisplayName}` e.g. `[SQL] East Asia`, `[SQL] South East Asia`
- All MI/DB telemetry lives in database `sqlazure1` on the regional Follower cluster.

---

## 1. MonManagementOperations — Control plane operation log

**Use for**: tracing FOG create/drop, MakeAccessible, UpdateSlo, AKV operations, restore, etc. **Always start FOG investigations here.**

| Column | Type | Notes |
|---|---|---|
| `PreciseTimeStamp` / `TIMESTAMP` | datetime | Both indexed; use either |
| `event` | string | `management_operation_start` / `management_operation_success` / `management_operation_failure` / `management_operation_rads_signal` |
| `operation_type` | string | ⚠️ NOT `operation_name`. Examples: `CreateManagedFailoverGroup`, `DropManagedFailoverGroup`, `MakeAllManagedDatabasesAccessible`, `AutomaticGeoSecondaryCreate`, `UpsertManagedServerEncryptionProtector`, `StartManagedServer`, `StopManagedServer`, `UpsertDatabaseTransparentDataEncryption` |
| `request_id` | string | UUID, groups events of a single operation |
| `operation_parameters` | string (XML) | Full input. Parse with `extract(@'<TagName>([^<]+)', 1, operation_parameters)` |
| `operation_result` | string | Empty / `Succeeded` / `Failed` (only set on success/failure events) |
| `state` | string | `` / `Succeeded` / `Failed` (set on rads_signal event) |
| `error_code` | long | 0 if no error |
| `error_message` | string | Human-readable failure |
| `error_severity` | long | ✅ This table has it (unlike MonSQLSystemHealth) |
| `is_user_error` | bool | True = caller error (45143 etc.), False = service-side |
| `logical_server_name` | string | ⚠️ Often empty for FOG ops — filter via `operation_parameters has '<server>'` instead |
| `logical_database_name` | string | Same caveat |
| `elapsed_time_milliseconds` | real | Duration on success/failure event |

**Cookbook — find any failed op for a server in a window:**
```kql
MonManagementOperations
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where operation_parameters has '{ServerName}'
| where event == 'management_operation_failure'
| project PreciseTimeStamp, operation_type, request_id, error_code,
          ErrorMsg = substring(error_message, 0, 250),
          FogName = extract(@'<FailoverGroupName>([^<]+)', 1, operation_parameters),
          DbId = extract(@'<ManagedDatabaseId>([^<]+)', 1, operation_parameters),
          DbName = extract(@'<DatabaseName>([^<]+)', 1, operation_parameters)
| order by PreciseTimeStamp asc
```

**Cookbook — full request_id timeline (start → success/failure):**
```kql
MonManagementOperations
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where request_id =~ '{RequestId}'
| project PreciseTimeStamp, event, operation_type, error_code, error_message, state
| order by PreciseTimeStamp asc
```

---

## 2. MonGeoDRFailoverGroups — FOG configuration snapshot

**Use for**: find FOG name, partner instance, partner region, role.

| Column | Type | Notes |
|---|---|---|
| `failover_group_name` | string | |
| `failover_group_id` | string | |
| `failover_group_type` | string | `Full` |
| `logical_server_name` | string | The MI this row belongs to |
| `partner_server_name` | string | ⚠️ NOT `partner_logical_server_name` |
| `partner_region` | string | e.g. `southeastasia` |
| `role` | string | `Primary` / `Secondary` |
| `failover_policy` | string | `Manual` / `Automatic` |
| `failover_group_create_time` | datetime | |
| `all_servers` | string | Often empty |
| `readonly_endpoint_failover_policy` | string | |

**Cookbook — find FOG info for a server:**
```kql
MonGeoDRFailoverGroups
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where logical_server_name =~ '{ServerName}' or partner_server_name =~ '{ServerName}'
| summarize arg_max(TIMESTAMP, *) by failover_group_name, logical_server_name
| project TIMESTAMP, failover_group_name, logical_server_name,
          partner_server_name, partner_region, role, failover_group_type
```

---

## 3. MonDbSeedTraces — Per-database seeding progress (BC only)

**Use for**: Business Critical seeding progress / failures. **GP MI uses storage-level copy and writes nothing here** — empty result on GP is normal.

| Column | Type | Notes |
|---|---|---|
| `database_name` | string | ⚠️ Stores **GUID** (physical_database_id), NOT logical name. To map: join `MonAnalyticsDBSnapshot` on `physical_database_id` |
| `database_id` | long | Local sqlservr db_id |
| `event` | string | Key values: `hadr_physical_seeding_progress`, `hadr_physical_seeding_failure`, `hadr_physical_seeding_state` |
| `role_desc` | string | `Source` (primary side) / `Destination` (secondary side) |
| `internal_state_desc` | string | `Pending` → `Active` → `Success` / `Failure` |
| `transferred_size_bytes` | long | Cumulative |
| `transfer_rate_bytes_per_second` | long | Instantaneous rate |
| `database_size_bytes` | long | Total size |
| `failure_code` / `failure_message` | long/string | Only on failure |
| `seeding_start_time` / `seeding_end_time` | datetime | |
| `local_seeding_guid` / `remote_seeding_guid` | string | Pair primary↔secondary side |

**Cookbook — current seeding state for a server (run on Secondary cluster):**
```kql
MonDbSeedTraces
| where TIMESTAMP >= ago({Window})
| where AppTypeName startswith 'Worker.CL'
| where LogicalServerName =~ '{ServerName}'
| where event == 'hadr_physical_seeding_progress'
| extend rate_mb_s = round(transfer_rate_bytes_per_second / 1024.0 / 1024.0, 2)
| extend pct = round(todouble(transferred_size_bytes) * 100.0 / todouble(database_size_bytes), 2)
| project originalEventTimestamp, database_name, pct, rate_mb_s, internal_state_desc, role_desc
| order by originalEventTimestamp desc
```

---

## 4. MonAnalyticsDBSnapshot — DB inventory and state

**Use for**: map db GUID ↔ logical name, current state, edition, backup retention, FOG membership. **Run BEFORE writing seeding queries to confirm DB exists with the GUID you expect.**

| Column | Type | Notes |
|---|---|---|
| `logical_server_name` | string | |
| `logical_database_name` | string | Customer-visible name |
| `logical_database_id` | string | GUID — same as `database_name` in MonDbSeedTraces |
| `physical_database_id` | string | Different GUID — physical layout id, used by FOG operation_parameters |
| `state` | string | `Ready`, `Inaccessible`, `Stopped`, `Copying`, `WaitingForPhysicalDatabaseToDrop`, `TailLogBackupInProgressToMakeDbInaccessible`, `PerformingAkvCheckToMakeDbInaccessible`, `HybridLinksDeactivationCompletedForStoppingDb` |
| `physical_database_state` | string | `Ready`, `Deactivated`, `DroppingWinFabProperties` |
| `database_type` | string | `SQL.ManagedUserDb`, `SQL.ManagedSystemDb` |
| `edition` | string | `GeneralPurpose`, `BusinessCritical` |
| `failover_group_id` | string | Empty if not in FOG |
| `create_mode` | string | `Default`, `PointInTimeRestore`, `RecoveryHybridContinuousCopy`, etc. |
| `create_time` | datetime | |
| `sql_instance_name` | string | AppName variant — instance hash |
| `tenant_ring_name` | string | Cluster fabric name |
| `backup_retention_days` | long | |
| `last_update_time` | datetime | When the row was last refreshed |

**Cookbook — current DB list with GUIDs:**
```kql
MonAnalyticsDBSnapshot
| where TIMESTAMP >= ago(1d)
| where logical_server_name =~ '{ServerName}'
| summarize arg_max(TIMESTAMP, *) by logical_database_name
| project logical_database_name, logical_database_id, physical_database_id,
          state, physical_database_state, edition, failover_group_id, create_mode
```

---

## 5. MonSQLSystemHealth — Errorlog + system_health XEvent + ring buffer

**Use for**: SQL-level errors (823/845/1133/1412/1408), recovery messages, AKV access failures, dump traces.

| Column | Type | Notes |
|---|---|---|
| `LogicalServerName` | string | |
| `AppName` | string | Instance hash — also use this to filter |
| `NodeName` | string | |
| `error_id` | long | SQL error number; 0 = no error (informational message) |
| ~~`error_severity`~~ | — | ⚠️ **DOES NOT EXIST**. Use `error_id` filter instead. |
| `message` | string | Free-text errorlog line |
| `event` | string | XEvent name when from system_health, e.g. `error_reported`, `xml_deadlock_report` |
| `process_id` | long | sqlservr PID |
| `originalEventTimestamp` | datetime | When the error fired in SQL (vs ingest TIMESTAMP) |
| `database_id` / `db_id` | long | Local sqlservr db_id |

**Cookbook — top SQL errors for a server:**
```kql
MonSQLSystemHealth
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where LogicalServerName =~ '{ServerName}'
| where error_id > 0
| summarize Cnt = count(),
            FirstTs = min(originalEventTimestamp),
            LastTs = max(originalEventTimestamp),
            MsgSample = tostring(take_any(message))
            by error_id
| order by Cnt desc
```

---

## Mandatory rule for ad-hoc queries

1. Identify the table you need.
2. Open this file (`mi-hot-tables.md`) — if the table is here, use the documented columns.
3. If not here → grep `mi-tables-reference.md`:
   ```
   grep -A 40 '^## TableName' mi-tables-reference.md
   ```
4. Only after confirming columns, write the KQL.
5. **Never guess column names** based on intuition or what "should" exist (e.g. `partner_logical_server_name`, `operation_name`, `error_severity`).

If a query fails with `SEM0100: Failed to resolve column`, do NOT retry with another guess — go back to step 2.
