---
name: akv-error-detection
description: Detects Azure Key Vault errors that may cause SQL Server to fail when reading data, lead to query delays, or prevent the database from starting.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug AKV Error Detection

## Skill Overview

This skill detects Azure Key Vault (AKV) errors in SQL databases. AKV errors may cause SQL Server to fail when reading data, lead to query delays, or even prevent the database from starting. When detected, the Azure Key Vault team (Security: Transparent Data Encryption (TDE) and AKV) should be engaged for investigation.

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
| Task 1 | Query AKV errors (edition-specific) | Always |

## Execution Steps

### Task 1: Execute the appropriate Kusto query based on edition. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

**Decision Logic**:
- **If `{edition}` is NOT `Hyperscale`** (i.e., Free, Basic, Standard, Premium, GeneralPurpose, or BusinessCritical): Execute **Query A** below
- **If `{edition}` is `Hyperscale`**: Execute **Query B** below

---

#### Query A: For Non-Hyperscale Editions (Free, Basic, Standard, Premium, GeneralPurpose, BusinessCritical)

**Condition**: Execute this query ONLY when `{edition}` ≠ `Hyperscale`

```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and AppName in ({AppNamesOnly})
| where error_id in (33183 , 37412,33184,37542,37566,37567,37568,37569,37570,37571,37572,37573,37574,37576,40981,45320,45321,45322,45324,45325,45326,45327,45329,45330,45362,45415,45463,45472,45494,45532,45538,45539,45654,45656,45720,45731,45746,45747,49981)
| summarize count=count(), message=take_any(message), StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp) by error_id,NodeName
| order by count desc
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
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| join kind=inner(appNames) on AppName
| where error_id in (33183 , 37412,33184,37542,37566,37567,37568,37569,37570,37571,37572,37573,37574,37576,40981,45320,45321,45322,45324,45325,45326,45327,45329,45330,45362,45415,45463,45472,45494,45532,45538,45539,45654,45656,45720,45731,45746,45747,49981)
| summarize count=count(), message=take_any(message), StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp) by error_id,NodeName
| order by count desc
```

---

#### Output (applies to both Query A and Query B)

Follow these instructions exactly:

1. **If query returns no results (rowcount = 0)**:
   - Display: "Azure Key Vault error is not detected."
   - **STOP HERE**

2. **If query returns results (rowcount > 0)**:
   - Display the error details as a table with all columns
   - Calculate the **Total Count** (sum of all count values)
   - Calculate the **Number of Error Types** (number of rows)
   - Determine the **Error Window** (earliest StartTime to latest EndTime across all rows)
   - Display the summary in this exact format:
   
   > Azure Key Vault error was detected {TotalCount} time(s) across {NumberOfErrorTypes} different error types between {EarliestStartTime} and {LatestEndTime}. The error may cause SQL Server to fail when reading data, lead to query delays, or even prevent the database from starting. Please engage the Azure Key Vault team (Security: Transparent Data Encryption (TDE) and AKV) for investigation.

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When AKV Error is Detected

#### Azure Key Vault Error Analysis Results

**Yes, Azure Key Vault errors were detected during the investigation period.**

#### Error Details

| Count | Error ID | Message | Start Time | End Time |
|-------|----------|---------|------------|----------|
| 500 | 37576 | Azure Key Vault connectivity error | 2026-01-15 10:15 | 2026-01-15 11:45 |
| 200 | 33183 | Failed to access key vault | 2026-01-15 10:20 | 2026-01-15 11:30 |
| 74 | 45472 | Key vault throttling | 2026-01-15 10:45 | 2026-01-15 11:00 |

#### Summary

Azure Key Vault error was detected 774 time(s) across 3 different error types between 2026-01-15 10:15 and 2026-01-15 11:45. The error may cause SQL Server to fail when reading data, lead to query delays, or even prevent the database from starting. Please engage the Azure Key Vault team (Security: Transparent Data Encryption (TDE) and AKV) for investigation.

---

### When No AKV Error is Detected

#### Azure Key Vault Error Analysis Results

**No, Azure Key Vault errors were NOT detected during the investigation period.**

#### Summary

Azure Key Vault error is not detected.


