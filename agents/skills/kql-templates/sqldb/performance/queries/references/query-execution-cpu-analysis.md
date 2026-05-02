---
name: query-execution-cpu-analysis
description: This skill analyzes T-SQL execution CPU usage recorded in QDS. If high CPU consumption is detected, it displays the query hash with the highest CPU usage. If no high CPU consumption is detected, it will also check for query hashes with high CPU usage at 15-minute intervals.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Query Execution CPU Analysis

## Skill Overview

This skill analyzes T-SQL execution CPU usage recorded in Query Data Store (QDS). It identifies whether SQL query execution has consumed significant CPU resources during the specified time period. The skill calculates CPU consumption as both a percentage of total User Pool CPU capacity and utilized User Pool CPU. If high CPU consumption is detected (≥30% of total capacity or ≥50% of utilized capacity), it displays detailed CPU consumption metrics and triggers sub-skills to identify the top CPU-consuming queries and analyze CPU trends over time.

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

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
MonWiQdsExecStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize totalCPU_ms = sum(cpu_time) / 1000.0
| project cpu_percent_OverAllUserPoolCPU=round(100*totalCPU_ms/{SumCpuMillisecondOfAllApp},1),
cpu_percent_ConsumedUserPoolCPU=round(100*totalCPU_ms/{ActualSumCpuMillisecondOfAllApp},1)
| extend cpuMessage=CPUMessage(cpu_percent_OverAllUserPoolCPU,cpu_percent_ConsumedUserPoolCPU)
| extend IssueDetected=iff(cpu_percent_OverAllUserPoolCPU>=30 or cpu_percent_ConsumedUserPoolCPU>=50,'true','false')
| project IssueDetected,totalCPU_ms,cpu_percent_OverAllUserPoolCPU,cpu_percent_ConsumedUserPoolCPU
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. Display the raw table without the IssueDetected column.
2. Save the value of IssueDetected to variable {IssueDetected}


### Task 2: Execute Sub-Skills

1. If {IssueDetected} is 'false', terminate this skill.
2. If {IssueDetected} is 'true':
   - Display the exact message: "As Query execution consumed significant CPU, we are going to do further checks"
   - **🚨 MANDATORY: Execute BOTH sub-skills below. Do NOT skip any.**

#### 🚨🚨 MANDATORY SUB-SKILL EXECUTION CHECKLIST 🚨🚨

**ALL of the following sub-skills are REQUIRED when IssueDetected='true':**

| Step | Sub-Skill | Description | Status |
| ---- | --------- | ----------- | ------ |
| 4.1 | [Top CPU Queries](top-cpu-queries.md) | Identify top CPU-consuming queries | ⬜ REQUIRED |
| 4.2 | [Query CPU Over Time Analysis](query-cpu-over-time-analysis.md) | Analyze CPU trends over time for top queries | ⬜ REQUIRED |

**⛔ CRITICAL ENFORCEMENT RULES:**
1. **NEVER skip Step 4.2** - Even if Step 4.1 identifies the top queries, you MUST continue to execute Step 4.2
2. **BOTH steps must show ✅ COMPLETE** before this skill is considered done
3. Step 4.2 provides temporal analysis that Step 4.1 cannot provide - they serve different purposes
4. Skipping Step 4.2 results in an incomplete investigation

**EXPECTED EXECUTION:**
- Step 4.1: Execute [Top CPU Queries](top-cpu-queries.md) → Get top CPU-consuming query hashes
- Step 4.2: Execute [Query CPU Over Time Analysis](query-cpu-over-time-analysis.md) → Show how those queries consumed CPU over time

**⚠️ DO NOT TERMINATE THIS SKILL UNTIL BOTH STEPS ARE COMPLETE**
   
