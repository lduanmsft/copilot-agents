# Kusto Queries for Log Full/Near Full Analysis

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC
- `{EndTime}`: End timestamp in UTC

**Resource identifiers:**
- `{physical_database_id}`: Physical database ID (GUID)
- `{LogicalServerName}`: Logical server name
- `{LogicalDatabaseName}`: Logical database name

**Service Fabric identifiers:**
- `{ClusterName}`: Service Fabric cluster name
- `{AppName}`: Application name (SQL instance name)
- `{NodeName}`: Fabric node name

---

## LOG100: Historical Log Space Info

**Purpose**: Track log space usage, max log size, and log holdup reasons over time window.

**What to look for**:
- LogUsedPercentage trending upward or sustained >70%
- Primary log_hold_up_reason pattern (most frequent value)
- Sudden jumps in LogSpaceUsedGB

```kql
let _physical_DBID = '{physical_database_id}';
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
let window = 5m;
MonDmLogSpaceInfo
| where TIMESTAMP between (_startTime .. _endTime)
| extend physical_db_name = substring(toupper(instance_name), 0, 36)
| where physical_db_name =~ _physical_DBID
| project TIMESTAMP, ClusterName, NodeName, logical_server_name, AppName, physical_db_name, counter_name, cntr_value
| order by TIMESTAMP asc, counter_name desc
| extend LogSpaceUsed = prev(cntr_value)
| where counter_name contains "Log File(s) Size (KB)"
| extend LogSpaceUsedGB = round(LogSpaceUsed/(1024.0*1024), 1), MaxLogSizeGB = round(cntr_value/(1024.0*1024), 1)
| extend LogUsedPercentage = round(LogSpaceUsedGB*100/MaxLogSizeGB, 1)
| summarize arg_max(TIMESTAMP, ClusterName, NodeName, logical_server_name, AppName, physical_db_name, LogSpaceUsedGB, MaxLogSizeGB, LogUsedPercentage) by Window_5m = bin(TIMESTAMP, window)
| join kind=leftouter (
    MonFabricThrottle
    | where TIMESTAMP between (_startTime .. _endTime)
    | where database_name =~ _physical_DBID
    | extend log_hold_up_reason = case(
        log_truncation_holdup == 'AvailabilityReplica', 'AVAILABILITY_REPLICA',
        log_truncation_holdup == 'LogBackup', 'LOG_BACKUP',
        log_truncation_holdup == 'ActiveTransaction', 'ACTIVE_TRANSACTION',
        log_truncation_holdup == 'ReplicationXact', 'REPLICATION',
        log_truncation_holdup == 'ActiveBackup', 'ACTIVE_BACKUP_OR_RESTORE',
        log_truncation_holdup)
    | summarize arg_max(TIMESTAMP, ClusterName, NodeName, LogicalServerName, AppName, log_hold_up_reason) by Window_5m = bin(TIMESTAMP, window)
) on Window_5m
| project Window_5m, ClusterName, NodeName, logical_server_name = coalesce(LogicalServerName, logical_server_name), AppName, physical_db_name, LogSpaceUsedGB, MaxLogSizeGB, LogUsedPercentage, log_hold_up_reason
```

## LOG200: Directory Quota Status

**Purpose**: Check for directory quota issues and stale directories (>100GB).

