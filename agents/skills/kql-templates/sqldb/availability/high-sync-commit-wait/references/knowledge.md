# HADR_SYNC_COMMIT Wait Type - Technical Knowledge

## Applicability

> **⚠️ IMPORTANT — Service Tier Prerequisite**
>
> `HADR_SYNC_COMMIT` waits are only possible on databases that use **synchronous replication**, which requires at least one synchronous secondary replica. This is only present in:
>
> | Service Tier | Synchronous Replicas | This Skill Applies? |
> |---|---|---|
> | **Business Critical (BC)** | Yes — always | ✅ Yes |
> | **Premium** | Yes — always | ✅ Yes |
> | **General Purpose (GP)** | No | ❌ No |
> | **Hyperscale** | No | ❌ No |
> | **Standard / Basic** | No | ❌ No |
>
> If the database SLO is **General Purpose or Hyperscale**, this skill does **not apply**. Dismiss it and investigate other wait types or availability mechanisms.

## Overview

The `HADR_SYNC_COMMIT` wait type occurs when the primary replica is waiting for the **quorum commit set** of synchronous secondary replicas to acknowledge that they have hardened the transaction log. This wait is a normal part of synchronous-commit availability groups but can indicate a performance or quorum-formation issue when wait times are excessive.

> **⚠️ Quorum Commit Model in Azure SQL DB (XDB) — BC / Premium**
>
> Azure SQL DB BC/Premium uses Service Fabric replica set sizing:
> - `TargetReplicaSetSize` (TRSS) = **4** — normal steady-state replica count
> - `MinReplicaSetSize` (MRSS) = **3** — Service Fabric will not allow the active view to drop below this
>
> Commits require acknowledgment from a **majority quorum** of the replicas in the active view (NOT acknowledgment from every replica):
> - With 4 replicas in view → majority = **3 of 4** must harden
> - With 3 replicas in view (post-failover or transient loss) → majority = **2 of 3** must harden
>
> **Implication**: A single lagging or down replica should **not** by itself cause `HADR_SYNC_COMMIT` waits, because the remaining 3-of-4 (or 2-of-3) replicas can still satisfy the quorum. `HADR_SYNC_COMMIT` waits in XDB therefore indicate that the **quorum commit set itself is blocked** — for example, two or more secondaries are slow or down, the commit-participating set has been reduced, or the new primary is in `must_catchup` after a failover.
>
> See [Service Fabric replica set size configuration](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-best-practices-replica-set-size-configuration) for background.

## HADRON Commit Manager Architecture (Engine Internals)

> **ℹ️ Internal context for RCA engineers**: This section documents the SQL Server engine internals that produce the `HADR_SYNC_COMMIT` wait. Understanding the commit manager architecture helps diagnose *why* commits stall, especially during reconfigurations and planned failovers.

### The Four Commit Managers

SQL Server's HADR subsystem (`HaDrCommitMgr` class in `hadrdbmgrpartner.h`) maintains **up to 4 commit manager instances** simultaneously. Each commit manager independently tracks a quorum of replicas and enforces its own harden policy. A transaction must satisfy **all active** commit managers before the commit is acknowledged.

| Index | Internal Name | Display Name | Purpose |
|-------|---------------|-------------|---------|
| 0 | `MainCommitMgr` | Main | **Current write quorum** — the active replica set from the current Service Fabric configuration. Handles steady-state synchronous commits. |
| 1 | `AlternateCommitMgr` | Alternate | **Previous write quorum** — replicas from the previous configuration. Active during reconfigurations to ensure both the old and new quorum sets are satisfied. |
| 2 | `GeoDrCommitMgr` | GeoDR | **Geo-replication** — for geographical disaster recovery. Always requires exactly 1 replica acknowledgment (fixed quorum of 1). |
| 3 | `MustCatchupCommmitMgr` | MustCatchup | **Must-Catchup** — activated during **planned failovers** when Service Fabric sets the `MustCatchup` flag on a replica. Ensures the designated replica catches up fully before the role swap completes. **This is the commit manager that causes stalls in the BUG 3546900 scenario.** |

Each commit manager tracks:
- **`m_quorumCommitCount`**: minimum number of replicas that must harden for quorum
- **`m_syncPartnerCount`**: count of synchronous partners in this commit set
- **`m_HardenedBlockSequence`**: the quorum-hardened log block position (advances as replicas acknowledge)

### Harden Policies

Each commit manager has exactly one of these policies at any time:

