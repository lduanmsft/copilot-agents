## Management Operation Timing

**MANDATORY**: When LoginOutages contains `OutageType = "CustomerInitiated"`, you MUST output a "Management Operation Timing" section **immediately after** the LoginOutages section and **before** the Failover Sequence / Per-Node Timeline sections.

**Section heading**: `## 📊 Management Operation Timing (HA210)`

**The HA210 query already produces one aggregated row per operation.** Copy the query result directly into the table below — no further transformation needed.

**Table format — use the query's original column names directly:**

| OperationType | RequestId | StartTime | EndTime | Duration | Status |
|---------------|-----------|-----------|---------|----------|--------|

- Copy query results directly into the table — no column renaming needed.
- RequestId: **full 36-character GUID — never abbreviate with `...`**.
- If `StartTime` is null, display `—`.
- If `EndTime` is null, display `—` (Duration will already say `In progress`).

**Example:**

```
## 📊 Management Operation Timing (HA210)

| OperationType | RequestId | StartTime | EndTime | Duration | Status |
|---------------|-----------|-----------|---------|----------|--------|
| ResumeContinuousCopy | 6314496D-95B8-4BDE-8CA5-8A6CC11C7DBB | 2026-03-13 11:49:29 | 2026-03-13 14:18:46 | 2h 29m | Success |
| GeoDrTargetReseed | CFB2B45C-B16A-429F-8BBC-45FE179E92A9 | 2026-03-13 14:37:25 | 2026-03-13 16:03:23 | 1h 25m | Success |
```

**Rules:**
- Do NOT re-aggregate, reformat durations, or add raw millisecond values. The query output is final.
- Do NOT truncate RequestId values. Always show the full GUID as returned by the query.
- Do NOT add columns not in the query output.

---

## Failover Sequence

**MANDATORY**: Before the detailed per-node timelines, generate a chronological table of all DeleteReplica and AddPrimary events.

**MANDATORY**: Whenever presenting timestamps in output, always include the date as well, using the format `yyyy-MM-dd HH:mm:ss`.

**Format:**

| Timestamp | Time gap | Primary | Event | Notes |
|-----------|-------------|-------------|-------|-------|
| yyyy-MM-dd HH:mm:ss |           | {NodeName} | DeleteReplica | Delete old primary replica |
| yyyy-MM-dd HH:mm:ss | {TimeGap} | {NodeName} | AddPrimary | Add primary replica attempt #1 |
| yyyy-MM-dd HH:mm:ss | {TimeGap} | {NodeName} | AddPrimary | Add primary replica attempt #2 |

**Instructions:**
- List ALL DeleteReplica events from HA106 query results
- List ALL AddPrimary events from HA107 query results (or HA108 for ZR/BC)
- Sort by timestamp chronologically
- Calculate time gap from previous event and include in Notes column
- Use actual timestamps from query results - DO NOT estimate or create timestamps
- This provides a high-level view of the failover sequence before detailed analysis

**Example:**

### Failover Sequence

Based on WinFabLogs (DeleteReplica and AddPrimary events):

| Timestamp | Time gap | Primary | Event | Notes |
|-----------|-------------|-------------|-------|-------|
| 2025-12-09 07:12:04 |           | _DB_3 | DeleteReplica | Delete old primary replica |
| 2025-12-09 07:12:09 | 5s | _DB_55 | AddPrimary | Add primary replica attempt #1 |
| 2025-12-09 09:01:10 | 1h 49m | _DB_57 | AddPrimary | Add primary replica attempt #2 |

---

## Detailed Per-Node Timeline Analysis

**MANDATORY**: After generating the Failover Sequence table, you MUST generate detailed per-node timeline analysis for EVERY node involved in the failover sequence.

**Requirements:**
- Generate one timeline section per node (old primary, new primary, failed attempts)
- Execute ALL queries listed in SKILL.md Step 6 for EACH node
- Print events in chronological order with timestamps from query results
- Calculate time gaps between consecutive events
- Include warnings section after each node's timeline
- Use the exact format shown below

**Example Format:**

Below is an example for an incident that had the following two failovers:
- **Failover #1**: 2025-12-09 07:12:04 → 2025-12-09 07:12:09 - _DB_3 → _DB_55 - FAILED
- **Failover #2**: 2025-12-09 09:01:10 → 2025-12-09 09:04:52 - _DB_55 → _DB_57 - SUCCESS

