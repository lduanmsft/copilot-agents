---
name: worker-thread-exhaustion-analysis
description: Check worker thread usage and identify possible root causes when worker thread exhaustion occurs.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Worker Thread Exhaustion Analysis

## Skill Overview

This skill checks worker thread usage and identifies possible root causes if worker thread exhaustion happened. Worker thread exhaustion can occur due to excessive blocking, sudden surge in active sessions, and other factors.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |

## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|---------|
| Task 1 | Query worker thread exhaustion events | Always |
| Task 2 | Display recommended next steps | ONLY if worker exhaustion detected |

---

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where message contains 'The request limit for the database' or message contains 'The request limit for the elastic pool'
| summarize count=count() by bin(originalEventTimestamp,1h)
| order by originalEventTimestamp asc
```

#### Output
Follow these instructions exactly:

1. **If query returns no results (rowcount = 0)**:
   - Display: "Worker threads exhaustion didn't happen."
   - **STOP HERE** - Do not proceed to Task 4

2. **If query returns results (rowcount > 0)**:
   - Display the hourly distribution as a table
   - Calculate and display the **Total Count** (sum of all hourly counts)
   - Continue to Task 4 to display recommended next steps

| Hour (UTC) | Count |
|------------|-------|
| `originalEventTimestamp` | `count` |

**Total Count**: Sum of all hourly counts

### Task 2: Display Recommended Next Steps

**Condition**: Only execute this task if Task 1 query returned results (rowcount > 0). If no results were returned, this skill has already terminated at Task 1.

#### Output

Display the following message exactly as written:

> 🔍 **Worker Thread Exhaustion Detected - Recommended Investigation Steps**
> 
> Worker thread exhaustion has been detected. To identify the root cause, consider running the following skills:
> 
> | Skill | Description | Link |
> |-------|-------------|------|
> | **Worker Session Similarity Analysis** | Check if session growth is causing worker thread increases | [worker-session-similarity-analysis.md](worker-session-similarity-analysis.md) |
> | **Blocking Detection** | Identify if blocking is contributing to worker thread exhaustion | [blocking-detection.md](../../blocking/references/blocking-detection.md) |
> | **Non-Yielding** | Check for non-yielding scheduler issues that may be causing worker threads to be held | [non-yielding.md](../../sqlos/references/non-yielding.md) |

You may also need to collect an Azure Profiler trace when the issue is occurring, if it cannot be identified from the common issues above.
---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Worker Thread Exhaustion is Detected

#### Worker Thread Exhaustion Analysis Results

**Yes, worker thread exhaustion was detected during the investigation period.**

#### Hourly Distribution

| Hour (UTC) | Count |
|------------|-------|
| 2026-01-15 10:00 | 1,250 |
| 2026-01-15 11:00 | 2,845 |
| 2026-01-15 12:00 | 948 |

**Total Count**: 5,043

---

> 🔍 **Worker Thread Exhaustion Detected - Recommended Investigation Steps**
> 
> Worker thread exhaustion has been detected. To identify the root cause, consider running the following skills:
> 
> | Skill | Description | Link |
> |-------|-------------|------|
> | **Worker Session Similarity Analysis** | Check if session growth is causing worker thread increases | [worker-session-similarity-analysis.md](worker-session-similarity-analysis.md) |
> | **Blocking Detection** | Identify if blocking is contributing to worker thread exhaustion | [blocking-detection.md](../../blocking/references/blocking-detection.md) |
> | **Non-Yielding** | Check for non-yielding scheduler issues that may be causing worker threads to be held | [non-yielding.md](../../sqlos/references/non-yielding.md) |

You may also need to collect an Azure Profiler trace when the issue is occurring, if it cannot be identified from the common issues above.
---

### When No Worker Thread Exhaustion is Detected

#### Worker Thread Exhaustion Analysis Results

**No, worker thread exhaustion was NOT detected during the investigation period.**

#### Summary

Worker threads exhaustion didn't happen.

