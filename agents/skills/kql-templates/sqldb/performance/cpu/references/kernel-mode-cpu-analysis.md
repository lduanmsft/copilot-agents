---
name: kernel-mode-cpu-analysis
description: This skill will check CPU usage in the Kernel Mode, and deliver suggestions if bottlenecks are detected
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Kernel Mode CPU Analysis

## Skill Overview

This skill checks CPU usage in the Kernel Mode and delivers suggestions if bottlenecks are detected. It analyzes kernel-level CPU consumption and identifies high CPU conditions that may indicate system-level performance issues.

## Kernel CPU Severity Levels

| Severity Level | Max Kernel CPU % | Impact Description |
|----------------|------------------|-------------------|
| Normal | < 10% | No kernel CPU issue detected |
| Moderate | >= 10% and < 15% | Not very high, but needs attention |
| High | >= 15% | Kernel CPU bottleneck, cause significant performance issue |


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

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{ApplicationNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let HighCpuThreshold=15;
MonRgLoad
| extend originalEventTimestamp = originalEventTimestampFrom
| where {ApplicationNamesNodeNamesWithOriginalEventTimeRange}
| where (event =~ 'instance_load' and code_package_name contains 'Code')
| extend KernelCpuUsagePeakPercent = round((kernel_load_peak*1.0 / cpu_load_cap) * 100,1)
| summarize peak_process_kernel_cpu_percent=max(KernelCpuUsagePeakPercent) by bin(originalEventTimestamp, 5min)
| summarize avg_kernel_cpu_percent=round(avg(peak_process_kernel_cpu_percent),1),
  max_kernel_cpu_percent=round(max(peak_process_kernel_cpu_percent),1),
  min_kernel_cpu_percent=round(min(peak_process_kernel_cpu_percent),1),
  high_cpu_duration_minutes=countif(peak_process_kernel_cpu_percent>=HighCpuThreshold)*5
```

### Task 1 Output

| Column | Type | Description | Output Column Name |
|--------|------|-------------|-------------------|
| `avg_kernel_cpu_percent` | real | Average kernel CPU usage percentage | Average Kernel CPU |
| `max_kernel_cpu_percent` | real | Maximum kernel CPU usage percentage. Use to determine severity per the [Kernel CPU Severity Levels](#kernel-cpu-severity-levels) table | Max Kernel CPU |
| `min_kernel_cpu_percent` | real | Minimum kernel CPU usage percentage | Min Kernel CPU |
| `high_cpu_duration_minutes` | int | Total minutes where kernel CPU exceeded 15% threshold | High CPU Duration |

- **max_kernel_cpu_percent >= 15** → Kernel CPU issue detected
- **max_kernel_cpu_percent < 15** → No kernel CPU issue during the investigation period

---

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.  Do not adjust or deviate from the section "Recommendations"

### When Kernel CPU Issue is Detected

#### Kernel Mode CPU Analysis Results

**Yes, kernel CPU issue was detected during the investigation period.**

#### Kernel CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max Kernel CPU** | 32.7% | 🚩 **High** |
| **Average Kernel CPU** | 12.3% | - |
| **Min Kernel CPU** | 2.1% | - |
| **High CPU Duration** | 45 minutes | - |
| **High CPU Threshold** | 15% | - |

#### Analysis

The Kernel Mode of the Azure DB ran into a CPU issue, with CPU utilization reaching **32.7%** (High severity). The kernel CPU exceeded the 15% threshold for **45 minutes** during the investigation period.

#### Root Cause Indicators

This pattern suggests:
- **System-level operations consuming CPU** - Kernel mode CPU indicates OS-level or driver-related processing

#### Recommendations


1. **Collect Azure Profiler Trace** - Capture detailed CPU profiling to identify specific kernel-mode operations


---

### When Moderate Kernel CPU Issue is Detected

#### Kernel Mode CPU Analysis Results

**Yes, moderate kernel CPU issue was detected during the investigation period.**

#### Kernel CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max Kernel CPU** | 12.8% | ⚠️ **Moderate** |
| **Average Kernel CPU** | 8.4% | - |
| **Min Kernel CPU** | 3.2% | - |
| **High CPU Duration** | 0 minutes | - |
| **High CPU Threshold** | 15% | - |

#### Analysis

The Kernel Mode of the Azure DB experienced moderate CPU usage, with CPU utilization reaching **12.8%** (Moderate severity). While the kernel CPU did not exceed the 15% High threshold, it is elevated above normal levels (>= 10%) and warrants attention.

#### Root Cause Indicators

This pattern suggests:
- **Elevated system-level operations** - Kernel mode CPU is higher than normal but not yet critical

#### Recommendations

1. **Monitor for escalation** - Continue monitoring to see if kernel CPU increases to High severity levels


---

### When No Kernel CPU Issue is Detected

#### Kernel Mode CPU Analysis Results

**No, kernel CPU issue was NOT detected during the investigation period.**

#### Kernel CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max Kernel CPU** | 3.4% | 🟢 **Normal** |
| **Average Kernel CPU** | 1.6% | - |
| **Min Kernel CPU** | 0.8% | - |
| **High CPU Duration** | 0 minutes | - |
| **High CPU Threshold** | 15% | - |

#### Analysis

The Kernel Mode of the Azure DB did not encounter a high CPU issue. The maximum kernel CPU usage was **3.4%**, well below the 15% threshold. This rules out kernel-mode CPU as a contributing factor to any performance issues during this period.

---

### Output Format Requirements

1. **Always start with a direct answer** - State clearly whether kernel CPU issue was detected
2. **Use the severity table** - Map max kernel CPU percentage to severity levels from the Kernel CPU Severity Levels section
3. **Include a summary table** - Present all metrics with their values
4. **Provide analysis** - Explain what the numbers mean in context
5. **Use ONLY documented recommendations** - When issue is detected, include ONLY the recommendations explicitly listed in this skill file. Do NOT add, invent, or modify recommendations
6. **Use 🚩 emoji** - Flag High or Severe kernel CPU for visibility
7. **Use ⚠️ emoji** - Flag Moderate kernel CPU for attention
8. **Use 🟢 emoji** - Indicate Normal severity when no issue detected