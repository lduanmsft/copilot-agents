---
name: top-cpu-queries
description: Get top N high CPU queries ranked by total CPU consumption. Use for "top N CPU queries", "highest CPU queries", "top CPU consuming queries".
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
keywords: ['top cpu queries', 'high cpu queries', 'top N cpu', 'highest cpu', 'cpu consuming queries', 'cpu summary']
---

# Debug Top CPU Queries (Summary)

## Skill Overview

**Use this skill when the user asks for "top N high CPU queries" or wants a summary view.**

This skill identifies the top CPU-consuming query hashes and analyzes their impact on the SQL Database. It retrieves {TopN} query hashes based on CPU consumption, calculates their percentage of User Pool CPU capacity and utilized CPU, and visualizes the CPU usage trend over time for the top query hash. When QDS CPU is high, it automatically retrieves detailed information about the top CPU-consuming query hash.

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
| summarize TotalQueryCPU_ms = sum(cpu_time) / 1000.0,dcount(query_plan_hash) by query_hash
| project TotalQueryCPU_Percent_UserPoolCPUCapacity=round(100*TotalQueryCPU_ms/{SumCpuMillisecondOfAllApp},1),
TotalQueryCPU_Percent_UsedUserPoolCPU=round(100*TotalQueryCPU_ms/{ActualSumCpuMillisecondOfAllApp},1),,dcount_query_plan_hash,query_hash
| order by TotalQueryCPU_ms desc
| take {TopN}
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw result.

