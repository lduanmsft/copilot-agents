---
name: readonly-65536
description: did qds 65536 happen;did qds run into 65536; did qds run into readonly due to 65536;Analyzes QDS Readonly events caused by query_store_disk_size_over_limit (ReadonlyReason 65536 - Max QDS Size reached).
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# QDS Readonly 65536 Analysis 

## Skill Overview

This skill analyzes Query Data Store (QDS) Readonly events triggered by ReadonlyReason 65536, which indicates the maximum QDS disk size limit has been reached. When QDS storage exceeds its configured `max_storage_size_mb`, QDS enters read-only mode to prevent further data collection. The analysis identifies the frequency and timing of these events and provides mitigation recommendations based on the current QDS size configuration.

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
| Task 2 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithPreciseTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let ReadonlyMessage = (totalCount:int,max_size_mb:long,dcount_max_size_mb: int,startTime:string,endTime:string)
{
let optionMessage=case(10240>max_size_mb,strcat("(The max size limit is 10240 MB, you have ",10240-max_size_mb," MB to increase)"),
max_size_mb==10240,strcat("(This is not an option, as the max_storage_size_mb of QDS is already set to 10240 MB, which is the maximum limit.)"),
strcat("(This is not an option, as the max_storage_size_mb of QDS is already set to ",max_size_mb," MB, which is already greater than the 10GB limit.)")
);
let percentOfLimit=max_size_mb*100.0/10240;
let mitigationMessage=case(50>=percentOfLimit,strcat("The mitigation includes the following actions:1. Increasing max_storage_size_mb of QDS;",optionMessage," 2. Implementing query parameterization;3. Decreasing stale_query_threshold_days;4. Removing specific entries in QDS."),
90>=percentOfLimit,strcat("The mitigation includes the following actions:1. Implementing query parameterization;2. Increasing max_storage_size_mb of QDS;",optionMessage,"3. Decreasing stale_query_threshold_days;4. Removing specific entries in QDS."),
strcat("The mitigation includes the following actions:1. Implementing query parameterization;2. Decreasing stale_query_threshold_days;3. Removing specific entries in QDS.4. Increasing max_storage_size_mb of QDS;",optionMessage));
let maxSizeMessage=case(dcount_max_size_mb ==1,strcat("The max size of QDS setting was ",max_size_mb," megabyte. "),
strcat("The max size of QDS setting was ",max_size_mb," megabyte. Please note, the Max Size Setting was adjusted ",dcount_max_size_mb-1," time(s).")
);
case(totalCount ==1,
strcat("The Azure Db ran into Readonly once at ",startTime, ", with ReadonlyReason 65536(Max QDS Size is reached). ",maxSizeMessage,mitigationMessage),
strcat("The Azure Db ran into Readonly ",totalCount," times with same ReadonlyReason 65536(Max QDS Size is reached). The first occurrence happended at ",startTime, ", and the most recent happened at ",endTime,". ",maxSizeMessage,mitigationMessage)
)
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event=~'query_store_disk_size_over_limit'
| extend current_size_mb=current_size_kb/1024
| extend max_size_mb=max_size_kb/1024
| project originalEventTimestamp,current_size_mb,max_size_mb
| summarize totalCount=count(),max_size_mb=max(max_size_mb),startTime=min(originalEventTimestamp),endTime=max(originalEventTimestamp),
dcount_max_size_mb=dcount(max_size_mb)
| extend startTime=format_datetime(startTime,'yyyy-MM-dd HH:mm')
| extend endTime=format_datetime(endTime,'yyyy-MM-dd HH:mm')
| where totalCount>0
| extend readonlyMessage=ReadonlyMessage(totalCount,max_size_mb,dcount_max_size_mb,startTime,endTime)
| project readonlyMessage
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If the Task3 returns results, display the exact message from the `readonlyMessage` column without any modifications.
2. If the Task3 doesn't return any result, display the following message exactly as written: "QDS didn't run into readonly due to 65536"


### Task 2: Execute Sub-Skills 
If QDS readonly 65536 is detected, execute the following sub‑skills and display:
"Because the 65536 issue was detected, we are going to perform additional checks:"
1. Execute the [QDS Size Over Time] (qds-size-overtime.md)  to check the QDS Size Health Status.
2. Execute the [QDS Size Based Cleanup Job Analysis] (qds-sizebased-cleanup-job-analysis.md)  to check the QDS Size Health Status.

If not detected, please do not display anything for this section

