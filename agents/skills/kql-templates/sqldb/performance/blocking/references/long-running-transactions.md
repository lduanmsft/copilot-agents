
---
name: long-running-transactions
description: Analyze and debug long running transactions in Azure SQL Database
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Long Running Transactions

## Skill Overview

This skill analyzes long running transactions in Azure SQL Database by querying the MonDmTranActiveTransactions table. It identifies transactions with extended durations, categorizes them by type (tempdb, user_db, user_db_with_accessed_tempdb), and distinguishes between regular transactions and Azure DB System Tasks. The skill provides a summary message indicating the count of long running transactions, their maximum duration, and flags system tasks or negative session IDs for expert review.

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
MonDmTranActiveTransactions
| where {AppNamesNodeNamesWithPreciseTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and (user_db_name =~ '{LogicalDatabaseName}' or 4>= database_id)
| extend category = iff(user_db_name == 'tempdb', 'tempdb', iff(accessed_tempdb == 0, 'user_db', 'user_db_with_accessed_tempdb'))
| extend duration_hour = round((end_utc_date - transaction_begin_time) / time(1h),1)
| extend negativeSessionCount=0>session_id
| extend IsSystemTask=program_name in ('DmvCollector', 'TdService', 'BackupService', 'MetricsDownloader')
| summarize max_duration_hour = arg_max(duration_hour,
session_id,
transaction_begin_time,
transaction_type,
transaction_state,
IsSystemTask,
status,
accessed_tempdb,category,
report_time = end_utc_date)
by transaction_id,negativeSessionCount
| summarize count(),max(max_duration_hour),avg(max_duration_hour),percentile(max_duration_hour,50) by IsSystemTask,accessed_tempdb,negativeSessionCount
| summarize totalCount=sum(count_), negativeSessionCount=sumif(count_,negativeSessionCount==true),systemTaskSessionCount=sumif(count_,IsSystemTask==true),max_duration_hour=max(max_max_duration_hour),avg_duration_hour=round(avg(avg_max_duration_hour),1),median_duration_hour=round(avg(percentile_max_duration_hour_50),1)
| where totalCount>0
| project totalCount, max_duration_hour, avg_duration_hour, median_duration_hour, systemTaskSessionCount, negativeSessionCount
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If zero row is returned, display the exact message "Long running queries were not detected when MonDmTranActiveTransactions collection starts"
2. If one or more rows are returned, construct the message using the query result columns:
   - Base message: `"{totalCount} long running transaction were detected, with max duration {max_duration_hour} hours, avg duration {avg_duration_hour} hours, median duration {median_duration_hour} hours."`
   - If `negativeSessionCount > 0`, append: `" {systemTaskSessionCount} transaction were Azure DB System Tasks, please engage Experts; {negativeSessionCount} transaction had negative session IDs"`

#### Sample Output

##### Long Running Transaction Status

{longRunningMessage from query result}

| Metric | Value |
|--------|-------|
| Total Long Running Transactions | {totalCount} |
| Max Duration | {max_duration_hour} hours |
| Avg Duration | {avg_duration_hour} hours |
| Median Duration | {median_duration_hour} hours |
| System Task Sessions | {systemTaskSessionCount} |
| Negative Session IDs | {negativeSessionCount} |

#### Example Messages

**Scenario 1: Standard long running transactions detected**
```
5 long running transaction were detected, with max duration 2.5 hours, avg duration 1.2 hours, median duration 0.8 hours.
```

**Scenario 2: System tasks involved (requires expert engagement)**
```
8 long running transaction were detected, with max duration 4.2 hours, avg duration 2.1 hours, median duration 1.5 hours. 3 transaction were Azure DB System Tasks, please engage Experts; 1 transaction had negative session IDs
```

**Scenario 3: No long running transactions**
```
Long running queries were not detected when MonDmTranActiveTransactions collection starts
```

#### Output Guidelines

1. **System Tasks**: If `systemTaskSessionCount > 0` or `negativeSessionCount > 0`, highlight with 🚩 and recommend engaging experts.
2. **Duration Threshold**: Transactions with duration > 1 hour should be flagged for attention.
3. **Transaction Categories**: The query categorizes transactions as:
   - `tempdb` - Transactions in tempdb
   - `user_db` - User database transactions without tempdb access
   - `user_db_with_accessed_tempdb` - User database transactions that accessed tempdb
