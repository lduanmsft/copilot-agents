# SQL DB Kusto Tables — Code-Level Reference

Scope: top DB-specific SQL DB tables from `sqldb\db-tables-list.txt`, excluding tables already documented in `mi-tables-code-reference.md` where possible. When repo search did not surface a usable schema/definition, the entry is marked as referenced in KQL templates only.

## 1. MonBillingElasticServerStatus — Elastic server billing/status snapshot

### Definition
Used by OSS custom-backup automation to find elastic servers with `resource_tags`, `subscription_id`, and `current_state` metadata. The code treats it as a billing/status table for elastic servers and joins it with `MonAnalyticsElasticServersSnapshot`.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/OSSManagedBackup/OSSDBCustomBackups.cs`
- **Data Origin**: Billing/elastic server status view consumed by MDS runner

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `subscription_id` | string | Customer subscription filter for backup automation | `OSSDBCustomBackups.cs` |
| `resource_tags` | dynamic/string | JSON tags; includes custom backup settings | `OSSDBCustomBackups.cs` |
| `current_state` | string | Server readiness state | `OSSDBCustomBackups.cs` |
| `server_id` | guid/string | Elastic server identifier used for joins | `OSSDBCustomBackups.cs` |
| `originalEventTimestamp` | datetime | Latest billing snapshot time | `OSSDBCustomBackups.cs` |

## 2. MonBillingPooledVldbStatus — Hyperscale pooled-VLDB billing state

### Definition
Consumed by `LRUpdateSloRunner` to identify Hyperscale pooled databases that are good candidates for SLO changes. The query uses the table as the authoritative pooled-VLDB billing/status snapshot.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/Socrates/LRUpdateSloRunner.cs`
- **Data Origin**: Billing status view for pooled Hyperscale VLDBs

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `edition` | string | Filtered to `Hyperscale` | `LRUpdateSloRunner.cs` |
| `current_state` | string | DB state; only `Ready` rows are used | `LRUpdateSloRunner.cs` |
| `TIMESTAMP` | datetime | Snapshot time for `arg_max` selection | `LRUpdateSloRunner.cs` |
| `billing_server_name` | string | Projected as `LogicalServerName` | `LRUpdateSloRunner.cs` |
| `database_id` | guid/string | Projected as `logical_db_id` for joins | `LRUpdateSloRunner.cs` |
| `database_name` | string | Logical DB name | `LRUpdateSloRunner.cs` |
| `page_server_count` | long | Max page-server count per DB | `LRUpdateSloRunner.cs` |
| `service_level_objective_id` | guid/string | Target SLO identifier | `LRUpdateSloRunner.cs` |
| `service_level_objective` | string | Current SLO name | `LRUpdateSloRunner.cs` |

## 3. MonBillingResourcePoolStatus — Elastic pool/resource-pool billability snapshot

### Definition
Backed by the logical resource pool state machine and explicitly called out in comments as a billability-sensitive view. It maps pool FSM states into user-visible resource-pool status and billing state.

### Code Source
- **Repository**: `BI_AS_Engine_Office_CC`
- **Key Files**: `/Sql/xdb/manifest/svc/mgmt/fsm/LogicalResourcePoolStateMachine.cs`
- **Data Origin**: CMS logical resource pool FSM surfaced through DmvCollector `viewcollection.xml`

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `logical_resource_pool_id` | guid/string | Logical pool identity (inferred from FSM/table) | `LogicalResourcePoolStateMachine.cs` |
| `current_state` | string/int | Current FSM/resource-pool state | `LogicalResourcePoolStateMachine.cs` |
| `user_visible_status` | string | User-facing pool state (`Creating`, `Ready`, `Disabled`, etc.) | `LogicalResourcePoolStateMachine.cs` |
| `is_billable` | bool | Whether the pool should be billed in that state | `LogicalResourcePoolStateMachine.cs` |
| `version` | int | FSM/view schema version coupling | `LogicalResourcePoolStateMachine.cs` |

## 4. MonLoginDispatcherPool — Login dispatcher queue/latency telemetry

### Definition
Availability Manager uses this table to detect dispatcher stalls. The table tracks per-dispatcher processing duration on a per-node basis and is queried over 5-minute windows.

### Code Source
- **Repository**: `SqlTelemetry`, `DsMainDev-bbexp`
- **Key Files**: `/Src/MdsRunners/MdsRunners/AvailabilityManager/AvailabilityManager.cs`; `/Sql/xdb/manifest/svc/sql/MDS/MonitoringSqlMDSAgentConfig_template.xml`
- **Data Origin**: MDS `DirectoryWatchItem` for `\Public\MonLoginDispatcherPool`

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `AppName` | string | Dispatcher process/app instance | `AvailabilityManager.cs` |
| `NodeName` | string | Node running the dispatcher | `AvailabilityManager.cs` |
| `ClusterName` | string | Tenant ring / cluster | `AvailabilityManager.cs` |
| `dispatcher_id` | string/int | Dispatcher instance identifier | `AvailabilityManager.cs` |
| `processing_duration_ms` | long | Stall duration; alert logic uses `> 45000` | `AvailabilityManager.cs` |
| `originalEventTimestamp` | datetime | 5-minute-binned event time | `AvailabilityManager.cs` |

## 5. MonRgServerless — Serverless billing/activity stream

### Definition
Used by serverless active-runner validation to determine whether a DB was active and whether billed duration matches management operations. The code treats `serverless_application_usage` rows as minute-granularity activity/billing evidence.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/Performance/ServerlessActiveRunners/ServerlessActiveRunnerBase.cs`; `/Src/MdsRunners/MdsRunners/Runners/Performance/ServerlessActiveRunners/ServerlessActiveRunnerConstants.cs`
- **Data Origin**: RG/serverless telemetry emitted by serverless runtime

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `instance_logical_server_name` | string | Logical server filter | `ServerlessActiveRunnerConstants.cs` |
| `instance_target_name` | string | Logical database filter | `ServerlessActiveRunnerConstants.cs` |
| `originalEventTimestamp` | datetime | Activity timestamp used for active-state detection | `ServerlessActiveRunnerConstants.cs` |
| `event` | string | `serverless_application_usage` event type | `ServerlessActiveRunnerConstants.cs` |
| `app_cpu_billed_normalized` | numeric | Non-zero indicates billable activity | `ServerlessActiveRunnerConstants.cs` |
| `billingDuration` | long | Derived minute count from summarized rows | `ServerlessActiveRunnerConstants.cs` |

## 6. MonSocratesForeignFileValidation — Hyperscale FFV/SBCD event stream

### Definition
The Snapshot-Based Corruption Detection monitor uses this as the core FFV telemetry table. It contains page-audit failures, post-read errors, page-ID mismatches, and related foreign-file validation fields.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/Socrates/SocratesSnapshotBasedCorruptionDetectionMonitor.cs`
- **Data Origin**: Socrates XEvents / FFV (`ffvalid.cpp`, `sqlserver.xevents.socrates_ffv.xml`)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | FFV event name such as `ffv_page_audit_failed` | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |
| `logical_database_name` | string | DB name associated with failure | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |
| `logical_database_guid` | guid/string | Stable DB identifier | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |
| `file_id` | int/string | Foreign/snapshot file id | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |
| `page_id` | int/string | Affected page id | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |
| `physical_db_id` | guid/string | Physical database id | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |
| `failure_kind` | string | Failure classification | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |
| `snapshot_name` | string | Snapshot name for post-read errors | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |
| `post_read_error` | string | Post-read error text/code | `SocratesSnapshotBasedCorruptionDetectionMonitor.cs` |

