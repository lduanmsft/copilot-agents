---
name: qds-sizebased-cleanupjob-disable-detection
description: Analyze QDS SizeBased cleanup mode settings to detect if cleanup is disabled, which may cause Query Store to run into readonly state.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug QDS SizeBased Cleanup Disabled Analysis

## Skill Overview

This skill analyzes Query Data Store (QDS) size-based cleanup mode settings. When size_based_cleanup_mode is set to off, the size-based cleanup background job doesn't run, which may cause QDS to run into readonly state with error 65536.

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

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithPreciseTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let SizeBasedCleanupModeMessage= (size_based_cleanup_mode_Disabled_Count:int,size_based_cleanup_mode_Disabled_Change_Count:int)
{
"QDS size_based_cleanup_mode was set to off. Please note, the size-based cleanup backgroub job doesn't run when the mode is off, which may cause QDS run into readonly with readonly issue 65536."
};
let setting1=(MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_and_state'
| where size_based_cleanup_mode =~ 'x_qdsSizeBasedCleanupModeMin'
| summarize size_based_cleanup_mode_Disabled_Count=count()
| extend joinColumn=1);
let setting2=(MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_changed'
| summarize
size_based_cleanup_mode_Disabled_Change_Count=countif(size_based_cleanup_mode_old=~ 'x_qdsSizeBasedCleanupModeMin' or size_based_cleanup_mode_new =~ 'x_qdsSizeBasedCleanupModeMin')
|extend joinColumn=1);
setting1
| join kind=inner (setting2) on joinColumn
| where size_based_cleanup_mode_Disabled_Count+size_based_cleanup_mode_Disabled_Change_Count>0
| extend sizeBasedCleanupModeMessage=SizeBasedCleanupModeMessage(CaptureModeAllCount,size_based_cleanup_mode_Disabled_Change_Count)
| project sizeBasedCleanupModeMessage
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If no row returned, please display "QDS SizeBased cleanup Mode was auto(enabled), we don't find obvious issue.",
else display the exact message from the `sizeBasedCleanupModeMessage` column without any modifications.

