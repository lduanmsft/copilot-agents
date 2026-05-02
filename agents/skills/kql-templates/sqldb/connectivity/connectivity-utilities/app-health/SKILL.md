---
name: app-health
description: Checks SQL Server application health on a DB node by detecting process restarts (process_id changes in MonSQLSystemHealth), auditing automation/user actions (LoginOutages and MonNonPiiAudit for sqlservr actions), and reviewing system health messages with classification as informational vs warning/error. Use when investigating whether the SQL instance experienced restarts, external kill commands, or abnormal system events during a connectivity incident.
---

# App Health Check

Verify the health of the SQL Server application (`sqlservr`) on the DB node during the incident window. This utility skill checks for process restarts, external automation actions, and abnormal system health messages.

## Required Information

### From User or ICM:
- **LogicalServerName** (e.g., `my-server`)
- **LogicalDatabaseName** (e.g., `my-db`)
- **StartTime** (UTC)
- **EndTime** (UTC)

### From execute-kusto-query skill:
- **kusto-cluster-uri**
- **kusto-database**

### From get-db-info skill:
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **NodeName** (DB node hosting the primary replica)

## Investigation Workflow

**Important**: Execute all steps in order. Output results after each step before proceeding to the next.

### Step 1: Detect Process Restarts

Check if the `sqlservr` process restarted during the incident window by looking for distinct `process_id` values.

**Execute query:** AH100 from [references/queries.md](references/queries.md)

**Analysis:**
- **Single `process_id`** → No restart detected. Note this and proceed to Step 2.
- **Multiple `process_id` values** → Restart confirmed. Record:
  - Old process: last seen at `max_time`
  - New process: first seen at `min_time`
  - Restart gap = difference between these timestamps
  - 🚩 Flag if gap > 60 seconds

### Step 2: Check for Automation/User Actions

Determine if any automation or user actions were performed that could explain or correlate with a restart.

#### Step 2.1: LoginOutages Audit

**Execute query:** AH200 from [references/queries.md](references/queries.md)

**Analysis:**
- Look for `OutageReasonLevel1/2/3` entries that indicate CAS kills, bot actions, or other automated interventions
- Correlate timestamps with any restart gap from Step 1
- 🚩 Flag actions temporally close to a detected restart

#### Step 2.2: MonNonPiiAudit Trail

**Execute query:** AH210 from [references/queries.md](references/queries.md)

**Analysis:**
- Check if `request` or `parameters` contain `sqlservr` — these directly target the SQL Server process
- Look for `KillProcess`, `ExecuteKillProcess` actions
- 🚩 Flag `sqlservr`-targeting actions near the restart timestamp
- Note other actions as informational context

### Step 3: Review System Health Messages

Examine system health messages from MonSQLSystemHealth for warning/error patterns.

#### Step 3.1: 🔴 MANDATORY — Aggregated Warning Pattern Screen

**Execute query:** AH305 from [references/queries.md](references/queries.md)

**⚠️ CRITICAL**: This step MUST be executed FIRST before any raw message queries. AH305 uses KQL aggregation to detect known warning/error patterns (I/O slow, memory pressure, deadlocks, stack dumps, etc.) and returns a small summary table regardless of how many raw messages exist. This prevents missing critical events buried in large result sets.

**Analysis:**
- If **any row** is returned, that pattern is a 🚩 **warning/error** that must be reported
- For each pattern found, immediately run **AH305_pre** from [references/queries.md](references/queries.md) to determine if it is acute or chronic

**Output a table:**

| Pattern | MessageCount | TotalOccurrences | MinTime | MaxTime | Found Pre-Window? | Assessment |
|---------|-------------|------------------|---------|---------|-------------------|------------|
| ... | ... | ... | ... | ... | Yes/No | 🚩 Acute / Chronic |

- **🚩 Acute**: Pattern does NOT appear in AH305_pre results — incident-specific, highlight prominently
- **Chronic**: Pattern also appears in AH305_pre — pre-existing, note but deprioritize

#### Step 3.2: Raw Message Drill-Down (Optional)

**Only execute if** AH305 found warning patterns that need detailed investigation (e.g., extracting file paths from I/O slow messages, analyzing timeline distribution of a specific pattern).

**Execute query:** AH300 from [references/queries.md](references/queries.md) — **add a `message contains` filter** for the specific pattern being investigated. Do NOT retrieve all unfiltered messages.

**Classification rules** — Use best judgement to see if a message is informational only or a warning/error.

**Output a table:**

| Timestamp | Message (summary) | Classification |
|-----------|--------------------|----------------|
| ... | ... | 🚩 Warning/Error or ℹ️ Informational |

#### Step 3.3: Check Warning/Error Messages Outside Incident Window (Legacy fallback)

**Only execute if** Step 3.2 was run and found additional warning/error messages not already classified by AH305/AH305_pre.

**Execute query:** AH310 from [references/queries.md](references/queries.md) **twice**:
1. **Pre-window**: `CheckStartTime` = StartTime minus 1 hour, `CheckEndTime` = StartTime
2. **Post-window**: `CheckStartTime` = EndTime, `CheckEndTime` = EndTime plus 1 hour

**Analysis:**

| Warning/Error Message | Found Pre-Window? | Found Post-Window? | Assessment |
|-----------------------|--------------------|--------------------|------------|
| ... | Yes/No | Yes/No | Chronic / 🚩 Acute |

- **Chronic**: Message appears both inside and outside the window — likely persistent background issue
- **🚩 Acute**: Message appears only during the incident window — likely incident-related and should be highlighted

## Summary Output

After completing all steps, provide a concise summary:

1. **Process Restart**: Was a restart detected? If yes, what was the gap duration?
2. **External Trigger**: Were any automation/user actions (CAS kill, bot, manual) correlated with the restart?
3. **System Health (Aggregated Patterns)**: List all patterns detected by AH305, with their acute/chronic classification, message counts, and time ranges. Acute patterns should be highlighted as 🚩.
4. **System Health (Raw Messages)**: If Step 3.2 was executed, list any additional findings from raw message inspection.
