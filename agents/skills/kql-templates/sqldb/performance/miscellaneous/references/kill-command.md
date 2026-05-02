---
name: kill-command
description: Detect if T-SQL KILL <spid> command was executed and its impact on CPU resource accounting discrepancies between User Pool CPU and QDS reports.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug T-SQL KILL Command Detection

## Skill Overview

This skill analyzes whether the T-SQL `KILL <spid>` command was executed against the database to terminate user sessions or queries.

> **⚠️ Note**: This skill detects the **T-SQL `KILL <spid>` command** (used to terminate SQL Server sessions/queries), **NOT** the Kill-Process CAS command (used for Azure platform-level process termination).

When a query is terminated via `KILL <spid>`, the CPU resources consumed by that query before termination are **not** accounted for by Query Data Store (QDS). This can cause discrepancies between User Pool CPU usage and the combined total of CPU usage reported by 'QDS', 'Successful Compilation', and 'Failed Compilation'.

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

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute Kusto query to detect kill commands | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithPreciseTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

**Purpose**: Show the hourly distribution of kill command events to identify patterns and peak kill times.

**Action**: Execute the Kusto query below, run the "[appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md)" if variables in the kusto query are not available:

```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithPreciseTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where message contains "Kill"
| summarize KillEventCount=count() by bin(PreciseTimeStamp, 1h)
| order by PreciseTimeStamp asc
```

#### Output
Follow these instructions exactly:

1. **If query returns no results (rowcount = 0)**:
   - Display: "Kill command was not detected."
   - **STOP HERE** - Do not proceed further

2. **If query returns results (rowcount > 0)**:
   - Display the hourly distribution as a table
   - Calculate and display the **Total Count** (sum of all hourly KillEventCount)
   - Highlight hours with unusually high kill event counts (consider top peaks) with **bold** and 🚩 emoji
   - Look for patterns (e.g., recurring spikes suggesting scheduled maintenance, failovers, or batch job cancellations)

| Hour (UTC) | KILL \<spid\> Count |
|------------|----------------------|
| `PreciseTimeStamp` | `KillEventCount` |

**Total Count**: Sum of all hourly counts

#### Sample Output

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results.

## 📈 Hourly Kill Command Distribution

| Hour (UTC) | KILL \<spid\> Count |
|------------|-------------|
| Mar 07 16:00 | 1 |
| Mar 07 17:00 | **2** 🚩 |

**Total Count**: 3

### 🔎 Pattern Analysis

| Peak Hour | KILL \<spid\> Count | Possible Cause |
|-----------|-------------|----------------|
| **Mar 07 17:00 UTC** | 2 | Failover event or manual query termination |

**Pattern Interpretation**:
- Recurring daily patterns → "Scheduled maintenance or batch job cancellations"
- Spikes during business hours → "Manual query cancellation by operations"

#### Output Guidelines

1. **Table Format**: Display hour and kill event count.
2. **Highlighting**: Mark peak hours (top 3-5 by kill events) with **bold** and 🚩 emoji.s
3. **Total Count**: Sum all kill events and display the total.
4. **Pattern Analysis**: Create a separate table listing the top 3-5 peak hours with possible causes:
   - Recurring patterns → "Scheduled maintenance or batch job cancellations"
   - Spikes at specific times → "Scheduled maintenance windows"
   - Spikes during business hours → "Manual query cancellation or timeout"
5. **CPU Impact Note**: Remind user that killed queries' CPU is not recorded in QDS, contributing to CPU discrepancy.

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Kill Commands are Detected

#### Kill Command Analysis Results

**Yes, kill commands were executed during the investigation period.**

#### 📈 Hourly KILL \<spid\> Command Distribution

| Hour (UTC) | KILL \<spid\> Count |
|------------|----------------------|
| Mar 07 16:00 | 1 |
| Mar 07 17:00 | **2** 🚩 |

**Total Count**: 3

#### 🔎 Pattern Analysis

| Peak Hour | KILL \<spid\> Count | Possible Cause |
|-----------|-------------|----------------|
| **Mar 07 17:00 UTC** | 2 | Failover event or manual query termination |

---

### When No Kill Commands are Detected

#### Kill Command Analysis Results

**No, kill commands were NOT detected during the investigation period.**

Kill command was not detected.