**Node header format:**
- Use `Primary Replica on {NodeName}` for all nodes


### Primary Replica on _DB_3 [Old Primary - Deleted]

**Time Window**: Process 91776 ended at 2025-12-09 07:11:52, new Process 231868 started at 2025-12-09 07:12:29

| Time (UTC)          | Time Gap  | Event                                                          | Query  |
|---------------------|-----------|----------------------------------------------------------------|--------|
| 2025-12-09 06:49:17 |           | Node status changed to "Disabling" (health still Ok)           |        |
| 2025-12-09 07:12:04 | 22m 47s   | DeleteReplica                                                  | HA106  |
| 2025-12-09 07:12:29 |     25s   | SQL Process Started (Process ID: 231868) [Estimated from telemetry] |  |
| 2025-12-09 07:12:32 |      3s   | Tempdb Recovery completed                                      | HA2010 |
| 2025-12-09 07:12:33 |      1s   | SQL Server ready for client connections                        | HA2020 |
| 2025-12-09 07:12:33 |      0s   | CFabricReplicaManager Registered service types                 | HA2030 |
| 2025-12-09 07:12:34 |      1s   | Process 231868 ended (only lasted 30 seconds)                  |        |
| 2025-12-09 07:27:16 | 14m 42s   | Node health degraded to "Warning"                              |        |
| 2025-12-09 07:45:24 | 18m 08s   | Node health dropped to "Error", node went "Down"               |        |
| 2025-12-09 07:57:17 | 11m 53s   | Node status changed to "Disabled"                              |        |
| 2025-12-09 08:12:17 | 15m 00s   | Node came back "Up"                                            |        |

🚩 **Major Issues:**
- Node was stuck in "Disabling" state for ~56 minutes before being deleted
- Node health progressively degraded: Ok → Warning → Error/Down
- New SQL process (231868) only lasted 30 seconds after the DeleteReplica event

---

### Primary Replica on _DB_55 [Failed Attempt - Script Upgrade Mode]

**Time Window**: 2025-12-09 07:12:09 (AddPrimary) to 2025-12-09 09:01:10 (next AddPrimary)

| Time (UTC)          | Time Gap  | Event                                                          | Query  |
|---------------------|-----------|----------------------------------------------------------------|--------|
| 2025-12-09 06:47:39 |           | 🚩 Error 18401 started (BEFORE failover): "Server is in script upgrade mode" |       |
| 2025-12-09 07:12:09 | 24m 30s | AddPrimary                                                     | HA107  |
| 2025-12-09 07:17:37 |  5m 28s   | Tempdb Recovery completed                                      | HA2010 |
| 2025-12-09 07:57:22 | 44m 45s | SQL Server ready for client connections                        | HA2020 |
| 2025-12-09 07:57:22 |      0s   | CFabricReplicaManager Registered service types                 | HA2030 |
| 2025-12-09 07:57:27 |      5s   | hadr_fabric_api_factory_create_replica [Detected: No event found] |    |
| 2025-12-09 07:57:12 |           | 🚩 Last Error 18401 occurrence (408 total occurrences from 2025-12-09 06:47:00 - 2025-12-09 07:57:00) |  |
| 2025-12-09 07:57:28 |      1s   | hadr_fabric_api_replicator_begin_change_role, new_role_desc: PRIMARY | HA5005 |
| 2025-12-09 07:57:28 |      0s   | Write Status changed to RECONFIGURATION_PENDING                | HA400  |
|                     |           | ❌ **No User Database Recovery completed**                     |        |
|                     |           | ❌ **No GRANTED write status** - stuck at RECONFIGURATION_PENDING | HA400 |
| 2025-12-09 08:53:41 | 56m 13s | Process 48712 telemetry ended                                  |       |


🚩 **Major ISSUE - Stuck in Script Upgrade Mode:**
- Error 18401 occurred 408 times between 2025-12-09 06:47:39 and 2025-12-09 07:57:12
- SQL was in script upgrade mode BEFORE the failover to this node
- Achieved RECONFIGURATION_PENDING but NEVER achieved GRANTED write status
- User database (9EB40E0E-2609-4060-8468-E92CB0287D75) never completed recovery
- This node was unusable for almost 2 hours, causing extended outage

🚩 **Timeline Delays:**
- AddPrimary to Tempdb Recovery: **5min 28sec** (slow)
- Tempdb Recovery to SQL Ready: **39min 45sec** (extremely slow)
- SQL Ready to Role Change: **6 seconds** (normal)
- Never achieved database recovery or write GRANTED

