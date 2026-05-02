# Output Format: Hyperscale Geo-Restore Investigation Report

> [!WARNING]
> AI Generated. To be verified!

This document defines the output format for the `hs-georestore` skill investigation report.

---

## Investigation Report Structure

### 1. Metadata Block

Always present at the top of every report.

| Field | Example |
|-------|---------|
| `request_id` | `5B4D8749-6CBC-4F7F-8EE9-40DA08381C61` |
| `restore_id` | `679056e6-fc9e-406b-bbb7-175f98d03ff4` |
| `Region` | `ProdUkSo1a` |
| `Source Server/DB` | `myserver / mydb` |
| `Target Server/DB` | `myserver / mydb-georestore` |
| `Target SLO` | `HS_Gen5_2` |
| `Point in Time (PIT)` | `2026-04-15T10:00:00Z` |
| `Adjusted PIT` | `2026-04-15T10:00:00Z` |
| `PIT used by xlog to snip log` | `2026-04-15T10:00:00Z` |
| `Status` | Succeeded / Failed / Stuck / Cancelled |
| `Total Duration` | `2h 15m` |

### 2. Error Classification (Failed restores only)

| Field | Value |
|-------|-------|
| `Error Type` | User Error / System Error |
| `Error Message` | From restore operation result |
| `Classification Rule` | Which pattern matched |

> If **User Error** → report stops here. No further investigation needed.

### 3. Geo-Replication Lag Analysis

| Field | Value |
|-------|-------|
| `Storage Account(s)` | List of storage accounts checked |
| `Max Geo-Replication Lag` | e.g., `2h 34m` |
| `Lag Assessment` | 🚩 Significant / ⚠️ Elevated / ✅ Healthy |
| `Requested Point-in-Time` | From `operation_parameters` |
| `Point-in-Time Within Lag Window` | Yes / No |

**Detail per storage account** (if multiple):

| Storage Account | Current Lag | Last Sync Time |
|----------------|-------------|----------------|
| `account_name_1` | `1h 45m` | `2026-04-15T08:15:00Z` |
| `account_name_2` | `2h 34m` | `2026-04-15T07:26:00Z` |

### 4. Root Cause Assessment

```
**Root Cause**: {One-sentence summary}
**Category**: Geo-Replication Lag / User Error / Unknown (Escalate to hs-restore)
**Confidence**: {0.0–1.0} — {Very Low / Low / Medium / High}
**Evidence Summary**: {2–3 sentences linking query results to the root cause}
```

**Confidence Scoring Guide:**

| Range | Label | Criteria |
|-------|-------|----------|
| 0.85–1.00 | High | Geo-replication lag clearly exceeds requested point-in-time, confirmed by QHGR20 |
| 0.60–0.84 | Medium | Lag is elevated but borderline relative to requested point-in-time |
| 0.40–0.59 | Low | Lag data is ambiguous or partially unavailable |
| 0.00–0.39 | Very Low | Data aged out, no lag data, or storage accounts unknown |

### 5. Recommended Actions

#### Immediate
- {Action 1 — e.g., "Retry geo-restore; geo-replication lag has since recovered"}

#### Mitigation
- {Action 2 — e.g., "Monitor storage account geo-replication status before initiating geo-restore"}

#### Escalation
- {Action 3 — e.g., "If lag is not the cause, escalate to hs-restore skill for full 4-phase pipeline investigation"}
- {Action 4 — e.g., "Engage Azure Storage team if geo-replication lag persists beyond SLA"}
