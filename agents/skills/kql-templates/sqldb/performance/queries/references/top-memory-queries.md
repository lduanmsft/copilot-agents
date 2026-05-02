---
name: top-memory-queries
description: This skill displays top 5 queries ranked by memory grants to identify queries consuming the most memory resources
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Top Memory Queries

## Skill Overview

This skill analyzes query performance by identifying the top queries with the highest memory grants. Memory grants indicate the amount of memory allocated for query execution (sorts, hash joins, etc.), which is a key metric for identifying memory-intensive queries that may be impacting database performance.

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

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 1a | Execute Elastic Pool query | `{isInElasticPool}` is true |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
        
```kql
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize maxMemoryGrantOfSingleExecution_mb=max(max_max_query_memory_pages)*8/1024,TotalMemoryGrant_mb= sum(max_query_memory_pages)*8/1024,executionCount=sum(execution_count) by query_hash
| order by maxMemoryGrantOfSingleExecution_mb desc nulls first
| take {TopN}
```

#### Task 1a: If `{isInElasticPool}` is true, also execute the following Kusto query to analyze memory grants across all databases in the elastic pool.

```kql
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' 
| summarize maxMemoryGrantOfSingleExecution_mb=max(max_max_query_memory_pages)*8/1024,TotalMemoryGrant_mb= sum(max_query_memory_pages)*8/1024,executionCount=sum(execution_count) by query_hash,database_name
| order by maxMemoryGrantOfSingleExecution_mb desc nulls first
| take {TopN}
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw result.
2. After showing the raw result, display the exact message:"Please type 'The detail of query [query_hash]' if you'd like to dig into."
