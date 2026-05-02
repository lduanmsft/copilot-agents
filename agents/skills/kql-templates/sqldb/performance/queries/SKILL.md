---
name: queries
description: Comprehensive query performance analysis including top resource-consuming queries (CPU, memory, reads, writes, log, tempdb), failed queries, wait analysis, long-running transactions, and query-specific diagnostics for Azure SQL databases.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
keywords: ['query', 'queries', 'slow query', 'query performance', 'failed query', 'wait queries', 'long-running', 'query timeout', 'top queries']
---

# Query Performance Analysis Skill

## Skill Overview

This skill provides comprehensive query performance analysis in Azure SQL databases. It identifies resource-intensive queries, analyzes execution patterns, detects failures, and provides detailed diagnostics for specific queries.

**Default Checks (Always Run)**:
- ⭐ Overall Top Queries Analysis
- ⭐ Top CPU Queries
- ⭐ Failed Query Execution Summary
- ⭐ Top Wait Queries

**Conditional Checks (Run When Relevant)**:
- Top Memory Queries
- Top Reads/Writes Queries
- Top Log/Tempdb Usage Queries
- Long-Running Transactions
- Query-Specific Diagnostics
- Query Execution Time vs Wait Time Analysis
- Query Antipattern Detection

## When to Use This Skill

This skill should be triggered when the user reports or asks about:
- **Slow queries** or query performance degradation
- **High CPU/memory usage** from specific queries
- **Failed queries** or query timeouts
- **Wait-related issues** (PAGEIOLATCH, CXPACKET, etc.)
- **Query execution patterns** and trends
- **Long-running transactions** blocking other operations
- **Resource-intensive queries** consuming CPU, memory, I/O, log space, or tempdb

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
| `{query_hash}` | Specific query hash (optional) | binary string | `0x73E64DD291EBBF6E` |

## Execution Order

Execute the following diagnostic checks. The checks are split into **Default Checks** (always run) and **Conditional Checks** (run based on context).

**⚠️ IMPORTANT: Output Filtering Rule**
- **ONLY display results from a sub-skill if it detects an issue (🚩)**
- **DO NOT display any output from a sub-skill if no issue is detected (✅)**
- This keeps the report concise and focused on actionable findings

---

## Default Checks (Always Run)

These checks are **MANDATORY** and should be executed in every query performance investigation.

### Step 1: Overall Top Queries Analysis ⭐ DEFAULT
**Reference**: [overall-top-queries.md](references/overall-top-queries.md)

Provides a comprehensive overview of the top resource-consuming queries across multiple dimensions (CPU, memory, reads, writes, waits). This gives a holistic view of query resource consumption.

**Why default**: Provides comprehensive resource overview to quickly identify problematic queries across all dimensions.

**Output Rule**: Only include this section if resource-intensive queries are detected.

---

### Step 2: Top CPU Queries ⭐ DEFAULT
**Reference**: [top-cpu-queries.md](references/top-cpu-queries.md)

Identifies the top CPU-consuming query hashes and analyzes their CPU usage patterns. Calculates percentage of User Pool CPU capacity and visualizes CPU usage trends over time.

**Why default**: CPU consumption is the most common query performance issue and must always be analyzed.

**Output Rule**: Only include this section if high CPU queries are detected.

**Related Analyses** (run if Step 2 detects issues):
- [top-cpu-queries-over-time.md](references/top-cpu-queries-over-time.md) - CPU usage trends
- [query-cpu-over-time-analysis.md](references/query-cpu-over-time-analysis.md) - Detailed CPU timeline

---

### Step 3: Failed Query Execution Summary ⭐ DEFAULT
**Reference**: [failed-query-execution-summary.md](references/failed-query-execution-summary.md)

Analyzes failed query executions including timeouts, aborts, and internal execution failures. Calculates failure rates to diagnose query execution issues.

**Why default**: Query failures indicate critical issues and must always be checked to rule out execution problems.

**Output Rule**: Only include this section if failed queries are detected.

**Related Analyses** (run if Step 3 detects failures):
- [top-failed-queries.md](references/top-failed-queries.md) - Top failing query hashes

---

### Step 4: Top Wait Queries ⭐ DEFAULT
**Reference**: [top-wait-queries.md](references/top-wait-queries.md)

Identifies queries experiencing the highest wait times. Analyzes wait patterns to understand resource contention and blocking.

**Why default**: Wait times indicate resource contention and are essential for understanding query performance degradation.

