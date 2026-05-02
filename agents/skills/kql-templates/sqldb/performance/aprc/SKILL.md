---
name: aprc
description: SQL Server Automatic Plan Correction for specific query
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug FORCE_LAST_GOOD_PLAN State

## Skill Overview

This skill checks SQL Server Automatic Plan Correction for specific query. It analyzes the MonAutomaticTuning telemetry to identify when new query plans have regressed compared to previously good plans, and provides frequency analysis to help determine the severity and nature of the regression.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | Query hash to investigate (optional) | binary string | `0x73E64DD291EBBF6E` |

## Execution Steps

### Task 1:  Obtain Kusto cluster information for the logical server
**CRITICAL:** Always identify the correct cluster - do NOT use default clusters
Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../../Common/execute-kusto-query/references/getKustoClusterDetails.md](../../Common/execute-kusto-query/references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Execute sub-skills

1. Execute Skill(force-last-good-plan-state-check)[references/force-last-good-plan-state-check.md]
2. Execute Skill(forced-plan-regression-detection-of-specific-query)[references/forced-plan-regression-detection-of-specific-query.md]
3. Execute Skill(plan-regression-detection-of-specific-query)[references/plan-regression-detection-of-specific-query.md]
