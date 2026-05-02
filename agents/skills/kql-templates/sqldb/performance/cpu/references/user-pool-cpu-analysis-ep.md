---
name: user-pool-cpu-analysis-ep
description: This skill will check CPU usage in the User Pool for elastic pool databases
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug User Pool CPU Analysis

## Skill Overview

This skill analyzes CPU usage in the User Pool to determine if high CPU issues exist. It checks whether CPU utilization exceeds the 80% threshold and identifies significant CPU usage changes. This skill is specifically for Elastic Pool databases.

## User Pool CPU Severity Levels

| Severity Level | Max User Pool CPU % | Impact Description |
|----------------|---------------------|-------------------|
| Normal | < 80% | No user pool CPU issue detected |
| High | >= 80% | User pool CPU bottleneck, causes significant performance impact |

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

**This skill has 3 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Query user pool CPU summary | Always |
| Task 2 | Query hourly CPU pattern | ONLY if max_cpu_percent >= 80% |
| Task 3 | Display recommended next steps | ONLY if max_cpu_percent >= 80% |

---

## Execution Steps

### Task 1: Query User Pool CPU Summary

If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them. Also verify `{isInElasticPool}` = true before executing this skill.

```kql
let HighCpuThreshold=80;
let SignificantChangeThreshold=40;
MonResourcePoolStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| summarize avg_cpu_percent=round(avg(avg_cpu_percent),2),
  max_cpu_percent=round(max(avg_cpu_percent),2),
  min_cpu_percent=round(min(avg_cpu_percent),2),
  high_cpu_duration_seconds=countif(avg_cpu_percent>=HighCpuThreshold)*15
| extend cpu_change_percent=round(max_cpu_percent - min_cpu_percent, 2)
| extend significant_change_detected=(cpu_change_percent >= SignificantChangeThreshold)
```

### Task 1 Output

