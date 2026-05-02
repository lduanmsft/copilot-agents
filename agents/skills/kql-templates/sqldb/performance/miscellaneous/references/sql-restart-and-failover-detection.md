---
name: sql-restart-and-failover-detection
description: Analyze SQL restart and failover events for the specified logical server and database
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug SQL Restart and Failover Detection

## Skill Overview

This skill analyzes SQL restart and failover events by querying MonSQLSystemHealth and SqlFailovers tables to detect if any restarts or failovers occurred during the specified time range.

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
| Task 1 | Execute Kusto query to detect restart/failover events | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithPreciseTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

**Executed Query:**
```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithPreciseTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| summarize StartTime=min(PreciseTimeStamp), EndTime=max(PreciseTimeStamp) by process_id, NodeName
| order by StartTime asc
```


#### Output
Follow these instructions exactly:

1. **If the query returns 0 or 1 row**: Display "No Restart/Failover detected." and stop.

2. **If the query returns 2+ rows** (indicating restarts/failovers occurred):
   - Calculate `failover_count = row_count - 1`
   - Display the summary message: "Azure DB restart/failover {failover_count} time(s)."
   - Generate the **Failover Timeline** table from the query results
   - Generate the **Failover Events** table by comparing consecutive rows
   - Provide brief **Analysis** of when failovers occurred

#### Output Generation Rules

**Failover Timeline Table:**
- Column `#`: Row number (1, 2, 3, ...)
- Column `Process ID`: Value from `process_id`
- Column `Node`: Value from `NodeName`
- Column `Start Time (UTC)`: Value from `StartTime`, formatted as `yyyy-MM-dd HH:mm:ss`
- Column `End Time (UTC)`: Value from `EndTime`, formatted as `yyyy-MM-dd HH:mm:ss`
- Column `Duration`: Calculate `EndTime - StartTime`, display as `~Xh Ym` or `~Xm`

**Failover Events Table:**
- For each pair of consecutive rows (row N and row N+1), create a failover event
- Column `Event`: "🚩 Failover {N}"
- Column `Time (UTC)`: Approximate time when failover occurred (EndTime of row N)
- Column `From`: "{NodeName} (PID {process_id})" from row N
- Column `To`: "{NodeName} (PID {process_id})" from row N+1
- Column `Gap`: Time difference between EndTime of row N and StartTime of row N+1

**Analysis Section:**
- Provide 1-2 sentences per failover event describing when it occurred
- Note any correlation with other issues if context is available (e.g., CPU saturation, worker exhaustion)

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Restart/Failover is Detected

#### SQL Restart and Failover Analysis Results

**Yes, restart/failover events were detected during the investigation period.**

#### Summary

Azure DB restart/failover 2 time(s).

#### Failover Timeline

| # | Process ID | Node | Start Time (UTC) | End Time (UTC) | Duration |
|---|------------|------|------------------|----------------|----------|
| 1 | 105636 | _DB_6 | 2026-03-07 00:00:16 | 2026-03-07 02:39:18 | ~2h 39m |
| 2 | 53588 | _DB_15 | 2026-03-07 02:40:16 | 2026-03-07 16:51:35 | ~14h 11m |
| 3 | 19648 | _DB_51 | 2026-03-07 16:52:02 | 2026-03-07 17:21:02 | ~29m |

#### Failover Events

| Event | Time (UTC) | From | To | Gap |
|-------|------------|------|-----|-----|
| 🚩 Failover 1 | ~02:39 | _DB_6 (PID 105636) | _DB_15 (PID 53588) | ~58 seconds |
| 🚩 Failover 2 | ~16:51 | _DB_15 (PID 53588) | _DB_51 (PID 19648) | ~27 seconds |

#### Analysis

- **Failover 1** occurred at approximately **02:39 UTC** - this was during the early morning when worker thread exhaustion events were starting to appear
- **Failover 2** occurred at approximately **16:51 UTC** - this was during the peak of the worker thread exhaustion and CPU saturation period (when CPU and workers were at 100%)

The second failover at 16:51 UTC may have been triggered due to the severe resource pressure from the high CPU and worker thread exhaustion that was ongoing from 10:00-17:00 UTC.

---

### When No Restart/Failover is Detected

#### SQL Restart and Failover Analysis Results

**No, restart/failover events were NOT detected during the investigation period.**

#### Summary

No Restart/Failover detected.
