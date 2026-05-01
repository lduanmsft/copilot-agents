# Debug Principles for Quorum Loss Investigation

## Triage Principles

### 1. Determine Quorum Loss Type

**Temporary vs. Permanent Quorum Loss:**

| Aspect | Temporary QL | Permanent QL |
|--------|--------------|--------------|
| **Replica expectation** | Replicas expected to recover | Replicas will NOT come back |
| **Cause** | Process crash, node restart, network partition | Node destroyed, drives failed |
| **Action** | Wait for recovery or restart SQL/node | Escalate to Availability Expert queue |
| **Risk** | Low - no data loss expected | High - potential data loss |

1. **Check if temporary**: Wait for partition to recover naturally
2. **Try restart**: Restart SQL process or fabric-node on unhealthy replicas
3. **If permanent**: Most replicas are permanently down - escalate immediately

### 2. Special Case Checks

**Before proceeding with standard triage:**

1. **GeoDR Secondary Alert?**
   - If role is FORWARDER, use Geo-secondary TSG instead
   - This skill is for Primary or Global Primary only

2. **Update SLO in Progress?**
   - If database is in Update SLO, follow Stuck Update SLO TSG

3. **Error 3456 on Secondaries?**
   - "Write lost on primary" indicates potential data loss
   - 🚩 **Escalate immediately** to SQL DB Availability Expert queue
   - For CRI: Perform Point In Time Restore (PITR) before the log LSN in the error

4. **Local Storage DB with Healthy Auxiliary Replica?**
   - Follow Auxiliary Replica-specific TSG

## Safety Checks Before Recovery

### 3. Pre-Recovery Validation

**MANDATORY checks before running ANY recovery commands:**

| Check | Requirement | 🚩 If Not Met |
|-------|-------------|---------------|
| Healthy replica exists | At least one replica with status 'Ready', database_state_desc ONLINE | Escalate to HA expert queue |
| Highest LSN | Healthy replica has the highest last_hardened_lsn | Potential data loss - escalate |
| Node is UP | Node hosting healthy replica is UP | Wait for node recovery |
| LSN is valid | 0 < LSN < 4294967295429496729565535 | Escalate - LSN undefined |

**🚩 If ANY check fails: Escalate to HA expert queue for potential data loss assessment**

### 4. LSN Validation Principles

1. **Always snapshot LSN info** before running any CAS command
2. **Document in incident** for auditing purposes
3. **Compare LSN values** between replicas:
   - Healthy replica should have highest `last_hardened_lsn`
   - If down primary has higher LSN, escalate for approval

## Investigation Principles

### 5. Timeline Reconstruction

1. **Start with quorum loss events** (QL100 - FTQuorumLoss)
2. **Identify affected replicas** and their failure times
3. **Check infrastructure** for each failed replica:
   - Compute node health
   - Network connectivity
   - Storage availability
4. **Correlate timestamps** across telemetry sources

### 6. Root Cause Categories

| Category | Indicators | Queries to Run |
|----------|------------|----------------|
| **Process Crash** | ProcessExitedOperational events | QL310, check exit codes |
| **Node Issues** | Node deactivation, bugcheck | QL400, MonSQLInfraHealthEvents |
| **Network Partition** | Replicas on different nodes can't communicate | Check transport errors |
| **Storage Failure** | XStore/drive issues | MonSQLInfraHealthEvents |
| **Reconfiguration Stuck** | ReconfigurationSlow events | QL500, HA1005 |

### 7. Reconfiguration Analysis

**Normal reconfiguration phases:**
1. Phase1 (GetLSN) - Quick
2. Phase2 (Catchup) - Variable based on log size
3. Phase3 (Deactivate) - Should be quick
4. Phase4 (Activate) - Should be quick

**🚩 Warning patterns:**
- ReconfigurationSlow events for extended periods
- Same reconfiguration start time appearing in multiple slow events
- Phase3_Deactivate stuck with S/N transition
- Multiple reconfigurations with same pattern

## Expected Timings

| Event | Normal | Warning | Critical |
|-------|--------|---------|----------|
| Quorum restoration | < 5 min | 5-15 min | > 15 min |
| Reconfiguration | < 2 min | 2-10 min | > 10 min |
| Replica rebuild | < 10 min | 10-30 min | > 30 min |
| SQL process start | < 30 sec | 30s-2min | > 2 min |
| Database recovery | < 2 min | 2-10 min | > 10 min |

### 6a. Replica Build Stuck Pattern

**Check Error 41614 state 3** (query QL330):
1. Look for repeated `hadr_fabric_build_replica_operation_state_change` events
2. If `old_state_desc` and `new_state_desc` repeat without progress, the build is stuck
3. Check `trigger_desc` for the blocking reason
4. 🚩 If stuck for > 10 minutes, investigate underlying infrastructure

### 6b. Long Recovery Detection

**Check recovery time** (query QL350):
1. Any `total_elapsed_time_sec > 600` (10 minutes) is a 🚩 red flag
2. Use QL340 (Database Recovery Trace) to see phase-by-phase progress
3. Extended redo phase may indicate large transaction log
4. Repeated recovery starts without completion indicate process crashes

## Recovery Actions

### 8. Recovery Command Principles

**Order of escalation:**

1. **Wait** - For temporary issues, allow natural recovery (minutes)
2. **Restart** - Try restarting SQL process or fabric-node
3. **Recover-FabricService** - CAS command when safe
4. **Signal-DataLossEvent** - Only after LSN verification
5. **Escalate** - If data loss risk confirmed

**Recover-FabricService:**
```powershell
Get-FabricService -ServiceName fabric:/Worker.ISO.Premium/{app-guid}/SQL.UserDb/{service-guid} -ServiceClusterName {cluster-fqdn} | Recover-FabricService
```

**Remove-Replica (Pre-Quorum Loss on disabled node):**
```powershell
Get-FabricNode -NodeName {NodeName} -NodeClusterName {ClusterName} | Remove-Replica -AppName {AppName} -PartitionId {PartitionId}
```
- Only use when at least two ready replicas remain

### 9. Post-Recovery Monitoring

1. **Monitor replica build progress** in "Database Replicas.xts" view, Seeding tab
2. **Verify quorum restored** via QL100 (FTQuorumRestored event)
3. **Confirm database ONLINE** via MonDmDbHadrReplicaStates
4. **Check for recurring issues** - pattern may indicate underlying problem

## Escalation Criteria

### 🚩 Immediate Escalation to SQL DB Availability Expert Queue

- Error 3456 "write lost on primary" on any secondary
- LSN validation fails
- No healthy replica available
- LSN is undefined (0 or max value)
- Permanent infrastructure failure confirmed
- Data loss is unavoidable

## Related Documentation

- [TRDB1002 - Quorum Loss TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-db-availability-tsgs-new/sql-db-availability-tsgs/ha/common-unavailability-root-causes/trdb0102-quorum-loss)
- [Service Fabric Disaster Recovery](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-disaster-recovery)