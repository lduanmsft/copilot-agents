---
name: blocking-detection
description: Detect and analyze blocking
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Peak Blocking Detection

## Skill Overview

This skill detects and analyzes blocking conditions at peak hours in Azure SQL Database. It queries the MonBlockedProcessReportFiltered table to identify the worst blocking scenario during the investigation period, calculating the percentage of blocked sessions relative to the database's worker thread capacity. The skill categorizes blocking severity from small to extremely severe based on the percentage of blocked sessions.

## Blocking Severity Levels

| Severity Level | Blockee Session % | Impact Description |
|----------------|-------------------|-------------------|
| Small | ≤ 1% | Minor blocking, may require investigation if concerning |
| Moderate | 1% - 2% | Noticeable blocking detected |
| Massive | 2% - 10% | May cause query slowness, timeouts, and deadlocks |
| Severe | 10% - 30% | Significant performance degradation, CPU usage may decrease |
| Extremely Severe | > 30% | Risk of worker thread exhaustion, system stability impacted |

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
| Task 2 | Blocking Events Distribution (Hourly) | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let BlockingStatus = (blockeeSessionPercent: real) {
    case(
    blockeeSessionPercent <= 1, "Small blocking detected, and You may run the skill 'Lead Blocker Sessions' to get more details if the blocking is a concern.",
    blockeeSessionPercent > 1 and blockeeSessionPercent <= 2, "Moderate blocking detected.",
    blockeeSessionPercent > 2 and blockeeSessionPercent <= 10, "Massive blocking detected. Please note that this condition may lead to noticeable performance issues, including but not limited to query slowness, timeouts, and deadlocks.",
    blockeeSessionPercent > 10 and blockeeSessionPercent <= 30, "Severe blocking detected! Please note that this condition may result in significant performance degradation, including but not limited to query slowness, timeouts, deadlocks and CPU usage decreasing.",
    "Extremely severe blocking detected! Please note that this condition may lead to worker thread exhaustion, potentially impacting system stability."
    )
    };
