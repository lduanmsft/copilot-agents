---
name: specific-query-execution-time-vs-wait-time-analysis
description: Analyzes the ratio of elapsed time to CPU time and identifies top wait types to determine if queries are waiting on resources or being blocked
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Specific Query Wait Type Analysis

## Skill Overview

This skill compares the ratio of elapsed time to execution time and checks top wait types if needed. A higher ratio indicates that the query is waiting on resources or being blocked rather than actively running.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | Query hash identifier | string | `0x123ABC` |
| `{query_id}` | Query ID | string | `12345` |



## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
``kusto
let WaitSummary=(sum_ExecutionTime_ms:long,sum_CpuTime_ms:long,total_wait_time_ms:long,ratio:real)
{
let waitSummary=strcat("The query experienced",
case(ratio>=0.3," significant",ratio>=0.2," moderate"," minimal"),
" waits, with a wait time to CPU time ratio of ",ratio,", indicating that it spent ",round(ratio*100,1),"% of its execution time either waiting for resources or being blocked.");
let actionPlan=strcat(case(ratio>=0.3," That significantly impact the performance,",ratio>=0.2," If this is a concern,",""),   " please review and apply the suggested action plans outlined in the sub-items below to address this wait issue.");
let parallelMessage=case(sum_CpuTime_ms>sum_ExecutionTime_ms and total_wait_time_ms>sum_CpuTime_ms," (You may notice that execution time is less than the CPU time, this is because this query used parallel execution plan)","");
strcat(waitSummary,iff(0.1>=ratio,"",actionPlan),parallelMessage);
};
let total_wait_time_ms=toscalar(MonWiQdsWaitStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where (isnotempty('{query_hash}') and query_hash =~ '{query_hash}') or (isnotempty('{query_id}') and query_id == '{query_id}')
| summarize sum(total_query_wait_time_ms)
);
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where (isnotempty('{query_hash}') and query_hash =~ '{query_hash}') or (isnotempty('{query_id}') and query_id == '{query_id}')
| summarize sum_CpuTime_ms=sum(cpu_time)/1000,sum_ExecutionTime_ms=sum(elapsed_time)/1000,count=count()
| where count>0
| extend ratio=round(total_wait_time_ms*1.0/sum_CpuTime_ms,2)
| extend waitSummary=WaitSummary(sum_ExecutionTime_ms,sum_CpuTime_ms,total_wait_time_ms,ratio)
| extend IssueDetected=ratio>0.1
| project IssueDetected,waitSummary
``

#### Output
Follow these instructions exactly. Only display output when specified:

1. Display the exact message from `ResultMessage` without any modification

2. **If `IssueDetected` is `true`**: 
   - Display the following message exactly as written:
   - "The query experienced significant or moderate waits. Please review the wait type analysis in the sub-skill below."

### Task 2: Execute Sub-Skills

If `IssueDetected` is `true`, execute the following sub-skill:

Execute the skill [Specific Query Wait Type Analysis](specific-query-wait-type-analysis.md)
