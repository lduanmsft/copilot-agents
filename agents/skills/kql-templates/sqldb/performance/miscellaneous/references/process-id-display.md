---
name: process-id-display
description: Displays all process IDs (PIDs) of an Azure SQL database during a specified time range, showing when each process was active. Triggered by keywords: process ID, pid.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---


# Process ID Display

## Skill Overview

This skill retrieves and displays all SQL Server process IDs (also known as PIDs) that were active for an Azure SQL database during a specified time range. It shows the start and end times for each process on each node, helping identify process lifecycle and activity patterns.

**Trigger Keywords**: `process ID`, `pid`, `process lifecycle`

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
| Task 1 | Execute Kusto query to display process IDs | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| summarize startTime=min(PreciseTimeStamp), endTime=max(PreciseTimeStamp) by NodeName, process_id,AppName
| project-reorder startTime, endTime, NodeName, process_id,AppName
| order by startTime asc
```

### Output Format

Display the results in a table format:

| Start Time | End Time | Node Name | Process ID |
|------------|----------|-----------|------------|
| `startTime` | `endTime` | `NodeName` | `process_id` |

**Interpretation**:
- **Start Time**: The earliest timestamp when this process ID was observed
- **End Time**: The latest timestamp when this process ID was observed
- **Node Name**: The database node where the process was running
- **Process ID**: The SQL Server process identifier (PID)

If multiple nodes are present, the results show process activity across all nodes, ordered chronologically by start time.

**No Results**: If no process IDs are found for the specified time range, report:
> "No process IDs were found for database `{LogicalDatabaseName}` on server `{LogicalServerName}` during the specified time range."

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Single Process ID is Found

#### Process IDs for {LogicalDatabaseName}

| Start Time | End Time | Node Name | Process ID |
|------------|----------|-----------|------------|
| 2026-03-07T09:01:22.946Z | 2026-03-07T16:51:36.932Z | _DB_15 | 53588 |

**Summary**: One process ID (**53588**) was active on node `_DB_15` throughout the specified time range (09:01 - 16:51 UTC).

---

### When Multiple Process IDs are Found (Node Change)

#### Process IDs for {LogicalDatabaseName}

| Start Time | End Time | Node Name | Process ID |
|------------|----------|-----------|------------|
| 2026-03-07T09:01:22.946Z | 2026-03-07T16:51:36.932Z | _DB_15 | 53588 |
| 2026-03-07T16:52:02.139Z | 2026-03-07T17:21:02.476Z | _DB_51 | 19648 |

**Summary**: 
- **Process 53588** on node `_DB_15`: Active from 09:01 to 16:51 UTC (~7h 50m)
- **Process 19648** on node `_DB_51`: Active from 16:52 to 17:21 UTC (~29m)

Note: A node change occurred around 16:52 UTC (from _DB_15 to _DB_51), which explains the new process ID.

---

### When No Process IDs are Found

#### Process IDs for {LogicalDatabaseName}

No process IDs were found for database `{LogicalDatabaseName}` on server `{LogicalServerName}` during the specified time range.
