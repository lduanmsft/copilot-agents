# MI Kusto Tables — Code-Level Reference

This file was built by searching msdata ADO code and reading the referenced source files. It focuses on the columns engineers most often use in KQL, not every raw telemetry field.

**Common telemetry columns** such as `TIMESTAMP`, `PreciseTimeStamp`, `ClusterName`, `NodeName`, `AppName`, `AppTypeName`, `LogicalServerName`, and `SubscriptionId` are omitted from some per-table column lists unless the code explicitly used them for table-specific logic.

---

## 1. MonManagedServers — MI Instance Metadata

### Definition
`MonManagedServers` is the managed-instance server inventory/state snapshot used by MI availability and repair logic. The code strongly suggests it mirrors the control-plane/CMS `managed_servers` entity and publishes periodic snapshots into Kusto.

### Code Source
- **Repositories**: `SqlTelemetry`, `SQLLivesiteAgents`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/WaflRunnerMitigators/CloudLifterMitigators/StuckStopRequestsMitigator.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterAvailability/MIDataMovementRunner.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/BackupRestore/FullBackupSkippedAfterGeoFailoverMIRunner.cs`
- **Data Origin**: inferred CMS/control-plane `managed_servers` snapshot, surfaced in Kusto as `MonManagedServers`
- **Evidence**:
  - `FullBackupSkippedAfterGeoFailoverMIRunner.cs` queries CMS `managed_servers` and correlates the same IDs/names with MI Kusto tables.
  - `StuckStopRequestsMitigator.cs` and `MIDataMovementRunner.cs` query `MonManagedServers` by `managed_server_id`, `name`, `state`, `edition`, `zone_redundant`.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `name` | string | Managed Instance name | `StuckStopRequestsMitigator.cs` projects `name`; CMS query uses `ms.name AS primary_managed_server_name` |
| `managed_server_id` | string | Stable MI server identifier | `StuckStopRequestsMitigator.cs`, `MissingMiTdeCertificateRunner.cs`, CMS `managed_servers.managed_server_id` |
| `state` | string | Current MI lifecycle state (`Ready`, `Stopped`, `Disabled`, etc.) | `StuckStopRequestsMitigator.cs` filters `state`; `MIDataMovementRunner.cs` filters `state == 'Ready'` |
| `edition` | string | MI tier, e.g. `BusinessCritical` | `MIDataMovementRunner.cs` filters `edition == 'BusinessCritical'` |
| `zone_redundant` | bool/int | Whether the MI is zone redundant | `MIDataMovementRunner.cs` uses `zone_redundant` to compute expected replica counts |
| `resource_group` | string | Azure resource group for the MI | Inferred from table schema/name; exact producer not found |
| `customer_subscription_id` | string | Customer subscription that owns the MI | Inferred from name; paired with MI inventory semantics |
| `create_time` | datetime | MI creation time | Inferred from control-plane metadata naming |
| `last_state_change_time` | datetime | Most recent state transition time | Inferred from control-plane metadata naming |
| `vcore_count` | int | Provisioned vCore count | Inferred from name |
| `reserved_storage_size_gb` | int | Reserved storage quota for the MI | Inferred from name |
| `hardware_family` | string | Hardware generation/family | Inferred from name |

---

## 2. MonManagedDatabases — MI Database Metadata

### Definition
`MonManagedDatabases` is the managed-database inventory/state table for MI. The code shows it is used as the Kusto-side reflection of CMS `managed_databases`, especially for correlating database IDs, names, failover-group membership, and server ownership.

### Code Source
- **Repositories**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/BackupRestore/FullBackupSkippedAfterGeoFailoverMIRunner.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/MissingMiTdeCertificateRunner.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LogFull.cs`
- **Data Origin**: inferred CMS `managed_databases` snapshot, surfaced in Kusto as `MonManagedDatabases`
- **Evidence**:
  - `FullBackupSkippedAfterGeoFailoverMIRunner.cs` queries CMS `managed_databases` and also queries `MonManagedDatabases` using the same keys.
  - `LogFull.cs` resolves `managed_database_id -> managed_database_name` from `MonManagedDatabases`.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `managed_database_id` | string | Stable MI database identifier | `FullBackupSkippedAfterGeoFailoverMIRunner.cs`; `LogFull.cs` lookup by `managed_database_id` |
| `managed_database_name` | string | Managed database name | CMS `managed_databases.managed_database_name`; `LogFull.cs` returns `managed_database_name` |
| `managed_server_id` | string | Owning MI server id | `FullBackupSkippedAfterGeoFailoverMIRunner.cs`; `MissingMiTdeCertificateRunner.cs` joins on `managed_server_id` |
| `failover_group_id` | string | FOG membership id | `FullBackupSkippedAfterGeoFailoverMIRunner.cs` filters by `failover_group_id` |
| `state` | string | Database state, typically `Ready` for healthy rows | CMS query filters `state = 'Ready'`; KQL query filters `state == 'Ready'` |
| `database_type` | string | MI DB type (`SQL.Msdb`, `SQL.ManagedModelDb`, etc.) | CMS query case expression on `database_type` in `FullBackupSkippedAfterGeoFailoverMIRunner.cs` |
| `create_time` | datetime | DB creation time | CMS query filters `create_time <= failover time` |
| `service_level_objective` | string | DB SLO/tier | Inferred from standard MI metadata naming |
| `edition` | string | Edition/tier | Inferred from standard MI metadata naming |
| `end_utc_date` | datetime | Snapshot validity/end time used for arg-max snapshot selection | `FullBackupSkippedAfterGeoFailoverMIRunner.cs` filters and `arg_max(end_utc_date, *)` |
| `start_utc_date` | datetime | Snapshot validity/start time | Inferred from snapshot naming |
| `backup_retention_days` | int | Backup retention setting | Inferred from name |

---

## 3. MonGeoDRFailoverGroups — FOG Configuration

### Definition
`MonGeoDRFailoverGroups` captures MI failover-group topology and policy: the failover-group id/name, primary vs partner, partner region/server, and failover policy settings. The matching CMS SQL uses `managed_failover_groups` plus `managed_failover_group_links`.

### Code Source
- **Repositories**: `SqlTelemetry`, `SQLLivesiteAgents`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/BackupRestore/FullBackupSkippedAfterGeoFailoverMIRunner.cs`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonGeoDRFailoverGroups.kql`
- **Data Origin**: CMS `managed_failover_groups` + `managed_failover_group_links`
- **Evidence**:
  - CMS query selects `failover_group_id`, `failover_group_name`, `failover_policy`, `partner_region`, `partner_server_name` from those tables.
  - KQL query uses `MonGeoDRFailoverGroups` keyed by `logical_server_name`.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `logical_server_name` | string | Primary MI logical server / failover-group owner | `MonGeoDRFailoverGroups.kql` filters on `logical_server_name` |
| `failover_group_id` | string | FOG identifier | CMS query in `FullBackupSkippedAfterGeoFailoverMIRunner.cs` |
| `failover_group_name` | string | FOG name | CMS query in `FullBackupSkippedAfterGeoFailoverMIRunner.cs` |
| `failover_policy` | string | Auto/manual failover policy | CMS query in `FullBackupSkippedAfterGeoFailoverMIRunner.cs` |
| `failover_grace_period_in_minutes` | int | Planned grace period before failover | Inferred from name / failover policy semantics |
| `failover_with_data_loss_grace_period_in_minutes` | int | Grace period for forced data-loss failover | Inferred from name |
| `partner_region` | string | Partner region for FOG | CMS query uses `mfgl.partner_region` |
| `partner_server_name` | string | Partner MI server name | CMS query uses `mfgl.partner_server_name` |
| `role` | string | Current role (`Primary`/secondary partner view) | CMS query filters `mfg.role = 'Primary'` |
| `failover_group_create_time` | datetime | FOG creation time | Inferred from name |
| `readonly_endpoint_failover_policy` | string | Read-only endpoint behavior | Inferred from name |
| `sub_type` | string | Subscription/type classification | Inferred from name |

---

## 4. MonDbSeedTraces — Seeding Progress

### Definition
`MonDbSeedTraces` is the MI seeding-progress/event table. The code shows it is driven by `hadr_physical_seeding_progress` events and used for both geo seeding and local seeding RCA, including progress checks, failure counts, and restart detection.

### Code Source
- **Repositories**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterAvailability/MIDataMovementRunner.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LogFull.cs`
- **Data Origin**: SQL/HADR physical seeding progress events for MI workers (`Worker.CL`)
- **Evidence**:
  - `MIDataMovementRunner.cs` repeatedly filters `event == 'hadr_physical_seeding_progress'`.
  - Queries use `internal_state_desc`, `role_desc`, `remote_machine_name`, `new_state`, `transferred_size_bytes`, `local_seeding_guid`.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Event type; code shows `hadr_physical_seeding_progress` | `MIDataMovementRunner.cs`; `LogFull.cs` |
| `database_name` | string | Database being seeded | `MIDataMovementRunner.cs` filters `database_name` |
| `role_desc` | string | Seeding role (`Source`/target role) | `MIDataMovementRunner.cs` filters `role_desc == 'Source'` |
| `internal_state_desc` | string | Human-readable internal seeding state | `MIDataMovementRunner.cs` checks `internal_state_desc == 'Success'` |
| `new_state` | string | New seeding state, e.g. `Failed` | `MIDataMovementRunner.cs` filters `new_state == 'Failed'` |
| `transferred_size_bytes` | long | Bytes transferred so far | `MIDataMovementRunner.cs` compares current vs previous `transferred_size_bytes` |
| `transfer_rate_bytes_per_second` | long | Current transfer rate | Inferred from name |
| `remote_machine_name` | string | Remote seeding endpoint/machine, often `:5022` listener | `MIDataMovementRunner.cs` filters `remote_machine_name contains ':5022'` |
| `local_seeding_guid` | string | Seeding session identifier | `MIDataMovementRunner.cs` groups/joins by `local_seeding_guid` |
| `seeding_start_time` | datetime | Start of seeding window | Inferred from name |
| `seeding_end_time` | datetime | End of seeding window | Inferred from name |
| `failure_message` | string | Failure detail text | Inferred from name |
| `retry_count` | int | Retry count for the seeding workflow | Inferred from name |

---

## 5. MonManagedInstanceResourceStats — Instance Resource Usage

### Definition
`MonManagedInstanceResourceStats` is the instance-level MI resource-utilization table. It is used for storage/utilization calculations and capacity-style health checks, especially around storage used vs reserved quota and instance CPU/load.

### Code Source
- **Repositories**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/BackupRestore/FullBackupSkippedAfterGeoFailoverMIRunner.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LogFull.cs`
- **Data Origin**: inferred instance resource DMV/telemetry pipeline for MI
- **Evidence**:
  - `FullBackupSkippedAfterGeoFailoverMIRunner.cs` reads `storage_space_used_mb` near failover time.
  - `LogFull.cs` maps `reserved_storage_mb` -> instance max size and `storage_space_used_mb` -> used space.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `start_time` | datetime | Start of resource-stat interval | Inferred from name |
| `end_time` | datetime | End of resource-stat interval | Inferred from name |
| `virtual_core_count` | int | Provisioned MI vCore count | Inferred from name |
| `avg_cpu_percent` | real | Average MI CPU utilization | Inferred from name |
| `reserved_storage_mb` | long | Reserved storage quota for the instance | `LogFull.cs` uses `reserved_storage_mb` as `max_size_mb` |
| `storage_space_used_mb` | long | Used instance storage | `FullBackupSkippedAfterGeoFailoverMIRunner.cs`; `LogFull.cs` |
| `backup_storage_consumption_mb` | long | Backup storage consumed by the instance | Inferred from name |
| `avg_log_write_percent` | real | Log write utilization | Inferred from name |
| `active_sessions` | int | Active sessions at the instance | Inferred from name |
| `active_workers` | int | Active worker count | Inferred from name |
| `total_logins` | int | Total login count in interval | Inferred from name |
| `server_name` | string | MI server name | Inferred from name |
| `sku` | string | MI SKU/tier | Inferred from name |
| `hardware_generation` | string | Underlying hardware generation | Inferred from name |
| `reserved_storage_iops` | long | Reserved storage IOPS | Inferred from name |

---

## 6. MonDmRealTimeResourceStats — DB-Level Real-Time Stats

### Definition
`MonDmRealTimeResourceStats` is the DB-level real-time performance table. The in-repo documentation explicitly states it maps to `sys.dm_db_resource_stats` and is collected every 15 seconds.

### Code Source
- **Repositories**: `SQL-DB-ON-Call-Common`, `SQLLivesiteAgents`
- **Key Files**:
  - `SQL-DB-ON-Call-Common:/content/Tools/Kusto/Performance-related-Kusto-Tables/MonDmRealTimeResourceStats.md`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonDmRealTimeResourceStats.kql`
- **Data Origin**: `sys.dm_db_resource_stats`
- **Evidence**:
  - The markdown doc states the mapping directly.
  - KQL query uses `replica_role`, `process_id`, `cpu_limit`, `slo_name`.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `avg_cpu_percent` | real | Average DB CPU as percent of DB capacity | `MonDmRealTimeResourceStats.md` |
| `avg_data_io_percent` | real | Average data IO utilization | `MonDmRealTimeResourceStats.md` |
| `avg_log_write_percent` | real | Average log write utilization | `MonDmRealTimeResourceStats.md` |
| `avg_memory_usage_percent` | real | Average memory utilization | `MonDmRealTimeResourceStats.md` |
| `xtp_storage_percent` | real | XTP/In-Memory OLTP storage usage | `MonDmRealTimeResourceStats.md` |
| `max_worker_percent` | real | Max worker utilization | `MonDmRealTimeResourceStats.md` |
| `max_session_percent` | real | Max session utilization | `MonDmRealTimeResourceStats.md` |
| `dtu_limit` | long | DTU limit; 0 for vCore model | `MonDmRealTimeResourceStats.md` |
| `database_id` | int | Database id | Standard DMV mapping / inferred from doc |
| `replica_type` | int | Replica type (`0` primary/forwarder, `1` secondary) | `MonDmRealTimeResourceStats.md` |
| `server_name` | string | Logical server name for the DB | Inferred from name |
| `database_name` | string | Database name | `MonDmRealTimeResourceStats.kql` filters `database_name` |
| `slo_name` | string | DB service objective name | `MonDmRealTimeResourceStats.md`; `MonDmRealTimeResourceStats.kql` |
| `avg_instance_cpu_percent` | real | Instance CPU percent seen by the DB's host instance | `MonDmRealTimeResourceStats.md` |
| `avg_instance_memory_percent` | real | Instance memory percent seen by the DB's host instance | `MonDmRealTimeResourceStats.md` |

---

## 7. MonBackup — Backup History

### Definition
`MonBackup` records backup service activity for MI databases. It contains backup start/end telemetry, sizes, paths, LSNs, and failure details, and is directly used by MI backup runners to verify full backups after failover.

### Code Source
- **Repositories**: `BusinessAnalytics`, `SqlTelemetry`
- **Key Files**:
  - `BusinessAnalytics:/Src/CosmosConfiguration/StaticSchemas/MonBackup.schema`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/BackupRestore/FullBackupSkippedAfterGeoFailoverMIRunner.cs`
- **Data Origin**: backup service telemetry (`database_backup` events) surfaced through `MonBackup`
- **Evidence**:
  - Schema defines backup path, times, sizes, LSNs, and exception fields.
  - Runner filters `event == 'database_backup'`, `backup_type == 'Full'`, `event_type == 'BACKUP_END'`.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Backup event category, e.g. `database_backup` | `FullBackupSkippedAfterGeoFailoverMIRunner.cs` |
