---
name: qds-setting-change
description: Analyze QDS setting changes; QDS Setting Change History; QDS Setting Changes
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug QDS Setting Change History

## Skill Overview

This skill retrieves and displays the history of Query Store (QDS) setting changes for an Azure SQL Database. It tracks changes to various QDS configuration parameters such as capture policy settings, flush intervals, max size, cleanup modes, and more. The skill shows when each setting was changed and what the old and new values were.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |



## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithPreciseTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
MonQueryStoreInfo
//Time Filter is not needed as we wanna display all change history.
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_changed'//event query_store_db_settings_changed is fired immediately when setting change occurres. Please note, query_store_db_settings_changed only display setting changes made in primary replica
| extend
Change = strcat
(
iff(capture_policy_execution_count_old != capture_policy_execution_count_new, strcat(', capture_policy_execution_count:', tostring(capture_policy_execution_count_old), '->', tostring(capture_policy_execution_count_new)), ''),
iff(capture_policy_mode_old != capture_policy_mode_new, strcat(', capture_policy_mode:', capture_policy_mode_old, '->', capture_policy_mode_new), ''),
iff(capture_policy_stale_threshold_hours_old != capture_policy_stale_threshold_hours_new, strcat(', capture_policy_stale_threshold_hours:', tostring(capture_policy_stale_threshold_hours_old), '->', tostring(capture_policy_stale_threshold_hours_new)), ''),
iff(capture_policy_total_compile_cpu_ms_old != capture_policy_total_compile_cpu_ms_new, strcat(', capture_policy_total_compile_cpu_ms:', tostring(capture_policy_total_compile_cpu_ms_old), '->', tostring(capture_policy_total_compile_cpu_ms_new)), ''),
iff(capture_policy_total_execution_cpu_ms_old != capture_policy_total_execution_cpu_ms_new, strcat(', capture_policy_total_execution_cpu_ms:', tostring(capture_policy_total_execution_cpu_ms_old), '->', tostring(capture_policy_total_execution_cpu_ms_new)), ''),
iff(fast_path_optimization_mode_old != fast_path_optimization_mode_new, strcat(', fast_path_optimization_mode:', fast_path_optimization_mode_old, '->', fast_path_optimization_mode_new), ''),
iff(flush_interval_seconds_old != flush_interval_seconds_new, strcat(', flush_interval_seconds:', flush_interval_seconds_old, '->', flush_interval_seconds_new), ''),
iff(interval_length_minutes_old != interval_length_minutes_new, strcat(', interval_length_minutes:', interval_length_minutes_old, '->', interval_length_minutes_new), ''),
iff(max_plans_per_query_old != max_plans_per_query_new, strcat(', max_plans_per_query:', max_plans_per_query_old, '->', max_plans_per_query_new), ''),
iff(max_size_mb_old != max_size_mb_new, strcat(', max_size_mb:', max_size_mb_old, '->', max_size_mb_new), ''),
iff(query_store_enabled_old != query_store_enabled_new, strcat(', query_store_enabled:', query_store_enabled_old, '->', query_store_enabled_new), ''),
iff(query_store_error_state_old != query_store_error_state_new, strcat(', query_store_error_state:', query_store_error_state_old, '->', query_store_error_state_new), ''),
iff(query_store_read_only_old != query_store_read_only_new, strcat(', query_store_read_only:', query_store_read_only_old, '->', query_store_read_only_new), ''),
iff(size_based_cleanup_mode_old != size_based_cleanup_mode_new, strcat(', size_based_cleanup_mode:', size_based_cleanup_mode_old, '->', size_based_cleanup_mode_new), ''),
iff(stale_query_threshold_days_old != stale_query_threshold_days_new, strcat(', stale_query_threshold_days:', stale_query_threshold_days_old, '->', stale_query_threshold_days_new), ''),
iff(wait_stats_capture_mode_old != wait_stats_capture_mode_new, strcat(', wait_stats_capture_mode:', wait_stats_capture_mode_old, '->', wait_stats_capture_mode_new), ''),
''
)
| extend Change=trim_start(',',Change)
| where isnotempty(Change)
| project PreciseTimeStamp,AppName,NodeName,Change
| order by PreciseTimeStamp
```

#### Output
1. Display the raw result

