---
name: blocking
description: Comprehensive blocking and deadlock analysis including blocking detection, lead blocker identification, blocking chain visualization, deadlock detection, and long-running transaction analysis for Azure SQL databases.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
keywords: ['blocking', 'blocked', 'blocker', 'deadlock', 'lock', 'LCK_M', 'worker thread', 'contention', 'long-running transaction', 'deadlock detection', 'query hash']
---

# Blocking Analysis Skill

## Skill Overview

This skill provides comprehensive blocking and deadlock analysis in Azure SQL databases. It detects blocking conditions, identifies lead blockers at the root of blocking chains, visualizes blocking relationships, detects deadlocks, identifies queries involved in deadlocks, and analyzes long-running transactions that may be holding locks.

**Default Checks (Always Run)**:
- ⭐ Peak Blocking Detection
- ⭐ Deadlock Detection

**Conditional Checks (Run When Relevant)**:
- Lead Blocker Sessions (if blocking detected)
- Long-Running Transactions
- Top Deadlock Queries

## When to Use This Skill

This skill should be triggered when the user reports or asks about:
- **Blocking issues** or sessions being blocked
- **Deadlocks** or lock contention
- **Worker thread exhaustion** or high blocked session counts
- **LCK_M_* waits** (lock waits) detected in query analysis
- **Long-running transactions** holding locks
- **Performance degradation** with lock symptoms

## Prerequisites

- Access to Kusto clusters for SQL telemetry
- Logical server name and database name
- Time range for investigation

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{monitorLoop}` | Specific monitor loop (optional) | integer | `79013` |

## Execution Order

Execute the following diagnostic checks. The checks are split into **Default Checks** (always run) and **Conditional Checks** (run based on context).

**⚠️ IMPORTANT: Output Filtering Rule**
- **ONLY display results from a sub-skill if it detects an issue (🚩)**
- **DO NOT display any output from a sub-skill if no issue is detected (✅)**
- This keeps the report concise and focused on actionable findings

---

## Default Checks (Always Run)

These checks are **MANDATORY** and should be executed in every blocking investigation.

### Step 1: Peak Blocking Detection ⭐ DEFAULT
**Reference**: [blocking-detection.md](references/blocking-detection.md)

Detects and analyzes blocking conditions at peak hours. Queries the MonBlockedProcessReportFiltered table to identify the worst blocking scenario during the investigation period, calculating the percentage of blocked sessions relative to the database's worker thread capacity.

**Blocking Severity Levels**:
| Severity Level | Blockee Session % | Impact Description |
|----------------|-------------------|-------------------|
| Small | ≤ 1% | Minor blocking, may require investigation if concerning |
| Moderate | 1% - 2% | Noticeable blocking detected |
| Massive | 2% - 10% | May cause query slowness, timeouts, and deadlocks |
| Severe | 10% - 30% | Significant performance degradation, CPU usage may decrease |
| Extremely Severe | > 30% | Risk of worker thread exhaustion, system stability impacted |

**Why default**: Blocking detection is the primary entry point for understanding if blocking exists and its severity.

**Output Rule**: Only include this section if blocking is detected.

---

### Step 2: Deadlock Detection ⭐ DEFAULT
**Reference**: [deadlock-detection.md](references/deadlock-detection.md)

Detects and analyzes deadlock conditions in Azure SQL Database. Queries the MonDeadlockReportsFiltered table to identify deadlock occurrences during the investigation period, showing the distribution of deadlocks over time.

**Why default**: Deadlock detection provides essential visibility into circular wait conditions that cause transaction failures (error 1205). Deadlocks often occur alongside blocking issues.

**Output Rule**: Only include this section if deadlocks are detected.

---

## Conditional Checks (Run Based on Context)

These checks are executed when specific patterns are identified or when investigating related issues.

### Step 3: Lead Blocker Sessions (Conditional)
**Reference**: [lead-blocker-sessions.md](references/lead-blocker-sessions.md)

Identifies the lead blocker session IDs, which are the root sessions at the head of blocking chains. A lead blocker is a session that blocks other sessions but is not itself blocked by any other session within the same monitor loop.

**When to run**:
- Step 1 (Blocking Detection) shows blocking detected
- Need to identify root cause of blocking chains
- Investigating which sessions to terminate or optimize

**Output Rule**: Only include this section if lead blockers are identified.

**Blocking Chain Visualization Example**:
```
987 (LEAD BLOCKER, running)
 └── 657
      └── 1100
           └── 1021

727 (LEAD BLOCKER, running)
 ├── 809
 └── 711
