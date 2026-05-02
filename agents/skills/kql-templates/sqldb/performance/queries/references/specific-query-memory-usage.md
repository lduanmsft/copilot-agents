---
name: specific-query-memory-usage
description: Analyze memory usage patterns for SQL queries to identify memory grant issues and optimization opportunities
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Memory Usage of Specific Query

## Skill Overview

This skill analyzes the memory usage patterns of specific SQL queries by examining memory grants and execution statistics. It helps identify queries that consume excessive memory, which can lead to performance degradation and resource contention. The analysis focuses on maximum memory grants per single execution and total memory grants across all executions.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | Query identifier for analysis | binary string | `0x1234567890ABCDEF` |
| `{query_id}` | The query ID to analyze | bigint | `12345` |



## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where (isnotempty('{query_hash}') and query_hash =~ '{query_hash}') or (isnotempty({query_id}) and query_id == {query_id})
| summarize maxMemoryGrantOfSingleExecution_mb=max(max_max_query_memory_pages)*8/1024,totalMemoryGrant_mb = sum(max_query_memory_pages)*8/1024,executionCount=sum(execution_count) by query_hash, query_id

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw result.