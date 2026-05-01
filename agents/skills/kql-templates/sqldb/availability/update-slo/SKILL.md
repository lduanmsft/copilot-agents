---
name: update-slo
description: Diagnoses Update SLO (Service Level Objective) stuck or failed operations, including tier change timeouts, scaling failures, and availability impact during SLO changes. Analyzes UpdateSloStateMachine FSM state transitions, management operations, replication lag, seeding progress, and long-running transactions. Covers ContinuousCopyV2, DetachAttach, and InPlace update modes. Related TSGs include GEODR0004, DBPOOLSCALE0009, DBPOOLSCALE0017.
---

# Update SLO Diagnostics

This skill analyzes Update SLO operations, identifies stuck or failed tier changes, and diagnoses availability issues during service tier modifications. It inspects the UpdateSloStateMachine finite state machine (FSM) transitions, identifies the stuck state, and routes to appropriate mitigations.

## Scope

- Update SLO stuck/hanging operations (GEODR0004, DBPOOLSCALE0009)
- Update SLO failures and timeouts
- Availability impact during SLO changes
- Scaling operation issues (tier upgrade/downgrade)
- Long-running Update SLO investigations (DBPOOLSCALE0017)

## Required Information

The following information is needed to begin analysis (obtained from ICM or provided directly):

| Parameter | Description | Example |
|-----------|-------------|---------|
| LogicalServerName | Logical server name | `my-server` |
| LogicalDatabaseName | Logical database name | `my-db` |
| StartTime | Investigation start time (UTC) | `2026-01-01 02:00:00` |
| EndTime | Investigation end time (UTC) | `2026-01-01 10:00:00` |
| KustoClusterUri | From execute-kusto-query skill | (resolved dynamically) |
| KustoDatabase | From execute-kusto-query skill | (resolved dynamically) |

**Derived during analysis:**
- `request_id` — From USLO200 (Step 1, always available)
- Source and target AppNames — From USLO100 (Step 2, available for longer-running operations)
- `database_usage_status` — `Active` (source) vs `UpdateSloTarget` (target) — from USLO100 (Step 2)
- `AppName` / `ClusterName` — From get-db-info skill

## Workflow

### Step 1: Validate Inputs and Get Management Operation Overview

Confirm all required parameters are available: `LogicalServerName`, `LogicalDatabaseName`, `StartTime`, `EndTime`, `KustoClusterUri`, `KustoDatabase`. If any are missing, stop and request them.

Run query **USLO200** to find the management operation(s) for this database.

- Identify the `request_id` for the Update SLO operation
- Check `event` column: `management_operation_success`, `management_operation_failure`, `management_operation_timeout`, or ongoing
- Note `elapsed_time` — if operation is still running, this shows how long it has been in progress
- If the operation completed, note whether it succeeded or failed and the total duration

### Step 2: Identify Source and Target

Run query **USLO100** to check for source/target database snapshots.

- Look for rows with `database_usage_status = 'UpdateSloTarget'` — this confirms an Update SLO was captured by the snapshot
- Extract source AppName (`database_usage_status = 'Active'`) and target AppName (`database_usage_status = 'UpdateSloTarget'`)
- Note the `service_level_objective` for both source and target to determine upgrade vs downgrade direction
- **Note:** Fast-completing operations may finish before `MonAnalyticsDBSnapshot` captures them. If no `UpdateSloTarget` rows are found but USLO200 confirms the operation, proceed with FSM analysis using the `request_id` from Step 1

### Step 3: Analyze FSM State Transitions

Run query **USLO210** using the `request_id` from Step 1.

- This shows the UpdateSloStateMachine state transitions with duration between each state
- Identify the **current state** (last `new_state` value) — this is the stuck state if the operation is ongoing
- Calculate duration in each state
- Flag any state with duration > expected timing (see [references/principles.md])
- Identify the FSM type: `UpdateSloStateMachine`, `LogicalDatabaseStateMachine`, `FabricServiceStateMachine`

### Step 4: Check for Exceptions and Errors

Run query **USLO300** to find management exceptions for this request.

- Look for `exception_type` and `stack_trace` values
- Common exceptions: `System.TimeoutException`, `FiniteStateMachineLockTimeoutException`, NodeAgent failures
- If `last_exception` contains `NodeAgent` → database may be unavailable, see [references/principles.md] Section "Database Unavailable During Update SLO"
- Cross-reference exception timestamps with FSM state transitions from Step 3

