---
name: readonly-262144
description: did qds 262144 happen;did qds run into 262144; did qds run into readonly due to 262144;Analyze QDS Readonly with ReadonlyReason 262144 (query_store_buffered_items_over_memory_limit)
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug QDS Readonly 262144 Analysis Skill

## Skill Overview

This skill analyzes Azure SQL Database Query Store (QDS) read-only mode occurrences caused by ReadonlyReason 262144. This condition occurs when the memory usage of BufferedItemsMemory reaches the database level memory threshold (set at 1% of total database memory). The skill detects and reports these occurrences and provides mitigation recommendations.

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
strcat("Note: we've detected abnormal memory usage that actual Buffereditem memory was less than the limit, it could be due to 'FastPath Optimization', please engage QDS Expert to investigate."));
let mitigationMessage=strcat("The mitigation includes the following actions:1. Implementing query parameterization;2. Upgrading the Service Level Objective (SLO) to increase memory capacity;3. Decreasing flush_interval_seconds;");
let dbLevelLimitMessage=strcat("The ",iff(totalCount==1," occurrence was ", " occurrences were")," due to the memory usage of BufferedItemsMemory reached the database level memory threshold-—set at 1% of the total database memory. ");
let occurrenceMessage=strcat("The Azure Sql Database Query Store (QDS) ran into read-only mode due to the ReadonlyReason-262144 ",totalCount,iff(totalCount==1," time", " times."));
strcat(occurrenceMessage,dbLevelLimitMessage,iff(incorrectCount==0, mitigationMessage,FastPathOptimizationMessage))
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event=='query_store_buffered_items_over_memory_limit' or
( event=='query_store_resource_total_over_instance_limit' and query_store_resource_type=='x_QdsResourceType_BufferedItemsMemory')
|summarize totalCount=count(),incorrectCount=countif(max_buffered_items_size_kb>current_buffered_items_size_kb or max_instance_total_resource_size_kb>current_instance_total_resource_size_kb)
| where totalCount>0
| extend readonlyMessage=ReadonlyMessage(totalCount,incorrectCount)
| project readonlyMessage
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If the Task3 returns results, display the exact message from the `readonlyMessage` column without any modifications.
2. If the Task3 doesn't return any result, display the following message exactly as written: "QDS Readonly with ReadonlyReason 262144 is not detected"

