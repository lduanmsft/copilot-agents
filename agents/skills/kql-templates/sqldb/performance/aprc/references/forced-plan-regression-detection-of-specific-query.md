---
name: forced-plan-regression-detection-of-specific-query
description: Detect and analyze plan regression on forced query plans for specific queries
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Forced Plan Regression Detection of Specific Query

## Skill Overview

This skill detects plan regression on forced query plans and analyzes whether the restored plan performed optimally. SQL Server may detect a plan regression and revert the query to the last known good plan, but if the restored plan does not perform optimally, it leads to performance degradation.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | Query hash for investigation | string | `0x1234567890ABCDEF` |
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
| where event == "automatic_tuning_plan_regression_verification_check_completed"//automatic_tuning_plan_regression_verification_check_completed  is fired  15 mins later after last good known query plan is forced and 'forced query plan' is executed at least 3 times
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
1. If zero row is returned, display the exact following message without any modification:"The query {query_hash} didn't have forced plan regression record in MonAutomaticTuning"
2. Display the query results as a table.
3. **IMPORTANT**: Always include this statement in your analysis when forced plan regression is detected: "Please note, this is a workload-related performance issue rather than a defect in SQL Server itself."

---

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Forced Plan Regression is Detected

#### Forced Plan Regression Detection Results

**Yes, forced plan regression was detected for query 105982 during the investigation period.**

#### Forced Plan Regression Summary

| Metric | Value |
|--------|-------|
| **Total Count** | 4 |
| **Count Per Minute** | 0.014 |
| **First Detection** | 2026-03-20 15:15:22 UTC |
| **Last Detection** | 2026-03-20 20:02:45 UTC |

#### Analysis

🚩 Query **105982** experienced **4** forced plan regression events during the investigation period (0.014 per minute). The `automatic_tuning_plan_regression_verification_check_completed` event is fired 15 minutes after the last known good query plan is forced and the forced query plan has been executed at least 3 times. This indicates that the restored plan did not perform optimally, leading to performance degradation.

Please note, this is a workload-related performance issue rather than a defect in SQL Server itself. Kindly engage the DBA team to investigate the underlying cause and ensure long-term query plan stability

#### Root Cause Indicators

This pattern suggests:
- **Forced plan inefficiency** - The last known good plan that was forced is no longer optimal for current data distribution
- **Data changes** - Underlying data has changed significantly since the "good" plan was established
- **Workload evolution** - Query patterns or parameter values have shifted, making the forced plan suboptimal

---

### When No Forced Plan Regression is Detected

#### Forced Plan Regression Detection Results

**No, forced plan regression was NOT detected for query 0x73E64DD291EBBF6E during the investigation period.**

#### Analysis

The query 0x73E64DD291EBBF6E didn't have forced plan regression record in MonAutomaticTuning. This indicates that no forced plan regression events (`automatic_tuning_plan_regression_verification_check_completed`) were recorded for this query during the specified time range.

This rules out forced plan regression as a contributing factor to any performance issues during this period.

---

### Output Format Requirements

1. **Always start with a direct answer** - State clearly whether forced plan regression was detected
2. **Include a summary table** - Present all metrics (totalCount, countPerMinute, minTime, maxTime) with their values
3. **Provide analysis** - Explain what the numbers mean in context
4. **Include the workload statement** - Always add "Please note, this is a workload-related performance issue rather than a defect in SQL Server itself.Kindly engage the DBA team to investigate the underlying cause and ensure long-term query plan stability " when regression is detected
5. **Use 🚩 emoji** - Flag forced plan regression issues for visibility