| `event_type` | string | Backup lifecycle event, e.g. `BACKUP_END` | `MonBackup.schema`; runner filters `event_type == 'BACKUP_END'` |
| `logical_server_name` | string | MI server name | `MonBackup.schema`; runner filters `LogicalServerName == ManagedServerName` |
| `logical_database_name` | string | Database name | `MonBackup.schema` |
| `logical_database_id` | string | Database id used as backup-service id | `MonBackup.schema`; runner projects `backup_service_database_id = logical_database_id` |
| `backup_type` | string | `Full`, `Diff`, etc. | `MonBackup.schema`; runner filters `backup_type == 'Full'` |
| `backup_path` | string | Backup artifact path | `MonBackup.schema` |
| `backup_start_date` | string/datetime | Backup start time | `MonBackup.schema` |
| `backup_end_date` | string/datetime | Backup completion time | `MonBackup.schema` |
| `first_lsn` | string | First LSN in backup range | `MonBackup.schema` |
| `last_lsn` | string | Last LSN in backup range | `MonBackup.schema` |
| `backup_size` | string/long | Compressed backup size | `MonBackup.schema` |
| `uncompressed_backup_size` | string/long | Uncompressed backup size | `MonBackup.schema` |
| `br_error_details` | string | Backup/restore error details | `MonBackup.schema` |
| `exception_message` | string | Backup exception message | `MonBackup.schema` |

---

## 8. AlrSQLErrorsReported — SQL Errorlog / Error-Reported Events

### Definition
`AlrSQLErrorsReported` is the structured SQL error-report/event table used for engine error analysis. The searched code references it as the source for system error detection (for example, OS error 112), but the exact producer definition was not found in the searched repos.

### Code Source
- **Repositories**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LogFull.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/AvailabilityManager/AvailabilityManager.cs` (search result)
- **Data Origin**: inferred structured SQL `error_reported` / errorlog telemetry pipeline
- **Evidence**:
  - `LogFull.cs` comment: “The query looks for system error 112 in AlrSQLErrorsReported …”
- **Gap**:
  - Exact producer file for the table itself was not found in the searched repos; per-column source is therefore partly inferred.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `error_number` | int | SQL error number | Inferred from standard `error_reported` naming |
| `severity` | int | SQL severity | Inferred from standard telemetry naming |
| `state` | int | SQL state | Inferred from standard telemetry naming |
| `user_defined` | bool | Whether the error is user-defined | Inferred from name |
| `category` | string | Error/event category | Inferred from name |
| `destination` | string | Sink/destination classification | Inferred from name |
| `is_intercepted` | bool | Whether error was intercepted upstream | Inferred from name |
| `callstack` | string | Captured call stack for the error | Inferred from name |
| `session_id` | int | SQL session id | Inferred from name |
| `database_id` | int | Database id associated with the error | Inferred from name |
| `database_name` | string | Database name associated with the error | Inferred from name |
| `query_hash` | string | Query hash linked to the error context | Inferred from name |
| `query_plan_hash` | string | Query plan hash linked to the error context | Inferred from name |
| `is_azure_connection` | bool | Whether the connection is an Azure-side connection | Inferred from name |

---

## 9. MonSQLSystemHealth — System Health XEvents / Errorlog Lines

### Definition
`MonSQLSystemHealth` is the general SQL-system-health/errorlog table used heavily by troubleshooting code. The code treats it as a view over SQL errorlog/system metadata messages and uses it for startup, recovery, IO, dump, and error-message analysis.

### Code Source
- **Repositories**: `DsMainDev`, `SqlTelemetry`, `SQLLivesiteAgents`
- **Key Files**:
  - `DsMainDev:/Tools/DevScripts/CosmosFetcher/scripts/MonSqlSystemHealth.script`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/BotTroubleshooterRunner/LogRows/MonSQLSystemHealthLogRow.cs`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonSQLSystemHealth.kql`
- **Data Origin**: `MonSQLSystemHealth.view` in Cosmos public views
- **Evidence**:
  - `MonSqlSystemHealth.script` reads `MonSQLSystemHealth.view` directly.
  - Log-row class validates/parses the canonical subset of columns.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Row timestamp used for range filters | `MonSQLSystemHealthLogRow.cs` |
| `PreciseTimeStamp` | datetime | Precise source event time | `MonSQLSystemHealthLogRow.cs` |
| `ClusterName` | string | Cluster/ring hosting the event | `MonSQLSystemHealthLogRow.cs` |
| `NodeRole` | string | Node role | `MonSQLSystemHealthLogRow.cs` |
| `MachineName` | string | Machine name | `MonSQLSystemHealthLogRow.cs` |
| `NodeName` | string | Node name | `MonSQLSystemHealthLogRow.cs` |
| `AppName` | string | SQL worker/app instance name | `MonSQLSystemHealthLogRow.cs` |
| `AppTypeName` | string | Worker/app type | `MonSQLSystemHealthLogRow.cs` |
| `LogicalServerName` | string | Logical server name | `MonSQLSystemHealthLogRow.cs` |
| `message` | string | Errorlog/system-health message text | `MonSQLSystemHealthLogRow.cs`; many `MonSQLSystemHealth.kql` queries filter on `message` |
| `error_id` | int | Parsed SQL error id used in troubleshooting queries | `MonSQLSystemHealth.kql` uses `error_id` repeatedly |
| `process_id` | int | SQL process id | `MonSQLSystemHealth.kql` summarizes by `process_id` |

---

## 10. MonLogin — Login Activity

### Definition
`MonLogin` is the MI/SQL login-attempt telemetry table. It contains final login outcomes, login substep failures, flags, error/state pairs, and timing/auth details.

### Code Source
- **Repositories**: `BusinessAnalytics`, `DsMainDev`, `SQLLivesiteAgents`
- **Key Files**:
  - `BusinessAnalytics:/Src/CosmosConfiguration/StaticSchemas/MonLogin.schema`
  - `DsMainDev:/Tools/DevScripts/CosmosFetcher/scripts/MonLogin.script`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonLogin.kql`
- **Data Origin**: `MonLogin.view` in Cosmos public views
- **Evidence**:
  - `MonLogin.script` reads `MonLogin.view` and filters `eventName in ('process_login_finish','login_substep_failure')`.
  - Schema enumerates login/auth/perf fields.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `logical_server_name` | string | Logical server name | `MonLogin.schema`; `MonLogin.script` filters by it |
| `database_name` | string | Database name | `MonLogin.schema`; `MonLogin.script` filters by it |
| `eventName` | string | Login event name | `MonLogin.script` filters `process_login_finish` / `login_substep_failure` |
| `is_success` | bool | Whether the login succeeded | `MonLogin.schema`; `MonLogin.kql` uses it heavily |
| `is_user_error` | bool | Whether failure is user-caused vs system-caused | `MonLogin.schema`; `MonLogin.kql` filters it |
| `error` | int | SQL/login error number | `MonLogin.schema`; `MonLogin.kql` summarizes by `error` |
| `state` | int | SQL/login error state | `MonLogin.schema`; `MonLogin.kql` summarizes by `state` |
| `lookup_error_code` | int | Upstream lookup/routing error code | `MonLogin.schema`; `MonLogin.kql` projects it |
| `lookup_state` | int | Upstream lookup/routing state | `MonLogin.schema`; `MonLogin.kql` projects it |
| `login_flags` | long | Bit flags describing login mode (e.g. read-only intent) | `MonLogin.schema`; `MonLogin.kql` decodes read-only from `login_flags` |
| `total_time_ms` | long | End-to-end login time | `MonLogin.schema` |
| `driver_name` | string | Client driver name | `MonLogin.schema`; `MonLogin.kql` projects driver info |
| `driver_version` | long | Driver version | `MonLogin.schema` |
| `instance_name` | string | Target instance/ring name used for routing analysis | `MonLogin.schema`; `MonLogin.kql` uses it in ring-address checks |
| `process_id` | long | Process id for backend lifetime analysis | `MonLogin.schema`; `MonLogin.kql` summarizes by `process_id` |

---

## 11. MonManagement — Management Operations

### Definition
`MonManagement` is the broad management/control-plane operations table for SQL/MI. The code uses it to analyze request timelines and UpdateSlo-related operations, and the schema shows it carries RP/CMS request metadata, requested target properties, and workflow state-machine fields.

### Code Source
- **Repositories**: `BusinessAnalytics`, `DsMainDev`
- **Key Files**:
  - `BusinessAnalytics:/Src/CosmosConfiguration/StaticSchemas/MonManagement.schema`
  - `DsMainDev:/Sql/Ntdbms/Hekaton/tools/Azure/HkCosmosTelemetry/Scope/MonManagement.script`
- **Data Origin**: `MonManagement.view` in Cosmos public views; likely RP/management workflow telemetry
- **Evidence**:
  - `MonManagement.script` reads `MonManagement.view` and extracts UpdateSlo request records.
  - `MonManagement.schema` enumerates management-operation payload fields.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `request_id` | string | Management request id | `MonManagement.script` clusters/sorts by `request_id` |
| `originalEventTimestamp` | datetime | Original management event time | `MonManagement.script` summarizes/group-bys it |
| `event` | string | Event emitted during the operation | `MonManagement.script` groups operation rows by event history |
| `logical_database_name` | string | Current logical database name | `MonManagement.script` projects/filter uses it |
| `requested_logical_database_name` | string | Requested target database name | `MonManagement.script` projects/filter uses it |
| `edition` | string | Current edition/SKU | `MonManagement.script` filters/projects it |
| `service_level_objective_name` | string | Current SLO name | `MonManagement.script` projects it |
| `service_level_objective_id` | string | Current SLO id | `MonManagement.script` projects it |
| `requested_logical_database_edition` | string | Requested target edition | `MonManagement.script` projects it |
| `requested_logical_database_slo` | string | Requested target SLO | `MonManagement.script` projects it |
| `operation_type` | string | Type of management operation | `MonManagement.schema` |
| `state_machine_type` | string | Workflow/state-machine driving the request | `MonManagement.schema` |
| `operation_parameters` | string | Serialized operation input parameters | `MonManagement.schema`; similar usage appears in `MonManagementOperations` queries |
| `failover_group_id` | string | Failover-group target id when relevant | `MonManagement.schema` |
| `management_operation_name` | string | Human-readable management action name | `MonManagement.schema` |

---

## 12. MonDmCloudDatabaseWaitStats — Wait Statistics

### Definition
`MonDmCloudDatabaseWaitStats` is the DB-level wait-statistics table. The in-repo documentation describes it as returning wait statistics at database level and maps its `wait_type` values to `sys.dm_os_wait_stats` semantics.

### Code Source
- **Repositories**: `SQL-DB-ON-Call-Common`
- **Key Files**:
  - `SQL-DB-ON-Call-Common:/content/Tools/Kusto/Performance-related-Kusto-Tables/MonDmCloudDatabaseWaitStats.md`
- **Data Origin**: database-level wait stats collection; wait names aligned with `sys.dm_os_wait_stats`
- **Evidence**:
  - Documentation explicitly defines cumulative and delta wait columns.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `database_id` | int | Database id | Inferred from table purpose/name |
| `server_name` | string | Logical server name | Inferred from name |
| `database_name` | string | Database name | Inferred from name |
| `wait_type` | string | Wait type name | `MonDmCloudDatabaseWaitStats.md` |
| `waiting_tasks_count` | long | Cumulative count of waits since startup | `MonDmCloudDatabaseWaitStats.md` |
| `delta_waiting_tasks_count` | long | Incremental waits since previous collection | `MonDmCloudDatabaseWaitStats.md` |
| `wait_time_ms` | long | Cumulative wait time since startup | `MonDmCloudDatabaseWaitStats.md` |
| `delta_wait_time_ms` | long | Incremental wait time since previous collection | `MonDmCloudDatabaseWaitStats.md` |
| `signal_wait_time_ms` | long | Cumulative signal wait time | Inferred from name |
| `delta_signal_wait_time_ms` | long | Incremental signal wait time | Inferred from name |

---

## 13. MonAnalyticsDBSnapshot — Database Snapshot Properties

### Definition
`MonAnalyticsDBSnapshot` is the core MI/DB inventory snapshot table used to identify the latest logical/physical database mapping, service URI, SLO, usage state, and placement/ring metadata.

### Code Source
- **Repositories**: `SqlTelemetry`, `SQLLivesiteAgents`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/BotTroubleshooterRunner/LogRows/MonAnalyticsDBSnapshotLogRow.cs`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonAnalyticsDBSnapshot.kql`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/AvailabilityManager/AvailabilityManager.cs` (comments describe CMS real-time snapshot modeling)
- **Data Origin**: analytics/CMS snapshot of database metadata
- **Evidence**:
  - Log-row class validates/parses core columns.
  - KQL query uses this table to derive `logical_database_id`, `physical_database_id`, `fabric_partition_id`, `tenant_ring_name`, `database_usage_status`, etc.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `logical_server_name` | string | Logical server name | `MonAnalyticsDBSnapshotLogRow.cs`; `MonAnalyticsDBSnapshot.kql` |
| `logical_database_id` | string | Logical database id | `MonAnalyticsDBSnapshotLogRow.cs`; `MonAnalyticsDBSnapshot.kql` |
| `logical_database_name` | string | Logical database name | `MonAnalyticsDBSnapshotLogRow.cs`; `MonAnalyticsDBSnapshot.kql` |
| `physical_database_id` | string | Physical database id | `MonAnalyticsDBSnapshotLogRow.cs`; `MonAnalyticsDBSnapshot.kql` |
| `sql_instance_name` | string | SQL instance/app name hosting the DB | `MonAnalyticsDBSnapshotLogRow.cs`; `MonAnalyticsDBSnapshot.kql` |
| `state` | string | Current DB lifecycle state | `MonAnalyticsDBSnapshot.kql` projects `state` |
| `physical_database_state` | string | Physical DB state | `MonAnalyticsDBSnapshot.kql` projects it |
| `database_type` | string | Database type classification | `MonAnalyticsDBSnapshot.kql` projects it |
| `edition` | string | Edition/SKU | `MonAnalyticsDBSnapshot.kql` projects it |
| `service_level_objective` | string | Service objective | `MonAnalyticsDBSnapshot.kql` projects it |
| `tenant_ring_name` | string | Tenant ring / placement ring | `MonAnalyticsDBSnapshotLogRow.cs`; `MonAnalyticsDBSnapshot.kql` |
| `customer_subscription_id` | string | Customer subscription id | `MonAnalyticsDBSnapshot.kql` projects it |
| `failover_group_id` | string | Failover-group id | `MonAnalyticsDBSnapshot.kql` projects it |
| `backup_retention_days` | int | Backup retention days | Inferred from name |
| `create_mode` | string | DB creation mode | `MonAnalyticsDBSnapshot.kql` projects it |
| `max_size_bytes` | long | Maximum DB size | Inferred from name |
| `database_usage_status` | string | Active vs `UpdateSloTarget` style usage state | `MonAnalyticsDBSnapshot.kql` comments and projections |

---

## 14. MonWiQdsExecStats — Query Store Execution Stats

### Definition
`MonWiQdsExecStats` is the Query Store execution-statistics telemetry table. The in-repo documentation says it is driven by the `query_store_runtime_stats_update` event and is used for per-query/per-plan CPU, duration, IO, memory grant, DOP, and rowcount analysis.

### Code Source
- **Repositories**: `SQL-DB-ON-Call-Common`
- **Key Files**:
  - `SQL-DB-ON-Call-Common:/content/Tools/Kusto/Performance-related-Kusto-Tables/MonWiQdsExecStats.md`
- **Data Origin**: Query Store runtime statistics update events
- **Evidence**:
  - The markdown doc explicitly says the event is `query_store_runtime_stats_update` and documents execution-stat columns.

### Columns

| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `query_id` | long | Query Store query id | `MonWiQdsExecStats.md` |
| `plan_id` | long | Query Store plan id | Inferred from Query Store naming |
| `query_hash` | string | Hash of query logic | `MonWiQdsExecStats.md` |
| `query_plan_hash` | string | Hash of query plan | `MonWiQdsExecStats.md` |
| `server_name` | string | Logical server name | Inferred from name |
| `database_name` | string | Database name | `MonWiQdsExecStats.md` sample query |
| `execution_count` | int | Total executions during the exhaust period | `MonWiQdsExecStats.md` |
| `cpu_time` | long | Total CPU time (microseconds) for the period | `MonWiQdsExecStats.md` |
| `elapsed_time` | long | Total elapsed time (microseconds) for the period | `MonWiQdsExecStats.md` |
| `logical_reads` | long | Total logical reads | `MonWiQdsExecStats.md` |
| `physical_reads` | long | Total physical reads | `MonWiQdsExecStats.md` |
| `logical_writes` | long | Total logical writes | `MonWiQdsExecStats.md` |
| `rowcount` | long | Total row count | `MonWiQdsExecStats.md` |
| `dop` | int | Total DOP across executions; divide by `execution_count` for avg | `MonWiQdsExecStats.md` |
| `log_bytes_used` | long | Total log bytes used | `MonWiQdsExecStats.md` |
| `tempdb_space_used` | long | Total tempdb space used | `MonWiQdsExecStats.md` |
| `max_query_memory_pages` | long | Total memory grant pages | `MonWiQdsExecStats.md` |
| `exec_type` | int | Execution outcome (`0` success, `3` client abort, `4` exception abort) | `MonWiQdsExecStats.md` |

---

## Notes on Confidence / Gaps

- **Highest confidence** sections are those backed by explicit schema/docs or direct parsing classes: `MonLogin`, `MonBackup`, `MonManagement`, `MonSQLSystemHealth`, `MonAnalyticsDBSnapshot`, `MonDmRealTimeResourceStats`, `MonDmCloudDatabaseWaitStats`, `MonWiQdsExecStats`.
- **Medium confidence** sections are the MI metadata tables inferred from runner queries and matching CMS SQL: `MonManagedServers`, `MonManagedDatabases`, `MonGeoDRFailoverGroups`, `MonManagedInstanceResourceStats`, `MonDbSeedTraces`.
- **Lowest confidence** is `AlrSQLErrorsReported`: code references were found, but the exact producing file was not found in the searched repos, so column meanings are mostly inferred from the table name and standard SQL `error_reported` telemetry semantics.

## 15. AlrMetricsForLogsToMetricsV1 — Logs-to-metrics materialization output

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 16. AlrSharedMAHeartbeat — Heartbeat telemetry for MA agents

### Definition
Appears to store heartbeat pings from Managed Agent services (`NodeMA`, `SharedMA`, `OtelMA`) used by internal health dashboards.

### Code Source
- **Repositories**: `MDM_SQL_AzureDBPrep`
- **Key Files**:
  - `MDM_SQL_AzureDBPrep:/Dashboards/Telemetry Platform/Prod/MA Health Monitoring.json`
- **Evidence**:
  - Dashboard queries group by `NodeMDSAgentSvc` and use `ClusterName`, `NodeName`, and `TIMESTAMP`.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Heartbeat time | `MA Health Monitoring.json` |
| `ClusterName` | string | Cluster emitting the heartbeat | `MA Health Monitoring.json` |
| `NodeName` | string | Node emitting the heartbeat | `MA Health Monitoring.json` |
| `NodeMDSAgentSvc` | string | Agent service identity (`NodeMA`, `SharedMA`, `OtelMA`) | `MA Health Monitoring.json` |

## 17. AlrSqlSatelliteRunner — SQL satellite runner alerts

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 18. AlrWinFabHealthApplicationState — Service Fabric application health snapshots

### Definition
Service Fabric application-level health state emitted by MDS directory watchers from the `AppSt` channel.

### Code Source
- **Repositories**: `SQL2017`
- **Key Files**:
  - `SQL2017:/Sql/xdb/externals/mds/CentralMDSAgentConfig_template.xml`
- **Evidence**:
  - The config declares `eventName="AlrWinFabHealthApplicationState"` and maps it to the `\AppSt` directory.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ClusterName` | string | Cluster identity | MDS config / query usage |
