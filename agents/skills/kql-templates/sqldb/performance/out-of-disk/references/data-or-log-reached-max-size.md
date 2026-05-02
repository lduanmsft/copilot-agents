---
name: data-or-log-reached-max-size
description: Data or Log reached max size.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Data or Log Reached Max Size

## Skill Overview

This skill determines if user database or tempdb data/log files have reached their maximum configured size on Azure SQL nodes. It analyzes the size on disk versus max size limits to detect when files have exhausted their allocated space.

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

**This skill has 4 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Caller Validation | Always |
| Task 2 | Execute the Kusto query below | Always |
| Task 3 | Check File Size Details (Conditional) | Conditional |
| Task 4 | Identify Log Full Cause (Conditional) | Conditional |

## Execution Steps

### Task 1: Caller Validation

This skill is intended to be invoked exclusively by [out-of-disk](../SKILL.md). If invoked by any other caller (e.g., directly by a user), terminate execution in this markdown file, display the exact message "Calling parent skill instead" and execute [out-of-disk](../SKILL.md) instead.

### Task 2: Execute the Kusto query below. If required variables (e.g., `{AppNamesOnly}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
MonSqlRgHistory
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~'{LogicalServerName}' 
| where event =~ 'aggregated_virtual_files_io_history'
| where (type_desc =~ 'ROWS' or type_desc =~ 'LOG')
| where (database_id > 4 and database_id < 32700) or database_id == 2
| extend size_on_disk_GB = round(size_on_disk_bytes / 1024.0 / 1024 / 1024, 0),
         max_size_GB = round(max_size_mb / 1024.0, 0)
| summarize max(max_size_GB), max(size_on_disk_GB) by type_desc, file_id, database_id,db_name//There are cases where a phantom database name with a very large max size shares the same DBID as a smaller database. We need to prevent this by including the database name in the validation logic.
| extend MaxSizeHit = iff(max_size_on_disk_GB >= max_max_size_GB, 1, 0)
| summarize MaxSizeHit = avg(MaxSizeHit) by database_id, type_desc
| summarize maxif(MaxSizeHit, database_id != 2 and type_desc =~ 'ROWS'),
            maxif(MaxSizeHit, database_id != 2 and type_desc =~ 'LOG'),
            maxif(MaxSizeHit, database_id == 2 and type_desc =~ 'ROWS'),
            maxif(MaxSizeHit, database_id == 2 and type_desc =~ 'LOG')
| extend UserdbDataMaxSizeHit = maxif_MaxSizeHit == 1,
         UserdbLogMaxSizeHit = maxif_MaxSizeHit1 == 1,
         TempdbDataMaxSizeHit = maxif_MaxSizeHit2 == 1,
         TempdbLogMaxSizeHit = maxif_MaxSizeHit3 == 1
| project UserdbDataMaxSizeHit, UserdbLogMaxSizeHit, TempdbDataMaxSizeHit, TempdbLogMaxSizeHit
```

#### Output

**Display Issue Status**

| Column | Condition | Message |
|--------|-----------|---------|
| `UserdbDataMaxSizeHit` | `true` | 🚩 **User database data file has reached max size** - The data file has exhausted its configured maximum size limit. |
| `UserdbDataMaxSizeHit` | `false` | ✅ **User database data file has not reached max size** |
| `UserdbLogMaxSizeHit` | `true` | 🚩 **User database log file has reached max size** - The transaction log file has exhausted its configured maximum size limit. |
| `UserdbLogMaxSizeHit` | `false` | ✅ **User database log file has not reached max size** |
| `TempdbDataMaxSizeHit` | `true` | 🚩 **Tempdb data file has reached max size** - The tempdb data file has exhausted its configured maximum size limit. |
| `TempdbDataMaxSizeHit` | `false` | ✅ **Tempdb data file has not reached max size** |
| `TempdbLogMaxSizeHit` | `true` | 🚩 **Tempdb log file has reached max size** - The tempdb transaction log file has exhausted its configured maximum size limit. |
| `TempdbLogMaxSizeHit` | `false` | ✅ **Tempdb log file has not reached max size** |

**Summary Table Format**

| File Type | Max Size Hit |
|-----------|--------------|
| User DB Data | {UserdbDataMaxSizeHit} |
| User DB Log | {UserdbLogMaxSizeHit} |
| Tempdb Data | {TempdbDataMaxSizeHit} |
| Tempdb Log | {TempdbLogMaxSizeHit} |

### Task 3: Check File Size Details (Conditional)

**Condition**: Execute this task ONLY when any of `UserdbDataMaxSizeHit`, `UserdbLogMaxSizeHit`, `TempdbDataMaxSizeHit`, or `TempdbLogMaxSizeHit` is `true`

Run the following Kusto query to get detailed file size information:

```kql
let AggInterval_do_NOT_change = time(15m);
MonSqlRgHistory
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where event == 'aggregated_virtual_files_io_history'
| where LogicalServerName =~ '{LogicalServerName}' and db_name =~ '{LogicalDatabaseName}'
| summarize file_space_used_gb = round(sum(spaceused_mb / 1024.0), 1),//actual space used
            file_space_reserved_gb = round(sum(size_on_disk_bytes / 1024.0 / 1024.0 / 1024.0), 1),//actual file size on the disk
            maximum_gb = sum(max_size_mb / 1024.0)
   by type_desc, bin(originalEventTimestamp, AggInterval_do_NOT_change)