## 7. MonSocratesQp — Hyperscale query-pushdown runtime telemetry

### Definition
Runtime telemetry for Socrates/Hyperscale query pushdown. The TSG documents it as the canonical Kusto table for pushdown aggregated stats, percentile stats, retries, and page-server execution cost.

### Code Source
- **Repository**: `TSG-SQL-DB-Performance`; `DsMainDev-bbexp`
- **Key Files**: `/content/Socrates-QP-Pushdown/SQP001-Socrates-QP-Pushdown-Overview.md`; `/Sql/xdb/manifest/svc/sql/MDS/MonitoringSqlMDSAgentConfig_template.xml`
- **Data Origin**: Socrates QP runtime telemetry from compute + page servers

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `event` | string | Pushdown event kind (`hyperscale_pushdown_aggregated_stats`, etc.) | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `session_id` | int | Query session id | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `query_hash` | long/hex | Logical query identity | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `query_plan_hash` | long/hex | Plan identity | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `node_id` | int | Plan node id | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `physical_operator` | string | Operator type | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `sent_requests` | long | Number of pushdown requests sent | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `pushed_rows_read` | long | Rows read on page servers | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `pushed_rows_returned` | long | Rows returned after pushdown filtering | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `duration_ms` | long | Total page-server execution time | `SQP001-Socrates-QP-Pushdown-Overview.md` |
| `cpu_time_ms` | long | Total page-server CPU time | `SQP001-Socrates-QP-Pushdown-Overview.md` |

## 8. MonBackupBilling — Hyperscale/VLDB backup billing workflow telemetry

### Definition
This table is the operational event stream behind VLDB backup billing alerts. The runner uses it to detect long-running billing requests, repeated billing errors, and page servers that are not producing expected billing calculations.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/VLDBBackupBilling.cs`
- **Data Origin**: Backup billing runtime events from backup/billing pipeline

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `request_id` | guid/string | Billing request identity | `VLDBBackupBilling.cs` |
| `error_type` | string | Billing error classification | `VLDBBackupBilling.cs` |
| `exception_details_format` | string | Error details used for filtering benign failures | `VLDBBackupBilling.cs` |
| `details_format` | string | Free-form details; distinguishes old/new API patterns | `VLDBBackupBilling.cs` |
| `file_path` | string | Backup file path normalized for grouping | `VLDBBackupBilling.cs` |
| `logical_database_id` | guid/string | Target database | `VLDBBackupBilling.cs` |
| `billing_metric_name` | string | Billing calculation kind | `VLDBBackupBilling.cs` |
| `AppName` | string | Page-server application | `VLDBBackupBilling.cs` |
| `ClusterName` | string | Ring/cluster source | `VLDBBackupBilling.cs` |

## 9. MonBillingBandwidthSummary2 — Billing bandwidth summary rollup

### Definition
Repo search mostly surfaced dashboards and agent templates rather than a concrete source definition. Treat as a billing summary table referenced by operational dashboards/KQL.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: Dashboard references only; no authoritative schema recovered in repo search
- **Data Origin**: Billing summary rollup (exact collector not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | No reliable code-side schema surfaced in search | — |

## 10. MonBillingDatabaseStatus2 — Per-database billing status view

### Definition
A Scope script explicitly reads `MonBillingDatabaseStatus2` from `Views/Public`, filters by region/ring, and persists rows clustered by `database_name` and `originalEventTimestamp`. This is a general database billing status snapshot.

### Code Source
- **Repository**: `DsMainDev-bbexp` / `DsMainDev`
- **Key Files**: `/Sql/Ntdbms/Hekaton/tools/Azure/HkCosmosTelemetry/Scope/MonBillingDatabaseStatus2.script`
- **Data Origin**: Public view consumed from Cosmos/Scope

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `database_name` | string | Clustering/sort key in script output | `MonBillingDatabaseStatus2.script` |
| `originalEventTimestamp` | datetime | Primary time dimension | `MonBillingDatabaseStatus2.script` |
| `ClusterName` | string | Used for control-ring filtering | `MonBillingDatabaseStatus2.script` |
| `billing_server_name` | string | Implied server dimension in billing views | `MonBillingDatabaseStatus2.script` |
| `current_state` | string | Standard status filter in companion billing views | `MonBillingDatabaseStatus2.script` |

## 11. MonBillingLtrBackup — Long-term retention backup billing view

### Definition
Search hits only found secondary alerting logic that excludes `MonBillingLtrBackup` from “finished processing view” delay checks. No direct view schema was recovered.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `BillingDmvCollectorLastSuccessfulExecutionAlertMds.cs` mentions it as a DmvCollector view id
- **Data Origin**: LTR billing/DmvCollector view (schema not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | No usable schema in first-pass search | — |

## 12. MonBillingPitrBackupSize — PITR backup-size billing view

### Definition
Search hits pointed to DmvCollector infrastructure rather than the concrete view definition. This appears to be a standard billing DmvCollector view for PITR backup size.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `MdsWriter.cs` / DmvCollector infrastructure references only
- **Data Origin**: DmvCollector billing view (schema not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | No reliable schema surfaced | — |

## 13. MonBillingServerStatus2 — Logical-server billing status view

### Definition
Repo search pointed to logical-database/server state-machine code, but not a direct table definition. This is likely the standard server-level counterpart of `MonBillingDatabaseStatus2`.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: State-machine references only; no direct schema recovered in first pass
- **Data Origin**: Billing/server-status view (schema not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | No direct definition recovered | — |

## 14. MonBillingVLDBBackupStatus — Hyperscale VLDB backup billing source table

### Definition
The billing pipeline doc names this as the source table for Hyperscale VLDB backup billing. Data is collected by DmvCollector against CMS every 10 minutes and then normalized into billing Scope templates.

### Code Source
- **Repository**: `TSG-SQL-DB-DataIntegration`
- **Key Files**: `/BackupRestore/VLDBBackupBilling-Billing-Pipeline.md`
- **Data Origin**: DmvCollector reading CMS `vldb` data every 10 minutes

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `logical_database_id` | guid/string | Database identity for billed resource | `VLDBBackupBilling-Billing-Pipeline.md` |
| `logical_server_name` | string | Server identity for resource URI generation | `VLDBBackupBilling-Billing-Pipeline.md` |
| `backup_billing_enabled` | bool/string | Used by normalized billing filters | `VLDBBackupBilling-Billing-Pipeline.md` |
| `state` | string | Validity/billability filter | `VLDBBackupBilling-Billing-Pipeline.md` |
| `usage_type` | string | Meter mapping key in billing templates | `VLDBBackupBilling-Billing-Pipeline.md` |
| `InfoFieldMeteredServiceType` | string | Commerce meter/service mapping | `VLDBBackupBilling-Billing-Pipeline.md` |
| `Quantity` | numeric | Hourly billed quantity emitted to commerce | `VLDBBackupBilling-Billing-Pipeline.md` |

## 15. MonBillingVldbStatus2 — Hyperscale single-VLDB billing status snapshot

### Definition
`LRUpdateSloRunner` uses this table for non-pooled Hyperscale databases and projects the same core SLO/page-server fields as the pooled variant. It acts as a per-VLDB billing/status snapshot.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/Socrates/LRUpdateSloRunner.cs`
- **Data Origin**: Billing status view for Hyperscale VLDBs

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `edition` | string | Filtered to `Hyperscale` | `LRUpdateSloRunner.cs` |
| `current_state` | string | Only `Ready` rows are used | `LRUpdateSloRunner.cs` |
| `TIMESTAMP` | datetime | Latest snapshot selection | `LRUpdateSloRunner.cs` |
| `billing_server_name` | string | Projected as `LogicalServerName` | `LRUpdateSloRunner.cs` |
| `database_id` | guid/string | Logical DB id for joins | `LRUpdateSloRunner.cs` |
| `database_name` | string | User DB name | `LRUpdateSloRunner.cs` |
| `page_server_count` | long | Hyperscale page-server fanout | `LRUpdateSloRunner.cs` |
| `service_level_objective_id` | guid/string | SLO id | `LRUpdateSloRunner.cs` |

