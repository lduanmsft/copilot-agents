---
name: top-writes-queries
description: This skill displays top 5 queries ranked by logical reads to identify queries consuming the most IO resources
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Top Logical Reads Queries

## Skill Overview

This skill analyzes query performance by identifying the top queries with the highest logical Write counts. Logical writes increase log activity, dirty pages, and I/O, causing WRITELOG waits, latency, and performance degradation across CPU, memory, and storage.

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
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize TotalLogical_writes = sum(logical_writes) by query_hash
| order by TotalLogical_writes desc nulls first
| take {TopN}
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw result.
2. After showing the raw result, display the exact message:"Please type 'The detail of query [query_hash]' if you'd like to dig into."
