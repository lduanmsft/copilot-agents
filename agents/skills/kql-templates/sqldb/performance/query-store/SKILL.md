---
name: query-store
description: This skill diagnoses Query Data Store (QDS) issues, including readonly state detection and root cause analysis
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# QDS Readonly Issues Skill

## Skill Overview

This skill detects Query Store (QDS) readonly conditions in Azure SQL Database. Query Store may enter a readonly state when it encounters various resource limitations including:
- Statement hash map exceeding memory limit
- Buffered items exceeding memory limit  
- Total resource usage exceeding instance limit
- Disk size exceeding limit
- Database running out of disk space

When readonly conditions are detected, further root cause analysis can be performed using the 'QDS Readonly Root Cause Analysis' skill.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |


## Execution Steps

### Task 1:  Obtain Kusto cluster information for the logical server
**CRITICAL:** Always identify the correct cluster - do NOT use default clusters
Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../../Common/execute-kusto-query/references/getKustoClusterDetails.md](../../Common/execute-kusto-query/references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Execute the "[appnameandnodeinfo skill](../../Common/appnameandnodeinfo/SKILL.md)" to get the values of variables

### Task 3: Execute Sub-Skills 
1. If {isInElasticPool} is false, display the exact message:"Database `{LogicalDatabaseName}` is a singleton database." without any modification.
2. Execute skill [QDS Readonly for Azure Singleton database] (references/readonly-detection-singleton.md) and display the result.
3. If {isInElasticPool} is true, display the exact message:"This Azure DB is in an elastic pool, we are going to do further checks" and execute the [QDS Readonly for Azure Elastic pool] (references/readonly-detection-ep.md).
