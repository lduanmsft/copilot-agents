---
name: readonly-detection-ep
description: Analyzes Query Store readonly issues and identifies root causes for QDS readonly events in Azure SQL Elastic Pool. 
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug QDS Readonly Root Cause Analysis

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
let FiterReadOnlyReasonArray=(ReadOnlyReasonArray:string)
{
let ReadOnlyReasonArray_result= replace_string(
replace_string(
replace_string(ReadOnlyReasonArray, "[", ""),
"]", ""),
"\"", "");
ReadOnlyReasonArray_result
};
let ReadonlyMessage = (totalReadonlyCount:int, currentDB_ReadonlyCount:int,otherDBs_ReadonlyCount:int,otherDBs_Dcount:int,
currentDB_ReadOnlyReasonArray:string,otherDBs_ReadOnlyReasonArray:string,logical_database_name:string)
{
case(
totalReadonlyCount==currentDB_ReadonlyCount,
strcat("Query Store of database [",logical_database_name,"] run into readonly ",currentDB_ReadonlyCount,iff(currentDB_ReadonlyCount==1," time", " times")," due to readonly_reason:",currentDB_ReadOnlyReasonArray,". Please note, this is the only database having QDS Readonly issue in the entire ElasticPool"),
currentDB_ReadonlyCount==0,strcat("Query Store of database [",logical_database_name,"] didn't run into readonly. At the ElasticPool level, ",otherDBs_Dcount," databases ran into QDS readonly issue ",otherDBs_ReadonlyCount,iff(totalReadonlyCount==1," time"," times")," due to readonly_reason:",otherDBs_ReadOnlyReasonArray,". Please note that we will not proceed with further QDS read-only analysis at this time. To continue, please specify a database had the QDS read-only issue and try again."),
strcat("Query Store of database [",logical_database_name,"] run into readonly ",currentDB_ReadonlyCount,iff(currentDB_ReadonlyCount==1," time", " times")," due to readonly_reason:",currentDB_ReadOnlyReasonArray,". At the ElasticPool level, other ",otherDBs_Dcount," databases run into QDS readonly issue ",otherDBs_ReadonlyCount,iff(otherDBs_ReadonlyCount==1," time"," times")," due to readonly_reason:",otherDBs_ReadOnlyReasonArray,".")
)
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event in ('query_store_resource_total_over_instance_limit','query_store_stmt_hash_map_over_memory_limit','query_store_buffered_items_over_memory_limit','query_store_disk_size_over_limit','query_store_database_out_of_disk_space')
| extend readOnlyReason=case(
event=~'query_store_disk_size_over_limit',"65536",
event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_StmtHashMapMemory',"131072",
event=~'query_store_stmt_hash_map_over_memory_limit',"131072",
event=~'query_store_buffered_items_over_memory_limit',"262144",
event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_BufferedItemsMemory',"262144",
event=~'query_store_database_out_of_disk_space',"524288",event
)
|summarize totalReadonlyCount=count(),currentDB_ReadonlyCount=countif(logical_database_name =~'{LogicalDatabaseName}'),otherDBs_ReadonlyCount=countif(logical_database_name !~'{LogicalDatabaseName}'),
otherDBs_Dcount=dcountif(logical_database_name,logical_database_name !~'{LogicalDatabaseName}'),
currentDB_ReadOnlyReasonArray=make_set_if(readOnlyReason,logical_database_name =~'{LogicalDatabaseName}'),otherDBs_ReadOnlyReasonArray=make_set_if(readOnlyReason,logical_database_name !~'{LogicalDatabaseName}')
| where totalReadonlyCount>0
| extend currentDB_ReadOnlyReasonArray=FiterReadOnlyReasonArray(currentDB_ReadOnlyReasonArray)
| extend otherDBs_ReadOnlyReasonArray=FiterReadOnlyReasonArray(otherDBs_ReadOnlyReasonArray)
| extend Keywords=replace_string(currentDB_ReadOnlyReasonArray,",",";")
| extend readonlyMessage=ReadonlyMessage(totalReadonlyCount,currentDB_ReadonlyCount,otherDBs_ReadonlyCount,otherDBs_Dcount,currentDB_ReadOnlyReasonArray,otherDBs_ReadOnlyReasonArray,'{LogicalDatabaseName}')
| project readonlyMessage,Keywords
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