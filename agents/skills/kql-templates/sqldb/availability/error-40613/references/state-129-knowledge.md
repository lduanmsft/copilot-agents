# Error 40613 State 129 - Knowledge Base

## Error Definition

**Error 40613**: "Database '%.*ls' on server '%.*ls' is not currently available."

**State 129**: HADR not available - The database replica is not in a PRIMARY or SECONDARY state. The HADR subsystem cannot serve connections because the replica is in an abnormal state (NONE, RESOLVING, NOT_AVAILABLE, etc.).

## When This Error Occurs

State 129 is raised when:

1. **Replica Role is NONE**: The replica has lost its role assignment (between transitions or after deactivation)
2. **Replica is RESOLVING**: Quorum loss — the replica cannot confirm its role without sufficient quorum
3. **HADR Subsystem Not Initialized**: The HADR subsystem has not started or has crashed
4. **Page Server Failure (Hyperscale)**: Socrates architecture page server connectivity lost, preventing the compute node from serving data
5. **Replica Deactivation**: Service Fabric is deactivating or moving the replica

## Incident Analysis: Hyperscale Correlation

Historical incident analysis (Q1 2026) reveals a **strong correlation between state 129 and Hyperscale SLOs**:

| Observation | Detail |
|-------------|--------|
| All 6 state 129 incidents were Hyperscale | SQLDB_HS_Gen5_*, SQLDB_HS_PRMS_* |
| Average TTM | 1.72 hours |
| Common regions | East US, UK South, West Europe |
| Root cause pattern | Page server connectivity or lifecycle issues |

This suggests state 129 is primarily a **Socrates architecture** issue where the compute node loses connectivity to page servers.

## Relationship with States 126 and 127

State 129 is **distinct from** the normal failover error sequence:

| State | Name | When It Occurs | Normal Failover? |
|-------|------|----------------|------------------|
| **126** | Database in transition | During active role change | ✅ Yes |
| **127** | Cannot open during warmup | After role change, during recovery | ✅ Yes |
| **129** | HADR not available | Replica not in PRIMARY/SECONDARY | ❌ No — abnormal state |

**Normal failover sequence**: 126 → 127 → Available
**State 129**: Indicates the replica is in an abnormal HADR state, NOT part of normal failover flow.

## Comparison with Related States

| State | Name | Condition | Typical Duration | SLO Affinity |
|-------|------|-----------|------------------|--------------|
| **126** | Database in transition | Role change executing | < 30 seconds | All |
| **127** | Cannot open during warmup | Recovery in progress | 30 sec - 2 min | All |
| **129** | HADR not available | Not PRIMARY/SECONDARY | Variable | Hyperscale (strong) |
| **84** | Cannot access master | User DB can't reach logical master | Variable | All |

## HADR Replica States

The HADR subsystem can be in several states:

```
HADR State Machine:
──────────────────────────────────────────────────────────────────────────────

                    ┌─────────────┐
                    │   PRIMARY   │ ← Serves read/write connections
                    └──────┬──────┘
                           │ Role change / failover
                    ┌──────▼──────┐
                    │    NONE     │ ← No role assigned (transient)
                    └──────┬──────┘
                          ╱ ╲
                         ╱   ╲
              ┌─────────▼┐   ┌▼──────────────┐
              │ SECONDARY │   │  RESOLVING    │ ← Quorum issues
              └───────────┘   └──────┬────────┘
                                     │
                              ┌──────▼────────┐
                              │ NOT_AVAILABLE  │ ← HADR subsystem down
                              └───────────────┘
──────────────────────────────────────────────────────────────────────────────

State 129 errors occur when replica is in: NONE, RESOLVING, NOT_AVAILABLE
```

### State Descriptions

| HADR State | Description | Connections? | Typical Cause |
|------------|-------------|--------------|---------------|
| PRIMARY | Active primary replica | ✅ Yes | Normal operation |
| SECONDARY | Active secondary replica | ✅ Read-only | Normal operation |
| NONE | No role assigned | ❌ State 129 | Between role changes |
| RESOLVING | Attempting to determine role | ❌ State 129 | Quorum loss |
| NOT_AVAILABLE | HADR subsystem unavailable | ❌ State 129 | Subsystem crash/failure |

## Hyperscale (Socrates) Architecture Context

In Hyperscale databases, the compute node depends on **page servers** for data access:

```
Hyperscale Architecture:
──────────────────────────────────────────────────────────────────────────────

  ┌──────────────┐     ┌──────────────┐
  │  Compute     │────►│ Page Server  │  ← Data pages
  │  Node        │     │  1           │
  │              │     └──────────────┘
  │ (HADR lives  │     ┌──────────────┐
  │  here)       │────►│ Page Server  │  ← Data pages
  │              │     │  2           │
  └──────────────┘     └──────────────┘
         │
         ▼
  If page server connectivity lost:
  → HADR subsystem may become NOT_AVAILABLE
  → State 129 errors for all connections
──────────────────────────────────────────────────────────────────────────────
```

