# Terms and Concepts for Update SLO

## General Concepts

1. **Update SLO (Service Level Objective)**: The process of changing a database's service tier, compute size, or storage configuration. Also known as tier change, scaling, or SLO change.

2. **Management Operation**: An Update SLO is triggered by a management operation (typically customer-initiated via tier/SLO change, or occasionally by internal load-balancing tasks). Each operation is tracked by a `request_id`. Visible in `MonManagementOperations` (180-day retention) and `MonManagement` (180-day retention for detailed FSM events).

3. **UpdateSloStateMachine**: The finite state machine (FSM) that manages the SLO change workflow. Transitions through states like `Pending`, `Copying`, `WaitingForRoleChange`, `NotifyingCompletion`, etc.

4. **LogicalDatabaseStateMachine**: The parent FSM that manages the database lifecycle. Transitions to `UpdateSloInProgress` during an Update SLO and back to `Ready` on completion.

5. **FabricServiceStateMachine**: Sub-FSM for Service Fabric operations during Update SLO (e.g., creating/dropping fabric services).

## Update SLO Modes

There are three modes for performing an Update SLO:

| Mode | Description | Speed | When Used |
|------|-------------|-------|-----------|
| **ContinuousCopyV2** | Uses GeoDR stack to copy data to a new instance. Source keeps serving, target catches up via replication. | Varies by SLO size — small SLOs (Basic, S0–S2) are much slower due to limited max IO rates; large SLOs can be fast. Can take hours for large DBs. | Most common. Cross-tier changes, cross-instance changes. |
| **DetachAttach** | Creates a new physical database pointing to original remote storage blobs. Source detaches files, target attaches them. | Fast for small DBs, can get stuck killing long transactions | Remote storage DBs (Basic/Standard SLOs). |
| **InPlace** | Same instance is updated with new resource allocations. No data movement. | Very fast (seconds to minutes) | Rare. Only Premium SLOs (P1, P4, P11) on same instance. |

**How to determine the mode:**
- Query `update_slo_requests` CMS table and check the `mode` column
- Or infer from the FSM states: `Copying` states suggest ContinuousCopyV2, `ReattachingToTarget` states suggest DetachAttach

## Common UpdateSloStateMachine States

### Normal Flow States (ContinuousCopyV2)

| State | Description | Expected Duration |
|-------|-------------|-------------------|
| Pending | Operation queued, waiting to start | Seconds to minutes |
| CreatingTargetSqlInstance | Creating the new SQL instance for the target SLO | Minutes |
| WaitingForTargetSqlInstanceCreation | Waiting for SF to provision the target | Minutes |
| Copying | Data copy from source to target is in progress | Minutes to hours (depends on DB size) |
| CheckingRedoQueueSize | Checking if redo queue has drained on target | Minutes |
| WaitingForRedoQueueToDrain | Waiting for target to catch up with source writes | Minutes to hours |
| DisablingConnectionsToSourceDatabase | Disconnecting users from source before role switch | Seconds |
| KillingLongTransactionsBeforeCopying | Terminating long-running transactions before copy | Minutes |
| ChangingRoleOnSource | Switching the source to secondary role | Minutes |
| WaitingForRoleChange | Waiting for the role change to complete | Minutes |
| NotifyingCompletion | Notifying dependent systems of completion | Seconds |
| WaitingForSourcePhysicalDatabaseDrop | Waiting for the old physical DB to be dropped | Minutes |
| UpdatingGeoDrLinks | Updating GeoDR replication links if applicable | Minutes |

### Normal Flow States (DetachAttach)

| State | Description | Expected Duration |
|-------|-------------|-------------------|
| KillingLongTransactionsBeforeReattach | Terminating transactions before detach | Minutes |
| DetachingSource | Detaching files from source instance | Minutes |
| ReattachingToTarget | Attaching files to target instance | Minutes |

## Common Stuck States and Causes

| Stuck State | Common Cause | Sub-TSG |
|-------------|-------------|---------|
| CheckingRedoQueueSize | SLO downgrade with heavy customer writes; target cannot keep up | GEODR0004.3 |
| KillingLongTransactionsBeforeCopying | Long-running transactions cannot be rolled back due to resource constraints | GEODR0004.24 |
| KillingLongTransactionsBeforeReattach | Same as above but for DetachAttach mode | GEODR0004.24 |
| WaitingForRoleChange | Rollback stuck, long recovery, or delayed startup | GEODR0004.4, .6, .27 |
| WaitingForSourcePhysicalDatabaseDrop | Fabric service drop timing out | GEODR0004.1 |
| WaitingForReplicationModeUpdate | Replication mode change stuck | GEODR0004.11 |
| NotifyingCompletion | CompleteHekatonSloDowngrade failure | GEODR0004.12 |
| WaitingForTargetSqlInstanceCreation | Target stuck in Resolving state | GEODR0004.18 |
| UpdatingRgSloPropertyBag | Performance team issue | Escalate to Performance |
| UpdatingGeoDrLinks | GeoDR link update stuck | GEODR0004.25 |
| Copying (with GP/BC → Hyperscale) | Migration issue, not standard Update SLO | Escalate to Hyperscale Migration |

## Alert Thresholds

