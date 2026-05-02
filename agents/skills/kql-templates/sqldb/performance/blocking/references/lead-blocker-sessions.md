---
name: lead-blocker-sessions
description: Find the lead blocking header session IDs (root of the blocking chain)
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Lead Blocker Sessions

## Skill Overview

This skill identifies the lead blocker session IDs, which are the root sessions at the head of blocking chains. A lead blocker is a session that blocks other sessions but is not itself blocked by any other session within the same monitor loop.

## Blocking Chain Concept

In a blocking chain:
- `blockee_session_id` is the session that is blocked by another session
- `blocker_session_id` is the session that blocks other sessions
- One `blockee_session_id` maps to exactly one `blocker_session_id` per monitor loop
- One `blocker_session_id` can block multiple different `blockee_session_id` values

**Lead Blocker Definition**: A session ID that appears as a `blocker_session_id` but does NOT appear as a `blockee_session_id` within the same `monitorLoop`.

### Example

| monitorLoop | blockee_session_id | blockee_waittime_ms | blockee_clientapp | blocker_session_id | blocker_status | blocker_clientapp |
|-------------|--------------------|---------------------|-------------------|--------------------|----------------|-------------------|
| 79013 | 1021 | 45951 | axBatch | 1100 | suspended | axBatch |
| 79013 | 1100 | 216297 | axBatch | 657 | suspended | axBatch |
| 79013 | 809 | 45941 | DAMS | 727 | running | axBatch |
| 79013 | 711 | 45950 | axServices | 727 | running | axBatch |
| 79013 | 657 | 216305 | axBatch | 987 | running | axBatch |

**Blocking Chains**:
1. 1021 ← blocked by 1100 ← blocked by 657 ← blocked by 987 (lead blocker: **987**)
2. 809 ← blocked by 727 (lead blocker: **727**)
3. 711 ← blocked by 727 (lead blocker: **727**)

**Total Wait Duration of Lead Blocker**:
1. Total wait time of session id 987= 45951+216297+45951=308199
2. Total wait time of session id 727= 45950+45941=91891

**Lead Blocker Session IDs**: 987, 727

| Lead Blocker | Blocked Sessions Count | Total Wait Duration(ms) |
|--------------|------------------------|-------------------------|
| **987** | 3 | 308199 |
| **727** | 2 | 91891 |

**Blocking Chain Visualization**:
```
987 (LEAD BLOCKER, running)
 └── 657
      └── 1100
           └── 1021

727 (LEAD BLOCKER, running)
 ├── 809
 └── 711
```

## Prerequisites

- Access to Kusto clusters for SQL telemetry
- Prior execution of blocking detection query to identify the relevant `monitorLoop`

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{monitorLoop}` | The specific monitor loop to analyze | int | `79013` |


## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
// Find lead blocker session IDs for a specific monitorLoop
// Lead blockers are sessions that appear as blocker_session_id but NOT as blockee_session_id
MonBlockedProcessReportFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| extend monitorLoop = extract('monitorLoop=\x22([0-9]+)\x22',1,blocked_process_filtered, typeof(int))
| parse blocked_process_filtered with anystr3:string '<blocked-process>' blockee '</blocked-process>' discard1
| parse blocked_process_filtered with anystr4:string'<blocking-process>' blocker '</blocking-process>' discard2
| extend blockee_session_id = extract('spid=\x22([0-9]+)\x22', 1, blockee, typeof(int))
| extend blockee_status = extract('status=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_status = iff(isempty(blockee_status) or isnull(blockee_status), "NULL", blockee_status)
| extend blockee_transactionid = extract('xactid=\x22([0-9]+)\x22', 1, blockee, typeof(long))
| extend blockee_frames = extract(@'\s*<stackFrames>\s*(.*?)\s*</stackFrames>\s*', 1, blockee, typeof(string))
| extend blockee_waittime_ms = extract('waittime=\x22([0-9]+)\x22', 1, blockee, typeof(int))
| extend blockee_transactionname = extract('transactionname=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_clientapp = extract('clientapp=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_clientapp = iff(isempty(blockee_clientapp) or isnull(blockee_clientapp), "NULL", blockee_clientapp)
| extend blockee_trancount = extract('trancount=\x22([0-9]+)\x22', 1, blockee, typeof(int))
| extend blockee_lasttranstarted = extract('lasttranstarted=\x22(.*?)\x22', 1, blockee, typeof(datetime))
| extend blockee_queryhash = extract('queryhash=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_isolationlevel = extract('isolationlevel=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_lastbatchstarted = extract('lastbatchstarted=\x22(.*?)\x22', 1, blockee, typeof(datetime))
| extend blockee_lastbatchcompleted = extract('lastbatchcompleted=\x22(.*?)\x22', 1, blockee, typeof(datetime))
| extend blockee_waitresource = extract('waitresource=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blocker_session_id = extract('spid=\x22([0-9]+)\x22', 1, blocker, typeof(int))
| extend blocker_waitresource = extract('waitresource=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_status = extract('status=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_status = iff(isempty(blocker_status) or isnull(blocker_status), "NULL", blocker_status)
| extend blocker_clientapp = extract('clientapp=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_clientapp = iff(isempty(blocker_clientapp) or isnull(blocker_clientapp), "NULL", blocker_clientapp)
| extend blocker_trancount = extract('trancount=\x22([0-9]+)\x22', 1, blocker, typeof(int))
| extend blocker_transactionid = extract('xactid=\x22([0-9]+)\x22', 1, blocker, typeof(long))
| extend blocker_frames = extract(@'\s*<stackFrames>\s*(.*?)\s*</stackFrames>\s*', 1, blocker, typeof(string))
| extend blocker_queryhash = extract('queryhash=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_isolationlevel = extract('isolationlevel=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_lastbatchstarted = extract('lastbatchstarted=\x22(.*?)\x22', 1, blocker, typeof(datetime))
| extend blocker_lastbatchcompleted = extract('lastbatchcompleted=\x22(.*?)\x22', 1, blocker, typeof(datetime))
| where isnotnull(blocker_session_id) and isnotnull(blockee_session_id)
| where monitorLoop=={monitorLoop}
| summarize arg_max(originalEventTimestamp, blockee_waittime_ms,blockee_transactionid,blockee_isolationlevel,blockee_clientapp,blockee_queryhash,blockee_waitresource,blockee_lastbatchstarted,
blockee_lastbatchcompleted,blocker_waitresource,blocker_transactionid,blocker_trancount, blocker_status,blocker_isolationlevel,blocker_clientapp,blocker_queryhash,blocker_waitresource,blocker_lastbatchstarted,blocker_lastbatchcompleted)
by monitorLoop,blockee_session_id,blocker_session_id
```

