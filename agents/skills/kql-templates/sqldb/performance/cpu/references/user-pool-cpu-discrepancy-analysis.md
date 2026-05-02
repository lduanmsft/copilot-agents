---
name: user-pool-cpu-discrepancy-analysis
description: This skill will check if there are significant discrepancy between User Pool CPU and the combined total of QDS CPU, Successful Compile CPU and Failed Compile CPU. If significant discrepancy is detected, will try to identify the cause of the discrepancy.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug User Pool CPU Discrepancy Analysis

## Skill Overview

This skill will check if there are significant discrepancy between User Pool CPU and the combined total of QDS CPU, Successful Compile CPU and Failed Compile CPU. If significant discrepancy is detected, will try to identify the cause of the discrepancy.

## CPU Discrepancy Severity Levels

| Severity Level | Recorded CPU / User Pool CPU Ratio | Impact Description |
|----------------|-----------------------------------|-------------------|
| Normal | ≥ 80% | No CPU discrepancy detected - QDS and compilation CPU accounts for most of User Pool CPU |
| High | < 80% | 🚩 Significant CPU discrepancy detected - indicates hidden CPU consumers, terminated queries, or telemetry gaps |

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
| Task 1 | Enable and execute the Kusto query below | Always |
| Task 2 | Display Recommended Next Steps | Always |

## Execution Steps

### Task 1: Enable and execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
let MonDmRealTimeResourceStats_Sample_sec=15;
let totalUserPoolCpu_ms=toscalar(MonDmRealTimeResourceStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize  tolong(sum(avg_cpu_percent*cpu_cap_in_sec *MonDmRealTimeResourceStats_Sample_sec*1000/100)));
let qdscpu_ms=toscalar(MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize tolong(sum(cpu_time)/1000));
let successful_compilecpu_ms=toscalar(MonWiQueryParamData
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| summarize tolong(sum(compile_cpu_time)/1000));
let failed_compilecpu_ms=toscalar(MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event =~'failed_compilation'
| summarize tolong(sum(compile_cpu)));
let totalRecordedCPU_ms=qdscpu_ms+successful_compilecpu_ms+failed_compilecpu_ms;//QDS CPU + Successful Compile CPU + Failed Compile CPU
let  totalRecordedCPU_totalUserPoolCpu_ratio=round(totalRecordedCPU_ms*100/totalUserPoolCpu_ms,1);
let IssueDetected=case(totalRecordedCPU_totalUserPoolCpu_ratio >= 80, 'false','true');//If the ratio is closed to 80%, we think the gap can be ignored, and IssueDetected is false.
let avgCPUPercentage=round(totalUserPoolCpu_ms*100.0/{SumCpuMillisecondOfAllApp},1);
let  totalRecordedCPUPercentage=round(totalRecordedCPU_ms*100.0/{SumCpuMillisecondOfAllApp},1);
let  qdsPercentage=round(qdscpu_ms*100/{SumCpuMillisecondOfAllApp},1);
let  successful_CompileCpuPercentage=round(successful_compilecpu_ms*100/{SumCpuMillisecondOfAllApp},1);
let  failed_CompileCpuPercentage=round(failed_compilecpu_ms*100/{SumCpuMillisecondOfAllApp},1);
print IssueDetected=IssueDetected,
      totalUserPoolCpu_ms=totalUserPoolCpu_ms,
      avgCPUPercentage=avgCPUPercentage,
      totalRecordedCPU_ms=totalRecordedCPU_ms,
      totalRecordedCPUPercentage=totalRecordedCPUPercentage,
      qdscpu_ms=qdscpu_ms,
      qdsPercentage=qdsPercentage,
      successful_compilecpu_ms=successful_compilecpu_ms,
      successful_CompileCpuPercentage=successful_CompileCpuPercentage,
      failed_compilecpu_ms=failed_compilecpu_ms,
      failed_CompileCpuPercentage=failed_CompileCpuPercentage
