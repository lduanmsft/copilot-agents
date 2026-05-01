---
name: high-sync-commit-wait
description: Debug high HADR_SYNC_COMMIT wait times for Azure SQL Database. Applies ONLY to Business Critical (BC) and Premium service tiers — GP and Hyperscale do not have synchronous replicas and are not eligible. Use when investigating synchronous commit latency, slow transaction commits due to secondary replica acknowledgment delays, or synchronization health issues. Analyzes replica states, redo queue sizes, log send rates, and wait statistics. Accepts either ICM ID or direct parameters (logical server name, database name, startTime, endTime in UTC). Executes Kusto queries via Azure MCP to identify root cause: disk I/O bottlenecks, CPU issues (compression), or network latency.
---

# Debug High HADR_SYNC_COMMIT Wait Times

Debug synchronous commit latency issues where the primary replica experiences excessive wait times for secondary replicas to acknowledge log hardening.

## Overview

The `HADR_SYNC_COMMIT` wait type occurs when a transaction on the primary replica waits for synchronous secondary replicas to confirm they have hardened the transaction log. Excessive waits indicate a performance bottleneck in the synchronization pipeline.

**Common root causes:**
- **Slow Disk I/O on Secondary**: Secondary replica unable to flush logs to disk quickly
- **High CPU (Compression)**: Log compression/decompression consuming excessive CPU
- **Network Bottleneck**: Insufficient bandwidth or high latency between replicas

## Required Information

This skill requires the following inputs:

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
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **physical_database_id**
- **fabric_partition_id**
- All other database environment variables

## Workflow

### 1. Validate Inputs

Ensure all required parameters are provided:
- From user/ICM: LogicalServerName, LogicalDatabaseName, StartTime, EndTime
- From execute-kusto-query: kusto-cluster-uri, kusto-database
- From get-db-info: AppName, ClusterName, and database identifiers

Calculate `Duration` between StartTime and EndTime.

> **⚠️ SLO Pre-Check — MANDATORY**
>
> Before proceeding, verify the database service tier from the `get-db-info` output:
>
> - **Business Critical (BC)** or **Premium** → ✅ Continue with this skill
> - **General Purpose (GP)**, **Hyperscale**, **Standard**, or **Basic** → ❌ **STOP**
>
> If the SLO is **not** BC or Premium, this skill does not apply. Synchronous replication does not exist on this tier, and `HADR_SYNC_COMMIT` waits cannot be the root cause. Inform the user and redirect investigation to other wait types or availability root causes.

> **⚠️ AppName Availability**
>
> `AppName` is required for query **HSC400** (XEvent System Health). If `AppName` was not present in the ICM custom fields, it must be obtained from the `get-db-info` skill output. If `get-db-info` also cannot resolve it, skip **HSC400** and note the omission in the report.

### 2. Confirm HADR_SYNC_COMMIT Waits

Execute query **HSC050** from [references/queries.md](references/queries.md) to directly confirm that `HADR_SYNC_COMMIT` wait times were elevated during the incident window.

**Purpose**: Establishes the root symptom before proceeding to queue analysis. If wait times are not elevated, the issue may be unrelated to synchronous commit latency.

**Flag 🚩 if:**
- `MaxWaitMs` > 100 ms sustained — indicates meaningful synchronization delay
- `TotalWaits` is consistently high across the window — indicates persistent pressure, not just spikes

If this query returns no results or all values are near zero, `HADR_SYNC_COMMIT` is likely not the root cause — consider redirecting investigation.

### 3. Analyze Replica States Timeline

Execute query **HSC100** from [references/queries.md](references/queries.md) to get an overview of replica health over time.

**Identify:**
- Which replicas are primary vs secondary
- Synchronization health status (HEALTHY, NOT_HEALTHY, PARTIALLY_HEALTHY)
- Synchronization state (SYNCHRONIZED, SYNCHRONIZING, NOT SYNCHRONIZING)
- Redo queue and log send queue trends

**Output summary table:**
| Time Window | Primary Node | Sync Health | Avg Redo Queue (KB) | Max Redo Queue (KB) |
|-------------|--------------|-------------|---------------------|---------------------|
| ... | ... | ... | ... | ... |

### 4. Identify Primary Node Transitions and Sync Health Summary

Execute queries **HSC110** and **HSC120** from [references/queries.md](references/queries.md).

