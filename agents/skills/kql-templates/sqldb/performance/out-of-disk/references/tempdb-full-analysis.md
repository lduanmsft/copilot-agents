---
name: tempdb-full-analysis
description: Analyze Tempdb database file and log file full conditions for Azure SQL Database
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Tempdb Full Analysis

## Skill Overview

This skill analyzes Tempdb full conditions by checking for allocation errors (1101, 1104, 1105, 5149) and examining Tempdb file and log space usage. It determines whether Tempdb data files or log files have reached their maximum size limits during the investigation time window.

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
| Task 1 | Caller Validation | Always |
| Task 2 | Execute the Kusto query below | Always |
| Task 3 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Caller Validation

This skill is intended to be invoked exclusively by [out-of-disk](../SKILL.md). If invoked by any other caller (e.g., directly by a user), terminate execution in this markdown file, display the exact message "Calling parent skill instead" and execute [out-of-disk](../SKILL.md) instead.

### Task 2: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let AllocationErrorCount=toscalar( MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where error_id in (1101,1104,1105,5149)
| count
);
let AggInterval_do_NOT_change = time(15m);
let TempdbFileFullResult = MonSqlRgHistory
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event=='aggregated_virtual_files_io_history'
| where database_id == 2
| where type_desc =~'ROWS'
| where AllocationErrorCount>0
| summarize
spaceused_gb = round(sum(spaceused_mb / 1024.0),1),//Actual space used.
size_on_disk_gb = round(sum(size_on_disk_bytes / 1024.0 / 1024.0 / 1024.0),1),//Actual file size on the disk.
max_size_gb=round(sum(max_size_mb/1024.0),1)//the maximum size to which files can grow.
by  type_desc, bin(originalEventTimestamp, AggInterval_do_NOT_change)
| project originalEventTimestamp,file_type=type_desc,spaceused_gb,size_on_disk_gb,max_size_gb
| where size_on_disk_gb==max_size_gb
| extend Timestamp=originalEventTimestamp
| summarize Timestamp=max(Timestamp),countTempdbFileFull=count();
TempdbFileFullResult
| extend IssueDetected = countTempdbFileFull > 0
| extend ResultMessage = iff(countTempdbFileFull > 0, 
    strcat("Tempdb database file was full, with first occurrence around ", format_datetime(Timestamp, 'yyyy-MM-dd HH:mm'), "."),
    "Tempdb is not full.")
| project Timestamp, countTempdbFileFull, IssueDetected, ResultMessage
```

#### Output

Follow these instructions exactly:

1.  Display the exact value from the `ResultMessage` column without any modification


### Task 3: Execute Sub-Skills

**Condition**: Execute the following sub-skills when `{IssueDetected}` is `true`

- Execute the skill [tempdb file size](tempdb-file-size.md)
- Execute the skill [Tempdb Space Usage](tempdb-space-usage.md)