| `ApplicationName` | string | Service Fabric application name | query usage |
| `HealthState` | string | Current health state | query usage |
| `Description` | string | Health details | query usage |
| `SourceId` | string | Source emitting the health record | query usage |

## 19. AlrWinFabHealthNodeEvent — Service Fabric node health events

### Definition
Service Fabric node-level health events emitted by MDS directory watchers from the `NodeEv` channel.

### Code Source
- **Repositories**: `SQL2017`
- **Key Files**:
  - `SQL2017:/Sql/xdb/externals/mds/CentralMDSAgentConfig_template.xml`
- **Evidence**:
  - The config declares `eventName="AlrWinFabHealthNodeEvent"` and maps it to the `\NodeEv` directory.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ClusterName` | string | Cluster identity | MDS config / query usage |
| `NodeName` | string | Service Fabric node name | query usage |
| `HealthState` | string | Node health state | query usage |
| `Description` | string | Health details | query usage |

## 20. AlrWinFabHealthPartitionEvent — Service Fabric partition health events

### Definition
Service Fabric partition-level health events emitted by MDS directory watchers from the `PartEv` channel.

### Code Source
- **Repositories**: `SQL2017`
- **Key Files**:
  - `SQL2017:/Sql/xdb/externals/mds/CentralMDSAgentConfig_template.xml`
- **Evidence**:
  - The config declares `eventName="AlrWinFabHealthPartitionEvent"` and maps it to the `\PartEv` directory.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ClusterName` | string | Cluster identity | MDS config / query usage |
| `ServiceName` | string | Service containing the partition | query usage |
| `HealthState` | string | Partition health state | query usage |
| `Description` | string | Health details | query usage |

## 21. AlrWinFabHealthReplicaEvent — Service Fabric replica health events

### Definition
Service Fabric replica-level health events emitted by MDS directory watchers from the `RepEv` channel.

### Code Source
- **Repositories**: `SQL2017`
- **Key Files**:
  - `SQL2017:/Sql/xdb/externals/mds/CentralMDSAgentConfig_template.xml`
- **Evidence**:
  - The config declares `eventName="AlrWinFabHealthReplicaEvent"` and maps it to the `\RepEv` directory.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ClusterName` | string | Cluster identity | MDS config / query usage |
| `ServiceName` | string | Replica's service | query usage |
| `HealthState` | string | Replica health state | query usage |
| `Description` | string | Health details | query usage |

## 22. AlrWinFabHealthServiceState — Service Fabric service health snapshots

### Definition
Service Fabric service-level health state emitted by MDS directory watchers from the `SvcSt` channel.

### Code Source
- **Repositories**: `SQL2017`
- **Key Files**:
  - `SQL2017:/Sql/xdb/externals/mds/CentralMDSAgentConfig_template.xml`
- **Evidence**:
  - The config declares `eventName="AlrWinFabHealthServiceState"` and maps it to the `\SvcSt` directory.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ClusterName` | string | Cluster identity | MDS config / query usage |
| `ServiceName` | string | Service Fabric service name | query usage |
| `HealthState` | string | Service health state | query usage |
| `Description` | string | Health details | query usage |

## 23. MonAdoDeploymentCabSnapshot — Latest ADO CAB work-item snapshot for deployment automation

### Definition
Stores ADO CAB work items ingested by the EZ-CAB deployment runner; the companion Kusto view/function computes latest state per item using `LastModifiedTime`.

### Code Source
- **Repositories**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/Deployment/DeploymentEzCabAdoRunner/DeploymentAdoEzCabSnapshot.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/Deployment/Schema/Views.csl`
- **Evidence**:
  - Runner sets `_targetTable = "MonAdoDeploymentCabSnapshot"`.
  - `Views.csl` derives latest state with `arg_max(LastModifiedTime, *)`.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `LastModifiedTime` | datetime | Last ADO work-item modification time | `DeploymentAdoEzCabSnapshot.cs`, `Views.csl` |
| `BugSource` | string | Source tag for ingested work items (`AdoEzCabExtension`) | `DeploymentAdoEzCabSnapshot.cs` |

## 24. MonAppEventLogErrors — Windows application event-log errors

### Definition
Application event-log error stream consumed by consolidation logic; one downstream use filters `EventID == '1000'` to derive crash telemetry.

### Code Source
- **Repositories**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/Telemetry/Kusto/Consolidation/ConsolidationRunner.cs`
- **Evidence**:
  - Consolidation logic reads `MonAppEventLogErrors`, filters `EventID == '1000'`, and projects crash fields.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `EventID` | string | Windows event identifier | `ConsolidationRunner.cs` |
| `EventDescription` | string | Event text payload | `ConsolidationRunner.cs` |
| `TIMESTAMP` | datetime | Event time | `ConsolidationRunner.cs` |
| `PreciseTimeStamp` | datetime | Precise event time | `ConsolidationRunner.cs` |
| `ClusterName` | string | Cluster identity | `ConsolidationRunner.cs` |
| `NodeName` | string | Node identity | `ConsolidationRunner.cs` |

## 25. MonAttentions — Client-cancel / attention events

### Definition
Attention events used in performance triage to identify cancellations from client drivers.

### Code Source
- **Repositories**: `TSG-SQL-DB-Performance`
- **Key Files**:
  - `TSG-SQL-DB-Performance:/content/Common-Perf-Queue-TSGs/CRI-Flowchart/MMSOP-Memory-Management-SOPs.md`
- **Evidence**:
  - TSG explicitly says “Check if there are cancellations from client driver” and queries `MonAttentions`.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Attention time | TSG query |
| `NodeName` | string | Node where attention occurred | TSG query |
| `duration` | long | Duration associated with the attention | TSG query |
| `database_name` | string | Database name | TSG query |
| `client_app_name` | string | Client application name | TSG query |
| `client_hostname` | string | Client host name | TSG query |
| `session_id` | int | Session id | TSG query |
| `event` | string | Event name | TSG query |
| `sessionName` | string | Session label | TSG query |

## 26. MonAuditOperational — Operational audit telemetry

### Definition
Referenced in KQL templates only. Search returned no reliable defining file.

### Code Source
- **Search result**: no code hit found.

## 27. MonAuditOperationalTelemetry — Operational audit telemetry extension

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 28. MonAuditRuntimeTelemetry — Runtime audit events sent to Cosmos

### Definition
Audit runtime telemetry table registered in Cosmos collection workflows for the auditing component.

### Code Source
- **Repositories**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Workflow registration calls `SetNewCosmosCollectionWorkflowTemplateRecord(tableName: "MonAuditRuntimeTelemetry", component: Component.Auditing, ...)`.

## 29. MonAuditSessionStatus — Audit session status stream

### Definition
Audit session-status telemetry registered in Cosmos collection workflows for the auditing component.

### Code Source
- **Repositories**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Workflow registration calls `SetNewCosmosCollectionWorkflowTemplateRecord(tableName: "MonAuditSessionStatus", component: Component.Auditing, ...)`.

## 30. MonAutomaticTuning — Automatic tuning regression/correction telemetry

### Definition
Explicitly modeled in unit-test seed data with `.create table` statements and sample rows for automatic tuning events.

### Code Source
- **Repositories**: `SqlLivesiteCopilot`
- **Key Files**:
  - `SqlLivesiteCopilot:/SQLPerfCopilot/PerfCopilotBot/SqlSkillUnitTest/SkillTest/APRC/DataSeeding.yaml`
- **Evidence**:
  - The seed file contains `.create table MonAutomaticTuning (...)` and sample inserts.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `originalEventTimestamp` | datetime | Event time | `DataSeeding.yaml` |
| `AppName` | string | SQL app / instance name | `DataSeeding.yaml` |
| `ClusterName` | string | Cluster identity | `DataSeeding.yaml` |
| `NodeName` | string | Node identity | `DataSeeding.yaml` |
| `LogicalServerName` | string | Logical server | `DataSeeding.yaml` |
| `logical_database_name` | string | Database name | `DataSeeding.yaml` |
| `event` | string | Tuning event kind | `DataSeeding.yaml` |
| `query_id` | long | Query Store query id | `DataSeeding.yaml` |
| `current_plan_id` | long | Current plan id | `DataSeeding.yaml` |
| `last_good_plan_id` | long | Last known good plan id | `DataSeeding.yaml` |
| `is_regression_detected` | bool | Regression detection flag | `DataSeeding.yaml` |
| `is_regression_corrected` | bool | Correction flag | `DataSeeding.yaml` |

## 31. MonAzureActiveDirService — Azure AD service telemetry

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 32. MonBackupFull — Full backup telemetry

### Definition
Referenced in KQL templates only. Search returned no reliable defining file for this exact table name.

### Code Source
- **Search result**: no code hit found for the exact name.

## 33. MonBillingBackupDatabaseSize — Billing snapshot of backup database size

### Definition
Billing telemetry table registered in Cosmos collection workflows; no stronger schema file was found in the allotted searches.

### Code Source
- **Repositories**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Workflow registration calls `SetNewCosmosCollectionWorkflowTemplateRecord(tableName: "MonBillingBackupDatabaseSize", component: Component.Billing, ...)`.

## 34. MonBillingGeoSnapshotSize — Billing geo-snapshot size telemetry

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 35. MonBillingSnapshotSize — Billing snapshot size telemetry

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 36. MonBlockedProcessReportFiltered — Filtered blocked-process reports

### Definition
Blocking-chain telemetry wrapped by performance copilot code and used to summarize lead blockers.

### Code Source
- **Repositories**: `SqlLivesiteCopilot`
- **Key Files**:
  - `SqlLivesiteCopilot:/SQLPerfCopilot/PerfCopilotBot/SqlDriCopilotAPI/Blocking.cs`
- **Evidence**:
  - `BlockeeSession` is documented as a wrapper over records in `MonBlockedProcessReportFiltered`.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `monitorLoop` | int | Blocking sample iteration id | `Blocking.cs` |
| `blockee_session_id` | int | Blocked session id | `Blocking.cs` |
| `blocker_session_id` | int | Blocking session id | `Blocking.cs` |
| `blockee_waittime_ms` | long | Wait time for blocked session | `Blocking.cs` |
| `blocker_queryhash` | string | Query hash for blocker | `Blocking.cs` |
| `blocker_clientapp` | string | Blocker client app | `Blocking.cs` |
| `blocker_status` | string | Blocker status | `Blocking.cs` |
| `blocker_trancount` | int | Blocker transaction count | `Blocking.cs` |
| `blocker_transactionid` | long | Blocker transaction id | `Blocking.cs` |
| `blocker_isolationlevel` | string | Blocker isolation level | `Blocking.cs` |
| `blocker_waitresource` | string | Wait resource | `Blocking.cs` |
| `blocker_lastbatchstarted` | datetime | Last batch start time | `Blocking.cs` |
| `blocker_lastbatchcompleted` | datetime | Last batch completion time | `Blocking.cs` |
| `originalEventTimestamp` | datetime | Detection time | `Blocking.cs` |

## 37. MonCapacityTenantSnapshot — Capacity state snapshot for tenant rings

### Definition
Capacity snapshot table validated by DmvCollector tests; tests assert many required columns that describe placement, overbooking, connectivity, and zone metadata.

### Code Source
- **Repositories**: `DsMainDev`
- **Key Files**:
  - `DsMainDev:/Sql/xdb/tests/suites/DmvCollector/DmvCollectorQueryUnitTests.cs`
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Unit test `DmvCollectorQuery_MonCapacityTenantSnapshotTest` enumerates required columns.
  - Cosmos deployment registers the table for collection.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `placement_affinity_tag` | string | Placement affinity | `DmvCollectorQueryUnitTests.cs` |
| `overbooking_ratio_percentage` | numeric | Overbooking ratio | `DmvCollectorQueryUnitTests.cs` |
| `effective_overbooking_ratio_percentage` | numeric | Effective overbooking ratio | `DmvCollectorQueryUnitTests.cs` |
| `replica_count` | int | Current replica count | `DmvCollectorQueryUnitTests.cs` |
| `maintenance_schedule_id` | string | Maintenance schedule | `DmvCollectorQueryUnitTests.cs` |
| `physical_zone` | string | Physical zone | `DmvCollectorQueryUnitTests.cs` |
| `used_cpu_capacity_smcu` | numeric | Used SMCU CPU capacity | `DmvCollectorQueryUnitTests.cs` |
| `used_cpu_capacity_dsmcu` | numeric | Used DSMCU CPU capacity | `DmvCollectorQueryUnitTests.cs` |

## 38. MonCDCTraces — Change Data Capture traces

### Definition
CDC telemetry table registered in Cosmos collection workflows. I did not find a stronger schema file in the allotted searches.

### Code Source
- **Repositories**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Workflow registration calls `SetNewCosmosCollectionWorkflowTemplateRecord(tableName: "MonCDCTraces", ...)`.

## 39. MonChangeManagedServerInstanceReqs — Managed-server change request telemetry

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 40. MonClusterLoad — Cluster/node health state reports

### Definition
Cluster-load table used by availability queries to inspect node health, node status, and uptime via `node_state_report` events.

