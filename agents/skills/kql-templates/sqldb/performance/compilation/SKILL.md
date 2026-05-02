---
name: compilation
description: Analyze query compilation issues in Azure SQL Database including failed compilations, long compilations, compile gateway contention, and high CPU usage from compilation activities.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---


# Query Compilation Issues Skill

## Skill Overview

This skill analyzes query compilation issues in Azure SQL databases. It detects and diagnoses problems related to query compilation including failed compilations, long-running compilations, compile gateway contention, and high CPU consumption from compilation activities.

## Prerequisites

- Access to Kusto clusters for SQL telemetry
- Logical server name and database name
- Time range for investigation

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{TopN}` | Number of top items (optional) | integer | `5` (default) |

## Execution Steps

### Task 1: Obtain Kusto Cluster Information
**CRITICAL:** Always identify the correct cluster - do NOT use default clusters

Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../../Common/execute-kusto-query/references/getKustoClusterDetails.md](../../Common/execute-kusto-query/references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Execute AppName and Node Info Skill
Execute the [appnameandnodeinfo skill](../../Common/appnameandnodeinfo/SKILL.md) to get the values of required variables:
- `{AppNamesNodeNamesWithOriginalEventTimeRange}`
- `{SumCpuMillisecondOfAllApp}`
- `{isElasticPool}`

---

### Step 1: Compilation CPU Analysis 

Analyze CPU consumption from both failed and successful compilations to determine if compilation activities are contributing to high CPU usage.

#### Step 1a: Failed Compilation CPU Analysis
**Reference**: [cpu-usage-of-failed-compilation](.github/skills/Performance/Compilation/references/cpu-usage-of-failed-compilation.md)


#### Step 1b: Successful Compilation CPU Analysis
**Reference**: [cpu-usage-of-successful-compilation](.github/skills/Performance/Compilation/references/cpu-usage-of-successful-compilation.md)

---

### Step 2: Failed Compilation Summary 
**Reference**: [failed-compilation-summary](.github/skills/Performance/Compilation/references/failed-compilation-summary.md)

---

### Step 3: Compile Gateway Contention 
**Reference**: [query-compile-gateway](.github/skills/Performance/Compilation/references/query-compile-gateway.md)

---

### Step 4: Top Failed Compilations by CPU 
**Reference**: [top-failed-compilation-ranked-by-cpu-usage](.github/skills/Performance/Compilation/references/top-failed-compilation-ranked-by-cpu-usage.md)

---

### Step 5: Top Successful Compilations by CPU Time  
**Reference**: [top-successful-compilation-ranked-by-cpu-usage](.github/skills/Performance/Compilation/references/top-successful-compilation-ranked-by-cpu-usage.md)

---
