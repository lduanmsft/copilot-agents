---
name: similar-incidents
description: Searches ICM for incidents with similar symptoms to provide historical context and identify patterns. This skill should be called AFTER diagnostic skills complete.
---

# Similar Incidents Search

This skill searches ICM (Incident Management system) for past incidents with similar symptoms, error patterns, or database configurations to provide historical context for the current investigation.

## Allowed Tools (STRICT WHITELIST)

**⚠️ CRITICAL: Only the following tools may be used for similar incidents search. Using any other tools (e.g., ADO work item search, ADO wiki search) is PROHIBITED.**

### Primary Search Tools

| Tool | Purpose | When to Use |
| ---- | ------- | ----------- |
| `mcp_icm-prod_get_similar_incidents` | ICM built-in ML similarity search | Step 2.1 - Always if incident ID available |

### Context & Summary Tools

| Tool | Purpose | When to Use |
| ---- | ------- | ----------- |
| `mcp_icm-prod_get_ai_summary` | Get AI-generated incident summary | Step 2.2 - For each similar incident found |
| `mcp_icm-prod_get_incident_context` | Get detailed incident metadata | Optional - For additional context |
| `mcp_icm-prod_get_incident_details_by_id` | Get full incident details | Optional - For resolution notes |

### 🚫 PROHIBITED Tools

**DO NOT use these tools for similar incidents search:**
- ❌ `mcp_ado_search_workitem` - This is for ADO work items, NOT ICM incidents
- ❌ `mcp_ado_search_wiki` - This is for wiki documentation, NOT incident search
- ❌ Any other ADO tools (`mcp_ado_*`) - These are not for ICM incident search
- ❌ `semantic_search` or `grep_search` - These search local files, not ICM

**If you find yourself reaching for a tool not in the whitelist above, STOP and reconsider.**

---

## Required Information

This skill requires the following inputs (should be provided by the calling agent):

### From User or ICM:
- **Current Incident ID** (optional - if investigating an existing incident)
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)

### From get-db-info skill:
- **service_level_objective** (e.g., "S3", "P2", "GP_Gen5_2")

## Output Requirement (MANDATORY)

**⚠️ CRITICAL**: The "📊 Similar Incidents Analysis" section MUST appear in EVERY investigation report, regardless of whether similar incidents are found.

- If similar incidents are found → Include full analysis with incident details
- If NO similar incidents are found → Still include the section using the no-results format from [references/report.md](references/report.md)

**This section is MANDATORY and cannot be skipped.**

## Workflow

### 1. Validate Inputs

Ensure required parameters are provided:
- LogicalServerName, LogicalDatabaseName

### 2. Search ICM for Similar Incidents

---

### 🚨🚨 MANDATORY EXECUTION CHECKLIST 🚨🚨

**STOP! Before proceeding, you MUST complete both of the following steps. Track your progress:**

| Step | Description | Status |
| ---- | ----------- | ------ |
| 2.1 | ICM built-in similarity search | ⬜ NOT STARTED |
| 2.2 | Deduplicate and get AI summaries | ⬜ NOT STARTED |


**⛔⛔⛔ ABSOLUTE ENFORCEMENT RULES ⛔⛔⛔**

1. **Both steps 2.1-2.2 are MANDATORY** - you MUST execute both steps using the specified tool
2. **Verify both steps show ✅ COMPLETE** before presenting Similar Incidents Analysis
3. **Use the output format from [references/report.md](references/report.md)** for the Similar Incidents Analysis section

**📋 Keep all relevant incidents from Step 2.1, then deduplicate, rank, and keep top ≤5 for AI summaries in Step 2.2.**

#### Step 2.1: Use ICM Built-in Similarity (MANDATORY if Incident ID Available)

**Run this if you have an ICM incident ID.** ICM's ML-based similarity algorithm often finds relevant matches.

```
Tool: mcp_icm-prod_get_similar_incidents
Parameters:
  incidentId: {current_incident_id}
```

✅ Mark Step 2.1 as COMPLETE → **PROCEED IMMEDIATELY to Step 2.2**

---

#### Step 2.2: Deduplicate and Get AI Summary for Top Incidents

**Collect all results from Step 2.1:**
1. Deduplicate incidents by ICM ID
2. Rank by relevance (see Section 3)
3. Select final top ≤5 most relevant incidents

For each relevant incident in the final list, get the AI-generated summary:

```
Tool: mcp_icm-prod_get_ai_summary
Parameters:
  incidentId: "{incident_id}"
```

**If NO incidents were found from Step 2.1:**
- This is a valid outcome — proceed to Step 5 (Present Findings) using the no-results format from [references/report.md](references/report.md)

✅ Mark Step 2.2 as COMPLETE

---

### 3. Filter and Rank Results

Rank the incidents returned by ICM similarity search by relevance:

**Ranking Criteria:**
1. Same logical server name AND same database name (highest relevance)
2. Same logical server name (different database)
3. Same major error/issue type
4. ICM similarity rank (order returned by `mcp_icm-prod_get_similar_incidents`)
5. Recency (prefer last 60 days)
6. Resolution status (prefer resolved with RCA)
7. Same owning team

**Final Output:** Select top ≤5 most relevant incidents.

### 4. Extract Insights

For each of the top similar incidents, extract:

**From AI Summary (`mcp_icm-prod_get_ai_summary`):**
- Root cause summary
- Key symptoms identified
- Resolution actions

