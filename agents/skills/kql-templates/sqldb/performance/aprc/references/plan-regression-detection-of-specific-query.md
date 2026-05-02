---
name: plan-regression-detection-of-specific-query
description: Detect SQL Server APRC plan regression events for queries
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Plan Regression Detection of Specific query

## Skill Overview

This skill detects plan regression events identified by SQL Server Automatic Plan Regression Correction (APRC). It analyzes the MonAutomaticTuning telemetry to identify when new query plans have regressed compared to previously good plans, and provides frequency analysis to help determine the severity and nature of the regression.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | Query hash to investigate (optional) | binary string | `0x73E64DD291EBBF6E` |
| `{query_id}` | The query ID to analyze | bigint | `12345` |



## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Caller validation. | Always |
| Task 2 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Caller validation.

This skill is intended to be invoked exclusively by [APRC](../SKILL.md). If invoked by any other caller, terminate execution in this marddown file, display the exact message "Calling parent skill instead" and execute [APRC](../SKILL.md) instead.

### Task 2: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let queryIds=(
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where (isnotempty('{query_hash}') and query_hash == '{query_hash}') or (isnotempty({query_id}) and query_id == {query_id})
| distinct query_id
);
MonAutomaticTuning
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| join kind=inner (queryIds) on query_id
| where event =~'automatic_tuning_plan_regression_detection_check_completed'//automatic_tuning_plan_regression_detection_check_completed is fired when new applied query plan has been executed at least 15 times
| where is_regression_detected ==true
| project originalEventTimestamp,event,query_id,is_regression_detected,is_regression_corrected,current_plan_id, last_good_plan_id,current_plan_cpu_time_average,current_plan_execution_count,last_good_plan_cpu_time_average,last_good_plan_execution_count
| summarize 
    totalCount=count(),
    countPerMinute=round(count()*1.0/(datetime_diff('minute',max(originalEventTimestamp),min(originalEventTimestamp))+1),3),
    minTime=min(originalEventTimestamp),
    maxTime=max(originalEventTimestamp)
| where totalCount >0
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If zero row is returned, display the exact following message without any modification:"The query {query_hash} didn't have record in MonAutomaticTuning"
2. Display the query results as a table.
3. **IMPORTANT**: Always include this statement in your analysis when plan regression is detected: "Please note, this is a workload-related performance issue rather than a defect in SQL Server itself. Kindly engage the DBA team to investigate the underlying cause and ensure long-term query plan stability."

---

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Plan Regression is Detected

#### Plan Regression Detection Results

**Yes, plan regression was detected for query 105982 during the investigation period.**

#### Plan Regression Summary

| Metric | Value |
|--------|-------|
| **Total Count** | 6 |
| **Count Per Minute** | 0.019 |
| **First Detection** | 2026-03-20 15:11:01 UTC |
| **Last Detection** | 2026-03-20 20:22:02 UTC |

#### Analysis

🚩 Query **105982** experienced **6** plan regression events during the investigation period (0.019 per minute). The `automatic_tuning_plan_regression_detection_check_completed` event is fired when a new applied query plan has been executed at least 15 times and SQL Server detects that the new plan is regressing compared to the previous plan.

Please note, this is a workload-related performance issue rather than a defect in SQL Server itself. Kindly engage the DBA team to investigate the underlying cause and ensure long-term query plan stability.

#### Root Cause Indicators

This pattern suggests:
- **Query plan instability** - The query optimizer selected a plan that performed worse than previous plans
- **Statistics changes** - Underlying data distribution may have changed causing suboptimal plan selection
- **Parameter sensitivity** - The query may be sensitive to parameter values (parameter sniffing)

---

### When No Plan Regression is Detected

#### Plan Regression Detection Results

**No, plan regression was NOT detected for query 0x73E64DD291EBBF6E during the investigation period.**

#### Analysis

The query 0x73E64DD291EBBF6E didn't have record in MonAutomaticTuning. This indicates that no plan regression events (`automatic_tuning_plan_regression_detection_check_completed`) were recorded for this query during the specified time range.

This rules out APRC plan regression as a contributing factor to any performance issues during this period.

---

### Output Format Requirements

1. **Always start with a direct answer** - State clearly whether plan regression was detected
2. **Include a summary table** - Present all metrics (totalCount, countPerMinute, minTime, maxTime) with their values
3. **Provide analysis** - Explain what the numbers mean in context
4. **Include the workload statement** - Always add "Please note, this is a workload-related performance issue rather than a defect in SQL Server itself. Kindly engage the DBA team to investigate the underlying cause and ensure long-term query plan stability " when regression is detected
5. **Use 🚩 emoji** - Flag plan regression issues for visibility
