---
name: triage
description: Determines the type of high availability issue (failover, quorum loss, etc.) by analyzing symptoms, telemetry patterns, and initial data. Select the appropriate diagnostic skills for detailed investigation. This is a shared utility skill used by the Availability agent to triage incidents and route them to specialized diagnostic skills.
---

# High Availability Issue Triage

This skill analyzes available information to determine the type of HA issue and route to the appropriate diagnostic skills for detailed investigation.

## Required Information

### From User or ICM:
- **Incident ID** (optional - if investigating an existing ICM incident)
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill:
- **deployment_type** (e.g., "GP without ZR", "GP with ZR", "BC")
- **service_level_objective**
- All database configuration variables

### Optional User Hints:
- Explicit keywords: "failover", "quorum loss", "replica", etc.
- Symptoms described by user

## Workflow

### 1. Extract ICM Incident Information (if Incident ID Available)

**Run this FIRST if an ICM incident ID is provided.** ICM contains valuable triage information that directly drives skill selection.

**Step 1a: Get incident context:**

```
Tool: mcp_icm-prod_get_incident_context
Parameters:
  incidentId: "{incident_id}"
```

**Step 1b: Get AI summary:**

```
Tool: mcp_icm-prod_get_ai_summary
Parameters:
  incidentId: "{incident_id}"
```

**Step 1c: Extract and store key fields:**

| Field | Variable | Triage Use |
| ----- | -------- | ---------- |
| **Title** | `icm_title` | Primary keyword source |
| **Description** | `icm_description` | Symptoms, error codes |
| **Severity** | `icm_severity` | Urgency indication |
| **Alert Source** | `icm_alert_source` | Monitor type hints |
| **AI Summary** | `icm_ai_summary` | Quick issue understanding |

**Step 1d: Analyze ICM content for skill keywords:**

Scan `icm_title`, `icm_description`, and `icm_ai_summary` for these keywords:

| Keywords Found | Set Flag | Skill to Include |
| -------------- | -------- | ---------------- |
| "failover", "replica transition", "role change", "primary", "secondary" | `icm_suggests_failover = true` | `failover` |
| "quorum", "quorum loss", "insufficient replicas", "partition" | `icm_suggests_quorum = true` | `quorum-loss` |
| "node down", "node failure", "bugcheck", "deactivation", "node health" | `icm_suggests_node = true` | `node-health` |
| "40613", "database unavailable", "connection refused" | `icm_suggests_failover = true` | `failover` |
| "connectivity", "timeout" | `icm_suggests_failover = true` | `failover` |
| "login failure", "login failed", "login success rate", "CRGW0001", "LoginFailureCause", "Login Failures Runner", "login errors" | `icm_suggests_login_failures = true` | `login-failure-triage` |
| "dump", "crash", "assertion", "watson", "stack dump", "process failure", "access violation" | `icm_suggests_dump = true` | `dump` |
| "40613 state 126", "state 126", "database in transition" | `icm_suggests_error_40613_126 = true` | `error-40613-state-126` |
| "40613 state 127", "state 127", "warmup", "cannot open database" | `icm_suggests_error_40613_127 = true` | `error-40613-state-127` |
| "frequent failover", "repeated failover", "failover frequency", "multiple failovers" | `icm_suggests_freq_failover = true` | `freq-failover` |
| "synchronizing", "replica recovery", "stuck recovery", "sync replica", "recovery pending" | `icm_suggests_sync_recovery = true` | `sync-replica-recovery` |
| "unplaced", "replica placement", "placement constraint", "no available nodes" | `icm_suggests_unplaced = true` | `unplaced-replicas` |
| "update slo", "slo change", "tier change", "scaling", "UpdateSloTarget", "stuck slo", "slo stuck" | `icm_suggests_update_slo = true` | `update-slo` |
| "seeding", "seed failure", "repeated seeding", "TRDB0058", "build replica", "ExistingDbInSeeding", "VDI Client failed", "AKVTDEIssue", "33111", "certificate missing" | `icm_suggests_seeding = true` | `seeding-rca` |
| "HADR_SYNC_COMMIT", "sync commit wait", "log send queue", "redo queue", "redo queue lag", "synchronous replication", "AVAILABILITY_REPLICA", "hadr sync" | `icm_suggests_hadr_sync_commit = true` | `high-sync-commit-wait` (BC/Premium only — skip for GP/Hyperscale) |

**Example ICM analysis:**