**What to look for**:
- Stale directories with size_gb > 100
- Orphaned RBPEX pages filling disk
- Match stale directories to application names

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
let _cluster = '{ClusterName}';
let _node = '{NodeName}';
MonRgManager
| where TIMESTAMP between (_startTime .. _endTime)
| where ClusterName =~ _cluster
| where NodeName =~ _node
| where event == "stale_directory"
| project originalEventTimestamp, deployment_status, size_gb = size/1024/1024/1024.0, target_directory, consecutive_detection
| where size_gb > 100
| extend target_directory = strcat(target_directory, "\\work\\data")
| summarize size_gb = max(size_gb), max(originalEventTimestamp), max(consecutive_detection) by target_directory
| join kind=inner (
    MonRgLoad
    | where TIMESTAMP between (_startTime .. _endTime)
    | where ClusterName =~ _cluster
    | where event == "directory_quota_report_load"
    | where NodeName =~ _node and top_monitored_directory == "data"
    | summarize by target_directory, application_name
) on target_directory
| project stale_folder_time = max_originalEventTimestamp, size_gb, target_directory, application_name, max_consecutive_detection
| join kind=inner (
    MonRgManager
    | where TIMESTAMP between (_startTime .. _endTime)
    | where ClusterName =~ _cluster
    | where NodeName =~ _node
    | where event contains "deregister" and code_package_name == "Code"
    | summarize deg_time = max(originalEventTimestamp) by application_name
) on application_name
| project-away application_name1
```

## LOG300: Active Backup Sessions

**Purpose**: Identify currently running backup operations that may be holding log truncation.

**Reference TSG**: BRDB0105 - Log Full with ACTIVE_BACKUP_OR_RESTORE

```kql
MonBackup
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ '{AppName}'
| where event_type in ('BACKUP_START', 'BACKUP_END')
| where logical_database_name =~ '{LogicalDatabaseName}'
| project originalEventTimestamp, event, process_id, event_type, logical_server_name, backup_type
| top 1000 by originalEventTimestamp desc
```

## LOG400: Replication Feature Status

**Purpose**: Determine which replication features are enabled (CDC, Synapse Link, Fabric Mirroring).

**Method**: Execute via XTS view `adhocquerytobackendinstance.xts` — select logical server and database (not master), then run:

```sql
SELECT name, is_cdc_enabled, is_change_feed_enabled AS is_synapse_link_enabled
FROM sys.databases
WHERE name = '{physical_database_id}'
```

## LOG500: HA Replica Synchronization State

**Purpose**: Check HA replica synchronization state and identify problematic replicas holding up truncation.

**What to look for**:
- `truncation_lsn` values that are significantly behind other replicas (key clue for finding the culprit)
- Large `redo_queue_size` on secondaries
- Replicas with unhealthy `synchronization_health_desc`

```kql
MonDmDbHadrReplicaStates
| where TIMESTAMP between (datetime({StartTime})-1h..datetime({EndTime})+1h)
| where AppTypeName !contains 'storage'
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where is_local == 1
| project TIMESTAMP, ClusterName, NodeName, AppName, synchronization_state_desc, synchronization_health_desc, database_state_desc, internal_state_desc, last_commit_lsn, last_hardened_lsn, last_redone_lsn, truncation_lsn, redo_queue_size
| order by TIMESTAMP asc, NodeName asc
```

## LOG520: GeoDR Configuration

**Purpose**: Check if database has GeoDR configuration with forwarder replica.

**Method**: Open `Database Replicas.xts` view, enter the physical_database_id in Step 1, click on partition_id in Step 2, select Primary replica in Step 4 and check if the database has a GeoDR secondary replica. Look for a row in the Hadron DMV tab with `internal_state` = "Forwarder".

## LOG530: Redo Queue Per Node (5-min granularity)

**Purpose**: Check redo queue size and redo rate per secondary node at 5-minute intervals. Used to detect symmetric vs asymmetric redo queue growth (Scenario 5: Customer Write Workload).

**Uses table**: MonDmDbHadrReplicaStates

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}'
    and logical_database_name =~ '{LogicalDatabaseId}'
| where is_primary_replica == 0
| summarize avg(redo_queue_size), max(redo_queue_size),
    avg(redo_rate),
    avg(log_send_queue_size), max(log_send_queue_size)
  by NodeName, bin(PreciseTimeStamp, 5m)
| order by PreciseTimeStamp asc, NodeName asc
```

**Key Output Columns**:
- NodeName, PreciseTimeStamp, avg/max redo_queue_size, avg redo_rate, avg/max log_send_queue_size

**Interpretation**:
- If ALL secondaries spike and recover in lockstep → write workload on primary
- If ONE secondary has disproportionately higher redo queue → secondary-side issue
- Stable redo_rate before/during/after spike → secondaries healthy, workload is the bottleneck

**Note (MI)**: For Managed Instance, `logical_database_name` is the **logical_database_id** (GUID), not the user-facing database name.

## LOG540: Write Throttle Status

**Purpose**: Check `percent_throttle_open` to detect write throttling caused by heavy log generation. A drop below 100% proves the system is actively slowing customer writes.

**Uses table**: MonFabricThrottle

```kql
MonFabricThrottle
| where TIMESTAMP between (datetime({StartTime}) .. datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}'
| where database_name =~ '{DatabaseNameFilter}'
| project TIMESTAMP, NodeName, percent_throttle_open, log_space_used_size_kb, max_log_size_kb, log_truncation_holdup
| order by TIMESTAMP asc
```