#### Output

Please follow the instructions carefully:

1. If zero rows are returned, display the exact message: "No lead blockers found for monitorLoop {monitorLoop}."
2. If one or more rows are returned, display the lead blocker session IDs and count.
3. Store the `lead_blocker_session_ids` for subsequent analysis.

#### Sample Output
```
## Lead Blocker Session IDs: 987, 727

| Lead Blocker | blocker_clientapp | Blocked Sessions Count | Total Wait Duration(ms) |
|--------------|-------------------|------------------------|-------------------------|
| **987** | axBatch | 3 | 308199 |
| **727** | axBatch | 2 | 91891 |

### Blocking Chain Visualization

987 (LEAD BLOCKER, running, axBatch)
 └── 657
      └── 1100
           └── 1021

727 (LEAD BLOCKER, running, axBatch)
 ├── 809
 └── 711

### Blocked Sessions by Client Application

Aggregate the blocked sessions (`blockee_session_id`) by `blockee_clientapp` and calculate total wait time for each client application.

| Client App | Blocked Sessions | Total Wait Time (ms) |
|------------|------------------|---------------------|
| **axBatch** | 3 | 308199 |
| **DAMS** | 1 | 45941 |
| **axServices** | 1 | 45950 |

**Output Guidelines**:
1. Group all `blockee_session_id` records by `blockee_clientapp`
2. Count the number of blocked sessions per client app
3. Sum the `blockee_waittime_ms` for each client app
4. Sort by Total Wait Time descending
5. Bold the client app name with the highest wait time

### Wait Resources

Aggregate the blocked sessions by `blockee_waitresource` to identify which resources are causing the most contention.

| Wait Resource | Sessions Waiting | Total Wait Time (ms) |
|---------------|------------------|---------------------|
| `KEY: 124:281474978938880 (ecffe0db1584)` | 3 | 250000 |
| `OBJECT: 124:2013302282:112` | 2 | 150000 |

**Output Guidelines**:
1. Group all `blockee_session_id` records by `blockee_waitresource`
2. Count the number of sessions waiting on each resource
3. Sum the `blockee_waittime_ms` for each resource
4. Sort by Sessions Waiting descending (or Total Wait Time if preferred)
5. Truncate very long wait resource strings if needed, but keep the key identifiers visible

## Azure DB System Task Detection

Check if `blocker_clientapp` or `blockee_clientapp` contains any of the following: `DmvCollector`, `TdService`, `BackupService`, `MetricsDownloader`, `Background`.

**Note**: A value of `NULL` indicates no client application name was provided in the blocked process report. This is different from Azure DB system tasks which have specific client app names.

- **If found**: Display "🚩 Azure DB System Task detected: {matched_clientapp_name}"
- **If not found**: Display "✅ Azure DB System Tasks are not involved in the blocking chains"
```