**HSC110 — Primary Node Timeline:**
- Detect unexpected role changes (GLOBAL_PRIMARY → PRIMARY → FORWARDER transitions)
- Establish which node held the primary role during the incident

**HSC120 — Synchronization Health Summary:**
- Quickly identify nodes with the highest unhealthy sample counts
- Compare max redo/log send queue sizes across nodes to isolate the bottleneck

**Flag 🚩 if:**
- More than one primary transition is observed (indicates repeated failovers)
- Any node has `UnhealthyCount` > 10% of total samples

### 5. Identify the Replica Set and Check the Quorum Commit Set

Execute query **HSC130** from [references/queries.md](references/queries.md).

> **⚠️ Quorum-commit framing**: In Azure SQL DB BC/Premium, commits require acknowledgment from the **majority quorum** of the active replica view (3 of 4 in normal state, 2 of 3 post-failover) — not from every replica. A single lagging secondary should **not** by itself cause `HADR_SYNC_COMMIT` waits. Investigation should start with: (1) what does the active replica view look like, (2) which replicas are in the commit-participating set (`is_commit_participant = true`), and (3) what is preventing the **quorum** from forming.

**Indicators that the quorum commit set is impaired:**
- Two or more `is_commit_participant = true` secondaries show large `redo_queue_size` (growing over time)
- One or more commit-participating replicas show degraded `synchronization_state_desc`
- The effective commit-participating count has dropped below the quorum threshold (≥3 of 4 normally, ≥2 of 3 post-failover)

**If the quorum commit set is impaired**, suspect:
- Slow disk I/O on more than one secondary
- High CPU on multiple secondaries (decompression overhead)
- Quorum Catchup after a planned failover (see Step 9)
- Report: "Quorum commit set is impaired — N of M commit-participating replicas are healthy; the slowest replica(s) gating quorum are: ..."

### 6. Check Log Send Queue Bottleneck Across the Quorum Commit Set

Execute query **HSC140** from [references/queries.md](references/queries.md).

**Indicators of log send bottleneck blocking quorum:**
- Large `log_send_queue_size` on primary (non `-1` values), especially when correlated with multiple secondaries lagging
- Low `log_send_rate`
- Flow control events

**Important**: A growing log send queue toward only **one** secondary while others remain healthy will not by itself cause `HADR_SYNC_COMMIT` waits, because that single secondary is not required for quorum. Confirm via HSC130/HSC100 that **multiple** commit-participating secondaries are affected, or that the affected replica is the one currently gating quorum.

**If the log send queue is impairing quorum**, suspect:
- Network bandwidth saturation between the primary and the secondaries that make up the quorum commit set
- Network latency to the quorum-required secondaries
- Report: "Primary's log-send to the quorum commit set is backed up — quorum cannot form because N of M required secondaries are not acknowledging in time"

### 7. Check Recovery/Reverting State

Execute query **HSC300** from [references/queries.md](references/queries.md).

**If database is RECOVERING or REVERTING:**
- Synchronization issues may be transient due to recovery
- Report: "Database in recovery state - synchronization issues may resolve after recovery completes"

### 8. Analyze XEvent System Health

Execute query **HSC400** from [references/queries.md](references/queries.md).

**Look for:**
- HADR Fabric messages indicating role changes or session timeouts (e.g., `CFabricReplicaManager::GetHadrSessionTimeout`)
- `BuildReplicaCatchup` events indicating replicas catching up after a failover
- `log_flush` messages indicating disk flush activity on the secondary
- Timestamps of first HADR-related messages to pinpoint when the issue began

**Flag 🚩 if:**
- Session timeout or ping frequency messages appear before the incident window — may indicate a pre-existing connectivity issue
- `BuildReplicaCatchup` events cluster around a particular time — indicates a failover preceded the high wait period

### 9. Check for Quorum Catchup (Known Issue — BUG 3546900)

Execute query **HSC160** from [references/queries.md](references/queries.md) to check if a planned failover to a lagging secondary caused the `HADR_SYNC_COMMIT` spike.

