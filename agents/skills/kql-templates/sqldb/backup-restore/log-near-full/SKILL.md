---
name: log-near-full
description: Debug Azure SQL Database transaction log full or near-full issues (errors 9002, 40552). Analyzes log truncation holdup reasons including backups, CDC, Synapse Link, Fabric Mirroring, HA replication, active transactions, and XTP checkpoints. Required inputs from calling agent - kusto-cluster-uri, kusto-database, physical_database_id, and all database configuration variables from get-db-info skill.
---

# Debug Azure SQL Database Log Full/Log Near Full Issues

Debug transaction log full or near-full issues that cause write failures (errors 9002, 40552) for Azure SQL Database.

## Background

The transaction log is truncated when log backups complete and all log consumers finish consuming the log. When truncation cannot occur, the log grows until reaching maximum capacity, causing write transaction failures.

**Log Consumers:**
- **Full/Differential Backup**: Holds truncation until backup writes complete
- **CDC/Synapse Link/Fabric Mirroring**: Holds truncation until log reader completes scan
- **High Availability**: Holds truncation until log reaches all secondaries and redo completes (includes GeoDR)
- **Hekaton (XTP)**: Holds truncation until XTP checkpoint completes

**Log Growth Issues:**
- **DirectoryQuotaNearFull**: Occurs when node directory has insufficient space for log growth
- **Severity**: Incidents created as Severity 2 or 3 when log space exceeds thresholds
- **Customer Impact**: Full log prevents all write operations, causing downtime

## Required Information

This skill requires the following inputs (should be obtained by the calling agent):

### From User or ICM:
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill:
- **physical_database_id**
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **NodeName**
- **service_level_objective**
- **deployment_type** (e.g., "GP without ZR", "GP with ZR", "BC")
- All other database environment variables

**Note**: The calling agent should use the `execute-kusto-query` skill and the `get-db-info` skill before invoking this skill.

## Workflow

### 1. Analyze Historical Log Space and Holdup Reason

Execute query **LOG100** from [references/queries.md](references/queries.md) (Historical Log Space Info).

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Track log space usage and holdup reasons"
- parameters:
  {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "let _physical_DBID = '{physical_database_id}'; let _startTime = datetime({StartTime}); let _endTime = datetime({EndTime}); let window = 5m; MonDmLogSpaceInfo | where TIMESTAMP between (_startTime .. _endTime) | extend physical_db_name = substring(toupper(instance_name), 0, 36) | where physical_db_name =~ _physical_DBID | project TIMESTAMP, ClusterName, NodeName, logical_server_name, AppName, physical_db_name, counter_name, cntr_value | order by TIMESTAMP asc, counter_name desc | extend LogSpaceUsed = prev(cntr_value) | where counter_name contains 'Log File(s) Size (KB)' | extend LogSpaceUsedGB = round(LogSpaceUsed/(1024.0*1024), 1), MaxLogSizeGB = round(cntr_value/(1024.0*1024), 1) | extend LogUsedPercentage = iif(MaxLogSizeGB > 0, round(LogSpaceUsedGB*100/MaxLogSizeGB, 1), 0.0) | summarize arg_max(TIMESTAMP, ClusterName, NodeName, logical_server_name, AppName, physical_db_name, LogSpaceUsedGB, MaxLogSizeGB, LogUsedPercentage) by Window_5m = bin(TIMESTAMP, window) | join kind = leftouter (MonFabricThrottle | where TIMESTAMP between (_startTime .. _endTime) | where database_name =~ _physical_DBID | extend log_hold_up_reason = case(log_truncation_holdup == 'AvailabilityReplica', 'AVAILABILITY_REPLICA', log_truncation_holdup == 'LogBackup', 'LOG_BACKUP', log_truncation_holdup == 'ActiveTransaction', 'ACTIVE_TRANSACTION', log_truncation_holdup == 'ReplicationXact', 'REPLICATION', log_truncation_holdup == 'ActiveBackup', 'ACTIVE_BACKUP_OR_RESTORE', log_truncation_holdup) | summarize arg_max(TIMESTAMP, ClusterName, NodeName, LogicalServerName, AppName, log_hold_up_reason) by Window_5m = bin(TIMESTAMP, window)) on Window_5m | project Window_5m, ClusterName, NodeName, LogicalServerName, AppName, physical_db_name, LogSpaceUsedGB, MaxLogSizeGB, LogUsedPercentage, log_hold_up_reason"
  }
