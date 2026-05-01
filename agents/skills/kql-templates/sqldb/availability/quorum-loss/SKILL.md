---
name: quorum-loss
description: Debug Azure SQL Database quorum loss scenarios where Service Fabric loses read or write quorum with expectation of replica recovery. Investigates blocked replica rebuilds, transient quorum faults, and determines if quorum loss is temporary or permanent. Use when troubleshooting QuorumLoss alerts where replicas are expected to recover but cannot rebuild due to underlying issues. Does NOT apply to Hyperscale/VLDB app types.
---

# Debug Azure SQL Database Quorum Loss Issues

!!!AI Generated. To be verified!!!

Debug high availability quorum loss scenarios for Azure SQL Database where Service Fabric loses either write or read quorum of replicas but expects them to recover.

## Overview

A database enters Quorum Loss (QL) state when Service Fabric cannot establish a majority quorum of the minimum replica set size. For Premium/Business Critical SLOs, the minimum is 3 replicas, so a majority (quorum) is 2 replicas.

This skill investigates quorum loss situations where:
- A quorum of replicas have transiently faulted (process crash, node restart, network partition)
- Service Fabric expects replicas to recover
- New replicas cannot be built due to underlying infrastructure issues
- Service Fabric is waiting (default: infinite) for replica recovery or administrative action
- **Writes are blocked**; reads may still be possible with reduced consistency guarantees

**Note:** This skill does NOT apply to Hyperscale/VLDB app types.

## Special Case Checks (Before Standard Triage)

**🚩 Check these FIRST before proceeding:**

1. **GeoDR Secondary Alert?**
   - If role is FORWARDER, use Geo-secondary TSG instead
   - This skill is for **Primary** or **Global Primary** only

2. **Update SLO in Progress?**
   - If database is in Update SLO, follow Stuck Update SLO TSG

3. **Error 3456 on Secondaries?**
   - "Write lost on primary" indicates **potential data loss**
   - 🚩 **Escalate immediately** to SQL DB Availability Expert queue
   - For CRI: Perform Point In Time Restore (PITR) before the log LSN in the error

4. **Local Storage DB with Healthy Auxiliary Replica?**
   - Follow Auxiliary Replica-specific TSG

## Understanding Quorum Loss

### What is Quorum?

In Azure SQL Database (Business Critical tier), data is replicated across multiple replicas using Service Fabric:
- **Primary replica:** Handles read-write workloads
- **Secondary replicas:** Maintain synchronized copies (typically 3 replicas total)
- **Quorum committed:** Data is considered committed when a majority of replicas (e.g., 2 out of 3) receive it

### Temporary vs. Permanent Quorum Loss

| Aspect | Temporary QL | Permanent QL |
|--------|--------------|--------------|
| **Replica expectation** | Replicas expected to recover | Replicas will NOT come back |
| **Cause** | Process crash, node restart, network partition | Node destroyed, drives failed |
| **Action** | Wait for recovery or restart SQL/node | Escalate to Availability Expert queue |
| **Risk** | Low - no data loss expected | High - potential data loss |

### Quorum Loss vs. Data Loss

| Aspect | Quorum Loss | Data Loss (OnDataLoss) |
|--------|-------------|------------------------|
| **Replica expectation** | Replicas expected to come back | Replicas will NOT come back |
| **Cause** | Transient failures (crash, restart, network) | Permanent failures (node destroyed, drives failed) |
| **Service Fabric action** | Waits for recovery (default: infinite) | Calls `OnDataLossAsync`, proceeds with best remaining replica |
| **Recovery approach** | Fix infrastructure, wait for replicas | Restore from backups or accept data loss |
| **Write availability** | Blocked | Blocked |
| **Read availability** | May be available with reduced consistency | May be available |

**Key difference:** Quorum Loss means Service Fabric *could* rebuild replicas to restore quorum, but something (compute/network/storage issue) is blocking the rebuild process.

## Required Information

When using this skill, provide:
- **Logical server name**: The SQL Database logical server
- **Database name**: The affected database
- **Time window**: Start and end time of the quorum loss incident (UTC)
- **Alert details**: QuorumLoss alert ID or IcM incident ID
- **Symptoms**: Write failures, connection timeouts, error messages

## Investigation Workflow

### 1. Confirm Quorum Loss State

**Check partition health:**
- Look for System.FM (Failover Manager) reports
- Health state should show ERROR with quorum loss description
- Verify partition is below minimum replica count

### 2. Identify Down Replicas

**Analyze replica health:**
- Which replicas are down and when did they fail?
- Check replica-level health reports for crash or fault indicators
- Review application logs for exceptions or errors

### 3. Investigate Infrastructure Issues

**Common causes of blocked replica rebuild:**

**Compute layer:**
- Nodes down, unresponsive, or in unhealthy state
- Service Fabric node status and events
- VM availability and resource allocation

**Network layer:**
- Network partitions preventing replica communication
- Connectivity issues between nodes
- Gateway or load balancer problems

**Storage layer:**
- Drive failures or storage account unavailability
- XStore/storage stamp issues
- Insufficient storage capacity

**Process layer:**
- Replica processes repeatedly crashing
- SQL process lifecycle events
- Unresponsive processes (check process dumps)

### 4. Check Service Fabric State

**Review Service Fabric components:**
- Partition stuck in reconfiguration?
- Replica rebuild attempts and failures
- Service Fabric repair tasks
- Build/reconfiguration timeout issues

### 5. Determine Recovery Path