### Code Source
- **Repositories**: `SQLLivesiteAgents`, `BusinessAnalytics`
- **Key Files**:
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonClusterLoad.kql`
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Availability query filters `event == "node_state_report"` and projects `health_state`, `node_status`, and `node_up_time`.
  - Cosmos deployment registers the table for collection.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Report time | `MonClusterLoad.kql` |
| `event` | string | Event type (`node_state_report`) | `MonClusterLoad.kql` |
| `ClusterName` | string | Cluster identity | `MonClusterLoad.kql` |
| `node_name` | string | Node name | `MonClusterLoad.kql` |
| `health_state` | string | Node health state | `MonClusterLoad.kql` |
| `node_status` | string | Node availability status | `MonClusterLoad.kql` |
| `node_up_time` | timespan | Node uptime | `MonClusterLoad.kql` |

## 41. MonConfigAppTypeOverrides — App-type configuration overrides

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 42. MonConfigLogicalServerOverrides — Logical-server configuration overrides

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 43. MonContainerShare — ContainerShareUtil / CSU operational telemetry

### Definition
ContainerShareUtil emits XEvents into `MonContainerShare`; internal TSGs then query the table for CRL transfer, import, and OOM analysis.

### Code Source
- **Repositories**: `DsMainDev`, `TSG-SQL-MI-Networking`
- **Key Files**:
  - `DsMainDev:/Sql/xdb/WCOW/ContainerShareUtil/Exe/XEvents/CsuHeartbeatEvent.cs`
  - `TSG-SQL-MI-Networking:/content/operational/active-production-problems/Deprecated/CSU-Slow-CRL-Import.md`
- **Evidence**:
  - `CsuHeartbeatEvent` says it is emitted periodically to `MonContainerShare`.
  - TSG queries use fields for CRL transfer/import and OOM detection.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `session_id` | guid/string | CSU session id | `CsuHeartbeatEvent.cs`, TSG query |
| `message` | string | CSU log message | `CsuHeartbeatEvent.cs` |
| `level` | string | Log level | `CsuHeartbeatEvent.cs` |
| `host_environment_type` | string | Host/container perspective | TSG query |
| `operation` | string | CSU operation name | TSG query |
| `step` | string | Operation step | TSG query |
| `exception_type` | string | Exception classification | TSG query |
| `stack_trace` | string | Stack trace | TSG query |
| `certificate_thumbprint` | string | Certificate/CRL identifier | TSG query |

## 44. MonCounterFiveMinute — Five-minute performance counter rollups

### Definition
Five-minute aggregated performance-counter table used by connectivity monitors and general node/cluster diagnostics.

### Code Source
- **Repositories**: `SqlTelemetry`, `BusinessAnalytics`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/Connectivity/LsassPrivilegedTimeMonitor.cs`
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Monitor queries `MonCounterFiveMinute` for `CounterName == "\\Process(Lsass)\\% Privileged Time"` and uses `MaxVal`, `NodeRole`, `ClusterName`, `NodeName`.
  - Cosmos deployment registers the table for collection.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Five-minute bucket time | `LsassPrivilegedTimeMonitor.cs` |
| `CounterName` | string | Counter path/name | `LsassPrivilegedTimeMonitor.cs` |
| `MaxVal` | numeric | Maximum value in bucket | `LsassPrivilegedTimeMonitor.cs` |
| `NodeRole` | string | Node role (for example `DB`) | `LsassPrivilegedTimeMonitor.cs` |
| `ClusterName` | string | Cluster identity | `LsassPrivilegedTimeMonitor.cs` |
| `NodeName` | string | Node identity | `LsassPrivilegedTimeMonitor.cs` |

## 45. MonCTTraces — Change Tracking traces

### Definition
Change Tracking telemetry used to detect `syscommittab_cleanup_alert` and related backend processing failures.

### Code Source
- **Repositories**: `SqlTelemetry`, `BusinessAnalytics`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/SyscommittabCleanupAlertRunner.cs`
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Runner queries `MonCTTraces` and filters `event == 'syscommittab_cleanup_alert'`.
  - Cosmos deployment registers the table for collection.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Trace time | `SyscommittabCleanupAlertRunner.cs` |
| `event` | string | CT event name | `SyscommittabCleanupAlertRunner.cs` |
| `rows_in_delay` | long | Delayed rows count | `SyscommittabCleanupAlertRunner.cs` |
| `logical_database_name` | string | Database name | `SyscommittabCleanupAlertRunner.cs` |
| `database_id` | int | Database id | `SyscommittabCleanupAlertRunner.cs` |
| `physical_database_guid` | guid/string | Physical DB guid | `SyscommittabCleanupAlertRunner.cs` |
| `logical_database_guid` | guid/string | Logical DB guid | `SyscommittabCleanupAlertRunner.cs` |
| `ClusterName` | string | Cluster identity | `SyscommittabCleanupAlertRunner.cs` |
| `AppTypeName` | string | App type | `SyscommittabCleanupAlertRunner.cs` |
| `AppName` | string | App / instance name | `SyscommittabCleanupAlertRunner.cs` |
| `LogicalServerName` | string | Logical server | `SyscommittabCleanupAlertRunner.cs` |

## 46. MonCvBranchBuildVersionMetadata — Branch/build version metadata

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 47. MonDatabaseEncryptionKeys — Database encryption key metadata

### Definition
Explicit static schema describing database encryption-key metadata collected by monitoring.

### Code Source
- **Repositories**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/CosmosConfiguration/StaticSchemas/MonDatabaseEncryptionKeys.schema`
- **Evidence**:
  - The static schema file enumerates the table columns and types.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Collection time | `MonDatabaseEncryptionKeys.schema` |
| `PreciseTimeStamp` | datetime | Precise collection time | `MonDatabaseEncryptionKeys.schema` |
| `ClusterName` | string | Cluster identity | `MonDatabaseEncryptionKeys.schema` |
| `NodeName` | string | Node identity | `MonDatabaseEncryptionKeys.schema` |
| `AppName` | string | SQL app / instance name | `MonDatabaseEncryptionKeys.schema` |
| `LogicalServerName` | string | Logical server | `MonDatabaseEncryptionKeys.schema` |
| `logical_database_id` | string | Logical database id | `MonDatabaseEncryptionKeys.schema` |
| `is_primary_replica` | int64 | Primary replica flag | `MonDatabaseEncryptionKeys.schema` |
| `is_encrypted` | int16 | Encryption enabled flag | `MonDatabaseEncryptionKeys.schema` |
| `name` | string | Encryption key name | `MonDatabaseEncryptionKeys.schema` |
| `database_id` | int64 | Database id | `MonDatabaseEncryptionKeys.schema` |
| `encryption_state` | int64 | Encryption state | `MonDatabaseEncryptionKeys.schema` |
| `key_algorithm` | string | Key algorithm | `MonDatabaseEncryptionKeys.schema` |
| `key_length` | int64 | Key length | `MonDatabaseEncryptionKeys.schema` |
| `encryptor_thumbprint` | string | Encryptor thumbprint | `MonDatabaseEncryptionKeys.schema` |
| `encryptor_type` | string | Encryptor type | `MonDatabaseEncryptionKeys.schema` |
| `percent_complete` | float | Encryption progress | `MonDatabaseEncryptionKeys.schema` |

## 48. MonDatabaseMetadata — Unified system-table metadata inventory

### Definition
A merged metadata table built by combining tagged columns from many system tables into `MonDatabaseMetadata`.

### Code Source
- **Repositories**: `BusinessAnalytics`, `SQL2019`
- **Key Files**:
  - `BusinessAnalytics:/Src/CosmosConfiguration/StaticSchemas/MonDatabaseMetadata.schema`
  - `SQL2019:/Sql/xdb/ExternalMonitoring/ValidateComplianceTags/ValidateDatabaseMetadataTagTask.cs`
- **Evidence**:
  - The static schema lists the emitted columns/types.
  - `ValidateDatabaseMetadataTagTask` explicitly says it combines system-table columns under `MonDatabaseMetadata`.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `LogicalServerName_DT_String` | string | Logical server name | `MonDatabaseMetadata.schema` |
| `logical_db_name_DT_String` | string | Logical database name | `MonDatabaseMetadata.schema` |
| `physical_db_name_DT_String` | string | Physical database name | `MonDatabaseMetadata.schema` |
| `logical_database_guid_DT_String` | string | Logical database guid | `MonDatabaseMetadata.schema` |
| `physical_database_guid_DT_String` | string | Physical database guid | `MonDatabaseMetadata.schema` |
| `table_name_DT_String` | string | Source system table name | `MonDatabaseMetadata.schema` |
| `name_DT_String` | string | Metadata name/value key | `MonDatabaseMetadata.schema` |
| `value_DT_String` | string | Metadata value | `MonDatabaseMetadata.schema` |
| `type_desc_DT_String` | string | Type description | `MonDatabaseMetadata.schema` |
| `timestamp_DT_DateTime` | datetime | Collection time | `MonDatabaseMetadata.schema` |

## 49. MonDeadlockReportsFiltered — Filtered deadlock XML reports

### Definition
Deadlock-report table that stores filtered XML deadlock graphs for Kusto-based deadlock investigation.

### Code Source
- **Repositories**: `SQL-DB-ON-Call-Common`
- **Key Files**:
  - `SQL-DB-ON-Call-Common:/content/Tools/Kusto/Performance-related-Kusto-Tables/MonDeadlockReportsFiltered.md`
- **Evidence**:
  - The doc explicitly says event `xml_deadlock_report_filtered` is fired into `MonDeadlockReportsFiltered`.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `AppName` | string | SQL app / instance name | `MonDeadlockReportsFiltered.md` |
| `originalEventTimestamp` | datetime | Event time | `MonDeadlockReportsFiltered.md` |
| `LogicalServerName` | string | Logical server | `MonDeadlockReportsFiltered.md` |
| `database_name` | string | Database name | `MonDeadlockReportsFiltered.md` |
| `event` | string | Event name (`xml_deadlock_report_filtered`) | `MonDeadlockReportsFiltered.md` |
| `xml_report_filtered` | string/xml | Deadlock graph payload | `MonDeadlockReportsFiltered.md` |

## 50. MonDeploymentAutomation — Deployment Automation control-ring telemetry

### Definition
Deployment Automation telemetry for buildouts and MI deployment workflows on the control ring.

### Code Source
- **Repositories**: `Doc-SQL-Deployment-Infrastructure`
- **Key Files**:
  - `Doc-SQL-Deployment-Infrastructure:/TechDocs/Telemetry/MonDeploymentAutomation.md`
- **Evidence**:
  - The doc explicitly describes the table and provides a telemetry summary.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Event time | `MonDeploymentAutomation.md` |
| `PreciseTimeStamp` | datetime | Precise event time | `MonDeploymentAutomation.md` |
| `ClusterName` | string | Cluster identity | `MonDeploymentAutomation.md` |
| `NodeName` | string | Node identity | `MonDeploymentAutomation.md` |
| `AppName` | string | App being deployed | `MonDeploymentAutomation.md` |
| `AppTypeName` | string | App type | `MonDeploymentAutomation.md` |
| `LogicalServerName` | string | Logical server | `MonDeploymentAutomation.md` |
| `package` | string | Package info | `MonDeploymentAutomation.md` |
| `event` | string | Deployment event kind | `MonDeploymentAutomation.md` |
| `sessionName` | string | Session name | `MonDeploymentAutomation.md` |
| `originalEventTimestamp` | datetime | Original event time | `MonDeploymentAutomation.md` |
| `version` | string | Deployment version | `MonDeploymentAutomation.md` |
| `severity` | string | Severity | `MonDeploymentAutomation.md` |
| `component` | string | Originating component | `MonDeploymentAutomation.md` |
| `message` | string | Descriptive message | `MonDeploymentAutomation.md` |
| `process_id` | int | Process id | `MonDeploymentAutomation.md` |
| `service_name` | string | Service name | `MonDeploymentAutomation.md` |
| `service_type` | string | Service type | `MonDeploymentAutomation.md` |
| `service_address` | string | Service address | `MonDeploymentAutomation.md` |
| `exception` | string | Exception details | `MonDeploymentAutomation.md` |
| `stack_trace` | string | Stack trace | `MonDeploymentAutomation.md` |

## 51. MonDeploymentAutomationInstances — Deployment Automation instance inventory/status

### Definition
Referenced in KQL templates only. Search returned no reliable defining file for this exact table name.

### Code Source
- **Search result**: no code hit found for the exact name.

## 52. MonDmContinuousCopyStatus — Continuous-copy / geo-replication status DMV snapshot

### Definition
DMV snapshot used to identify geo-primary vs forwarder roles for continuous-copy links.

### Code Source
- **Repositories**: `SQLLivesiteAgents`, `BusinessAnalytics`
- **Key Files**:
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonDmContinuousCopyStatus.kql`
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Query filters `link_type == 'LAG_REPLICA_LINK_TYPE_CONTINUOUS_COPY'` and derives geo roles from `is_target_role`.
  - Cosmos deployment registers the table for collection.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `PreciseTimeStamp` | datetime | Snapshot time | `MonDmContinuousCopyStatus.kql` |
| `LogicalServerName` | string | Local logical server | `MonDmContinuousCopyStatus.kql` |
| `partner_server` | string | Partner logical server | `MonDmContinuousCopyStatus.kql` |
| `partner_database` | string | Partner database | `MonDmContinuousCopyStatus.kql` |
| `link_type` | string | Replication link type | `MonDmContinuousCopyStatus.kql` |
| `is_target_role` | int/bool | Target-role indicator | `MonDmContinuousCopyStatus.kql` |
| `NodeName` | string | Node identity | `MonDmContinuousCopyStatus.kql` |
| `AppName` | string | App / instance name | `MonDmContinuousCopyStatus.kql` |

## 53. MonDmDbHadrReplicaStates — HADR replica-state DMV snapshot

### Definition
DMV snapshot of HADR replica states for logical databases, used heavily in failover/HA investigations.

### Code Source
- **Repositories**: `DsMainDev`, `SQLLivesiteAgents`, `BusinessAnalytics`
- **Key Files**:
  - `DsMainDev:/Tools/DevScripts/CosmosFetcher/scripts/MonDmDbHadrReplicaStates.script`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonDmDbHadrReplicaStates.kql`
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - CosmosFetcher script points at `MonDmDbHadrReplicaStates.view`.
  - Availability query uses `internal_state_desc`, `database_state_desc`, `synchronization_state_desc`, and `secondary_lag_seconds`.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `LogicalServerName` | string | Logical server | `MonDmDbHadrReplicaStates.script` |
| `logical_database_name` | string | Database name | `MonDmDbHadrReplicaStates.script` |
| `PreciseTimeStamp` | datetime | Snapshot time | `MonDmDbHadrReplicaStates.kql` |
| `ClusterName` | string | Cluster identity | `MonDmDbHadrReplicaStates.kql` |
| `NodeName` | string | Node identity | `MonDmDbHadrReplicaStates.kql` |
| `internal_state_desc` | string | Replica internal role/state | `MonDmDbHadrReplicaStates.kql` |
| `database_state_desc` | string | Database state | `MonDmDbHadrReplicaStates.kql` |
| `synchronization_state_desc` | string | Sync state | `MonDmDbHadrReplicaStates.kql` |
| `is_local` | int/bool | Local-replica flag | `MonDmDbHadrReplicaStates.kql` |
| `secondary_lag_seconds` | long | Replica lag in seconds | query resource doc |

## 54. MonDmDbResourceGovernance — Per-database resource governance limits

### Definition
DB resource-governance snapshot used to inspect SLO, CPU, memory, session, and worker limits for a database.

### Code Source
- **Repositories**: `BI_AS_Engine_Office_CC`
- **Key Files**:
  - `BI_AS_Engine_Office_CC:/TestTools/SQLAzureDevOpsKit/TSGCompanionSterling/Resources/Queries.Designer.cs`
- **Evidence**:
  - Embedded query `LimitsDBResource` targets `MonDmDbResourceGovernance` and selects core limit columns.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `LogicalServerName` | string | Logical server | `Queries.Designer.cs` |