```

#### Output
Follow these instructions exactly. Only display output when specified:

1. **If `IssueDetected` is `false`**: 
   - Display no output
   - Terminate this skill immediately and exit
   
2. **If `IssueDetected` is `true`**: 
   - Display the following message exactly as written, without any modifications:
   - "CPU Discrepancy has been detected, doing further check to figure out why CPU discrepancy happened"


### Task 2: Display Recommended Next Steps

**Display the following recommendation ONLY if `IssueDetected` is `true`. If `false`, terminate this skill.**

#### Output

Display the following message exactly as written:

> 🔍 **CPU Discrepancy Detected - Recommended Investigation Steps**
> 
> A significant CPU discrepancy has been detected between User Pool CPU and the recorded CPU (QDS + Compilation). To identify the root cause, consider running the following skills:
> 
> | Skill | Description | Link |
> |-------|-------------|------|
> | **SQL Restart/Failover Analysis** | Check if SQL restarts or failovers occurred during the time window | [sql-restart-and-failover-detection.md](../../miscellaneous/references/sql-restart-and-failover-detection.md) |
> | **Kill Command Analysis** | Check if KILL commands terminated queries before CPU was recorded | [kill-command.md](../../miscellaneous/references/kill-command.md) |
> | **QDS Readonly Detection** | Check if Query Data Store entered readonly mode | [QDS SKILL.md](../../query-store/SKILL.md) |
> | **Long Running Queries** | Check for long-running transactions that may not have completed | [long-running-transactions.md](../../blocking/references/long-running-transactions.md) |
> 
> ⚠️ **If the above checks do not identify the root cause:**
> 
> Even when all four checks return negative results, CPU discrepancy can still occur due to scenarios not captured in standard telemetry, such as internal system processes, background tasks, or query execution patterns that bypass QDS recording. In these cases, analyze **Azure Profiler traces** to capture detailed CPU stack information. Note that Azure SQL DB automatically collects profiler traces when CPU usage is high, so traces may already be available for the incident time window.

---

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### Sample Output - No Discrepancy Detected

When the recorded CPU accounts for ≥80% of User Pool CPU, no discrepancy is detected and the skill terminates silently.

| Metric | Value | % of Total CPU Capacity |
|--------|-------|------------------------|
| **User Pool CPU** | 12,450,000 ms | 45.2% |
| **Recorded CPU (Total)** | 10,560,000 ms | 38.3% |
| └─ QDS CPU | 10,320,000 ms | 37.5% |
| └─ Successful Compile CPU | 185,000 ms | 0.7% |
| └─ Failed Compile CPU | 55,000 ms | 0.2% |

**Analysis**: The recorded CPU (10.56 GB-ms) accounts for **84.8%** of User Pool CPU (12.45 GB-ms), which is above the 80% threshold. ✅ **No significant CPU discrepancy detected.**

> **Result**: Skill terminates - no further investigation needed.

---

### Sample Output - Discrepancy Detected

When the recorded CPU accounts for <80% of User Pool CPU, a significant discrepancy is detected.

#### CPU Discrepancy Summary

| Metric | Value | % of Total CPU Capacity |
|--------|-------|------------------------|
| **User Pool CPU** | 530,068,246 ms | 93.5% |
| **Recorded CPU (Total)** | 3,792,516 ms | 0.7% |
| └─ QDS CPU | 3,780,916 ms | ~0% |
| └─ Successful Compile CPU | 1,081 ms | ~0% |
| └─ Failed Compile CPU | 10,519 ms | ~0% |

#### Analysis

The User Pool CPU (530 GB-ms) is **~140x higher** than the recorded CPU from QDS and compilation (3.8 GB-ms). The recorded CPU only accounts for **0.7%** of the User Pool CPU, which is significantly below the expected 80% threshold.

---

> 🔍 **CPU Discrepancy Detected - Recommended Investigation Steps**
> 
> A significant CPU discrepancy has been detected between User Pool CPU and the recorded CPU (QDS + Compilation). To identify the root cause, consider running the following skills:
> 
> | Skill | Description | Link |
> |-------|-------------|------|
> | **SQL Restart/Failover Analysis** | Check if SQL restarts or failovers occurred during the time window | [sql-restart-and-failover-detection.md](../../miscellaneous/references/sql-restart-and-failover-detection.md) |
> | **Kill Command Analysis** | Check if KILL commands terminated queries before CPU was recorded | [kill-command.md](../../miscellaneous/references/kill-command.md) |
> | **QDS Readonly Detection** | Check if Query Data Store entered readonly mode | [QDS SKILL.md](../../query-store/SKILL.md) |
> | **Long Running Queries** | Check for long-running transactions that may not have completed | [long-running-transactions.md](../../blocking/references/long-running-transactions.md) |
> 
> 
> Even when all four checks return negative results, CPU discrepancy can still occur due to scenarios not captured in standard telemetry, such as internal system processes, background tasks, or query execution patterns that bypass QDS recording. In these cases, analyze **Azure Profiler traces** to capture detailed CPU stack information. Note that Azure SQL DB automatically collects profiler traces when CPU usage is high, so traces may already be available for the incident time window.

### Output Format Requirements

1. **Always include the CPU Discrepancy Summary table** - Show User Pool CPU, Recorded CPU (Total), and breakdown by QDS/Compile CPU
2. **Use hierarchical indentation** - Use `└─` prefix for sub-components (QDS CPU, Successful Compile CPU, Failed Compile CPU)
3. **Include percentage of total capacity** - Show what percentage each metric represents of total CPU capacity
4. **Provide analysis section** - Explain the magnitude of discrepancy and its significance
5. **Use bold for emphasis** - Highlight key metrics and multipliers (e.g., **~140x higher**)
6. **Include recommended next steps** - Always display the investigation skills table when discrepancy is detected