```
ICM Title: "SQL DB Availability - Quorum Loss Alert for server xyz"
ICM Description: "Customer reported database unavailable. Multiple replicas down."
ICM AI Summary: "Quorum loss detected due to node failures in zone 2."

Analysis:
- "Quorum Loss" in title → icm_suggests_quorum = true
- "node failures" in AI summary → icm_suggests_node = true

Result: Select skills ["quorum-loss", "node-health"]
```

### 2. Check for Explicit Keywords from User

If user explicitly mentioned:
- **"failover"**, **"replica transition"**, **"role change"** → Include the `failover` skill
- **"quorum loss"**, **"replica rebuild"**, **"quorum"** → Include the `quorum-loss` skill
- **"node down"**, **"node failure"**, **"bugcheck"** → Include the `node-health` skill
- **"dump"**, **"crash"**, **"assertion"**, **"watson"** → Include the `dump` skill
- **"40613 state 126"**, **"database in transition"** → Include the `error-40613-state-126` skill
- **"login failure"**, **"login success rate"**, **"CRGW0001"**, **"LoginFailureCause"** → Include the `login-failure-triage` skill
- **"40613 state 127"**, **"warmup"**, **"cannot open database"** → Include the `error-40613-state-127` skill
- **"frequent failover"**, **"repeated failover"** → Include the `freq-failover` skill
- **"sync replica"**, **"replica recovery"**, **"stuck recovery"** → Include the `sync-replica-recovery` skill
- **"unplaced"**, **"placement"**, **"no available nodes"** → Include the `unplaced-replicas` skill
- **"update slo"**, **"slo change"**, **"scaling"**, **"tier change"** → Include the `update-slo` skill
- **"seeding"**, **"seed failure"**, **"build replica"**, **"TRDB0058"**, **"VDI"**, **"ExistingDbInSeeding"** → Include the `seeding-rca` skill
- **"HADR_SYNC_COMMIT"**, **"sync commit wait"**, **"log send queue"**, **"redo queue lag"**, **"synchronous replication"**, **"AVAILABILITY_REPLICA"** → Include the `high-sync-commit-wait` skill (**only if SLO is Business Critical or Premium — skip for GP/Hyperscale**)

### 3. Query SqlFailovers and LoginOutages (TO BE IMPLEMENTED)

Execute preliminary queries to understand incident characteristics:
- Check `SqlFailovers` table for completed failover events
- Check `LoginOutages` table for connectivity issues
- Analyze patterns and severity

**Queries**: See [references/queries.md](references/queries.md) (TO BE ADDED)

### 4. Analyze Telemetry Patterns (TO BE IMPLEMENTED)

Based on available data:
- **Failover indicators**:
  - Replica role changes
  - SQL process restarts
  - Service Fabric reconfiguration events
  - Planned or unplanned failovers
  
- **Quorum loss indicators**:
  - Service Fabric health reports showing quorum loss
  - Multiple replica failures simultaneously
  - Blocked reconfiguration
  - No primary replica available

### 5. Select Diagnostic Skills

**Build the selected_skills list using all evidence:**

