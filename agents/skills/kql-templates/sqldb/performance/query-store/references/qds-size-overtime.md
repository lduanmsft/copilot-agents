---
name: qds-size-overtime
description: Check the size of query store (QDS) reached to 80%, 90% and 100% over the time.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# QDS Size Over Time Skill

## Skill Overview

This skill checks the Query Data Store (QDS) size over time to identify if QDS has reached or is approaching its storage limits. It analyzes historical data to determine if there are issues with QDS storage capacity that could affect query performance monitoring.

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
let SizeMessage = (totalCount:int, count_greaterthan100:int,count_greaterthan90:int,count_greaterthan80:int)
{
let summaryMessage=case(count_greaterthan100 >0,"Issue detected. Here are the details:",
count_greaterthan80>0,"Potential issue detected. Here are the details:",
"We don't find obvious issue. Here are the details:");
strcat(summaryMessage," Over the past 7 days up to the specified time range, the size of QDS reached its size limit ",
count_greaterthan100,iff(count_greaterthan100==1," time", " times"),", exceeded 90% of limit ",count_greaterthan90,iff(count_greaterthan90==1," time", " times"),", and exceeded 80% of limit ",count_greaterthan80,
iff(count_greaterthan80==1," time", " times"),"——accounting for ",round(count_greaterthan100*100.0/totalCount,1),"%, ",round(count_greaterthan90*100.0/totalCount,1),"%, ",round(count_greaterthan80*100.0/totalCount,1),"% of the total statistical data, respectively.")
};
MonQueryStoreInfo
| where {AppNamesNodeNamesWithPreciseTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event == "query_store_disk_size_info"
| summarize totalCount=count(), count_greaterthan100=countif(current_size_kb>=max_size_kb),count_greaterthan90=countif(current_size_kb>max_size_kb*0.9), count_greaterthan80=countif(current_size_kb>max_size_kb*0.8)
| extend sizeMessage=SizeMessage(totalCount,count_greaterthan100,count_greaterthan90,count_greaterthan80)
| extend IssueDetected=iff(count_greaterthan80 >0,'true','false')
| project sizeMessage,IssueDetected
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. display the exact message from the `sizeMessage` column without any modifications.


