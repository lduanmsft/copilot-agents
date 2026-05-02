---
name: cpu
description: Analyze high CPU usage issues in Azure SQL Database; Determine if high CPU usage happened.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# High CPU Issues Skill

## Skill Overview

This skill detects high cpu issue from four different angles: compilation, query execution and QDS. It includes the following analysis:User pool CPU, Kernel Model CPU, System Pool CPU and Node level CPU.


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


### Task 3: Execute CPU Analysis Skills

1. **User Pool CPU Analysis**:
   - Execute skill [User Pool CPU Analysis for Singleton](references/user-pool-cpu-analysis-singleton.md) and display the result.
   - If {isElasticPool} is true, display the exact message: "This Azure DB is in an elastic pool, we are going to do further checks" and execute the [User Pool CPU Analysis for Elastic Pool](references/user-pool-cpu-analysis-ep.md).
  
2. **Kernel Mode CPU Analysis**:
   - Execute skill [Kernel Mode CPU Analysis](references/kernel-mode-cpu-analysis.md)

3. **System Pool CPU Analysis**:
   - Execute skill [System Pool CPU Analysis](references/system-pool-cpu-analysis.md)

4. **Node Level CPU Analysis**:
   - Execute skill [Node Level CPU Analysis](references/node-level-cpu.md)
   - This analyzes total node CPU usage and detects pegged cores