```

---

### Step 4: Long-Running Transactions (Conditional)
**Reference**: [long-running-transactions.md](references/long-running-transactions.md)

Analyzes long-running transactions that may be blocking other operations or holding locks. Identifies transactions with extended durations, categorizes them by type (tempdb, user_db, user_db_with_accessed_tempdb), and distinguishes between regular transactions and Azure DB System Tasks.

**When to run**:
- Step 1 (Blocking Detection) shows blocking detected
- ICM mentions "long-running", "transaction", or "uncommitted transaction"
- Investigating why a session is holding locks for extended periods

**Output Rule**: Only include this section if long-running transactions are detected.

---

### Step 5: Top Deadlock Queries (Conditional - USER REQUEST ONLY)
**Reference**: [top-deadlock-queries.md](references/top-deadlock-queries.md)

Identifies the top N query hashes most frequently involved in deadlocks. Shows which specific queries are causing deadlocks by extracting query hash values from the deadlock XML reports and aggregating their frequency.

**⚠️ DO NOT AUTO-INVOKE**: This check requires **explicit user request**. Do NOT automatically run this check even if deadlocks are detected.

**When to run**:
- **User explicitly requests** query hash analysis (e.g., types "top deadlock queries", "which queries caused deadlocks", "deadlock query hashes")
- Step 2 (Deadlock Detection) shows deadlocks detected (prerequisite, but not sufficient to auto-invoke)

**Output Rule**: Only include this section when the user explicitly requests it.

---

## Execution Workflow

### Task 1: Obtain Kusto Cluster Information
**CRITICAL:** Always identify the correct cluster - do NOT use default clusters

Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../../Common/execute-kusto-query/references/getKustoClusterDetails.md](../../Common/execute-kusto-query/references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Obtain Database Metadata
**Action**: Use the [appnameandnodeinfo skill](../../Common/appnameandnodeinfo/SKILL.md) to retrieve database configuration variables including AppName, NodeName, and time range information.

### Task 3: Execute Blocking Checks

**Default Checks (ALWAYS RUN)**:
Execute these checks in every blocking investigation:
1. **Peak Blocking Detection** (Step 1) ⭐
2. **Deadlock Detection** (Step 2) ⭐

**Conditional Checks (RUN WHEN RELEVANT)**:
Execute these based on findings from default checks or ICM keywords:
3. **Lead Blocker Sessions** (Step 3) - If blocking detected in Step 1
4. **Long-Running Transactions** (Step 4) - If blocking detected or ICM mentions transactions
5. **Top Deadlock Queries** (Step 5) - ⚠️ **ONLY when user explicitly requests** (do NOT auto-invoke)

**Output Filtering Rule**: 
- Run each diagnostic check
- Only display results if issues are found (🚩)
- Skip displaying sections with no findings (✅)

### Task 4: Summary
After executing all checks, provide a brief summary:
- Report blocking severity level
- List lead blocker session IDs with blocked session counts
- Identify long-running transactions if applicable
- Provide recommendations for resolution

## Output Format

```markdown
## 🔍 Blocking Analysis

### Summary
[Brief overview of blocking findings]

### Peak Blocking Detection
🚩 [Blocking severity and percentage]
**Peak Time**: [timestamp]
**Blocked Sessions**: [count] ([percentage]% of capacity)

### Deadlock Detection
🚩 [Deadlock summary]
**Total Deadlocks**: [count]
**Hourly Average**: [rate]

### Lead Blocker Sessions (if blocking detected)
🚩 [Lead blocker identification]
| Lead Blocker | Blocked Sessions Count | Total Wait Duration(ms) |
|--------------|------------------------|-------------------------|
| **[session_id]** | [count] | [duration] |

**Blocking Chain**:
[Visual representation of blocking chain]

### Long-Running Transactions (if applicable)
🚩 [Long-running transaction details]

### Top Deadlock Queries (if deadlocks detected)
🚩 [Query hashes involved in deadlocks]
| Query Hash | Deadlock Count | First Occurrence | Last Occurrence |
|------------|----------------|------------------|-----------------|
| [hash] | [count] | [timestamp] | [timestamp] |

### Recommendations
[Actionable next steps for blocking resolution]
```

## Related Skills

This skill complements other performance diagnostics:
- **Queries**: For query performance analysis (may reveal queries causing blocking)
- **CPU**: For CPU analysis (blocking can mask as low CPU when queries are waiting)
- **out-of-disk**: For storage issues that may cause blocking
- **Deadlock**: For deadlock-specific analysis

## Notes

- This skill has **2 default checks** that ALWAYS run: blocking detection and deadlock detection
- **3 conditional checks** run based on findings or ICM keywords: lead blocker sessions, long-running transactions, and top deadlock queries
- The `monitorLoop` value from Step 1 is used in Step 3 (Lead Blocker Sessions) to identify the exact blocking snapshot
- Lead blockers should be investigated first - resolving them resolves the entire blocking chain
- Multiple blocking chains may exist simultaneously - analyze each lead blocker separately
- Follow the output filtering rule strictly to keep reports focused on actionable findings
