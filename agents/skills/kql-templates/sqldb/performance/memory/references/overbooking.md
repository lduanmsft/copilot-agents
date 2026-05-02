---
name: overbooking
description: Debug Memory Overbooking issue for Azure DB;Debug DRG issue for Azure DB;Debug MRG issue for Azure DB.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Memory Overbooking Issues Skill

## Skill Overview

This skill provides a comprehensive workflow for debugging Azure SQL Database memory overbooking issues and delivers actionable suggestions. Even if overbooking is not detected, other memory-related issues may still exist.

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
| Task 1 | MRG Detection | Always |
| Task 2 | DRG Detection | Always |


## Execution Steps

### Task 1: MRG Detection

 If required variables (e.g., `{NodeNamesWithOriginalEventTimeRange}`, `{AppNamesOnly}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

MonRgManager
| where {NodeNamesWithOriginalEventTimeRange}
| where event == 'multi_instance_mem_rg_recliam_target'
| where multi_instance_mem_rg_instance_name has_any ({AppNamesOnly})
| summarize count=count()

#### Output
 If the count is 0, then display "No MRG is detected from {StartTime} and {EndTime}"
 If count is greater than 0, then display "MRG is detected {count} times from {StartTime} and {EndTime}; This is Node level memory pressure cause. This may impact overall performance. Please note that MRG is designed to mitigate node-level memory pressure and its activation is expected behavior under such conditions. Do not file an ICM for this."
 
### Task 2: DRG Detection

 MonRgManager
 | where {NodeNamesWithOriginalEventTimeRange}
 | where event == 'dynamic_rg_cap_change' and resource=='MEMORY'
 | extend AppName = extract(@"/([^/]+)/\(Code,SQL\)", 1, instance_name)
 | where AppName has_any ({AppNamesOnly})
 | summarize count=count()

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
 1. If the count is 0, then display "No Dynamic RG is detected from {StartTime} and {EndTime}".
 2. If count is greater than 0, then display "DRG is detected {count} times from {StartTime} and {EndTime};This is Node level memory pressure(Overbooking), and the overall performance may be impacted, including but not limited to query slowness, login outage, drastic memory cap change, database failover. Please engage Sql Server RG team for RCA"