**Key Output Columns**:
- percent_throttle_open (100 = no throttle, 0 = writes fully blocked), log_space_used_size_kb, log_truncation_holdup

**Interpretation**:
- `percent_throttle_open = 100` → no restriction, normal writes
- `percent_throttle_open < 100` → system is throttling writes due to log pressure
- `percent_throttle_open` drops correlating with redo queue spikes → confirms heavy write workload

**Note (MI)**: For Managed Instance, use `logical_database_id` as `{DatabaseNameFilter}`. For SQL DB, use `physical_database_id`.

## LOG550: Backup Activity Per Node

**Purpose**: Check if any backup operations ran on secondary nodes. Used to rule out backup-on-secondary as a cause of AVAILABILITY_REPLICA holdup.

**Uses table**: MonBackup

```kql
MonBackup
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where AppName =~ '{AppName}'
| where event_type in ('BACKUP_START','BACKUP_END')
| where logical_database_name =~ '{LogicalDatabaseId}'
| summarize backup_count=count(),
    backup_types=make_set(backup_type),
    min_time=min(originalEventTimestamp),
    max_time=max(originalEventTimestamp)
  by NodeName
| order by backup_count desc
```

**Key Output Columns**:
- NodeName, backup_count, backup_types

**Interpretation**:
- If all backups are on a single node (primary) → backup-on-secondary ruled out
- If backups appear on secondary nodes → backup-on-secondary may be contributing to redo lag

## LOG560: Secondary Replica Health

**Purpose**: Check health state of all secondary replicas during the incident window. Used to confirm secondaries were healthy (not down, suspended, or unhealthy) throughout the spike.

**Uses table**: MonDmDbHadrReplicaStates

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}'
    and logical_database_name =~ '{LogicalDatabaseId}'
| where is_primary_replica == 0
| summarize count(),
    make_set(synchronization_state_desc),
    make_set(synchronization_health_desc),
    make_set(database_state_desc),
    make_set(is_suspended),
    avg(redo_queue_size), max(redo_queue_size),
    avg(redo_rate),
    avg(log_send_queue_size), max(log_send_queue_size),
    avg(secondary_lag_seconds), max(secondary_lag_seconds)
  by NodeName, bin(PreciseTimeStamp, 1h)
| order by PreciseTimeStamp asc, NodeName asc
```

**Key Output Columns**:
- synchronization_state_desc (should be SYNCHRONIZED), synchronization_health_desc (should be HEALTHY), database_state_desc (should be ONLINE), is_suspended (should be 0)

**Interpretation**:
- All `SYNCHRONIZED` / `HEALTHY` / `ONLINE` / `is_suspended=0` → secondaries healthy, not the cause
- Any `NOT SYNCHRONIZING` / `NOT_HEALTHY` / `is_suspended=1` → secondary-side issue, investigate further
- Any `SYNCHRONIZING` → secondary catching up, may be recovering from a problem

**Note (MI)**: For Managed Instance, `logical_database_name` is the **logical_database_id** (GUID). The `database_state_desc` for the primary node may show as empty string (`""`) instead of `ONLINE` — this is normal.

## LOG600: Log Reuse Wait Description

**Purpose**: Check current log_reuse_wait_desc directly from the database.

**Method**: Execute via XTS view `adhocquerytobackendinstance.xts`:

```sql
SELECT name, log_reuse_wait_desc
FROM sys.databases
WHERE name = '{physical_database_id}'
```

## LOG610: Log File Space Usage

**Purpose**: Check current log file space usage directly from the database.

**Method**: Execute via XTS view `adhocquerytobackendinstance.xts`:

```sql
SELECT name,
       CAST(FILEPROPERTY(name, 'SpaceUsed') AS bigint) * 8 / 1024. AS log_used_mb,
       CAST(max_size AS bigint) * 8 / 1024. AS max_log_size_mb
FROM sys.database_files
WHERE type_desc = 'LOG'
```

## Notes

- All Kusto queries should be executed via mcp_azure_mcp_kusto tool using the cluster URI and database from execute-kusto-query skill
- XTS view queries require direct SQL access to backend instance via `adhocquerytobackendinstance.xts`
- Timespan format: Use `4h + 30m` for complex durations, or `1h`, `90m`, `5400s` for single units
- Source TSG: BRDB0156 - Log Near Full (ADO Wiki: `/BackupRestore/BRDB0156 Log near full` in TSG-SQL-DB-DataIntegration)
