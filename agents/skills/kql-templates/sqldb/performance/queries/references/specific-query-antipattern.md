---
name: specific-query-antipattern
description: Detect if antipattern happen;
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Query AntiPattern Analysis

## Skill Overview

This skill checks if the specified query has any AntiPatterns and displays the type of AntiPattern detected. 

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | The query hash to analyze | string | `0x1234567890ABCDEF` |



## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithPreciseTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where event =~ 'query_antipattern'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed)))
| extend query_plan_hash = strcat('0x', toupper(tohex(query_plan_hash_signed)))
| where query_hash =~'{query_hash}'
| distinct antipattern_type,query_plan_hash,query_hash
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:

1. **antipattern_type**: Display the type of AntiPattern detected in the query
2. **query_plan_hash**: Display the query plan hash associated with the antipattern
3. **query_hash**: Display the query hash that was analyzed

4. If antipatterns are detected, display: "AntiPatterns in T-SQL have been detected, which can degrade performance and lead to increased consumption of CPU, memory, and I/O resources. Please optimize the T-SQL query to address these issues."

5. If no results are returned, display: "AntiPattern was not detected. Please note that we only search MonQueryProcessing from the time range specified. You may need to adjust the time range if needed"
