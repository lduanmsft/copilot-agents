---
name: drive-out-of-space
description: Analyzes drive out of space usage in azure DB.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Drive Out Of Space

## Skill Overview

This skill analyzes disk drive usage on Azure SQL nodes to detect out-of-disk issues. It checks if drives have reached alert thresholds (96%) or near-full conditions (99%), and provides detailed information about disk space usage patterns.

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
| Task 1 | Caller Validation | Always |
| Task 2 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Caller Validation

This skill is intended to be invoked exclusively by [Space Issue Analysis](../SKILL.md). If invoked by any other caller (e.g., directly by a user), terminate execution in this markdown file, display the exact message "Calling parent skill instead" and execute [Space Issue Analysis](../SKILL.md) instead.

### Task 2: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
MonRgLoad
| extend originalEventTimestamp = originalEventTimestampFrom
| extend AppName = tostring(split(application_name, '/')[-1])
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where event == 'directory_quota_report_load' and target_directory endswith 'work\\data'
| extend drive_name = substring(target_directory, 4, 3)
| summarize by drive_name,ClusterName, application_name, NodeName, target_directory, event
| join kind = inner (
                      MonRgLoad
                      | extend originalEventTimestamp = originalEventTimestampFrom
                      | where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
                      | where event == 'drive_usage_report_load' and drive_name != '' and drive_capacity_in_bytes > 0
                      | where ClusterName in ({HistoricalTenantRingNames}) and NodeName in ({NodeNames})
                      | summarize arg_max(round(drive_usage_percentage, 1), originalEventTimestampFrom) by ClusterName, NodeName, drive_name, drive_capacity_in_gb = toint(drive_capacity_in_bytes / 1024.0 / 1024 / 1024), drive_usage_alert_threshold_percentage
 ) on ClusterName, NodeName, drive_name
| project originalEventTimestampFrom, NodeName, drive_name, drive_capacity_in_gb, drive_usage_percentage, drive_available_space_gb = toint(drive_capacity_in_gb*(100-drive_usage_percentage)/100.0), drive_usage_alert_threshold_percentage, target_directory, application_name, ClusterName
| extend IssueDetected=drive_usage_percentage>=96
```

#### Output

**Step 1: Display Issue Status**

| Condition | Message |
|-----------|---------|
| `IssueDetected = true` (any row has usage ≥ 96%) | 🚩 **Drive Out of Disk issue has been detected** |
| `IssueDetected = false` (all rows have usage < 96%) | ✅ **Drive out of disk issue has not been detected. Usage is below the 96% alert threshold.** |

**Step 2: Display Drive Usage Summary Table**

| Column | Description |
|--------|-------------|
| `originalEventTimestampFrom` | Timestamp of the measurement |
| `NodeName` | Azure SQL node name |
| `drive_name` | Drive letter (e.g., S:\, D:\) |
| `drive_capacity_in_gb` | Total drive capacity in GB |
| `drive_usage_percentage` | Current usage percentage |
| `drive_available_space_gb` | Available space in GB |
| `drive_usage_alert_threshold_percentage` | Alert threshold (typically 96%) |
| `IssueDetected` | true if usage ≥ 96%, false otherwise |


