---
name: specific-query-detail
description: Display the details of a specific query by invoking multiple diagnostic sub-skills
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Detail of Specific Query

## Skill Overview

This skill provides comprehensive details about a specific query by orchestrating multiple diagnostic sub-skills. It analyzes plan regression, antipatterns, execution summary, CPU usage and wait types for the specified query.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | The query hash to analyze (provide this OR query_id) | string | `0x73E64DD291EBBF6E` |
| `{query_id}` | The query ID to analyze (provide this OR query_hash) | long | `12345` |


## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Invoke the following sub-skills | Always |

## Execution Steps

### Task 1: Invoke the following sub-skills

Execute each sub-skill with the parameters collected above. Present results from each sub-skill in separate sections.

#### 2. APRC Plan Regression Analysis
**Skill**: [APRC](../../aprc/SKILL.md)

Detects if the query has experienced plan regression and if Automatic Plan Regression Correction (APRC) has taken action.

---

#### 2. Query AntiPattern Analysis
**Skill**: [Query AntiPattern Analysis](./specific-query-antipattern.md)

Checks if the query has any detected AntiPatterns that may degrade performance.

**⚠️ WARNING**: This sub-skill does NOT support `query_id`. If the caller provided `query_id` instead of `query_hash`, **skip this sub-skill** and display the following message in the output:
> "AntiPattern analysis skipped: The specific-query-antipattern skill requires query_hash and does not support query_id."

---

#### 2. Query Execution Summary
**Skill**: [Specific Query Execution Summary](./specific-query-execution-summary.md)

Retrieves execution statistics including success/failure rates and total execution count.

---

#### 2. CPU Usage of Query Analysis
**Skill**: [CPU Usage of Specific Query](./specific-query-cpu-usage.md)

Analyzes CPU consumption patterns for the specific query.

---

#### 2. CPU Usage Over Time Analysis
**Skill**: [CPU Usage Over Time of Specific Query](./specific-query-cpu-usage-over-time.md)

Displays the CPU usage of the specific query over time at 15-minute intervals to identify CPU consumption patterns and spikes.

---

#### 2. Memory Usage of Query Analysis
**Skill**: [Memory Usage of Specific Query](./specific-query-memory-usage.md)

Analyzes memory grant patterns for the specific query to identify excessive memory consumption.

---

#### 2. Execution Time vs Wait Time Analysis
**Skill**: [Specific Query Execution Time vs Wait Time Analysis](./specific-query-execution-time-vs-wait-time-analysis.md)

Compares the ratio of elapsed time to CPU time to determine if the query is waiting on resources or being blocked rather than actively running.

---

#### 2. Query Wait Type Summary
**Skill**: [Specific Query Wait Type Analysis](./specific-query-wait-type-analysis.md)

Identifies the wait types associated with query execution to understand resource bottlenecks.

---


## Output

Present results from each sub-skill in the following format:

### 📊 Query Detail Summary for `{query_hash}` or `{query_id}`

#### 1. Plan Regression Analysis
[Results from sub-skill 3.1]

#### 2. AntiPattern Analysis
[Results from sub-skill 3.2]

#### 3. Execution Summary
[Results from sub-skill 3.3]

#### 4. CPU Usage Analysis
[Results from sub-skill 3.4]

#### 5. CPU Usage Over Time
[Results from sub-skill 3.5]

#### 6. Memory Usage Analysis
[Results from sub-skill 3.6]

#### 7. Execution Time vs Wait Time Analysis
[Results from sub-skill 3.7]

#### 8. Wait Type Summary
[Results from sub-skill 3.8]


---

**Note**: Query text is not available in Kusto telemetry. To retrieve the query SQL text, query the database directly:
```sql
SELECT qt.query_sql_text, q.query_id
FROM sys.query_store_query_text qt
JOIN sys.query_store_query q ON qt.query_text_id = q.query_text_id
WHERE q.query_hash = {query_hash}
```
