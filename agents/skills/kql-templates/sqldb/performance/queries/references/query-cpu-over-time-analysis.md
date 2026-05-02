---
name: query-cpu-over-time-analysis
description: This skill checks the T-SQL execution CPU usage over time, at 15-minute intervals
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Query CPU over time Analysis

## Skill Overview

This skill analyzes CPU usage of T-SQL execution over time to identify if SQL query execution caused high CPU consumption. It aggregates CPU metrics at 15-minute intervals and identifies periods where CPU usage exceeded 70% threshold.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{HighCPUThreshold}` | The threshold hold of High CPU | float | 70 |

If `{HighCPUThreshold}` is not provided by user, use 70



## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let QDSAggIntervalInMin = time(15m);
let cap_interval = materialize(MonDmRealTimeResourceStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize min(cpu_cap_in_sec) by bin(originalEventTimestamp, QDSAggIntervalInMin));
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize cores_per_sec = sum(cpu_time) / (QDSAggIntervalInMin / time(1microsecond)) by bin(originalEventTimestamp, QDSAggIntervalInMin)
| lookup kind = inner ( cap_interval ) on originalEventTimestamp
| extend cpu_percent = round(100.0 * cores_per_sec / min_cpu_cap_in_sec, 1)
| where cpu_percent>{HighcpuWarningThreshold}
| project originalEventTimestamp,cpu_percent
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If zero row is returned, please display the exact the following message from the  without any modifications:"We don't find cpu usage exceeded than {HighCPUThreshold}%"
2. If one or more rows are returned, please display the raw table.
    2.1 After showing the raw result, display the exact message:"Here are the table data that cpu usage exceed {HighCPUThreshold}%"

### Task 2: Execute Sub-Skills

Based on the analysis results from Task 1: 
If one or more rows are returned, Execute Skill (Top 5 CPU Usage T-SQL Execution Over Time)[top-cpu-queries-over-time.md]
