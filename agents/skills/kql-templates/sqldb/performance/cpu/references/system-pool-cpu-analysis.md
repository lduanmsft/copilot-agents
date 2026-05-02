---
name: system-pool-cpu-analysis
description: This skill will check CPU usage in the System Pool (excluding the User Pool), and deliver suggestions if bottlenecks are detected
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug System Pool CPU Analysis

## Skill Overview

This skill checks CPU usage in the System Pool (excluding the User Pool) and delivers suggestions if bottlenecks are detected. It analyzes system-level resource pool CPU consumption and identifies high CPU conditions that may indicate internal SQL Server operations consuming excessive resources.

## System Pool CPU Severity Levels

| Severity Level | Max System Pool CPU % | Impact Description |
|----------------|----------------------|-------------------|
| Normal | < 20% | No system pool CPU issue detected |
| Moderate | >= 20% and < 30% | Not very high, but needs attention |
| High | >= 30% | System pool CPU bottleneck, causes significant performance impact |


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
let aggInterval_doNOTchange = time(15m);
let HighCpuThreshold=30;
let cap_interval = materialize(MonDmRealTimeResourceStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize min(cpu_cap_in_sec) by bin (originalEventTimestamp, aggInterval_doNOTchange));
let systemPoolCpuResource=materialize(MonSqlRgHistory
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event =~ 'aggregated_resource_pools_plus_history'
| extend originalEventTimestamp = end_aggregated_sample
| extend pool_name= iff(pool_name =~ 'SloSharedPool1' or pool_name startswith 'UserPool.DBid','User Pool',pool_name)
| extend pool_name= iff(pool_name!='User Pool','System Pools', pool_name)
| where pool_name =='System Pools'
| summarize delta_total_cpu_usage_ms = sum(delta_total_cpu_usage_ms), start_aggregated_sample = min(start_aggregated_sample), end_aggregated_sample = max(end_aggregated_sample) by originalEventTimestamp = bin(end_aggregated_sample, aggInterval_doNOTchange), pool_name
| extend avg_cores_sec = delta_total_cpu_usage_ms/((end_aggregated_sample-start_aggregated_sample)/1ms)
| project-away delta_total_cpu_usage_ms
| lookup kind=leftouter (cap_interval) on originalEventTimestamp
| extend PercentCPU = round(100.0*avg_cores_sec/min_cpu_cap_in_sec,1)
| extend Timestamp=originalEventTimestamp
| project Timestamp, PercentCPU);
systemPoolCpuResource
| summarize avg_cpu_percent=round(avg(PercentCPU),1),
  max_cpu_percent=round(max(PercentCPU),1),
  min_cpu_percent=round(min(PercentCPU),1),
  high_cpu_duration_minutes=countif(PercentCPU>=HighCpuThreshold)*15
```

### Task 2 Output

| Column | Type | Description | Output Column Name |
|--------|------|-------------|-------------------|
| `avg_cpu_percent` | real | Average system pool CPU usage percentage | Average System Pool CPU |
| `max_cpu_percent` | real | Maximum system pool CPU usage percentage. Use to determine severity per the [System Pool CPU Severity Levels](#system-pool-cpu-severity-levels) table | Max System Pool CPU |
| `min_cpu_percent` | real | Minimum system pool CPU usage percentage | Min System Pool CPU |
| `high_cpu_duration_minutes` | int | Total minutes where system pool CPU exceeded 30% threshold | High CPU Duration |

- **max_cpu_percent >= 30** → System pool CPU issue detected
- **max_cpu_percent < 30** → No system pool CPU issue during the investigation period

---

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When System Pool CPU Issue is Detected

#### System Pool CPU Analysis Results

**Yes, system pool CPU issue was detected during the investigation period.**

#### System Pool CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max System Pool CPU** | 45.2% | 🚩 **High** |
| **Average System Pool CPU** | 28.5% | - |
| **Min System Pool CPU** | 8.3% | - |
| **High CPU Duration** | 60 minutes | - |
| **High CPU Threshold** | 30% | - |

#### Analysis

The System Pools (excluding the User Pool) consumed a significant amount of CPU resources, with CPU utilization reaching **45.2%** (High severity). The system pool CPU exceeded the 30% threshold for **60 minutes** during the investigation period.

#### Root Cause Indicators

This pattern suggests:
- **Internal SQL Server operations consuming CPU** - System pools handle background tasks like Backup, PVS Cleanup

#### Recommendations

1. **Review individual pool usage** - Execute the Top 2 System Pool CPU Analysis sub-skill to identify which specific system pools are consuming CPU

---

### When System Pool CPU Usage is Moderate (>= 20% and < 30%)

#### System Pool CPU Analysis Results

**System pool CPU usage is moderate - not critical, but warrants attention.**

#### System Pool CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max System Pool CPU** | 24.8% | ⚠️ **Moderate** |
| **Average System Pool CPU** | 18.2% | - |
| **Min System Pool CPU** | 6.5% | - |
| **High CPU Duration** | 0 minutes | - |
| **High CPU Threshold** | 30% | - |

#### Analysis

The System Pools (excluding the User Pool) showed moderate CPU consumption, with utilization reaching **24.8%** (Moderate severity). While this did not exceed the 30% threshold, it is elevated compared to typical baseline levels and may warrant monitoring.

#### Root Cause Indicators

This pattern suggests:
- **Elevated background activity** - System pools are handling more internal operations than usual
- **Potential early warning sign** - If workload increases, this could escalate to high CPU usage

#### Recommendations

1. **Monitor trend** - Track system pool CPU over time to see if it continues to increase
2. **Review scheduled tasks** - Check if any maintenance jobs or background processes are contributing to the elevated usage

---

### When No System Pool CPU Issue is Detected

#### System Pool CPU Analysis Results

**No, system pool CPU issue was NOT detected during the investigation period.**

#### System Pool CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max System Pool CPU** | 12.4% | 🟢 **Normal** |
| **Average System Pool CPU** | 5.8% | - |
| **Min System Pool CPU** | 1.2% | - |
| **High CPU Duration** | 0 minutes | - |
| **High CPU Threshold** | 30% | - |

#### Analysis

The System Pools (excluding the User Pool) did not consume a significant amount of CPU resources. The maximum system pool CPU usage was **12.4%**, well below the 30% threshold. This rules out system pool CPU as a contributing factor to any performance issues during this period.

---

### Output Format Requirements

1. **Always start with a direct answer** - State clearly whether system pool CPU issue was detected
2. **Use the severity table** - Map max system pool CPU percentage to severity levels from the System Pool CPU Severity Levels section
3. **Include a summary table** - Present all metrics with their values
4. **Provide analysis** - Explain what the numbers mean in context
5. **Add recommendations when issue detected** - Give actionable next steps based on findings
6. **Use 🚩 emoji** - Flag High severity for visibility
7. **Use ⚠️ emoji** - Flag Moderate severity for attention
8. **Use 🟢 emoji** - Indicate Normal severity when no issue detected

### Task 2: Execute Sub-Skills

**Execute the following sub-skill ONLY if `max_cpu_percent >= 30`. If below threshold, terminate this skill.**
- Execute the skill [Top 2 System Pool CPU Analysis](top-system-pool-cpu-analysis.md)