```
selected_skills = []

# Priority 1: ICM-derived evidence (highest signal)
if icm_suggests_failover:
    selected_skills.append("failover")
if icm_suggests_quorum:
    selected_skills.append("quorum-loss")
if icm_suggests_node:
    selected_skills.append("node-health")
if icm_suggests_dump:
    selected_skills.append("dump")
if icm_suggests_error_40613_126:
    selected_skills.append("error-40613-state-126")
if icm_suggests_login_failures:
    selected_skills.append("login-failure-triage")
if icm_suggests_error_40613_127:
    selected_skills.append("error-40613-state-127")
if icm_suggests_freq_failover:
    selected_skills.append("freq-failover")
if icm_suggests_sync_recovery:
    selected_skills.append("sync-replica-recovery")
if icm_suggests_unplaced:
    selected_skills.append("unplaced-replicas")
if icm_suggests_update_slo:
    selected_skills.append("update-slo")
if icm_suggests_seeding:
    selected_skills.append("seeding-rca")
if icm_suggests_hadr_sync_commit and deployment_type in ["BC", "Premium"]:
    selected_skills.append("high-sync-commit-wait")

# Priority 2: User-provided keywords
if user_mentioned_failover and "failover" not in selected_skills:
    selected_skills.append("failover")
if user_mentioned_quorum and "quorum-loss" not in selected_skills:
    selected_skills.append("quorum-loss")
if user_mentioned_node and "node-health" not in selected_skills:
    selected_skills.append("node-health")
if user_mentioned_dump and "dump" not in selected_skills:
    selected_skills.append("dump")
if user_mentioned_error_40613_126 and "error-40613-state-126" not in selected_skills:
    selected_skills.append("error-40613-state-126")
if user_mentioned_login_failures and "login-failure-triage" not in selected_skills:
    selected_skills.append("login-failure-triage")
if user_mentioned_error_40613_127 and "error-40613-state-127" not in selected_skills:
    selected_skills.append("error-40613-state-127")
if user_mentioned_freq_failover and "freq-failover" not in selected_skills:
    selected_skills.append("freq-failover")
if user_mentioned_sync_recovery and "sync-replica-recovery" not in selected_skills:
    selected_skills.append("sync-replica-recovery")
if user_mentioned_unplaced and "unplaced-replicas" not in selected_skills:
    selected_skills.append("unplaced-replicas")
if user_mentioned_update_slo and "update-slo" not in selected_skills:
    selected_skills.append("update-slo")
if user_mentioned_seeding and "seeding-rca" not in selected_skills:
    selected_skills.append("seeding-rca")
if user_mentioned_hadr_sync_commit and "high-sync-commit-wait" not in selected_skills and deployment_type in ["BC", "Premium"]:
    selected_skills.append("high-sync-commit-wait")

# Priority 3: Database state from get-db-info
# If get-db-info returned UpdateSloTarget or AddSecondary state, include update-slo
if db_state in ["UpdateSloTarget", "AddSecondary"] and "update-slo" not in selected_skills:
    selected_skills.append("update-slo")

# Priority 4: Telemetry patterns (when implemented)
# if sqlFailovers_found: selected_skills.append("failover")
# if quorum_patterns_found: selected_skills.append("quorum-loss")

# Default if nothing found
if selected_skills is empty:
    selected_skills = ["failover"]
```

**Decision matrix:**

| ICM Flag | User Keyword | Telemetry | DB State | Selected Skills | Confidence |
| -------- | ------------ | --------- | -------- | --------------- | ---------- |
| `icm_suggests_quorum` | - | - | - | `["quorum-loss"]` | High |
| `icm_suggests_failover` | - | - | - | `["failover"]` | High |
| `icm_suggests_node` | - | - | - | `["node-health"]` | High |
| `icm_suggests_dump` | - | - | - | `["dump"]` | High |
| `icm_suggests_error_40613_126` | - | - | - | `["error-40613-state-126"]` | High |
| `icm_suggests_login_failures` | - | - | - | `["login-failure-triage"]` | High |
| `icm_suggests_error_40613_127` | - | - | - | `["error-40613-state-127"]` | High |
| `icm_suggests_freq_failover` | - | - | - | `["freq-failover"]` | High |
| `icm_suggests_sync_recovery` | - | - | - | `["sync-replica-recovery"]` | High |
| `icm_suggests_unplaced` | - | - | - | `["unplaced-replicas"]` | High |
| `icm_suggests_update_slo` | - | - | - | `["update-slo"]` | High |
| `icm_suggests_quorum` + `icm_suggests_node` | - | - | - | `["quorum-loss", "node-health"]` | High |
| `icm_suggests_hadr_sync_commit` (BC/Premium only) | - | - | - | `["high-sync-commit-wait"]` | High |
| - | "failover" | - | - | `["failover"]` | High |
| - | - | SqlFailovers found | - | `["failover"]` | Medium |
| - | - | - | UpdateSloTarget or AddSecondary | `["update-slo"]` | Medium |
| - | - | - | - | `["failover"]` (default) | Low |

**Multiple skills** are selected when evidence suggests overlapping issue types (e.g., node failure causing quorum loss).

**Default**: If no clear indicators found → `["failover"]`

### 6. Validate Selection

If incident type is ambiguous:
> ⚠️ **Incident type unclear.** Defaulting to the `failover` skill for investigation.
> 
> Consider refining the triage logic if this becomes a frequent issue.

## Output (MANDATORY)

**⚠️ CRITICAL**: The triage output is MANDATORY and must appear **exactly once** in the final investigation report.

**Timing Rule**:
- Do NOT display triage output during intermediate data gathering steps
- Do NOT display triage output immediately after triage is complete
- The "✅ Triage Complete" section should appear **only in the final structured report**, after the Incident Summary and Database Environment sections, and before the detailed diagnostic analysis

