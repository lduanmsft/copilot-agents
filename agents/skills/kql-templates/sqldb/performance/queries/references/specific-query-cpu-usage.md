---
name: specific-query-cpu-usage
description: This skill will check the CPU usage of the specified query and display the total CPU time and the percentage of its usage in the User Pool CPU.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug CPU Usage of Specific Query

## Skill Overview

This skill will check the CPU usage of the specified query and display the total CPU time and the percentage of its usage in the User Pool CPU.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | The hash of the query | binary string | `0x73E64DD291EBBF6E` |
| `{query_id}` | The query ID to analyze | bigint | `12345` |



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
| where (isnotempty('{query_hash}') and query_hash =~ '{query_hash}') or (isnotempty({query_id}) and query_id == {query_id})
| summarize totalCPU_ms = sum(cpu_time)/1000,max_cpuTime_ms=max(max_cpu_time)/1000,total_ExecutionCount=sum(execution_count) by query_hash, query_id
| project query_hash,query_id,total_ExecutionCount,totalCPU_ms,max_cpuTime_ms,cpu_percent=round(100*totalCPU_ms/{SumCpuMillisecondOfAllApp},3)
| extend executionStatus=strcat("The query was executed ",total_ExecutionCount," times, accounting for ",cpu_percent,"% of total User Pool CPU Capacity, with a maximum CPU time of ",max_cpuTime_ms,"ms for a single execution.")
| project executionStatus
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If zero row is returned, display the exact message "We don't have data for this query, as it appears it hasn't been executed within the specified time period."
2. If one or more rows are returned, display the exact message {{executionStatus}}.