| Column | Type | Description | Output Column Name |
|--------|------|-------------|-------------------|
| `avg_cpu_percent` | real | Average user pool CPU usage percentage | Average User Pool CPU |
| `max_cpu_percent` | real | Maximum user pool CPU usage percentage. Use to determine severity per the [User Pool CPU Severity Levels](#user-pool-cpu-severity-levels) table | Max User Pool CPU |
| `min_cpu_percent` | real | Minimum user pool CPU usage percentage | Min User Pool CPU |
| `high_cpu_duration_seconds` | int | Total seconds where user pool CPU exceeded 80% threshold | High CPU Duration |
| `cpu_change_percent` | real | Difference between max and min CPU (max - min) | CPU Change |
| `significant_change_detected` | bool | True if cpu_change_percent >= 40% | Significant Change |

### Issue Detection Logic

- **max_cpu_percent >= 80** → 🚩 User pool CPU issue detected → **CONTINUE TO TASK 2**
- **max_cpu_percent < 80 AND significant_change_detected = true** → ⚠️ No high CPU but significant CPU change detected (warn customer) → Terminate skill
- **max_cpu_percent < 80 AND significant_change_detected = false** → 🟢 No user pool CPU issue during the investigation period → Terminate skill

---

### Task 2: Query Hourly CPU Pattern

**Execute this task ONLY if `max_cpu_percent >= 80` from Task 1.**

This query provides an hourly breakdown of CPU usage to identify when the CPU spikes occurred during the investigation period.

```kql
MonResourcePoolStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| summarize 
    avg_cpu_percent=round(avg(avg_cpu_percent),2), 
    max_cpu_percent=round(max(avg_cpu_percent),2),
    min_cpu_percent=round(min(avg_cpu_percent),2)
  by bin(originalEventTimestamp, 1h)
| order by originalEventTimestamp asc
```

### Task 2 Output

| Column | Type | Description | Output Column Name |
|--------|------|-------------|-------------------|
| `originalEventTimestamp` | datetime | Hour bucket (UTC) | Hour (UTC) |
| `avg_cpu_percent` | real | Average CPU usage for that hour | Avg CPU |
| `max_cpu_percent` | real | Maximum CPU usage for that hour | Max CPU |
| `Status` | string | Derived from `max_cpu_percent` using Status Logic below | Status |

**Display the results as a table with the following format:**

| Hour (UTC) | Avg CPU | Max CPU | Status |
|------------|---------|---------|--------|
| 2026-01-15 10:00 | 25.4% | 45.2% | ✅ Normal |
| 2026-01-15 11:00 | 85.3% | 99.8% | 🚩 High |
| ... | ... | ... | ... |

**Status Logic:**
- `max_cpu_percent >= 80` → 🚩 **High** or 🚩 **Critical** (if max >= 95%)
- `max_cpu_percent >= 60 AND max_cpu_percent < 80` → ⚠️ **Rising**
- `max_cpu_percent < 60` → ✅ **Normal**

---

### Task 3: Display Recommended Next Steps

**Display the following recommendation ONLY if `max_cpu_percent >= 80`. If below threshold, terminate this skill.**

#### Output

Display the following message exactly as written:

> 🔍 **High CPU Detected - Recommended Investigation Steps**
> 
> High user pool CPU has been detected on the Elastic Pool. To identify the root cause, consider running the following skills:
> 
> | Skill | Description | Link |
> |-------|-------------|------|
> | **CPU Discrepancy Analysis** | Check if CPU reported matches QDS + Compile CPU. Helps identify hidden CPU consumers or telemetry gaps | [user-pool-cpu-discrepancy-analysis.md](user-pool-cpu-discrepancy-analysis.md) |
> | **Query Execution CPU Analysis** | Identify top CPU-consuming queries from QDS | [query-execution-cpu-analysis.md](../../queries/references/query-execution-cpu-analysis.md) |
> | **Successful Compilation CPU** | Check if query compilation is consuming excessive CPU | [cpu-usage-of-successful-compilation.md](../../compilation/references/cpu-usage-of-successful-compilation.md) |
> | **Failed Compilation CPU** | Check if failed compilations are contributing to CPU usage | [cpu-usage-of-failed-compilation.md](../../compilation/references/cpu-usage-of-failed-compilation.md) |

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When User Pool CPU Issue is Detected

#### User Pool CPU Analysis Results

**Yes, user pool CPU issue was detected on the Elastic Pool during the investigation period.**

#### User Pool CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max User Pool CPU** | 99.8% | 🚩 **High** |
| **Average User Pool CPU** | 45.2% | - |
| **Min User Pool CPU** | 2.1% | - |
| **High CPU Duration** | 1800 seconds (30 minutes) | - |
| **High CPU Threshold** | 80% | - |

#### Analysis

The User Pool of the Elastic Pool ran into a CPU issue, with CPU utilization reaching **99.8%** (High severity). The user pool CPU exceeded the 80% threshold for **1800 seconds (30 minutes)** during the investigation period.

#### Root Cause Indicators

This pattern suggests:
- **Query workload consuming excessive CPU** - User pool CPU indicates application queries are CPU-bound
- **Potential query performance issues** - May indicate inefficient queries, missing indexes, or parameter sniffing

---

> 🔍 **High CPU Detected - Recommended Investigation Steps**
> 
> High user pool CPU has been detected on the Elastic Pool. To identify the root cause, consider running the following skills:
> 
> | Skill | Description | Link |
> |-------|-------------|------|
> | **CPU Discrepancy Analysis** | Check if CPU reported matches QDS + Compile CPU. Helps identify hidden CPU consumers or telemetry gaps | [user-pool-cpu-discrepancy-analysis.md](user-pool-cpu-discrepancy-analysis.md) |
> | **Query Execution CPU Analysis** | Identify top CPU-consuming queries from QDS | [query-execution-cpu-analysis.md](../../queries/references/query-execution-cpu-analysis.md) |
> | **Successful Compilation CPU** | Check if query compilation is consuming excessive CPU | [cpu-usage-of-successful-compilation.md](../../compilation/references/cpu-usage-of-successful-compilation.md) |
> | **Failed Compilation CPU** | Check if failed compilations are contributing to CPU usage | [cpu-usage-of-failed-compilation.md](../../compilation/references/cpu-usage-of-failed-compilation.md) |

---

### When User Pool CPU Issue is Detected (with short duration note)

#### User Pool CPU Analysis Results

**Yes, user pool CPU issue was detected on the Elastic Pool during the investigation period.**

#### User Pool CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max User Pool CPU** | 85.3% | 🚩 **High** |
| **Average User Pool CPU** | 28.4% | - |
| **Min User Pool CPU** | 5.2% | - |
| **High CPU Duration** | 45 seconds | - |
| **High CPU Threshold** | 80% | - |

#### Analysis

The User Pool of the Elastic Pool ran into a CPU issue, with CPU utilization reaching **85.3%** (High severity). The user pool CPU exceeded the 80% threshold for **45 seconds** during the investigation period.

> ⚠️ **Note**: Although the Elastic Pool experienced high CPU usage, there was no observation of a continuous high CPU condition lasting 15 minutes. This suggests short CPU spikes rather than sustained high CPU.

#### Root Cause Indicators

This pattern suggests:
- **Intermittent CPU spikes** - Short bursts of high CPU rather than sustained load
- **Possible batch job or scheduled task** - Brief high CPU may indicate periodic workload

---

> 🔍 **High CPU Detected - Recommended Investigation Steps**
> 
> High user pool CPU has been detected on the Elastic Pool. To identify the root cause, consider running the following skills:
> 
> | Skill | Description | Link |
> |-------|-------------|------|
> | **CPU Discrepancy Analysis** | Check if CPU reported matches QDS + Compile CPU. Helps identify hidden CPU consumers or telemetry gaps | [user-pool-cpu-discrepancy-analysis.md](user-pool-cpu-discrepancy-analysis.md) |
> | **Query Execution CPU Analysis** | Identify top CPU-consuming queries from QDS | [query-execution-cpu-analysis.md](../../queries/references/query-execution-cpu-analysis.md) |
> | **Successful Compilation CPU** | Check if query compilation is consuming excessive CPU | [cpu-usage-of-successful-compilation.md](../../compilation/references/cpu-usage-of-successful-compilation.md) |
> | **Failed Compilation CPU** | Check if failed compilations are contributing to CPU usage | [cpu-usage-of-failed-compilation.md](../../compilation/references/cpu-usage-of-failed-compilation.md) |

---

### When No User Pool CPU Issue is Detected (but significant change observed)

#### User Pool CPU Analysis Results

**No, user pool CPU issue was NOT detected on the Elastic Pool during the investigation period.**

#### User Pool CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max User Pool CPU** | 65.2% | 🟢 **Normal** |
| **Average User Pool CPU** | 25.8% | - |
| **Min User Pool CPU** | 8.3% | - |
| **High CPU Duration** | 0 seconds | - |
| **High CPU Threshold** | 80% | - |
| **CPU Change (Max - Min)** | 56.9% | ⚠️ Significant |

#### Analysis

The User Pool of the Elastic Pool did not encounter a high CPU issue, as the maximum CPU usage was **65.2%**, below the 80% threshold. However, we notice that the CPU usage had a **significant change of 56.9%** (from 8.3% to 65.2%), which may warrant attention.

#### Root Cause Indicators

This pattern suggests:
- **Variable workload** - CPU usage fluctuated significantly during the period
- **Potential workload changes** - May indicate batch processing or varying application load

---

### When No User Pool CPU Issue is Detected

#### User Pool CPU Analysis Results

**No, user pool CPU issue was NOT detected on the Elastic Pool during the investigation period.**

#### User Pool CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max User Pool CPU** | 35.4% | 🟢 **Normal** |
| **Average User Pool CPU** | 12.8% | - |
| **Min User Pool CPU** | 3.2% | - |
| **High CPU Duration** | 0 seconds | - |
| **High CPU Threshold** | 80% | - |

#### Analysis

The User Pool of the Elastic Pool did not encounter a high CPU issue. The maximum user pool CPU usage was **35.4%**, well below the 80% threshold. This rules out user pool CPU as a contributing factor to any performance issues during this period.

---

### Output Format Requirements

1. **Always start with a direct answer** - State clearly whether user pool CPU issue was detected
2. **Use the severity table** - Map max user pool CPU percentage to severity levels from the User Pool CPU Severity Levels section
3. **Include a summary table** - Present all metrics with their values
4. **Provide analysis** - Explain what the numbers mean in context
5. **⚠️ WARN on significant CPU changes** - If `significant_change_detected = true` (cpu_change >= 40%), add a **warning row** in the summary table showing `CPU Change (Max - Min)` with ⚠️ **Significant** severity, even when no high CPU detected. This warns the customer about volatile CPU patterns.
6. **Note short duration spikes** - If high CPU detected but duration < 15 minutes, add the note about intermittent spikes
7. **Display recommended next steps when issue detected** - Show the recommendation table with available sub-skills for further investigation
8. **Use 🚩 emoji** - Flag High CPU severity (>= 80%) for visibility
9. **Use ⚠️ emoji** - Flag significant CPU change (>= 40%) for customer warning
10. **Use 🟢 emoji** - Indicate Normal severity when no issue detected

---

## Appendix B: Sub-Skill Descriptions (Reference Only)

> **Note**: This section describes the recommended sub-skills that can be executed for further investigation when high CPU is detected.

| Sub-Skill | Purpose |
|-----------|--------|
| CPU Discrepancy Analysis | Checks if CPU reported by MonResourcePoolStats matches QDS + Compile CPU. Helps identify hidden CPU consumers or telemetry gaps. |
| Query Execution CPU | Identifies top CPU-consuming queries from QDS |
| Successful Compilation | Checks if query compilation is consuming excessive CPU |
| Failed Compilation | Checks if failed compilations are contributing to CPU usage |