**Output Rule**: Only include this section if queries with significant wait times are detected.

**Related Analyses** (run if Step 4 detects wait issues):
- [top-wait-types-of-query-execution.md](references/top-wait-types-of-query-execution.md) - Wait type breakdown

---

## Conditional Checks (Run Based on Context)

These checks are executed when specific resource consumption patterns are identified or when investigating specific query issues.

### Step 5: Top Memory Queries (Conditional)
**Reference**: [top-memory-queries.md](references/top-memory-queries.md)

Identifies queries consuming the most memory grants. Useful for diagnosing memory pressure issues.

**When to run**:
- Step 2 (Top CPU) shows memory-related waits (e.g., RESOURCE_SEMAPHORE)
- ICM mentions "memory", "memory grants", or "memory pressure"
- Investigating memory-related performance issues

**Output Rule**: Only include this section if memory-intensive queries are detected.

---

### Step 6: Top Reads/Writes Queries (Conditional)
**References**: 
- [top-reads-queries.md](references/top-reads-queries.md)
- [top-writes-queries.md](references/top-writes-queries.md)

Identifies queries performing the most logical reads and writes. Useful for I/O-intensive workload analysis.

**When to run**:
- Step 4 (Wait Queries) shows I/O-related waits (PAGEIOLATCH_*, WRITELOG)
- ICM mentions "I/O", "disk I/O", "reads", or "writes"
- Investigating storage performance issues

**Output Rule**: Only include this section if I/O-intensive queries are detected.

---

### Step 7: Top Log/Tempdb Usage Queries (Conditional)
**References**:
- [top-log-queries.md](references/top-log-queries.md)
- [top-tempdb-usage-queries.md](references/top-tempdb-usage-queries.md)

Identifies queries consuming the most transaction log space or tempdb resources.

**When to run**:
- ICM mentions "log full", "tempdb full", or "transaction log"
- Disk skill detected tempdb or log space issues
- Investigating space-related problems

**Output Rule**: Only include this section if log or tempdb-intensive queries are detected.

---

### Step 8: Long-Running Transactions (Conditional)
**Reference**: [long-running-transactions.md](../Blocking/references/long-running-transactions.md)

Analyzes long-running transactions that may be blocking other operations or holding locks.

**When to run**:
- ICM mentions "blocking", "long-running", "transaction", or "deadlock"
- Step 4 (Wait Queries) shows lock-related waits (LCK_M_*)
- Investigating blocking or lock contention issues

**Output Rule**: Only include this section if long-running transactions are detected.

---

### Step 9: Query-Specific Diagnostics (Conditional)
**Primary Reference**: [specific-query-detail.md](references/specific-query-detail.md)

This is an **orchestrator skill** that provides comprehensive diagnostics for a specific query by invoking the following sub-skills:

| Sub-Skill | Description | Reference |
|-----------|-------------|-----------|
| APRC Plan Regression | Checks for query plan regression and APRC corrections | [APRC SKILL](../APRC/SKILL.md) |
| AntiPattern Analysis | Detects query antipatterns affecting performance | [specific-query-antipattern.md](references/specific-query-antipattern.md) |
| Execution Summary | Success/failure rates and execution counts | [specific-query-execution-summary.md](references/specific-query-execution-summary.md) |
| CPU Usage Analysis | CPU consumption patterns | [specific-query-cpu-usage.md](references/specific-query-cpu-usage.md) |
| Wait Type Summary | Wait types and resource bottlenecks | [specific-query-wait-type-analysis.md](references/specific-query-wait-type-analysis.md) |
| Compilation Statistics | Successful compilation CPU usage | [cpu-usage-of-successful-compilation.md](../Compilation/references/cpu-usage-of-successful-compilation.md) |
| Failed Compilation | Failed compilation events | [failed-compilation-summary.md](../Compilation/references/failed-compilation-summary.md) |

**Additional individual skills** (for targeted analysis):
- [specific-query-memory-usage.md](references/specific-query-memory-usage.md) - Memory grant analysis
- [specific-query-execution-time-vs-wait-time-analysis.md](references/specific-query-execution-time-vs-wait-time-analysis.md) - Execution vs wait breakdown

Provides detailed diagnostics for a specific query hash including plan regression, antipatterns, execution summary, CPU/memory usage, wait analysis, and compilation statistics.

