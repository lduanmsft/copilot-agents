---
name: qds-current-setting
description: Retrieve and analyze Query Data Store (QDS) current settings to identify potential configuration issues.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug QDS Current Settings

## Skill Overview

This skill retrieves the current Query Data Store (QDS) settings for an Azure SQL Database and analyzes the capture policy configuration. It helps identify if the capture mode is set to 'Full' instead of 'Auto' or other not recommended settings, which can cause Query Store to enter read-only mode due to size limitations. 

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

```kql
let CapturePolicyStatus = (capture_policy_mode: string,capture_policy_execution_count:int,capture_policy_total_compile_cpu_ms:int,capture_policy_total_execution_cpu_ms:int)
{
let recommendatoin="Suggest switching to Auto mode. Current setting is not recommended because it persists all queries into Query Store and is likely to cause Query Store to enter read-only mode due to one of the following reasons: 65536, 131072, 262144.";
case(
capture_policy_mode =~'x_qdsCaptureModeAll' ,strcat("CaptureMode is set to 'Full' instead of 'Auto'. ",recommendatoin),
capture_policy_execution_count<30 or capture_policy_total_compile_cpu_ms<1000 or capture_policy_total_execution_cpu_ms<100,strcat("The capture_policy_setting allows more queries to be persisted ",recommendatoin),"We don't find obvious issue."
  )
  //Sample output1:CaptureMode is set to 'Full' instead of 'Auto'. Suggest switching to Auto mode. Current setting is not recommended because it persists all queries into Query Store and is likely to cause Query Store to enter read-only mode due to one of the following reasons: 65536, 131072, 262144.
  //Sample output2:The capture_policy_setting allows more queries to be persisted. Suggest switching to Auto mode. Current setting is not recommended because it persists all queries into Query Store and is likely to cause Query Store to enter read-only mode due to one of the following reasons: 65536, 131072, 262144.
  };
  MonQueryStoreInfo
  | where {AppNamesNodeNamesWithOriginalEventTimeRange}
  | where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
  | where event == 'query_store_db_settings_and_state'////event query_store_db_diagnostics happens every 60 mins.
  | extend ActualState = case (db_state_actual == 0, 'Off', db_state_actual == 1, 'ReadOnly', db_state_actual == 2, 'ReadWrite', db_state_actual == 3, 'Error', db_state_desired == 4, 'READ_CAPTURE_SECONDARY','Other')
  | extend DesiredState = case (db_state_desired == 0, 'Off', db_state_desired == 1, 'ReadOnly', db_state_desired == 2, 'ReadWrite', db_state_desired == 3, 'Error', db_state_desired == 4, 'READ_CAPTURE_SECONDARY','Other')
  |top 1  by  PreciseTimeStamp desc
  | extend capturePolicyStatus=CapturePolicyStatus(capture_policy_mode,capture_policy_execution_count,capture_policy_total_compile_cpu_ms,capture_policy_total_execution_cpu_ms)
  |project capturePolicyStatus
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the exact message from the `capturePolicyStatus` column without any modifications.
2. Display the raw result.

