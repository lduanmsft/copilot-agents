---
name: top-failed-compilation-ranked-by-cpu-usage
description: This skill will display the topN failed compilations that used the most CPU resources.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Top Failed compilation ranked by CPU Usage

## Skill Overview

This skill analyzes and identifies the top N failed query compilations that consumed the most CPU resources. It provides insights into compilation failures, including CPU usage and compilation duration metrics for each failed compilation attempt, helping identify problematic queries that fail during compilation.

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
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed, 16)))
| where event =~'failed_compilation'
| summarize compile_cpu_ms=sum(compile_cpu),compile_duration_ms=sum(compile_duration) by query_hash
| order by compile_cpu_ms desc
| take {TopN}
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw result
2. If zero row is returned, display the exact following message without any modification:
"We don't have data for this query, as it appears no failed compilation happened. This is a positive indicator - no queries failed during compilation in the investigation window"