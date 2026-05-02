---
name: top-system-pool-cpu-analysis
description: Analyze the top 2 system resource pool CPU usage for SQL Database performance troubleshooting
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Top System Pool CPU Analysis

## Skill Overview

This skill analyzes the top 2 system resource pool CPU usage patterns for a SQL Database. It helps identify which system resource pools are consuming the most CPU resources by analyzing the MonSqlRgHistory telemetry data. The skill excludes SloSharedPool1 and UserPool databases to focus on system-level resource pools, providing insights into CPU utilization patterns over time.

> **Note**: For aggregate system pool CPU severity levels, see [System Pool CPU Analysis](system-pool-cpu-analysis.md#system-pool-cpu-severity-levels).


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

```kql
let aggInterval_doNOTchange = time(15m) ;
let cap_interval = materialize(MonDmRealTimeResourceStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize min(cpu_cap_in_sec) by bin (originalEventTimestamp, aggInterval_doNOTchange));
MonSqlRgHistory
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where event =~ 'aggregated_resource_pools_plus_history'
| where LogicalServerName =~ '{LogicalServerName}'
| extend originalEventTimestamp = end_aggregated_sample
| extend pool_name !~ 'SloSharedPool1' and pool_name !startswith 'UserPool.DBid'
| lookup kind = inner(
MonSqlRgHistory
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where event =~ 'aggregated_resource_pools_plus_history'
| where LogicalServerName =~ '{LogicalServerName}'
| where pool_name !~ 'SloSharedPool1' and pool_name !startswith 'UserPool.DBid'
| top-nested {TopN} of pool_name by max(delta_total_cpu_usage_ms) desc
) on pool_name
| summarize delta_total_cpu_usage_ms = sum(delta_total_cpu_usage_ms), start_aggregated_sample = min(start_aggregated_sample), end_aggregated_sample = max(end_aggregated_sample) by originalEventTimestamp = bin(end_aggregated_sample, aggInterval_doNOTchange), pool_name
| extend avg_cores_sec = delta_total_cpu_usage_ms/((end_aggregated_sample-start_aggregated_sample)/1ms)
| project-away delta_total_cpu_usage_ms
| lookup kind=leftouter (cap_interval) on originalEventTimestamp
| extend PercentCPU = round(100.0*avg_cores_sec/min_cpu_cap_in_sec,3)
| extend Timestamp=originalEventTimestamp
| project Timestamp, pool_name, PercentCPU
```

#### Output
Follow these instructions exactly. Only display output when specified:

1. Display the raw result from the query without any modification

---

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### Top 5 System Pool CPU Summary

| Rank | Pool Name | Max CPU % | Avg CPU % | Peak Time (UTC) |
|------|-----------|-----------|-----------|-----------------|
| 1 | **internal** | 🚩 **53.86%** | 14.32% | 2026-03-18 19:15 |
| 2 | **SloSecSharedPool** | 15.51% | 3.79% | 2026-03-18 19:15 |
| 3 | InMemDmvCollectorPool | 0.18% | 0.11% | 2026-03-18 18:45 |
| 4 | InMemQueryStorePool | 0.008% | 0.006% | 2026-03-18 19:15 |
| 5 | InMemBackupRestorePool | 0.004% | 0.003% | 2026-03-18 17:45 |

### CPU Timeline for Top 2 Pools

| Timestamp (UTC) | internal (%) | SloSecSharedPool (%) |
|-----------------|--------------|---------------------|
| 15:00 | 4.17 | 1.09 |
| 15:15 | 3.70 | 0.99 |
| 15:30 | 6.63 | 1.66 |
| 15:45 | 2.84 | 0.73 |
| 16:00 | 3.49 | 0.92 |
| 16:15 | 3.70 | 0.98 |
| 16:30 | 6.31 | 1.26 |
| 16:45 | 2.77 | 0.68 |
| 17:00 | 2.95 | 0.75 |
| 17:15 | 2.54 | 0.63 |
| 17:30 | 2.43 | 0.60 |
| 17:45 | 2.88 | 0.76 |
| 18:00 | 2.35 | 0.59 |
| 18:15 | 🚩 14.46 | 4.23 |
| 18:30 | 🚩 19.64 | 5.52 |
| 18:45 | 🚩 **50.12** | 🚩 **14.72** |
| 19:00 | 🚩 22.03 | 5.59 |
| 19:15 | 🚩 **53.86** | 🚩 **15.51** |
| 19:30 | 🚩 45.58 | 🚩 12.60 |
| 19:45 | 🚩 19.25 | 5.28 |

### Analysis

Provide analysis of the top system pool CPU consumers:

1. **Identify the dominant pool** - Which pool is consuming the most CPU
2. **Correlate with other metrics** - Check if the spike correlates with kernel mode CPU or other issues
3. **Explain pool purposes** - Provide context on what each pool is responsible for

| Pool | Purpose | Typical Analysis |
|------|---------|------------------|
| **internal** | Core SQL engine operations (geo-replication, redo, recovery) | High usage on geo-secondary indicates heavy redo/apply operations |
| **SloSecSharedPool** | Secondary/geo-replication workloads | Elevated usage confirms geo-replication activity |
| **InMemDmvCollectorPool** | DMV data collection | Usually low; spikes indicate monitoring overhead |
| **InMemQueryStorePool** | Query Store operations | Usually low; spikes indicate QDS flush activity |
| **InMemBackupRestorePool** | Backup and restore operations | Spikes during backup windows |
| **InMemXdbLoginPool** | Cross-database login and authentication operations | Spikes indicate authentication or cross-database query activity |
| **InMemXdbSeedingPool** | Cross-database seeding operations (geo-replication initial sync) | High usage during geo-replica seeding or database copy operations |
| **PVSCleanerPool** | Persistent Version Store cleanup (ADR version cleanup) | Spikes indicate PVS cleanup after long transactions or high version generation |
| **PVSPreAllocPool** | Persistent Version Store pre-allocation | Elevated usage indicates proactive PVS space allocation for ADR |

### Output Format Requirements

1. **Always include the Top N Summary table** - Show all top pools with their max, avg CPU and peak time
2. **Include CPU Timeline for Top 2 Pools** - Provide time-series view for the two highest consumers
3. **Use 🚩 emoji** - Flag values exceeding thresholds (e.g., >20% for system pools)
4. **Bold peak values** - Highlight the maximum values in each column
5. **Provide analysis section** - Explain the findings and correlate with other metrics