- **DBPOOLSCALE0009 / MS0011**: Fires when an Update SLO has not completed within approximately **12 hours**
- **DBPOOLSCALE0017 / MSSOP0022**: Long-running Update SLO investigation alert
- Very often these alerts are **false alarms** and self-heal shortly after the incident is created

## Cancellation and Mitigation Commands

| Command | Purpose |
|---------|---------|
| `Cancel-ManagementOperation -OperationId {request_id}` | Cancel the stuck Update SLO operation |
| `Set-Database` (via PowerShell) | Re-issue the SLO change after cancellation |
| `Set-UpdateSloProperty` (change_role_start_time) | For GEODR0004.27 — set future time to extend timeout |
| GEODRSOP0001 | Kill SQL process on primary replica of affected physical database |
| GEODRSOP0002 | Cancel and re-issue Update SLO |
| GEODRSOP0003 | Reseed geo-secondary |

## Telemetry Tables

| Table | Retention | Purpose |
|-------|-----------|---------|
| `MonManagementOperations` | 180 days | High-level operation tracking (request_id, type, duration, errors) |
| `MonManagement` | 180 days | Detailed FSM state transitions (state_machine_type, old/new state, exceptions) |
| `MonManagementExceptions` | 180 days | Exception details for management operations |
| `MonAnalyticsDBSnapshot` | 45 days | Database configuration, SLO, state, usage status |
| `MonDmContinuousCopyStatus` | 28 days | Replication lag between source and target |
| `MonSQLSystemHealth` | 60 days | SQL error messages and system health events |
| `MonDbSeedTraces` | 28 days | Database seeding operations and progress |
| `MonNodeAgentEvents` | 180 days | NodeAgent activity for correlation |

## Related TSGs

| TSG ID | Title | When to Use |
|--------|-------|-------------|
| GEODR0004 | Stuck Update SLO | Main TSG — use XTS view `GEODR0004_StuckUpdateSlo.xts` |
| GEODR0004.1 | Physical database drop stuck | State: WaitingForSourcePhysicalDatabaseDrop |
| GEODR0004.2 | Stuck in non-GeoDR state | States: WaitingForTargetSqlInstanceCreation, NotifyingCompletion, KillingLongTransactions, UpdatingRgSloPropertyBag |
| GEODR0004.3 | Stuck waiting for redo queue to drain | State: CheckingRedoQueueSize, WaitingForRedoQueueToDrain |
| GEODR0004.4 | Rollback stuck | "Nonqualified transactions are being rolled back" errors |
| GEODR0004.6 | Delayed startup | WaitingForRoleChange when startup is delayed by rollback or recovery |
| GEODR0004.9 | Slow data transfer to target | Copying state with slow progress |
| GEODR0004.11 | Stuck in WaitingForReplicationModeUpdate | Replication mode change stuck |
| GEODR0004.12 | Failing on CompleteHekatonSloDowngrade | NotifyingCompletion with Hekaton error |
| GEODR0004.18 | Target stuck in Resolving state | WaitingForTargetSqlInstanceCreation with target in Resolving |
| GEODR0004.24 | Stuck Killing Long Transactions | KillingLongTransactionsBeforeCopying/BeforeReattach |
| GEODR0004.25 | Stuck in UpdatingGeoDrLinks | GeoDR link update stuck |
| GEODR0004.27 | Timing out due to delayed startup | Startup delayed by fulltext operations |
| DBPOOLSCALE0009 | Stuck Update SLO (DB available) | Alert: 12-hour threshold, database still accessible |
| DBPOOLSCALE0017 | Long Running Update SLO | Investigation-level TSG for long operations |
| GEODR0008 | Log full due to stuck Update SLO on forwarder | Transaction log full scenario |

## Related Documentation

All source materials used to build and maintain this skill. These URLs are fetched
during skill creation and updates to extract knowledge, principles, and queries.

### Internal Documentation (eng.ms / ADO Wiki)
- [GEODR0004 - Stuck Update SLO](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-et1-geodr/geodr/geodr0004-stuck-update-slo)
- [DBPOOLSCALE0009 / MS0011 - Stuck Update SLO DB Available](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-ms/ms-tsgs/ms0011-stuck-update-slo-db-available)
- [DBPOOLSCALE0017 / MSSOP0022 - Investigating Long Running Update SLO](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-ms/ms-tsgs/mssop0022-investigating-long-running-update-slo)
- [GEODR0004.3 - Stuck Waiting for Redo Queue to Drain](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-et1-geodr/geodr/geodr0004-stuck-update-slo/geodr0004-3-stuck-waiting-for-redo-queue-to-drain)
- [GEODR0004.24 - Stuck Killing Long Transactions](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-et1-geodr/geodr/geodr0004-stuck-update-slo/geodr0004-24-update-slo-stuck-killing-long-transactions)
- [GEODR0004.4 - Rollback Stuck](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-et1-geodr/geodr/geodr0004-stuck-update-slo/geodr0004-4-rollback-stuck)
- [GEODR0004.1 - Physical Database Drop Stuck](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-et1-geodr/geodr/geodr0004-stuck-update-slo/geodr0004-1-physical-database-drop-stuck)
- [DBPOOLSCALE0002 - Investigation of Update SLO Workflows in Sterling](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-ms/ms-tsgs/dbpoolscale0002-investigation-of-update-slo-workflows-in-sterling)