| `database_name` | string | Database name | `Queries.Designer.cs` |
| `NodeName` | string | Node identity | `Queries.Designer.cs` |
| `slo_name` | string | SLO name | `Queries.Designer.cs` |
| `primary_bucket_fill_rate_cpu` | numeric | CPU fill rate | `Queries.Designer.cs` |
| `primary_group_max_cpu` | numeric | CPU limit | `Queries.Designer.cs` |
| `min_cores` | numeric | Minimum cores | `Queries.Designer.cs` |
| `min_memory` | numeric | Minimum memory | `Queries.Designer.cs` |
| `max_db_memory` | numeric | Max DB memory | `Queries.Designer.cs` |
| `primary_group_max_workers` | int | Worker limit | `Queries.Designer.cs` |
| `max_sessions` | int | Session limit | `Queries.Designer.cs` |
| `max_memory_grant` | numeric | Max memory grant | `Queries.Designer.cs` |

## 55. MonDmExecCachedPlansSummary — Cached-plan summary DMV snapshot

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 56. MonDmIoVirtualFileStats — Per-file IO and size DMV snapshot

### Definition
DMV snapshot used for database/log file size and IO latency analysis.

### Code Source
- **Repositories**: `SQLLivesiteAgents`, `BusinessAnalytics`
- **Key Files**:
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonDmIoVirtualFileStats.kql`
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Availability queries compute DB size, log usage, and IO stall statistics from the table.
  - Cosmos deployment registers the table for collection.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `PreciseTimeStamp` | datetime | Snapshot time | `MonDmIoVirtualFileStats.kql` |
| `NodeName` | string | Node identity | `MonDmIoVirtualFileStats.kql` |
| `LogicalServerName` | string | Logical server | `MonDmIoVirtualFileStats.kql` |
| `db_name` | string | Database name | `MonDmIoVirtualFileStats.kql` |
| `file_id` | int | File id | `MonDmIoVirtualFileStats.kql` |
| `type_desc` | string | File type (`ROWS`/`LOG`) | `MonDmIoVirtualFileStats.kql` |
| `size_on_disk_bytes` | long | File size on disk | `MonDmIoVirtualFileStats.kql` |
| `spaceused_mb` | numeric | Space used | `MonDmIoVirtualFileStats.kql` |
| `max_size_mb` | numeric | Max file size | `MonDmIoVirtualFileStats.kql` |
| `is_primary_replica` | int/bool | Primary replica flag | `MonDmIoVirtualFileStats.kql` |

## 57. MonDmOsBPoolPerfCounters — Buffer-pool performance counters

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 58. MonDmOsExceptionStats — OS exception statistics DMV snapshot

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

## 59. MonDmOsMemoryClerks — Memory clerk DMV snapshot

### Definition
DMV snapshot exposed through a public `MonDmOsMemoryClerks.view` and CosmosFetcher helper script.

### Code Source
- **Repositories**: `DsMainDev`
- **Key Files**:
  - `DsMainDev:/Tools/DevScripts/CosmosFetcher/scripts/MonDmOsMemoryClerks.script`
- **Evidence**:
  - Script points directly to `/Views/Public/MonDmOsMemoryClerks.view` and filters by `AppName`.

### Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `AppName` | string | SQL app / instance name | `MonDmOsMemoryClerks.script` |

## 60. Confidence note for entries 15–59

### Definition
These appended entries mix **high-confidence** source-backed sections (for example `MonDatabaseEncryptionKeys`, `MonDatabaseMetadata`, `MonDeploymentAutomation`, `MonDmContinuousCopyStatus`, `MonDmDbHadrReplicaStates`, `MonDmIoVirtualFileStats`, `MonBlockedProcessReportFiltered`) with **medium/low-confidence** sections where only workflow registration, dashboards, or KQL usage were found.

# MI Kusto Tables — Code-Level Reference (Batch 2)

This file covers requested tables **61-105**. I used `msdata-search_code` first and only promoted tables to code-backed summaries when a searched file gave a defensible definition or column evidence. If results were weak, I marked the table as **Referenced in KQL templates only**.

---

## 61. MonDmOsSpinlockStats — Spinlock contention DMV telemetry

### Definition
No durable source-code definition was found in the searched repos. The table appears to be consumed downstream rather than defined in the results returned by code search.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: likely DMV snapshot of `sys.dm_os_spinlock_stats`

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 62. MonDmOsWaitstats — Wait statistics DMV telemetry

### Definition
Search results only showed consumer code, not a producer/schema definition. The table is clearly used for performance analysis, but the searched files did not define its schema.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: likely DMV snapshot of wait statistics

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 63. MonDmTempDbFileSpaceUsage — tempdb file-space DMV telemetry

### Definition
No useful producer/schema file was found. Returned search hits were unrelated consumers or generic MDS config files.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: likely tempdb DMV snapshot

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 64. MonDmTranActiveTransactions — Active transaction DMV telemetry

### Definition
The search mostly returned TSG/media references rather than a table producer or schema definition.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: likely transaction DMV snapshot

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 65. MonDmUserActivityDetection — User activity detection telemetry

### Definition
Search hits were not table-definition files. I could not identify a trustworthy schema producer from the returned results.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred user-activity detection pipeline

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 66. MonDwBilling — DW billing telemetry

### Definition
The search did not surface a useful producer/schema file for this exact table. Returned hits were unrelated or indirect references.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred DW billing / resource accounting pipeline

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 67. MonFabricApi — Service Fabric API HA events

### Definition
`MonFabricApi` is a Kusto table for Service Fabric / HADR fabric API events. The searched repo documents it as an event-backed table with event-specific subpages and enum mappings.

### Code Source
- **Repository**: `SQL-DB-ON-Call-Common`, `DsMainDev-bbexp`
- **Key Files**:
  - `SQL-DB-ON-Call-Common:/content/Tools/Kusto/High-Availability-Related-Kusto-Tables/MonFabricApi.md`
  - `DsMainDev-bbexp:/Tools/DevScripts/CosmosFetcher/scripts/MonFabricApi.script`
- **Data Origin**: XEvent / Fabric API telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `fault_type_desc` | string | Decoded Fabric fault type (`Permanent`, `Transient`, etc.) | `MonFabricApi.md` |
| `fault_reason_desc` | string | Decoded replica fault reason enum | `MonFabricApi.md` |
| `AppName` | string | App / replica instance filter used by CosmosFetcher script | `MonFabricApi.script` |

## 68. MonFabricClusters — Fabric cluster inventory/health telemetry

### Definition
Search results did not expose a clear producer or schema file for this exact table.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Service Fabric cluster metadata

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 69. MonFabricDebug — Fabric debug traces

### Definition
The search returned docs and query files, but not a strong source-code producer definition. I did not find enough code evidence to safely derive schema.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonFabricDebug.kql`
- **Data Origin**: inferred Fabric debug/XEvent traces

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 70. MonFabricThrottle — Fabric throttling telemetry

### Definition
Returned results were KQL/query references rather than a table producer or schema definition.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonFabricThrottle.kql`
- **Data Origin**: inferred Fabric throttling diagnostics

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 71. MonFedAuthTicketService — Federated auth ticket service telemetry

### Definition
The search mostly found GDPR manifests and unrelated config. No trustworthy producer/schema file was found.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred FedAuth service telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 72. MonFulltextActiveCatalogs — Full-text crawl/catalog status telemetry

### Definition
`MonFulltextActiveCatalogs` is a full-text status table used to detect stuck auto-crawl conditions. The runner filters it for enabled catalogs with pending changes, completed crawl history, and no documents processed.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/FullTextRunner/FullTextPendingChangesRunner.cs`
- **Data Origin**: Full-text engine/catalog status telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `is_enabled` | bool/int | Whether the full-text catalog/index is enabled | `FullTextPendingChangesRunner.cs` |
| `change_tracking_state_desc` | string | Change-tracking mode; runner expects `AUTO` | `FullTextPendingChangesRunner.cs` |
| `has_crawl_completed` | bool/int | Indicates a prior crawl completed | `FullTextPendingChangesRunner.cs` |
| `crawl_end_date` | datetime | Last crawl completion time | `FullTextPendingChangesRunner.cs` |
| `pending_changes` | long | Outstanding changes waiting to be crawled | `FullTextPendingChangesRunner.cs` |
| `docs_processed` | long | Documents processed by crawl; runner flags `0` | `FullTextPendingChangesRunner.cs` |
| `database_id` | long | Database identifier for the affected DB | `FullTextPendingChangesRunner.cs` |
| `catalog_id` | long | Full-text catalog identifier | `FullTextPendingChangesRunner.cs` |
| `object_id` | long | Object/index identifier with pending crawl work | `FullTextPendingChangesRunner.cs` |

## 73. MonFullTextInfo — Full-text information/event telemetry

### Definition
Search results were weak and did not expose a producer/schema file for this exact table.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred full-text engine telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 74. MonGovernorResourcePools — Resource Governor pool telemetry

### Definition
Only consumer code references were returned. No schema/producer definition was found in the searched files.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Resource Governor DMV/XEvent telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 75. MonGovernorWorkloadGroups — Resource Governor workload-group telemetry

### Definition
Search hits pointed to downstream analysis code, not to a reliable producer/schema definition.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Resource Governor workload-group telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 76. MonHyperVEvents — Hyper-V host/worker ETW events

### Definition
`MonHyperVEvents` is an ETW-backed table defined in the OTel MDS agent template. Multiple Hyper-V providers publish into the same Kusto event name.

### Code Source
- **Repository**: `DsMainDev-bbexp`
- **Key Files**:
  - `DsMainDev-bbexp:/Sql/xdb/manifest/svc/OTelMonitoringAgent/AzDbOTelMdsConfig_template.xml`
- **Data Origin**: ETW (`Microsoft.Windows.HyperV.Compute`, `Microsoft-Windows-Hyper-V-Compute`, `Microsoft.Windows.HyperV.Worker`, `Microsoft-Windows-Hyper-V-Worker`, `Microsoft-Windows-Hyper-V-Virtual-PMEM`)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ClusterName` | string | Ring / cluster identity injected by the MDS agent | `AzDbOTelMdsConfig_template.xml` |
| `NodeRole` | string | Role name captured from environment | `AzDbOTelMdsConfig_template.xml` |
| `MachineName` | string | Machine identity of the ETW emitter | `AzDbOTelMdsConfig_template.xml` |
| `NodeName` | string | Node identity of the ETW emitter | `AzDbOTelMdsConfig_template.xml` |
| `RelatedActivityId` | guid/string | ETW activity correlation field | `AzDbOTelMdsConfig_template.xml` |
| `KeywordMask` | string/int | ETW keyword mask included in header | `AzDbOTelMdsConfig_template.xml` |

## 77. MonImportExport — Import/Export request lifecycle telemetry

### Definition
`MonImportExport` stores tenant-ring Import/Export operation timing and request correlation. The long-running request processor joins it with `MonManagementOperations` to detect requests that started but never finished.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ImportExport/ImportExportLongRunningRequestProcessor.cs`
- **Data Origin**: Import/Export service telemetry (tenant ring), correlated with management/control-ring telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `request_id` | guid/string | Stable request identifier for the I/E job | `ImportExportLongRunningRequestProcessor.cs` |
| `operation_type` | string | Operation kind (`ImportToExistingDatabase`, `ImportToNewDatabase`, `ExportDatabase`) | `ImportExportLongRunningRequestProcessor.cs` |
| `server_name` | string | Target logical server from operation parameters | `ImportExportLongRunningRequestProcessor.cs` |
| `database_name` | string | Target database from operation parameters | `ImportExportLongRunningRequestProcessor.cs` |
| `tr_min_time` | datetime | Earliest tenant-ring event for the request | `ImportExportLongRunningRequestProcessor.cs` |
| `tr_max_time` | datetime | Latest tenant-ring event for the request | `ImportExportLongRunningRequestProcessor.cs` |
| `tr_running_time` | timespan | Tenant-ring runtime computed from `tr_min_time` | `ImportExportLongRunningRequestProcessor.cs` |
| `tr_app_name` | string | Tenant-ring AppName handling the request | `ImportExportLongRunningRequestProcessor.cs` |

## 78. MonLinkedServerInfo — Linked-server inventory/usage telemetry

### Definition
No trustworthy producer/schema file was found in the returned search results.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred linked-server telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 79. MonLogReaderTraces — Replication log-reader phase/session telemetry

### Definition
`MonLogReaderTraces` is populated from replication XEvents emitted by `ReplXEventDependencies`. It captures per-session/per-phase log reader telemetry, LSN boundaries, wait stats, and command counters.

### Code Source
- **Repository**: `DsMainDev-bbexp`
- **Key Files**:
  - `DsMainDev-bbexp:/Sql/Ntdbms/srvrepl/src/ReplXEventDependencies.cpp`
- **Data Origin**: Replication XEvents (`repl_logscan_session`, `repl_cmd_counter`, `repldone_session`)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `database_id` | int | Database being scanned by the log reader | `ReplXEventDependencies.cpp` |
| `session_id` | int | Log-reader session identifier | `ReplXEventDependencies.cpp` |
| `phase_number` | int | Replication scan phase number | `ReplXEventDependencies.cpp` |
| `tran_count` | int | Transactions seen in the session/phase | `ReplXEventDependencies.cpp` |
| `log_record_count` | int | Number of log records scanned | `ReplXEventDependencies.cpp` |
| `start_lsn` | string | Start LSN for a scan interval | `ReplXEventDependencies.cpp` |
| `end_lsn` | string | End LSN for a scan interval | `ReplXEventDependencies.cpp` |
| `last_commit_lsn` | string | Last commit LSN seen by the session | `ReplXEventDependencies.cpp` |
| `wait_stats` | xml/string | Worker wait stats captured at phase end | `ReplXEventDependencies.cpp` |
| `command_count` | int | Command count for the session | `ReplXEventDependencies.cpp` |

## 80. MonLtrConfiguration — Long-term retention configuration/state

### Definition
`MonLtrConfiguration` is the LTR state/configuration snapshot used by backup/LTR runners. The code shows it carries per-database LTR retention settings, backup timestamps, geo-DR role, lifecycle state, and server/database identity.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LTR/VldbLTRSnapshotOutOfSLA.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LTR/LTRSubscriptionMismatchAlert.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LTR/LTRSterlingBackupSLA.cs`
- **Data Origin**: LTR FSM / backup configuration pipeline

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `logical_server_id` | string | Stable logical-server identifier | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSubscriptionMismatchAlert.cs` |
| `logical_database_id` | string | Stable logical-database identifier | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |
| `logical_server_name` | string | Server name for reporting/joining | `VldbLTRSnapshotOutOfSLA.cs` |
| `logical_database_name` | string | Database name for reporting/joining | `VldbLTRSnapshotOutOfSLA.cs` |
| `weekly_retention` | string | Weekly LTR retention policy | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |
| `monthly_retention` | string | Monthly LTR retention policy | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |
| `yearly_retention` | string | Yearly LTR retention policy | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |
| `week_of_year` | int/string | Scheduling parameter for yearly retention | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |
| `is_vldb` | bool/int | Marks VLDB / Hyperscale page-server scenarios | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |
| `last_backup_time` | datetime | Most recent LTR backup time | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |
| `next_backup_time` | datetime | Next scheduled LTR backup time | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |
| `state` | string | LTR row state (`Ready`, `ReadyToPurge`, etc.) | `VldbLTRSnapshotOutOfSLA.cs`, `LTRSterlingBackupSLA.cs` |

## 81. MonMachineLocalWatchdog — Machine-local certificate/watchdog findings