---

### Primary Replica on _DB_57 [Successful]

**Time Window**: 2025-12-09 09:01:10 (AddPrimary) to end of outage

| Time (UTC)          | Time Gap  | Event                                                          | Query  |
|---------------------|-----------|----------------------------------------------------------------|--------|
| 2025-12-09 09:01:10 |           | AddPrimary                                                     | HA107  |
| 2025-12-09 09:02:28 |  1m 18s   | SQL Process Started (Process ID: 180836) [Estimated from telemetry] |    |
| 2025-12-09 09:02:32 |      4s   | Tempdb Recovery completed                                      | HA2010 |
| 2025-12-09 09:02:33 |      1s   | SQL Server ready for client connections                        | HA2020 |
| 2025-12-09 09:02:33 |      0s   | CFabricReplicaManager Registered service types                 | HA2030 |
| 2025-12-09 09:02:37 |      4s   | hadr_fabric_api_factory_create_replica [No event in result - estimated] |  |
| 2025-12-09 09:02:43 |      6s   | hadr_fabric_api_replicator_begin_change_role, new_role_desc: PRIMARY | HA5005 |
| 2025-12-09 09:02:44 |      1s   | Write Status changed to RECONFIGURATION_PENDING                | HA400  |
| 2025-12-09 09:04:08 |  1m 24s   | Recovery completed for database 9EB40E0E-2609-4060-8468-E92CB0287D75 | HA4020 |
| 2025-12-09 09:04:52 |     44s   | ✅ Write Status changed to GRANTED                             | HA400  |

✅ **Successful Failover:**
- AddPrimary to Tempdb Recovery: **1min 18sec** (normal)
- Tempdb Recovery to SQL Ready: **1 second** (excellent)
- SQL Ready to Role Change: **10 seconds** (normal)
- Role Change to Database Recovery: **1min 24sec** (normal)
- Database Recovery to Write GRANTED: **44 seconds** (normal)
- **Total time from AddPrimary to Write GRANTED: 3min 38sec** ✅

---

## Summary of Findings

### Root Cause Chain

1. **Initial Trigger**: Node _DB_3 started degrading at 2025-12-09 06:49:17, stuck in "Disabling" for 56 minutes
2. **First Failover Attempt Failed** (2025-12-09 07:12:04 → 2025-12-09 07:12:09):
   - Service Fabric deleted _DB_3 and added primary to _DB_55
   - **Critical Error**: _DB_55 was already in Error 18401 (script upgrade mode) since 2025-12-09 06:47:39
   - _DB_55 never achieved write GRANTED status
   - Extended outage by ~2 hours
3. **Second Failover Succeeded** (2025-12-09 09:01:10 → 2025-12-09 09:04:52):
   - Failover to _DB_57 completed successfully
   - Write GRANTED achieved at 2025-12-09 09:04:52
   - **Outage ended**

### Key Performance Metrics

| Node    | AddPrimary → SQL Ready | SQL Ready → Write GRANTED | Total Failover Time | Status        |
|---------|------------------------|---------------------------|---------------------|---------------|
| _DB_3   | N/A (old primary)      | N/A                       | N/A                 | Deleted       |
| _DB_55  | **~45 minutes** 🚩     | **Never achieved** ❌      | Failed              | Stuck Error 18401 |
| _DB_57  | **~1min 23sec** ✅      | **2min 19sec** (total time including intermediate steps) ✅ | **3min 42sec** ✅    | Success       |


## Impact Timeline
**Total Outage Duration**: ~2 hours 20 minutes (2025-12-09 07:10:00 - 2025-12-09 09:30:00)

| Failover# | Old Primary | New Primary |  StartTime    |  EndTime      | Duration | Major Issues |
|-----------|-------------|-------------|---------------------|---------------------|----------|--------------|
| 1  ❌    | _DB_3       | _DB_55      | 2025-12-09 07:12:04 | 2025-12-09 09:01:10 | 1h 49m   | Error 18401  |
| 2  ✅    | _DB_55      | _DB_57      | 2025-12-09 09:01:10 | 2025-12-09 09:04:52 |     3m 42s   |              |


### Mitigation
The second failover to _DB_57 succeeded. _DB_57 achieved GRANTED write status at 2025-12-09 09:04:52
