---
name: memory
description: Analyze memory-related issues in Azure SQL Database including memory overbooking (MRG/DRG), out of memory (OOM) events, and buffer pool decreases. Provides comprehensive memory diagnostics and routing recommendations.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Memory Issues Analysis Skill

## Skill Overview

This skill provides comprehensive memory diagnostics for Azure SQL Database. It executes three sub-skills in sequence to analyze:
1. **Memory Overbooking** - Detects MRG (Multi-instance Resource Group) and DRG (Dynamic Resource Group) events indicating node-level memory pressure
2. **OOM Summary** - Identifies Out of Memory events and provides routing based on oomCause
3. **Buffer Pool Decrease** - Detects significant drops (≥20%) in MEMORYCLERK_SQLBUFFERPOOL

Note, these skills are independent but should be executed together for a complete memory analysis. Do NOT skip any sub-skill. Each provides unique insights into memory-related issues and potential performance impacts.

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

**This skill has 3 tasks.**

| Task | Description | Condition |
|------|-------------|-----------|
| Task 1 | Obtain Kusto cluster information for the logical server | Always |
| Task 2 | Execute the appnameandnodeinfo skill to get metadata variables | Always |
| Task 3 | Execute Memory Analysis Skills (overbooking, oom-summary, bufferpool-decrease) | Always |

## Execution Steps

### Task 1: Obtain Kusto cluster information for the logical server

**CRITICAL:** Always identify the correct cluster - do NOT use default clusters

Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../../Common/execute-kusto-query/references/getKustoClusterDetails.md](../../Common/execute-kusto-query/references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Execute the "[appnameandnodeinfo skill](../../Common/appnameandnodeinfo/SKILL.md)" to get the values of variables

### Task 3: Execute Memory Analysis Skills

**🔴🔴🔴 MANDATORY: Execute ALL THREE sub-skills below. Do NOT skip any. Do NOT proceed to other skills until all three are complete. 🔴🔴🔴**

1. **Memory Overbooking Analysis**:
   - Execute skill  [overbooking](references/overbooking.md)

2. **Out of Memory (OOM) Event Analysis**:
   - Execute skill  [oom-summary](references/oom-summary.md)

3. **Buffer Pool Decrease Analysis**:
   - Execute the [bufferpool-decrease](references/bufferpool-decrease.md)

**⛔ STOP CHECK**: Before leaving this skill, verify ALL THREE sub-skills above have been executed. Incomplete execution is a workflow violation.
