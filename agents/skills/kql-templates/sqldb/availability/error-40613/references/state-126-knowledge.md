# Error 40613 State 126 - Knowledge Base

## Error Definition

**Error 40613**: "Database '%.*ls' on server '%.*ls' is not currently available."

**State 126**: Database in transition - The database is actively undergoing a role change or state transition and cannot accept connections.

## When This Error Occurs

State 126 is raised when:

1. **Active Role Change**: The replica is transitioning from secondary to primary (or vice versa)
2. **Failover In Progress**: A planned or unplanned failover is executing
3. **Service Fabric Reconfiguration**: The partition is being reconfigured

## Comparison with Related States

| State | Name | Condition | Typical Duration |
|-------|------|-----------|------------------|
| **126** | Database in transition | Role change actively executing | < 30 seconds |
| **127** | Cannot open during warmup | Role change complete, database warming up | 30 sec - 5 min |
| **129** | HADR not available | Database not PRIMARY or SECONDARY state | Variable |
| **84** | Cannot access master | User DB can't reach logical master | Variable |

## Expected vs. Problematic Scenarios

### Expected (No Action Required)

- **Normal failover**: State 126 errors for 10-30 seconds during planned maintenance
- **Customer-initiated failover**: Brief errors after `Invoke-AzSqlDatabaseFailover`
- **SLO change**: Transient errors during tier changes

### Problematic (Requires Investigation)

| Symptom | Possible Cause | Investigation |
|---------|---------------|---------------|
| Errors > 2 minutes | Stuck role change | Check MonFabricApi for incomplete begin/end |
| Repeated state 126 | Frequent failovers | Use freq-failover skill |
| State 126 → 127 | Slow recovery | Check warmup and buffer pool |
| + Quorum warnings | Quorum loss blocking transition | Use quorum-loss skill |

## Role Change Process

```
Timeline of Normal Role Change:
──────────────────────────────────────────────────────────────────────────────
                                                                              
  T+0s              T+5s                  T+20s              T+30s            
   │                  │                     │                  │              
   ▼                  ▼                     ▼                  ▼              
[Begin Role    [Old Primary        [New Primary        [Recovery         
 Change]        Steps Down]         Activated]          Complete]        
                                                                              
   ├──────────────────┼─────────────────────┼──────────────────┤              
   │     STATE 126    │      STATE 126      │    STATE 127     │              
   │   (transition)   │    (transition)     │    (warmup)      │              
   │                  │                     │                  │              
──────────────────────────────────────────────────────────────────────────────
```

## Key Telemetry Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `MonLogin` | Captures login failures | error, state, error_count |
| `MonFabricApi` | Role change XEvents | begin/end_change_role |
| `SqlFailovers` | Completed failover summary | FailoverStartTime, FailoverEndTime |
| `LoginOutages` | Platform outage reporting | OutageType, durationSeconds |
| `MonSQLSystemHealth` | SQL error log messages | Recovery messages |

## Key XEvents for Role Changes

### hadr_fabric_api_replicator_begin_change_role

Fired when role change begins. Key fields:
- `new_role` / `new_role_desc`: Target role (Primary/Secondary)
- `current_state` / `current_state_desc`: Current replica state
- `work_id`: Correlates with end event
- `process_id`: SQL process

### hadr_fabric_api_replicator_end_change_role

Fired when role change completes. Key fields:
- `result` / `result_desc`: Success or failure reason
- `work_id`: Must match begin event
- `process_id`: Must match begin event

## Troubleshooting Checklist

- [ ] Confirm error 40613 state 126 in MonLogin
- [ ] Calculate error duration (< 30s = normal, > 2min = problem)
- [ ] Check SqlFailovers for corresponding failover
- [ ] Verify role change completed (begin/end events paired)
- [ ] Check recovery completed (MonSQLSystemHealth)
- [ ] Review LoginOutages for impact assessment


## Common Mitigations

| Scenario | Mitigation |
|----------|------------|
| Normal transient | No action - document as expected behavior - canned RCA |
| Prolonged failover | Use failover skill for root cause |
| Stuck reconfiguration | May require SF intervention - Additional Troubleshooting |
| Repeated failures | Identify underlying node/storage issues |

## References

- [Azure SQL Database high availability](https://learn.microsoft.com/en-us/azure/azure-sql/database/high-availability-sla)
- [Troubleshoot transient connection errors](https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-connectivity-issues)