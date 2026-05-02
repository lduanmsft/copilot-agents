---
name: dump-summary
description: Analyze SQL Server dump creation events and dump file summary for Azure SQL Database
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Dump Summary

## Skill Overview

This skill analyzes SQL Server dump file creation events to determine if dumps were created during the investigation time window. It checks the MonSqlDumperActivity table for dump events, identifies the most frequent stack signatures, and provides details about dump error types. The skill supports both standard tier databases and Hyperscale databases with separate queries.

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
| Task 1 | Execute Kusto query to detect dump events | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesOnly}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

**Decision Logic**:
- **If `{edition}` is NOT `Hyperscale`** (i.e., Free, Basic, Standard, Premium, GeneralPurpose, or BusinessCritical): Execute **Query A** below
- **If `{edition}` is `Hyperscale`**: Execute **Query B** below

---

#### Query A: For Non-Hyperscale Editions (Free, Basic, Standard, Premium, GeneralPurpose, BusinessCritical)

**Condition**: Execute this query ONLY when `{edition}` ≠ `Hyperscale`

```kql
let baseUrl="https://portal.watson.azure.com/dump?dumpUID=";
MonSqlDumperActivity
| extend AppName=split(TargetAppName, "/")[-1]//To extract the appname after last slash in a value like fabric:/Worker.ISO.Premium/ABCDEFG
| extend LogicalServerName=split(TargetLogicalServerName, ".")[0]//To extract the string before the first dot in a value like "serverName.database.windows.net"
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~ '{LogicalServerName}'
| extend DumperStartTime=PreciseTimeStamp//DumperStartTime is supposed to be Datetime, however it's string datatype in some clusters(sqlazureeus12 for example). To make it work in all regions, temporarily use PreciseTimeStamp
| where DumperStartTime between(datetime({StartTime})..datetime({EndTime}))
| extend DumperStartTime=format_datetime(DumperStartTime, 'yyyy-MM-dd HH:mm')
| summarize arg_max(TIMESTAMP,DumperStartTime, AppName,NodeName,ClusterName,CallStack,StackSignature,DumpErrorText,DumpErrorDetails) by DumpUID//remove duplicated entry
| summarize count(),min(DumperStartTime),max(DumperStartTime),take_any(DumpErrorDetails),URL=strcat(baseUrl,take_any(DumpUID)) by StackSignature
| project-reorder count_
| order by count_ 
```

---

#### Query B: For Hyperscale Edition

**Condition**: Execute this query ONLY when `{edition}` = `Hyperscale`

```kql
let baseUrl="https://portal.watson.azure.com/dump?dumpUID=";
let appNames=materialize (
MonSocrates
| where  (originalEventTimestamp between (datetime({StartTime})..datetime({EndTime})))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where isnotempty(foreign_file_id)
| summarize by AppName,AppTypeName
);
MonSqlDumperActivity
| extend AppName=split(TargetAppName, "/")[-1]
| extend AppName=tostring(AppName)
| extend LogicalServerName=split(TargetLogicalServerName, ".")[0]
| where LogicalServerName =~ '{LogicalServerName}'
| join kind=inner(appNames) on AppName
| extend DumperStartTime=PreciseTimeStamp//DumperStartTime is supposed to be Datetime, however it's string datatype in some clusters(sqlazureeus12 for example). To make it work in all regions, temporarily use PreciseTimeStamp
| where DumperStartTime between (datetime({StartTime})..datetime({EndTime}))
| extend DumperStartTime=format_datetime(DumperStartTime, 'yyyy-MM-dd HH:mm')
| extend IsComputeNode=(AppTypeName1=='Worker.Vldb.Compute')
| summarize arg_min(DumperStartTime, AppName, NodeName,ClusterName,CallStack,StackSignature,DumpErrorText,DumpErrorDetails,IsComputeNode) by DumpUID,AppTypeName1//remove duplicated entry
| summarize count(),min(DumperStartTime),max(DumperStartTime),take_any(DumpErrorDetails),URL=strcat(baseUrl,take_any(DumpUID)) by StackSignature,AppTypeName1,IsComputeNode
| project-reorder count_
| order by count_ 
```

