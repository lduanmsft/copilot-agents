---
name: bufferpool-decrease
description: Check if MEMORYCLERK_SQLBUFFERPOOL had decreased and if the decrease is greater than or equal to 20%
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Buffer Pool Drop Skill

## Skill Overview

This skill provides a comprehensive workflow for detecting and analyzing significant decreases in the Azure SQL Database buffer pool, delivering suggestions to the user.

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
let AggInterval_do_NOT_change = time(5m);
let warningThreshold=20;
MonSqlMemoryClerkStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName=~'{LogicalServerName}'
| where memory_clerk_type =~'MEMORYCLERK_SQLBUFFERPOOL'
| summarize MemoryInMB=sum(pages_kb)/1024 by bin(originalEventTimestamp, AggInterval_do_NOT_change),process_id
| extend timestamp=format_datetime(originalEventTimestamp, 'yyyy-MM-dd HH:mm')
| project timestamp, MemoryInMB,process_id
| order by timestamp asc
| serialize
| extend prevMemoryInMB = prev(MemoryInMB),prevProcess_id=prev(process_id),prevTimestamp=prev(timestamp)
| project timestamp,prevTimestamp,MemoryInMB,prevMemoryInMB,dropInMB=prevMemoryInMB-MemoryInMB,prevProcess_id,process_id
| extend percentage=round(dropInMB*100.0/prevMemoryInMB,1)
| where dropInMB >0
| where percentage >=warningThreshold
| where prevProcess_id==process_id//filter out sql restart
| summarize count=count(),arg_max(dropInMB,percentage,prevMemoryInMB,prevTimestamp,MemoryInMB,timestamp)
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
 1. If the count is 0, then display "Buffer Pool was fine, significant drop was not detected.(Note: this skill doesn't account for memory drops caused by SQL Server restarts)"
 2. If count is greater than 0, then display "The Buffer Pool dropped significantly {{count}} times. The most notable drop occurred between {{prevTimestamp}} and {{timestamp}}, with a decrease of {{dropInMB}}MB —from {{prevMemoryInMB}}MB to {{MemoryInMB}}MB—a reduction of {{percentage}}%. (Note: this skill doesn't account for memory drops caused by SQL Server restarts)"
 3. Display message below, and replace the placeholder with proper value:

"Here is the kusto query used in this skill, please run it to verify if needed

```kql
let AggInterval_do_NOT_change = time(5m);
MonSqlMemoryClerkStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName=~'{LogicalServerName}'
| where memory_clerk_type =~'MEMORYCLERK_SQLBUFFERPOOL'
| summarize MemoryInMB=sum(pages_kb)/1024 by bin(originalEventTimestamp, AggInterval_do_NOT_change)
| order by originalEventTimestamp asc nulls first
| render timechart
```
 "