| Policy | Behavior | When Set |
|--------|----------|----------|
| `DoNothing` | Commit returns immediately — no remote harden wait | Async mode, DB suspended, or no sync partners |
| `Delay` | Brief sleep then return (catch-up throttling) | Partner is synchronizing but not yet close enough to switch to wait |
| `WaitForHarden` | **Block the committing thread** in a loop waiting for remote harden acknowledgment. **This is where `HADR_SYNC_COMMIT` waits appear.** | Synchronous commit mode; partner is synchronized or close to it |
| `KillAll` | Kill the thread — abort all pending commits | Lease expired, aborting, or replica is no longer primary |

### Per-Partner Policy Progression

Each secondary replica partner has its own `DbMgrPartnerCommitPolicy` that tracks synchronization state and independently progresses through policies:

```
DoNothing → Delay → WaitForHarden
```

The transition from `Delay` to `WaitForHarden` happens when the partner's hardened LSN is within a threshold (`x_SwitchToWaitBytes`) of the primary's flushed log. This transition is driven by `AdvanceHardenPolicy()`.

### Service Fabric ↔ Engine Quorum Set Mapping

Service Fabric communicates replica quorum assignments through `CFabricReplicaConfiguration`. The `MustCatchup` flag is read from `FABRIC_REPLICA_INFORMATION_EX1.MustCatchup` in the fabric configuration payload.

| Service Fabric Enum | Engine Bitmask | Commit Managers Involved |
|---------------------|----------------|--------------------------|
| `FABRIC_REPLICA_QUORUM_SET_CURRENT` | `COMMIT_QUORUM_SET_MAIN` | Main only |
| `FABRIC_REPLICA_QUORUM_SET_PREVIOUS` | `COMMIT_QUORUM_SET_ALTERNATE` | Alternate only |
| `FABRIC_REPLICA_QUORUM_SET_ALL` | `COMMIT_QUORUM_SET_LOCAL_ALL` | Main + Alternate |
| `FABRIC_REPLICA_QUORUM_SET_MUSTCATCH_CURRENT` | `COMMIT_QUORUM_SET_MUSTCATCH_MAIN` | Main + MustCatchup |
| `FABRIC_REPLICA_QUORUM_SET_MUSTCATCH_ALL` | `COMMIT_QUORUM_SET_MUSTCATCH_LOCAL_ALL` | Main + Alternate + MustCatchup |

### Planned Failover: MustCatchup Commit Manager Flow

During a planned failover, Service Fabric calls `WaitForQuorumCatchUp()`. The flow has two phases:

1. **Phase 1 (write status GRANTED)**: Optional pre-wait phase. The engine may call `WaitForFirstPhaseCatchup()` to let secondaries catch up while the database is still writable. The MustCatchup commit manager is activated but the `m_fWaitForMustCatchup` flag may be deferred.

2. **Phase 2 (write status NOT GRANTED)**: Write barrier is set — no new writes accepted. `WaitForQuorumCatchUpInternal()` iterates over all active commit managers. For the MustCatchup commit manager specifically, it calls `UpdateSingleCommitManagerForFullQuorum(MustCatchupCommmitMgr)` which requires **all** MustCatchup-tagged replicas to harden up to the end-of-flushed-log. The engine then waits on `m_HardenedBlockSequence.WaitGreaterThan()` with wait type `PWAIT_HADR_SYNC_COMMIT` until the quorum is satisfied or a timeout with no progress occurs.

**The stall scenario (BUG 3546900)**: If PLB selects a lagging replica as the new primary and that replica is tagged with `MustCatchup`, the MustCatchup commit manager blocks all synchronous commits until the lagging replica hardens all log up to end-of-flushed-log. If the replica is significantly behind, this creates a prolonged stall visible as elevated `HADR_SYNC_COMMIT` waits.

### XEvents for Commit Manager Diagnosis

The following XEvents are emitted by the engine and are captured in Kusto telemetry tables (primarily `MonFabricApi`):