**Why**: Displaying triage output during intermediate steps AND in the final report causes duplicate sections, which confuses users.

Return to the calling agent:
- **selected_skills**: Array of skill names (e.g., `["failover"]` or `["failover", "quorum-loss"]`)
- **triage_reason**: Brief explanation of why these skills were selected
- **triage_evidence**: Key keywords/patterns found that led to the selection
- **confidence**: `"high"`, `"medium"`, `"low"` (based on evidence strength)

**⚠️ CRITICAL — Triage Evidence Must Reflect Only Data Available at Triage Time:**

The Triage Complete section is a **point-in-time snapshot**. Reason, Evidence, and Confidence must only cite data sources that were available when triage ran:

- **When ICM ID was provided in Step 1**: Reason/Evidence may cite ICM title, tags, description, AI summary, and custom fields.
- **When NO ICM ID was provided**: Reason/Evidence must **NOT** reference ICM titles, ICM tags, ICM descriptions, or ICM AI summaries. The only valid evidence sources are:
  - User-provided keywords/parameters
  - DBINFO results (cluster migration, database states, multiple configs)
  - Absence of ICM context ("No ICM ID provided; defaulting to failover")

Do **NOT** retroactively update the Triage Complete section with information discovered after triage has completed.

**Confidence levels:**
| Level | Criteria |
| ----- | -------- |
| **High** | ICM title/description clearly indicates issue type OR user explicitly specified |
| **Medium** | Keywords found in ICM or telemetry patterns match |
| **Low** | No clear indicators, defaulting to failover |

**⚠️ CRITICAL — Confidence Does NOT Affect Skill Execution:**

Confidence is **purely diagnostic metadata** — it explains *why* skills were selected, nothing more.

- **Once skills are selected, they MUST be executed with full rigor regardless of confidence level.**
- Low confidence does NOT mean the agent may loosely interpret, skip steps, abbreviate output, or deviate from the skill's documented workflow.
- A "Low" confidence `failover` skill execution must produce **identical depth, format, and completeness** as a "High" confidence execution.
- Every query, every output section, every formatting rule in the skill's SKILL.md and references/ applies unconditionally.

**MANDATORY Display Format (appears EXACTLY ONCE in final report):**

```
## ✅ Triage Complete

| Field | Value |
|-------|---------|
| **Selected Skills** | {selected_skills} |
| **Reason** | {triage_reason} |
| **Evidence** | {triage_evidence} |
| **Confidence** | {confidence} |
```

**⚠️ IMPORTANT**: This section must appear **exactly once** in the entire response. Do not duplicate it.

**Example output:**

```
## ✅ Triage Complete

| Field | Value |
|-------|-------|
| **Selected Skills** | ["failover", "node-health"] |
| **Reason** | ICM indicates node failure causing replica build delays and failover issues |
| **Evidence** | Tags: "Disk I/O Error", "Replica Build Delay", "Node Deactivation"; AI summary mentions "node failures", "delayed replica failover" |
| **Confidence** | High |
```

**After triage is complete**, the agent stores the results internally and proceeds to invoke each selected skill in sequence. The triage output is included in the final report only. **Reminder: every selected skill must be executed exactly as documented — confidence level has no bearing on execution quality or completeness.**

## Current Implementation Status

**Implemented:**
- [x] Extract ICM incident context (title, description, severity, AI summary)
- [x] Keyword extraction from ICM for skill routing
- [x] User keyword detection
- [x] Multi-skill selection based on evidence

**Pending:**
- [ ] SqlFailovers/LoginOutages query analysis
- [ ] Service Fabric health report pattern detection
- [ ] Telemetry-based pattern recognition

## Future Enhancements

- [ ] Implement SqlFailovers/LoginOutages query analysis
- [ ] Add Service Fabric health report pattern detection
- [ ] Integrate with alert classification from ICM
- [ ] Add machine learning model for pattern recognition
- [ ] Support additional HA issue types (e.g., backup/restore, geo-replication)
- [ ] Enhance confidence scoring with historical data

## Usage Notes

This skill should be called by the agent after the `execute-kusto-query` skill and the `get-db-info` skill, but before invoking diagnostic skills. The selected skill names are used to route the investigation to the appropriate specialized diagnostic skills. The agent may invoke multiple diagnostic skills if triage determines the incident has characteristics of multiple issue types.
