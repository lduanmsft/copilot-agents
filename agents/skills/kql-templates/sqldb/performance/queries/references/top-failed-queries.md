---
name: top-failed-queries
description: Analyze top queries with the highest number of failures from MonWiQdsWaitStats
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Top Failed Queries

## Skill Overview

This skill identifies the top queries with the highest number of failures from MonWiQdsWaitStats table, showing the wait categories with the highest total wait time for each query. It helps diagnose query performance issues by correlating failure counts with wait statistics.

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
MonWiQdsWaitStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where exec_type !=0
| top-nested {TopN} of query_hash by failedCount=count(),
top-nested 2 of  wait_category by total_query_wait_time_ms=sum(total_query_wait_time_ms) desc
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If zero row is returned, display the exact message "No query failure detected in MonWiQdsWaitStats."
2. If one or more rows are returned, display the raw result exactly as returned.
   After showing the raw result, display the exact message:"Please type 'The detail of query [query_hash]' if you'd like to dig into."