```

**Store variables**:
- `PeakLogUsedPercentage` (highest value observed)
- `PeakLogUsedGB` (peak log space used)
- `MaxLogSizeGB` (max log size)
- `PrimaryLogHoldupReason` (most frequent holdup reason)

**Output to user**:
> ✅ **Log Space Analysis Complete**
> - **Peak Log Usage**: {PeakLogUsedPercentage}%
> - **Max Log Size**: {MaxLogSizeGB} GB
> - **Peak Used**: {PeakLogUsedGB} GB
> - **Primary Holdup Reason**: {PrimaryLogHoldupReason}

**Validation**: 
- If query returns no results:
  > 🚩 No log space data found for database in time window {StartTime} to {EndTime}. Verify database ID and time window are correct.

**MI-Specific Fallback**:
- `MonDmLogSpaceInfo` is **empty** for Managed Instance databases. If no results are returned and the database is MI, fall back to `MonFabricThrottle` for log space data.
- For MI, `MonFabricThrottle` uses the **logical_database_id** (not physical_database_id) as the `database_name` column. Use `logical_database_id` from get-db-info as the filter value.
- Use columns: `log_space_used_size_kb`, `max_log_size_kb`, `log_truncation_holdup`, `percent_throttle_open`.
- `MonDmExecRequests`, `MonDmExecSessions`, `MonDmExecConnections`, `MonDmRealTimeResourceStats` are also **empty** for MI — do not rely on these tables for MI troubleshooting.

### 2. Check for DirectoryQuotaNearFull

Execute query **LOG200** from [references/queries.md](references/queries.md) (Directory Quota Status).

**If results found**:
> 🚩 **DirectoryQuotaNearFull Issue Detected**
> - **Directory**: {target_directory}
> - **Size**: {size_gb} GB
> - **Detection Time**: {stale_folder_time}
> 
> **Recommended Action**: Transfer incident to **Azure SQL DB/SQL DB Perf : InterProcessRG/ResourceLimits** queue or refer to TSG PERFTS016 for directory quota resolution.

If this issue is detected, **stop further analysis** as mitigation requires different queue/approach.

### 3. Determine Mitigation Path Based on Holdup Reason

Based on `PrimaryLogHoldupReason` from Step 1, execute diagnostic queries and provide mitigation guidance:

#### ACTIVE_BACKUP_OR_RESTORE or LOG_BACKUP

**Diagnostic Steps**:
1. Check active backups using query **LOG300** (Active Backup Sessions)
2. Review backup start/end pairs for hung or failed backups

**Special Case - Hyperscale Reverse Migration**:
- If database is on Hyperscale with LOG_BACKUP holdup and reverse migration suspected:
  > 🚩 **Hyperscale Reverse Migration Detected**
  > 
  > **Recommended Action**: Transfer incident to **Hyperscale Migration** queue (Soc074). Migration may need to be canceled to release log.

**Mitigation Options**:
> **ACTIVE_BACKUP_OR_RESTORE Detected**
> 
> **Recommended Actions**:
> 1. If BACKUP_START without matching BACKUP_END: Investigate hung backup
> 2. If backup failures detected: Investigate error messages
> 3. Refer to: TSG BRDB0105 for detailed mitigation steps

#### REPLICATION

**Diagnostic Steps**:
1. Check replication feature using query **LOG400** (Replication Feature Status) via XTS adhocquerytobackendinstance view
2. Route to appropriate skill based on enabled feature:
   - **CDC**: Use **cdc-log-full** skill (TSG CDC0001)
   - **Synapse Link**: Use **synapse-link-log-full** skill (TSG SL0001)
   - **Fabric Mirroring**: Use **synapse-link-log-full** skill (TSG SL0001) — SL0001 Section 2.2 routes to autoreseed-db (TL0005) for REPLICATION holdup

**Mitigation**:
> **REPLICATION Issue Detected**
> - **Feature**: {CDC/Synapse Link/Fabric Mirroring}
> 
> **Recommended Actions**:
> - **For CDC**: Refer to TSG CDC0001 or use cdc-log-full skill
> - **For Synapse Link**: Refer to TSG SL0001 or use synapse-link-log-full skill
> - **For Fabric Mirroring**: Refer to TSG SL0001 or use synapse-link-log-full skill (routes to autoreseed-db for REPLICATION holdup)

#### AVAILABILITY_REPLICA

**Diagnostic Steps**:
1. First check if CDC is enabled using query **LOG400** (via XTS adhocquerytobackendinstance view)
2. If CDC enabled, follow CDC mitigation path (TSG CDC0001, "Case 4: Kill active Txn")
3. Check replica status using query **LOG500** (HA Replica Synchronization State)

**Common Scenarios**:

**Scenario 1: Backups on Secondary (Managed Instance)**
> **Recommended Action**: Refer to TSG "Managed Instance log full due to AVAILABILITY_REPLICA Backups on Secondary replica"

**Scenario 1a: Lagging Secondary via truncation_lsn**
If query **LOG500** shows all replicas SYNCHRONIZED/HEALTHY but log is still growing, compare `truncation_lsn` across replicas. The problematic replica will have a `truncation_lsn` much lower (older) than the primary and other secondaries. Mitigation: Kill the SQL Server process on the lagging replica.

**Scenario 2: Large Redo Queue**
If query **LOG500** shows redo queue >1GB:
> 🚩 **Large Redo Queue Detected**
> - **Secondary**: {secondary_node}
> - **Redo Queue**: {redo_queue_size_mb} MB
> - **Estimated Catch-up**: {estimated_time}
> 
> **Recommended Actions**:
> 1. Check secondary health and resource consumption
> 2. Verify network connectivity
> 3. Consider temporary workload throttling
> 4. Refer to: TSG "Log full due to AVAILABILITY_REPLICA - Large Redo Queue"

**Scenario 3: Down/Tombstoned Replica**
> 🚩 **Down/Tombstoned Replica Detected**
> - **Replica**: {replica_node}
> - **State**: {replica_state}
> 
> **Recommended Action**: Refer to TSG "Tombstoned target replica causing logfull on source database"

**Scenario 4: GeoDR**
Execute query **LOG520** (GeoDR Configuration)
> 🚩 **GeoDR Forwarder Issue**
> **Recommended Action**: Transfer to GeoDR queue or refer to TSG GEODR0003

**Scenario 5: Customer Write Workload Exceeding Redo Capacity**

This scenario detects when heavy customer write workload (e.g., ETL, bulk inserts, index rebuilds) generates transaction log faster than HA secondaries can replay via redo. The log cannot be truncated until all secondaries catch up, causing log growth.

**Diagnostic Steps** (run in parallel):
1. **Redo queue symmetry** — Execute query **LOG530** (Redo Queue Per Node). Compare `max(redo_queue_size)` across all secondary nodes in 5-minute bins. If ALL secondaries spike together (within same time window), the bottleneck is write volume on the primary, not a secondary-side issue.
2. **Redo rate stability** — From the same **LOG530** results, check `avg(redo_rate)`. If redo rate remains constant (~same value before, during, and after the spike), secondaries are healthy and processing at maximum sustained rate.
3. **Write throttle** — Execute query **LOG540** (Write Throttle Status). If `percent_throttle_open` drops below 100% during the spike, this is direct proof of heavy write throughput triggering the throttle.
4. **Backup per node** — Execute query **LOG550** (Backup Activity Per Node). If all backups ran exclusively on the primary node (zero on secondaries), backup-on-secondary is ruled out.
5. **Replica health** — Execute query **LOG560** (Secondary Replica Health). All secondaries must show `SYNCHRONIZED` / `HEALTHY` / `ONLINE` / `is_suspended=0` throughout the spike.

**Classification Criteria** — If ALL of the following are true:
- Redo queues are **symmetric** (all secondaries spike and recover in lockstep)
- Redo rate is **stable** (not degraded during spike)
- `percent_throttle_open` **dropped below 100%** during spike
- **No backup activity on secondary** nodes
- All replicas remained **SYNCHRONIZED / HEALTHY / ONLINE / not suspended**
- Log usage **declined after workload stopped** (self-recovery)

→ Classify as: **Customer Write Workload — not a service-side issue**

> ✅ **Customer Write Workload Detected**
> - **Pattern**: All {N} secondaries spiked in lockstep — redo queues rose and fell together
> - **Redo Rate**: Stable at ~{redo_rate} KB/s throughout (secondaries healthy)
> - **Write Throttle**: `percent_throttle_open` dropped to {min_throttle}% at peak
> - **Backup on Secondary**: None detected — all backups on primary
> - **Replica Health**: All SYNCHRONIZED / HEALTHY / ONLINE throughout
> - **Self-Mitigated**: Yes — log usage declined after workload completed

**Store variables**:
- `N` (number of secondary nodes)
- `redo_rate` (average redo rate observed)
- `min_throttle` (minimum throttle percentage observed)
>
> **Root Cause**: Customer write workload generated log faster than HA secondaries could redo, causing `AVAILABILITY_REPLICA` holdup.
>
> **Recommended Actions for Customer**:
> 1. Break large ETL/bulk operations into smaller batches to reduce log generation rate
> 2. Stagger concurrent write workloads — avoid overlapping heavy jobs
> 3. Monitor log usage during ETL windows via `sys.dm_db_log_space_usage`
> 4. Consider increasing max log size if approaching limits during peak write periods
> 5. For BC tier: be aware that redo throughput is the bottleneck — sustained writes exceeding ~130-140 KB/s per secondary will cause log accumulation
>
> **Classification**: Customer workload — not a service-side issue. No action required from Azure SQL engineering.

#### ACTIVE_TRANSACTION

**Diagnostic Steps**:
1. Check if CDC/Synapse Link/Fabric Mirroring enabled using query **LOG400** (via XTS adhocquerytobackendinstance view)
2. Check current log reuse wait using query **LOG600** (Log Reuse Wait Description) via XTS adhocquerytobackendinstance view
3. Check remaining log capacity using query **LOG610** (Log File Space Usage) via XTS adhocquerytobackendinstance view

**Mitigation**:
> **ACTIVE_TRANSACTION Detected**
> - **Transaction ID**: {transaction_id}
> - **Duration**: {transaction_duration}
> - **Session ID**: {session_id}
> 
> **Recommended Actions**:
> - **If CDC enabled**: Refer to TSG "CDC log full due to active transaction"
> - **If Synapse Link enabled**: Refer to TSG SL0001, section "Case3 Kill Active Transaction"
> - **If Shrink running**: Refer to TSG "Log near full due to shrink transaction"
> - **General**: Refer to TSG "LogFull Due to Active_Transaction"

#### CHECKPOINT or OLDEST_PAGE

**Mitigation**:
> **CHECKPOINT/OLDEST_PAGE Issue Detected**
> 
> **Recommended Action**: 
> 1. Take JIT access to physical database
> 2. Execute `CHECKPOINT` command
> 3. This should immediately release log space
> 
> **Note**: Only **one** manual checkpoint should be needed.

#### XTP_CHECKPOINT

**Diagnostic Steps**:
1. Refer to TSG HK0020 for XTP checkpoint investigation
2. Check for orphaned RBPEX pages via directory quota analysis (LOG200)

**Mitigation**:
> **XTP_CHECKPOINT Issue Detected**
> 
> **Recommended Action**: 
> - **If orphaned RBPEX detected**: Link repair item https://msdata.visualstudio.com/_workitems/edit/1851900
> - **General XTP issue**: Refer to TSG HK0020

## Post-Mitigation Verification

After applying mitigation, verify log space is recovering:

1. Re-run LOG100 (Triage query from Step 1) to confirm:
   - `LogUsedPercentage` is decreasing over time
   - `log_hold_up_reason` has changed from the original holdup reason

2. Use XTS view **adhocquerytobackendinstance** to verify current state:

```sql
SELECT name, log_reuse_wait_desc FROM sys.databases WHERE name = '{physical_database_id}'
```

```sql
SELECT name, CAST(FILEPROPERTY(name, 'SpaceUsed') AS bigint) * 8 / 1024. AS log_used_mb,
       CAST(max_size AS bigint) * 8 / 1024. AS max_log_size_mb
