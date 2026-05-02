---
name: cpu-usage-of-successful-compilation
description: CPU Usage of successful compilation;Analyze CPU usage from successful query compilations and recompilations to identify if compilation activities are contributing to high CPU consumption
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Successful compilation CPU Analysis

## Skill Overview

This skill analyzes the CPU consumption from successful query compilations and recompilations. It determines whether compilation activities are consuming a significant percentage of the total CPU resources. If successful compilations account for 10% or more of CPU usage, the skill identifies this as a potential performance issue and triggers further investigation into the top queries by compilation CPU.

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

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

MonWiQueryParamData
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend compile_code=iff(compile_code =='Success','Compilation','Recompile')
| summarize compile_cpu_time_ms=sum(compile_cpu_time+auto_update_stats_cpu_time)/1000
| project CPU_Percent = round(100.0 * (compile_cpu_time_ms/{SumCpuMillisecondOfAllApp}), 1)
| extend IssueDetected = CPU_Percent >= 10
| extend ResultMessage = iff(IssueDetected == 'True', 
    strcat("Successful compilation consumed a significant amount of CPU resources, accounting for ", CPU_Percent, "%. Identifying high CPU usage from query compilations."),
    strcat("Successful compilation did not consume a significant amount of CPU resources, with usage at ", CPU_Percent, "%"))

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
Analyze the CPU_Percent value returned from the query:
1. Display the exact value from "ResultMessage" column without any modification.
2. If no data is returned, display: "As issue is detected, we are going to do further checks"

