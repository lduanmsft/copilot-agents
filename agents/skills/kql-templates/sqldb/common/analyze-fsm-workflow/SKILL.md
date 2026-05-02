---
name: analyze-fsm-workflow
description: Core FSM workflow analysis engine. Given a request_id (or context like fabric cluster/server name), discovers the operation, maps the FSM workflow tree, detects stuck state machines, identifies bottlenecks, analyzes child workflows, and produces an RCA log. Includes Control Plane extensions for two-layer telemetry analysis (MonManagementOperations + MonManagement), MOSM throttling detection, deterministic vs transient error classification, and Management Service resource utilization. Used by domain-specific agents (provisioning, GeoDR, etc.).
---

# Analyze FSM Workflow

Shared engine for evidence-based bottleneck analysis of FSM workflows.

## Required Parameters

- `{request_id}` — GUID of the management operation. OR:
- `{LogicalServerName}` — server name for context-based queries. OR:
- `{FabricClusterTR}` — fabric cluster name (e.g., `tr513`) for ring-level queries
- `{StartTime}`, `{EndTime}` — (optional) time window for scoping queries

## Prerequisites

Determine the correct Kusto cluster BEFORE running queries.
See the **Query Execution** section in [references/queries.md](references/queries.md) for cluster routing, fan-out, and tool instructions.

## Queries

All Kusto queries are defined in [references/queries.md](references/queries.md) with query IDs (FSM001–FSM070, SW110–SW610).
Reference queries by ID when executing them.

---

## Domain Concepts

### State Machine (FSM)

A state machine (FSM) is a logical unit that manages transitions between states of an entity.
Each state machine type is suffixed with `StateMachine` (e.g., `ManagementOperationStateMachine`).

A **workflow** is a chain of FSMs working together to complete a larger task.
It emerges when one FSM triggers another as a child.

### Workflow Position

Workflow position is a hierarchical identifier tracking parent-child relationships between FSMs:

- `/0/` — Root FSM (e.g., `ManagementOperationStateMachine`)
- `/0/0/` — Child triggered by `/0/`
- `/0/0/0/` — Grandchild triggered by `/0/0/`

**Parent-Child Rule**: A workflow position is a parent of another if it is a prefix (e.g., `/0/0/` is parent of `/0/0/0/`).

### Two-Layer Telemetry (Control Plane)

Control Plane operations have **two telemetry layers**. Mixing them up is the #1 source of false conclusions.

| Aspect | `MonManagementOperations` | `MonManagement` |
|--------|--------------------------|------------------|
| **Level** | Operation-level (API request lifecycle) | Workflow/FSM-level (internal state machine events) |
| **Events** | `management_operation_start`, `_timeout`, `_cancel`, `_failure`, `_success` | `fsm_executing_action`, `fsm_fired_event_failed`, `fsm_creating_state_machine`, etc. |
| **Error info** | `error_code`, `error_message` — **often empty for FSM timeouts** | `message`, `exception_type`, `stack_trace` — **contains the actual exception** |
| **Use for** | Request timeline, success rate, operation parameters | Actual error diagnosis, exception stack traces, retry patterns, FSM state transitions |

