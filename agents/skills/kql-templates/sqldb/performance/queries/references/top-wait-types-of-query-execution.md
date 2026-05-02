---
name: top-wait-types-of-query-execution
description: Analyze overall wait types of query execution to identify performance bottlenecks
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Top Wait Types of Query Execution

## Skill Overview

This skill analyzes the MonWiQdsWaitStats table to identify the top wait types affecting query execution performance. It calculates the percentage contribution of each wait category to help identify performance bottlenecks.

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
| Task 2 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let totalWaitTime_ms=toscalar(MonWiQdsWaitStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize sum(total_query_wait_time_ms));
MonWiQdsWaitStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize sumWaitTime_ms=sum(total_query_wait_time_ms) by wait_category
| project wait_category,sumWaitTime_ms, percentage=round(sumWaitTime_ms*100.0/totalWaitTime_ms,1)
| order by sumWaitTime_ms
| take {TopN}
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display below the result using below format
|wait_category|sumWaitTime_ms|percentage|
|-------------|-------------|-----------|
|             |             |           |
|             |             |           |
|             |             |           |
|             |             |           |

Sample output
|wait_category|sumWaitTime_ms|percentage|
|-------------|-------------|-----------|
|LOCK         | 1000000     | 31.5%     |
|LATCH        | 500000      | 15.7%     |
|BUFFERLATCH  | 250000      | 7.8%      |
|TRANSACTION  | 25000       | 0.7%      |
|NETWORKIO    | 2000        | 0%        |
Here is the kusto query used in this skill, please run it to verify.
```kql
MonWiQdsWaitStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
//| where exec_type != 0  //uncomment this line to filter out successful queries
| summarize sumWaitTime_ms=sum(total_query_wait_time_ms) by wait_category
| order by sumWaitTime_ms
| take 5
```


### Task 2: Execute Sub-Skills 
If issue is detected, display the following sentence exactly as written:"Because the LOCK issue was detected, please review ASC to check the blocking status"