| XEvent Name | Description | Key Columns |
|---|---|---|
| `hadr_fabric_api_replicator_update_catchup_replica_set_configuration` | Fires when Service Fabric sends a catchup replica set configuration update | `must_catchup_replica_count`, `replica_infos_mustcatchup` (XML), `replica_infos_current` (XML), `write_quorum_current` |
| `hadr_fabric_api_replicator_begin_wait_for_quorum_catchup` | Fires when quorum catchup begins | `catch_up_mode`, `must_catch_up_replica_count`, `epoch_configuration_number` |
| `hadr_fabric_api_replicator_end_wait_for_quorum_catchup` | Fires when quorum catchup ends | `result`, `result_desc` |
| `hadr_fabric_api_replicator_wait_for_quorum_catchup_all_timeout` | Fires on quorum catchup timeout | `result`, `duration_ms`, `progress_timeout_ms` |
| `hadr_db_commit_mgr_set_policy` | Fires when a commit manager's policy changes | commit manager ID, new policy, delay |
| `hadr_db_commit_mgr_harden` | Fires when a transaction commit harden completes | `wait_log_block` (the LSN waited for) |
| `hadr_db_commit_mgr_harden_still_waiting` | Fires when a commit is still waiting for remote harden | target log block, elapsed time |
| `hadr_db_commit_mgr_update_harden` | Fires when hardened LSN is updated | new hardened LSN, commit policy, delay |
| `hadr_db_partner_set_policy` | Fires when a partner's commit policy changes | partner ID, new policy |
| `hadr_db_partner_set_sync_state` | Fires when a partner's sync state changes | partner ID, new sync state |

### MustCatchup Replica XML Format

The `replica_infos_mustcatchup` and `replica_infos_current` XML columns contain replica details in this format:

```xml
<![CDATA[<replica fabricId="134197673185021991" role="4" roleDesc="REPLICA_ROLE_ACTIVE_SECONDARY"
         status="2" statusDesc="FABRIC_REPLICA_STATUS_UP"
         replicatorAddress="..."
         currentProgress="-1" catchUpCapability="-1"
         mustCatchup="1"/>]]>
```

The `mustCatchup="1"` attribute (boolean integer: `1` = true, `0` = false) identifies which replica Service Fabric has designated as the must-catchup target. Values of `-1` for `currentProgress` and `catchUpCapability` indicate the information was not yet known at the time of the configuration update.

### Ring Buffer Diagnostics

The engine records commit policy changes to a dedicated ring buffer (`HadrDbMgrCommitRingBufferRecord`) accessible via `GetCommitRingBuffer()`. Each record contains: database ID, replica ID, **commit manager ID** (identifies Main/Alternate/GeoDR/MustCatchup), current harden policy, sync config, partner counts, log block position, and lease state.

## Key Concepts

### Synchronous Commit Flow (Quorum Commit)

1. **Primary Replica**: Captures the log block and dispatches it to all participating secondary replicas
2. **Secondary Replicas**: Each participating secondary receives the log block, hardens it to disk, and acknowledges back to the primary
3. **Primary Replica**: Allows the commit to complete once the **majority quorum** of the active replica view has acknowledged hardening — it does **not** wait for every replica
4. A replica that is excluded from the commit-participating set (`is_commit_participant = false`) does not contribute to or block quorum

**Investigation focus**: Because commits depend on the quorum commit set rather than any single replica, investigation should start by identifying the active replica set, which replicas are commit participants, and what is preventing the **quorum** from forming — not just which single replica is slow.

### Log Block Lifecycle

> **ℹ️ SQL Server box-product only**: The extended events listed below (`hadr_capture_log_block`, `hadr_transport_receive_log_block_message`, `log_flush_start`/`log_flush_complete`, `hadr_send_harden_lsn_message`, `hadr_receive_harden_lsn_message`, `hadr_db_commit_mgr_harden`) are part of the SQL Server box-product diagnostic surface. Several of them — including `log_flush_complete.duration` and `hadr_db_commit_mgr_harden.wait_log_block` — are **not enabled in Azure SQL DB (XDB)**. The flow below is documented for context and for engineers debugging on box-product builds. For XDB investigation, rely on the telemetry tables and waits described later in this document.

The end-to-end flow of a log block involves these extended events:

| Event | Mode | Location | Description |
|-------|------|----------|-------------|
| `hadr_capture_log_block` | 1 | Primary | SQL starts to capture a log block |
| `hadr_capture_log_block` | 2 | Primary | SQL copies data to log block buffer |
| `hadr_capture_log_block` | 3 | Primary | Log block is ready to send |
| `hadr_capture_log_block` | 4 | Primary | Log block sent to specific secondary |
| `hadr_transport_receive_log_block_message` | 1 | Secondary | Data received in secondary redo thread |
| `hadr_transport_receive_log_block_message` | 2 | Secondary | Log block content saved to redo buffer |
| `log_flush_start` | - | Secondary | Start to flush log block to disk |
| `log_flush_complete` | - | Secondary | Log block flushed to disk |
| `hadr_send_harden_lsn_message` | 3 | Secondary | Send hardened LSN to primary |
| `hadr_receive_harden_lsn_message` | 1 | Primary | Primary receives hardened LSN message |
| `hadr_db_commit_mgr_harden` | - | Primary | Transaction commits after hardening confirmed |

### Wait Log Block Property

