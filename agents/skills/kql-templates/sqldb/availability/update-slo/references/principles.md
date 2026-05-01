# Debug Principles for Update SLO Issues

## Principle 1: Confirm Update SLO is Actually Stuck

Very often "Update SLO stuck" alerts are **false alarms** and self-heal shortly after the incident is created.

Before deep investigation:
1. Check if the Update SLO completed between alert time and investigation time (USLO200)
2. If `management_operation_success` event exists → the operation completed, confirm with customer
3. If no `UpdateSloTarget` rows in USLO100 → the operation is no longer in progress

## Principle 2: Identify the Stuck State First

The **stuck state** determines the root cause and mitigation path. Always identify it before proceeding.

1. Run USLO210 (FSM state transitions) to get the chronological state progression
2. The **last `new_state`** value is the current/stuck state
3. Calculate duration in each state
4. Apply the routing table below to determine next steps

## Principle 3: State Routing Table

| Stuck State | Expected Duration | 🚩 Stuck If | Sub-TSG | Typical Root Cause |
|-------------|-------------------|-------------|---------|-------------------|
| Pending | < 5 min | > 30 min | Check control plane overload (USLO800) | FSM queue backlog |
| CreatingTargetSqlInstance | < 10 min | > 30 min | GEODR0004.18 | Target stuck in Resolving |
| WaitingForTargetSqlInstanceCreation | < 15 min | > 1 hour | GEODR0004.18 | SF provisioning issue |
| Copying | Varies by DB size (~1 min/1.5 GB) | > 12 hours for small DBs | GEODR0004.9 | Slow data transfer |
| CheckingRedoQueueSize | < 30 min | > 2 hours | GEODR0004.3 | SLO downgrade with heavy writes |
| WaitingForRedoQueueToDrain | < 30 min | > 2 hours | GEODR0004.3 | Target cannot catch up |
| KillingLongTransactionsBeforeCopying | < 30 min | > 1 hour | GEODR0004.24 | Long transactions, resource constraints |
| KillingLongTransactionsBeforeReattach | < 30 min | > 1 hour | GEODR0004.24 | Long transactions (DetachAttach mode) |
| DisablingConnectionsToSourceDatabase | < 5 min | > 30 min | Check exceptions | Connection kill issues |
| ChangingRoleOnSource | < 10 min | > 30 min | GEODR0004.4 | Rollback stuck |
| WaitingForRoleChange | < 15 min | > 1 hour | GEODR0004.4/.6/.27 | Rollback, recovery, delayed startup |
| WaitingForSourcePhysicalDatabaseDrop | < 10 min | > 1 hour | GEODR0004.1 | Fabric service drop timeout |
| WaitingForReplicationModeUpdate | < 10 min | > 1 hour | GEODR0004.11 | Replication mode stuck |
| NotifyingCompletion | < 5 min | > 30 min | GEODR0004.12 | Hekaton SLO downgrade failure |
| UpdatingRgSloPropertyBag | < 5 min | > 30 min | Escalate to Performance | Performance team issue |
| UpdatingGeoDrLinks | < 10 min | > 30 min | GEODR0004.25 | GeoDR link update issue |

## Principle 4: Check Exception Context

Exceptions in USLO300 provide critical diagnostic context:

| Exception Pattern | Interpretation | Action |
|-------------------|---------------|--------|
| `stack_trace` contains `NodeAgent` | Database is unavailable | Check if geo-secondary exists → GEODRSOP0003 (reseed); otherwise TRDB0002 |
| `exception_type = 'System.TimeoutException'` | Fabric operation timed out | Check GEODR0004.1 for physical DB drop stuck |
| `stack_trace` contains `CompleteHekatonSloDowngrade` | Hekaton downgrade failed | GEODR0004.12 |
| `stack_trace` contains `FiniteStateMachineLockTimeoutException` | FSM lock contention | Check for concurrent operations on same database |
| `event = 'fsm_executed_action_failed'` with repeated entries | Action is failing and retrying | Check `action` column for which step, and `stack_trace` for details |

## Principle 5: Database Unavailable During Update SLO

If the database becomes unavailable during Update SLO:

1. Check USLO300 for `NodeAgent` errors in stack traces
2. If database has geo-secondary → reseed using GEODRSOP0003
3. If no geo-secondary → start with TRDB0002 (standard database troubleshooting)
4. If stuck in KillingLongTransactions and DB unavailable → GEODR0004.24

## Principle 6: ContinuousCopyV2 Redo Queue Analysis

When stuck in `CheckingRedoQueueSize` or `WaitingForRedoQueueToDrain`:

1. This is typically a **user error** — SLO downgrade while customer has heavy write workload
2. The target has lower compute resources and cannot keep up with source writes
3. **Normal behavior**: Redo queue should drain within 30 minutes for most databases
4. **🚩 Stuck if**: Redo queue not draining after 2+ hours
5. **Mitigation**: Contact customer to reduce write traffic, then cancel (GEODRSOP0002) and re-issue

## Principle 7: GP/BC to Hyperscale Migration

If the Update SLO is stuck in `Copying` state and the target SLO is Hyperscale:

1. This is a **migration operation**, not a standard Update SLO
2. Escalate to the **Hyperscale Migration** team
3. Do NOT attempt standard GEODR0004 mitigations

## Principle 8: Expected Timings Summary

| Phase | Normal | Warning | Critical |
|-------|--------|---------|----------|
| Total Update SLO (small DB, < 1 GB) | < 30 min | 30 min–2 hours | > 2 hours |
| Total Update SLO (medium DB, 1–100 GB) | < 2 hours | 2–6 hours | > 6 hours |
| Total Update SLO (large DB, > 100 GB) | < 6 hours | 6–12 hours | > 12 hours |
| Any single FSM state | < 30 min | 30 min–1 hour | > 1 hour |
| Pending to first active state | < 5 min | 5–30 min | > 30 min |
| Redo queue drain | < 30 min | 30 min–2 hours | > 2 hours |
| Role change | < 15 min | 15 min–1 hour | > 1 hour |
| Physical DB drop | < 10 min | 10 min–1 hour | > 1 hour |

## Analysis Workflow

For each Update SLO investigation:

1. Execute queries USLO100, USLO200, USLO210, USLO300 (minimum required set)
2. Execute USLO400, USLO500 if ContinuousCopyV2 mode is identified
3. Execute USLO600 to confirm SLO transition history
4. Execute USLO700 only if stuck in drop states
5. Execute USLO800 if control plane overload is suspected
6. Compare results against expected timings above
7. Mark states with ✅ (normal) or 🚩 (stuck/problematic)
8. For 🚩 states:
   - Include actual query with parameters in output
   - Include result summary
   - Apply routing table (Principle 3) to identify sub-TSG
   - Recommend specific mitigation
9. Do NOT speculate — base conclusions only on observed data and these principles