---

#### Output for Query A (Non-Hyperscale)

Follow these instructions exactly:

1. **If query returns no results (rowcount = 0)**:
   - Display: "The azure Db didn't have dump created"
   - **STOP HERE**

2. **If query returns results (rowcount > 0)**:
   - Display the dump summary as a table with all columns
   - Calculate and display the **Total Count** (sum of all count_ values)

| Count | StackSignature | DumpErrorDetails | Start Time | End Time | Sample Dump URL |
|-------|----------------|------------------|------------|----------|------------------|
| `count_` | `StackSignature` | `any_DumpErrorDetails` | `min_DumperStartTime` | `max_DumperStartTime` | `URL` |

**Total Count**: Sum of all count_ values

---

#### Output for Query B (Hyperscale)

Follow these instructions exactly:

1. **If query returns no results (rowcount = 0)**:
   - Display: "The azure Db didn't have dump created"
   - **STOP HERE**

2. **If query returns results (rowcount > 0)**:
   - Display the dump summary as a table with all columns (including IsComputeNode)
   - Calculate and display the **Total Count** (sum of all count_ values)

| Count | StackSignature | DumpErrorDetails | Start Time | End Time | IsComputeNode | Sample Dump URL |
|-------|----------------|------------------|------------|----------|---------------|------------------|
| `count_` | `StackSignature` | `any_DumpErrorDetails` | `min_DumperStartTime` | `max_DumperStartTime` | `IsComputeNode` | `URL` |

**Total Count**: Sum of all count_ values

> **Note**: `IsComputeNode = true` means the dump was created on a Compute Node. `IsComputeNode = false` means the dump was created on a Page Server or Log Server.

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Dump is Detected (Non-Hyperscale)

## Dump Summary Results

**Yes, SQL Server dumps were created during the investigation period.**

### Dump Details

| Count | StackSignature | DumpErrorDetails | Start Time | End Time | Sample Dump URL |
|-------|----------------|------------------|------------|----------|------------------|
| 15 | 00000000000003BD | Stalled Dispatcher | 2026-01-15 10:50 | 2026-01-15 11:32 | [Link](https://portal.watson.azure.com/dump?dumpUID=sample-uid-1) |
| 12 | 00000000000001A2 | Non-yielding Scheduler | 2026-01-15 10:33 | 2026-01-15 11:15 | [Link](https://portal.watson.azure.com/dump?dumpUID=sample-uid-2) |
| 10 | 00000000000002C5 | StackDump (all) | 2026-01-15 10:45 | 2026-01-15 11:50 | [Link](https://portal.watson.azure.com/dump?dumpUID=sample-uid-3) |
| 7 | 00000000000004D8 | ex_dump_if_requested | 2026-01-15 10:40 | 2026-01-15 11:20 | [Link](https://portal.watson.azure.com/dump?dumpUID=sample-uid-4) |

**Total Count**: 44

---

### When Dump is Detected (Hyperscale)

## Dump Summary Results

**Yes, SQL Server dumps were created during the investigation period.**

### Dump Details

| Count | StackSignature | DumpErrorDetails | Start Time | End Time | IsComputeNode | Sample Dump URL |
|-------|----------------|------------------|------------|----------|---------------|------------------|
| 15 | 00000000000003BD | Stalled Dispatcher | 2026-01-15 10:50 | 2026-01-15 11:32 | true | [Link](https://portal.watson.azure.com/dump?dumpUID=sample-uid-1) |
| 12 | 00000000000001A2 | Non-yielding Scheduler | 2026-01-15 10:33 | 2026-01-15 11:15 | false | [Link](https://portal.watson.azure.com/dump?dumpUID=sample-uid-2) |
| 10 | 00000000000002C5 | StackDump (all) | 2026-01-15 10:45 | 2026-01-15 11:50 | false | [Link](https://portal.watson.azure.com/dump?dumpUID=sample-uid-3) |

**Total Count**: 37

---

### When No Dump is Detected

## Dump Summary Results

**No, SQL Server dumps were NOT created during the investigation period.**

### Summary

The azure Db didn't have dump created.