let WorkersLimitPerDB=(MonDmDbResourceGovernance
| where PreciseTimeStamp>datetime_add('day',-2,datetime({StartTime})) and PreciseTimeStamp<datetime_add('day',2,datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and database_name  =~ '{LogicalDatabaseName}'
| extend WorkersLimitPerDB = primary_group_max_workers
| extend WorkersLimitPerPool = primary_pool_max_workers
| summarize  WorkersLimitPerPool = take_any(WorkersLimitPerPool), WorkersLimitPerDB = take_any(WorkersLimitPerDB) by AppName
| project WorkersLimitPerDB  ,AppName);
MonBlockedProcessReportFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| extend monitorLoop = extract('monitorLoop=\x22([0-9]+)\x22',1,blocked_process_filtered, typeof(int))
| parse blocked_process_filtered with anystr3:string '<blocked-process>' blockee '</blocked-process>' discard1
| parse blocked_process_filtered with anystr4:string'<blocking-process>' blocker '</blocking-process>' discard2
| extend blockee_session_id = extract('spid=\x22([0-9]+)\x22', 1, blockee, typeof(int))
| extend blocker_session_id = extract('spid=\x22([0-9]+)\x22', 1, blocker, typeof(int))
| project originalEventTimestamp,monitorLoop,blockee_session_id,blocker_session_id,AppName
| summarize blockees = make_set(blockee_session_id), blockers = make_set(blocker_session_id),timestamp=format_datetime(min(originalEventTimestamp),'yyyy-MM-dd HH:mm:ss') by monitorLoop,AppName
| extend MergedList = array_concat(blockees, blockers)//This will remove duplicated entries
| summarize blockingSessionArray=make_set(MergedList),arg_min(timestamp,blockees) by monitorLoop,AppName
| extend  blockingChainSessionCount= array_length(blockingSessionArray)//the number of sessions involved in blocking, including both blockees and lead blockers
| extend  blockeeSessionCount= array_length(blockees)//the number of blockee session, excluding lead blockers
| where blockeeSessionCount>0//no blocking detected if it's 0.
| project-away blockingSessionArray
| order by blockeeSessionCount desc
| take 1
| join kind=leftouter (WorkersLimitPerDB) on AppName
| extend blockeeSessionPercent = iff(isnull(WorkersLimitPerDB) or WorkersLimitPerDB == 0, real(-1), round(100.0*blockeeSessionCount/WorkersLimitPerDB,1))
| extend IssueDetected = iff(blockeeSessionPercent < 0, true, blockeeSessionPercent > 1)
| extend blockingStatus = iff(blockeeSessionPercent < 0, 
    strcat("Blocking detected but worker thread capacity is unavailable. The peak BLOCKING occurred at ", timestamp, ", ", blockeeSessionCount, " session(s) were blocked. Unable to calculate percentage due to missing resource governance data."),
    strcat(BlockingStatus(blockeeSessionPercent), " The peak BLOCKING occurred at ", timestamp, ", ", blockeeSessionCount, " session(s) were blocked, accounting for ", blockeeSessionPercent, "% of the total capacity(", WorkersLimitPerDB, ")."))
//| project blockingStatus,monitorLoop
```

#### Output

Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:

1. If zero rows are returned, display the exact message: "No blocking was detected during the investigation period."
2. If one or more rows are returned, display the exact message from the `blockingStatus` column without any modifications.


#### Sample Output
### Blocking Status

{blockingStatus message from query result}

| Metric | Value |
|--------|-------|
| Severity Level | **{Small/Moderate/Massive/Severe/Extremely Severe}** |
| Peak Blocked Sessions | {blockeeSessionCount} |
| Worker Thread Capacity | {WorkersLimitPerDB} |
| Blocked Session % | {blockeeSessionPercent}% |
| monitorLoop | {monitorLoop} |


### Task 2: Blocking Events Distribution (Hourly)

**Purpose**: Show the hourly distribution of blocking events to identify patterns and peak blocking times.

**Action**: Execute the Kusto query below, run the "[appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md)" if variables in the kusto query are not available:

```kql
MonBlockedProcessReportFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize BlockingEventCount=count() by bin(originalEventTimestamp, 1h)
| order by originalEventTimestamp asc
```

#### Output

1. Display the hourly blocking event counts as a table.
2. Highlight hours with unusually high blocking event counts (consider top peaks).
3. Look for patterns (e.g., daily spikes at certain hours suggesting scheduled batch jobs).

#### Sample Output


## 📈 Hourly Blocking Distribution

| Hour (UTC) | Events | | Hour (UTC) | Events |
|------------|--------|---|------------|--------|
| Feb 26 00:00 | 13 | | Feb 27 01:00 | **813** 🚩 |
| Feb 26 01:00 | **910** 🚩 | | Feb 27 02:00 | 66 |
| Feb 26 02:00 | 391 | | Feb 27 06:00 | 98 |
| Feb 26 03:00 | 286 | | Feb 27 10:00 | 68 |
| Feb 26 11:00 | 396 | | Feb 27 18:00 | **489** 🚩 |
| Feb 26 20:00 | 142 | | Feb 27 20:00 | 155 |

**Total Events**: ~5,983 blocking events over 2 days

### 🔎 Pattern Analysis

| Peak Hour | Events | Possible Cause |
|-----------|--------|----------------|
| **Feb 26 01:00 UTC** | 910 | Scheduled overnight batch jobs |
| **Feb 27 01:00 UTC** | 813 | Scheduled overnight batch jobs |
| **Feb 27 18:00 UTC** | 489 | Business hours activity |

**Pattern**: Consistent spikes at **01:00 UTC** suggest scheduled batch jobs or maintenance windows.


#### Output Guidelines

1. **Table Format**: Use a two-column side-by-side layout when data spans multiple days for compactness.
2. **Highlighting**: Mark peak hours (top 3-5 by event count) with **bold** and 🚩 emoji.
3. **Total Events**: Sum all blocking events and display the total.
4. **Pattern Analysis**: Create a separate table listing the top 3-5 peak hours with possible causes:
   - Spikes at 00:00-02:00 UTC → "Scheduled overnight batch jobs"
   - Spikes during business hours (08:00-18:00 UTC) → "Business hours activity"
   - Recurring daily patterns → "Scheduled maintenance or batch processing"
5. **Omit Low-Count Hours**: If there are many hours with very low counts (< 10 events), they may be omitted from the display to reduce clutter.

---

### Output Section: Next Steps Hint (Display Only - DO NOT Auto-Execute)

**⚠️ IMPORTANT**: This section is **informational output only**. It provides a hint to the end user about available follow-up actions. **DO NOT automatically invoke** the Lead Blocker Sessions skill. The user must manually request it if needed.

**Purpose**: When blocking is detected, display a recommendation to the user suggesting they can manually run the Lead Blocker Sessions skill for deeper analysis.

#### Display Rules

If blocking was detected (any severity level), **display the following recommendation text** in the output:

#### Recommendation Text Template

```
## 🔍 Next Steps (Manual Action Required)

Blocking was detected during the investigation period. If you need to identify the root cause and the sessions responsible for blocking, you can **manually run** the following skill:

**Available Skill**: `Lead Blocker Sessions`

This skill will:
- Identify the lead blocker session IDs (root of blocking chains)
- Analyze blocking chain hierarchy
- View blocker/blockee session details (client app, wait resources, transaction info)
- Detect if Azure DB system background tasks are involved

**Required Parameter**: `monitorLoop` = {monitorLoop value from peak blocking event above}
```

#### Output Urgency Levels (Text Only)

Adjust the displayed recommendation text based on severity:
- Small (≤1%): "**Optional**: You may run `Lead Blocker Sessions` if the blocking is a concern"
- Moderate/Massive (1-10%): "**Recommended**: Consider running `Lead Blocker Sessions` to identify root cause"
- Severe/Extremely Severe (>10%): "🚩 **Strongly Recommended**: Consider running `Lead Blocker Sessions` to identify the blocking root cause"

#### Sample Output (for Severe blocking)

```
## 🔍 Next Steps (Manual Action Required)

🚩 **Severe blocking detected!** If you need to identify the root cause, you can **manually run**:

**Skill**: `Lead Blocker Sessions`
**Parameter**: `monitorLoop` = 79013 (from peak blocking at 2026-02-27 18:39:34)

This will identify:
- Lead blocker session IDs responsible for the blocking chains
- Blocking chain visualization
- Session details (client app, queries, wait resources)
- Whether Azure DB system tasks are involved
```

**Reminder**: This is a **hint only**. Do not execute Lead Blocker Sessions automatically.