FROM sys.database_files WHERE type_desc = 'LOG'
```

3. Confirm:
   - `log_reuse_wait_desc` is no longer the original holdup reason
   - Log space used percentage is below 97%
   - Customer can execute write workloads

4. If mitigation unsuccessful, re-evaluate `log_hold_up_reason` — it may have changed to a different reason. Try the corresponding TSG for the new holdup reason.

## Escalation

If mitigation does not resolve the issue, escalate based on holdup reason:

| log_reuse_wait_desc | Escalate To |
|---|---|
| LOG_BACKUP or ACTIVE_BACKUP_OR_RESTORE | **Backup Restore Service** expert queue (SqlDbBRService@service.microsoft.com) |
| REPLICATION | **Change Data Capture** queue |
| AVAILABILITY_REPLICA (local secondary) | **SQL DB Availability** queue |
| AVAILABILITY_REPLICA (GeoDR secondary) | **GeoDR (Failover Groups, AutoDR, DB Copy, Read Scale)** queue |
| AVAILABILITY_REPLICA (Hyperscale) | **Socrates Data Plane (Hyperscale)** queue |
| XTP_CHECKPOINT | **Hekaton Storage** queue |
| Other / Unknown | **Backup Restore Service** expert queue |

## XTS View Checks

### Check CDC/Synapse Link Status

Use XTS view **adhocquerytobackendinstance**:
```sql
SELECT name, is_cdc_enabled, is_change_feed_enabled as is_synapse_link_enabled 
FROM sys.databases 
WHERE name = '<physical_database_id>'
```

### Check Current Log Reuse Wait Description

Use XTS view **adhocquerytobackendinstance**:
```sql
SELECT name, log_reuse_wait_desc 
FROM sys.databases 
WHERE name = '<physical_database_id>'
```

**Note**: For Hyperscale databases, when using mirroring.xts in Step 4, select the partition with `fabric_service_uri` that starts with `fabric:/Worker.Vldb.Compute/`.

## Summary Output Format

After completing analysis, provide summary:

> ## 🔍 **Log Full/Near Full Analysis Summary**
> 
> **Database Information:**
> - Physical Database ID: {PhysicalDatabaseID}
> - Logical Server: {LogicalServerName}
> - Logical Database: {LogicalDatabaseName}
> - Cluster/Node: {ClusterName}/{NodeName}
> 
> **Log Space Analysis:**
> - Peak Usage: {PeakLogUsedPercentage}%
> - Max Log Size: {MaxLogSizeGB} GB
> - Peak Used: {PeakLogUsedGB} GB
> - Analysis Window: {StartTime} to {EndTime}
> 
> **Root Cause:**
> - Primary Holdup Reason: {PrimaryLogHoldupReason}
> - {Additional diagnostic findings}
> 
> **Recommended Actions:**
> {Numbered list of specific mitigation steps}
> 
> **Related TSGs:**
> {List of relevant TSG links}

## Related References

- [references/queries.md](references/queries.md) — Kusto query definitions (LOG100–LOG610)
- [references/terms.md](references/terms.md) — Terminology and concepts
- [references/principles.md](references/principles.md) — Debug decision tree and severity assessment
- [references/report.md](references/report.md) — Output format templates
- [references/prep/sources.md](references/prep/sources.md) — TSG source URLs
