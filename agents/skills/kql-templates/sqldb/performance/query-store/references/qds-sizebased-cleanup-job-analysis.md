---
name: qds-sizebased-cleanup-job-analysis
description: Analyzes QDS (Query Data Store) Size Based Cleanup job execution history over the past 7 days to detect failures, long-running jobs, and potential issues.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug QDS Size Based Cleanup Job Analysis

## Skill Overview

This skill analyzes QDS Size Based Cleanup job execution to detect:
- Total number of cleanup jobs executed in the past 7 days
- Jobs that started but didn't complete (potential failures)
- Long-running cleanup jobs (taking more than 60 minutes)
- Overall health status of QDS size-based cleanup operations

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
let longDurationThreshold=60;
let CleanupJobMessage = (totalCount_cleanupStart:int,totalCount_CleanupFinish:int,endedWithCleanupFinish:bool,longDurationCount:int,min_duration:int,max_duration:int,avg_duration:real)
{
let longDurationMessage=case(longDurationCount >0,strcat(" Additionally, ",longDurationCount," Cleanup job took more than 60 mins to complete. The most time consuming one took ",max_duration," minutes to complete, while the average completion time was ",avg_duration, " mins. You may engage QDS experts to investigate the long-running jobs."),
isnan(avg_duration)==false,strcat("The most time consuming one took ",max_duration," minutes to complete, while the average completion time was ",toint(avg_duration), " mins"),
""
);
let potentionalFailureCount=totalCount_cleanupStart-totalCount_CleanupFinish;
let lastCleanupWithoutFinishMessage="Please note, The most recent cleanup job started but did not complete. There are two possible reasons: 1) The specified time range may not include the job's completion time. Try expanding the endTime and rerunning it. 2) The cleanup background job failed, then please engage QDS expert to investigate.";
let failedCleanupJobMessage=case(potentionalFailureCount==0,"",
endedWithCleanupFinish ==false and potentionalFailureCount==1,lastCleanupWithoutFinishMessage,
endedWithCleanupFinish ==true  and potentionalFailureCount>0, strcat(potentionalFailureCount, " of ",totalCount_cleanupStart, " started but didn't complete, indicating potential failures. Please engage QDS expert to investigate."),
strcat(potentionalFailureCount, " of ",totalCount_cleanupStart, " started but didn't complete, indicating potential failures. Please engage QDS expert to investigate. ",lastCleanupWithoutFinishMessage)
);
let succeededCleanupJobMessage=case(
potentionalFailureCount==0,strcat("Over the past 7 days up to the specified time period, QDS size-based cleanup background job(s) were executed ",totalCount_cleanupStart," time(s), no failure detected. "),
strcat("Over the past 7 days up to the specified time period, QDS size-based cleanup background job(s) were executed ",totalCount_cleanupStart," time(s), ",totalCount_CleanupFinish," of ",totalCount_cleanupStart," completed successfully. ")
);
strcat(succeededCleanupJobMessage,failedCleanupJobMessage,longDurationMessage)
};
let longRunningCleanupJob=MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
|where event in ('query_store_size_retention_cleanup_started','query_store_size_retention_cleanup_finished')
|order by originalEventTimestamp asc nulls first
| serialize
| extend preTime =iff(event=~'query_store_size_retention_cleanup_finished',prev(originalEventTimestamp), datetime(null))
| extend duration_minutes=datetime_diff('minute',originalEventTimestamp,preTime)
| extend duration_hours=datetime_diff('hour',originalEventTimestamp,preTime)
| extend originalEventTimestamp=format_datetime(originalEventTimestamp,'yyyy-MM-dd HH:mm')
| where event =~'query_store_size_retention_cleanup_finished'
| project originalEventTimestamp,preTime,duration_minutes,duration_hours,event,current_size_kb,target_delete_size_kb,deleted_plan_count,deleted_query_count,estimated_deleted_size_kb,last_deleted_query_total_cpu,max_deleted_total_cpu
| order by originalEventTimestamp asc
| summarize totalCount_LongRunningCleanupJob=countif(duration_minutes>=60),longDurationCount=countif(duration_minutes>=longDurationThreshold),min_duration=min(duration_minutes),max_duration=max(duration_minutes),avg_duration=round(avg(duration_minutes),1)
| extend joinColumn=1
;
let potentailFailedCleanupJob=MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event in ('query_store_size_retention_cleanup_started','query_store_size_retention_cleanup_finished')
| order by originalEventTimestamp asc nulls first
| serialize
| extend rn = row_number()
| summarize maxCountOfCleanupFinished=maxif(rn,event=~'query_store_size_retention_cleanup_finished' ),maxCount=max(rn),
totalCount_CleanupFinish=countif(event=~'query_store_size_retention_cleanup_finished') ,
totalCount_CleanupStart=countif(event=~'query_store_size_retention_cleanup_started' or (event=~'query_store_size_retention_cleanup_finished' and rn==1))
| extend endedWithCleanupFinish=maxCountOfCleanupFinished==maxCount
| extend potentionalFailureCount=totalCount_CleanupStart-totalCount_CleanupFinish
| extend joinColumn=1;
potentailFailedCleanupJob
| join kind=fullouter (longRunningCleanupJob) on joinColumn
| project totalCount_CleanupStart,totalCount_CleanupFinish,endedWithCleanupFinish,longDurationCount,min_duration,max_duration,avg_duration
| where totalCount_CleanupStart >=1
| extend cleanupJobMessage=CleanupJobMessage(totalCount_CleanupStart,totalCount_CleanupFinish,endedWithCleanupFinish,longDurationCount,min_duration,max_duration,avg_duration)
| extend IssueDetected=case(totalCount_CleanupStart-totalCount_CleanupFinish>1 or max_duration >=longDurationThreshold,'true','false')
| summarize count=count() ,arg_max(totalCount_CleanupStart,cleanupJobMessage,IssueDetected)
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If count returned by Task3 is 0, Display: "No QDS Cleanup job detected in the past 7 days. Could be a telemetry issue or QDS issue. Please engage QDS expert", else display the exact message from the `cleanupJobMessage` column without any modifications.

