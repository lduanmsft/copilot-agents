---
name: failed-compilation-summary
description: This skill will display failed compilation queries
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Failed Compilation Summary

## Skill Overview

This skill analyzes and detects failed query compilations in the database. It provides a summary of compilation failures, including counts by error code and detailed metrics by query hash (CPU usage, compilation duration, and failure count). This helps identify queries that are consistently failing during compilation and the reasons for these failures.

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

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

~~~kql
// This query displays the total number of failed compilations
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed, 16)))
| where event =~'failed_compilation'
| summarize FailedCount=count()
| where FailedCount > 0

// This query displays the failed compilation with error code
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed, 16)))
| where event =~'failed_compilation'
| summarize FailedCount=count() by error_code;

//This query displays the failed compilation with compile_cpu and compile_duration
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed, 16)))
| where event =~'failed_compilation'
| summarize compile_cpu_ms=sum(compile_cpu),compile_duration_ms=sum(compile_duration),FailedCount=count() by query_hash
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw result
