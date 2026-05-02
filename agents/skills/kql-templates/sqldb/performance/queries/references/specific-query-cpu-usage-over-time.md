---
name: specific-query-cpu-usage-over-time
description: This skill displays the CPU usage of a specific query over time at 15-minute intervals to identify CPU consumption patterns and spikes.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug CPU Usage Over Time of Specific Query

## Skill Overview

This skill analyzes the CPU usage of a specific query (identified by query_hash) over time at 15-minute intervals. It helps identify when the query consumed the most CPU and whether there were spikes or patterns in resource consumption.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | The hash of the query to analyze | binary string | `0x73E64DD291EBBF6E` |
| `{query_id}` | The query ID to analyze | bigint | `12345` |



## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | Generate Time Series Visualization (Optional) | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let QDSAggIntervalInMin = time(15m);
let cap_interval = materialize(MonDmRealTimeResourceStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize min(cpu_cap_in_sec) by bin(originalEventTimestamp, QDSAggIntervalInMin));
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where (isnotempty('{query_hash}') and query_hash =~ '{query_hash}') or (isnotempty({query_id}) and query_id == {query_id})
| summarize 
    cpu_time_ms = sum(cpu_time)/1000,
    execution_count = sum(execution_count),
    avg_cpu_per_exec_ms = round(sum(cpu_time)/1000.0/sum(execution_count), 2),
    query_plan_hashes = make_set(query_plan_hash)
  by bin(originalEventTimestamp, QDSAggIntervalInMin)
| lookup kind = inner (cap_interval) on originalEventTimestamp
| extend cpu_cap_ms = min_cpu_cap_in_sec * 1000 * 15 * 60  // CPU capacity in ms for 15 min interval
| extend cpu_percent_of_capacity = round(100.0 * cpu_time_ms / cpu_cap_ms, 2)
| project 
    TimeInterval = originalEventTimestamp,
    ExecutionCount = execution_count,
    TotalCPU_ms = cpu_time_ms,
    AvgCPU_per_exec_ms = avg_cpu_per_exec_ms,
    CPU_Percent_of_Capacity = cpu_percent_of_capacity,
    QueryPlanHashes = query_plan_hashes,
    CPU_Cap_in_sec = min_cpu_cap_in_sec
| order by TimeInterval asc
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:

1. **If zero rows are returned**: Display the exact message:
   "We don't have CPU usage data for the specified query in the specified time period."

2. **If one or more rows are returned**:
   - Display the results as a table
   - After the table, provide a brief summary:
     - Peak CPU interval (time with highest CPU_Percent_of_Capacity)
     - Peak CPU percentage
     - Total execution count across all intervals
     - Average CPU per execution across all intervals

### Task 2: Generate Time Series Visualization (Optional)

If the result has more than 3 data points, suggest generating a time series chart showing:
- X-axis: TimeInterval
- Y-axis: CPU_Percent_of_Capacity
- Secondary Y-axis: ExecutionCount

This helps visualize CPU usage patterns and correlate them with execution frequency.

---

## Example Output

### CPU Usage Over Time for Query `0x51B34948CE07A165`

| TimeInterval | ExecutionCount | TotalCPU_ms | AvgCPU_per_exec_ms | CPU_Percent_of_Capacity |
|--------------|----------------|-------------|---------------------|-------------------------|
| 2026-02-21 11:00:00 | 1,234 | 45,678 | 37.02 | 5.07 |
| 2026-02-21 11:15:00 | 2,456 | 89,012 | 36.24 | 9.89 |
| 2026-02-21 11:30:00 | 3,789 | 156,789 | 41.38 | 17.42 |
| ... | ... | ... | ... | ... |

**Summary**:
- **Peak CPU Interval**: 2026-02-21 11:30:00
- **Peak CPU Percentage**: 17.42%
- **Total Executions**: 7,479
- **Overall Avg CPU/Execution**: 38.21 ms