**Why Hyperscale is affected**: The compute node's HADR subsystem depends on page server connectivity. When page servers are unreachable, the HADR subsystem cannot guarantee data consistency and transitions to NOT_AVAILABLE.

## Expected vs. Problematic Scenarios

### Brief Disruption (< 30 seconds)

- **During reconfiguration**: Brief state 129 during extended role transition
- **Transient page server hiccup**: Momentary connectivity loss (Hyperscale)

### Problematic (Requires Investigation)

| Symptom | Possible Cause | Investigation |
|---------|---------------|---------------|
| Errors > 30 sec (Hyperscale) | Page server failure | Check `MonSQLSystemHealth` for page server errors |
| Errors > 30 sec (BC/GP) | Quorum loss | Use `quorum-loss` skill |
| Replica stuck in NONE | Failed role transition | Check `MonFabricApi` for stuck transitions |
| Replica in RESOLVING | Quorum loss | Use `quorum-loss` skill |
| No HADR events at all | HADR subsystem crash | Check node health, `MonSQLSystemHealth` |
| Repeated state 129 | Recurring infrastructure issue | Check for pattern across incidents |

## Key Telemetry Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `MonLogin` | Captures login failures | error, state, error_count |
| `MonFabricApi` | Role change, replica state, write status | begin/end_change_role, state_change, report_fault |
| `SqlFailovers` | Completed failover summary | `FailoverStartTime`, `FailoverEndTime` |
| `LoginOutages` | Platform outage reporting | `OutageType`, `durationSeconds`, `OutageReasonLevel1` |
| `MonSQLSystemHealth` | Error and diagnostic messages | `message` (page server, HADR errors) |

## Key `MonFabricApi` Events

### `hadr_fabric_api_replicator_state_change`
Fired when HADR replica state changes. Key fields:
- `current_state_desc`: New state ("PRIMARY", "SECONDARY", "NONE", "RESOLVING", "NOT_AVAILABLE")
- `new_role_desc`: Role associated with the state change

### `hadr_fabric_api_replicator_report_fault`
Fired when the HADR replica reports a fault. Key fields:
- `result_desc`: Fault description
- `current_state_desc`: State when fault occurred

### `hadr_fabric_api_partition_write_status`
Tracks write status changes:
- `previous_write_status_desc` / `current_write_status_desc`
- NOT_PRIMARY, RECONFIGURATION_PENDING, Granted

## Troubleshooting Checklist

- [ ] Confirm error 40613 state 129 in `MonLogin`
- [ ] Check SLO type from get-db-info (Hyperscale vs GP/BC)
- [ ] Calculate error duration
- [ ] Check `SqlFailovers` for associated failover
- [ ] Check `MonFabricApi` for replica state (NONE, RESOLVING, NOT_AVAILABLE)
- [ ] Check `MonFabricApi` for role change events
- [ ] If Hyperscale: Check `MonSQLSystemHealth` for page server errors
- [ ] If BC/GP: Check for quorum loss indicators
- [ ] Review `LoginOutages` for impact and root cause categorization
- [ ] Verify write status recovery

## Common Mitigations

| Scenario | Mitigation |
|----------|------------|
| Page server failure (HS) | Escalate to Socrates/Hyperscale team |
| Quorum loss | Use `quorum-loss` skill, check node health |
| Stuck in NONE | May need replica restart, escalate to `failover` skill |
| Transient (< 30 sec) | Monitor, may self-resolve |
| Node failure | Use `node-health` skill |
| Recurring pattern | Investigate infrastructure (page servers, nodes, network) |

## Canned RCA Template

For brief transient state 129 errors (< 30 seconds) associated with a reconfiguration:

```
Root Cause: Transient HADR unavailability during reconfiguration

Between {StartTime} and {EndTime}, the database experienced brief 
unavailability (state 129 errors) when the HADR subsystem was 
temporarily not in a PRIMARY or SECONDARY state during a 
reconfiguration event.

Timeline:
- State 129 errors started: {FirstError}
- State 129 errors stopped: {LastError}
- Total duration: {DurationSeconds} seconds
- Associated failover: {FailoverInfo}

The HADR subsystem recovered and the database became available.

Recommendation: For applications sensitive to brief disruptions, 
implement retry logic with exponential backoff as documented at:
https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-connectivity-issues
```

## References

- [Azure SQL Database high availability](https://learn.microsoft.com/en-us/azure/azure-sql/database/high-availability-sla)
- [Hyperscale service tier](https://learn.microsoft.com/en-us/azure/azure-sql/database/service-tier-hyperscale)
- [Troubleshoot transient connection errors](https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-connectivity-issues)