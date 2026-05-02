---
name: non-yielding
description: Detect and analyze non-yielding scheduler issues that may cause query slowness, system task failures, and worker thread exhaustion.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Non-yielding Scheduler

## Skill Overview

This skill detects non-yielding scheduler events in Azure SQL Database. Non-yielding schedulers can lead to various performance issues, including but not limited to query slowness, system task failure, Azure DB hanging, and worker thread exhaustion.

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
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | If non-yielding was detected, execute the following query to get detailed cal... | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
MonSqlRmRingBuffer
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event =~'nonyield_copiedstack_ring_buffer_recorded'
| summarize Totalcount=count()
| where Totalcount > 0
| extend nonYieldingMessage=strcat("Non-yielding scheduler happened ", PluralOrSingular(Totalcount,"time")," This may lead to various performance issues, including but not limited to query slowness, system task failure, Azure DB hanging, and worker thread exhaustion. Please review the callstack to investigate.")
| project nonYieldingMessage
```

#### Output
Follow these instructions exactly. Only display output when specified:

1. Display the exact message from `nonYieldingMessage` without any modification

2. **If the query returns empty results**: 
   - Display the following message exactly as written:
   - "Non-yielding was not detected."

### Task 2: If non-yielding was detected, execute the following query to get detailed callstack information

```kql
MonSqlRmRingBuffer
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event =~'nonyield_copiedstack_ring_buffer_recorded'
| summarize count(), StartTime=arg_min(originalEventTimestamp,dispatcher_pool_name,user_mode_time,kernel_mode_time,
scheduler_id,thread_id,system_thread_id,session_id,
worker,task,request_id,nonyield_type,worker_wait_stats),EndTime=max(originalEventTimestamp) by stack_frames
| extend duration_minutes=datetime_diff('minute',EndTime,StartTime)
| project-reorder count_,stack_frames,StartTime,EndTime,duration_minutes
| order by StartTime asc
```

#### Output
Display the callstack details to help investigate the root cause of the non-yielding scheduler issue.