**From Incident Context (`mcp_icm-prod_get_incident_context`):**
- Severity and duration
- Owning team
- Related services/regions
- Customer impact

#### 4.1 Parse RCA Summaries for Root Causes

Extract structured root cause information from AI summaries:

```
For each incident summary, identify:
1. Primary root cause category (see categorization below)
2. Contributing factors
3. Trigger event (what initiated the incident)
4. Impact scope (single DB, server, region, etc.)
```

**Root Cause Extraction Keywords:**

| Category | Keywords to Match |
| -------- | ----------------- |
| Infrastructure | "node health", "node issues", "hardware", "bugcheck", "memory", "disk", "network" |
| Failover | "failover", "replica transition", "role change", "primary" |
| Quorum | "quorum", "partition", "replica count", "majority" |
| Resource | "CPU", "memory", "throttling", "resource exhaustion" |
| Configuration | "misconfiguration", "setting", "policy", "zone" |
| Deployment | "deployment", "upgrade", "update", "code push" |

#### 4.2 Extract Mitigation Actions from Incident History

For resolved incidents, extract the mitigation steps taken:

```
Tool: mcp_icm-prod_get_incident_details_by_id
Parameters: incidentId = {incident_id}

Extract from resolution notes:
1. Immediate mitigation (what stopped the bleeding)
2. Long-term fix (permanent resolution)
3. Escalation path (teams involved)
4. Time to mitigate (duration from detection to mitigation)
```

**Common Mitigation Patterns:**

| Issue Type | Typical Mitigations |
| ---------- | ------------------- |
| Node failure | Node replacement, replica rebuild, traffic reroute |
| Long failover | Retry failover, manual intervention, replica heal |
| Quorum loss | Force quorum, add replicas, zone rebalance |
| Tempdb issues | Extend recovery timeout, restart SQL, increase tempdb size |
| Write blocked | Clear write status, failover to healthy replica |

#### 4.3 Identify Common Patterns Across Incidents

Analyze the collection of similar incidents for patterns:

**Time-based Patterns:**
- Peak hours (8am-6pm local time) vs off-peak
- Maintenance windows (Tuesdays, Thursdays)
- Monthly/quarterly patterns

**Infrastructure Patterns:**
- Same cluster or ring
- Same region or zone
- Same hardware generation

**Workload Patterns:**
- Same service tier (GP/BC)
- Same database size range
- Same customer segment

**Pattern Detection Algorithm:**
```
1. Group incidents by root cause category
2. Calculate frequency: count / total_incidents
3. Identify time clustering (>2 incidents within 7 days)
4. Flag recurring patterns (>30% frequency)
5. Note any common infrastructure (cluster, region, zone)
```

#### 4.4 Categorize Incidents by Root Cause Type

Assign each incident to one primary category:

| Category | Description | Typical TTM |
| -------- | ----------- | ----------- |
| **INFRA-NODE** | Node-level infrastructure failure | 15-30 min |
| **INFRA-NETWORK** | Network connectivity issues | 5-60 min |
| **INFRA-STORAGE** | Storage or disk issues | 30-120 min |
| **FAILOVER-SLOW** | Failover exceeding SLA | 10-45 min |
| **FAILOVER-FAILED** | Failover did not complete | 30-120 min |
| **QUORUM-TRANSIENT** | Temporary quorum loss | 5-15 min |
| **QUORUM-PERSISTENT** | Extended quorum loss | 30-180 min |
| **RESOURCE-CPU** | CPU exhaustion or throttling | 15-60 min |
| **RESOURCE-MEMORY** | Memory pressure | 15-60 min |
| **CONFIG-ERROR** | Misconfiguration issue | Variable |
| **DEPLOYMENT** | Deployment or upgrade issue | Variable |
| **UNKNOWN** | Root cause not determined | Variable |

**Categorization Output:**
```
Incident Categorization Summary:
- INFRA-NODE: 3 incidents (40%)
- FAILOVER-SLOW: 2 incidents (27%)
- QUORUM-TRANSIENT: 2 incidents (27%)
- UNKNOWN: 1 incident (6%)

Most Common Category: INFRA-NODE
Average TTM for INFRA-NODE: 22 minutes
```

### 5. Present Findings (MANDATORY)

**⚠️ CRITICAL**: This section MUST always be included in the final report, even if no similar incidents are found.

**⚠️ MANDATORY OUTPUT**: Before outputting the "📊 Similar Incidents Analysis" section, you **MUST read** `.github/skills/Common/similar-incidents/references/report.md` and **copy-paste** the Summary Section template exactly, replacing placeholders with actual values. The step tracking table (Steps 2.1 and 2.2) is REQUIRED — never omit it or replace it with free-form text.

---

## Integration with Other Skills

### Before This Skill:
- skill `execute-kusto-query` - Get region information
- skill `get-db-info` - Get database configuration for matching
- skill `triage` - Determine issue types
- Diagnostic skills selected by triage (e.g., `failover`, `quorum-loss`, `node-health`, etc.)

### After This Skill:
- Final report generation - Incorporate historical context into the investigation summary

### Execution Order:
This skill should be executed **AFTER** all diagnostic skills complete, so the investigation report already contains diagnostic context before adding the similar-incidents section.

## Reference

See [references/report.md](references/report.md) for detailed report formatting and JSON output structure.

## Usage Note

- Results should be treated as **guidance, not definitive answers**
- Always validate historical patterns against current telemetry
- Similar incidents may have different root causes despite similar symptoms
- Use historical context to **inform, not replace** current investigation
