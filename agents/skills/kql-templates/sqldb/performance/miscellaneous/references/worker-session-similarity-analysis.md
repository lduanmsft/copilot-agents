---
name: worker-session-similarity-analysis
description: Compare patterns between worker threads usage and sessions usage to identify if session growth is causing worker thread increases.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Worker Session Similarity Analysis

## Skill Overview

This skill compares the pattern similarity between worker threads usage and sessions usage using cosine similarity. A high similarity (>0.9) indicates that the increased number of worker threads may be caused by sessions spawned by user applications.

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
let SimilarityMessage=(similarity: real)
{
let highSimilarityMessage="The pattern of worker threads and sessions is very similar. The increased number of worker threads may be caused by sessions spawned by user applications. Please review the ASC Report 'Database Resource Consumption Statistics' to confirm.";
let noCorrelationMessage="No correlation between worker threads and session spike has been detected.";
iif(similarity > 0.9, highSimilarityMessage, noCorrelationMessage)
};
MonDmRealTimeResourceStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize Max_Worker = max(max_worker_percent), Max_Session = max(max_session_percent) by bin(originalEventTimestamp, 15s)
| sort by originalEventTimestamp asc nulls last
| summarize workers=make_list(Max_Worker),sessions=make_list(Max_Session)
| extend similarity = series_cosine_similarity(workers, sessions)
| extend resultMessage=SimilarityMessage(similarity)
| project resultMessage, similarity, IssueDetected=similarity > 0.9
```

#### Output
Follow these instructions exactly. Only display output when specified:

1. Display the exact message from `resultMessage` without any modification
2. Display the similarity value (e.g., "Cosine similarity: 0.95")

3. **If `IssueDetected` is `true`**: 
   - Recommend reviewing the ASC Report 'Database Resource Consumption Statistics' to confirm the correlation

