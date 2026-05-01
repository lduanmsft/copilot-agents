# Error 40613 State 127 - Knowledge Base

## Error Definition

**Error 40613**: "Database '%.*ls' on server '%.*ls' is not currently available."

**State 127**: Cannot open database during warmup - The role change has completed but the database is still performing recovery (redo/undo) and cannot accept connections yet.

## When This Error Occurs

State 127 is raised when:

1. **Database Recovery Running**: The database is replaying committed transactions (redo) or rolling back uncommitted transactions (undo)
2. **Post-Failover Warmup**: The new primary is initializing after a successful role change
3. **Tempdb Recovery**: System databases are still recovering

## Relationship with State 126

State 127 typically follows state 126 in a failover sequence:

| Phase | State | What's Happening |
|-------|-------|------------------|
| 1. Role Change | **126** | Replica transitioning from secondary to primary |
| 2. Warmup | **127** | Role change complete, database recovery in progress |
| 3. Available | None | Recovery complete, connections accepted |

## Comparison with Related States

| State | Name | Condition | Typical Duration |
|-------|------|-----------|------------------|
| **126** | Database in transition | Role change actively executing | < 30 seconds |
| **127** | Cannot open during warmup | Role change complete, database warming up | 30 sec - 5 min |
| **129** | HADR not available | Database not PRIMARY or SECONDARY state | Variable |
| **84** | Cannot access master | User DB can't reach logical master | Variable |

## Database Recovery Phases

After a role change completes, the new primary performs crash recovery:

```
Recovery Process:
──────────────────────────────────────────────────────────────────────────────
                                                                              
  Phase 1           Phase 2              Phase 3            Complete          
   │                  │                     │                  │              
   ▼                  ▼                     ▼                  ▼              
[Analysis]      [Redo Phase]          [Undo Phase]       [DB Available]   
                                                                              
   │                  │                     │                  │              
Determine        Replay               Roll back           Accept           
what needs       committed            uncommitted         connections       
recovery         transactions         transactions                          
   │                  │                     │                  │              
 ~1-2s            1s - 5min            1s - 10min                            
──────────────────────────────────────────────────────────────────────────────
```

### Phase 1: Analysis
- Very fast (typically < 2 seconds)
- Determines the recovery scope

### Phase 2: Redo
- Replays all committed transactions from the log
- Duration depends on:
  - Size of transaction log
  - Amount of activity before failover
  - Parallel redo capability (enabled by default)
- Typical: 1-60 seconds for most workloads

### Phase 3: Undo
- Rolls back any uncommitted transactions
- Duration depends on:
  - Number and size of uncommitted transactions
  - Long-running transactions before failover
- Can be lengthy if large transactions were in progress

## Expected vs. Problematic Scenarios

### Expected (No Action Required)

- **Normal failover**: State 127 errors for 30-60 seconds during recovery
- **Large transaction log**: Up to 2-3 minutes for very active databases
- **SLO change**: Brief warmup after tier change operations

### Problematic (Requires Investigation)

| Symptom | Possible Cause | Investigation |
|---------|---------------|---------------|
| Errors > 5 minutes | Stuck recovery | Check `MonSQLSystemHealth` for errors |
| Recovery never completes | Database corruption or storage issue | Check `MonSQLSystemHealth`, TempDB health |
| Repeated state 127 | Frequent failovers | Use `freq-failover` skill |
| Tempdb delays | DropTempObjectsOnDBStartup | Check temp object count |

## Factors Affecting Warmup Duration

| Factor | Impact | Why |
|--------|--------|-----|
| **Database activity before failover** | High | More transactions to redo |
| **Long-running transactions** | High | More work to undo |
| **Non-CTR/Non-ADR transactions** | High | Require full undo during recovery, no instant rollback |
| **Database size** | Medium | Larger databases may have more log |
| **SLO tier** | Medium | Higher tiers have more resources |
| **Storage performance** | Medium | I/O throughput affects redo speed |
| **Temp object count** | Low-Medium | Cleanup during tempdb recovery |

## Key Telemetry Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `MonLogin` | Captures login failures | error, state, error_count |
| `MonFabricApi` | Role change and write status | end_change_role, write_status |
| `SqlFailovers` | Completed failover summary | `FailoverStartTime`,`FailoverEndTime` |
| `LoginOutages` | Platform outage reporting | `OutageType`,`durationSeconds` ,`OutageReasonLevel1`,`OutageReasonLevel2` |
| `MonSQLSystemHealth` | Recovery and error messages | `error_id`,`message` |

## Key Messages in MonSQLSystemHealth

### Recovery Start
```
Starting up database {physical_database_id}
```

### Parallel Redo (Phase 2)
```
Parallel redo is started for database '{physical_database_id}'
Parallel redo is shutdown for database '{physical_database_id}'
Error 3450: "Recovery of database '%.*ls' (%d) is %d%% complete (approximately %d seconds remain). Phase %d of 3. This is an informational message only. No user action is required."
```

### Recovery Complete
```
"Recovery completed for database %ls (database ID %d) in %I64d second(s) (analysis %I64d ms, redo %I64d ms, undo %I64d ms [system undo %I64d ms, regular undo %I64d ms].) ADR-enabled=%d, Is primary=%d, OL-Enabled=%d. This is an informational message only. No user action is required."
```

### Tempdb Recovery
```
Recovery completed for database tempdb (database ID 2) in X second(s)
```

## Troubleshooting Checklist

- [ ] Confirm error 40613 state 127 in MonLogin
- [ ] Calculate error duration (< 1min = normal, > 5min = problem)
- [ ] Check SqlFailovers for preceding failover
- [ ] Verify role change completed successfully (MonFabricApi)
- [ ] Check recovery progress (MonSQLSystemHealth)
- [ ] Look for "Recovery completed" message
- [ ] Verify write status was granted
- [ ] Review LoginOutages for impact assessment

## Common Mitigations

| Scenario | Mitigation |
|----------|------------|
| Normal warmup | No action - document as expected behavior - canned RCA |
| Prolonged redo | Monitor, may be normal for active databases |
| Long undo | Check for long-running transactions before failover |
| Tempdb delays | Check temp object count, consider cleanup |
| Stuck recovery | Escalate to failover skill, may need replica restart |
| Storage issues | Check XStore health, disk metrics |
| Readable Secondaries | Activity can block redo. |

## Canned RCA Template

For normal state 127 errors (< 1 minute):

```
Root Cause: Normal database warmup following failover

Between {StartTime} and {EndTime}, the database experienced brief 
unavailability (state 127 errors) while warming up after a failover. 
This is expected behavior.

Timeline:
- Failover started: {FailoverStartTime}
- Failover completed: {FailoverEndTime}
- Recovery completed: {RecoveryTime}
- Total warmup: {WarmupDuration} seconds

This duration is within normal parameters. The database recovery 
completed successfully and the database became available.

Recommendation: No action required. For applications sensitive to 
failover duration, consider implementing retry logic with exponential 
backoff as documented at:
https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-connectivity-issues
```

## References

- [Azure SQL Database high availability](https://learn.microsoft.com/en-us/azure/azure-sql/database/high-availability-sla)
- [Troubleshoot transient connection errors](https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-connectivity-issues)
- [Accelerated database recovery](https://learn.microsoft.com/en-us/sql/relational-databases/accelerated-database-recovery-concepts)