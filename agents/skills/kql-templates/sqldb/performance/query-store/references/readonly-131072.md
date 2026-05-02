---
name: readonly-131072
description: did qds 131072 happen;did qds run into 131072; did qds run into readonly due to 131072;Detect if QDS run into 13172 issue and deliver recommendation. Analyze Query Store (QDS) Readonly mode due to ReadonlyReason 131072 (query_store_stmt_hash_map_over_memory_limit)
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug QDS Readonly 131072 

## Skill Overview

This skill analyzes Azure SQL Database Query Store (QDS) read-only mode caused by ReadonlyReason 131072. This condition occurs when the memory usage of StmtHashMapMemory reaches the database level memory threshold (5% of total database memory). The skill detects occurrences of `query_store_stmt_hash_map_over_memory_limit` events and provides mitigation recommendations.

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
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let ReadonlyMessage = (totalCount:int,incorrectCount:int)
{
let FastPathOptimizationMessage=iff(incorrectCount==0,"",
strcat("Note: we've detected abnormal memory usage that actual StmtHash memory was less than the limit, it could be due to 'FastPath Optimization', please engage QDS Expert to investigate."));
let mitigationMessage=strcat("The mitigation includes the following actions:1. Implementing query parameterization;2. Upgrading the Service Level Objective (SLO) to increase memory capacity;3. Decreasing capture_policy_stale_threshold_hours;4. Decreasing stale_query_threshold_days.");
let dbLevelLimitMessage=strcat("The ",iff(totalCount==1," occurrence was ", " occurrences were")," due to the memory usage of StmtHashMapMemory reached the database level memory threshold-—set at 5% of the total database memory. ");
let occurrenceMessage=strcat("The Azure Sql Database Query Store (QDS) ran into read-only mode due to the ReadonlyReason-131072 ",totalCount,iff(totalCount==1," time", " times."));
strcat(occurrenceMessage,dbLevelLimitMessage,iff(incorrectCount==0, mitigationMessage,FastPathOptimizationMessage))
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event=='query_store_stmt_hash_map_over_memory_limit' or
( event=='query_store_resource_total_over_instance_limit' and query_store_resource_type=='x_QdsResourceType_StmtHashMapMemory')
|summarize totalCount=count(),
incorrectCount=countif(max_stmt_hash_map_size_kb>current_stmt_hash_map_size_kb or max_instance_total_resource_size_kb>current_instance_total_resource_size_kb)
| where totalCount>0
| extend readonlyMessage=ReadonlyMessage(totalCount,incorrectCount)
| project readonlyMessage
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If the Task3 returns results, display the exact message from the `readonlyMessage` column without any modifications.
2. If the Task3 doesn't return any result, display the following message exactly as written: "QDS Readonly with ReadonlyReason 131072 is not detected"