> **ℹ️ SQL Server box-product only — not enabled on Azure SQL DB (XDB).**

The `hadr_db_commit_mgr_harden` event contains a `wait_log_block` property that identifies which log block LSN the commit was waiting for. On SQL Server box-product builds where this XEvent property is enabled, this is the key correlation point for tracing the full timeline. In Azure SQL DB, use the replica state telemetry (`MonDmDbHadrReplicaStates`) and waits described below instead.

## Performance Counters

### SQLServer:Availability Replica Counters

| Counter | Description |
|---------|-------------|
| Bytes Sent to Replica/sec | Rate of log data sent to secondary |
| Bytes Sent to Transport/sec | Rate of data sent to transport layer |
| Bytes Received from Replica/sec | Rate of data received (secondary side) |
| Flow Control/sec | Number of flow control events |
| Flow Control Time (ms/sec) | Time spent in flow control |
| Resent Messages/sec | Messages requiring retransmission |

### SQLServer:Databases Counters

| Counter | Description |
|---------|-------------|
| Log Bytes Flushed/sec | Rate of log hardening to disk |
| Log Flushes/sec | Number of log flush operations |
| Log Flush Wait Time | Time waiting for log flush |

### Network Adapter Counters

| Counter | Description |
|---------|-------------|
| Bytes Total/sec | Total network throughput |
| Bytes Sent/sec | Outbound network traffic |
| Bytes Received/sec | Inbound network traffic |
| Current Bandwidth | Maximum adapter bandwidth |

## Key Telemetry Tables

### MonDmDbHadrReplicaStates

Primary table for AG replica state tracking. Key columns:

| Column | Description |
|--------|-------------|
| `redo_queue_size` | Size of redo queue in KB |
| `redo_rate` | Rate of redo operations KB/sec |
| `log_send_queue_size` | Size of log send queue in KB |
| `log_send_rate` | Rate of log sending KB/sec |
| `synchronization_health_desc` | HEALTHY, NOT_HEALTHY, PARTIALLY_HEALTHY |
| `synchronization_state_desc` | SYNCHRONIZED, SYNCHRONIZING, NOT SYNCHRONIZING, REVERTING |
| `is_primary_replica` | True if local replica is primary |
| `is_commit_participant` | True if replica participates in commits |
| `internal_state_desc` | GLOBAL_PRIMARY, PRIMARY, FORWARDER, SECONDARY |

### MonDmOsWaitStats

Wait statistics including HADR_SYNC_COMMIT and related wait types.

### MonSQLSystemHealth

Extended event ring buffer data from system_health session.

## Root Cause Categories

### 1. Slow Disk I/O on Secondary

**Symptoms:**
- High WRITELOG or PAGEIOLATCH_* wait times on secondary
- Elevated I/O latency on the secondary's log file (visible via `MonDmIoVirtualFileStats` for the log file)
- Long duration between `log_flush_start` and `log_flush_complete` *(SQL Server box-product only — not available on Azure SQL DB)*
- High `duration` property on the `log_flush_complete` event *(SQL Server box-product only — not enabled on Azure SQL DB)*

**Investigation:**
- Check disk I/O performance counters on secondary
- Look for concurrent I/O-intensive workloads (read-only queries, backups)
- Verify hardware compatibility between primary and secondary

### 2. High CPU (Compression/Decompression)

**Symptoms:**
- `hadr_log_block_compression` events logged with `is_compressed=true`
- Long duration between `log_flush_start` and `hadr_log_block_compression` on primary
- Long duration between `hadr_transport_receive_log_block_message` (mode=2) and `hadr_log_block_decompression` on secondary

**Investigation:**
- Check CPU utilization on both replicas
- Review AG compression settings
- Consider TF1462 (disable compression) or TF9591 (disable parallel compression for SQL 2016+)

### 3. Network Bottleneck or Latency

**Symptoms:**
- `Bytes Total/sec` approaching `Current Bandwidth/8` on network adapter
- Network perf counter `Bytes Sent/sec` matches AG counter `Bytes Sent to Transport/sec`
- High Flow Control/sec values

**Latency Measurement with XEvents:**
- **Primary → Secondary latency**: Duration from `hadr_capture_log_block` (mode=4) to `hadr_transport_receive_log_block_message` (mode=1)
- **Secondary → Primary latency**: Duration from `hadr_send_harden_lsn_message` (mode=3) to `hadr_receive_harden_lsn_message` (mode=1)

**Investigation:**
- Measure network round-trip time between replicas
- Check for network congestion or bandwidth saturation
- Review AG endpoint configuration

