---
name: top-successful-compilation-ranked-by-cpu-usage
description: This skill will display the topN queries that consumed the most CPU time during compilation
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Top Queries by compilation CPU

## Skill Overview

This skill analyzes and identifies the top N queries that consumed the most CPU time during compilation and recompilation. It provides insights into which queries are causing the highest compilation CPU usage, including metrics such as maximum compilation CPU time, maximum compilation duration, and occurrence count.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{TopN}` | Number of top items to retrieve| integer | 5 |

If `{TopN}` is not provided, please use 5 by default.


## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
MonWiQueryParamData
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend compile_duration_sec=round(compile_duration/1000.0/1000,1)
| extend compile_cpu_time_sec=round(compile_cpu_time/1000.0/1000,1)
| extend compile_memory_mb=round(compile_memory/1024,1)
| summarize count=count(),max_compile_duration_sec=max(compile_duration_sec),max_compile_cpu_time_sec=max(compile_cpu_time_sec) by query_hash
| project-reorder max_compile_cpu_time_sec,max_compile_duration_sec,count
| order by max_compile_cpu_time_sec desc
| take {TopN}
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw result
2. If zero row is returned, display the exact following message without any modification:
"No data returned, as it appears NO successful compilation happened in the investigation window."