**Key rules:**
1. Empty `error_code`/`error_message` on `MonManagementOperations` does **NOT** mean "no error" — the error is at the FSM layer in `MonManagement`
2. Always query **both tables** when investigating failures
3. The `message` column in `MonManagement` is the **most reliable** source of exception details
4. For timeout events: `MonManagementOperations` tells you the operation timed out; `MonManagement` `fsm_fired_event_failed` events tell you **WHY**
5. The `operation_parameters` column is progressively enriched — derived parameters like `IsTridentNative` are only present on **non-start** events (`management_operation_timeout`, `management_operation_failure`, `management_operation_success`, `management_operation_cancel`). Never rely on the `management_operation_start` event for these values. See [knowledge.md](references/knowledge.md#operation-parameters) for details.

### MOSM Architecture

MOSM (Management Operation State Machine) has built-in mechanisms for rate limiting, throttling, and queueing. Do NOT claim these mechanisms are absent without verifying.

- **Release throttling**: Operations go through a release gate (`management_operation_released` event)
- **Concurrency limits**: MOSM limits concurrent operations per operation type, per cluster, and per tenant ring
- **Queueing**: Operations can be queued when concurrency limits are reached

### Keys and Multiple FSM Instances

The same `state_machine_type` can have multiple instances at the same level, each with a different `keys` value.
Use `(state_machine_type, keys, workflow_position)` to uniquely identify an FSM instance.

Example tree:
```text
ManagementOperationStateMachine (/0/)
│   Key: 840E7DE0-…
│   State: WaitingForOperationToComplete
│
└── VldbGeoDrContinuousCopyStateMachine (/0/0/)
    │   Key: 3ab7-…,41424796a
    │   State: PreparingSecondaryDatabaseForChangePrimary
    │
    └── VldbComputeDatabaseStateMachine (/0/0/0/)
        │   Key: 73d8246d225f
        │   State: NotifyingPhysicalDbForFabricPropertyUpdate
        │
        ├── FabricNameStateMachine (/0/0/0/0/) — UpdatingFabricProperties
        ├── FabricNameStateMachine (/0/0/0/1/) — UpdatingFabricProperties
        ├── FabricNameStateMachine (/0/0/0/2/) — WaitingForFabricPropertyUpdate
        └── FabricNameStateMachine (/0/0/0/3/) — Ready
```

Multiple instances at the same level (e.g., four `FabricNameStateMachine` at `/0/0/0/N/`) represent parallel work — each with its own key and state. The parent waits for ALL children to reach a terminal state.

---

## ⛔ Anti-Patterns — NEVER Do These

### 1. Concluding "No Errors" From Empty Operation-Level Fields
- **NEVER** conclude "no errors found" when `error_code` and `error_message` are empty on `MonManagementOperations`
- **Rule**: ALWAYS query `MonManagement` for `fsm_fired_event_failed` events and check the `message` column

### 2. Classifying Deterministic Errors as "Capacity/Transient"
- **NEVER** classify a deterministic exception (same error on every retry) as a "capacity" or "transient" issue
- If every request fails with the identical error, the root cause is a code defect — retries cannot help
- **Rule**: Check failure count per request (query SW210). If all requests fail the same number of times (= max retries), the error is deterministic

### 3. Using Causal Language Without Evidence
- **NEVER** say "overwhelmed", "saturated", "bottleneck", "flooded" without measured resource contention data (CPU%, queue depth, thread pool, memory)
- Many simultaneous failures can be caused by a single deterministic error repeated across requests
- **Rule**: Present measured data before using causal language

### 4. Asserting Architecture Without Evidence
- **NEVER** claim a system feature exists or does not exist (rate limiting, throttling, queueing) without code or documentation evidence
- **Rule**: If you cannot cite a specific code path or config setting, say "not verified"

### 5. Analyzing FSM-Level Errors When Operations Never Left the MOSM Queue
- **NEVER** investigate FSM-level exceptions or MonManagement/MonFSM errors for operations that were stuck in the MOSM request queue (`queue_type > 0, request_rank > 0` in `MonManagementOperations`)
- Queued operations never executed FSM actions — any FSM errors found on the same ring are from **different, unrelated operations**
- **Rule**: Always check `MonManagementOperations` for `management_operation_pending` events with `queue_type` and `request_rank` BEFORE diving into FSM-level telemetry. If the operation was queued, the root cause is queue saturation, not FSM errors.

---

## Step 1: Operation Discovery

Execute query **FSM001** (by request_id), **FSM002** (by server name), or **FSM003** (by fabric cluster) from [references/queries.md](references/queries.md).

**If no request_id** (context-based query via FSM002/FSM003):

**CRITICAL: Context-based queries return ALL SMs on a ring, not just the reported operation's SMs.**
Many SMs on a ring are independent workflows (e.g., `AzureStorageAccountStateMachine`, `AzureDnsRecordStateMachine`)
that share infrastructure but are NOT part of the workflow the ICM describes.

**Before proceeding, anchor results to the ICM context:**
1. Cross-reference candidate SMs against the ICM's correlation ID, monitor name, and title keywords
2. Filter to SMs whose `state_machine_type` is semantically related to the ICM-reported operation
   - e.g., for `SECRETS0011` / `SecretsRotation/...` → focus on `SqlRingSecretsStateMachine`, `FabricClusterStateMachine`, and their direct dependencies
   - e.g., for `SOC006` / `AddNewFile` → focus on `VeryLargeDatabaseStateMachine`, `VldbPageServerStateMachine`, `SqlInstanceStateMachine`, etc.
3. SMs with high fail counts that belong to **different, unrelated workflows** on the same ring are **noise, not bottlenecks**
4. Report unrelated high-failure SMs as "Ring Health: other failing SMs on this ring" — NOT as the primary bottleneck

**Extract**: operation_type, start/end timestamps, status (success/failed/timeout/stuck), error codes, cluster name.

**If no results**: Execute query **FSM070** from [references/queries.md](references/queries.md) to check both tables.

---

## Step 2: FSM Workflow Mapping

### 2A: State Transitions (MonFSM)

Execute query **FSM010** from [references/queries.md](references/queries.md).

### 2B: Stuck-State Detection (MonManagement) — CRITICAL

Execute query **FSM020** from [references/queries.md](references/queries.md).

Stuck SMs retrying the same action WITHOUT transitioning are invisible to MonFSM.

**If `fail_count > 10`**: This SM is a **strong bottleneck candidate** — takes **priority** over MonFSM transitions.

**IMPORTANT (context-based queries only):** When operating without a `request_id`, `fail_count > 10` alone is
NOT sufficient to declare a bottleneck. You MUST also verify the SM belongs to the ICM-reported operation's
workflow tree (see Step 1 anchoring rules). A high-failure SM from an unrelated workflow on the same ring
is a coincidence, not the root cause.

### 2C: Build Workflow Tree

- **Workflow position**: `/0/` = root, `/0/0/` = child. Parent = prefix.
- **Group by**: `(state_machine_type, keys, workflow_position)` = one SM instance
- **Calculate**: dwell time per state, total duration per SM
- **Add stuck SMs**: `{SM} stuck in {action} ({fail_count} failures, {first_fail} → {last_fail})`

### 2D: Data Sufficiency Gate

Compare FSM data window vs known operation duration:
- **≥ 50%**: Proceed
- **20-50%**: Caution flag
- **< 20%**: **STOP**. Report "Insufficient telemetry data."

---

## Step 3: Bottleneck Identification

**Priority order** (higher beats lower):

1. **Stuck SMs** (from Step 2B): If any SM has `fail_count > 10`, it is the primary bottleneck candidate
   regardless of dwell time. A stuck SM blocking progress is more diagnostic than a long-running but
   progressing SM. Example: `SqlRingSecretsStateMachine` stuck in `RotateCredentials` with 400 failures
   over 2 hours is the bottleneck — even if `FabricClusterStateMachine` ran for 6 hours total.
2. **Self-loops** (from self-loop detection below): SM staying in the same state with zero failures.
3. **Longest-dwell states** between workflow start and end — use only when no stuck SMs or self-loops exist.
4. **Innermost child SM** consuming > 50% of parent's total time.
5. No clear winner → report **top 3 candidates** with confidence levels.

**Rules**:
- Report at **BOTH levels** (parent + child SM)
- **Cross-check** ICM-reported state if available
- **Low-confidence**: dwell < 50% and no stuck SMs → flag, report top 3
- **Longest ≠ bottleneck**: A long-running SM that is *progressing through states normally* is not a
  bottleneck. The bottleneck is the SM that is *stuck or failing* and preventing the operation from
  completing. Always check Step 2B results before concluding based on dwell time alone.
- **ICM-context gate (MANDATORY for context-based queries)**: Before declaring ANY SM as the bottleneck,
  verify it is part of the workflow described by the ICM. Highest fail count on a ring ≠ bottleneck for the
  reported operation. An unrelated SM with 24,000 failures is ring noise; the operation's own SM with 7,000
  failures is the actual bottleneck.

**Self-loop detection (MANDATORY)**:
- If an action's `old_state == new_state` in >90% of `fsm_executed_action` events → flag as **self-loop bottleneck**
- Self-loops mean the action completes but deliberately stays in the same state (polling/throttling/waiting)
- These have ZERO `fsm_executed_action_failed` events — they are invisible to stuck detection based on failures alone
- **Always recommend Bluebird code inspection** for self-loops — only the code reveals why the action loops
- Example: `DeploymentAutomationInstanceStateMachine.AllocatingCompute` loops because `ShouldAllocateCompute()` returns false (throttling threshold exhausted)

---

## Step 4: Detailed Analysis

Execute query **FSM030** from [references/queries.md](references/queries.md).

---

## Step 5: Child Workflow Discovery

Execute query **FSM040** from [references/queries.md](references/queries.md).

For each relevant child: **repeat Steps 1-4**.

---

## Step 6: Correlate Parent and Child

Combined timeline. How child issues impacted parent.

---

## Step 7: Cross-Request Stuck State Detection

When a workflow tree shows an SM waiting for a child callback that never arrives, but the expected child SM is **NOT present** in the current request's workflow tree (Step 2C), the operation may be blocked by a **prior request** that left a shared SM in a stuck state.

### When to apply

- A parent SM is in a `WaitingFor*` state (e.g., `WaitingForWinFabDatabaseServiceDeletion`, `WaitingForPhysicalDatabaseDeactivation`)
- The expected callback event (e.g., `ProcessWinFabDatabaseServiceDeleted`) never appears under this request_id
- The child SM type (e.g., `FabricServiceStateMachine`, `PhysicalDatabaseStateMachine`) is absent from the workflow tree

### Procedure

1. **Identify the shared SM key**: Extract the `keys` value from the stuck parent SM
2. **Derive the time window**: Use the stuck parent SM's earliest `fsm_executed_action_failed` timestamp from Step 2B as the anchor point. Compute `AnchorTime - 24h` and `AnchorTime + 24h`.
3. **Query MonManagement by keys, NOT by request_id**, over the derived ±24h window:
   ```kql
   MonManagement
   | where originalEventTimestamp between (datetime({AnchorTime_minus_24h}) .. datetime({AnchorTime_plus_24h}))
   | where keys has "{shared_sm_key}"
   | where state_machine_type == "{expected_child_sm_type}"
   | project originalEventTimestamp, event, action, old_state, new_state, exception_type,
            Msg=substring(message, 0, 400), keys, request_id
   | order by originalEventTimestamp asc
   ```
3. **Find the owning request_id**: The child SM will be owned by a **different request_id** — often an internal workflow (TR evacuation, fleet management, EventDeactivate)
4. **Trace that request's full workflow tree** (repeat Steps 1-4 with the owning request_id)
5. **Report the cross-request dependency**:
   ```
   ⚠️ Cross-request stuck state detected:
   - User request {request_id_A} is blocked at {ParentSM}.{WaitingState}
   - The child SM {ChildSM} is owned by prior request {request_id_B} ({request_type})
   - {ChildSM} is stuck at {stuck_state} due to: {exception}
   - The user operation cannot proceed until the prior request's SM is unblocked
   ```

### Common patterns

| Stuck Parent SM | Waiting State | Expected Child SM | Common Prior Request Type |
|----------------|---------------|-------------------|-------------------------|
| `PhysicalDatabaseStateMachine` | `WaitingForWinFabDatabaseServiceDeletion` | `FabricServiceStateMachine` | Internal EventDeactivate (TR evacuation) |
| `LogicalDatabaseStateMachine` | `WaitingForPhysicalDatabaseDeactivation` | `PhysicalDatabaseStateMachine` | Internal EventDeactivate |
| `PhysicalDatabaseStateMachine` | `WaitingForWinFabDatabaseServiceCreation` | `FabricServiceStateMachine` | Prior create/activate request |

### Key insight: Workflow composition differences

Different request types include different SM types in their workflow:

| Request Type | SM Types Included |
|-------------|------------------|
| `DropLogicalDatabase` (user) | ManagementOperationSM, LogicalDatabaseSM, **SqlAliasCacheRecordSM**, SqlAliasSM, SqlLogicalDatabaseSM, PhysicalDatabaseSM, FabricServiceSM, AzureStorageAccountSM |
| `EventDeactivate` (internal) | LogicalDatabaseSM, PhysicalDatabaseSM, FabricServiceSM |

⚠️ `EventDeactivate` does NOT include `SqlAliasCacheRecordSM`. If an internal deactivation runs before a user drop, `FabricServiceSM.Drop` may fail on FK constraints (`FK_sql_alias_cache_records_fabric_services`) because alias cache records weren't cleaned up. The user drop later cleans them up, but `FabricServiceSM` is already stuck retrying under the earlier request.

---

## Timing Rules

- PowerShell: `[datetime]"end" - [datetime]"start"`
- Round to 2 decimal places

---

## Control Plane Extension: Stuck Workflow Investigation

When investigating a **stuck Control Plane management operation**, execute these additional steps after the core FSM analysis above. These require a `request_id` and target the CP-specific telemetry layers.

See [references/investigation-tips.md](references/investigation-tips.md) for triage shortcuts and [references/principles.md](references/principles.md) for debug principles.

### CP Step 1: Check Operation Lifecycle (SW100)

Execute query **SW100** from [references/queries.md](references/queries.md) against `MonManagementOperations` to see the full operation lifecycle.

| Event | Interpretation |
|-------|----------------|
| `management_operation_timeout` | Operation exceeded time limit — check FSM for underlying errors |
| `management_operation_failure` | Operation failed explicitly — check error_code and error_message |
| `management_operation_cancel` | Operation was cancelled — check why |
| `management_operation_rejected` | Operation was throttled by MOSM |

**If `error_code`/`error_message` are empty**: Proceed to CP Step 1b. Do NOT conclude "no errors".

### CP Step 1b: Check MOSM Request Queueing (SW115) — CRITICAL

**MANDATORY when operations timeout with empty error fields, or when `management_operation_pending` events exist.**

Execute query **SW115** from [references/queries.md](references/queries.md) to detect operations stuck in MOSM request queues.

**Key fields:**
- `queue_type` — The type of queue the request is waiting in (see enum below)
- `queue_id` — The ID of the resource being queued on (e.g., elastic pool ID, server ID)
- `request_rank` — Position in the queue (1 = next to execute, higher = further back)

**RequestQueueType enum** (from `dsmaindev` repo, `RequestQueueType`):

| Value | Name | Description |
|-------|------|-------------|
| 0 | None | Not queued |
| 1 | LogicalServerIdQueue | Queued behind other operations on the same logical server |
| 2 | LogicalDatabaseIdQueue | Queued behind other operations on the same logical database |
| 3 | ElasticPoolIdQueue | Queued behind other operations on the same elastic pool (legacy) |
| 4 | ResourcePoolIdQueue | Queued behind other operations on the same resource pool / elastic pool |
| 5 | ManagedServerIdQueue | Queued behind other operations on the same managed instance |

**Interpretation:**

| Signal | Interpretation |
|--------|----------------|
| `queue_type > 0` and `request_rank > 0` | Operation is **queued**, not executing — it never reached the FSM layer |
| `request_rank > 20` | Severe queue depth — the elastic pool/server has a large backlog of operations |
| Persistent `management_operation_pending` with stable/high `request_rank` | Operations ahead in queue are not completing — investigate what is blocking the queue head |
| `queue_type = 4` (ResourcePoolIdQueue) | Elastic pool concurrency limit hit — too many operations targeting the same pool |

**⚠️ CRITICAL ANTI-PATTERN**: When operations are queued (`queue_type > 0, request_rank > 0`), they **never made it past the MOSM queueing layer**. Do NOT look for FSM-level errors (MonManagement, MonFSM) as the root cause — the operation never executed FSM actions. The root cause is upstream: whatever is consuming the queue slots on that elastic pool/server/database.

**When this pattern is detected:**
1. Identify the `queue_id` (this is the resource pool / elastic pool ID)
2. Query what other operations are targeting that same `queue_id` and consuming slots
3. Check if the queue head operations are themselves stuck or slow
4. Report as **MOSM Queueing / Elastic Pool Concurrency Saturation**

### CP Step 2: Check MOSM Throttling (SW110)

Execute query **SW110** to measure MOSM release delay.

| Delay | Interpretation |
|-------|----------------|
| < 1 minute | Normal |
| 1-10 minutes | Moderate throttling |
| > 10 minutes | Heavy throttling or queueing |

### CP Step 3: Get FSM-Level Exceptions (SW200)

**MANDATORY when operation-level errors are empty.**

Execute query **SW200** to get actual exceptions from the `message` column of `MonManagement`. Also run **SW200a** for aggregated exception patterns.

### CP Step 4: Deterministic vs Transient (SW210)

Execute query **SW210** to classify the error pattern.

| Signal | Classification |
|--------|---------------|
| Every retry produces identical error (AvgFailures = MaxFailures = retry limit) | **Deterministic** — Code Defect |
| Failure counts vary across requests | **Transient** — may be Capacity or External Dependency |

### CP Step 5: FSM Latency Distribution (SW310)

Execute query **SW310** to determine whether time is spent inside FSM actions or waiting between them.

| Pattern | Interpretation |
|---------|----------------|
| High idle time | Waiting on external dependency or MOSM scheduling |
| High action time | FSM action itself is slow (e.g., slow CMS write) |

### CP Step 6: Target Tenant Ring (SW400)

Execute query **SW400** to check if failures concentrate on a specific tenant ring.

### CP Step 7: MS Resource Utilization (SW500a-e)

Execute queries **SW500a** through **SW500e** to analyze Management Service resource utilization:
- Node CPU, MS CPU — resource exhaustion
- Active Requests, Active Work Items, Active Workflows — FSM framework pressure
- Pending Work Items, Avg Queue Latency — queueing at FSM level

---

## Root Cause Classification

After completing the investigation, classify the root cause. See [references/root-cause-classification.md](references/root-cause-classification.md) for detailed criteria.

| Category | Indicators |
|----------|-----------|
| **Code Defect** | Deterministic exception, same error on every retry, specific exception type (SqlException, overflow, NullRef) |
| **Configuration** | Wrong timeout, missing feature flag, stale credentials |
| **Deployment** | Failure onset correlates with deployment timestamp, only affected rings where deployment was applied |
| **Capacity** | Resource metrics show pressure (CPU > 90%, queue depth), timeouts correlated with load |
| **External Dependency** | Errors from upstream service (storage, Key Vault, Node Agent), idle time in FSM waiting on external call |
| **MOSM Queueing** | Operations stuck in `management_operation_pending` with `queue_type > 0` and `request_rank > 0`; elastic pool or server has too many concurrent operations; operations timeout without ever reaching FSM execution |
| **Operational** | Manual step missed, wrong command executed |

**⚠️ Commonly Confused: Capacity vs Code Defect** — "Many failures" does NOT equal "Capacity". Many simultaneous failures can be caused by a single deterministic code defect. The distinguishing factor: capacity errors correlate with load and resource metrics show pressure; code defects fail identically regardless of load.

## CRITICAL: No False Positives

**NEVER** present incomplete data as a definitive bottleneck.

## Reference

- [references/queries.md](references/queries.md) — All Kusto queries (FSM001–FSM070, SW100–SW610)
- [references/knowledge.md](references/knowledge.md) — Architecture, terminology, root cause classification
- [references/principles.md](references/principles.md) — Debug principles and investigation tips
- [references/investigation-tips.md](references/investigation-tips.md) — Triage shortcuts
- [references/root-cause-classification.md](references/root-cause-classification.md) — Root cause taxonomy
