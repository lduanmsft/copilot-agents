# Terms and Concepts

## Core Concepts

### Quorum
For stateful services in Service Fabric, incoming data is replicated between replicas (the primary and active secondaries). If a majority of replicas receive the data, it is considered **quorum committed**. For example, with 5 replicas, 3 constitute a quorum (N/2 + 1). At any point, at least a quorum of replicas has the latest data.

For Premium/Business Critical SLOs, the minimum replica set size is 3 replicas, so a majority (quorum) is 2 replicas.

### Quorum Loss (QL)
A database enters Quorum Loss (QL) state when Service Fabric cannot establish a majority quorum of the minimum replica set size. For Premium/Business Critical SLOs, this occurs when 2 or more replicas are down simultaneously.

**Characteristics:**
- A quorum of replicas have transiently faulted
- Service Fabric cannot determine if remaining replicas have sufficient data to restore the partition
- New replicas cannot be built due to underlying issues (compute, network, storage)
- Service Fabric prevents additional writes to the partition and waits for quorum restoration
- Default wait time is **infinite** (requires administrative action to proceed)

**Example:** If a partition has 3 replicas and 2 fail, Service Fabric enters quorum loss because it cannot guarantee the remaining 1 replica has complete data.

**Note:** This skill does NOT apply to Hyperscale/VLDB app types.

### Pre-Quorum Loss
Pre-Quorum Loss occurs when enough replicas are down to risk entering quorum loss, but the threshold has not yet been triggered. For example, with 3 replicas, if 1 is down, you are at risk of quorum loss (one more failure would trigger it).

### Data Loss vs. Quorum Loss

| Aspect | Quorum Loss | Data Loss (OnDataLoss) |
|--------|-------------|------------------------|
| **Replica expectation** | Replicas expected to come back | Replicas will NOT come back |
| **Cause** | Process crash, node restart, transient network partition | Nodes destroyed, drives failed permanently |
| **Service Fabric action** | Waits for recovery (default: infinite) | Calls `OnDataLossAsync`, proceeds with best remaining replica |
| **Recovery approach** | Fix infrastructure, wait for replicas | Restore from backups or accept data loss |
| **Write availability** | Blocked | Blocked |
| **Read availability** | May be available with reduced consistency | May be available |

**Key difference:** Quorum Loss means Service Fabric *could* rebuild replicas to restore quorum, but something (compute/network/storage issue) is blocking the rebuild process.

### LSN (Log Sequence Number)

**last_hardened_lsn** - The log sequence number that has been hardened (persisted) on a replica. Critical for data loss prevention:

- **Valid LSN:** 0 < LSN < 4294967295429496729565535
- **Invalid LSN:** LSN = 0 or LSN = 4294967295429496729565535 (undefined)

When recovering from quorum loss:
- The replica with the highest `last_hardened_lsn` should be used for recovery
- If a down replica has higher LSN than surviving replicas, data loss may occur

### Error 3456 - Write Lost on Primary

🚩 **Critical Error:** When secondaries report "Error: 3456" (write lost on primary), this indicates potential data loss. Immediate escalation required:
- Escalate to SQL DB Availability Expert queue
- For CRI: Perform Point In Time Restore (PITR) before the log LSN in the error

### Error 41614 - Transient Fabric Error During Replica Build

Error 41614 indicates: "Fabric Service '%ls' encountered a transient error while performing Windows Fabric operation on '%ls' database."

**State 3** is particularly important for quorum loss investigation:
- Indicates the replica build operation is stuck in a state change
- Occurs when Service Fabric is trying to rebuild replicas but encounters transient errors
- Repeated occurrences with the same `old_state_desc`/`new_state_desc` indicate the build is stuck
- Check `trigger_desc` to understand what is blocking the rebuild

### Database Recovery Trace

When a replica starts up, the database goes through recovery phases:
1. **Analysis phase** - Scans the transaction log to determine what needs to be redone/undone
2. **Redo phase** - Replays committed transactions from the log
3. **Undo phase** - Rolls back uncommitted transactions

🚩 **Red flag:** Recovery time over 10 minutes (`total_elapsed_time_sec > 600`) indicates potential issues:
- Large transaction log requiring extended redo
- Storage performance problems slowing recovery
- Repeated recovery attempts due to process crashes

## Service Fabric Components

### System.FM (Failover Manager)
- Authority that manages information about service partitions
- Reports partition health state (OK, Warning, Error)
- Tracks replica counts and quorum status
- Reports when partition is below minimum or target replica count
- Emits FTQuorumLoss and FTQuorumRestored events

### WinFab Event Types

| Event Type | Description |
|------------|-------------|
| **FTQuorumLoss** | Partition entered quorum loss state |
| **FTQuorumRestored** | Quorum has been restored |
| **FTUpdate** | Failover unit state changed |
| **ReconfigurationStarted** | Reconfiguration began |
| **ReconfigurationCompleted** | Reconfiguration finished |
| **ReconfigurationSlow** | Reconfiguration taking longer than expected |
| **ProcessExitedOperational** | SQL process exited |
| **UnplacedReplica** | Replica cannot be placed on any node |
| **FTDataLoss** | Data loss event occurred |

