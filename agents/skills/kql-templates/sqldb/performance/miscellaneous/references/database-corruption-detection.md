---
name: database-corruption-detection
description: Detects database corruption events in Azure SQL databases by analyzing system health telemetry for corruption-related error IDs.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Database Corruption Detection

## Skill Overview

This skill detects database corruption in Azure SQL databases by querying the MonSQLSystemHealth table for corruption-related error IDs (211, 823, 824, 825, 829, 2533, 2570, 2576, 3203, 7985, 7989, 8909, 8914, 8916, 8928, 8939, 8942, 8948, 8964, 8965, 8978, 8992, 8998, 8999). Database corruption affects both data integrity and Azure DB availability, which can lead to severe consequences including database downtime, login failures, and query execution errors.

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
| Task 1 | Execute Kusto query to detect corruption events | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesOnly}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

**Decision Logic**:
- **If `{edition}` is NOT `Hyperscale`** (i.e., Free, Basic, Standard, Premium, GeneralPurpose, or BusinessCritical): Execute **Query A** below
- **If `{edition}` is `Hyperscale`**: Execute **Query B** below

---

#### Query A: For Non-Hyperscale Editions (Free, Basic, Standard, Premium, GeneralPurpose, BusinessCritical)

**Condition**: Execute this query ONLY when `{edition}` ≠ `Hyperscale`

```kql
MonSQLSystemHealth
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~ '{LogicalServerName}'
| where error_id in (211,823,824,825,829,2533,2570,2576,3203,7985,7989,8909,8914,8916,8928,8939,8942,8948,8964,8965,8978,8992,8998,8999) 
| summarize totalCount=count(),dcount=dcount(error_id),StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp)
| summarize count(),take_any(message),StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp) by error_id,NodeName
```

---

#### Query B: For Hyperscale Edition

**Condition**: Execute this query ONLY when `{edition}` = `Hyperscale`

```kql
let appNames=materialize (
MonSocrates
| where  (originalEventTimestamp between (datetime({StartTime})..datetime({EndTime})))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where isnotempty(foreign_file_id)
| summarize by AppName,AppTypeName
);
MonSQLSystemHealth
| where  (originalEventTimestamp between (datetime({StartTime})..datetime({EndTime})))
| where LogicalServerName =~ '{LogicalServerName}' 
| join kind=inner(appNames) on AppName
| where error_id in (211,823,824,825,829,2533,2570,2576,3203,7985,7989,8909,8914,8916,8928,8939,8942,8948,8964,8965,8978,8992,8998,8999) 
| summarize count(),take_any(message),StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp) by error_id,NodeName
```

---

#### Output (applies to both Query A and Query B)

Follow these instructions exactly:

1. **If query returns no results (rowcount = 0)**:
   - Display: "Corruption is not detected."
   - **STOP HERE** - Do not proceed further

2. **If query returns results (rowcount > 0)**:
   - Display the corruption events as a table
   - Calculate and display the **Total Count** (sum of all count values)
   - Display the recommendation to engage the Storage Engine team

| error_id | count | message | StartTime | EndTime | NodeName |
|----------|-------|---------|-----------|---------|----------|
| `error_id` | `count_` | `message` | `StartTime` | `EndTime` | `NodeName` |

**Total Count**: Sum of all count values

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Corruption is Detected

#### Database Corruption Analysis Results

**Yes, database corruption was detected during the investigation period.**

#### Corruption Events

| error_id | count | message | StartTime | EndTime | NodeName |
|----------|-------|---------|-----------|---------|----------|
| 823 | 450 | Error 823: I/O error detected during read... | 2026-01-15 10:15 | 2026-01-15 11:42 | _DB_35 |
| 824 | 50 | Error 824: Logical consistency-based I/O error... | 2026-01-15 10:18 | 2026-01-15 11:45 | _DB_35 |

**Total Count**: 500

---

The Database corruption affects both data integrity and Azure DB availability, which can lead to severe consequences, including (but not limited to) database downtime, login failures, and query execution errors. **Please Engage the Storage Engine team to investigate.**

---

### When No Corruption is Detected

#### Database Corruption Analysis Results

**No, database corruption was NOT detected during the investigation period.**

#### Summary

Corruption is not detected.