### 4. HADR_SYNC_COMMIT Spike during Quorum Catchup (Known Issue — BUG 3546900)

**Background:**

During a planned failover, the Service Fabric Placement Load Balancer (PLB) selects a new primary replica based on multiple factors including load balancing metrics, fault domains, affinity constraints, and harden distance. Because PLB does not rely solely on how far behind a secondary replica is lagging, it may select a secondary that has a significant redo or log send queue backlog as the new primary.

When this occurs, the new primary enters a **Quorum Catchup** state. The `must_catchup commit manager` is engaged to ensure the remaining secondaries catch up to the new primary's state. During this catchup phase, all synchronous commits are blocked, causing a spike in `HADR_SYNC_COMMIT` wait times.

**Symptoms:**
- `HADR_SYNC_COMMIT` waits spike immediately following a planned failover or role transition
- `BuildReplicaCatchup` events appear in XEvent system health data (query HSC400) around the time of the failover
- High `redo_queue_size` or `log_send_queue_size` on secondary replicas immediately after the failover
- `synchronization_state_desc` shows `SYNCHRONIZING` (not `SYNCHRONIZED`) on secondary replicas after the transition
- The node that became primary was previously a secondary with a large redo/log send queue

**Investigation:**
- Check query HSC110 (Primary Node Timeline) for role transitions during the incident window
- Check query HSC400 (XEvent System Health) for `BuildReplicaCatchup` events
- Check query HSC160 (Quorum Catchup Detection) to correlate role transitions with queue spikes on secondaries
- Compare `redo_queue_size` before and after the transition for the new primary's secondaries

**Why PLB may choose a lagging secondary:**

PLB considers factors beyond harden/truncation LSN when selecting a new primary:
1. **Updated Replicas** — prioritizes replicas that minimize reconfigurations
2. **Affinity Constraints** — service or replica placement rules
3. **Harden Distance** — distance between primary and secondary state (not the sole factor)
4. **Load Balancing Metrics** — CPU and memory usage across nodes
5. **Fault Domains** — distribution for failure resilience
6. **Placement Constraints** — node capacity and resource availability

Because of these combined factors, PLB cannot rely solely on how far behind a local secondary is lagging to choose or exclude it as a new primary.

**Status:** This is a known product bug ([BUG 3546900](https://dev.azure.com/msdata/Database%20Systems/_workitems/edit/3546900)). The proposed fix is to set the `must_catchup commit manager` mode to `DoNothing` to avoid getting stuck in Quorum Catchup. The bug is currently in `Approved` state (not yet fixed).

**Reference ICM:** [549907140](https://portal.microsofticm.com/imp/v3/incidents/details/549907140/home)

## XEvent Query Patterns

> **ℹ️ SQL Server box-product only**: The following XEvent correlation patterns rely on properties (e.g., `wait_log_block`, `log_block_id`) that are **not enabled in Azure SQL DB (XDB)**. They are retained here for engineers troubleshooting on SQL Server box-product builds. For XDB, use the telemetry-based queries in [queries.md](./queries.md) instead.

### Finding Next Log Block LSN

To trace a specific commit wait, first find the `wait_log_block` value from `hadr_db_commit_mgr_harden`, then find the next sequential log block (within 120 units, since max log block is 60KB and 1 unit = 512 bytes):

```
Secondary: log_block_id > [current log_block_id] AND log_block_id <= [current log_block_id] + 120
```

### Correlating Primary Events

```
(name != hadr_receive_harden_lsn_message AND log_block_id = [current log_block_id])
OR (name == hadr_receive_harden_lsn_message AND log_block_id = [next log_block_id])
OR (name == hadr_db_commit_mgr_harden AND wait_log_block = [current log_block_id])
```

### Correlating Secondary Events

```
(name != hadr_send_harden_lsn_message AND log_block_id = [current log_block_id])
OR (name == hadr_send_harden_lsn_message AND log_block_id = [next log_block_id])
```

## References

- [TechCommunity: Capture Logs for AG Performance Troubleshooting](https://techcommunity.microsoft.com/blog/sqlserver/how-to-capture-logs-for-availability-group-performance-troubleshooting/3699540)
- [MSDN: Recommendations for Availability Replicas](https://msdn.microsoft.com/en-us/library/ff878487.aspx)
- [BUG 3546900: HADR_SYNC_COMMIT spike during Quorum Catchup](https://dev.azure.com/msdata/Database%20Systems/_workitems/edit/3546900)
- [ICM 549907140: RCA for HADR_SYNC_COMMIT waits](https://portal.microsofticm.com/imp/v3/incidents/details/549907140/home)