### Fabric API Events (MonFabricApi)

| Event | Description |
|-------|-------------|
| **hadr_fabric_api_replicator_begin_change_role** | Role change operation started |
| **hadr_fabric_api_replicator_end_change_role** | Role change operation completed |
| **hadr_fabric_api_partition_write_status** | Write status changed (GRANTED = writable) |
| **hadr_fabric_api_replicator_begin_build_replica** | Replica build operation started |
| **hadr_fabric_api_replicator_end_build_replica** | Replica build operation completed |
| **hadr_fabric_api_replicator_begin_wait_for_quorum_catchup** | Waiting for quorum catchup |
| **hadr_fabric_api_replicator_end_wait_for_quorum_catchup** | Quorum catchup completed |
| **hadr_fabric_build_replica_operation_state_change** | Replica build state machine transition |

### Partition States

- **Below Minimum Replica Count:** System.FM reports ERROR
- **Below Target Replica Count:** System.FM reports WARNING
- **In Quorum Loss:** System.FM reports ERROR
- **Stuck in Reconfiguration:** System.FM reports WARNING

## Azure SQL Database High Availability

### Local Storage Model (Business Critical tier)

- Uses Service Fabric cluster of database engine processes
- Primary replica with up to 3 secondary replicas
- Always maintains a quorum of available database engine nodes
- Similar to SQL Server Always On Availability Groups
- Failover initiated by Azure Service Fabric

### Replica Types

- **Primary Replica:** Accessible for read-write workloads
- **Secondary Replicas:** Contain synchronized copies of data
- **Read Scale-Out:** Ability to redirect read-only connections to secondary replicas
- **Auxiliary Replica:** Special replica type for local storage DBs

### GeoDR Considerations

- If the alert is for a GeoDR secondary (role is FORWARDER), use the Geo-secondary TSG instead
- This skill is for **Primary** or **Global Primary** roles only

## Troubleshooting Quorum Loss

### Common Causes of Blocked Replica Rebuild

1. **Compute node issues:** Nodes down, not responding, or in unhealthy state
2. **Network connectivity:** Partitions preventing replica communication
3. **Storage failures:** Drives failed, storage account unavailable
4. **Resource allocation:** Insufficient resources to create new replicas
5. **Process crashes:** Replica processes repeatedly crashing
6. **Update SLO in progress:** Database is in Update SLO (use Stuck Update SLO TSG)

### Temporary vs. Permanent Quorum Loss

**Temporary QL:**
- Wait for partition to recover naturally
- Try restarting SQL process or fabric-node on unhealthy replicas
- Usually resolves within minutes

**Permanent QL:**
- Most replicas are permanently down
- Underlying infrastructure has failed
- Requires escalation to SQL DB Availability Expert queue

### Recovery Commands

**Recover-FabricService CAS Command:**
```powershell
Get-FabricService -ServiceName fabric:/Worker.ISO.Premium/{app-guid}/SQL.UserDb/{service-guid} -ServiceClusterName {cluster-fqdn} | Recover-FabricService
```

**Remove-Replica CAS Command (Pre-QL, replica on disabled node):**
```powershell
Get-FabricNode -NodeName {NodeName} -NodeClusterName {ClusterName} | Remove-Replica -AppName {AppName} -PartitionId {PartitionId}
```
- Only use when at least two ready replicas remain

**Signal-DataLossEvent:**
- Use only after verifying remaining replica's hardened LSN matches or exceeds the down primary's LSN
- If not verified, escalate for approval

### Post-Recovery Monitoring

- Monitor replica build progress in the "Database Replicas.xts" view, Seeding tab
- Verify FTQuorumRestored event in WinFabLogs
- Confirm database_state_desc is ONLINE in MonDmDbHadrReplicaStates

## Related Documentation

All source materials used to build and maintain this skill. These URLs are fetched
during skill creation and updates to extract knowledge, principles, and queries.

### Internal Documentation (eng.ms / ADO Wiki)
- [TRDB0102 - Quorum Loss](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-db-availability-tsgs-new/sql-db-availability-tsgs/ha/common-unavailability-root-causes/trdb0102-quorum-loss)
- [CRGW0001 - Login success rate is below 99% LoginErrorsFound_40613_127](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-db-availability-tsgs-new/sql-db-availability-tsgs/ha/autotsg/crgw0001-login-success-rate-is-below-99-loginerrorsfound_40613_127)
  - Section: STEP_10_Check_QuorumLoss_reported_by_WinFabLogs

### Public Documentation
- [Service Fabric System Health Reports](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-understand-and-troubleshoot-with-system-health-reports)
- [Service Fabric Disaster Recovery](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-disaster-recovery)
- [Azure SQL Database High Availability](https://learn.microsoft.com/en-us/azure/azure-sql/database/high-availability-sla-local-zone-redundancy?view=azuresql)