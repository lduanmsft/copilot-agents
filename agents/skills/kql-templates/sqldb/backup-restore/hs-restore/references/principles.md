# Debug Principles: Hyperscale (VLDB) Restore Investigation

This file documents the debug methodology and interpretation rules for diagnosing Hyperscale restore failures, stuck restores, and slow restores. Extracted from `investigation-flow.md` interpretation rules and engineering domain expertise.

---

## 1. Status Determination (from QHR10)

### Operation Status Classification

From `MonManagementOperations` events:

| Status | Signal | Next Step |
|--------|--------|-----------|
| **Succeeded** | `management_operation_success` event present | Investigate slow duration if needed |
| **Failed** | `management_operation_failed` event present | Classify error → Run QHR15 (drop check) → QHR20 |
| **Cancelled** | `management_operation_cancelled` event present | No RCA needed unless recurrence |
| **Stuck / Still Running** | No completion event | Treat as stuck → Run QHR20 → QHR30 for phase detection |

### Error Classification

When QHR10 shows failure, classify from `error_message`:

#### User Error Patterns (explicitly mark as "User Error")

- Target database name issues: duplicates, invalid characters, null/empty, "already exists"
- Quota/Limit issues: server database count, vCore quota, "server would exceed the allowed"
- Key Vault issues: "Azure Key Vault"
- Geo-Secondary blocks: "BlockRestoreOnVldbGeoSecondary"
- Source database deleted/unavailable
- `ElasticPoolInconsistentVcoreGuaranteeSettings`

#### System Error Patterns (explicitly mark as "System Error")

- "The service objective assignment for the database has failed..."
- Timeout patterns (no user action possible)
- Internal exceptions without user-facing guidance

**Default**: If no pattern matches → classify as **System Error**.

---

## 2. Branching Decision Logic

### After QHR30 — Determine Bottleneck Phase

```
QHR30 Results
    │
    ├── AppCreationTime > 30 min, or stuck before restoreAppsCreatedTime
    │       → Branch A: App Creation Deep-Dive
    │
    ├── CopyTime > 30 min, or stuck between restoreAppsCreatedTime and copyDoneTime  
    │       → Branch B: Data Copy Deep-Dive
    │
    └── RedoTime > 30 min, or stuck after copyDoneTime
            → Branch C: Redo Deep-Dive
```

> **Multiple branches may apply** if more than one phase shows high latency. Investigate the earliest/longest bottleneck first.

### High Latency Flags

For any duration > 30 minutes, explicitly flag:
- `AppCreationTime > 30 min` → "High Latency: App Creation"
- `CopyTime > 30 min` → "High Latency: Data Copy"
- `RedoTime > 30 min` → "High Latency: Redo"

### Configuration Mismatch Detection

From QHR30:
- `SourceActiveBackupStorageType` vs `TargetDBStorageAccountType` differ → flag **"Storage Type Mismatch"** (may require cross-region or cross-account copy)
- `CountOfPS > 300` → flag **"Large Number of Target Page Servers"** (contributes to high restore duration — more PS means more parallel copy/redo work)

> **IMPORTANT — Do NOT confuse these two numbers:**
> - **Page Server Count** (`CountOfPS` from QHR30) = number of **Page Servers** (SF apps of type `Worker.Vldb.Storage`). Typical range: 1–100+.
> - **Page Server Files** (`{N}` in QHR20 message `"Copy of {N} page server snapshot and XLog files finished successfully."`) = number of **data files** copied. Can be hundreds or thousands. This is NOT the page server count.
- `RedoSizeGB` large → correlates with longer Phase 4

---

## 3. Stuck Restore Detection

### Phase Detection Rules (evaluate top to bottom — first match wins)

| Stuck Condition (from QHR30) | Stuck Phase | Branch | `{phase_start}` | `{phase_end}` |
|------|------|------|------|------|
| `restorePlanGeneratedTime` is null/empty | Pre-plan (Destage Wait) | None — special case | `restore_start_time` (QHR10) | `now()` |
| `restoreAppsCreatedTime == todatetime(1)` | App Creation | **Branch A** | `restorePlanGeneratedTime` | `now()` |
| `copyDoneTime == todatetime(1)` | Data Copy | **Branch B** | `restoreAppsCreatedTime` | `now()` |
| `restoreFinishedTime == todatetime(1)` | Redo | **Branch C** | `copyDoneTime` | `now()` |

### Pre-plan Stuck (Special Case)

If the restore is stuck before plan generation, skip the branching decision tree entirely. Run only:
- **QHR40A/B** (Exceptions) — with `{phase_start}` = `restore_start_time`, `{phase_end}` = `now()`
- **QHR110** (Restore Plan Generation) — check if plan generation was attempted
- **QHR120** (Destage Progress) — check if source DB transaction log is still destaging

### Resolving `target_logical_database_id` for Stuck Restores

For Branch B and C queries, `target_logical_database_id` is needed but unavailable from `operation_result` (no success event). If the restore is stuck in Data Copy or Redo, the target DB's apps already exist — extract from MonManagement FSM keys:

```kusto
MonManagement
| where request_id == toupper("{request_id}")
| where event contains "fsm_transition"
| where message contains "logical_db_name"
| parse message with * "logical_db_name=" target_logical_database_id "," *
| where isnotempty(target_logical_database_id)
| summarize by target_logical_database_id
| take 1
```

---

## 4. Phase Time Windows

All shared queries (QHR40A/B, QHR50, QHR60, QHR70, QHR80) use `{phase_start}` and `{phase_end}`. Substitute from QHR30:

| Phase | `{phase_start}` | `{phase_end}` |
|-------|-----------------|----------------|
| Pre-plan / Destage (stuck only) | `restore_start_time` (QHR10) | `now()` |
| App Creation (Branch A) | `restorePlanGeneratedTime` | `restoreAppsCreatedTime` (or `now()` if stuck) |
| Data Copy (Branch B) | `restoreAppsCreatedTime` | `copyDoneTime` (or `now()` if stuck) |
| Redo (Branch C) | `copyDoneTime` | `restoreFinishedTime` (or `now()` if stuck) |

---

## 5. Query Applicability Matrix

Not all shared queries apply to all branches.

| Query | Branch A (App) | Branch B (Copy) | Branch C (Redo) |
|-------|:-:|:-:|:-:|
| QHR40A/B — Exceptions | ✅ | ✅ | ✅ |
| QHR50 — FSM Throttling | ✅ | ✅ | ✅ |
| QHR60 — Replica Creation Delays | ✅ | ❌ | ✅ |
| QHR70 — Stuck App Detection | ✅ | ✅ | ✅ |
| QHR80 — WinFabLogs Placement | ✅ | ❌ | ✅ |
| QHR100 — Orchestrator State Flow | ✅ | ✅ | ✅ |
| QHR110 — Restore Plan Generation | ✅ | ✅ | ✅ |
| QHR120 — Destage Progress | ✅ | ✅ | ✅ |
| QHR130 — Storage Calls | ✅ | ✅ | ✅ |
| QHR90 — App Placement Failures | ✅ | ❌ | ❌ |
| QHR190 — Blob Copy Operations | ❌ | ✅ | ❌ |
| QHR140 — Compute ErrorLog | ❌ | ❌ | ✅ |
| QHR150 — Recovery Traces | ❌ | ❌ | ✅ |
| QHR160 — RBPEX Placement Errors | ❌ | ❌ | ✅ |
| QHR170 — Xlog/LogReplica Traces | ❌ | ❌ | ✅ |
| QHR180 — Long Page Redo Summary | ❌ | ❌ | ✅ |
