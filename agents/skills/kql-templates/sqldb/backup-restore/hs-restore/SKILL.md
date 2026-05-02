---
name: hs-restore
description: Investigate Hyperscale (VLDB) restore failures, stuck restores, and slow restores. Diagnoses 4-phase restore pipeline (Plan Creation, App Creation, Data Copy, Redo) using 24 pre-built Kusto queries. Covers failed RCA, stuck detection, and slow restore analysis.
---

# Hyperscale (VLDB) Restore Investigation

Investigate why a Hyperscale restore **failed**, is **stuck**, or was **slow**. This skill traces the restore through 4 phases (Plan Creation → App Creation → Data Copy → Redo) using pre-built Kusto queries to identify the bottleneck and root cause.

## Required Information

The agent needs **one** of these input combinations to start:

### Path A: From ICM
- **ICM ID** — use `mcp_icm-prod_get_incident_details_by_id` to extract `request_id`, `restore_id`, server/database names, timestamps, and region from custom fields

### Path B: Direct IDs
- **request_id** (management operation GUID) — proceed directly to [Step 2](#step-2-operation-overview)
- **restore_id** — resolve to `request_id` via QHR00A
- **Region** (e.g., `ProdUkSo1a`, `westeurope`)

### Path C: Server/Database Name
- **Logical server name** and optionally **database name**
- **Approximate time range** (or ICM timestamps for heuristics)
- **Region**

## References

- **[queries.md](references/queries.md)** — All 24 KQL queries (QHR00A–QHR190). Execute ONLY queries from this file.
- **[knowledge.md](references/knowledge.md)** — Restore architecture, exception patterns, known issues, key tables.
- **[principles.md](references/principles.md)** — Debug methodology: status determination, branching logic, stuck detection, phase time windows, query applicability.
- **[output.md](references/output.md)** — Investigation report template and output conventions.
- **[prep/sources.md](references/prep/sources.md)** — TSG URLs, XTS view, and source documentation.

## Query Execution Format

> **MANDATORY TOOL**: ALL Kusto queries in this skill MUST be executed using `mcp_sqlops_query_kusto` (SqlOps MCP server).
> Do NOT search for alternative Kusto tools.

Example:

```
Tool: mcp_sqlops_query_kusto
Parameters:
  query: "<KQL from queries.md — verbatim, with parameters substituted>"
  region: "<region>"
```

> **CRITICAL**: Execute ONLY queries from `references/queries.md`. NEVER create or modify ad-hoc Kusto queries. Substitute `{parameter}` placeholders with actual values from investigation variables.

---

## Workflow

### Step 1: Input Resolution

**Goal**: Obtain `request_id` and `region`.

#### If ICM provided (Path A):
1. Read ICM via `mcp_icm-prod_get_incident_details_by_id`
2. Extract `request_id`, `restore_id`, server/database names, region from custom fields
3. Use time range heuristics from QHR00C (see `references/principles.md` Section 3)
4. If `request_id` not in ICM → use `restore_id` with QHR00A or server/db with QHR00B

#### If restore_id provided (Path B):
1. Run **QHR00A** — Find `request_id` by `restore_id`
2. Apply disambiguation logic from QHR00C if multiple results

#### If server/database provided (Path C):
1. Run **QHR00B** — Find `request_id` by server/database name
2. Apply disambiguation logic from QHR00C if multiple results

#### Disambiguation Rules (QHR00C):
- **1 result** → use directly
- **Multiple results** + ICM has `TargetLogicalDatabaseName` → filter by `TargetDb`
- **Still multiple** → present rows to user, ask to choose
- **>10 results** → ask user for narrower time range
- **0 results** → widen time range or ask user for more details
- **None of the above** → ask user explicitly for `request_id`

---

### Step 2: Operation Overview

Run **QHR10** to establish timeline, status, and extract investigation variables.

**Extract these variables from `operation_parameters` XML** (save for all subsequent queries):

| Variable | XML Key |
|----------|---------|
| `restore_id` | `<RestoreId>` |
| `source_logical_database_id` | `<SourceLogicalDatabaseId>` |
| `source_logical_server_name` | `<SourceLogicalServerName>` |
| `source_logical_database_name` | `<SourceLogicalDatabaseName>` |
| `target_logical_server_name` | `<TargetLogicalServerName>` |
| `target_logical_database_name` | `<TargetLogicalDatabaseName>` |
| `target_slo` | `<TargetServiceLevelObjectiveName>` |
| `point_in_time` | `<PointInTime>` |
| `source_database_dropped_time` | `<SourceDatabaseDroppedTime>` |
| `restore_start_time` | TIMESTAMP of `management_operation_start` event |
| `restore_end_time` | TIMESTAMP of completion event, or `now()` if stuck |

> **Note**: `target_logical_database_id` is in `operation_result` XML of `management_operation_success` event. For stuck restores, see [Stuck Restore Resolution](#stuck-restore-resolution).

**Determine Status** from QHR10 events:
- `management_operation_success` → **Succeeded**
- `management_operation_failed` → **Failed** (classify error — see `references/principles.md` Section 1)
- `management_operation_cancelled` → **Cancelled**
- No completion event → **Stuck / Still Running**

**If Failed**: Run **QHR15** (Target Database Drop Check) before proceeding. If drop detected → report as root cause.

**If User Error** detected from error classification → report finding and stop (no deep-dive needed).

---

### Step 3: Phase Detection

Run **QHR20** (Restore Step Progress) and **QHR30** (VldbRestoreMetrics) **in parallel** — both use `request_id`/`restore_id` and are independent.

From QHR30, save phase timestamps:
- `restorePlanGeneratedTime` — Phase 1 complete
- `restoreAppsCreatedTime` — Phase 2 complete
- `copyDoneTime` — Phase 3 complete
- `restoreFinishedTime` — Phase 4 complete

**Determine bottleneck phase** (see `references/principles.md` Section 2):

| Condition | Branch |
|-----------|--------|
| `AppCreationTime > 30 min` or stuck before `restoreAppsCreatedTime` | **Branch A** (App Creation) |
| `CopyTime > 30 min` or stuck between `restoreAppsCreatedTime` and `copyDoneTime` | **Branch B** (Data Copy) |
| `RedoTime > 30 min` or stuck after `copyDoneTime` | **Branch C** (Redo) |

> Multiple branches may apply. Investigate the longest/earliest bottleneck first.

**For stuck restores** — detect phase using rules in `references/principles.md` Section 3.

> **MANDATORY**: You MUST execute ALL applicable steps (Steps 4, 5, and 6) before generating the report (Step 7). The only valid early-exit points are:
> - **User Error** detected in Step 2 → report finding and stop
> - **Target DB Dropped** confirmed by QHR15 in Step 2 → report as root cause and stop
>
> In all other cases — including when the bottleneck phase seems obvious — continue through Steps 4–6. Do NOT skip ahead to report generation.

---

### Step 4: Shared Queries

Run these shared queries with the **bottleneck phase time window** (see `references/principles.md` Section 4 for `{phase_start}` / `{phase_end}` per phase):

> **💡 Performance: Parallel query, sequential analysis.** Run Round 1 queries **in parallel** — all share the same inputs (`request_id`, `{phase_start}`, `{phase_end}`). Analyze results in the documented order after all complete. Then run Round 2 (conditional queries that depend on Round 1 results).

**Round 1 — execute in parallel** (all branches unless noted):
1. **QHR40A** — Exception Counts During Phase
2. **QHR50** — FSM Throttling
3. **QHR60** — Replica Creation Delays (Branch A + C only)
4. **QHR70** — Stuck App Detection / FSM Outliers
5. **QHR100** — Restore Orchestrator State Flow
6. **QHR110** — Restore Plan Generation
7. **QHR120** — Destage Progress — Source DB
8. **QHR130** — Storage Calls

**Round 2 — conditional, after Round 1 completes:**
9. **QHR40B** — Sample Exception Details (only if QHR40A found exceptions)
10. **QHR80** — WinFabLogs Placement Check (Branch A + C only; one per QHR70 outlier)

> See `references/principles.md` Section 5 for the full applicability matrix.

---

### Step 5: Branch-Specific Queries

#### Branch A: App Creation Deep-Dive
After shared queries, run:
- **QHR90** — App Placement Failures (CreationFailed state)

**Key signals**: QHR60 stuck replicas, QHR70/QHR80 placement failures, QHR90 CreationFailed state, QHR50 FSM throttling.

#### Branch B: Data Copy Deep-Dive
After shared queries (skip QHR60, QHR80), run:
- **QHR190** — Blob Copy Operations (per-page-server copy status)

**Key signals**: QHR190 failed copies, QHR130 storage errors, QHR30 storage type mismatch, QHR40 exceptions.

#### Branch C: Redo Deep-Dive
After shared queries, run **in parallel**:
- **QHR140** — Restored Compute ErrorLog
- **QHR150** — Recovery Traces
- **QHR160** — RBPEX Placement Errors
- **QHR170** — Xlog/LogReplica Traces
- **QHR180** — Long Page Redo Summary (primary redo diagnostic)

**Key signals**: QHR180 slowest page server, QHR160 RBPEX errors, QHR150 stalled recovery, QHR140 engine errors.

#### Known Issues Cross-Reference (MANDATORY)

After completing branch-specific queries, compare findings from Steps 4–5 against the documented known issues in `references/knowledge.md` Section 3. For each known issue, check whether the corresponding signal was observed:

| Known Issue | Signal to Match | Query |
|-------------|-----------------|-------|
| Stuck Replica Creation (ICM 728004373, 738740724) | `WaitingTimeForReplica > 30m` | QHR60 |
| FSM Throttling | `priority != 1` and `duration > 30m` | QHR50 |
| Target DB Dropped During Restore | Drop/delete events in restore window | QHR15 |

For each match, flag it as a finding (if not already captured) and reference the known issue ICM IDs and documented mitigation from knowledge.md.

---

### Step 6: Similar & Correlated Incidents

After diagnostic analysis is complete, search ICM for historical incidents with similar patterns. This provides context on whether the issue is recurring and what mitigations worked previously.

#### 6.1 Build DynamicSearchTerms

Collect search terms from the investigation findings so far:

```
DynamicSearchTerms:
  error_codes: [from QHR10 error classification + QHR40B exception details]
  symptoms: [from bottleneck phase — e.g., "stuck restore", "FSM throttling", "placement failure", "slow blob copy", "RBPEX error", "recovery stalled"]
  sf_components: [from branch queries — e.g., "PageServer", "BlobCopy", "RestoreOrchestrator", "FSM"]
```

#### 6.2 Invoke Similar Incidents Skill

Use the `similar-incidents` skill (`Common/similar-incidents`) with these inputs:

| Input | Source | Value |
|-------|--------|-------|
| Current Incident ID | Step 1 (Path A only) | ICM ID, if available |
| LogicalServerName | Step 2 (QHR10) | `target_logical_server_name` |
| LogicalDatabaseName | Step 2 (QHR10) | `target_logical_database_name` |
| StartTime | Step 2 (QHR10) | `restore_start_time` |
| EndTime | Step 2 (QHR10) | `restore_end_time` |
| DynamicSearchTerms | Step 6.1 | Built from findings |

**Conditional execution:**
- **Path A (ICM provided)**: All 6 search steps (3.1–3.6) execute
- **Path B/C (no ICM)**: Steps 3.1 and 3.2 are marked N/A (require ICM ID); Steps 3.3–3.6 execute using server/database names and DynamicSearchTerms

#### 6.3 Invoke Correlated Incidents Skill

Use the `correlated-incidents` skill (`Common/correlated-incidents`) with these inputs:

| Input | Source | Value |
|-------|--------|-------|
| LogicalServerName | Step 2 (QHR10) | `target_logical_server_name` |
| LogicalDatabaseName | Step 2 (QHR10) | `target_logical_database_name` |
| StartTime | Step 2 (QHR10) | `restore_start_time` |
| EndTime | Step 2 (QHR10) | `restore_end_time` |
| AppName | From `get-db-info` skill or QHR30 topology | Target database AppName |

> **Note**: The correlated-incidents skill searches IcM DataWarehouse discussion entries for mentions of the same server/database/AppName. This helps CSS engineers find existing CRIs before filing their own.

Include both the "📊 Similar Incidents Analysis" and "📊 Correlated Incidents Analysis" sections in the final report, even if no results are found.

---

### Step 7: Report

> **CHECKPOINT — Verify before generating report:**
> 1. ALL shared queries from Step 4 have been executed for the bottleneck phase
> 2. ALL branch-specific queries from Step 5 have been executed for each applicable branch
> 3. Known Issues cross-reference (Step 5) has been completed using actual query results
> 4. Similar & Correlated Incidents search (Step 6) has been completed
>
> **An RCA with "queries not yet executed" is incomplete. Execute the queries — do not substitute lower confidence for missing work.**

Generate investigation report using the template in `references/output.md`.

1. **Metadata Block** — request_id, restore_id, region, server/db, SLO, status, duration
2. **Error Classification** (failed only) — User Error vs System Error
3. **Phase Duration Breakdown** — from QHR30, with High Latency flags
4. **Source/Target Configuration** — SLO, target page server count, storage type mismatch
5. **Findings** — each with severity, source query, evidence, impact
6. **Known Issues Cross-Reference** — from Step 5 known issues check
7. **Root Cause Assessment** — one-sentence summary + category
8. **Similar & Correlated Incidents** — from Step 6
9. **Recommended Actions** — immediate, mitigation, prevention, escalation

---

## Stuck Restore Resolution

For stuck restores where `target_logical_database_id` is needed but unavailable:

Run **QHR00D** — Resolve target_logical_database_id from request_id (see `references/queries.md`).

---

## Edge Cases

1. **Data aged out** — Kusto retention is typically 14-30 days. If queries return empty for old restores, state "Data aged out" and report what is available.
2. **Sparse telemetry** — Not all phases emit `message_scrubbed_resource_name`. Use QHR100 (orchestrator state flow) as fallback for phase timing.
3. **Pre-plan stuck** — If stuck before plan generation (QHR30 `restorePlanGeneratedTime` is null), skip branching. Run only QHR40A/B, QHR110, QHR120.
4. **Multiple bottleneck phases** — If >1 phase shows high latency, investigate each separately with its own time window.
5. **Non-Hyperscale restore** — If `target_slo` does NOT have `HS_` prefix, this is not a Hyperscale restore. Route to `restore-failure` skill instead.

## Related Skills

- **[restore-failure](../restore-failure/SKILL.md)** — Non-Hyperscale restore failures (DTU/vCore editions)
- **[router](../router/SKILL.md)** — BackupRestore skill router
