# Output Format: Hyperscale Restore Investigation Report

> [!WARNING]
> AI Generated. To be verified!

This document defines the output format for the `hs-restore` skill investigation report.

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
| `Target Server/DB` | `myserver / mydb-restored` |
| `Target SLO` | `HS_Gen5_2` |
| `Point in Time` | `2025-12-15T10:00:00Z` |
| `Status` | Succeeded / Failed / Stuck / Cancelled |
| `Total Duration` | `5h 26m` |

### 2. Error Classification (Failed restores only)

| Field | Value |
|-------|-------|
| `Error Type` | User Error / System Error |
| `Error Message` | From restore operation result |
| `Classification Rule` | Which pattern matched |

### 3. Phase Duration Breakdown

| Phase | Duration (min) | Timestamps | Flag |
|-------|---------------|-----------|------|
| Plan Creation | `N` | `start` → `restorePlanGeneratedTime` | |
| App Creation | `N` | `restorePlanGeneratedTime` → `restoreAppsCreatedTime` | 🚩 High Latency (if >30m) |
| Data Copy | `N` | `restoreAppsCreatedTime` → `copyDoneTime` | 🚩 High Latency (if >30m) |
| Redo | `N` | `copyDoneTime` → `restoreFinishedTime` | 🚩 High Latency (if >30m) |

#### 3.1 Detailed Event Timeline (Bottleneck Phase)

**MANDATORY**: After the phase summary table, generate a chronological event timeline scoped to the **bottleneck phase** identified above. Include all timestamped events from queries executed during Steps 3–5 that fall within the bottleneck phase window.

**Bottleneck Phase**: {Phase Name} (`{phase_start}` → `{phase_end}`)

| Time (UTC) | Time Gap | Event |
|------------|----------|-------|
| yyyy-MM-dd HH:mm:ss | | {First event in phase} |
| yyyy-MM-dd HH:mm:ss | {gap} | {Next event} |
| yyyy-MM-dd HH:mm:ss | 🚩 {gap} | {Anomalous event — flag if gap > 10m} |

**Instructions:**
- Include events from: step progress, orchestrator states, FSM events, replica creation, stuck apps, storage calls, and branch-specific queries
- Sort all events chronologically regardless of source query
- Calculate time gap from the previous event; flag with 🚩 if gap exceeds 10 minutes
- Use actual timestamps from query results — DO NOT estimate or fabricate timestamps
- If multiple bottleneck phases exist, generate one timeline per phase

**🚩 Timeline Delays:**
- {Phase start} to {first event}: **{duration}** — {normal/slow}
- {Event A} to {Event B}: **{duration}** — {explanation of delay}
- Total unexplained gap: **{duration}**

### 4. Source/Target Configuration

| Field | Value |
|-------|-------|
| `Source SLO` | e.g., `HS_Gen5_4` |
| `Target SLO` | e.g., `HS_Gen5_2` |
| `Target Page Server Count` | e.g., `45` — this is the number of Page Servers, NOT the file count from the copy-done message |
| `Target 1 TB Page Servers` | e.g., `3` |
| `Source Backup Storage Type` | e.g., `GRS` |
| `Target Backup Storage Type` | e.g., `LRS` |
| `Storage Type Mismatch` | Yes / No |
| `Redo Size (GB)` | e.g., `1.234` |

### 5. Findings

Each finding follows this format:

```
**Finding F{N}: {Title}**
- **Severity**: Critical / Warning / Info
- **Evidence**: {Key data points from query results}
- **Impact**: {How this affected the restore}
- **Related ICM**: {If applicable — e.g., ICM 728004373}
```

Example findings:
- Finding: Stuck Page Server Replicas
- Finding: FSM Throttling >30 min
- Finding: App Placement Failures
- Finding: Slow Blob Copy
- Finding: RBPEX Errors
- Finding: Recovery Stalled
- Finding: Target Database Dropped

### 6. Known Issues Cross-Reference

Compare findings against documented known issues in `references/knowledge.md` Section 3.

**Rules:**
- **Only include matched known issues** (confidence Medium or higher). Omit issues that did not match.
- If **no** known issues matched, replace the table with: "No known issues matched the investigation signals."
- When a known issue matches, reference the ICM IDs and documented mitigation from knowledge.md Section 8.

| Known Issue | Signal | Evidence |
|-------------|--------|----------|
| {Matched Issue Name} (ICM {ids}) | {Signal that triggered the match} | {Brief evidence from query results} |

### 7. Root Cause Assessment

