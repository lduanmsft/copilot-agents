---
name: readonly-detection-singleton
description: Analyzes Query Store readonly issues and identifies root causes for QDS readonly events in Azure SQL Singleton database. 
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# QDS Readonly Issues Skill

## Skill Overview

This skill detects Query Store (QDS) readonly conditions in Azure SQL Database. Query Store may enter a readonly state when it encounters various resource limitations including:
- Statement hash map exceeding memory limit
- Buffered items exceeding memory limit  
- Total resource usage exceeding instance limit
- Disk size exceeding limit
- Database running out of disk space

This skill is intended to be invoked only by QDS Readonly Detection (../SKILL.md). If triggered by any other caller, it should not respond.

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
| Task 1 | Caller validation. | Always |
| Task 2 | Execute the Kusto query below | Always |
| Task 3 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Caller validation.

This skill is intended to be invoked exclusively by [QDS Readonly Detection](../SKILL.md). If invoked by any other caller, terminate execution in this marddown file, display the exact message "Calling parent skill instead" and execute [QDS Readonly Detection](../SKILL.md) instead.

### Task 2: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let ReadonlyMessage = (totalCount:int, dcount:int,readOnlyReasonArray:string)
{
case(
dcount==1 and totalCount==1,strcat("Query Store run into readonly one time due to readonly_reason:",readOnlyReasonArray),
strcat("Query Store run into readonly ",totalCount," times due to readonly_reason:",readOnlyReasonArray))
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~'{LogicalServerName}' and logical_database_name =~'{LogicalDatabaseName}'
| where event in ('query_store_resource_total_over_instance_limit','query_store_stmt_hash_map_over_memory_limit','query_store_buffered_items_over_memory_limit','query_store_disk_size_over_limit','query_store_database_out_of_disk_space')
| extend readOnlyReason=case(
event=~'query_store_disk_size_over_limit',"65536",
event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_StmtHashMapMemory',"131072",
event=~'query_store_stmt_hash_map_over_memory_limit',"131072",
event=~'query_store_buffered_items_over_memory_limit',"262144",
event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_BufferedItemsMemory',"262144",
event=~'query_store_database_out_of_disk_space',"524288",event
)
| summarize totalCount=count(),dcount_=dcount(readOnlyReason),readOnlyReasonArray=make_set(readOnlyReason)
| where totalCount>0
| extend readOnlyReasonArray=tostring(readOnlyReasonArray)
| extend readOnlyReasonArray=replace_string(readOnlyReasonArray,"[","")
| extend readOnlyReasonArray=replace_string(readOnlyReasonArray,"]","")
| extend readOnlyReasonArray=replace_string(readOnlyReasonArray,"\"","")
| extend Keywords=replace_string(readOnlyReasonArray,",",";")
| extend finalMessage=ReadonlyMessage(totalCount,dcount_,readOnlyReasonArray)
| project finalMessage,Keywords
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If the Task3 returns results, please display the exact message from the "finalMessage" column without any modifications.
2. If the Task3 doesn't return any result, it indicates Query Store didn't run into readonly. Please display the following sentence exactly as written:"Query Store didn't run into readonly between  {StartTime} and {EndTime}"


### Task 3: Execute Sub-Skills 
If QDS readonly is detected, display the following sentence exactly as written:"Because the QDS readonly issue was detected, we are going to perform additional checks:"
And execute the following sub‑skills, wether or not run depends on the value of variable "Keywords" got from "Task 1".

1. If the variable "Keywords" contains "65536", "131072" or "262144", execute the [QDS CaptureMode analysis] (readonly-capturemode-analysis.md)  to check the QDS Capture mode setting.
2. If the variable "Keywords" contains "65536", execute the skill [QDS Readonly 65536 Analysis] (readonly-65536.md) to dig into the 65535 detail.
3. If the variable "Keywords" contains "131072",  execute follow two skills:
    1) [QDS Readonly 131072 Analysis] (readonly-131072.md)  to dig into the 131072 detail.
    2) [Ratio of statementSqlHash to queryHash analysis] (readonly-rca-statementsqlhash-singleton.md).
    3) [QDS Related Memory] (qds-memory.md).
4. If the variable "Keywords" contains "262144",   execute follow two skills:
    1) [QDS Readonly 262144 Analysis](readonly-262144.md)
    2) [Ratio of statementSqlHash to queryHash analysis] (readonly-rca-statementsqlhash-singleton.md).
    3) [QDS Related Memory] (qds-memory.md).

If not detected, please do not display anything for this section
