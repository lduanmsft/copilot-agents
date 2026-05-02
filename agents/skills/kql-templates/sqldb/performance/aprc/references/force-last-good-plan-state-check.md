---
name: force-last-good-plan-state-check
description: This skill checks the state of the FORCE_LAST_GOOD_PLAN automatic tuning option to determine if automatic query plan correction is enabled for the database
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug FORCE_LAST_GOOD_PLAN State

## Skill Overview

This skill checks the state of the FORCE_LAST_GOOD_PLAN automatic tuning option in Azure SQL Database. The FORCE_LAST_GOOD_PLAN option enables automatic query plan correction by forcing the last known good execution plan when a query plan regression is detected. This skill analyzes the option's actual state, desired state, and whether it has been disabled by the system during the investigation time range.

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
MonAutomaticTuningState
  | where {AppNamesNodeNamesWithPreciseTimeRange}
  | extend logical_database_name=logical_db_name
  | where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
  | where option_name == "FORCE_LAST_GOOD_PLAN" 
  | summarize offCount=countif(option_actual_state==0),onCount=countif(option_actual_state==1),offBySystemCount=countif(option_system_disabled==1)
  | extend IssueDetected=offCount+offBySystemCount>0
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If zero rows returned or all counts are 0, display: "No FORCE_LAST_GOOD_PLAN state data found for this database during the investigation period."
2. Display the query results as a table.
3. Based on the results, determine the state message using the logic below:
   - If `offBySystemCount > 0`: "🚩 The FORCE_LAST_GOOD_PLAN option was disabled by the system, please transfer to queue 'Automatic tuning, Azure SQL Analytics' for RCA if this is a concern."
   - If `offCount > 0` and `onCount == 0`: "🚩 The FORCE_LAST_GOOD_PLAN option was off, hence it will not automatically force the last good query plan. Please consider enabling it if needed."
   - If `offCount > 0` and `onCount > 0`: "🚩 The FORCE_LAST_GOOD_PLAN option was changed. Please note, the Auto Query Plan Correction will not happen if FORCE_LAST_GOOD_PLAN is OFF."
   - Otherwise: "Everything looks good, FORCE_LAST_GOOD_PLAN is not turned off."

---

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When FORCE_LAST_GOOD_PLAN is ON (No Issues)

#### FORCE_LAST_GOOD_PLAN State Check Results

**Everything looks good, FORCE_LAST_GOOD_PLAN is not turned off.**

#### State Summary

| Metric | Value |
|--------|-------|
| **Off Count** | 0 |
| **On Count** | 6 |
| **Disabled by System Count** | 0 |
| **Issue Detected** | false |

#### Analysis

The FORCE_LAST_GOOD_PLAN automatic tuning option was consistently enabled during the investigation period. Automatic query plan correction is active and will force the last known good execution plan when a query plan regression is detected.

---

### When FORCE_LAST_GOOD_PLAN is OFF

#### FORCE_LAST_GOOD_PLAN State Check Results

🚩 **The FORCE_LAST_GOOD_PLAN option was off, hence it will not automatically force the last good query plan. Please consider enabling it if needed.**

#### State Summary

| Metric | Value |
|--------|-------|
| **Off Count** | 5 |
| **On Count** | 0 |
| **Disabled by System Count** | 0 |
| **Issue Detected** | true |

#### Analysis

🚩 The FORCE_LAST_GOOD_PLAN automatic tuning option was **disabled** during the investigation period. This means SQL Server will not automatically correct query plan regressions. If query performance issues are occurring, consider enabling this option.

#### Recommendation

To enable automatic plan correction, run the following T-SQL:
```sql
ALTER DATABASE CURRENT SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON);
```

---

### When FORCE_LAST_GOOD_PLAN was Disabled by System

#### FORCE_LAST_GOOD_PLAN State Check Results

🚩 **The FORCE_LAST_GOOD_PLAN option was disabled by the system, please transfer to queue 'Automatic tuning, Azure SQL Analytics' for RCA if this is a concern.**

#### State Summary

| Metric | Value |
|--------|-------|
| **Off Count** | 0 |
| **On Count** | 3 |
| **Disabled by System Count** | 2 |
| **Issue Detected** | true |

#### Analysis

🚩 The FORCE_LAST_GOOD_PLAN automatic tuning option was **disabled by the system** during the investigation period. This typically occurs when the system detects an issue that prevents automatic plan correction from functioning properly.

#### Recommendation

Transfer to queue **'Automatic tuning, Azure SQL Analytics'** for root cause analysis.

---

### Output Format Requirements

1. **Always start with a direct answer** - State clearly whether any issues were detected with FORCE_LAST_GOOD_PLAN
2. **Include a summary table** - Present all metrics (offCount, onCount, offBySystemCount, IssueDetected) with their values
3. **Provide analysis** - Explain what the state means in context
4. **Include recommendations** - Provide actionable next steps when issues are detected
5. **Use 🚩 emoji** - Flag issues for visibility when FORCE_LAST_GOOD_PLAN is off or disabled
