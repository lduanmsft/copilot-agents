---
name: top-cpu-queries-over-time
description: Time-series analysis of CPU usage trends per query at 15-minute intervals. Use for "CPU trend", "CPU over time", "CPU timeline" - NOT for "top N CPU queries" summary.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
keywords: ['cpu trend', 'cpu over time', 'cpu timeline', 'cpu pattern', 'cpu history', 'time series']
---

# Debug Top CPU Usage T-SQL Execution Over Time

## Skill Overview

**⚠️ For simple "top N high CPU queries" summary requests, use [top-cpu-queries.md](top-cpu-queries.md) instead.**

This skill analyzes Query Data Store (QDS) execution statistics to identify the top TopN T-SQL queries consuming the most CPU over time. It calculates CPU utilization percentage for each query at 15-minute intervals and provides a time-series view of CPU consumption patterns.

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

let QDSAggIntervalInMin = time(15m);
let top_N = materialize(MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| top-nested {TopN} of query_hash by sum(cpu_time) desc
| project-away  aggregated_query_hash
);
let cap_interval = materialize(MonDmRealTimeResourceStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize min(cpu_cap_in_sec) by bin(originalEventTimestamp, QDSAggIntervalInMin));
let All_cpu_utilization = materialize(MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize cores_per_sec = sum(cpu_time) / (QDSAggIntervalInMin / time(1microsecond)) by bin(originalEventTimestamp, QDSAggIntervalInMin), query_hash
| lookup kind = inner ( cap_interval ) on originalEventTimestamp
| extend TotalQueryCPU_Pct = round(100.0 * cores_per_sec / min_cpu_cap_in_sec, 1)
| project originalEventTimestamp, query_hash, TotalQueryCPU_Pct);
let top_N_cpu_utilization = materialize(MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| lookup kind = inner ( top_N ) on query_hash
| summarize cores_per_sec = sum(cpu_time) / (QDSAggIntervalInMin / time(1microsecond)) by bin(originalEventTimestamp, QDSAggIntervalInMin), query_hash
| lookup kind = inner ( cap_interval ) on originalEventTimestamp
| extend TotalQueryCPU_Pct = round(100.0 * cores_per_sec / min_cpu_cap_in_sec, 1)
| project originalEventTimestamp, query_hash, TotalQueryCPU_Pct
| union All_cpu_utilization);//top_N_cpu_utilization
// Create a temporary table containing rows of timestamps that are binned with size 'QDSAggIntervalInMin'.
// The timestamps range between the smallest and the largest timestamp retrieved from 'top_N_cpu_utilization' table
let timestamps = range
originalEventTimestamp
from bin(toscalar(top_N_cpu_utilization | summarize min(originalEventTimestamp)), QDSAggIntervalInMin)
to bin(toscalar(top_N_cpu_utilization | summarize max(originalEventTimestamp)), QDSAggIntervalInMin)
step QDSAggIntervalInMin;
// CROSS JOIN. The new table will contain a new column originalEventTimestamp such that the timestamps are binned equally for each query_hash.
// The cardinality of this new table will be N * NumOfRows(timestamps)
let top_N_with_timestamps = timestamps
| extend tmp_join_col = 1 // temporary column with a dummy value 1 for cross-join
| join kind = inner (
top_N
| project query_hash
| extend tmp_join_col = 1 // temporary column with a dummy value 1 for cross-join
) on tmp_join_col
| project query_hash, originalEventTimestamp;
// Final results
top_N_cpu_utilization
| join kind = rightouter(top_N_with_timestamps) on query_hash, originalEventTimestamp
| project originalEventTimestamp=originalEventTimestamp1, query_hash=query_hash1, TotalQueryCPU_Pct
| extend TotalQueryCPU_Pct = case(isnull(TotalQueryCPU_Pct), 0.0, TotalQueryCPU_Pct) // fill missing value with 0
| sort by originalEventTimestamp asc

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw result.