**When to run**:
- User provides a specific query hash (`{query_hash}`)
- Previous steps identified a problematic query that needs detailed analysis
- ICM mentions a specific query or query hash

**Output Rule**: Only include this section if analyzing a specific query.

---

### Step 10: Query Antipattern Detection (Conditional)
**Reference**: [specific-query-antipattern.md](references/specific-query-antipattern.md)

Detects common query antipatterns that lead to performance issues (e.g., implicit conversions, scans on large tables, parameter sniffing).

**When to run**:
- Step 2 (Top CPU) or Step 4 (Wait Queries) identified problematic queries
- Investigating query design or optimization opportunities
- ICM mentions "query optimization" or "performance tuning"

**Output Rule**: Only include this section if antipatterns are detected.

---

### Step 11: Query Execution CPU Analysis (Conditional)
**Reference**: [query-execution-cpu-analysis.md](references/query-execution-cpu-analysis.md)

Analyzes CPU consumption during query execution phases to identify CPU hotspots.

**When to run**:
- Step 2 (Top CPU) identified high CPU queries
- Need deeper analysis of query execution CPU patterns
- ICM mentions "query execution" or "compilation CPU"

**Output Rule**: Only include this section if CPU execution issues are detected.

---

## Execution Workflow

### Task 1: Obtain Kusto Cluster Information
**CRITICAL:** Always identify the correct cluster - do NOT use default clusters

Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../../Common/execute-kusto-query/references/getKustoClusterDetails.md](../../Common/execute-kusto-query/references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Obtain Database Metadata
**Action**: Use the [appnameandnodeinfo skill](../../Common/appnameandnodeinfo/SKILL.md) to retrieve database configuration variables including AppName, NodeName, and time range information.

### Task 3: Execute Query Performance Checks

**Default Checks (ALWAYS RUN)**:
Execute these checks in every investigation:
1. **Overall Top Queries Analysis** (Step 1) ⭐
2. **Top CPU Queries** (Step 2) ⭐
3. **Failed Query Execution Summary** (Step 3) ⭐
4. **Top Wait Queries** (Step 4) ⭐

**Conditional Checks (RUN WHEN RELEVANT)**:
Execute these based on findings from default checks or ICM keywords:
5. **Top Memory Queries** (Step 5) - If memory pressure or RESOURCE_SEMAPHORE waits detected
6. **Top Reads/Writes Queries** (Step 6) - If I/O waits (PAGEIOLATCH, WRITELOG) detected
7. **Top Log/Tempdb Usage** (Step 7) - If space issues or ICM mentions log/tempdb
8. **Long-Running Transactions** (Step 8) - If blocking or LCK_M_* waits detected
9. **Query-Specific Diagnostics** (Step 9) - If query hash provided or problematic query identified
10. **Query Antipattern Detection** (Step 10) - If optimization opportunities needed
11. **Query Execution CPU Analysis** (Step 11) - If deep CPU analysis needed

**Output Filtering Rule**: 
- Run each diagnostic check
- Only display results if issues are found (🚩)
- Skip displaying sections with no findings (✅)

### Task 4: Summary
After executing all checks, provide a brief summary:
- List which query issues were detected (if any)
- Identify top resource-consuming queries with query hashes
- Provide recommendations for query optimization or further investigation
- If no issues found, state that clearly

## Output Format

```markdown
## 🔍 Query Performance Analysis

### Summary
[Brief overview of query performance findings]

### [Check Name - only if issue detected]
[Results from the diagnostic check]
🚩 [Issue description]
**Top Query Hash**: `0x...`
[Query details and resource consumption]

### Recommendations
[Actionable next steps for query optimization]
```

## Related Skills

This skill complements other performance diagnostics:
- **CPU**: For overall CPU analysis (query execution is a subset)
- **memory**: For memory pressure issues affecting queries
- **out-of-disk**: For storage space issues (tempdb, log)
- **QDS**: For Query Store readonly issues affecting query statistics
- **APRC**: For automatic plan correction and regressions
- **Compilation**: For query compilation issues

## Notes

- This skill has **4 default checks** that ALWAYS run: overall top queries, top CPU queries, failed queries, and top wait queries
- **7 conditional checks** run based on findings or ICM keywords
- Query hashes are the key identifier for tracking specific queries
- Follow the output filtering rule strictly to keep reports focused on actionable findings
- If a specific query hash is provided, prioritize query-specific diagnostics
- Multiple query issues may be related (e.g., high CPU query causing waits for other queries)
