---
name: connectivity-triage
description: Determines the type of connectivity issues (login failure, session disconnect, etc.) by analyzing symptoms, telemetry patterns, and initial data. Select the appropriate diagnostic skills for detailed investigation. The Connectivity agent uses this skill to triage incidents and route them to specialized diagnostic skills.
---

<!-- Note: This skill is modeled from the triage skill in the Availability agent, and credit goes to xpeng88 and the availability team for the original design and implementation. The logic is adapted to focus on connectivity-related issues rather than availability/failover, but the overall structure and approach are similar. TODO: Find a way to make the structure a template which can be reused and maintained among agents. -->

# Connectivity Issue Triage

This skill analyzes available information to determine the type of connectivity issues and route to the appropriate diagnostic skills for detailed investigation.

## Required Information

### From User or ICM:
- **Incident ID** (optional - if investigating an existing ICM incident)
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

OR

- **Connectivity Ring Name** (e.g., `cr11.eastasia1-a.control.database.windows.net`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill:
- **deployment_type** (e.g., "GP without ZR", "GP with ZR", "BC")
- **service_level_objective**
- All database configuration variables

### Optional User Hints:
- Explicit keywords: "login failure", "disconnect", etc.
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

**⚠️ CRITICAL — Allowed Triage Inputs (STRICT ALLOWLIST)**:
Only the following five ICM sources may be used for triage skill selection:

| Field | Variable | Triage Use |
| ----- | -------- | ---------- |
| **Title** | `icm_title` | Primary keyword source |
| **Description** | `icm_description` | Symptoms, error codes |
| **Severity** | `icm_severity` | Urgency indication |
| **Alert Source** | `icm_alert_source` | Monitor type hints |
| **AI Summary Tags** | `icm_ai_summary_tags` | AI-generated classification tags (the `Tags` array from the AI summary only) |

**🚫 PROHIBITED Triage Inputs for Root Cause Analysis:**
- ❌ ICM discussion entries (human-posted comments, investigation notes)
- ❌ AI Summary free-text fields (Description, Causes, Symptoms, BriefSummary, LatestUpdate)
- ❌ Any other human analysis or manually-added content

These sources must **NOT** be used to derive root cause conclusions in subsequent diagnostic skills. However, they may serve as **non-authoritative hints** for triage skill selection in this step, without influencing final diagnostic outcomes.

**Step 1d: Analyze ICM content for skill keywords:**

Scan **only** `icm_title`, `icm_description`, and `icm_ai_summary_tags` for these keywords:

| Keywords Found | Set Flag | Skill to Include |
| -------------- | -------- | ---------------- |
| "Gateway node low login success rate", "GatewayNodeLowLoginSuccessRate" | `icm_suggests_gw_node_low_success = true` | `gateway-node-low-login-success-rate` |
| "connectivity", "login failure" | `icm_suggests_login_failure = true` | `login-failure` |
| "session disconnect", "timeout" | `icm_suggests_session_disconnect = true` | `session-disconnect` |
| "HasXdbHostRestarts", "xdbhost restart" | `icm_suggests_xdbhost_restart = true` | `xdbhost-restart` |
| "BRAIN detected unusual trend in SLI "Login Success-Rate - Azure SQL DB"" | `icm_suggests_Brain_outage = true` | `brain-low-login-success-rate` |
| "nodes are unhealthy", "Gateway nodes are unhealthy", "Control Ring Nodes Unhealthy", "20% of Gateway nodes" | `icm_suggests_control_ring_nodes_unhealthy = true` | `control-ring-nodes-unhealthy` |

**Example ICM analysis:**

```
ICM Title: "SQL DB login failure for server xyz"
ICM Description: "Customer reported failures to login to the database."
ICM AI Summary Tags: [{"TagName": "Login Failure", "Score": 5}, {"TagName": "Session Timeout", "Score": 3}]

Analysis:
- "login failure" in title → icm_suggests_login_failure = true
- "Session Timeout" in AI summary tags → icm_suggests_session_disconnect = true

Result: Select skills ["login-failure", "session-disconnect"]
```

> **⚠️ Reminder**: ICM discussion entries and AI summary free-text may contain human analysis or speculation. These must NOT influence root cause conclusions in downstream diagnostic skills. Only telemetry data (Kusto query results) should drive root cause analysis.

### 2. Check for Explicit Keywords from User

If user explicitly mentioned:
- **"login failure"**, **"connectivity"** → Include the `login-failure` skill
- **"session disconnect"**, **"timeout"** → Include the `session-disconnect` skill

### 3. Select Diagnostic Skills

**Build the selected_skills list using all evidence:**

```
selected_skills = []

# Priority 1: ICM-derived evidence
if icm_suggests_Brain_outage:
    selected_skills.append("brain-low-login-success-rate")
if icm_suggests_xdbhost_restart:
    selected_skills.append("xdbhost-restart")
if icm_suggests_login_failure:
    selected_skills.append("login-failure")
if icm_suggests_session_disconnect:
    selected_skills.append("session-disconnect")
if icm_suggests_gw_node_low_success:
    selected_skills.append("gateway-node-low-login-success-rate")
if icm_suggests_control_ring_nodes_unhealthy:
    selected_skills.append("control-ring-nodes-unhealthy")

# Priority 2: User-provided keywords
if user_mentioned_login_failure:
    selected_skills.append("login-failure") if not already present
if user_mentioned_session_disconnect:
    selected_skills.append("session-disconnect") if not already present

# Priority 3: Telemetry patterns (when implemented)
# if login_failure_found: selected_skills.append("login-failure")
# if session_disconnect_found: selected_skills.append("session-disconnect")

# Default if nothing found
if selected_skills is empty:
    selected_skills = ["login-failure"]  # Default to login-failure for connectivity issues
```

**Decision matrix:**

| ICM Flag | User Keyword | Telemetry | Selected Skills | Confidence |
| -------- | ------------ | --------- | --------------- | ---------- |
| `icm_suggests_gw_node_low_success` | - | - | `["gateway-node-low-login-success-rate"]` | High |
| `icm_suggests_control_ring_nodes_unhealthy` | - | - | `["control-ring-nodes-unhealthy"]` | High |
| `icm_suggests_Brain_outage` | - | - | `["brain-low-login-success-rate"]` | High |
| `icm_suggests_xdbhost_restart` | - | - | `["xdbhost-restart"]` | High |
| `icm_suggests_login_failure` | - | - | `["login-failure"]` | High |
| `icm_suggests_session_disconnect` | - | - | `["session-disconnect"]` | High |
| - | "failover" | - | `["failover"]` | High |
| - | - | SqlFailovers found | `["failover"]` | Medium |
| - | - | - | `["login-failure"]` (default) | Low |

**Multiple skills** are selected when evidence suggests overlapping issue types (e.g., login failure accompanied with session disconnect).

**Default**: If no clear indicators found → `["login-failure"]`

### 4. Validate Selection

If incident type is ambiguous:
> ⚠️ **Incident type unclear.** Defaulting to the `login-failure` skill for investigation.
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
- **selected_skills**: Array of skill names (e.g., `["login-failure"]` or `["login-failure", "session-disconnect"]`)
- **triage_reason**: Brief explanation of why these skills were selected
- **triage_evidence**: Key keywords/patterns found that led to the selection
- **confidence**: `"high"`, `"medium"`, `"low"` (based on evidence strength)

**Confidence levels:**
| Level | Criteria |
| ----- | -------- |
| **High** | ICM title/description clearly indicates issue type OR user explicitly specified |
| **Medium** | Keywords found in ICM or telemetry patterns match |
| **Low** | No clear indicators, defaulting to login-failure |

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
| **Selected Skills** | ["login-failure", "session-disconnect"] |
| **Reason** | ICM indicates login failure and session disconnect issues |
| **Evidence** | Tags: "Login Failed", "Session Timeout"; AI summary mentions "login failures", "session timeouts" |
| **Confidence** | High |
```

**After triage is complete**, the agent stores the results internally and proceeds to invoke each selected skill in sequence. The triage output is included in the final report only.

## Current Implementation Status

**Implemented:**
- [x] Extract ICM incident context (title, description, severity, AI summary)
- [x] Keyword extraction from ICM for skill routing
- [x] User keyword detection
- [x] Multi-skill selection based on evidence

## Future Enhancements

- [ ] Integrate with alert classification from ICM
- [ ] Add machine learning model for pattern recognition
- [ ] Support additional connectivity issue types
- [ ] Enhance confidence scoring with historical data

## Usage Notes

This skill should be called by the agent after the `execute-kusto-query` skill and the `get-db-info` skill, but before invoking diagnostic skills. The selected skill names are used to route the investigation to the appropriate specialized diagnostic skills. The agent may invoke multiple diagnostic skills if triage determines the incident has characteristics of multiple issue types.
