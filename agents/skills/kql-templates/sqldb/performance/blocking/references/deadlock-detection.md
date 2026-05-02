---
name: deadlock-detection
description: Detect and analyze deadlocks
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Deadlock Detection

## Skill Overview

This skill detects and analyzes deadlock conditions in Azure SQL Database. It queries the MonDeadlockReportsFiltered table to identify deadlock occurrences during the investigation period, showing the distribution of deadlocks over time.

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
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | Deadlock Events Distribution (15-minute intervals) | Always |
| Task 3 | Hourly Deadlock Summary | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. 

If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kusto
let DeadlockData = MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered';
let HourlyAvg = toscalar(DeadlockData 
    | summarize count() by bin(originalEventTimestamp, 1h)
    | summarize avg(count_));
DeadlockData
| summarize TotalDeadlocks = count(), 
            FirstDeadlock = min(originalEventTimestamp), 
            LastDeadlock = max(originalEventTimestamp)
| extend HourlyAverage = round(HourlyAvg, 1)
| extend IssueDetected = TotalDeadlocks > 5
```

#### Output

Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:

1. If zero rows are returned OR TotalDeadlocks is 0, display the exact message: "No deadlocks were detected during the investigation period."
2. If deadlocks are found, display the summary table with the metrics.

#### Sample Output

##### Deadlock Status

| Metric | Value |
|--------|-------|
| Severity Level | **{Minimal/Moderate/Significant/Severe/Critical}** |
| Total Deadlocks | {TotalDeadlocks} |
| Hourly Average | {HourlyAverage} |
| First Occurrence | {FirstDeadlock} |
| Last Occurrence | {LastDeadlock} |

---

### Task 2: Deadlock Events Distribution (15-minute intervals)

**Purpose**: Show the distribution of deadlock events to identify patterns and peak deadlock times.

**Action**: Execute the Kusto query below, run the "[appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md)" if variables in the kusto query are not available:

```kusto
let Interval = 15min;
MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered'
| summarize DeadlockCount = count() by bin(originalEventTimestamp, Interval)
| order by originalEventTimestamp asc
```

#### Output

1. Display the deadlock event counts as a table.
2. Highlight time periods with unusually high deadlock counts (consider top peaks).
3. Look for patterns (e.g., spikes at certain times suggesting scheduled jobs or high-concurrency periods).

#### Sample Output

##### 📈 Deadlock Distribution (15-minute intervals)

| Time (UTC) | Deadlocks | | Time (UTC) | Deadlocks |
|------------|-----------|---|------------|-----------|
| Feb 26 00:00 | 2 | | Feb 27 01:00 | **15** 🚩 |
| Feb 26 01:00 | **12** 🚩 | | Feb 27 02:00 | 3 |
| Feb 26 02:00 | 5 | | Feb 27 06:00 | 4 |
| Feb 26 03:00 | 3 | | Feb 27 10:00 | 2 |
| Feb 26 11:00 | 6 | | Feb 27 18:00 | **8** 🚩 |
| Feb 26 20:00 | 4 | | Feb 27 20:00 | 3 |

**Total Deadlocks**: ~67 deadlocks over 2 days

##### 🔎 Pattern Analysis

| Peak Time | Deadlocks | Possible Cause |
|-----------|-----------|----------------|
| **Feb 26 01:00 UTC** | 12 | Scheduled overnight batch jobs with competing transactions |
| **Feb 27 01:00 UTC** | 15 | Scheduled overnight batch jobs with competing transactions |
| **Feb 27 18:00 UTC** | 8 | High business hours concurrency |

**Pattern**: Consistent spikes at **01:00 UTC** suggest concurrent batch jobs accessing overlapping resources.

#### Output Guidelines

1. **Table Format**: Use a two-column side-by-side layout when data spans multiple days for compactness.
2. **Highlighting**: Mark peak periods (top 3-5 by deadlock count) with **bold** and 🚩 emoji.
3. **Total Deadlocks**: Sum all deadlock events and display the total.
4. **Pattern Analysis**: Create a separate table listing the top 3-5 peak times with possible causes:
   - Spikes at 00:00-02:00 UTC → "Scheduled overnight batch jobs with competing transactions"
   - Spikes during business hours (08:00-18:00 UTC) → "High business hours concurrency"
   - Recurring daily patterns → "Scheduled jobs or batch processing with resource contention"
5. **Omit Low-Count Periods**: If there are many periods with zero or very low counts (< 1 deadlock), they may be omitted from the display to reduce clutter.

---

### Task 3: Hourly Deadlock Summary

**Purpose**: Provide a higher-level hourly summary for trend analysis.

**Action**: Execute the Kusto query below, run the "[appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md)" if variables in the kusto query are not available:

```kusto
MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered'
| summarize DeadlockCount = count() by bin(originalEventTimestamp, 1h)
| order by originalEventTimestamp asc
```

#### Output

Display hourly summary only if it provides additional insight beyond the 15-minute distribution.

---

### Output Section: Next Steps Hint (Display Only - DO NOT Auto-Execute)

**⚠️ IMPORTANT**: This section is **informational output only**. It provides a hint to the end user about available follow-up actions. **DO NOT automatically invoke** any follow-up skills. The user must manually request them if needed.

**Purpose**: When deadlocks are detected, display a recommendation to the user suggesting they can investigate further.

#### Display Rules

If deadlocks were detected (any severity level), **display the following recommendation text** in the output:

#### Recommendation Text Template

```
## 🔍 Next Steps (Manual Action Required)

