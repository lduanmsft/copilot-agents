---
name: top-deadlock-queries
description: Display the top N query hashes involved in deadlocks
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Top Deadlock Queries

## Skill Overview

This skill identifies and displays the top query hashes involved in deadlock events in Azure SQL Database. It queries the MonDeadlockReportsFiltered table to extract query hashes and query plan hashes from deadlock XML reports, helping identify the specific queries that are frequently involved in deadlock scenarios.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{TopN}` | Number of deadlock events to analyze | integer | `10` |


## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | Aggregate Query Hash Frequency | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kusto
MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered'
| extend Complete_Deadlock_Graph = trim_end(@'[ \t\r\n]+', xml_report_filtered) endswith '</deadlock>'
| order by Complete_Deadlock_Graph desc nulls last, originalEventTimestamp desc nulls last
| take {TopN}
| extend Complete_Deadlock_Graph = iff(Complete_Deadlock_Graph == 1, 'true', 'false')
| project originalEventTimestamp, xml_report_filtered, NodeName, Complete_Deadlock_Graph
| extend query_hashes = extract_all(@'queryhash=\x22([^\s]+)\x22', xml_report_filtered)
| extend query_plan_hashes = extract_all(@'queryplanhash=\x22([^\s]+)\x22', xml_report_filtered)
// Remove 0x0 hashes and empty sets.
// 0x0 hashes represent frames that don't have a query or execution plan, e.g. exec proc frames inside triggers.
| extend query_hashes = set_difference(query_hashes, dynamic(['0x0000000000000000']))
| extend query_plan_hashes = set_difference(query_plan_hashes, dynamic(['0x0000000000000000']))
| extend query_hashes = iif(array_length(query_hashes) > 0, query_hashes, '')
| extend query_plan_hashes = iif(array_length(query_plan_hashes) > 0, query_plan_hashes, '')
| project originalEventTimestamp, NodeName, Complete_Deadlock_Graph, query_hashes, query_plan_hashes
```

#### Output

Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:

1. If zero rows are returned, display the exact message: "No deadlocks were detected during the investigation period."
2. If rows are returned, display the deadlock events with their associated query hashes in a table format.

#### Sample Output

##### Top Deadlock Queries

| # | Timestamp (UTC) | Query Hashes | Query Plan Hashes | Complete Graph |
|---|-----------------|--------------|-------------------|----------------|
| 1 | 2026-03-10 20:15:32 | `0x1A2B3C4D5E6F7890` | `0x9876543210FEDCBA` | true |
| 2 | 2026-03-10 20:14:18 | `0x2B3C4D5E6F789012`, `0x3C4D5E6F78901234` | `0x8765432109FEDCBA` | true |
| 3 | 2026-03-10 20:12:45 | `0x4D5E6F7890123456` | | false |

---

### Task 2: Aggregate Query Hash Frequency

**Purpose**: Identify which query hashes appear most frequently in deadlocks.

**Action**: Execute the Kusto query below, run the "[appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md)" if variables in the kusto query are not available:

```kusto
MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered'
| extend query_hashes = extract_all(@'queryhash=\x22([^\s]+)\x22', xml_report_filtered)
| extend query_hashes = set_difference(query_hashes, dynamic(['0x0000000000000000']))
| mv-expand query_hash = query_hashes to typeof(string)
| where isnotempty(query_hash)
| summarize DeadlockCount = count(), 
            FirstOccurrence = min(originalEventTimestamp), 
            LastOccurrence = max(originalEventTimestamp) 
    by query_hash
| order by DeadlockCount desc
| take 10
```

#### Output

Display the most frequently occurring query hashes in deadlocks.

#### Sample Output

##### 🔥 Top Query Hashes by Deadlock Frequency

| Rank | Query Hash | Deadlock Count | First Seen | Last Seen |
|------|------------|----------------|------------|-----------|
| 1 | `0x1A2B3C4D5E6F7890` | **847** 🚩 | 2026-03-10 19:49:37 | 2026-03-10 20:40:51 |
| 2 | `0x2B3C4D5E6F789012` | **523** 🚩 | 2026-03-10 19:50:12 | 2026-03-10 20:39:45 |
| 3 | `0x3C4D5E6F78901234` | 312 | 2026-03-10 19:52:08 | 2026-03-10 20:38:22 |
| 4 | `0x4D5E6F7890123456` | 198 | 2026-03-10 20:01:15 | 2026-03-10 20:35:18 |
| 5 | `0x5E6F789012345678` | 87 | 2026-03-10 20:05:33 | 2026-03-10 20:30:42 |

**Total Unique Query Hashes**: 12

#### Output Guidelines

1. **Rank by Frequency**: Order query hashes by the number of times they appear in deadlocks.
2. **Highlighting**: Mark the top 2-3 most frequent query hashes with **bold** and 🚩 emoji.
3. **Time Range**: Show first and last occurrence to indicate the duration of the problem.

---

### Output Section: Next Steps Hint (Display Only - DO NOT Auto-Execute)

**⚠️ IMPORTANT**: This section is **informational output only**. It provides a hint to the end user about available follow-up actions. **DO NOT automatically invoke** any follow-up actions. The user must manually request them if needed.

**Purpose**: When deadlock query hashes are identified, display recommendations to the user for further investigation.

#### Recommendation Text Template

```
## 🔍 Next Steps (Manual Action Required)

Query hashes involved in deadlocks have been identified. To investigate further:

1. **Find Query Text**: Use the query hash to find the actual SQL query text from Query Store or sys.dm_exec_query_stats
2. **Review Execution Plans**: Use the query plan hash to analyze execution plans for optimization opportunities
3. **Check Index Usage**: Verify if the queries have appropriate indexes to minimize lock contention

**Sample Query to Find Query Text** (run in your database):
```sql
SELECT TOP 10 
    qs.query_hash,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1, 
        ((CASE qs.statement_end_offset 
            WHEN -1 THEN DATALENGTH(st.text)
            ELSE qs.statement_end_offset 
        END - qs.statement_start_offset)/2)+1) AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
WHERE qs.query_hash = 0x{query_hash_without_0x_prefix}
```

**💡 Tip**: Deadlocks often occur alongside blocking issues. We also suggest reviewing the blocking status - type `blocking detection` or `blocking status`.
```

---

## Additional Notes

### Understanding Query Hashes

| Field | Description |
|-------|-------------|
| **Query Hash** | A hash value computed from the query text (normalized). Same query hash = same logical query |
| **Query Plan Hash** | A hash value computed from the execution plan. Same plan hash = same execution strategy |
| **0x0000000000000000** | Represents frames without a query, e.g., stored procedure execution frames inside triggers |

### Why Query Hashes are Important

1. **Identify Problematic Queries**: Query hashes help pinpoint specific queries causing deadlocks
2. **Track Across Executions**: Same query executed multiple times will have the same hash
3. **Correlate with Query Store**: Use the hash to find detailed query statistics in Query Store
4. **Plan Analysis**: Query plan hashes help identify if plan changes contributed to deadlocks

### Common Causes for Query Hash Appearing in Deadlocks

1. **Lock Ordering Issues**: Query accesses resources in inconsistent order
2. **Missing Indexes**: Full table scans cause excessive lock escalation
3. **Long-Running Transactions**: Holding locks for extended periods
4. **High Concurrency**: Multiple sessions running the same query simultaneously