### Step 5: Assess Replication and Seeding (if applicable)

If the Update SLO mode is **ContinuousCopyV2** (copy-based):

Run query **USLO400** to check replication status between source and target.

- Look at `replication_lag_sec` — high values indicate the target cannot keep up
- Check `replication_state` for issues
- If stuck in `CheckingRedoQueueSize` or `WaitingForRedoQueueToDrain`, this indicates a redo queue drain issue (see GEODR0004.3 in [references/knowledge.md])

Run query **USLO500** for SQL system health errors on source and target AppNames.

- Look for Error 823, 824, 825 (I/O errors) or Error 9001 (log errors)
- Check for "Nonqualified transactions are being rolled back" messages (rollback stuck — GEODR0004.4)

### Step 6: Check SLO Transition History

Run query **USLO600** to see historical SLO transitions for this database.

- This shows SLO values over time with timestamps
- Confirms whether the SLO change actually applied or reverted
- Useful for understanding if the operation was retried multiple times

### Step 7: Route to Specific Sub-TSG Based on Stuck State

Using the stuck state from Step 3 and exceptions from Step 4, apply the routing table in [references/principles.md] to identify the specific sub-TSG and mitigation.

| Stuck State | Sub-TSG | Action |
|-------------|---------|--------|
| CheckingRedoQueueSize / WaitingForRedoQueueToDrain | GEODR0004.3 | User error (SLO downgrade with heavy writes) |
| KillingLongTransactionsBeforeCopying / BeforeReattach | GEODR0004.24 | Resource constraints or unavailable DB |
| WaitingForRoleChange | GEODR0004.4 / .6 / .27 | Rollback stuck, long recovery, or delayed startup |
| WaitingForSourcePhysicalDatabaseDrop | GEODR0004.1 | Fabric service drop stuck |
| WaitingForReplicationModeUpdate | GEODR0004.11 | Replication mode update stuck |
| NotifyingCompletion + CompleteHekatonSloDowngrade | GEODR0004.12 | Hekaton SLO downgrade issue |
| WaitingForTargetSqlInstanceCreation | GEODR0004.18 | Target creation stuck in resolving |
| UpdatingRgSloPropertyBag | Escalate to Performance | Performance team issue |
| UpdatingGeoDrLinks | GEODR0004.25 | GeoDR link update stuck |
| Copying (general) | GEODR0004 main | Kill process, cancel and re-issue |

### Step 8: Generate Report

Format the output following [references/output.md]:
- State Machine Timeline with duration per state
- Stuck state identification with 🚩 markers
- Root cause and recommended mitigation
- Link to relevant sub-TSG

## Key Terms

- **UpdateSloStateMachine**: The FSM that manages SLO change operations
- **ContinuousCopyV2**: Update SLO mode using GeoDR stack to copy data (most common)
- **DetachAttach**: Update SLO mode for remote storage DBs (attach/detach blobs)
- **InPlace**: Rare Update SLO mode for Premium SLOs on same instance
- **request_id**: Unique identifier for each management operation
- See [references/knowledge.md] for full definitions

## Query Execution Format

Refer to [references/queries.md] for all queries with placeholders.

## Related Skills

- **failover**: If Update SLO causes a failover event
- **quorum-loss**: If Update SLO triggers quorum loss
- **node-health**: If the stuck state is related to node infrastructure issues

## Related Categories

- Category 7: Logical Master Issues - Master DB stuck in update SLO
- Category 9: Control Plane & Management

## Routing Teams

- `ComponentCode.ControlPlane` — Default for Update SLO issues
- `GeoDR` — For GEODR0004 sub-TSG issues (stuck states in GeoDR flow)
- `Performance` — For UpdatingRgSloPropertyBag issues
- `Hyperscale Migration` — If GP/BC → Hyperscale migration stuck in Copying

## Reference

- [knowledge.md](references/knowledge.md) — Definitions, concepts, and related documentation
- [principles.md](references/principles.md) — Debug principles and escalation criteria
- [queries.md](references/queries.md) — Kusto queries with placeholders
- [output.md](references/output.md) — Investigation report template