### Definition
`MonMachineLocalWatchdog` contains machine-local watchdog records. The certificates expiry runner parses it for certificate metadata embedded in `message_resourcename` and uses it to detect expiring or non-rotated certs.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CertificatesExpiryDetection/CertificatesExpiryDetectionRunner.cs`
- **Data Origin**: Machine-local watchdog / certificate watcher telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `component` | string | Component name; runner filters `CertificateWatchdog` | `CertificatesExpiryDetectionRunner.cs` |
| `message_resourcename` | string | Encoded watchdog payload parsed for cert details | `CertificatesExpiryDetectionRunner.cs` |
| `Thumbprint` | string | Certificate thumbprint extracted from payload | `CertificatesExpiryDetectionRunner.cs` |
| `ExpiryDate` | datetime/string | Certificate expiration date | `CertificatesExpiryDetectionRunner.cs` |
| `LogicalName` | string | Registry logical name for the certificate | `CertificatesExpiryDetectionRunner.cs` |
| `IsManaged` | string/bool | Whether the cert is managed/rotated | `CertificatesExpiryDetectionRunner.cs` |
| `dSMSPath` | string | DSMS certificate path | `CertificatesExpiryDetectionRunner.cs` |
| `Subject` | string | Certificate subject | `CertificatesExpiryDetectionRunner.cs` |
| `LastUpdate` | datetime | Most recent watchdog observation | `CertificatesExpiryDetectionRunner.cs` |
| `NodeCount` | long | Number of nodes reporting the same certificate | `CertificatesExpiryDetectionRunner.cs` |

## 82. MonManagedInstanceCategorizedDatabaseOutages — Categorized MI DB outages

### Definition
`MonManagedInstanceCategorizedDatabaseOutages` is the categorized output table for MI database outages. Detection writes raw outages first; the categorization runner reads them, assigns outage reasons, and outputs the categorized records.

### Code Source
- **Repository**: `SqlTelemetry`, `DsMainDev-bbexp`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterAvailability/AvailabilityOutageCategorizationV2/AvailabilityOutagesCategorizationV2Runner.cs`
  - `DsMainDev-bbexp:/Sql/xdb/externals/mds/OutagesDetection.compliance.xml`
- **Data Origin**: MDS runner output from availability outage categorization

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `OutageStartTime` | datetime | Start of the database outage | `OutagesDetection.compliance.xml`, `AvailabilityOutagesCategorizationV2Runner.cs` |
| `OutageEndTime` | datetime | End of the outage | `OutagesDetection.compliance.xml`, `AvailabilityOutagesCategorizationV2Runner.cs` |
| `Type` | string | Outage type/classification (`SF`, torn-affinity variants, etc.) | `OutagesDetection.compliance.xml`, `AvailabilityOutagesCategorizationV2Runner.cs` |
| `OutageReason` | string | Classified outage reason | `OutagesDetection.compliance.xml`, `AvailabilityOutagesCategorizationV2Runner.cs` |
| `DatabasePartitionId` | string | Partition/database identifier used for uniqueness and joins | `OutagesDetection.compliance.xml`, `AvailabilityOutagesCategorizationV2Runner.cs` |
| `AppName` | string | Fabric application/app instance for the DB | `OutagesDetection.compliance.xml` |
| `SubscriptionId` | string | Customer subscription identifier | `OutagesDetection.compliance.xml` |
| `ServiceLevelObjective` | string | MI DB SLO at time of outage | `OutagesDetection.compliance.xml` |
| `OutageHash` | string | Dedup/identity key for the outage | `OutagesDetection.compliance.xml`, `AvailabilityOutagesCategorizationV2Runner.cs` |
| `LogicalServerName` | string | Managed Instance name | `OutagesDetection.compliance.xml`, `AvailabilityOutagesCategorizationV2Runner.cs` |
| `LogicalDatabaseName` | string | Managed database name | `OutagesDetection.compliance.xml`, `AvailabilityOutagesCategorizationV2Runner.cs` |
| `Details` | string | Extended RCA details | `OutagesDetection.compliance.xml` |

## 83. MonManagedInstanceDatabaseOutages — Raw MI DB outage detections

### Definition
`MonManagedInstanceDatabaseOutages` is the raw outage-detection table populated by `AvailabilityOutagesDetectionV2Runner`. It stores incomplete and complete outage windows before categorization.

### Code Source
- **Repository**: `SqlTelemetry`, `DsMainDev-bbexp`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterAvailability/AvailabilityOutageCategorizationV2/AvailabilityOutagesDetectionV2Runner.cs`
  - `DsMainDev-bbexp:/Sql/xdb/externals/mds/OutagesDetection.compliance.xml`
- **Data Origin**: MDS runner output from availability outage detection

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `OutageStartTime` | datetime | Outage start timestamp | `AvailabilityOutagesDetectionV2Runner.cs`, `OutagesDetection.compliance.xml` |
| `OutageEndTime` | datetime | Outage end timestamp; null for incomplete outages | `AvailabilityOutagesDetectionV2Runner.cs`, `OutagesDetection.compliance.xml` |
| `Phase0` | string/bool | Detection-specific outage phase marker | `OutagesDetection.compliance.xml` |
| `NewPrimary` | string | New primary replica/node after failover | `OutagesDetection.compliance.xml` |
| `OldPrimary` | string | Previous primary replica/node | `OutagesDetection.compliance.xml` |
| `DatabasePartitionId` | string | Database partition identifier | `AvailabilityOutagesDetectionV2Runner.cs`, `OutagesDetection.compliance.xml` |
| `Type` | string | Outage type | `AvailabilityOutagesDetectionV2Runner.cs`, `OutagesDetection.compliance.xml` |
| `PLBActivity` | string | Related placement/load balancer activity | `OutagesDetection.compliance.xml` |
| `Constraint` | string | Constraint context recorded for outage | `OutagesDetection.compliance.xml` |
| `OutageHash` | string | Dedup/identity key | `AvailabilityOutagesDetectionV2Runner.cs`, `OutagesDetection.compliance.xml` |
| `LogicalServerName` | string | MI server name | `OutagesDetection.compliance.xml` |
| `LogicalDatabaseName` | string | MI database name | `OutagesDetection.compliance.xml` |

## 84. MonManagedInstanceInfo — Managed Instance inventory/status snapshot

### Definition
Returned results showed consumers and operational references, but not a clean producer/schema file for this exact table. The table appears to be an MI inventory snapshot used by multiple runners.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/Telemetry/Kusto/Load/KustoTablesLoadReporter.cs`
- **Data Origin**: inferred MI inventory snapshot

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 85. MonManagedInstanceSSBConversations — MI Service Broker conversation telemetry

### Definition
The search surfaced only TSG documentation referencing the table as a useful source for cross-instance Service Broker investigations; no schema producer was found.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `TSG-SQL-MI-Availability:/content/Index/SqlMI-SSB/TSGCLSSB0004-Cross-Instance-Service-Broker-General-TSG.md`
- **Data Origin**: inferred Service Broker telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 86. MonManagedServer — Likely typo for `MonManagedServers`

### Definition
Searching the singular name did not return a solid source definition; existing code and prior references strongly suggest the real table is `MonManagedServers`. Per request, I am not inventing a schema for the typo form.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: likely typo of MI server inventory table

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | Likely typo; use `MonManagedServers` instead. | — |

## 87. MonManagedServerCategorizedOutages — Categorized MI server outages

### Definition
No useful source-definition file was returned for this exact table name. The closest code evidence was for related outage tables, not this one.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred MI server outage categorization pipeline

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 88. MonManagedServerInstances — Managed Instance fabric app/tenant-ring mapping

### Definition
`MonManagedServerInstances` is used as an MI instance inventory/mapping table that ties managed-server identity to tenant ring and fabric application URI. The strongest evidence comes from MI endpoint monitoring code that groups failures by managed server.

### Code Source
- **Repository**: `SqlTelemetry`, `TSG-SQL-MI-Networking`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/ConnectivityNetworking/NetworkMonitoringMiEndpointsRunner.cs`
  - `TSG-SQL-MI-Networking:/content/connectivity/Deprecated/tsgminw1014-network-monitoring-mi-endpoints.md`
- **Data Origin**: inferred MI management inventory snapshot

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `tenant_ring_name` | string | Tenant ring that hosts the MI | `tsgminw1014-network-monitoring-mi-endpoints.md` |
| `managed_server_id` | string | Stable managed-server identifier | `tsgminw1014-network-monitoring-mi-endpoints.md` |
| `name` | string | Instance/app name used to join from `MonNetworkMonitoring.app_name` | `tsgminw1014-network-monitoring-mi-endpoints.md` |
| `fabric_application_uri` | string | Fabric application URI for the MI | `tsgminw1014-network-monitoring-mi-endpoints.md`, `NetworkMonitoringMiEndpointsRunner.cs` |

## 89. MonManagementArchivedBackup — Archived backup / LTR archival telemetry

### Definition
`MonManagementArchivedBackup` stores backup-archive/LTR archival events and failures. The alert code groups errors and, in a separate runner, looks for failed VLDB LTR backup events in the same table.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/MonManagementArchivedBackupErrorAlert.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LTR/VLDBFailedLTRAlert.cs`
- **Data Origin**: backup management / LTR archival service telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Event time used for alert windows | `MonManagementArchivedBackupErrorAlert.cs` |
| `ClusterName` | string | Cluster where archive/LTR event occurred | `MonManagementArchivedBackupErrorAlert.cs` |
| `error_message` | string | Archive/LTR failure text | `MonManagementArchivedBackupErrorAlert.cs` |
| `event` | string | Event name; alert code filters failures, VLDB code filters `ltr_vldb_backup_failure` | `MonManagementArchivedBackupErrorAlert.cs`, `VLDBFailedLTRAlert.cs` |
| `operation_type` | string | Archive/LTR operation kind | `MonManagementArchivedBackupErrorAlert.cs`, `VLDBFailedLTRAlert.cs` |
| `stack_trace` | string | Stack trace for grouped archive failures | `MonManagementArchivedBackupErrorAlert.cs` |
| `request_id` | string | Request identifier for failed VLDB LTR operations | `VLDBFailedLTRAlert.cs` |
| `logical_server_id` | string | Server identifier for the failed backup | `VLDBFailedLTRAlert.cs` |
| `logical_database_id` | string | Database identifier for the failed backup | `VLDBFailedLTRAlert.cs` |
| `failure_type` | string | Failure category for LTR backup failure events | `VLDBFailedLTRAlert.cs` |

## 90. MonManagementExceptions — Management exception telemetry

### Definition
Search results only showed consumers and operational references, not a producer/schema definition for the table.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred management exception/event stream

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 91. MonManagementOperations — Control-plane management operation telemetry

### Definition
`MonManagementOperations` is the control-ring operations table for management requests. The import/export processor filters it for start/success/failure/cancel events and parses `operation_parameters` to extract server/database names.

### Code Source
- **Repository**: `SqlTelemetry`, `SQLLivesiteAgents`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/ImportExport/ImportExportLongRunningRequestProcessor.cs`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonManagementOperations.kql`
- **Data Origin**: Management service / control-plane operation events

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Operation lifecycle event (`management_operation_start`, `...success`, `...failure`, etc.) | `ImportExportLongRunningRequestProcessor.cs` |
| `operation_type` | string | Requested management action | `ImportExportLongRunningRequestProcessor.cs` |
| `operation_parameters` | xml/string | XML payload parsed for server/database names | `ImportExportLongRunningRequestProcessor.cs` |
| `request_id` | string | Request identifier for the operation | `ImportExportLongRunningRequestProcessor.cs` |
| `transaction_id` | string | Transaction identifier correlated with FSM | `ImportExportLongRunningRequestProcessor.cs` |
| `originalEventTimestamp` | datetime | Original event time used for duration calculations | `ImportExportLongRunningRequestProcessor.cs` |
| `server_name` | string | Parsed target server name | `ImportExportLongRunningRequestProcessor.cs` |
| `database_name` | string | Parsed target database name | `ImportExportLongRunningRequestProcessor.cs` |

## 92. MonManagementResourceProvider — ARM/resource-provider request telemetry

### Definition
`MonManagementResourceProvider` has an explicit static schema in BusinessAnalytics. It captures RP/ARM-style request metadata, routing, resource identity, request/response details, and exception fields.

### Code Source
- **Repository**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/CosmosConfiguration/StaticSchemas/MonManagementResourceProvider.schema`
- **Data Origin**: Management Resource Provider / ARM-style request telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `action` | string | Requested RP action | `MonManagementResourceProvider.schema` |
| `action_name` | string | Friendly action name | `MonManagementResourceProvider.schema` |
| `api_version` | string | ARM/RP API version | `MonManagementResourceProvider.schema` |
| `operation_type` | string | Operation category/type | `MonManagementResourceProvider.schema` |
| `request_id` | string | Request identifier | `MonManagementResourceProvider.schema` |
| `correlation_id` | string | Correlation id across hops | `MonManagementResourceProvider.schema` |
| `logical_server_name` | string | Target logical server | `MonManagementResourceProvider.schema` |
| `logical_database_name` | string | Target logical database | `MonManagementResourceProvider.schema` |
| `resource_group` | string | Azure resource group | `MonManagementResourceProvider.schema` |
| `resource_type` | string | Target resource type | `MonManagementResourceProvider.schema` |
| `response_code` | int | HTTP/operation response code | `MonManagementResourceProvider.schema` |
| `exception_message` | string | Captured exception text | `MonManagementResourceProvider.schema` |

## 93. MonMIGeoDRFailoverGroupsConnectivity — MI GeoDR FOG connectivity status

### Definition
`MonMIGeoDRFailoverGroupsConnectivity` is an MI GeoDR connectivity table used by `MIDataMovementRunner`. The runner fans out to the North Europe Kusto cluster, filters for `HasConnectivity == false`, and summarizes broken connectivity by managed server.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterAvailability/MIDataMovementRunner.cs`
- **Data Origin**: MI GeoDR failover-group connectivity checks

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ManagedServerName` | string | MI name checked for GeoDR connectivity | `MIDataMovementRunner.cs` |
| `HasConnectivity` | bool | Whether connectivity succeeded | `MIDataMovementRunner.cs` |
| `TIMESTAMP` | datetime | Time window for connectivity evaluation | `MIDataMovementRunner.cs` |
| `NoConnEventCount` | long | Count of no-connectivity observations per server (summarized) | `MIDataMovementRunner.cs` |

## 94. MonNetworkMonitoring — Network probe / endpoint test telemetry

### Definition
`MonNetworkMonitoring` is emitted by the NetworkMonitoring MDS agent template and consumed by networking runners. It carries probe events such as `gateway_test` and `mi_endpoints`, later grouped by cluster/app/server/IP to create incidents.

### Code Source
- **Repository**: `SqlTelemetry`, `DsMainDev-bbexp`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/ConnectivityNetworking/NetworkMonitoringGatewayRunner.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/ConnectivityNetworking/NetworkMonitoringMiEndpointsRunner.cs`
  - `DsMainDev-bbexp:/Sql/xdb/manifest/svc/NetworkMonitoring/MDS/NetworkMonitoringMDSAgentConfig_template.xml`
- **Data Origin**: Network Monitoring application logs captured by MDS agent

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Probe/event name such as `gateway_test` or `mi_endpoints` | `NetworkMonitoringGatewayRunner.cs`, `NetworkMonitoringMiEndpointsRunner.cs` |
| `log_level` | string | Probe result severity; runners count `Error` | TSG query referenced by `NetworkMonitoringMiEndpointsRunner.cs` |
| `app_name` | string | App/fabric instance being probed | `NetworkMonitoringMiEndpointsRunner.cs` |
| `ip_address` | string | Endpoint IP that failed probes | `NetworkMonitoringMiEndpointsRunner.cs` |
| `ClusterName` | string | Cluster/ring identity | `NetworkMonitoringGatewayRunner.cs`, `NetworkMonitoringMDSAgentConfig_template.xml` |
| `NodeName` | string | Node identity from MDS identity block | `NetworkMonitoringMDSAgentConfig_template.xml` |
| `LogicalServerName` | string | Logical server identity injected by the MDS agent | `NetworkMonitoringMDSAgentConfig_template.xml` |
| `SubscriptionId` | string | Subscription identity injected by the MDS agent | `NetworkMonitoringMDSAgentConfig_template.xml` |

## 95. MonNodeAgentEvents — Node agent operational events

### Definition
Search results did not surface a trustworthy table producer or schema file. Consumers reference the table for troubleshooting only.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `AzureSQLTools:/Console/Modules/ClusterManagementModule/BackupSqlDw.cs`
- **Data Origin**: inferred node-agent operational event stream

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 96. MonNodeTraceETW — Generic node ETW trace sink

### Definition
`MonNodeTraceETW` appears in the OTel MDS template as a generic ETW event sink for node traces. In the current template it is commented out as part of a staged rollout, but the event name and identity mapping are explicit.

