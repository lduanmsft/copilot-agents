# HADR_SYNC_COMMIT Investigation Queries

This file contains Kusto queries for investigating high HADR_SYNC_COMMIT wait times in Azure SQL Database.

## Query Parameter Placeholders

Replace these placeholders with actual values:
- `{StartTime}`: Start timestamp (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp (e.g., `2026-01-01 03:00:00`)
- `{LogicalServerName}`: Logical server name
- `{LogicalDatabaseName}`: Logical database name
- `{AppName}`: From get-db-info skill (sql_instance_name)

> **Note on timestamp columns**: `MonDmDbHadrReplicaStates` exposes two timestamp columns.
> Queries in this file use `TIMESTAMP` (coarser, partition-aligned) or `PreciseTimeStamp` (higher resolution) depending on the query goal. Both are valid — do not substitute one for the other.

---

## HSC050 - HADR_SYNC_COMMIT Wait Statistics

Query `MonDmOsWaitStats` to confirm that `HADR_SYNC_COMMIT` waits were actually elevated during the incident window.

**Purpose**: Directly validate the root symptom before proceeding to queue-based analysis. If waits are not elevated, the incident is unlikely to be caused by synchronous commit latency.

```kql
MonDmOsWaitStats
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ '{AppName}'
| where wait_type == 'HADR_SYNC_COMMIT'
| summarize
    AvgWaitMs = avg(wait_time_ms),
    MaxWaitMs = max(wait_time_ms),
    TotalWaits = sum(waiting_tasks_count)
    by bin(TIMESTAMP, 1m)
| order by TIMESTAMP asc
```

---

## HSC100 - HADR Replica States Timeline

Query MonDmDbHadrReplicaStates to get an overview of replica health, sync state, and queue sizes over time.

**Purpose**: Identify periods of poor synchronization health, large redo/log send queues, or slow sync rates.

```kql
MonDmDbHadrReplicaStates
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| project
    TIMESTAMP,
    NodeName,
    is_primary_replica,
    is_local,
    redo_queue_size,
    redo_rate,
    log_send_queue_size,
    log_send_rate,
    synchronization_health_desc,
    synchronization_state_desc,
    is_commit_participant,
    internal_state_desc,
    is_forwarder,
    AppName
| order by TIMESTAMP asc
```

---

## HSC110 - Primary Node Timeline

Query to identify primary node changes and role transitions during the incident window.

**Purpose**: Establish timeline of primary replica ownership and detect unexpected role changes.

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where internal_state_desc in ('GLOBAL_PRIMARY', 'PRIMARY', 'FORWARDER')
| where is_local == 1
| summarize dcount(logical_database_name) by bin(PreciseTimeStamp, 1m), ClusterName, NodeName, internal_state_desc
| order by PreciseTimeStamp asc
```

---

## HSC120 - Synchronization Health Summary

Query to summarize synchronization health status per node.

**Purpose**: Quickly identify nodes with unhealthy or degraded synchronization.

```kql
MonDmDbHadrReplicaStates
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| summarize 
    HealthyCount = countif(synchronization_health_desc == 'HEALTHY'),
    UnhealthyCount = countif(synchronization_health_desc != 'HEALTHY'),
    AvgRedoQueueSize = avg(redo_queue_size),
    MaxRedoQueueSize = max(redo_queue_size),
    AvgLogSendQueueSize = avg(log_send_queue_size),
    MaxLogSendQueueSize = max(log_send_queue_size)
    by NodeName, internal_state_desc
| order by UnhealthyCount desc
```

---

## HSC130 - Redo Queue and Rate Analysis

Query to analyze redo queue behavior and identify bottlenecks on secondary replicas.

**Purpose**: Detect if secondary replicas are falling behind due to slow redo.

```kql
MonDmDbHadrReplicaStates
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where is_primary_replica == false
| summarize
    AvgRedoQueue = avg(redo_queue_size),
    MaxRedoQueue = max(redo_queue_size),
    AvgRedoRate = avg(redo_rate),
    MinRedoRate = min(redo_rate),
    SampleCount = count()
    by bin(TIMESTAMP, 1m), NodeName
| order by TIMESTAMP asc, NodeName asc
```

---

## HSC140 - Log Send Queue Analysis

Query to analyze log send queue on primary replica.

**Purpose**: Detect if primary is backing up log send queue due to slow network or secondary issues.

> **Note**: On General Purpose tier databases, `log_send_queue_size` and `log_send_rate` may return `-1` (not available). This is expected behavior — skip this query's interpretation if all values are `-1`.

```kql
MonDmDbHadrReplicaStates
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where is_primary_replica == true
| summarize
    AvgLogSendQueue = avg(log_send_queue_size),
    MaxLogSendQueue = max(log_send_queue_size),
    AvgLogSendRate = avg(log_send_rate),
    MinLogSendRate = min(log_send_rate)
    by bin(TIMESTAMP, 15m), NodeName
| order by TIMESTAMP asc
```

---

## HSC300 - Database Recovery State Check

Query to check if database is in recovery or reverting state.

**Purpose**: Identify if synchronization issues are due to database recovery.

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where database_state_desc == 'RECOVERING' or synchronization_state_desc == 'REVERTING'
| project PreciseTimeStamp, NodeName, synchronization_state_desc, database_state_desc, internal_state_desc
| order by PreciseTimeStamp asc
| take 1000
```

---

## HSC400 - XEvent System Health Data (if available)

Query MonSQLSystemHealth for extended event data related to HADR.

**Purpose**: Access extended event ring buffer data for detailed HADR diagnostics.

```kql
MonSQLSystemHealth
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ '{AppName}'
| where message has 'hadr' or message has 'log_flush'
| project TIMESTAMP, process_id, NodeName, message
| order by TIMESTAMP asc
| take 500
```

---


## HSC160 - Quorum Catchup Detection

Query to detect if a planned failover occurred to a lagging secondary, causing Quorum Catchup and `HADR_SYNC_COMMIT` spikes.

**Purpose**: Identify role transitions where the new primary's secondaries show large redo/log send queues or `SYNCHRONIZING` state, indicating Quorum Catchup. This is associated with known issue [BUG 3546900](https://dev.azure.com/msdata/Database%20Systems/_workitems/edit/3546900).

**Flag 🚩 if:**
- A node transitions to `PRIMARY` or `GLOBAL_PRIMARY` while other nodes show `synchronization_state_desc` = `SYNCHRONIZING` with growing `redo_queue_size`
- The `SYNCHRONIZING` state persists for an extended period after the role transition
- `HADR_SYNC_COMMIT` waits (from HSC050) spike immediately after the role transition timestamp

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where is_local == 1
| project
    PreciseTimeStamp,
    NodeName,
    internal_state_desc,
    is_primary_replica,
    synchronization_state_desc,
    synchronization_health_desc,
    redo_queue_size,
    log_send_queue_size,
    is_commit_participant
| order by PreciseTimeStamp asc, NodeName asc
```

---

## HSC170 - Identify Lagging Catchup Replica (during Quorum Catchup)

Query to rank secondary replicas by redo/log-send backlog and synchronization state during/after a primary role transition. Use this to identify the specific replica(s) that are lagging and gating the quorum commit set during Quorum Catchup.

**Purpose**: When **HSC160** confirms that a Quorum Catchup pattern exists, this query isolates **which** secondary is the most-behind replica so the RCA can name the exact node whose catchup is blocking commit progress. Pair this with **HSC110** (to identify the role-transition timestamp) and **HSC160** (to confirm the catchup pattern).

**How to interpret:**
- `MaxRedoQueue_KB` and `MaxLogSendQueue_KB` rank replicas by backlog magnitude
- `SynchronizingSamples` counts how many telemetry rows show the replica still in `SYNCHRONIZING` (not `SYNCHRONIZED`) state during the window
- `IsCommitParticipantSamples` indicates whether the replica was part of the commit-participating set during the window — a lagging non-participant cannot block commits
- `LaggingScore` is a simple composite — the replica with the highest score is the most likely catchup-gating replica

**Flag 🚩 if:**
- A non-primary replica shows `MaxRedoQueue_KB` orders of magnitude larger than other secondaries
- That same replica shows `SynchronizingSamples` covering most of the post-transition window
- That replica was `is_commit_participant = true` during the spike (i.e., it was actually required for quorum)

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where is_local == 1
| where is_primary_replica == false
| summarize
    MaxRedoQueue_KB = max(redo_queue_size),
    AvgRedoQueue_KB = avg(redo_queue_size),
    MinRedoRate = min(redo_rate),
    MaxLogSendQueue_KB = max(log_send_queue_size),
    AvgLogSendQueue_KB = avg(log_send_queue_size),
    SynchronizingSamples = countif(synchronization_state_desc == 'SYNCHRONIZING'),
    NotSynchronizedSamples = countif(synchronization_state_desc != 'SYNCHRONIZED'),
    IsCommitParticipantSamples = countif(is_commit_participant == true),
    TotalSamples = count(),
    FirstSeen = min(PreciseTimeStamp),
    LastSeen = max(PreciseTimeStamp)
    by NodeName, internal_state_desc
| extend LaggingScore = MaxRedoQueue_KB + MaxLogSendQueue_KB + (SynchronizingSamples * 1000)
| order by LaggingScore desc
```

---

## HSC180 - MonFabricApi: MustCatchup Replica Detection

Query `MonFabricApi` to identify if a MustCatchup replica was designated during a quorum catchup, which replicas were tagged, and whether quorum catchup succeeded or timed out.

**Purpose**: Directly confirm the MustCatchup commit manager scenario by examining the fabric API telemetry. The `replica_infos_mustcatchup` XML column contains the replica(s) flagged with `mustCatchup="true"` by Service Fabric. Cross-reference with **HSC110** (role transitions) and **HSC160** (redo queue growth) to build the full RCA.

**Key XEvents in MonFabricApi**:
- `hadr_fabric_api_replicator_update_catchup_replica_set_configuration` — contains `must_catchup_replica_count` and `replica_infos_mustcatchup` XML
- `hadr_fabric_api_replicator_begin_wait_for_quorum_catchup` — start of quorum catchup with `must_catch_up_replica_count` and `catch_up_mode`
- `hadr_fabric_api_replicator_end_wait_for_quorum_catchup` — end of quorum catchup with success/failure `result`

**Flag 🚩 if:**
- `must_catchup_replica_count` > 0 in the `update_catchup_replica_set_configuration` event
- The `replica_infos_mustcatchup` XML shows a replica with `mustCatchup="1"`
- The `begin_wait_for_quorum_catchup` event has `catch_up_mode` = 1 (WRITE_QUORUM) with `must_catch_up_replica_count` > 0
- The `end_wait_for_quorum_catchup` event shows a failed result or the duration between begin/end is excessively long

```kql
// Part 1: Detect MustCatchup replica set configuration updates
MonFabricApi
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where physical_database_id =~ '{physical_database_id}'
| where event in (
    'hadr_fabric_api_replicator_update_catchup_replica_set_configuration',
    'hadr_fabric_api_replicator_begin_wait_for_quorum_catchup',
    'hadr_fabric_api_replicator_end_wait_for_quorum_catchup',
    'hadr_fabric_api_replicator_wait_for_quorum_catchup_all_timeout'
  )
| project
    TIMESTAMP,
    event,
    fabric_replica_id,
    must_catchup_replica_count,
    must_catch_up_replica_count,
    catch_up_mode,
    replica_count_current,
    write_quorum_current,
    result,
    result_desc,
    replica_infos_mustcatchup,
    replica_infos_current,
    NodeName
| order by TIMESTAMP asc
```

```kql
// Part 2: Parse the MustCatchup replica XML to identify the specific replica(s)
// Use this after Part 1 confirms must_catchup_replica_count > 0
MonFabricApi
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where physical_database_id =~ '{physical_database_id}'
| where event == 'hadr_fabric_api_replicator_update_catchup_replica_set_configuration'
| where must_catchup_replica_count > 0
| project TIMESTAMP, NodeName, must_catchup_replica_count,
    write_quorum_current, replica_count_current,
    replica_infos_mustcatchup, replica_infos_current
| order by TIMESTAMP asc
```

> **Note**: The `replica_infos_mustcatchup` column contains CDATA-wrapped XML in the format:
> ```xml
> <![CDATA[<replica fabricId="134197673185021991" role="4" roleDesc="REPLICA_ROLE_ACTIVE_SECONDARY"
>          status="2" statusDesc="FABRIC_REPLICA_STATUS_UP" replicatorAddress="..."
>          currentProgress="-1" catchUpCapability="-1" mustCatchup="1"/>]]>
> ```
> The `mustCatchup="1"` attribute (boolean integer: `1` = true, `0` = false) identifies the replica(s) Service Fabric designated as must-catchup targets.
> The `currentProgress` and `catchUpCapability` fields indicate how far behind the replica was at the time of the configuration update (value `-1` means not yet known).

---

## References

- [knowledge.md](./knowledge.md) - Technical background on HADR_SYNC_COMMIT
- [SKILL.md](../SKILL.md) - Investigation workflow
