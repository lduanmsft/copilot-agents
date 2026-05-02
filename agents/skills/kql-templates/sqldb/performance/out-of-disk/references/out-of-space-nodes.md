---
name: out-of-space-nodes
description: Analyzes space related allocation failures recorded in SQL errorlog
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Has out of space issue

## Skill Overview

This skill returns space related allocation failures recorded in SQL errorlog. These errors are caused by:
- Hitting max size of user DB or tempdb (data or tlog)
- Directory out of space (work/data where system db such as tempdb and data/log of user DB which are using local storage - Premium or BusinessCritical)
- Drive out of space

### Error Codes Detected

| Error Code | Description |
|------------|-------------|
| **Error 3257** | Insufficient free space in filegroup |
| **Error 9002** | Transaction log full |
| **Error 5149** | File I/O error - insufficient disk space |
| **Error 1105** | Could not allocate space for object |
| **Error 1101** | Could not allocate a new page for database |

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

This skill is intended to be invoked exclusively by [out-of-disk](../SKILL.md). If invoked by any other caller (e.g., directly by a user), terminate execution in this markdown file, display the exact message "Calling parent skill instead" and execute [out-of-disk](../SKILL.md) instead.

### Task 2: Execute the Kusto query below. If required variables (e.g., `{AppNamesOnly}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
MonSQLSystemHealth
| where PreciseTimeStamp between ((datetime({StartTime}) - 12h) .. datetime({EndTime}))
| where AppName in {AppNamesOnly}
| where event in ('errorlog_written', 'systemmetadata_written') and (message contains 'Error: 3257' or message contains 'Error: 9002' or message contains 'Error: 5149' or message contains 'Error: 1105' or message contains 'Error: 1101')
| extend required_space = extract('requires ([0-9]+)', 1, message, typeof(real)) / 1024 / 1024 / 1024
| extend available_space = extract('only ([0-9]+)', 1, message, typeof(real)) / 1024 / 1024 / 1024
| extend errorMessage=substring(message,124,strlen(message))
| summarize StartTime = min(PreciseTimeStamp),(LastSeenTime, RequiredSpaceGB, AvailableSpaceGB) = arg_max(PreciseTimeStamp, required_space, available_space, errorMessage, error_id) by AppName, ClusterName, NodeName
| project AppName, NodeName, AvailableSpaceGB, RequiredSpaceGB, LastSeenTime, errorMessage, ErrorId=error_id, ClusterName, StartTime, sourceName = 'MonSQLSystemHealth aka Errorlog'
| top 10 by LastSeenTime desc
```

#### Output

**Step 1: Display Issue Status**

| Condition | Message |
|-----------|---------|
| Query returns rows | 🚩 **Out of space allocation failures detected in SQL errorlog** |
| Query returns no rows | ✅ **No out of space allocation failures detected in SQL errorlog** |

**Step 2: Display Out of Space Events Table**

| Column | Description |
|--------|-------------|
| `AppName` | SQL instance/application name |
| `NodeName` | Azure SQL node name |
| `AvailableSpaceGB` | Available space in GB at time of error |
| `RequiredSpaceGB` | Required space in GB that could not be allocated |
| `LastSeenTime` | Most recent occurrence of the error |
| `StartTime` | First occurrence of the error |
| `errorMessage` | Error message from SQL errorlog |
| `ErrorId` | SQL error ID code |
| `ClusterName` | Azure SQL cluster name |
| `sourceName` | Data source (MonSQLSystemHealth aka Errorlog) |