### Code Source
- **Repository**: `DsMainDev-bbexp`, `SQLLivesiteAgents`
- **Key Files**:
  - `DsMainDev-bbexp:/Sql/xdb/manifest/svc/OTelMonitoringAgent/AzDbOTelMdsConfig_template.xml`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonNodeTraceETW.kql`
- **Data Origin**: ETW node traces via MDS/OTel agent

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ClusterName` | string | Cluster identity from agent identity block | `AzDbOTelMdsConfig_template.xml` |
| `NodeRole` | string | Node role | `AzDbOTelMdsConfig_template.xml` |
| `MachineName` | string | Host machine name | `AzDbOTelMdsConfig_template.xml` |
| `NodeName` | string | Node instance name | `AzDbOTelMdsConfig_template.xml` |

## 97. MonNonPiiAudit — Non-PII audit telemetry

### Definition
Only KQL/query references were returned, not a producer/schema definition.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonNonPiiAudit.kql`
- **Data Origin**: inferred audit stream with PII-scrubbed payloads

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 98. MonPrivateClusterCapacityManagement — Private cluster capacity telemetry

### Definition
Search results were indirect and did not expose a producer/schema file for the table.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred private-cluster capacity pipeline

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 99. MonPrivateClusters — Private cluster inventory telemetry

### Definition
Search results were mostly metadata/validation references, not a reliable source definition.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred private-cluster inventory

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 100. MonQPTelemetry — Query-processing telemetry

### Definition
The requested search term did not return a trustworthy source-definition file for this exact table.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred query-processing telemetry stream

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 101. MonQueryProcessing — Query-processing/XEvent plan telemetry

### Definition
`MonQueryProcessing` is a broad query-processing telemetry table. The DW optimizer code explicitly says logical plan details are posted via the `uqo_logical_query_plan` XEvent and persisted into `MonQueryProcessing`.

### Code Source
- **Repository**: `DsMainDev-bbexp`, `SQL-DB-ON-Call-Common`
- **Key Files**:
  - `DsMainDev-bbexp:/Sql/Ntdbms/query_dw/qeoptim_dw/dbi_dw/log/log_op_logger.h`
  - `SQL-DB-ON-Call-Common:/content/Tools/Kusto/Performance-related-Kusto-Tables/MonQueryProcessing.md`
- **Data Origin**: query optimizer / query-processing XEvents

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TableMetadata` | string/json | Embedded metadata such as DB/object/dist info for referenced tables | `log_op_logger.h` |
| `idPos` | int | Operator position in the logged logical plan | `log_op_logger.h` |
| `idParent` | int | Parent operator position | `log_op_logger.h` |
| `GroupNumber` | int | Optimizer group number for the operator | `log_op_logger.h` |
| `RowCount` | int | Estimated/observed row-count value logged with the operator | `log_op_logger.h` |
| `RowSize` | int | Row-size value logged with the operator | `log_op_logger.h` |
| `OpName` | string | Logical operator name | `log_op_logger.h` |
| `PhysicalOpName` | string | Derived physical operator name | `log_op_logger.h` |
| `OperatorType` | string | Operator type/class | `log_op_logger.h` |
| `OperatorInfo` | string/json | Operator-specific JSON payload | `log_op_logger.h` |

## 102. MonQueryStoreFailures — Query Store severe-failure/shutdown telemetry

### Definition
`MonQueryStoreFailures` records Query Store failure events. The severe-error shutdown detector uses it as the main table and filters `event == 'query_store_severe_error_shutdown'`.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/QueryStore/SevereErrorShutdownIssue.cs`
- **Data Origin**: Query Store failure / severe shutdown telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `originalEventTimestamp` | datetime | Start time of the severe shutdown event | `SevereErrorShutdownIssue.cs` |
| `event` | string | Failure event name; runner expects `query_store_severe_error_shutdown` | `SevereErrorShutdownIssue.cs` |
| `AppName` | string | App / engine instance for the affected DB | `SevereErrorShutdownIssue.cs` |
| `LogicalServerName` | string | Server containing the affected database | `SevereErrorShutdownIssue.cs` |
| `logical_database_name` | string | Affected database name | `SevereErrorShutdownIssue.cs` |
| `ClusterName` | string | Cluster/ring where the issue occurred | `SevereErrorShutdownIssue.cs` |

## 103. MonQueryStoreInfo — Query Store diagnostics/info telemetry

### Definition
`MonQueryStoreInfo` stores Query Store diagnostics, including DB-level memory usage and shutdown completion events. Different Query Store runners read specific event types from it.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/QueryStore/HighDatabaseMemoryUsageIssue.cs`
  - `SqlTelemetry:/Src/MdsRunners/MdsRunners/Runners/QueryStore/SevereErrorShutdownIssue.cs`
- **Data Origin**: Query Store diagnostics/events

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Diagnostics event name (`query_store_db_diagnostics`, `query_store_shutdown_in_error_state_finished`) | `HighDatabaseMemoryUsageIssue.cs`, `SevereErrorShutdownIssue.cs` |
| `ExtraFields` | dynamic/json | Payload with Query Store memory counters | `HighDatabaseMemoryUsageIssue.cs` |
| `logical_database_name` | string | Database name being diagnosed | `HighDatabaseMemoryUsageIssue.cs`, `SevereErrorShutdownIssue.cs` |
| `LogicalServerName` | string | Server containing the database | `HighDatabaseMemoryUsageIssue.cs`, `SevereErrorShutdownIssue.cs` |
| `database_id` | int | Database identifier | `HighDatabaseMemoryUsageIssue.cs` |
| `current_buffered_items_size_kb` | long | Current buffered-items memory (parsed from `ExtraFields`) | `HighDatabaseMemoryUsageIssue.cs` |
| `max_memory_available_kb` | long | Available memory cap for QDS calculations | `HighDatabaseMemoryUsageIssue.cs` |
| `current_stmt_hash_map_size_kb` | long | Current QDS hash-map memory | `HighDatabaseMemoryUsageIssue.cs` |
| `originalEventTimestamp` | datetime | Event time for shutdown completion correlation | `SevereErrorShutdownIssue.cs` |

## 104. MonRecoveryTrace — Database recovery progress/completion traces

### Definition
`MonRecoveryTrace` is exposed through a public `.view` and used by KQL to inspect recovery start/progress/completion messages. The query file shows it carries recovery event names, trace messages, DB identity, node/process, and elapsed recovery timings.

### Code Source
- **Repository**: `DsMainDev-bbexp`, `SQLLivesiteAgents`
- **Key Files**:
  - `DsMainDev-bbexp:/Tools/DevScripts/CosmosFetcher/scripts/MonRecoveryTrace.script`
  - `SQLLivesiteAgents:/temp/Availability/kusto-queries/MonRecoveryTrace.kql`
- **Data Origin**: recovery trace/XEvent style telemetry surfaced through `MonRecoveryTrace.view`

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `database_name` | string | Database name or physical DB GUID appearing in recovery messages | `MonRecoveryTrace.kql` |
| `database_id` | int | Database id from recovery trace | `MonRecoveryTrace.kql` |
| `event` | string | Recovery event name (`database_recovery_trace`, `database_recovery_complete`) | `MonRecoveryTrace.kql` |
| `trace_message` | string | Recovery progress/completion text | `MonRecoveryTrace.kql` |
| `originalEventTimestamp` | datetime | Original event time | `MonRecoveryTrace.kql` |
| `NodeName` | string | Node emitting the recovery trace | `MonRecoveryTrace.kql` |
| `process_id` | string/int | Process associated with the recovery event | `MonRecoveryTrace.kql` |
| `total_elapsed_time_sec` | int | Total recovery time in seconds for completion events | `MonRecoveryTrace.kql` |

## 105. MonRedirector — Redirector / URI-cache redirection telemetry

### Definition
`MonRedirector` is emitted from WinFab URI-cache/redirection code. The code explicitly publishes telemetry when force-refresh or URI-cache delete operations succeed/fail and when login redirection behavior is adjusted.

### Code Source
- **Repository**: `DsMainDev-bbexp`
- **Key Files**:
  - `DsMainDev-bbexp:/Sql/Ntdbms/xdb/winfab/postsosboot/xdburicache.cpp`
- **Data Origin**: redirector / WinFab URI-cache telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `service_name` | string | Service URI/name being redirected or refreshed | `xdburicache.cpp` |
| `resolve_count` | int | Count of resolve attempts before force refresh | `xdburicache.cpp` |
| `resolve_result` | int/hresult | Result of the resolve/refresh operation | `xdburicache.cpp` |
| `cache_type` | string/int | Cache kind, e.g. URI cache | `xdburicache.cpp` |
| `cache_instance` | string/int | Cache instance identifier | `xdburicache.cpp` |
| `entry` | string/int | Entry affected by delete/refresh telemetry | `xdburicache.cpp` |
| `entries` | int | Entry count after delete/refresh operation | `xdburicache.cpp` |
| `error_code` | int | Result/error code for cache delete path | `xdburicache.cpp` |
| `message` | string | Free-form reason/context (e.g. `Triggered by CAS`) | `xdburicache.cpp` |

# MI Kusto Tables — Code-Level Reference (Batch 3)

This file covers requested tables **106-143**. I used `msdata-search_code` on each table name and only elevated entries to code-backed summaries when the returned files gave a defensible definition or clear field evidence. Otherwise, the table is marked **Referenced in KQL templates only**.

---

## 106. MonResourcePoolStats — Resource pool performance telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonResourcePoolStats`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred resource pool stats

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 107. MonRestoreEvents — Restore event timeline telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonRestoreEvents`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred restore workflow events

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 108. MonRestoreRequests — Restore request lifecycle telemetry

### Definition
A Scope script reads the public `MonRestoreRequests.view`, filters it by region, tenant ring, and date range, then materializes the output as a structured stream. The script explicitly clusters and sorts the result by `restore_request_id` and `timestamp`, making it a downstream export surface for restore-request telemetry.

### Code Source
- **Repository**: `DsMainDev-bbexp`
- **Key Files**:
  - `/Sql/Ntdbms/Hekaton/tools/Azure/HkCosmosTelemetry/Scope/MonRestoreRequests.script`
- **Data Origin**: Cosmos public view / restore workflow telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `restore_request_id` | string | Primary restore-request identifier used as the clustering key for exported streams. | `MonRestoreRequests.script` |
| `timestamp` | datetime | Primary event time used for stream sorting. | `MonRestoreRequests.script` |
| `ClusterName` | string | Ring/cluster filter used to scope exported restore data. | `MonRestoreRequests.script` |

## 109. MonRgLoad — Resource governor load telemetry

### Definition
`MonRgLoad` is used by a SqlTelemetry runner to compute CPU and memory utilization for Renzo control-plane instances. The runner filters `instance_load` rows and projects RG process ID, node, cluster, and load/cap counters before correlating them with `MonSqlRenzoCp`.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `/Src/MdsRunners/MdsRunners/Runners/SqlRenzoRunners/ResourceUtilizationRunners/SqlRenzoCpApplicationResourceUtilizationRunner.cs`
- **Data Origin**: MDS Runner / resource-governor load telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Row type; the runner filters `instance_load` RG load samples. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `code_package_name` | string | Code package identity; runner scopes to `RenzoCP.Code`. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `application_name` | string | Fabric application name; runner scopes to `fabric:/RenzoCP`. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `rg_instance_process_id` | long | RG instance process ID used to join back to Renzo service processes. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `cpu_load` | real | Observed CPU load for the instance. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `cpu_load_cap` | real | CPU cap used to compute `cpu_ratio`. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `memory_load` | real | Observed memory load for the instance. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `memory_load_cap` | real | Memory cap used to compute `memory_ratio`. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `NodeName` | string | Service Fabric node used in the join to Renzo process metadata. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `ClusterName` | string | Cluster identity used with node/process joins. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |

## 110. MonRgManager — Resource governor manager metrics

### Definition
A static BusinessAnalytics schema defines `MonRgManager` as a resource-governor manager event/metric table. The schema exposes metric name/value pairs plus cap-change, timer, reclaim, and package metadata fields.

### Code Source
- **Repository**: `BusinessAnalytics`
- **Key Files**:
  - `/Src/CosmosConfiguration/StaticSchemas/MonRgManager.schema`
- **Data Origin**: Cosmos static schema / resource-governor manager telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `metric_name` | string | Name of the RG manager metric being emitted. | `MonRgManager.schema` |
| `metric_value` | int32/int64 | Numeric value for the metric. | `MonRgManager.schema` |
| `_event` | string | Raw event name emitted by the component. | `MonRgManager.schema` |
| `resource` | string | Governed resource the event refers to. | `MonRgManager.schema` |
| `old_cap` | int32 | Previous cap before a cap-change event. | `MonRgManager.schema` |
| `new_cap` | int32 | New cap after a cap-change event. | `MonRgManager.schema` |
| `instance_name` | string | RG manager instance name. | `MonRgManager.schema` |
| `application_name` | string | Owning application name. | `MonRgManager.schema` |
| `code_package_name` | string | Code package reporting the metric/event. | `MonRgManager.schema` |
| `timestamp` | datetime | Event timestamp. | `MonRgManager.schema` |

## 111. MonRolloutProgress — Rollout orchestration progress telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonRolloutProgress`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred rollout orchestration telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 112. MonSocrates — Socrates platform telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSocrates`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Socrates service telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 113. MonSqlAgent — SQL Agent operational telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlAgent`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred SQL Agent telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 114. MonSqlBrokerRingBuffer — SQL Broker ring buffer events

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlBrokerRingBuffer`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred ring buffer / broker telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 115. MonSqlCaches — SQL cache telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlCaches`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred cache / plan-store telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 116. MonSqlDump — SQL dump and crash telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlDump`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred dump pipeline telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 117. MonSqlDumperActivity — SQL dumper invocation telemetry

### Definition
A checked-in Kusto schema script defines `MonSqlDumperActivity` as one row per SQL dumper invocation across Azure SQL Database clusters. The docstring explicitly positions it for dump creation, Watson submission, crash-signature, and suppressed-dump analysis.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `/SQLKusto/ServiceGroupRoot/KqlFiles/Services/SqlTelemetry/Watson/MonSqlDumperActivity.kql`
- **Data Origin**: Kusto schema / SqlDumper + Watson telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Event timestamp in UTC. | `MonSqlDumperActivity.kql` |
| `DumpUID` | string | Unique identifier for the dump instance. | `MonSqlDumperActivity.kql` |
| `TargetPid` | long | Process ID of the target process being dumped. | `MonSqlDumperActivity.kql` |
| `DumpFlags` | long | Bitwise SQLDUMPER_FLAGS value describing dump behavior. | `MonSqlDumperActivity.kql` |
| `ErrorCode` | long | Dump creation error code; `0` means success. | `MonSqlDumperActivity.kql` |
| `IsFailed` | bool | Whether dump creation failed. | `MonSqlDumperActivity.kql` |
| `StackSignature` | string | Crash stack-signature hash. | `MonSqlDumperActivity.kql` |
| `FileSize` | long | Dump file size in bytes. | `MonSqlDumperActivity.kql` |
| `SubmitResult` | string/long | Watson submission result code. | `MonSqlDumperActivity.kql` |
| `TargetAppName` | string | Application/instance that was dumped. | `MonSqlDumperActivity.kql` |

## 118. MonSqlFrontend — SQL frontend service telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlFrontend`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred frontend service telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 119. MonSqlMemNodeOomRingBuffer — Memory-node OOM ring buffer telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlMemNodeOomRingBuffer`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred memory OOM ring-buffer telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 120. MonSqlMemoryClerkStats — Memory clerk statistics telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlMemoryClerkStats`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred memory clerk / DMV telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 121. MonSqlRenzoCp — Renzo control-plane service telemetry

### Definition
SqlTelemetry runners use `MonSqlRenzoCp` as the authoritative RenzoCP service/probe table, joining on process, node, and cluster to map RG load back to concrete service instances. The referenced runner specifically looks for `event == 'metadatastore_probe_status'` rows.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `/Src/MdsRunners/MdsRunners/Runners/SqlRenzoRunners/ResourceUtilizationRunners/SqlRenzoCpApplicationResourceUtilizationRunner.cs`
- **Data Origin**: MDS Runner / Renzo control-plane telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Time filter used when correlating probe rows. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `event` | string | Renzo event name; runner filters `metadatastore_probe_status`. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `ClusterName` | string | Cluster identity used for join correlation. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `NodeName` | string | Node identity used for join correlation. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `service_instance_name` | string | Resolved Renzo service instance name. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |
| `process_id` | long | Process ID joined against RG instance process ID. | `SqlRenzoCpApplicationResourceUtilizationRunner.cs` |

