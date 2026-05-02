---
name: cpu-usage-of-failed-compilation
description: The cpu usage of failed compilation;Analyze CPU usage from failed query compilations to identify if they are consuming significant CPU resources
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Failed Compilation CPU Analysis

## Skill Overview

This skill analyzes the CPU consumption from failed query compilations. It calculates the percentage of total CPU resources consumed by failed compilations and determines whether this represents a significant performance issue. If failed compilations consume 10% or more of total CPU, it indicates a potential problem that requires further investigation.

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
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event =~'failed_compilation'
| summarize compile_cpu_ms=sum(compile_cpu)
| project CPU_Percent = round(100.0 * (compile_cpu_ms/{SumCpuMillisecondOfAllApp}), 1)
| extend IssueDetected=CPU_Percent>=10
| extend ResultMessage = iff(IssueDetected == 'True', 
    strcat("Failed compilation consumed a significant amount of CPU resources, accounting for {CPU_Percent}%. Identifying high CPU usage from failed query compilations"),
    strcat("Failed compilation didn't consume a significant amount of CPU resources, with usage at {CPU_Percent}%"))
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the exact messager from "ResultMessage" column without any modification.

### Task 2: Execute Sub-Skills
1. If IssueDetected column is false, terminate this skill.
2. If IssueDetected column is true, execute the skill [Top Failed compilation ranked by CPU Usage](top-failed-compilations-by-cpu.md)
