---
name: failed-query-execution-summary
description: Analyzes failed, timeout, aborted, and internal execution failure query summaries from QDS execution stats.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Failed Query Execution Summary

## Skill Overview

This skill investigates failed query executions by analyzing Query Data Store (QDS) execution statistics. It identifies queries that failed due to timeouts, aborts, or internal execution failures, and calculates the failure rate to help diagnose query execution issues.

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

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let FailureStatus = (failedPercentage: real,failedCount:long,totalExecCount:long)
{
case(
failedCount==0, strcat(totalExecCount," queries were executed and no failed query execution detected."),
strcat(failedCount, " of ",totalExecCount," queries failed, representing a failure rate of ",failedPercentage,"%.")
)
};
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize totalExecCount = sum(execution_count), failedCount = sumif(execution_count, exec_type !=0)
| extend failedPercentage=case(totalExecCount == 0, 0, round(100.0*failedCount/totalExecCount,3))
| extend IssueDetected=failedCount>=1
| extend failureStatus=FailureStatus(failedPercentage,failedCount,totalExecCount)
| project IssueDetected,failureStatus
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the exact message from the "failureStatus" column without any modifications.
2. Save the value IssueDetected in variable {IssueDetected}

Here is the kusto query used in this skill, please run it to verify:

```kql
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize totalExecCount = sum(execution_count), abortCount = sumif(execution_count, exec_type == 3), errorCount = sumif(execution_count, exec_type == 4)
```


### Task 2: Execute Sub-Skills 
1. If {IssueDetected} is false, then terminate this skill.
2. If {IssueDetected} is true, display the following mesage without any modification: "Because the query execution failure issue was detected, we are going to perform additional checks:"
    2.1 Execute Skill (Top Wait Types of Query Execution)[top-wait-types-of-query-execution.md]
    2.2 Execute Skill (Top Failed Queries)[top-failed-queries.md]