## 122. MonSqlRenzoTraceEvent — Renzo trace-event telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlRenzoTraceEvent`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Renzo trace-event telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 123. MonSqlRgHistory — Resource governor history telemetry

### Definition
A static BusinessAnalytics schema defines `MonSqlRgHistory` as a history/snapshot table with database, file, IO-delta, and replica/storage metadata. It looks like periodic RG/file-history capture rather than free-form trace events.

### Code Source
- **Repository**: `BusinessAnalytics`
- **Key Files**:
  - `/Src/CosmosConfiguration/StaticSchemas/MonSqlRgHistory.schema`
- **Data Origin**: Cosmos static schema / RG history telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `active_session_count_max` | int32 | Maximum active session count seen for the sample. | `MonSqlRgHistory.schema` |
| `database_id` | int32 | Database identifier. | `MonSqlRgHistory.schema` |
| `db_name` | string | Database name. | `MonSqlRgHistory.schema` |
| `delta_num_of_reads` | int64 | Read-count delta for the sample window. | `MonSqlRgHistory.schema` |
| `delta_num_of_bytes_read` | int64 | Bytes-read delta for the sample window. | `MonSqlRgHistory.schema` |
| `delta_num_of_writes` | int64 | Write-count delta for the sample window. | `MonSqlRgHistory.schema` |
| `delta_num_of_bytes_written` | int64 | Bytes-written delta for the sample window. | `MonSqlRgHistory.schema` |
| `file_path` | string | Underlying file path. | `MonSqlRgHistory.schema` |
| `is_primary_replica` | boolean | Whether the sample came from the primary replica. | `MonSqlRgHistory.schema` |
| `size_on_disk_bytes` | int64 | On-disk file size. | `MonSqlRgHistory.schema` |

## 124. MonSqlRmRingBuffer — SQL resource-monitor ring buffer telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlRmRingBuffer`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred resource-monitor ring-buffer telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 125. MonSqlSampledBufferPoolDescriptors — Sampled buffer-pool descriptor telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSqlSampledBufferPoolDescriptors`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred buffer-pool sampling telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 126. MonSqlSecurityService — SQL Security Service telemetry

### Definition
A SqlTelemetry runner uses `MonSqlSecurityService` to detect certificate-cache refresh failures and related exceptions. The queries show the table carries per-request security-service events, certificate names, client descriptors, request IDs, and exception text.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `/Src/MdsRunners/MdsRunners/Runners/Provisioning/Components/SecretsAndAutoRotation/SSSCacheCertificateRefreshFailureRunner.cs`
- **Data Origin**: SQL Security Service event telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Security-service event name; runner filters refresh failure/exception events. | `SSSCacheCertificateRefreshFailureRunner.cs` |
| `message` | string | Message text; primary query filters `Rejected`. | `SSSCacheCertificateRefreshFailureRunner.cs` |
| `ClusterName` | string | Cluster where the failure occurred. | `SSSCacheCertificateRefreshFailureRunner.cs` |
| `AppName` | string | Application instance encountering the failure. | `SSSCacheCertificateRefreshFailureRunner.cs` |
| `certificate_name` | string | Certificate alias/name being refreshed. | `SSSCacheCertificateRefreshFailureRunner.cs` |
| `client_description` | string | Client identity attempting the refresh. | `SSSCacheCertificateRefreshFailureRunner.cs` |
| `request_id` | string | Request correlation identifier used to join exception and failure rows. | `SSSCacheCertificateRefreshFailureRunner.cs` |
| `exception_message` | string | Detailed exception text for refresh failures. | `SSSCacheCertificateRefreshFailureRunner.cs` |
| `TIMESTAMP` | datetime | Time filter used in the failure/exception queries. | `SSSCacheCertificateRefreshFailureRunner.cs` |

## 127. MonSqlShrinkInfo — SQL shrink-operation telemetry

### Definition
A managed-backup repair runner treats `MonSqlShrinkInfo` as the shrink lifecycle table for detecting stuck DBCC shrink operations. The code looks for `shrink_started on spid ...`, `shrink_move_page_started`, and `shrink_move_page_completed` status transitions keyed by `shrink_id`.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LogNearFull/ShrinkBotSubmitRepairAction.cs`
- **Data Origin**: DBCC shrink / log-near-full telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `logical_server_name` | string | Logical server hosting the database. | `ShrinkBotSubmitRepairAction.cs` |
| `logical_database_name` | string | Logical database being shrunk. | `ShrinkBotSubmitRepairAction.cs` |
| `AppName` | string | Application instance associated with the shrink operation. | `ShrinkBotSubmitRepairAction.cs` |
| `status` | string | Shrink lifecycle state such as started or move-page events. | `ShrinkBotSubmitRepairAction.cs` |
| `shrink_id` | string | Identifier for a specific shrink operation. | `ShrinkBotSubmitRepairAction.cs` |
| `spid` | int | Session ID extracted from the shrink-start status string. | `ShrinkBotSubmitRepairAction.cs` |
| `originalEventTimestamp` | datetime | Timestamp used to determine stall duration. | `ShrinkBotSubmitRepairAction.cs` |
| `NodeName` | string | Node running the shrink session. | `ShrinkBotSubmitRepairAction.cs` |
| `AppTypeName` | string | Application type, used to limit repairs to Hyperscale compute. | `ShrinkBotSubmitRepairAction.cs` |
| `ClusterName` | string | Cluster/ring used for follow-up validation and repair. | `ShrinkBotSubmitRepairAction.cs` |

## 128. MonSqlTransactions — SQL transaction telemetry

### Definition
A CosmosFetcher script reads the public `MonSqlTransactions.view` over a caller-supplied date range and exposes it for app-scoped pulls. The script is consumer-oriented rather than a producer definition, but it confirms the table is a shared production view for transaction telemetry.

### Code Source
- **Repository**: `DsMainDev-bbexp`
- **Key Files**:
  - `/Tools/DevScripts/CosmosFetcher/scripts/MonSqlTransactions.script`
- **Data Origin**: Cosmos public view / SQL transaction telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `AppName` | string | Application filter applied by the fetcher script. | `MonSqlTransactions.script` |

## 129. MonSQLXStore — SQL XStore telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSQLXStore`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred XStore storage telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 130. MonSQLXStoreIOStats — SQL XStore I/O statistics telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSQLXStoreIOStats`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred XStore I/O telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 131. MonSsbManagedInstanceTransmissions — Service Broker transmission telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSsbManagedInstanceTransmissions`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Service Broker telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 132. MonSystemEventLogErrors — System event-log error telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonSystemEventLogErrors`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Windows system event-log telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 133. MonTranReplTraces — Transactional replication trace telemetry

### Definition
A SqlTelemetry runner uses `MonTranReplTraces` as the source of replication-dispatcher errors. It filters dispatcher trouble/error events, ignores expected broken-pipe noise, and summarizes first-seen times by cluster and app before creating health properties/incidents.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/Replication/ReplDispatcherErrorAlert.cs`
- **Data Origin**: transactional replication trace telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Trace event name; runner looks for dispatcher troubleshoot/error events. | `ReplDispatcherErrorAlert.cs` |
| `message_type` | string | Severity/category; runner filters `ERROR` troubleshoot rows. | `ReplDispatcherErrorAlert.cs` |
| `exception_message` | string | Error text used to suppress expected broken-pipe noise. | `ReplDispatcherErrorAlert.cs` |
| `originalEventTimestamp` | datetime | First-seen event timestamp summarized by the alert. | `ReplDispatcherErrorAlert.cs` |
| `ClusterName` | string | Cluster where the dispatcher error occurred. | `ReplDispatcherErrorAlert.cs` |
| `AppName` | string | Application instance running the dispatcher. | `ReplDispatcherErrorAlert.cs` |

## 134. MonUcsConnections — UCS connection telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonUcsConnections`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred UCS connection telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 135. MonUpsertTenantRingRequests — Tenant-ring upsert request telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonUpsertTenantRingRequests`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred control-plane request telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 136. MonWiDmDbPartitionStats — Workload Insights DB partition statistics

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonWiDmDbPartitionStats`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Workload Insights partition telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 137. MonWiQdsWaitStats — Query Store wait statistics telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonWiQdsWaitStats`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Query Store wait telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 138. MonWiQueryParamData — Query-parameter telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonWiQueryParamData`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred Workload Insights query-parameter telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 139. MonWorkerWaitStats — Worker wait-statistics telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonWorkerWaitStats`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred worker wait telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 140. MonXdbhost — XDB host service telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonXdbhost`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred xdb host telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 141. MonXdbLaunchSetup — XDB launch/setup telemetry

### Definition
A checked-in availability query uses `MonXdbLaunchSetup` to inspect `XdbLaunchSqlSetupEntryPointLog` records around an incident time window. That makes the table a startup/setup log stream for xdb SQL launch processing.

### Code Source
- **Repository**: `SQLLivesiteAgents`
- **Key Files**:
  - `/temp/Availability/kusto-queries/MonXdbLaunchSetup.kql`
- **Data Origin**: xdb launch/setup logging

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `TIMESTAMP` | datetime | Primary time filter for setup-log queries. | `MonXdbLaunchSetup.kql` |
| `AppName` | string | Application name used to scope setup logs. | `MonXdbLaunchSetup.kql` |
| `message_systemmetadata` | string | System metadata text; query filters the setup entry-point marker. | `MonXdbLaunchSetup.kql` |
| `originalEventTimestamp` | datetime | Original event time projected for investigation. | `MonXdbLaunchSetup.kql` |
| `NodeName` | string | Node that emitted the setup log. | `MonXdbLaunchSetup.kql` |

## 142. MonDwBilling — DW billing telemetry

### Definition
No durable source-code definition was found in the searched repos. Search hits were consumers, docs, dashboards, or query templates rather than a producer/schema file for `MonDwBilling`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: —
- **Data Origin**: inferred billing / cost-accounting telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| — | — | No code-derived columns identified in searched repos. | — |

## 143. MonLabRunResults — Lab-run result rollup telemetry

### Definition
`LabRunReporter` explicitly populates `MonLabRunResults` by appending the latest `MonLabRunSnapshot` row for each `(SessionId, JobId)` pair and left-anti joining against existing results. In other words, `MonLabRunResults` is a deduplicated rollup table derived from lab-run snapshots fetched from CloudTest APIs.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**:
  - `/Src/MdsRunners/MdsRunners/Runners/ContinuousValidation/LabRunReporter/LabRunReporter.cs`
- **Data Origin**: CloudTest REST -> MonLabRunSnapshot -> Kusto append pipeline

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `SessionId` | string | Lab session identifier; part of the deduplication key. | `LabRunReporter.cs` |
| `JobId` | string | Lab job identifier; part of the deduplication key. | `LabRunReporter.cs` |
| `SessionEndTime` | datetime | Cutoff time used when appending recent runs. | `LabRunReporter.cs` |
| `TenantId` | string | Tenant filter applied during ingestion. | `LabRunReporter.cs` |

---

## Replication TSG addendum

The following code references were re-verified for the Transactional Replication TSG pipeline using `msdata-search_code` and `msdata-repo_get_file_content` in the `Database Systems` project.

### MonTranReplTraces — dispatcher and replication error surface
- **Repository**: `SqlTelemetry`
- **Key file**: `/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/Replication/ReplDispatcherErrorAlert.cs`
- **Code evidence**:
  - `GetKustoDataForLastMinutes("MonTranReplTraces", rangeMinutes, query)` is the direct consumer.
  - Filters `event in ("repl_dispatcher_troubleshoot", "repl_dispatcher_error")` and `message_type == "ERROR"`.
  - Suppresses expected broken-pipe noise via `exception_message` filtering.
  - Summarizes by `ClusterName` and `AppName`, then joins `MonAnalyticsDBSnapshot` to recover `logical_server_name`.
- **Key columns confirmed**: `event`, `message_type`, `exception_message`, `originalEventTimestamp`, `ClusterName`, `AppName`, `logical_server_name`.

### MonCDCTraces + MonLogReaderTraces — CDC scheduler and log-reader correlation
- **Repository**: `SqlTelemetry`
- **Key file**: `/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/Replication/CdcSchedulerNotRunningDeprecated.cs`
- **Code evidence**:
  - Builds the primary candidate set from `MonCDCTraces` and anti-joins recent activity from both `MonCDCTraces` and `MonLogReaderTraces`.
  - `MonCDCTraces` activity predicates include `event == 'cdc_session'`, `event == 'cdc_error'`, `event_type == 'CaptureJobFailed'`, and `event_details contains 'Skipping database because replbeginlsn and repllsn are null lsn.'`.
  - `MonLogReaderTraces` is used as the companion signal with `event == 'repldone_session'` or `event == 'repl_logscan_session'`.
  - Join keys are `LogicalServerName` and `logical_database_guid`, with supporting fields `logical_database_name`, `physical_database_guid`, `NodeName`, `AppName`, and `ClusterName`.
- **Key columns confirmed**: `LogicalServerName`, `logical_database_guid`, `logical_database_name`, `physical_database_guid`, `event`, `event_type`, `event_details`, `error_number`, `status`, `component`.

### MonCTTraces — syscommittab cleanup alert pipeline
- **Repository**: `SqlTelemetry`
- **Key file**: `/Src/MdsRunners/MdsRunners/Runners/CloudLifterRunners/SyscommittabCleanupAlertRunner.cs`
- **Code evidence**:
  - Runner comment explicitly states it detects `syscommittab_cleanup_alert` in `MonCTTraces`.
  - Query filters `event == 'syscommittab_cleanup_alert'` and `column_ifexists('rows_in_delay', 0) > 250000000`.
  - Packs `logical_database_name`, `database_id`, `physical_database_guid`, `logical_database_guid`, and `rows_in_delay` into the incident payload.
  - Summarizes by `ClusterName`, `AppTypeName`, `AppName`, and `LogicalServerName`.
- **Key columns confirmed**: `event`, `rows_in_delay`, `logical_database_name`, `database_id`, `physical_database_guid`, `logical_database_guid`, `AppTypeName`, `AppName`, `LogicalServerName`.

### MonManagedDatabaseInfo — producer-side schema definition
- **Repository**: `SqlTelemetry`
- **Key file**: `/SQLKusto/ServiceGroupRoot/KqlFiles/Developer/jahiegel/sqlazure1_schema_update`
- **Code evidence**:
  - Kusto DDL contains `.alter-merge table MonManagedDatabaseInfo (...)`.
  - The checked-in schema includes `code_package_version`, `end_utc_date`, `start_utc_date`, `sql_database_id`, `managed_database_id`, `owner_sid`, `compatibility_level`, and `collation_name`.
  - This matches the replication TSG usage where `collation_name` is inspected to diagnose case-sensitive collation issues.
- **Key columns confirmed**: `LogicalServerName`, `code_package_version`, `sql_database_id`, `managed_database_id`, `compatibility_level`, `collation_name`.

### AlrWinFabHealthDeployedAppEvent — SQL Agent crash-loop alert surface
- **Repository**: `SqlTelemetry`
- **Key file**: `/SQLKusto/ServiceGroupRoot/KqlFiles/Developer/jahiegel/sqlazure1_schema_update`
- **Code evidence**:
  - Kusto DDL contains `.alter-merge table AlrWinFabHealthDeployedAppEvent (...)`.
  - The checked-in schema includes `ApplicationName`, `HealthState`, `SourceId`, `Property`, `Description`, `IsExpired`, `Version`, and `NodeEntityName`.
  - This matches the replication TSG query pattern that searches `Description` for `sqlagent.exe` exits and groups by `ApplicationName`.
- **Key columns confirmed**: `ApplicationName`, `HealthState`, `SourceId`, `Property`, `Description`, `IsExpired`, `Version`, `NodeEntityName`, `LogicalServerName`, `ClusterName`.