| summarize max(file_space_used_gb), max(file_space_reserved_gb) by maximum_gb, type_desc
| where max_file_space_reserved_gb>=maximum_gb and max_file_space_used_gb>=maximum_gb
| project type_desc, maximum_gb, max_file_space_reserved_gb, max_file_space_used_gb
```

#### Output

**Display File Size Summary**

| Column | Description |
|--------|-------------|
| `type_desc` | File type (ROWS for data file, LOG for transaction log) |
| `maximum_gb` | Maximum file size limit in GB |
| `max_file_space_reserved_gb` | Maximum file size on disk (reserved space) in GB |
| `max_file_space_used_gb` | Maximum actual space used in GB |

#### Sub-Task 3.1: Compare with SLO Maximum Size

**Action**: Search the following online articles to determine the maximum supported size for the corresponding Service Level Objective (SLO) and edition:

- [vCore single databases](https://learn.microsoft.com/en-us/azure/azure-sql/database/resource-limits-vcore-single-databases?view=azuresql)
- [DTU single databases](https://learn.microsoft.com/en-us/azure/azure-sql/database/resource-limits-dtu-single-databases?view=azuresql)


**Comparison Logic**:

1. Identify the database's SLO/service tier from the database environment information
2. Look up the maximum data size and log size for that SLO in the appropriate article
3. Compare the `maximum_gb` value from Kusto with the documented maximum size

**Output**:

If the actual maximum size (from Kusto) is **lower** than the maximum documented in the articles, display:

> ⚠️ **Warning: The maximum is lower than the maximum of the SLO.**
>
> | Metric | Actual (from Kusto) | Documented Maximum (from Article) |
> |--------|---------------------|-----------------------------------|
> | Data File Max Size | {actual_data_max_gb} GB | {documented_data_max_gb} GB |
> | Log File Max Size | {actual_log_max_gb} GB | {documented_log_max_gb} GB |

If the actual maximum size equals the documented maximum, display:

> ✅ **The database is configured with the maximum size supported by the SLO.**

### Task 4: Identify Log Full Cause (Conditional)

**Condition**: Execute this task ONLY when `UserdbLogMaxSizeHit = true` OR `TempdbLogMaxSizeHit = true`

If the log file is full, run the following Kusto query to identify the cause of log full:

```kql
MonFabricThrottle
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where log_truncation_holdup !~ 'NoHoldup'
| summarize count(), min(TIMESTAMP), max(TIMESTAMP) by log_truncation_holdup, NodeName, ClusterName
```

#### Output

**Display Log Truncation Holdup Analysis**

| Column | Description |
|--------|-------------|
| `log_truncation_holdup` | The reason preventing log truncation (e.g., ACTIVE_TRANSACTION, REPLICATION, LOG_BACKUP, etc.) |
| `count_` | Number of occurrences |
| `min_TIMESTAMP` | First occurrence time |
| `max_TIMESTAMP` | Last occurrence time |
| `NodeName` | Azure SQL node name |
| `ClusterName` | Azure SQL cluster name |

**Common log_truncation_holdup values and their meanings:**

| Value | Description |
|-------|-------------|
| `ACTIVE_TRANSACTION` | A long-running transaction is preventing log truncation |
| `LOG_BACKUP` | Log backup is pending or in progress |
| `REPLICATION` | Replication is lagging behind |
| `DATABASE_MIRRORING` | Database mirroring/AG synchronization is pending |
| `CHECKPOINT` | Checkpoint has not occurred |
| `OLDEST_PAGE` | The oldest dirty page has not been flushed |

