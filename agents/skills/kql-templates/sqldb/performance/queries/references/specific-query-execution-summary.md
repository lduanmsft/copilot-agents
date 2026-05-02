---
name: specific-query-execution-summary
description: Analyzes query execution summary including success/failure rates from QDS execution stats
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Specific Query execution summary

## Skill Overview

This skill retrieves query execution summary statistics from MonWiQdsExecStats table to analyze how many times a query has been executed and what percentage of executions failed. It provides insight into query reliability and error rates.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | The query hash to analyze (provide this OR query_id) | string | `0x73E64DD291EBBF6E` |
| `{query_id}` | The query ID to analyze (provide this OR query_hash) | long | `12345` |



## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
let ExecSummary=(totalExecCount:long, errorCount:long, failedRatio:real)
{
case(totalExecCount==0,"The query execution count was 0",
errorCount==0,strcat("The query has been executed ",tostring(totalExecCount)," time(s) without any error."),
strcat("Please note, ",failedRatio,"% of query execution failed, here is the detail: ",errorCount," of ",totalExecCount," executions failed.")
)
//Sample output1:The query execution count was 0
//Sample output2:Please note, 0.1% of query execution failed, here is the detail: 94 of 65533 executions failed.
//Sample output3:The query has been executed 1000 times without any error.
};
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where (isnotempty('{query_hash}') and query_hash =~ '{query_hash}') or (isnotempty('{query_id}') and query_id == {query_id})
| summarize totalExecCount = sum(execution_count), errorCount = sumif(execution_count, exec_type != 0)
| extend failedRatio=iff(totalExecCount > 0, round(errorCount*100.0/totalExecCount,1), 0.0)
| extend execSummary=ExecSummary( totalExecCount, errorCount, failedRatio)
| extend IssueDetected=errorCount >0
| project execSummary,IssueDetected
```

#### Output
Follow these instructions exactly. Only display output when specified:

1. Display the exact message from `ResultMessage` without any modification