## 16. MonCapacityDBSnapshot — DB capacity/replica configuration snapshot

### Definition
DmvCollector unit tests explicitly validate this view and require replica-management columns. The table is a database-level capacity snapshot used for placement/replica analysis.

### Code Source
- **Repository**: `SQL2017`
- **Key Files**: `/Sql/xdb/tests/suites/DmvCollector/DmvCollectorQueryUnitTests.cs`
- **Data Origin**: DmvCollector CMS view

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `target_replica_count` | int | Desired replica count | `DmvCollectorQueryUnitTests.cs` |
| `min_replica_count` | int | Minimum replica count | `DmvCollectorQueryUnitTests.cs` |
| `restart_wait_duration` | timespan/int | Restart/cooldown wait period | `DmvCollectorQueryUnitTests.cs` |

## 17. MonAnalyticsLogicalServerSnapshot — Logical server analytics snapshot

### Definition
Search results point to DmvCollector unit tests, indicating this is a CMS/DmvCollector snapshot view for logical server metadata. No direct inline schema was recovered in the first pass.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `DmvCollectorQueryUnitTests.cs` references the view indirectly
- **Data Origin**: DmvCollector/CMS snapshot (schema not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | Direct schema not surfaced in first-pass search | — |

## 18. MonActiveXeSessions — Active XE session inventory

### Definition
MDS configuration shows an event/table family for active DB XE sessions (`MonActiveDbXeSessions`, related events/targets/actions/object-columns). Search did not surface a concrete C# schema for the SQL DB-facing table name.

### Code Source
- **Repository**: `SQL2017`
- **Key Files**: `/Sql/xdb/externals/mds/CentralMDSAgentConfig_template.xml`
- **Data Origin**: MDS directory-watched XE session telemetry under `\Public\MonActiveDbXeSessions`

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | Config shows table/event creation but not final schema | — |

## 19. MonDatabaseMetrics — Database size/usage metric table

### Definition
Used to compare backend max size versus analytics metadata. The runner computes effective max size from `storage_in_bytes / storage_percent * 100`, which implies this table contains normalized storage consumption metrics per database.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/Godzilla/MaxSizeBug9832313Alert.cs`
- **Data Origin**: DB metrics stream joined to analytics snapshots

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `server_name` | string | Logical server name | `MaxSizeBug9832313Alert.cs` |
| `database_name` | string | Database name | `MaxSizeBug9832313Alert.cs` |
| `storage_in_bytes` | long | Observed storage size | `MaxSizeBug9832313Alert.cs` |
| `storage_percent` | numeric | Percent-of-max usage | `MaxSizeBug9832313Alert.cs` |
| `TIMESTAMP` | datetime | Snapshot time used for lookback | `MaxSizeBug9832313Alert.cs` |

## 20. MonDmLogSpaceInfo — DMV log-space counter stream

### Definition
The max-log-size reset runner uses this as the raw log-space source and filters it on `counter_name contains 'Used Size'`. It is effectively a DMV/perf-counter stream for per-database log usage.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/LogNearFull/MaxLogSizeReset.cs`
- **Data Origin**: DMV/log-space info collector

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `counter_name` | string | Counter discriminator (`Used Size`) | `MaxLogSizeReset.cs` |
| `cntr_value` | long | Raw counter value | `MaxLogSizeReset.cs` |
| `TIMESTAMP` | datetime | Snapshot time | `MaxLogSizeReset.cs` |
| `ClusterName` | string | Ring/cluster source | `MaxLogSizeReset.cs` |
| `instance_name` | string | Physical DB instance name; first 36 chars form physical DB id | `MaxLogSizeReset.cs` |
| `AppName` | string | Owning worker app | `MaxLogSizeReset.cs` |
| `AppTypeName` | string | Worker type filter | `MaxLogSizeReset.cs` |

## 21. MonDmSloViolations — Per-interval SLO violation telemetry

### Definition
The observability framework uses this as its core incident/baseline signal for CPU, IO, and log SLO regressions. It contains detailed per-interval violation amounts and timing fields.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/SqlMiObservabilityFramework/SqlMiObservabilityClassification/Classes/AnyViolationClass.cs`
- **Data Origin**: Dm SLO-violation collector

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `PreciseTimeStamp` | datetime | Exact violation time | `AnyViolationClass.cs` |
| `LogicalServerName` | string | Server identity | `AnyViolationClass.cs` |
| `db_name` | string | DB identity (extended to `database_name`) | `AnyViolationClass.cs` |
| `slo_io_violation` | int/bool | IO violation flag | `AnyViolationClass.cs` |
| `slo_io_violation_amount` | numeric | IO violation magnitude | `AnyViolationClass.cs` |
| `slo_cpu_violation` | int/bool | CPU violation flag | `AnyViolationClass.cs` |
| `slo_cpu_consumed_time_ms` | long | CPU active time | `AnyViolationClass.cs` |
| `slo_cpu_delay_time_ms` | long | CPU delay/violation time | `AnyViolationClass.cs` |
| `slo_log_violation` | int/bool | Log violation flag | `AnyViolationClass.cs` |
| `slo_log_active_time_ms` | long | Log active interval | `AnyViolationClass.cs` |
| `slo_log_bytes_delivered` | long | Delivered log bytes | `AnyViolationClass.cs` |

## 22. MonDwRequestSteps — Synapse/DW request-step telemetry

### Definition
DW diagnostics code writes this as a dynamic MDS event and explicitly applies SQL-command obfuscation rules for it. That indicates a per-request-step execution table for warehouse engine diagnostics.

### Code Source
- **Repository**: `DsMainDev-bbexp`
- **Key Files**: `/Sql/Ntdbms/mpdw/Dev/src/Common/Common/Diagnostics/Listeners/MonitoringDiagnosticsServiceListener.cs`
- **Data Origin**: DW MDS diagnostics listener / ETW event stream

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `command` | string | Step SQL text; obfuscated for begin/running events | `MonitoringDiagnosticsServiceListener.cs` |
| `EventName` | string | Event phase name | `MonitoringDiagnosticsServiceListener.cs` |
| `ErrorCode` | int | Surfaced SQL/MPP/Odbc error code | `MonitoringDiagnosticsServiceListener.cs` |
| `ErrorState` | int | SQL error state when available | `MonitoringDiagnosticsServiceListener.cs` |
| `StackTrace` | string | Exception stack trace | `MonitoringDiagnosticsServiceListener.cs` |
| `Message` | string | Human-readable message | `MonitoringDiagnosticsServiceListener.cs` |

## 23. MonDwUnexpectedExceptions — DW unexpected-exception stream

### Definition
Also emitted via the DW diagnostics listener, with the same SQL text redaction path as request-step telemetry. This table captures unexpected exception events and sanitized command text.

### Code Source
- **Repository**: `DsMainDev-bbexp`
- **Key Files**: `/Sql/Ntdbms/mpdw/Dev/src/Common/Common/Diagnostics/Listeners/MonitoringDiagnosticsServiceListener.cs`
- **Data Origin**: DW MDS diagnostics listener / exception ETW events

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `command` | string | Obfuscated SQL when exception event is relevant | `MonitoringDiagnosticsServiceListener.cs` |
| `EventName` | string | Includes `GeneralInstrumentation:UnexpectedExceptionErrorEvent` | `MonitoringDiagnosticsServiceListener.cs` |
| `ErrorCode` | int | Exception error number | `MonitoringDiagnosticsServiceListener.cs` |
| `ErrorState` | int | SQL error state when present | `MonitoringDiagnosticsServiceListener.cs` |
| `StackTrace` | string | Exception stack | `MonitoringDiagnosticsServiceListener.cs` |
| `Message` | string | Redacted message text | `MonitoringDiagnosticsServiceListener.cs` |

## 24. MonConnectivityFeatureSnapshot — Connectivity feature-state snapshot

### Definition
Search results primarily surfaced deployment-package references and not a concrete schema. Treat as a connectivity feature-state snapshot used by infra/deployment flows.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: Deployment package references only; no authoritative view/schema recovered
- **Data Origin**: Connectivity/deployment snapshot (schema not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | No direct schema recovered | — |

## 25. MonDataSync — SQL Data Sync operational telemetry

### Definition
Used to detect UAMI loading failures and skipped sync-group drops. The runner treats it as the authoritative app-level Data Sync event stream with structured detail text and sync-group identifiers.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/MdsRunners/MdsRunners/Runners/ManagedBackup/DataSync/DataSyncUAMIFailureAlert.cs`
- **Data Origin**: Data Sync runtime telemetry

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `AppName` | string | Sync app identity | `DataSyncUAMIFailureAlert.cs` |
| `Detail` | string | Main event detail text | `DataSyncUAMIFailureAlert.cs` |
| `EDetail` | string | Extended detail text | `DataSyncUAMIFailureAlert.cs` |
| `SyncGroupId` | guid/string | Sync-group identity | `DataSyncUAMIFailureAlert.cs` |
| `UniqueFailureLogs` | dynamic | Distinct failure messages summarized per app | `DataSyncUAMIFailureAlert.cs` |
| `ObjectFailurePercentage` | numeric | Per-object UAMI load failure rate | `DataSyncUAMIFailureAlert.cs` |
| `AllFailurePercentage` | numeric | Whole-app UAMI load failure rate | `DataSyncUAMIFailureAlert.cs` |

## 26. MonResourceStats — DB resource-consumption rollup

### Definition
Used by a WAFL mitigator as a source of stage DB inventory. The code summarizes by cluster, logical server, and database name, implying a per-database resource stats table.

### Code Source
- **Repository**: `SqlTelemetry`
- **Key Files**: `/Src/WAFL/Core/Mitigators/ThroughputTestMitigator.cs`
- **Data Origin**: Resource stats rollup (`WASD2StageMonResourceStats` in stage usage)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `ClusterName` | string | Cluster/ring | `ThroughputTestMitigator.cs` |
| `LogicalServerName` | string | Logical server | `ThroughputTestMitigator.cs` |
| `database_name` | string | Database name | `ThroughputTestMitigator.cs` |
| `originalEventTimestamp` | datetime | Lookback filter column | `ThroughputTestMitigator.cs` |

## 27. MonDeploymentWorkflow — Deployment workflow execution telemetry

### Definition
Documented internal telemetry table for deployment workflow progress, sequencing, snapshots, and exceptions. The TechDoc provides both example query shape and a detailed field list.

### Code Source
- **Repository**: `Doc-SQL-Deployment-Infrastructure`
- **Key Files**: `/TechDocs/Telemetry/MonDeploymentWorkflow.md`
- **Data Origin**: Deployment workflow/runtime instrumentation

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `sequence_type` | string | Workflow step category | `MonDeploymentWorkflow.md` |
| `sequence_event_name` | string | Specific workflow event | `MonDeploymentWorkflow.md` |
| `workflow_id` | guid/string | Workflow instance id | `MonDeploymentWorkflow.md` |
| `sequence_id` | guid/string | Sequence instance id | `MonDeploymentWorkflow.md` |
| `sequence_properties` | dynamic/string | JSON payload for step properties | `MonDeploymentWorkflow.md` |
| `result` | string | Event result | `MonDeploymentWorkflow.md` |
| `message` | string | Message text | `MonDeploymentWorkflow.md` |
| `exception_type` | string | Exception type | `MonDeploymentWorkflow.md` |
| `snapshot_id` | guid/string | Snapshot identifier | `MonDeploymentWorkflow.md` |
| `status` | string | Entity/workflow status | `MonDeploymentWorkflow.md` |

## 28. MonDwEngineLogs — DW engine log stream

### Definition
Search results surfaced DW backup/restore bot code but no direct schema. Treat as a DW engine log table referenced by warehouse automation and diagnostics.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `DwBackupSlaAutoMitigator.cs` references only; no direct schema recovered
- **Data Origin**: DW engine logging pipeline (schema not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | No reliable schema surfaced in first-pass search | — |

## 29. MonAnalyticsRPSnapshot — RP/control-plane analytics snapshot

### Definition
Search results pointed to DmvCollector unit tests rather than direct field definitions. The table appears to be an analytics snapshot for RP/control-plane metadata.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: `DmvCollectorQueryUnitTests.cs` references only
- **Data Origin**: DmvCollector/CMS analytics snapshot (schema not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | Direct schema not surfaced in first-pass search | — |

## 30. MonAzureFileShareSnapshot — Azure file-share snapshot inventory

### Definition
Repo search mostly returned dashboards/usage references rather than a concrete source definition. Treat as a storage snapshot table consumed by investigative KQL.

### Code Source
- **Repository**: Referenced in KQL templates only
- **Key Files**: Dashboard references only; no direct schema recovered
- **Data Origin**: Azure file-share snapshot inventory (schema not recovered)

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
| `Not recovered` | — | No reliable schema surfaced in first-pass search | — |

## Shared Tables Also Present in MI Reference

For shared table definitions, see `mi-tables-code-reference.md`.

Shared/high-value tables observed in both SQL DB and MI references include:
- `MonDeploymentAutomation`
- `MonRolloutProgress`
- `MonDwBilling`
- `MonSocrates`
- `MonBackup`
- `MonRgManager`
- `MonDmRealTimeResourceStats`
- `MonGeoDRFailoverGroups`
- `MonQueryProcessing`
- `MonResourcePoolStats`

# Dashboard New Tables — Code Definitions (2026-04-30)

## MonAuditOperational — Operational Audit Events
### Definition
Audit event stream for SQL DB operational auditing. Records audit lifecycle events: start/stop/modify, target changes, state transitions. Each row is an XEvent from the audit subsystem on the backend worker.
### Code Source
- **Data Origin**: XEvent (audit_operational session)
- **Key Relationship**: Joins to MonAuditOperationalTelemetry via audit_guid
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| audit_name | string | Name of the audit object |
| audit_id | long | Audit object identifier |
| audit_guid | string | Unique audit GUID (join key) |
| target_path | string | Audit target storage path |
| error_code | long | Error code (0 = success) |
| state | long | Audit state |
| is_geo_replica | bool | Whether on geo replica |
| is_named_replica | bool | Whether on named replica |

## MonAuditOperationalTelemetry — Audit Configuration Telemetry
### Definition
Extension table for audit operational telemetry. Records audit specification changes: action groups added/dropped, retention policy, category changes. Paired with MonAuditOperational via audit_guid.
### Code Source
- **Data Origin**: XEvent (audit telemetry)
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| audit_specification_name | string | Audit spec being modified |
| audit_action_groups_added | string | Action groups enabled |
| audit_action_groups_dropped | string | Action groups removed |
| retention_days | long | Audit retention window in days |
| category | string | Audit category |

## MonAutomaticTuningState — Automatic Tuning State Snapshot
### Definition
Per-database automatic tuning state snapshot from MDS Runner. Records desired vs actual state for each tuning option (Force Plan, Create Index, Drop Index). Numeric codes for mode and option states.
### Code Source
- **Data Origin**: MDS Runner (CMS snapshot of sys.database_automatic_tuning_options)
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| option_name | string | Tuning option (e.g., FORCE_LAST_GOOD_PLAN) |
| option_desired_state | long | 0=Off, 1=On (user requested) |
| option_actual_state | long | 0=Off, 1=On (effective) |
| option_reason | long | Reason code if actual != desired |
| option_system_disabled | long | 1 if system disabled |
| mode_desired_state | long | Auto/Custom/Inherit |
| mode_actual_state | long | Effective mode |

## MonBillingJobAgentStatus — Elastic Job Agent Billing Status
### Definition
Billing/status snapshot for Elastic Job Agent resources. Tracks job account lifecycle states and billability transitions for Azure billing pipeline.
### Code Source
- **Data Origin**: CMS snapshot
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| job_account_name | string | Job Agent account name |
| job_account_id | string | Job Agent account GUID |
| current_state | string | Lifecycle state |
| service_level_objective | string | SLO tier |
| current_state_billability | long | Billable flag (current) |
| last_state_billability | long | Billable flag (previous) |
| billing_start_time | datetime | When billing started |
| resource_tags | string | Azure resource tags JSON |

## MonBillingSqlDbVCoreBackupSizes — vCore Backup Storage Billing
### Definition
Billing snapshot for SQL DB vCore backup counts and storage sizes. Used by billing pipeline to calculate backup storage charges. Separates LRS vs ZRS storage for pricing tiers.
### Code Source
- **Data Origin**: CMS snapshot (backup metadata)
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| backup_retention_in_days | long | Configured retention days |
| full_backup_count | long | Number of full backups |
| diff_backup_count | long | Number of differential backups |
| log_backup_count | long | Number of log backups |
| backup_storage_size | long | Total backup storage (bytes) |
| backup_zrs_storage_size | long | ZRS backup storage (bytes) |
| backup_lrs_storage_size | long | LRS backup storage (bytes) |
| database_state | long | Database state code |

## MonBillingVldbPoolStatus — VLDB Elastic Pool Billing
### Definition
Billing/status snapshot for Very Large Database (VLDB) elastic pools. Tracks pool-level billability, license type, and zone resilience for Azure billing pipeline.
### Code Source
- **Data Origin**: CMS snapshot
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| vldb_pool_id | string | VLDB pool GUID |
| vldb_pool_name | string | Pool display name |
| database_edition | string | Edition (Premium, BusinessCritical, etc.) |
| current_state | string | Pool lifecycle state |
| current_state_billability | long | Billable flag |
| license_type | string | License type (LicenseIncluded, BasePrice) |
| service_level_objective | string | SLO |
| zone_resilient | long | 1 if zone-redundant |
| read_scale_units | long | Read-scale replica count |

## MonConfigMgr — Local Config Manager Events
### Definition
Traces from the local configuration manager service on each node. Records config switch changes, run durations, and config application events. Used to diagnose configuration deployment issues.
### Code Source
- **Data Origin**: XEvent / service trace
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| LocalConfigMgrTraceEventType | long | Event type code |
| RunDuration | long | Config run duration (ms) |
| TraceId | string | Trace correlation ID |
| switchName | string | Config switch being changed |
| switchValue | string | New switch value |
| applicationType | string | App type receiving config |
| Details/details | string | Event details text |

## MonFabricClient — Service Fabric Client Operations
### Definition
Service Fabric client API call telemetry from SQL Azure nodes. Records fabric operations (partition queries, service resolution, upgrade operations) with timing and error details. Critical for diagnosing replica placement and fabric health issues.
### Code Source
- **Repository**: SqlTelemetry (VnetSvcEndpointXdbhostHealth.cs references)
- **Data Origin**: SF client SDK instrumentation
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| elapsed_time_milliseconds | real | API call duration |
| exception_type | string | Exception if failed |
| fabric_service_uri | string | Target SF service |
| fabric_application_uri | string | Target SF application |
| partition_id | string | Target partition GUID |
| caller_function | string | Calling function name |
| caller_state_machine | string | State machine context |
| unplaced_replica_reasons | string | Why replica couldn't be placed |

## MonJobAgentStatus — Elastic Job Agent Status
### Definition
Operational status snapshot for Elastic Job Agent. Similar to MonBillingJobAgentStatus but focused on operational state rather than billing. Includes database-level SLO tracking.
### Code Source
- **Data Origin**: CMS snapshot
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| job_account_name | string | Job Agent name |
| job_account_id | string | Job Agent GUID |
| server_name | string | Hosting server |
| database_name | string | Hosting database |
| current_state | string | Agent state |
| service_level_objective_id | string | Agent SLO ID |
| db_service_level_objective_id | string | Database SLO ID |

## MonUserQuery — User Query Tracking
### Definition
User query operation telemetry from the backend worker. Records query execution events including duration, errors, and client context. MDS agent collects from Public\MonUserQuery telemetry directory.
### Code Source
- **Repository**: TSG-SQL-DB-Telemetry (MonitoringSqlMDSAgentConfig_template)
- **Data Origin**: XEvent → MDS directory watch
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| operation_name | string | Query operation type |
| logical_server_name | string | Server name |
| logical_database_name | string | Database name |
| session_id | long | SQL session ID |
| client_app_name | string | Client application name |
| duration | long | Query duration (microseconds) |
| error_code | long | Error code (0 = success) |
| http_code | long | HTTP response code |

## MonXOdbcWrapper — ODBC Wrapper Events
### Definition
ODBC wrapper diagnostic events from the backend worker. Records ODBC connection lifecycle, error states, and connection string details. MDS agent collects from Public\MonXOdbcWrapper directory.
### Code Source
- **Repository**: TSG-SQL-DB-Telemetry (MonitoringSqlMDSAgentConfig_template)
- **Data Origin**: XEvent → MDS directory watch
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| odbc_handle | long | ODBC handle ID |
| error_code | long | ODBC error code |
| sql_state | long | SQL state code |
| odbc_state | string | ODBC state string |
| message | string | Error/diagnostic message |
| odbc_connection_string | string | Connection string (may be redacted) |
| call_stack | string | Call stack at event time |

## MonXdbHost — XDB Host Monitoring
### Definition
XDB host health telemetry from database nodes. Used by VnetSvcEndpointXdbhostHealth runner to detect nodes missing Service Tunnel (VNET) adapters. Records adapter presence checks with text-based status messages.
### Code Source
- **Repository**: SqlTelemetry
- **Key Files**: /Src/MdsRunners/MdsRunners/Runners/VnetSvcEndpoints/VnetSvcEndpointXdbhostHealth.cs
- **Data Origin**: Node-level health check (XDB host service)
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| text | string | Health check message ("Service Tunnel Adapter is not present" / "CheckServiceTunnelAdapter - Adapter found") |
| NodeRole | string | Node role (filter != 'MN') |
| ClusterName | string | Ring/cluster name |
| NodeName | string | Node identifier |

## MonVaCmsPolicySnapshot — VA Policy Configuration Snapshot
### Definition
CMS snapshot of Vulnerability Assessment policy configuration per server/database. Records VA scan schedule settings, email notification config, and storage settings.
### Code Source
- **Data Origin**: CMS snapshot
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| IsRecurringScansEnabled | long | 1 if periodic scans enabled |
| IsServerPolicy | long | 1 if server-level policy |
| PolicyType | string | Policy type |
| HasStorageContainerPath | long | 1 if storage configured |
| IsStoragelessEnabled | long | 1 if storageless VA |
| EmailAccountAdmin | long | 1 if admin gets email |

## MonVaService — VA Service Logs
### Definition
Vulnerability Assessment service operational logs. Records VA service processing events, component health, and diagnostic messages.
### Code Source
- **Data Origin**: VA service logs (OpenTelemetry format)
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| severity | string | Log severity level |
| component | string | VA component name |
| message | string | Log message text |
| InstanceServerName | string | Target server |
| InstanceAppTypeName | string | App type of target |

## MonVaServiceOperationalAlerts — VA Operational Alerts
### Definition
Operational alerts emitted by the VA service health monitoring pipeline. Records alert conditions with severity and additional diagnostic info.
### Code Source
- **Data Origin**: VA service alert pipeline
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| Component | string | VA component raising alert |
| Source | string | Alert source |
| Severity | string | Alert severity |
| AlertMessage | string | Alert description |
| AdditionalInfo | string | Extra diagnostic context |

## MonVaServiceScanResults — VA Scan Results
### Definition
Individual scan findings from Vulnerability Assessment scans. Each row is one rule evaluation result for one database scan. Includes baseline comparison data.
### Code Source
- **Data Origin**: VA scan output
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| ScanId | string | Scan execution GUID |
| ScanType | string | Scan type |
| ScanTriggerType | string | Manual/Scheduled/OnDemand |
| DatabaseName | string | Scanned database |
| RuleId | string | VA rule identifier |
| RuleSeverity | string | Rule severity level |
| ResultLevel | string | Pass/Fail/Warning |
| BaselineResultLevel | string | Previous baseline result |
| ResultSizeInBytes | long | Result payload size |

## MonWiDmMissingIndexes — Missing Index Recommendations
### Definition
Snapshot of sys.dm_db_missing_index_details + dm_db_missing_index_group_stats DMVs. Records missing index suggestions with impact scores for query optimization.
### Code Source
- **Data Origin**: MDS Runner (DMV snapshot)
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| equality_columns | string | Columns for equality predicates |
| inequality_columns | string | Columns for inequality predicates |
| included_columns | string | Suggested included columns |
| statement | string | Target table (schema.table) |
| user_seeks | long | Number of user seeks that would benefit |
| avg_user_impact | real | Estimated % improvement |
| avg_total_user_cost | real | Average query cost |

## MonWiDmMissingIndexesQuery — Missing Indexes with Query Hash
### Definition
Extended missing index data with query-level granularity. Adds query_hash, query_plan_hash, and sql_handle to link missing index suggestions to specific queries.
### Code Source
- **Data Origin**: MDS Runner (DMV snapshot)
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| query_hash | string | Query hash for grouping |
| query_plan_hash | string | Plan hash |
| last_sql_handle | string | SQL handle for text retrieval |
| equality_columns | string | Equality predicate columns |
| inequality_columns | string | Inequality predicate columns |
| included_columns | string | Suggested included columns |

## MonWiSysIndexColumns — Index Column Metadata Snapshot
### Definition
Snapshot of sys.index_columns system view. Records index-column mappings for all indexes in monitored databases.
### Code Source
- **Data Origin**: MDS Runner (CMS snapshot)
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| object_id | long | Table object ID |
| index_id | long | Index identifier |
| column_id | long | Column identifier |
| key_ordinal | long | Position in index key |
| is_descending_key | long | 1 if descending |
| is_included_column | long | 1 if included (non-key) column |
| column_store_order_ordinal | long | Columnstore order position |

## MonManagementOperation — Management Operations (RADS)
### Definition
Management operation telemetry used by RADS (Regression Auto-Detection System). Related to MonManagement but uses operation_type field (vs MonManagementResourceProvider's operation_name). Not found as separate physical table — likely a view/alias over MonManagement.
### Code Source
- **Repository**: SqlTelemetry
- **Key Files**: /Src/MdsRunners/MdsRunners/Runners/Provisioning/Components/Quality/Rads/KustoQueryProvider.cs
- **Data Origin**: Control plane operations
### Key Columns
| Column | Type | Meaning |
|--------|------|---------|
| operation_type | string | Management action type (RADS uses this vs operation_name) |
| operation_parameters | string | XML payload with server/db details |
| request_id | string | Operation correlation ID |

## MonDmRealTimeResourceStats_Sample_sec — Per-Second Resource Stats
### Definition
NOT a physical table. Likely a Kusto function or dashboard-level calculation that resamples MonDmRealTimeResourceStats at per-second granularity (vs the standard 15-second interval). Used in DRI Copilot performance CPU discrepancy skills.
### Code Source
- **Repository**: SqlLivesiteCopilot (CPU_UserPoolCPUDiscrepancy.yaml)
- **Data Origin**: Derived from MonDmRealTimeResourceStats (which maps to sys.dm_db_resource_stats)

## MonLoginTime — Login Time Breakdown
### Definition
NOT a physical table. Dashboard-calculated view that breaks down MonLogin total_time_ms into sub-phases (redirect, auth, connection setup). The login timing columns all come from MonLogin XEvent fields.
### Code Source
- **Data Origin**: Derived from MonLogin (Gateway XEvent: process_login_finish)

## MonRedirectorTime — Redirector Timing
### Definition
NOT a physical table. Dashboard-calculated view for Gateway redirector timing. Likely derived from MonRedirector table with timing-focused projections.
### Code Source
- **Data Origin**: Derived from MonRedirector (Gateway redirect/cache telemetry)




# Shared Tables — Code Definitions (from MI Reference)

The following table code definitions are shared between SQL DB and MI.
They were originally documented in `mi-tables-code-reference.md` and are included here for self-contained reference.

---

## AlrSQLErrorsReported — SQL Errorlog / Error-Reported Events

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

---

## AlrSharedMAHeartbeat — Heartbeat telemetry for MA agents

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

---

## AlrWinFabHealthApplicationState — Service Fabric application health snapshots

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

---

## AlrWinFabHealthNodeEvent — Service Fabric node health events

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

---

## AlrWinFabHealthPartitionEvent — Service Fabric partition health events

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

---

## MonAnalyticsDBSnapshot — Database Snapshot Properties

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

---

## MonAppEventLogErrors — Windows application event-log errors

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

---

## MonAttentions — Client-cancel / attention events

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

---

## MonAuditRuntimeTelemetry — Runtime audit events sent to Cosmos

### Definition
Audit runtime telemetry table registered in Cosmos collection workflows for the auditing component.

### Code Source
- **Repositories**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Workflow registration calls `SetNewCosmosCollectionWorkflowTemplateRecord(tableName: "MonAuditRuntimeTelemetry", component: Component.Auditing, ...)`.

---

## MonAuditSessionStatus — Audit session status stream

### Definition
Audit session-status telemetry registered in Cosmos collection workflows for the auditing component.

### Code Source
- **Repositories**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Workflow registration calls `SetNewCosmosCollectionWorkflowTemplateRecord(tableName: "MonAuditSessionStatus", component: Component.Auditing, ...)`.

---

## MonAutomaticTuning — Automatic tuning regression/correction telemetry

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

---

## MonAzureActivDirService — Azure AD service telemetry

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

---

## MonBackup — Backup History

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

---

## MonBlockedProcessReportFiltered — Filtered blocked-process reports

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

---

## MonCDCTraces — Change Data Capture traces

### Definition
CDC telemetry table registered in Cosmos collection workflows. I did not find a stronger schema file in the allotted searches.

### Code Source
- **Repositories**: `BusinessAnalytics`
- **Key Files**:
  - `BusinessAnalytics:/Src/Deployment/DeploymentPackageInstances/SterlingDeployments/CosmosDeploymentPackage.cs`
- **Evidence**:
  - Workflow registration calls `SetNewCosmosCollectionWorkflowTemplateRecord(tableName: "MonCDCTraces", ...)`.

---

## MonCTTraces — Change Tracking traces

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

---

## MonCapacityTenantSnapshot — Capacity state snapshot for tenant rings

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

---

## MonClusterLoad — Cluster/node health state reports

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

---

## MonConfigAppTypeOverrides — App-type configuration overrides

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

---

## MonConfigLogicalServerOverrides — Logical-server configuration overrides

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

---

## MonCounterFiveMinute — Five-minute performance counter rollups

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

---

## MonCvBranchBuildVersionMetadata — Branch/build version metadata

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

---

## MonDatabaseEncryptionKeys — Database encryption key metadata

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

---

## MonDatabaseMetadata — Unified system-table metadata inventory

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

---

## MonDbSeedTraces — Seeding Progress

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

---

## MonDeadlockReportsFiltered — Filtered deadlock XML reports

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

---

## MonDmCloudDatabaseWaitStats — Wait Statistics

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

---

## MonDmContinuousCopyStatus — Continuous-copy / geo-replication status DMV snapshot

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

---

## MonDmDbHadrReplicaStates — HADR replica-state DMV snapshot

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

---

## MonDmDbResourceGovernance — Per-database resource governance limits

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

---

## MonDmIoVirtualFileStats — Per-file IO and size DMV snapshot

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

---

## MonDmOsBPoolPerfCounters — Buffer-pool performance counters

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

---

## MonDmOsExceptionStats — OS exception statistics DMV snapshot

### Definition
Referenced in KQL templates only. I did not find a reliable producer/schema file in the allotted searches.

### Code Source
- **Search result**: no strong defining file found.

---

## MonDmOsMemoryClerks — Memory clerk DMV snapshot

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

---

## MonDmOsSpinlockStats — Spinlock contention DMV telemetry

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

---

## MonDmOsWaitStats — Wait statistics DMV telemetry

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

---

## MonDmRealTimeResourceStats — DB-Level Real-Time Stats

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

---

## MonDmTempDbFileSpaceUsage — tempdb file-space DMV telemetry

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

---

## MonDmTranActiveTransactions — Active transaction DMV telemetry

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

---

## MonDmUserActivityDetection — User activity detection telemetry

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

---

## MonDwBilling — DW billing telemetry

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

---

## MonFabricApi — Service Fabric API HA events

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

---

## MonFabricClusters — Fabric cluster inventory/health telemetry

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

---

## MonFabricDebug — Fabric debug traces

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

---

## MonFabricThrottle — Fabric throttling telemetry

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

---

## MonFedAuthTicketService — Federated auth ticket service telemetry

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

---

## MonFullTextInfo — Full-text information/event telemetry

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

---

## MonFulltextActiveCatalogs — Full-text crawl/catalog status telemetry

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

---

## MonGeoDRFailoverGroups — FOG Configuration

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

---

## MonGovernorResourcePools — Resource Governor pool telemetry

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

---

## MonGovernorWorkloadGroups — Resource Governor workload-group telemetry

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

---

## MonImportExport — Import/Export request lifecycle telemetry

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

---

## MonLabRunResults — Lab-run result rollup telemetry

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

---

## MonLogReaderTraces — Replication log-reader phase/session telemetry

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

---

## MonLogin — Login Activity

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

---

## MonLtrConfiguration — Long-term retention configuration/state

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

---

## MonMIGeoDRFailoverGroupsConnectivity — MI GeoDR FOG connectivity status

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

---

## MonMachineLocalWatchdog — Machine-local certificate/watchdog findings

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

---

## MonManagedInstanceResourceStats — Instance Resource Usage

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

---

## MonManagedServers — MI Instance Metadata

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

---

## MonManagement — Management Operations

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

---

## MonManagementArchivedBackup — Archived backup / LTR archival telemetry

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

---

## MonManagementExceptions — Management exception telemetry

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

---

## MonManagementOperations — Control-plane management operation telemetry

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

---

## MonManagementResourceProvider — ARM/resource-provider request telemetry

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

---

## MonNodeAgentEvents — Node agent operational events

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

---

## MonNodeTraceETW — Generic node ETW trace sink

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

---

## MonNonPiiAudit — Non-PII audit telemetry

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

---

## MonPrivateClusters — Private cluster inventory telemetry

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

---

## MonQPTelemetry — Query-processing telemetry

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

---

## MonQueryProcessing — Query-processing/XEvent plan telemetry

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

---

## MonQueryStoreFailures — Query Store severe-failure/shutdown telemetry

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

---

## MonQueryStoreInfo — Query Store diagnostics/info telemetry

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

---

## MonRecoveryTrace — Database recovery progress/completion traces

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

---

## MonRedirector — Redirector / URI-cache redirection telemetry

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

---

## MonResourcePoolStats — Resource pool performance telemetry

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

---

## MonRestoreEvents — Restore event timeline telemetry

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

---

## MonRestoreRequests — Restore request lifecycle telemetry

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

---

## MonRgLoad — Resource governor load telemetry

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

---

## MonRgManager — Resource governor manager metrics

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

---

## MonRolloutProgress — Rollout orchestration progress telemetry

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

---

## MonSQLSystemHealth — System Health XEvents / Errorlog Lines

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

---

## MonSQLXStore — SQL XStore telemetry

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

---

## MonSQLXStoreIOStats — SQL XStore I/O statistics telemetry

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

---

## MonSocrates — Socrates platform telemetry

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

---

## MonSqlCaches — SQL cache telemetry

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

---

## MonSqlDump — SQL dump and crash telemetry

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

---

## MonSqlDumperActivity — SQL dumper invocation telemetry

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

---

## MonSqlFrontend — SQL frontend service telemetry

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

---

## MonSqlMemNodeOomRingBuffer — Memory-node OOM ring buffer telemetry

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

---

## MonSqlMemoryClerkStats — Memory clerk statistics telemetry

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

---

## MonSqlRenzoCp — Renzo control-plane service telemetry

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

---

## MonSqlRenzoTraceEvent — Renzo trace-event telemetry

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

---

## MonSqlRgHistory — Resource governor history telemetry

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

---

## MonSqlRmRingBuffer — SQL resource-monitor ring buffer telemetry

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

---

## MonSqlSecurityService — SQL Security Service telemetry

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

---

## MonSqlShrinkInfo — SQL shrink-operation telemetry

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

---

## MonSqlTransactions — SQL transaction telemetry

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

---

## MonSystemEventLogErrors — System event-log error telemetry

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

---

## MonUcsConnections — UCS connection telemetry

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

---

## MonWiDmDbPartitionStats — Workload Insights DB partition statistics

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

---

## MonWiQdsExecStats — Query Store Execution Stats

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

---

## MonWiQdsWaitStats — Query Store wait statistics telemetry

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

---

## MonWiQueryParamData — Query-parameter telemetry

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

---

## MonWorkerWaitStats — Worker wait-statistics telemetry

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

---

## MonXdbhost — XDB host service telemetry

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