Deadlocks were detected during the investigation period. To investigate further, consider:

1. **Review Deadlock Graphs**: Analyze the XML deadlock reports to understand the resources and queries involved
2. **Identify Patterns**: Look for recurring deadlock victims and common resource contention points
3. **Query Analysis**: Review the queries involved in deadlocks for optimization opportunities

**Common Deadlock Causes**:
- Transactions accessing resources in different orders
- Long-running transactions holding locks
- Missing or suboptimal indexes
- High concurrency on hot spots (frequently accessed rows/pages)

**💡 Tips**:
- Deadlocks often occur alongside blocking issues. We also suggest reviewing the blocking status - you may type `blocking detection` or `blocking status` to run the blocking analysis skill.
- To identify which specific queries are causing deadlocks, you may type `top deadlock queries` to run the skill that shows the most frequently involved query hashes in deadlocks.
```

#### Sample Output (for Significant deadlock activity)

```
## 🔍 Next Steps (Manual Action Required)

🚩 **Significant deadlock activity detected!** To investigate further:

**Common Investigation Steps**:
1. Review deadlock XML reports for resource contention details
2. Identify the queries and tables involved in deadlocks
3. Check for missing indexes on frequently deadlocked tables
4. Review transaction isolation levels and lock hints

**Typical Causes**:
- Transactions accessing tables in different orders
- Long-running transactions holding locks
- Index scans causing excessive lock escalation

**💡 Tips**:
- We also suggest reviewing the blocking status - type `blocking detection` or `blocking status`.
- To identify which queries are causing deadlocks, type `top deadlock queries`.
```

**Reminder**: This is a **hint only**. Do not execute any follow-up analysis automatically.

---

## Additional Notes

### Understanding Deadlocks vs Blocking

| Aspect | Blocking | Deadlock |
|--------|----------|----------|
| Definition | One transaction waits for another to release locks | Circular wait where transactions block each other |
| Resolution | Wait until blocking transaction completes | SQL Server automatically terminates one transaction (victim) |
| Impact | Performance degradation, timeouts | Transaction rollback, application retry required |
| Detection Table | MonBlockedProcessReportFiltered | MonDeadlockReportsFiltered |

### Common Deadlock Prevention Strategies

1. **Access resources in consistent order**: Ensure all transactions access tables in the same order
2. **Keep transactions short**: Minimize the time locks are held
3. **Use appropriate isolation levels**: Consider READ COMMITTED SNAPSHOT or SNAPSHOT isolation
4. **Optimize queries**: Add indexes to reduce lock duration and scope
5. **Implement retry logic**: Application should handle deadlock errors (Error 1205) gracefully