**Context**: When PLB selects a lagging secondary as the new primary during a planned failover, the `must_catchup commit manager` engages Quorum Catchup. During this state, all synchronous commits are blocked, causing `HADR_SYNC_COMMIT` waits to spike. This is a known product bug ([BUG 3546900](https://dev.azure.com/msdata/Database%20Systems/_workitems/edit/3546900)).

**Cross-reference with prior steps:**

1. **HSC110 (Step 4)**: Check if a role transition occurred during the incident window
2. **HSC400 (Step 8)**: Look for `BuildReplicaCatchup` events correlating with the role transition
3. **HSC160 (This step)**: Confirm that secondaries entered `SYNCHRONIZING` state with growing `redo_queue_size` after the transition
4. **HSC170 (This step)**: Identify *which* specific secondary is the most-behind replica gating the quorum commit set
5. **HSC180 (This step)**: Query `MonFabricApi` to confirm the MustCatchup commit manager was engaged and identify the exact replica tagged with `mustCatchup="true"` by Service Fabric

**Flag 🚩 if all three conditions are met:**
- A role transition occurred (from HSC110)
- `BuildReplicaCatchup` events are present (from HSC400)
- Secondaries show `SYNCHRONIZING` with high/growing `redo_queue_size` after the transition (from HSC160)

**Additional confirmation via HSC180:**
- `must_catchup_replica_count` > 0 in the `update_catchup_replica_set_configuration` event
- `replica_infos_mustcatchup` XML shows a replica with `mustCatchup="1"`
- The `begin_wait_for_quorum_catchup` event shows `must_catch_up_replica_count` > 0

Use **HSC170** to call out the specific lagging-catchup replica by name (the replica with the highest `LaggingScore` — typically the one with the largest `MaxRedoQueue_KB` and the most `SynchronizingSamples`) so the RCA can identify the exact node whose catchup is gating commit progress.

Use **HSC180** to directly confirm from fabric API telemetry that the MustCatchup commit manager was activated and which replica was designated.

If this pattern is confirmed, the root cause is **Quorum Catchup after planned failover** — a known product bug. Report this as the root cause and reference BUG 3546900 and ICM 549907140.

### 10. Summarize Findings and Root Cause

Based on the analysis, determine the most likely root cause:

**🔴 Slow Disk I/O on Secondary:**
- High redo_queue_size with low redo_rate
- Wait times correlate with disk activity
- **Recommendation**: Investigate disk performance on secondary replica

**🟡 High CPU (Compression/Decompression):**
- CPU utilization high during wait spikes
- Compression enabled (check MonSQLSystemHealth for hadr_log_block_compression events)
- **Recommendation**: Consider disabling compression (TF1462) or parallel compression (TF9591)

**🟠 Quorum Catchup after Planned Failover (Known Issue — BUG 3546900):**
- Role transition detected (HSC110) followed immediately by HADR_SYNC_COMMIT spike (HSC050)
- `BuildReplicaCatchup` events in XEvent data (HSC400)
- Secondaries in `SYNCHRONIZING` state with growing redo queue after failover (HSC160)
- Cause: PLB selected a lagging secondary as new primary; `must_catchup commit manager` blocked synchronous commits during Quorum Catchup
- **Recommendation**: This is a known product bug (BUG 3546900). The proposed fix is to set the `must_catchup commit manager` to `DoNothing`. Reference ICM 549907140 in the RCA.

**🔵 Network Bottleneck:**
- High log_send_queue_size with low log_send_rate
- Flow control events present
- **Recommendation**: Check network bandwidth and latency between replicas

**Output final summary:**
```
## Root Cause Analysis Summary

**Primary Symptom**: High HADR_SYNC_COMMIT wait times
**Affected Period**: {StartTime} to {EndTime}
**Primary Node**: {NodeName}

### Findings:
1. ...
2. ...

### Most Likely Root Cause: [Disk I/O | CPU | Network | Quorum Catchup (BUG 3546900)]

### Recommendations:
1. ...
2. ...
```

## References

- [references/knowledge.md](references/knowledge.md) - Technical background on HADR_SYNC_COMMIT
- [references/queries.md](references/queries.md) - Kusto queries for investigation
- [TechCommunity Blog](https://techcommunity.microsoft.com/blog/sqlserver/how-to-capture-logs-for-availability-group-performance-troubleshooting/3699540) - AG Performance Troubleshooting
- [BUG 3546900](https://dev.azure.com/msdata/Database%20Systems/_workitems/edit/3546900) - HADR_SYNC_COMMIT spike during Quorum Catchup (Known Issue)
- [ICM 549907140](https://portal.microsofticm.com/imp/v3/incidents/details/549907140/home) - RCA for HADR_SYNC_COMMIT waits (reference incident)