**Options:**
1. **Wait for transient issues to resolve** (recommended for temporary failures)
2. **Bring down replicas back online** (restart processes/nodes)
3. **Fix underlying infrastructure** (resolve compute/network/storage issues)
4. **Administrative action** (use `Repair-ServiceFabricPartition` API - **potential data loss**)

## What This Skill Investigates

- **Partition health state** and quorum status from System.FM
- **Replica health reports** and fault events
- **Replica state transitions** and lifecycle events
- **Service Fabric partition state** (creation, reconfiguration, stuck states)
- **Underlying infrastructure health:**
  - Compute node availability and events
  - Network connectivity and partitions
  - Storage account and disk health
  - Resource allocation and capacity
- **SQL process lifecycle** events and crashes
- **Repair tasks** and recovery actions
- **Timeline correlation** of failures across layers

## Expected Outcomes

The investigation will identify:
1. **Root cause** preventing replica recovery/rebuild
2. **Affected replicas** and their failure reasons
3. **Infrastructure component** blocking recovery (compute/network/storage)
4. **Timeline** of events leading to quorum loss
5. **Recommended action:**
   - Wait for transient recovery
   - Specific infrastructure fix required
   - Escalation path (compute/network/storage teams)
   - Administrative intervention needed (with data loss risk assessment)

## Execute Queries

Execute queries from [references/queries.md](references/queries.md) to investigate the quorum loss:

**Step 1: Identify Quorum Loss Event**
- QL100 (FTQuorumLoss Events) - Confirm quorum loss and FTQuorumRestored events
- QL110 (Quorum Loss Time Ranges) - Calculate duration of quorum loss

**Step 2: Check Partition and Service State**
- QL200 (Partition Service Lifecycle) - Check for stuck partition creation
- QL210 (WinFab Event Timeline) - Overview of key events

**Step 3: Analyze Replicas**
- QL300 (Replica Health from MonDmDbHadrReplicaStates) - Track primary transitions
- QL310 (SQL Process Exits) - Check for process crashes
- QL320 (Database Recovery State) - Check if stuck in RECOVERING
- QL330 (Replica Build State Change Stuck) - Check Error 41614 state 3
- QL340 (Database Recovery Trace) - Full recovery timeline with phases
- QL350 (Long Recovery Detection) - 🚩 Flag recovery > 10 minutes

**Step 4: Investigate Infrastructure**
- QL400 (Infrastructure Health Events) - Bugchecks, reboots, failures
- QL410 (SQL Process Start Events) - Process lifecycle

**Step 5: Review Reconfiguration**
- QL500 (Reconfiguration Status) - Check if stuck in reconfiguration
- QL510 (Reconfiguration Slow Events) - Identify prolonged reconfigurations
- QL520 (Reconfiguration Duration Summary) - Phase-by-phase timing

**Step 6: Check for Data Loss Indicators**
- QL600 (Unplaced Replica with Data Loss) - 🚩 Critical if results found
- QL610 (Node Deactivation Events) - Nodes being deactivated

**Step 7: Impact Assessment**
- QL700 (LoginOutages Impact) - Customer impact assessment

**Step 8: Fabric API Investigation**
- QL800 (FabricApi Event Timeline) - Comprehensive Fabric API event overview
- QL810 (Write Status Granted) - Confirm when primary became writable
- QL820 (Reconfiguration History) - Detailed replica set composition over time

Follow the query execution tips and common patterns documented in [references/queries.md](references/queries.md).

## Safety Checks Before Recovery

**🚩 MANDATORY before running ANY recovery commands:**

| Check | Requirement | If Not Met |
|-------|-------------|------------|
| Healthy replica exists | At least one replica with status 'Ready', database_state_desc ONLINE | Escalate to HA expert queue |
| Highest LSN | Healthy replica has the highest last_hardened_lsn | Potential data loss - escalate |
| Node is UP | Node hosting healthy replica is UP | Wait for node recovery |
| LSN is valid | 0 < LSN < 4294967295429496729565535 | Escalate - LSN undefined |

**Always snapshot LSN info before running any CAS command and document in incident for auditing.**

## Recovery Actions

**Order of escalation:**

1. **Wait** - For temporary issues, allow natural recovery (minutes)
2. **Restart** - Try restarting SQL process or fabric-node on unhealthy replicas
3. **Recover-FabricService** - CAS command when safety checks pass:
   ```powershell
   Get-FabricService -ServiceName fabric:/Worker.ISO.Premium/{app-guid}/SQL.UserDb/{service-guid} -ServiceClusterName {cluster-fqdn} | Recover-FabricService
   ```
4. **Signal-DataLossEvent** - Only after LSN verification (remaining replica LSN >= down primary LSN)
5. **Escalate** - If data loss risk confirmed, escalate to SQL DB Availability Expert queue

**Pre-Quorum Loss (replica on disabled node):**
```powershell
Get-FabricNode -NodeName {NodeName} -NodeClusterName {ClusterName} | Remove-Replica -AppName {AppName} -PartitionId {PartitionId}
```
- Only use when at least two ready replicas remain

## Post-Recovery Monitoring

1. Monitor replica build progress in "Database Replicas.xts" view, Seeding tab
2. Verify FTQuorumRestored event in WinFabLogs (run QL100 again)
3. Confirm database_state_desc is ONLINE via MonDmDbHadrReplicaStates

## Reference

See [knowledge.md](references/knowledge.md) for detailed definitions, concepts, and related documentation.
See [principles.md](references/principles.md) for debug principles and escalation criteria.