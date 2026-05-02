---
name: hs-georestore
description: Investigate Hyperscale (VLDB) geo-restore failures and slow geo-restores. Determines operation status, classifies user vs system errors, and checks whether failures are caused by storage account geo-replication lag using MonBlobClient telemetry.
---

# Hyperscale (VLDB) Geo-Restore Investigation

Investigate why a Hyperscale geo-restore **failed** or was **slow**. This skill checks the management operation status, classifies error type, and determines whether the failure is due to storage account geo-replication sync lag.

## Required Information

The agent needs **one** of these input combinations to start:

### Path A: From ICM
- **ICM ID** — use `mcp_icm-prod_get_incident_details_by_id` to extract `request_id`, `restore_id`, server/database names, timestamps, and region from custom fields

### Path B: Direct IDs
- **request_id** (management operation GUID) — proceed directly to [Step 2](#step-2-operation-overview)
- **restore_id** — resolve to `request_id` via QHGR00A
- **Region** (e.g., `ProdUkSo1a`, `westeurope`)

### Path C: Server/Database Name
- **Logical server name** and optionally **database name**
- **Approximate time range** (or ICM timestamps for heuristics)
- **Region**

## References

- **[queries.md](references/queries.md)** — All KQL queries (QHGR00A–QHGR20, including QHGR05). Execute ONLY queries from this file.
- **[output.md](references/output.md)** — Investigation report template and output conventions.

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
3. If `request_id` not in ICM → use `restore_id` with QHGR00A or server/db with QHGR00B

#### If restore_id provided (Path B):
1. Run **QHGR00A** — Find `request_id` by `restore_id`
2. Apply disambiguation rules if multiple results

#### If server/database provided (Path C):
1. Run **QHGR00B** — Find `request_id` by server/database name
2. Apply disambiguation rules if multiple results

#### Disambiguation Rules:
- **1 result** → use directly
- **Multiple results** + ICM has `TargetLogicalDatabaseName` → filter by `TargetDb`
- **Still multiple** → present rows to user, ask to choose
- **>10 results** → ask user for narrower time range
- **0 results** → widen time range or ask user for more details

---

### Step 1.5: Geo-Restore Verification

**Goal**: Confirm this is actually a geo-restore and not a database copy.

Run **QHGR05** using the `request_id` obtained in Step 1. This query checks that `operation_parameters` contains `<IsCrossServerRestore>false</IsCrossServerRestore>`, which distinguishes geo-restores from cross-server database copies.

**Analysis**:
- **Results returned** → Confirmed geo-restore. Proceed to Step 2.
- **No results** → This is NOT a geo-restore (likely a database copy or cross-server restore). Stop investigation and route to the appropriate skill (`hs-restore` for Hyperscale restores, `restore-failure` for non-Hyperscale).

---

### Step 2: Operation Overview

Run **QHGR10** to establish timeline, status, and extract investigation variables.

**Extract these variables from `operation_parameters` XML** (save for subsequent queries):

| Variable | XML Key |
|----------|---------|
| `restore_id` | `<RestoreId>` |
| `source_logical_database_id` | `<SourceLogicalDatabaseId>` |
| `source_logical_server_name` | `<SourceLogicalServerName>` |
| `source_logical_database_name` | `<SourceLogicalDatabaseName>` |
| `target_logical_server_name` | `<TargetLogicalServerName>` |
| `target_logical_database_name` | `<TargetLogicalDatabaseName>` |
| `target_edition` | `<TargetEdition>` |
| `target_slo` | `<TargetServiceLevelObjectiveName>` |
| `point_in_time` | `<PointInTime>` |
| `source_database_dropped_time` | `<SourceDatabaseDroppedTime>` |
| `restore_start_time` | TIMESTAMP of `management_operation_start` event |
| `restore_end_time` | TIMESTAMP of completion event, or `now()` if stuck |

**Determine Status** from QHGR10 events:
- `management_operation_success` → **Succeeded**
- `management_operation_failed` → **Failed** (classify error)
- `management_operation_cancelled` → **Cancelled**
- No completion event → **Stuck / Still Running**

**Error Classification:**

#### User Error Patterns (stop investigation, report as user error):
- Target database name issues: duplicates, invalid characters, null/empty, "already exists"
- Quota/Limit issues: server database count, vCore quota, "server would exceed the allowed"
- Key Vault issues: "Azure Key Vault"
- Geo-Secondary blocks: "BlockRestoreOnVldbGeoSecondary"
- Source database deleted/unavailable
- `ElasticPoolInconsistentVcoreGuaranteeSettings`

#### System Error Patterns (proceed to Step 3):
- "The service objective assignment for the database has failed..."
- Timeout patterns (no user action possible)
- Internal exceptions without user-facing guidance

**Default**: If no pattern matches → classify as **System Error** and proceed to Step 2.5.

**If User Error detected** → Report finding and stop. No further investigation needed.

---

### Step 2a: Resolve Region Kusto Cluster

**Goal**: Resolve the target server's region Kusto cluster so subsequent queries (QHGR12, QHGR15, QHGR20) execute against the correct region instead of fanning out across all clusters.

Run **QHGR11** with the `target_logical_server_name` and timestamps from Step 2.

**Post-processing**:
1. Extract the region segment from the returned ClusterName FQDN (e.g., `cr10.northcentralus1-a.control.database.windows.net` → `northcentralus1`)
2. Save as `{region}` — pass this to `mcp_sqlops_query_kusto` for all subsequent queries

**If QHGR11 returns 0 results**: Try with `source_logical_server_name` instead, or ask the user for the region.

---

### Step 2.5: State Machine Transitions

**Goal**: Trace the full restore pipeline — every state machine transition across restore request orchestration, page server provisioning, storage copy, compute database creation, and SQL instance readiness.

Run **QHGR15** with the `request_id`. This query runs for **all** investigations (success, failure, or stuck) and is the primary diagnostic for understanding the restore timeline.

**What to look for:**

| Signal | Meaning |
|--------|---------|
| Large `elapsed_time_milliseconds` on a single action | That phase was the duration bottleneck |
| `fsm_log_exception` events | Errors during that state machine phase — check `exception_type` and `message` |
| A state machine stuck in `is_stable_state == false` | Restore is hung at that phase |
| `VldbPageServerStateMachine` taking long | Page server snapshot restore is slow (large redo size) |
| `AzureStorageCopy*` taking long | Storage blob copy is the bottleneck (large database or slow copy throughput) |
| All state machines completing normally | Healthy restore — no action needed |

**For successful restores**: Use this to build the duration breakdown (which phase took the most time).
**For failed restores**: Identify which state machine failed and at which transition, then proceed to Step 3.
**For stuck restores**: Identify the last state machine that was active and its current state.

---

### Step 3: Point-in-Time Extraction

**Goal**: Extract the actual Point in Time (PIT), Adjusted PIT, and PIT used by xlog to snip log from the restore request progress events.

Run **QHGR12** with the `restore_id` from Step 2 and the `{region}` resolved in Step 2a.

**Extract these three values from `message_scrubbed_resource_name`:**

| Value | Description |
|-------|-------------|
| **PIT** | Requested point-in-time from the user/API |
| **Adjusted PIT** | Adjusted point-in-time after geo-replication lag or data availability consideration |
| **PIT used by xlog to snip log** | Actual point-in-time used by xlog to truncate the log — the effective restore point |

**Analysis**:
- If PIT ≠ Adjusted PIT → The system adjusted the restore point (possibly due to geo-replication lag).
- If all three match → Clean restore, no point-in-time adjustment was needed.
- Include all three values in the investigation report metadata.

---

### Step 4: Storage Account Geo-Replication Lag Check

**Goal**: Determine whether the geo-restore failure or slowness is caused by storage account geo-replication lag.

#### 4.1 Identify Storage Accounts

From the source database's XLog destage blob storage, identify the storage account names used. These are the storage accounts that hold the geo-replicated backup data.

> The storage account names should come from the ICM, the user, or prior knowledge of the source database's storage configuration. Ask the user for the storage account names if not available.

#### 4.2 Run Geo-Replication Lag Query

Run **QHGR20** with the identified storage account names and the region of the **source** database (where the geo-replicated storage resides).

**Analysis**:
- **`max_current_lag` > desired RPO** → 🚩 Geo-replication lag exceeds acceptable threshold. The geo-restore could not restore to the requested point-in-time because the storage account had not yet replicated data up to that point.
- **`max_current_lag` is small (< 15 min)** → Geo-replication is healthy. The failure is likely caused by something else — escalate to `hs-restore` skill for full 4-phase analysis.

**Interpretation Guidelines**:
- Typical geo-replication lag is under 15 minutes for most regions.
- Lag > 1 hour is unusual and should be flagged as a significant finding.
- If `geo_replication_last_sync_time` is much earlier than the requested `point_in_time`, this confirms the storage account had not replicated data to the requested restore point.

---

### Step 5: Report

Generate investigation report using the template in `references/output.md`.

1. **Metadata Block** — request_id, restore_id, region, server/db, SLO, status, duration
2. **Error Classification** (failed only) — User Error vs System Error
3. **Geo-Replication Lag Analysis** — storage account names, current lag, assessment
4. **Root Cause Assessment** — one-sentence summary
5. **Recommended Actions** — immediate, mitigation, escalation

---

## Edge Cases

1. **Data aged out** — Kusto retention is typically 14–30 days. If queries return empty for old restores, state "Data aged out" and report what is available.
2. **Storage account names unknown** — Prompt the user for storage account names. Without them, QHGR20 cannot be executed.
3. **Non-Hyperscale restore** — If `target_slo` does NOT have `HS_` prefix, this is not a Hyperscale restore. Route to `restore-failure` skill instead.
4. **Lag query returns no results** — The storage account may not have geo-replication enabled, or the data has aged out. Note this in findings.
5. **System error but no geo-replication lag** — If QHGR20 shows healthy replication but the restore still failed, escalate to the `hs-restore` skill for full 4-phase pipeline investigation.

## Related Skills

- **[hs-restore](../hs-restore/SKILL.md)** — Full Hyperscale restore investigation (4-phase pipeline with 24 queries). Escalate here if geo-replication lag is not the root cause.
- **[hyperscale-georestore-metrics](../hyperscale-georestore-metrics/SKILL.md)** — Weekly Hyperscale geo-restore metrics and batch failure analysis.
- **[restore-failure](../restore-failure/SKILL.md)** — Non-Hyperscale restore failures (DTU/vCore editions).
- **[router](../router/SKILL.md)** — BackupRestore skill router.
