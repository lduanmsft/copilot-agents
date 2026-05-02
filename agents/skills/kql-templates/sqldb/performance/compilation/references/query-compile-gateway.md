---
name: query-compile-gateway
description: Detect and analyze query compilation waiting for gateway resources
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Query Compile Gateway Detection

## Skill Overview

This skill detects query compilation waiting for gateway resources in Azure SQL Database. SQL Server uses compile gateways (MSR gateways) to control memory consumption during query compilation. When queries wait for gateway resources, it indicates one of two cases:

1. **Complex queries requiring significant memory** - There are complex queries (or multiple queries) that need significant memory to compile (e.g., queries with many joins, large IN lists, or complex expressions)
2. **Memory pressure during compilation** - The system is experiencing memory pressure during the compilation phase, limiting available compilation resources

Either condition can lead to query execution delays as queries queue up waiting for compilation resources.

## Compile Gateway Severity Levels

| Severity Level | Max Waiter Count | Impact Description |
|----------------|------------------|-------------------|
| Minor | 1 - 5 | Minor gateway contention, may require investigation if concerning |
| Moderate | 6 - 20 | Noticeable compilation delays detected |
| Significant | 21 - 50 | Compilation bottleneck, may cause query latency |
| Severe | > 50 | High compilation contention |

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

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where message has_cs 'Gateway' and message has_cs 'MSR-'
| extend name = extract('(.*)Value', 1, message, typeof(string))
| extend max_count = extract('Configured Units[ ]+([0-9]+)', 1, message, typeof(int))
| extend available_count = extract('Available Units[ ]+([0-9]+)', 1, message, typeof(int))
| extend active_count = extract('Acquires[ ]+([0-9]+)', 1, message, typeof(int))
| extend waiter_count = extract('Waiters[ ]+([0-9]+)', 1, message, typeof(int))
| extend threshold_mb = round(extract('Threshold[ ]+([0-9]+)', 1, message, typeof(long)) / 1024.0 / 1024, 1)
| where active_count > 0 and waiter_count > 0
| summarize max_max_count = max(max_count), max_waiter_count = max(waiter_count), max_active_count = max(active_count), min_originalEventTimestamp = min(originalEventTimestamp), max_originalEventTimestamp = max(originalEventTimestamp)
 by CompileGatewayName = name, NodeName
```

### Task 2 Output

| Column | Type | Description | Output Column Name |
|--------|------|-------------|-------------------|
| `CompileGatewayName` | string | Name of the compile gateway (e.g., "Small Gateway (SloSharedPool1)") | Gateway Name |
| `NodeName` | string | The database node where contention was detected | Node |
| `max_max_count` | int | Maximum configured units for this gateway | Max Config Units |
| `max_waiter_count` | int | Maximum number of queries waiting for gateway resources. Use to determine severity per the [Compile Gateway Severity Levels](#compile-gateway-severity-levels) table | Max Waiters |
| `max_active_count` | int | Maximum number of active compilation units | Max Active |
| `min_originalEventTimestamp` | datetime | Start of the contention period | Time Range (start) |
| `max_originalEventTimestamp` | datetime | End of the contention period | Time Range (end) |

> **Note**: When presenting results, combine `min_originalEventTimestamp` and `max_originalEventTimestamp` into a single "Time Range" column formatted as `YYYY-MM-DD HH:MM - YYYY-MM-DD HH:MM`.

- **Results returned** → Gateway contention detected
- **No results** → No gateway contention during the investigation period

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Gateway Contention is Detected

```markdown
## Query Compilation Gateway Analysis Results

**Yes, query compilation was waiting for gateway resources during the investigation period.**

### Gateway Contention Summary

| Gateway Name | Node | Max Config Units | Max Waiters | Max Active | Severity | Time Range |
|-------------|------|-----------------|-------------|------------|----------|------------|
| Small Gateway (SloSharedPool1) | _DB_39 | 128 | **1095** | 128 | 🚩 **Severe** | 2026-03-12 22:10 - 2026-03-13 00:25 |
| Medium Gateway (SloSharedPool1) | _DB_39 | 32 | **45** | 32 | 🚩 **Significant** | 2026-03-12 22:10 - 2026-03-12 23:59 |

### Analysis

1. **Small Gateway** - Up to **1095 waiters** with all 128 units active (fully saturated). This is **severe contention** (>50 waiters) lasting ~2 hours.

2. **Medium Gateway** - Up to **45 waiters** with all 32 units active. This is **significant contention** (21-50 waiters).

### Root Cause Indicators

This pattern suggests:
- **Complex queries requiring significant compilation memory** - Many queries needed gateway resources simultaneously
- **Compilation bottleneck** - Gateway resources were completely saturated, causing significant queuing
- **Impact period**: The worst contention occurred between 22:10 and 00:25 UTC on March 12-13

### Recommendations

1. **Query optimization** - Review queries running during this period for excessive complexity (many joins, large IN lists, complex expressions)
2. **Workload distribution** - Consider spreading query execution to reduce concurrent compilation load
3. **Query store analysis** - Check query store for queries with high compilation times during this window
```

### When No Gateway Contention is Detected

```markdown
## Query Compilation Gateway Analysis Results

**No, query compilation was NOT waiting for gateway resources during the investigation period.**

The query returned no results, indicating that during the specified time range:
- No compile gateway contention was detected
- Queries were compiling without waiting for gateway resources
- This rules out compilation memory pressure as a root cause
```

### Output Format Requirements

1. **Always start with a direct answer** - State clearly whether gateway contention was detected
2. **Use the severity table** - Map max waiter counts to severity levels from the Compile Gateway Severity Levels section
3. **Include a summary table** - Present all detected gateways with their metrics
4. **Provide analysis** - Explain what the numbers mean in context
5. **Add recommendations** - Give actionable next steps based on findings
6. **Use 🚩 emoji** - Flag severe or significant contention for visibility