```
**Root Cause**: {One-sentence summary}
**Category**: App Creation / Data Copy / Redo / Infrastructure / User Error
**Bottleneck Phase**: Phase {N} — {Name}
**Confidence**: {0.0–1.0} — {High / Medium / Low / Very Low}
**Contributing Factors**: {List}
**Evidence Summary**: {2–3 sentences linking key query results to the root cause}
```

**Confidence Scoring Guide:**

| Range | Label | Criteria for HS Restore |
|-------|-------|------------------------|
| 0.85–1.00 | High | Root cause confirmed by multiple query signals + matches a documented known issue or has corroborating similar incidents |
| 0.60–0.84 | Medium | Clear bottleneck phase with supporting query evidence, but no known issue match or external confirmation |
| 0.40–0.59 | Low | Partial evidence — bottleneck phase identified but key diagnostic queries returned empty or ambiguous results |
| 0.00–0.39 | Very Low | Minimal evidence — data aged out, sparse telemetry, or multiple competing hypotheses with no clear signal |

> **Important**: "Queries not yet executed" is NEVER a valid reason for reduced confidence. All applicable queries from Steps 4–5 must be executed before assessing confidence. If a query returns empty results or data has aged out, that is valid evidence (Low/Very Low confidence). But skipping queries entirely is not — go back and execute them.

### 8. Similar & Correlated Incidents

This section is **MANDATORY** — include it even if no similar or correlated incidents are found.

> **Output Rule**: Do NOT include internal search methodology in the report — no "Search Methods Executed" checklists, "Dynamic Search Terms" lists, or "Search Criteria" blocks. The RCA audience needs only the results. Describe the search scope in a brief introductory sentence (e.g., "Found 3 potentially related incidents in the Backup Restore Hyperscale team (last 90 days):").

#### 📊 Similar Incidents Analysis

Found {count} similar incidents in {team_name} (last {N} days):

| Rank | ICM ID | Date | Title | Severity |
| ---- | ------ | ---- | ----- | -------- |
| 1 | [{id}](https://portal.microsofticm.com/imp/v5/incidents/details/{id}/summary) | {date} | {title} | {severity} |

*If no similar incidents found: "No similar incidents found."*

#### 📊 Correlated Incidents Analysis

Found {count} correlated incidents for `{target_logical_server_name}` / `{target_logical_database_name}` in the 30 days prior to the restore:

| Rank | IcM ID | Severity | Status | Impact Start | Title |
| ---- | ------ | -------- | ------ | ------------ | ----- |
| 1 | [{id}](https://portal.microsofticm.com/imp/v5/incidents/details/{id}/summary) | {sev} | {status} | {date} | {title} |

*If no correlated incidents found: "No correlated incidents found for `{server}` / `{database}` in the 30 days prior to the restore."*

### 9. Recommended Actions

Numbered list of actions based on findings. **Do NOT use internal query IDs (QHR prefix)** — describe actions in user-friendly terms.

1. **Immediate**: {Action if restore is stuck — e.g., restart stuck app processes}
2. **Mitigation**: {Steps to resolve the root cause — describe what to check, not which internal query to run}
3. **Prevention**: {Long-term recommendations}
4. **Escalation**: {Team to escalate to, if needed — e.g., Socrates Data Plane / Backup Restore Hyperscale}

**Example (good):** "Investigate replica creation delays during the App Creation window (2026-03-23T15:42Z to 2026-03-26T00:12Z) to identify specific stuck replicas."
**Example (bad):** "Run QHR60 and QHR70 scoped to the App Creation window."

---

## Output Conventions

- Always include the `!!!AI Generated. To be verified!!!` warning at the top of every report
- Use 🚩 for flags and warnings
- Times in minutes (for durations < 24h) or hours+minutes (for longer)
- GUIDs in uppercase
- **Never use internal query IDs (QHR prefix) in any section of the output report** — the audience is the end user, not the skill developer
- If data is aged out for a query, state: "Data aged out — no results available"
- If a query returns empty results, state the meaning per the query's analysis guidance



### Conversion Checklist

When converting the standard report to ICM format, replace ALL pipe tables:

1. Section 1 — Metadata Block table → `<table>`
2. Section 2 — Error Classification table → `<table>`
3. Section 3 — Phase Duration Breakdown table → `<table>`
4. Section 3.1 — Detailed Event Timeline table → `<table>`
5. Section 4 — Source/Target Configuration table → `<table>`
6. Section 6 — Known Issues Cross-Reference table → `<table>`
7. Section 7 — Confidence Scoring Guide table → omit (internal reference only)
8. Section 8 — Similar Incidents table → `<table>`
9. Section 8 — Correlated Incidents table → `<table>`
