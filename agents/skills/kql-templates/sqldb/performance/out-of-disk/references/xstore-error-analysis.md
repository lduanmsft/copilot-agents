---
name: xstore-error-analysis
description: Analyze XStore (Azure SQL Database storage layer) errors to identify storage-related issues affecting database performance and availability.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug XStore Error Analysis

## Skill Overview

This skill analyzes XStore errors in Azure SQL Database. XStore is the storage layer for Azure SQL DB, and errors in this layer can lead to database availability issues, I/O failures, and performance degradation.

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

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesOnly}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
let ErrorMessage=(totalCount: int,errorcodeArray:string,
count_TopError: int,mapped_errorcode: int,dcount_errorcode: int
)
{
let noErrorMessage="We didn't detect any XStore related errors.";
let summary=strcat(
"The Azure DB Storage run into error ",totalCount, iif(totalCount == 1, " time", " times"),
" with ",dcount_errorcode, iif(dcount_errorcode == 1, " single error ", " different errors"),errorcodeArray,".");
let topError=iif(dcount_errorcode ==1,"",
strcat(" The top error was ",mapped_errorcode, ", happening ",count_TopError, iif(count_TopError == 1, " time", " times")));
iif(totalCount == 0, noErrorMessage, strcat(summary,topError))
};
MonSQLXStore
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~ '{LogicalServerName}'
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where event =='xio_failed_request'
| where file_path contains '.mdf' or file_path contains '.ndf' or file_path contains '.ldf'
| summarize count_=count() by mapped_errorcode
| summarize totalCount=sum(count_),errorcodeArray=make_set(mapped_errorcode),count_TopError=arg_max(count_, mapped_errorcode),dcount_errorcode=dcount(mapped_errorcode)
| extend errorMessage=ErrorMessage(totalCount,errorcodeArray,count_TopError,mapped_errorcode,dcount_errorcode)
| project errorMessage
```

#### Output
Follow these instructions exactly. Only display output when specified:

1. Display the exact message from `errorMessage` without any modification


