# Kusto Queries for Long Reconfiguration Database Debugging

!!!AI Generated. To be verified!!!

## Query Parameter Placeholders

Replace these placeholders with actual values when running queries:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp in UTC
- `{Duration}`: Time duration (e.g., `1h`, `101m`, `24h`)

**Resource identifiers:**
- `{AppName}`: Application name (e.g., `fabric:/sterling-dpseastus2-lnxsqlmi02/Sterling.User.c7c3b2a1-...`)
- `{PartitionId}`: Service Fabric partition ID (GUID)
- `{ClusterName}`: Service Fabric cluster name (from `tenant_ring_name`)
- `{NodeName}`: Fabric node name
- `{physical_database_id}`: Physical database ID (GUID)
- `{LogicalDatabaseName}`: Logical database name used in management operations
- `{LogicalServerName}`: Logical server name used in seeding progress tracking

---

## Step 1: Confirm Issue Is Active

### LR100 - Check Active Long Reconfiguration Alert

**Purpose:** Verify whether the long reconfiguration alert is still active or has self-healed.

**What to look for:**
- If the latest timestamp is recent, the issue is still active
- If the latest timestamp is before the current time with no new events, the issue has self-healed
- Check the `Description` field for details on the affected partition

```kql
AlrWinFabHealthPartitionEvent
| where ServiceName contains "{AppName}"
| where Description contains "Partition reconfiguration is taking longer than expected."
| project TIMESTAMP, ClusterName, ApplicationName, ServiceName, PartitionId, Description
| summarize max(TIMESTAMP) by ClusterName, ApplicationName, ServiceName, PartitionId, Description
```

**Expected output:**
- `TIMESTAMP`: Last time the alert was observed
- `ClusterName`: Cluster where the issue occurred
- `PartitionId`: Affected partition

---

## Step 2: Identify Specific Case

### LR200 - Case 1: Error 41614 State 27 (GP Only)

**Purpose:** Check if quorum catchup is failing with ERR_STATE_HADR_DB_MGR_DOES_NOT_EXIST (GP instances only).

**What to look for:**
- Non-zero count indicates this is the root cause
- Check which nodes are affected
- 🚩 If present, mitigation is to kill old primary (then new primary if needed)

```kql
MonFabricApi
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where error_code == long(41614)
| where error_state == long(27)
| summarize count() by NodeName
```

**Expected output:**
- `NodeName`: Node where the error occurred
- `count_`: Number of error occurrences

---

### LR210 - Case 2: Inconsistent Remote Replicas (Error 5120)

**Purpose:** Check for inconsistent remote replicas (Error 5120, Severity 16, State 5).

**What to look for:**
- Any rows returned indicate inconsistent remote replicas
- Check the `message` field for detailed error information
- 🚩 If present, follow TSGCL0069.2 or TSGCL0069.1

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where error_id == 5120
| summarize count(), min(TIMESTAMP), max(TIMESTAMP), any(message)
```

**Expected output:**
- `count_`: Number of occurrences
- `min_TIMESTAMP` / `max_TIMESTAMP`: Time range of the error
- `any_message`: Sample error message

---

### LR220 - Case 3: Error 5173 - File Metadata Mismatch

**Purpose:** Check for file metadata discrepancy between GeoSecondary and GeoPrimary.

**What to look for:**
- Any rows indicate file metadata mismatch
- Error message: "One or more files do not match the primary file of the database..."
- 🚩 If present, reseed GeoSecondary (SOPCL00104.3) then follow TSGCL0069.1

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where error_id == 5173
| summarize count(), min(TIMESTAMP), max(TIMESTAMP), any(message)
```

**Expected output:**
- `count_`: Number of occurrences
- `any_message`: Detailed error message

---

### LR230 - Case 4: Long Running Checkpoint (Start)

**Purpose:** Check for checkpoint start events to identify long running checkpoints.

**What to look for:**
- Compare results with LR231 (checkpoint finish) — if start exists without a corresponding finish, checkpoint is stuck
- Note the `NodeName` where checkpoint started

```kql
MonFabricDebug
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where partition_id =~ "{PartitionId}"
| where debug_trace has "HaDrDbMgr::CheckpointDBInternal: Starting checkpoint"
| project TIMESTAMP, debug_trace, NodeName
```

**Expected output:**
- `TIMESTAMP`: When checkpoint started
- `NodeName`: Node where checkpoint is running
- `debug_trace`: Full trace message

---

### LR231 - Case 4: Long Running Checkpoint (Finish)

**Purpose:** Check for checkpoint finish events. Compare with LR230 to determine if checkpoint completed.

**What to look for:**
- If LR230 has results but LR231 does not, the checkpoint is stuck
- If LR231 has results after mitigation time only, the checkpoint was long running but completed after intervention
- 🚩 If stuck: Take dump, then kill primary SQL process

```kql
MonFabricDebug
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where partition_id =~ "{PartitionId}"
| where debug_trace has "HaDrDbMgr::CheckpointDBInternal: Finished checkpoint"
| project TIMESTAMP, debug_trace, NodeName
```

**Expected output:**
- `TIMESTAMP`: When checkpoint finished
- `NodeName`: Node where checkpoint completed

---

### LR240 - Case 5: Instance Boot Deadlock

**Purpose:** Check for instance boot deadlock where sessions hold replication master locks.

**What to look for:**
- Results containing "Waiting" indicate an active deadlock
- 🚩 If present, kill the stuck SQL process

```kql
MonSQLSystemHealth
| where TIMESTAMP > ago(1d)
| where AppTypeName =~ "Worker.CL"
| where AppName =~ "{AppName}"
| where message contains "HaDrDbMgr::DelayKillingSessionsHoldingReplMasterLocks -"
| summarize arg_max(TIMESTAMP, message) by ClusterName, NodeName, process_id
| where message contains "HaDrDbMgr::DelayKillingSessionsHoldingReplMasterLocks - Waiting"
```

**Expected output:**
- `TIMESTAMP`: Last occurrence of the deadlock
- `NodeName`: Affected node
- `process_id`: SQL process ID to kill
- `message`: Deadlock details

---

---

### LR305 - Case 10: msdb Upgrade Script Stuck (DBCC UPDATEUSAGE Lock)

**Purpose:** Check if the msdb upgrade script started but never completed during a role transition to PRIMARY. This is a known issue (PBI 4448193) where `DBCC UPDATEUSAGE` blocks on a metadata lock held by another session on msdb, preventing the role transition from completing.

**What to look for:**
- If `originalEventTimestamp1` (TRUSTWORTHY step) is **NULL** → upgrade is stuck, this is the root cause
- If `duration` is more than a few seconds → upgrade was slow, at risk of future incidents
- Normal duration is < 3 seconds

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where message contains "Checking the size of MSDB..."
| project originalEventTimestamp, message, NodeName, process_id, collect_current_thread_id
| join kind=leftouter
(
    MonSQLSystemHealth
    | where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
    | where AppName =~ "{AppName}"
    | where message contains "Setting database option TRUSTWORTHY to ON for database 'msdb'."
    | project originalEventTimestamp, message, NodeName, process_id, collect_current_thread_id
) on process_id, collect_current_thread_id
| extend duration = originalEventTimestamp1 - originalEventTimestamp
| order by duration
```

**Expected output:**
- `originalEventTimestamp`: When the msdb upgrade started ("Checking the size of MSDB...")
- `originalEventTimestamp1`: When the upgrade finished ("Setting TRUSTWORTHY to ON") — **NULL if stuck**
- `duration`: Time to complete — should be < 3 seconds
- `NodeName`: Node where upgrade ran

**Confirmation query — check script start/complete in error log:**
```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where message has "PerformConfigureDatabaseInternal" and message has "Sql.Msdb.Sql"
| project PreciseTimeStamp, NodeName, message
| order by PreciseTimeStamp asc
```

Look for:
- ✅ `"upgrading script 'Sql.Msdb.Sql'"` — script started
- ❌ `"PerformConfigureDatabaseInternal completed running of script Sql.Msdb.Sql"` — **MISSING** = stuck
- 🚩 If started without completed on the same node → confirmed Case 10

**Mitigation:** Kill the primary SQL process. The new primary will re-run the upgrade and it typically completes in seconds.

**Known issue:** [PBI 4448193](https://dev.azure.com/msdata/5603b9e3-ece0-4518-b9c8-1a36054d9970/_workitems/edit/4448193) — "MSDB upgrade script can last for 10s of minutes"

---

## Step 2a: Performance Pressure Check

> **⚠️ Always run these queries as part of standard triage.** Performance pressure (CPU, memory, I/O) can cause or contribute to long reconfigurations by starving HADR threads, blocking log transport, or preventing quorum catchup.

### LR250 - CPU and I/O Pressure (Instance-Level Resource Stats)

**Purpose:** Check instance-level CPU, data I/O, and log write pressure during the incident window. High sustained resource usage can starve HADR operations and prevent reconfiguration from completing.

**What to look for:**
- `avg_cpu_percent` > 90% sustained → CPU pressure may block HADR threads
- `avg_data_io_percent` > 90% sustained → I/O pressure may block checkpoint/recovery
- `avg_log_write_percent` > 90% sustained → Log write saturation may block HADR log transport
- `max_worker_percent` approaching 100% → Worker thread exhaustion

```kql
MonResourceStats
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| project originalEventTimestamp, NodeName, avg_cpu_percent, avg_data_io_percent, avg_log_write_percent, max_worker_percent, max_session_percent
| order by originalEventTimestamp asc
```

**Expected output:**
- `avg_cpu_percent`: CPU usage percentage
- `avg_data_io_percent`: Data I/O usage percentage
- `avg_log_write_percent`: Log write usage percentage
- `max_worker_percent`: Worker thread usage percentage

---

### LR252 - Memory Pressure (Resource Pool Memory Grants)

**Purpose:** Check for memory grant timeouts and excessive memory grant usage in resource pools. Memory pressure can block queries and internal operations, contributing to reconfiguration delays.

**What to look for:**
- `delta_total_memgrant_timeout_count` > 0 → Memory grants are timing out (severe pressure)
- High `active_memgrant_count` → Many concurrent memory grants consuming available memory
- Compare `used_memgrant_kb` across nodes to identify imbalanced memory consumption

```kql
MonGovernorResourcePools
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| summarize 
    total_memgrant_timeouts = sum(delta_total_memgrant_timeout_count),
    max_active_memgrants = max(active_memgrant_count),
    max_used_memgrant_kb = max(used_memgrant_kb),
    avg_cpu_usage_ms = avg(delta_total_cpu_usage_ms)
    by NodeName, name
| where total_memgrant_timeouts > 0 or max_active_memgrants > 50
| order by total_memgrant_timeouts desc
```

**Expected output:**
- `total_memgrant_timeouts`: Number of memory grant timeouts (0 = healthy)
- `max_active_memgrants`: Peak concurrent memory grants
- `max_used_memgrant_kb`: Peak memory grant usage in KB
- `name`: Resource pool name

---

### LR254 - I/O Pressure (Virtual File Stats)

**Purpose:** Check for I/O stalls on database files that could indicate storage-level pressure blocking reconfiguration, log transport, or recovery operations.

**What to look for:**
- High `delta_io_stall_read_ms` or `delta_io_stall_write_ms` → Storage is slow
- Average I/O latency > 50ms is concerning, > 200ms is severe
- Compare across nodes — if one node has significantly higher latency, it may indicate a local storage issue
- Pay attention to log files (`type_desc = 'LOG'`) — log I/O stalls directly impact HADR transport

```kql
MonDmIoVirtualFileStats
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where delta_is_valid == 1
| summarize 
    total_reads = sum(delta_num_of_reads),
    total_writes = sum(delta_num_of_writes),
    total_read_stall_ms = sum(delta_io_stall_read_ms),
    total_write_stall_ms = sum(delta_io_stall_write_ms),
    total_io_stall_ms = sum(delta_io_stall)
    by NodeName, db_name, type_desc
| extend avg_read_latency_ms = iff(total_reads > 0, total_read_stall_ms * 1.0 / total_reads, 0.0)
| extend avg_write_latency_ms = iff(total_writes > 0, total_write_stall_ms * 1.0 / total_writes, 0.0)
| where avg_read_latency_ms > 50 or avg_write_latency_ms > 50 or total_io_stall_ms > 60000
| order by total_io_stall_ms desc
```

**Expected output:**
- `avg_read_latency_ms` / `avg_write_latency_ms`: Average I/O latency (< 20ms normal, > 50ms concerning, > 200ms severe)
- `total_io_stall_ms`: Total time spent waiting on I/O
- `type_desc`: `DATA` or `LOG` — log file stalls are more impactful for HADR

---

### LR256 - Wait Stats Analysis (Resource Contention)

**Purpose:** Check for resource-contention wait types that indicate CPU, memory, I/O, or thread pressure during the incident window. Specific wait types can pinpoint exactly which resource is under pressure.

**What to look for:**
- `SOS_SCHEDULER_YIELD` → CPU pressure (threads yielding due to CPU exhaustion)
- `RESOURCE_SEMAPHORE` → Memory grant pressure (queries waiting for memory)
- `THREADPOOL` → Worker thread exhaustion
- `WRITELOG` → Log write bottleneck (may block HADR transport)
- `PAGEIOLATCH_*` → Data I/O pressure
- `HADR_*` → HADR-specific waits (transport, sync, redo)
- `PARALLEL_REDO_*` → Redo thread contention on secondaries

```kql
MonDmCloudDatabaseWaitStats
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where delta_is_valid == 1
| where wait_type in (
    'SOS_SCHEDULER_YIELD', 'THREADPOOL', 'RESOURCE_SEMAPHORE', 'RESOURCE_SEMAPHORE_QUERY_COMPILE',
    'WRITELOG', 'PAGEIOLATCH_SH', 'PAGEIOLATCH_EX', 'PAGEIOLATCH_UP', 'IO_COMPLETION',
    'HADR_LOGCAPTURE_WAIT', 'HADR_SYNC_COMMIT', 'HADR_FILESTREAM_IOMGR_IOCOMPLETION',
    'PARALLEL_REDO_DRAIN_WORKER', 'PARALLEL_REDO_WORKER_SYNC', 'PARALLEL_REDO_LOG_CACHE'
)
| summarize 
    total_waiting_tasks = sum(delta_waiting_tasks_count),
    total_wait_time_ms = sum(delta_wait_time_ms),
    max_wait_time_ms = max(delta_max_wait_time_ms)
    by NodeName, wait_type
| where total_wait_time_ms > 10000
| order by total_wait_time_ms desc
```

**Expected output:**
- `wait_type`: Type of wait (identifies the bottleneck)
- `total_waiting_tasks`: Number of tasks that waited
- `total_wait_time_ms`: Total wait time in ms
- `max_wait_time_ms`: Longest single wait

---

### LR258 - Performance Error Indicators (Non-Yielding, OOM, I/O Stalls)

**Purpose:** Check for SQL Server error-level performance indicators: non-yielding schedulers (CPU starvation), out-of-memory conditions, and I/O timeout errors. These are definitive evidence of severe resource pressure.

**What to look for:**
- Error 17883/17884 (non-yielding scheduler) → Severe CPU pressure, thread stuck
- Error 17888 (deadlocked schedulers) → Multiple threads deadlocked
- Error 701/802 (insufficient memory) → OOM condition
- Error 8645/8651 (memory grant timeout) → Queries can't get memory
- Error 833/837 (I/O taking longer than 15/30 seconds) → Severe I/O stalls
- Error 855/856 (uncorrectable hardware memory corruption) → Hardware issue

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where error_id in (17883, 17884, 17888, 701, 802, 8645, 8651, 833, 837, 855, 856)
| summarize count(), min(originalEventTimestamp), max(originalEventTimestamp), any(message) by error_id, NodeName
| order by count_ desc
```

**Expected output:**
- `error_id`: Error number identifying the type of pressure
- `count_`: Frequency (more = more severe)
- `NodeName`: Which node is under pressure
- `any_message`: Sample error message with details

**Error reference:**

| Error | Meaning | Severity |
|-------|---------|----------|
| 17883 | Non-yielding scheduler detected | 🚩 Severe CPU |
| 17884 | Non-yielding scheduler with stack dump | 🚩 Severe CPU |
| 17888 | Deadlocked schedulers | 🚩 Critical CPU |
| 701 | Insufficient system memory | 🚩 Severe Memory |
| 802 | Insufficient memory in buffer pool | 🚩 Severe Memory |
| 8645 | Memory grant timeout | ⚠️ Memory pressure |
| 8651 | Memory grant denied | 🚩 Severe Memory |
| 833 | I/O > 15 seconds | ⚠️ I/O pressure |
| 837 | I/O > 30 seconds | 🚩 Severe I/O |
| 855/856 | Hardware memory corruption | 🚩 Hardware |

---

## Step 2b: Container and Networking Infrastructure Check

> **⚠️ Always run these queries as part of standard triage.** If non-SQL services (e.g., marker service) are also stuck in Reconfiguring, the issue is likely at the infrastructure/networking layer, not SQL/HADR. Leaked network containers, failed pod sandboxes, or crashed containers can cause HADR transport to break across all nodes.

### LR260 - Active Containers Per Node

**Purpose:** Check how many containers are currently active on each node. A node with 0 active containers indicates the SQL container is down, which explains why HADR transport is broken. Also detects recent container crashes.

**What to look for:**
- `ActiveContainers = 0` → Container is down on that node, SQL is not running
- Compare across nodes — all nodes should have at least 1 active container
- If a node had container crashes (join with terminated events), `ActiveContainers` is set to 0

```kql
let _containersBase = () {
    WinFabLogs
    | where ClusterName =~ "{ClusterName}"
    | where NodeName in ({NodeList})
    | where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
    | where TaskName contains "Hosting"
    | where EventType in (
        "NetworkingSubsystem", "Activator", "ApplicationService",
        "CriContainerActivator", "CriContainerTracker",
        "ContainerExitedOperational", "ContainerActivatedOperational",
        "ContainerDeactivatedOperational", "ContainerTerminated",
        "ActiveExecutablesAndContainersStats", "ProcessExitedOperational",
        "Deactivator", "SingleCodePackageApplicationHostProxy", "ByoVnetProvider"
    )
    | project ETWTimestamp, ClusterName, NodeName, EventType, Text
};
_containersBase
| where Text has "Number of activated Containers"
| parse Text with "Statistics: Number of activated Containers:" Containers ", Executables:" *
| join kind=leftouter (
    _containersBase
    | where EventType in ("ContainerTerminated", "ContainerDeactivatedOperational", "ContainerExitedOperational")
    | project NodeName, ContainerCrash=1
) on NodeName
| extend ActiveContainers = iff(ContainerCrash == 1, 0, toint(Containers))
| summarize arg_max(ETWTimestamp, ActiveContainers) by NodeName
| project ActiveContainers, NodeName
```

**Expected output:**
- `NodeName`: Node name
- `ActiveContainers`: Number of active containers (0 = container down)

---

### LR262 - Container Starts Per Node

**Purpose:** Count how many containers were started on each node during the incident window. Multiple starts indicate container crash loops. No starts on a node could mean the container was stable (good) or couldn't start (bad — check NC errors).

**What to look for:**
- Nodes with many container starts → crash loop
- Nodes with 0 starts → container stable since before incident, OR failed to start (check LR264)
- Compare with LR260 to determine current state

```kql
let _containersBase = () {
    WinFabLogs
    | where ClusterName =~ "{ClusterName}"
    | where NodeName in ({NodeList})
    | where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
    | where TaskName contains "Hosting"
    | where EventType in (
        "NetworkingSubsystem", "Activator", "ApplicationService",
        "CriContainerActivator", "CriContainerTracker",
        "ContainerExitedOperational", "ContainerActivatedOperational",
        "ContainerDeactivatedOperational", "ContainerTerminated",
        "ActiveExecutablesAndContainersStats", "ProcessExitedOperational",
        "Deactivator", "SingleCodePackageApplicationHostProxy", "ByoVnetProvider"
    )
    | project ETWTimestamp, ClusterName, NodeName, EventType, Text
};
_containersBase
| where EventType == 'ContainerActivatedOperational'
| where Text startswith_cs "Container sf"
| summarize count() by NodeName
```

**Expected output:**
- `NodeName`: Node name
- `count_`: Number of container activations during the window

---

### LR264 - Network Container (NC) Create/Delete Results Per Node

**Purpose:** Check if network container operations succeeded or failed on each node. NC failures prevent container networking from being set up, which blocks HADR transport. This is the most common infrastructure cause of instance-wide long reconfiguration.

**What to look for:**
- `NC_Create FAIL` → Network container couldn't be created on that node (leaked/stale NC blocking IP)
- `NC_Delete FAIL` → Leaked NC couldn't be cleaned up
- Nodes with FAIL results need Connectivity and Networking team engagement
- 🚩 NC failures explain broken HADR transport (`log_send_queue_size = -1`) and non-SQL services stuck in Reconfiguring

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ "{ClusterName}"
| where NodeName in ({NodeList})
| where TaskName == "Hosting" and EventType == "ByoVnetProvider"
| where Text has "ValidateCreateNetworkContainer" or Text has "ValidateDeleteNetworkContainer"
| extend Action = iff(Text has "ValidateCreate", "NC_Create", "NC_Delete")
| extend Result = iff(Text has "ErrorCode=E_FAIL", "FAIL", "OK")
| summarize count(), min(ETWTimestamp), max(ETWTimestamp) by NodeName, Action, Result
| order by NodeName, Action
```

**Expected output:**
- `NodeName`: Node where NC operation occurred
- `Action`: `NC_Create` or `NC_Delete`
- `Result`: `OK` or `FAIL`
- `count_`: Number of operations

---

### LR266 - Container Lifecycle Timeline

**Purpose:** Show the full container lifecycle (activate, terminate, exit) per node to understand when containers crashed, restarted, or failed to start. Provides the timeline needed to correlate container issues with HADR transport failures.

**What to look for:**
- `ContainerTerminated` / `ContainerExitedOperational` with `ExitCode=4294967295` (0xFFFFFFFF) → unexpected crash
- `ContainerActivatedOperational` after a crash → container restarted
- Gaps with no activation after termination → container failed to restart (check NC errors)
- `UnexpectedTermination=True` → crash, not graceful shutdown

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ "{ClusterName}"
| where NodeName in ({NodeList})
| where TaskName == "Hosting"
| where Text has "{AppName}"
| where EventType in (
    "ContainerActivatedOperational", "ContainerTerminated",
    "ContainerExitedOperational", "ContainerDeactivatedOperational",
    "PodSandboxInstance"
)
| project ETWTimestamp, NodeName, EventType, Text
| order by NodeName, ETWTimestamp asc
```

**Expected output:**
- `ETWTimestamp`: When the event occurred
- `NodeName`: Node where the event occurred
- `EventType`: Type of container lifecycle event
- `Text`: Full event details (container ID, exit code, image name)

---

### LR268 - Service Package Activation Failures

**Purpose:** Check if Service Fabric service package activation failed on any node. Activation failures cascade from NC failures and prevent the SQL container from starting. This confirms the infrastructure root cause.

**What to look for:**
- `ErrorCode=E_FAIL` on Activator/ServicePackage/VersionedServicePackage → activation failed
- Correlate with LR264 — NC failures cause activation failures
- If activation failed, killing SQL processes will NOT help — the infrastructure issue must be resolved first

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ "{ClusterName}"
| where NodeName in ({NodeList})
| where TaskName == "Hosting"
| where Text has "{AppName}"
| where EventType in ("Activator", "ServicePackage", "VersionedServicePackage", "NetworkingSubsystem")
| where Text has "ErrorCode=E_FAIL"
| summarize count(), min(ETWTimestamp), max(ETWTimestamp), any(Text) by NodeName, EventType
| order by NodeName, count_ desc
```

**Expected output:**
- `NodeName`: Node where activation failed
- `EventType`: Which component failed (Activator → ServicePackage → VersionedServicePackage)
- `count_`: Number of failures
- `any_Text`: Sample error with details

---

## Step 3: General Investigation (Case 6 - Unknown Issue)

### LR300 - General Error Survey

**Purpose:** Survey all errors during the issue window when no known case matches.

**What to look for:**
- Group errors by `error_id` to identify the most frequent errors
- Look for patterns — many occurrences of the same error may indicate root cause
- Check `message` for actionable information

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where message contains "Error:"
| summarize count(), min(TIMESTAMP), max(TIMESTAMP), any(message) by error_id, NodeName
```

**Expected output:**
- `error_id`: Error identifier
- `NodeName`: Node where error occurred
- `count_`: Frequency of the error
- `any_message`: Sample error message

---

### LR310 - Case 7: XEvent Dispatcher Deadlock

**Purpose:** Check if the XEvent engine dispatcher pool is stuck with long running targets, which can block SQL process operations and cause reconfiguration to hang.

**What to look for:**
- Any rows indicate XEvent dispatcher deadlock — this is a known root cause
- 🚩 If present, kill the SQL process on the affected node

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where message contains "XE Engine dispatcher pool for sessions that has long running targets"
| project originalEventTimestamp, NodeName, message
```

**Expected output:**
- `originalEventTimestamp`: When the XEvent deadlock was detected
- `NodeName`: Affected node
- `message`: Details of the stuck XEvent session

---

### LR320 - SQL Process Lifetime Analysis

**Purpose:** Identify SQL process restarts, crashes, or gaps in process lifetime that overlap with the reconfiguration issue. Helps determine if the issue was caused by a process crash.

**What to look for:**
- Gaps between `max_TIMESTAMP` of one process and `min_TIMESTAMP` of the next indicate a process restart
- A process that started during the incident window may indicate a crash/restart cycle
- Multiple short-lived processes indicate instability

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| summarize min(TIMESTAMP), max(TIMESTAMP) by process_id, NodeName
| order by min_TIMESTAMP asc
```

**Expected output:**
- `process_id`: SQL Server process ID
- `NodeName`: Node where the process was running
- `min_TIMESTAMP` / `max_TIMESTAMP`: Process lifetime window

---

### LR330 - Forwarder Redo Queue Size

**Purpose:** Check if a database in FORWARDER role has a large redo queue, which can delay reconfiguration completion.

**What to look for:**
- Large redo queue (> 1 GB) indicates the forwarder is behind and reconfiguration cannot complete until redo catches up
- 🚩 If redo queue is very large, reconfiguration may be stuck waiting for redo

```kql
MonDmDbHadrReplicaStates
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where internal_state_desc == "FORWARDER"
| summarize max_redo_queue_size_kb = max(redo_queue_size) by NodeName, logical_database_name
| extend max_redo_queue_size_gb = max_redo_queue_size_kb * 1.0 / 1000.0 / 1000.0
| order by max_redo_queue_size_gb desc
```

**Expected output:**
- `NodeName`: Node hosting the forwarder replica
- `logical_database_name`: Database name
- `max_redo_queue_size_gb`: Maximum redo queue size in GB

---

### LR340 - Database Recovery Time

**Purpose:** Check if a database recovery completed during the incident window and how long it took. Long recovery times can cause reconfiguration to appear stuck.

**What to look for:**
- If recovery completed, note the time — this is when the database became available
- If no recovery completed, the database may still be recovering (stuck)
- Parse the recovery time from the message (e.g., "Recovery completed... in X second(s)")

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where message contains "Recovery completed for database"
| project originalEventTimestamp, NodeName, message
| order by originalEventTimestamp desc
```

**Expected output:**
- `originalEventTimestamp`: When recovery completed
- `NodeName`: Node where recovery occurred
- `message`: Recovery details including duration

---

### LR350 - Mitigation Actions History

**Purpose:** Check if any mitigation actions (dumps, kills, restarts) were taken during the incident window by DRI or automation. Helps understand if mitigation was attempted and what the effect was.

**What to look for:**
- `DumpSqlInstance` / `DumpProcess` = dump was taken before mitigation
- `ExecuteKillProcess` / `KillProcess` = SQL process was killed
- `RestartReplica` = replica was restarted
- If multiple restarts were attempted but issue persisted, the root cause is deeper
- Check the `username` to determine if it was manual DRI action or automation

```kql
MonNonPiiAudit
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where * contains "{AppName}"
| project TIMESTAMP, NodeName, username, request_action, request
| order by TIMESTAMP asc
```

**Expected output:**
- `TIMESTAMP`: When the action was executed
- `username`: Who performed the action (DRI alias or automation account)
- `request_action`: Type of action (DumpSqlInstance, ExecuteKillProcess, RestartReplica, etc.)
- `request`: Full URL with node name and cluster details

---

### LR355 - Management Operations (Reseed, SLO Update, etc.)

**Purpose:** Check for management operations (reseed, SLO update, failover API, etc.) that were triggered during or after the incident. A reseed operation can fix log corruption (Error 9003) by rebuilding the database from the geo-primary.

**What to look for:**
- `reseed` operations — indicates someone attempted to fix a corrupt/stuck forwarder database
- Check if the operation succeeded or timed out
- `operation_start` / `operation_success` / `operation_failure` events show the lifecycle
- Timed-out reseeds require PG investigation before retrying — the timeout root cause must be understood first

```kql
MonManagementOperations
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where operation_parameters contains ">{LogicalDatabaseName}<"
| project TIMESTAMP, event, operation_type, operation_state, elapsed_time_milliseconds, operation_parameters
| order by TIMESTAMP asc
```

**Expected output:**
- `event`: Operation lifecycle event (management_operation_start, management_operation_success, management_operation_failure)
- `operation_type`: Type of operation (e.g., Reseed, UpdateSlo, FailoverApi)
- `operation_state`: Current state of the operation
- `elapsed_time_milliseconds`: How long the operation took

---

### LR356 - Seeding Progress Tracking

**Purpose:** Track the progress of a reseed operation after log corruption (Error 9003) or SUSPECT database. Use this when a reseed has been initiated (confirmed via LR355) to monitor whether seeding is progressing or stuck.

**What to look for:**
- Seeding progress messages — check if percentage is advancing over time
- If seeding is stuck at the same percentage, there may be a blocking issue
- Seeding completion message confirms the database has been rebuilt
- If no results after a reseed was triggered, seeding may have failed to start

```kql
MonDbSeedTraces
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ "{LogicalServerName}"
| where database_name =~ "{physical_database_id}"
| project TIMESTAMP, NodeName, database_name, event, message
| order by TIMESTAMP asc
```

**Expected output:**
- `TIMESTAMP`: When the seeding event occurred
- `NodeName`: Node where seeding is running
- `database_name`: Physical database ID being reseeded
- `event` / `message`: Seeding progress details

---

### LR361 - WinFab Node ID to NodeName Mapping

**Purpose:** Convert Service Fabric internal node GUIDs to human-readable node names (_DB64C_0, _DB64C_1, etc.) for FTUpdate analysis. Run this first, then use the output to build LR362.

**What to look for:**
- Map each `NodeId` (GUID) to its `MappedNodeName` (e.g., `_DB64C_2`)
- The `KustoExtend` column provides ready-to-paste extend statements for LR362

```kql
WinFabLogs
| where ClusterName =~ "{ClusterName}"
| where TaskName == "FM" and EventType == "NodeState" and Text contains "NodeName:"
| extend NodeId = Id
| extend MappedNodeName = extract("NodeName: ([^\n\t\r ]+)", 1, Text)
| where MappedNodeName contains "DB"
| extend KustoExtend = strcat("| extend Text = replace_regex(Text, \"", NodeId, ".*?\\r\", \"", MappedNodeName, "\\r\\n\")")
| distinct NodeId, MappedNodeName, KustoExtend
```

**Expected output:**
- `NodeId`: SF internal GUID for the node
- `MappedNodeName`: Human-readable name (e.g., `_DB64C_0`)
- `KustoExtend`: Ready-to-paste KQL extend statement for LR362

---

### LR362 - WinFab FTUpdate Reconfiguration Timeline (Human-Readable)

**Purpose:** Show the Service Fabric partition state changes (FTUpdate events) with human-readable node names. This shows exactly when reconfiguration started, what triggered it, and which replica roles changed.

**How to use:**
1. Run LR361 first to get node ID → name mapping
2. Copy the `KustoExtend` statements from LR361 results
3. Paste them into this query, replacing the example `extend` lines

**What to look for:**
- **Role transitions:** `P/S` = Primary demoting to Secondary, `S/P` = Secondary promoting to Primary
- **Replica flags:** `U` = Up, `D` = Down, `I` = InBuild, `T` = ToBeDropped, `E` = InConfiguration
- **Actions:** `SwapPrimarySecondary` = planned failover, `DoReconfiguration` = triggered reconfig, `AddPrimary`/`DeleteReplica` = replica changes
- **Partition state:** `SP` = SwapPrimary, `SPB` = SwapPrimary Below (SQL engine processing), `SPWB` = SwapPrimary Wait Below (stuck waiting for SQL)
- Also check for `UnplacedReplica` events if replicas are missing

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where Text contains "{AppName}"
| where EventType == "FTUpdate"
| parse Text with * "SQL." * "/" databaseId " " *
// Paste extend lines from LR361 below (replace GUIDs with node names):
// | extend Text = replace_regex(Text, "GUID_1.*?\r", "_DB64C_0\r\n")
// | extend Text = replace_regex(Text, "GUID_2.*?\r", "_DB64C_1\r\n")
// | extend Text = replace_regex(Text, "GUID_3.*?\r", "_DB64C_2\r\n")
// | extend Text = replace_regex(Text, "GUID_4.*?\r", "_DB64C_3\r\n")
| project ETWTimestamp, databaseId, Text
```

**FTUpdate flags reference:**

| Flag | Meaning |
|------|---------|
| **Role (before/after):** | |
| `P/P` | Primary staying Primary |
| `P/S` | Primary demoting to Secondary |
| `S/P` | Secondary promoting to Primary |
| `S/S` | Secondary staying Secondary |
| `S/I` | Secondary becoming InBuild (being rebuilt) |
| `N/P`, `N/S` | Normal state Primary/Secondary |
| **Status:** | |
| `RD` | Ready |
| `SB` | Standby |
| `IB` | InBuild |
| **Availability:** | |
| `U` | Up |
| `D` | Down |
| **Flags:** | |
| `E` | In reconfiguration (Elected) |
| `P` | Pending (new primary being promoted) |
| `I` | InBuild flag |
| `T` | ToBeDropped |
| `TG` | ToBeDropped by Gateway |
| `N` | Newly created/placed |
| **Partition state codes:** | |
| `SP` | SwapPrimary in progress |
| `SPB` | SwapPrimary Below (SQL engine processing role change) |
| `SPWB` | SwapPrimary Wait Below (waiting for SQL — if stuck here, SQL is blocked) |

---

### LR360 - Replica Sync State Timeline

**Purpose:** Track when secondaries lost synchronization with the primary. Helps identify the root trigger — if all secondaries lost sync simultaneously, the issue is likely on the primary side.

**What to look for:**
- Transition from `SYNCHRONIZED` to `NOT SYNCHRONIZING` — note the timestamp and which node first
- If all secondaries drop sync at the same time, the primary is the problem
- If one secondary drops first and others follow later, check what happened on that secondary
- Check `log_send_queue_size`: `-1` indicates broken transport

```kql
MonDmDbHadrReplicaStates
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| project TIMESTAMP, NodeName, internal_state_desc, synchronization_state_desc, synchronization_health_desc, last_hardened_lsn, end_of_log_lsn, log_send_queue_size
| order by TIMESTAMP asc
```

**Expected output:**
- `synchronization_state_desc`: `SYNCHRONIZED` (healthy) or `NOT SYNCHRONIZING` (problem)
- `synchronization_health_desc`: `HEALTHY` or `NOT_HEALTHY`
- `log_send_queue_size`: `0` = caught up, `>0` = behind, `-1` = broken

---

### LR370 - UCS Connection Errors

**Purpose:** Check for UCS (Unified Communication Stack) connection failures between replicas. Error 10060 (TCP timeout) indicates network-level connectivity loss.

**What to look for:**
- `error_number: 10060` = TCP connection timeout — remote party not responding
- Check which nodes and addresses are affected
- If both sides report errors simultaneously → network path issue
- If only secondaries report errors toward primary → primary is unresponsive

```kql
MonUcsConnections
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where error_number == 10060 or stream_status in ('Disconnected', 'ConnectionError')
| project TIMESTAMP, event, NodeName, address, target_address, stream_status, error_number, error_message
| order by TIMESTAMP asc
```

**Expected output:**
- `NodeName`: Node reporting the error
- `address` / `target_address`: Local and remote endpoints
- `error_number`: `10060` = TCP timeout
- `stream_status`: `Disconnected` or `ConnectionError`

---

### LR380 - Backup on Secondary Activity

**Purpose:** Check for backup-on-secondary operations that may have gotten stuck. A stuck backup can block the primary's HaDrDbMgr thread via `SendBackupCmdMsgAndWaitForResponse`, causing the primary to become unresponsive to all HADR operations.

**What to look for:**
- `BACKUP LOG started` without corresponding `BACKUP LOG finished` = stuck backup
- `ProcessBackupCmdResultMsg` = successful backup result received by primary
- Missing result messages after backup started = backup hung, primary thread blocked
- Check timing: if backup starts right before HADR transport timeouts, this is likely the trigger

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where message has_any ('ProcessBackupCmd', 'Backup Succeeded', 'BACKUP LOG started', 'BACKUP LOG finished', 'SendBackupBmsUpdate')
| project PreciseTimeStamp, NodeName, message
| order by PreciseTimeStamp asc
```

**Expected output:**
- `PreciseTimeStamp`: Exact time of backup activity
- `NodeName`: Node executing the backup (secondary) or processing result (primary)
- `message`: Backup operation details — look for started without finished

---

### LR390 - HADR Transport Timeouts

**Purpose:** Check for HADR transport session timeouts between replicas. These indicate the SQL HADR layer lost connectivity, which happens after UCS dies or when the primary's HaDrDbMgr thread is blocked.

**What to look for:**
- `Timeout Detected 90 s` = existing connection timed out (90s default)
- `Queue Timeout from [CHadrTransportReplica::Init]` = new connection attempt timed out
- `State change: HadrSession_Connected → HadrSession_Timeout` = session died
- Check which nodes are affected: if all secondaries time out toward the primary simultaneously, the primary is the problem

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where message has 'HADR TRANSPORT' and message has_any ('Timeout', 'timeout')
| project PreciseTimeStamp, NodeName, message
| order by PreciseTimeStamp asc
```

**Expected output:**
- `PreciseTimeStamp`: When the timeout was detected
- `NodeName`: Node reporting the timeout
- `message`: Timeout details including session IDs and state changes

---

### LR395 - HADR Timeout Scope Analysis (Primary vs Secondary Issue)

**Purpose:** Determine whether HADR transport timeouts are isolated to one secondary or affect all secondaries. This is critical for identifying whether the problem is on the primary side or a specific secondary.

**What to look for:**
- **One secondary has timeouts, others don't** → Problem is on that secondary (network, storage, stuck backup). **Mitigation: kill that secondary's SQL process.**
- **All secondaries have timeouts simultaneously** → Problem is on the primary (blocked HaDrDbMgr thread, stuck backup orchestration). **Mitigation: kill the primary SQL process.**
- Compare `first_timeout` across nodes — if all secondaries' first timeout is within seconds of each other, the primary went unresponsive at that moment

```kql
MonSQLSystemHealth
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ "{AppName}"
| where message has 'HADR TRANSPORT' and message has_any ('Timeout', 'timeout')
| summarize 
    timeout_count = count(), 
    first_timeout = min(PreciseTimeStamp), 
    last_timeout = max(PreciseTimeStamp) 
    by NodeName
| order by first_timeout asc
```

**Expected output:**
- `NodeName`: Node reporting timeouts
- `timeout_count`: Number of timeout events on this node
- `first_timeout`: When the first timeout was detected on this node
- `last_timeout`: When the last timeout was detected

**Decision matrix:**

| Pattern | Diagnosis | Mitigation |
|---------|-----------|------------|
| 1 secondary with timeouts, others healthy | Secondary-side issue (network, storage, stuck backup on that node) | Kill the problematic secondary's SQL process |
| All secondaries with timeouts at ~same time | Primary-side issue (blocked thread, stuck backup orchestration) | Kill the primary SQL process |
| Timeouts cascade: 1 secondary first, others follow minutes later | Secondary issue caused primary to get stuck (e.g., primary's reconnection loop starved healthy secondaries) | Kill the primary SQL process |

---

## Step 4: Post-Mitigation Verification

### LR400 - Verify Issue Resolved

**Purpose:** Confirm that the long reconfiguration has been resolved after mitigation (run 15 minutes after mitigation).

**What to look for:**
- ✅ Last timestamp is **before** mitigation time — issue is healed
- ❌ New timestamps **after** mitigation time — issue persists, try alternative mitigation or escalate

```kql
AlrWinFabHealthPartitionEvent
| where ServiceName contains "{AppName}"
| where Description contains "Partition reconfiguration is taking longer than expected."
| project TIMESTAMP, ClusterName, ApplicationName, ServiceName, PartitionId, Description
| summarize max(TIMESTAMP) by ClusterName, ApplicationName, ServiceName, PartitionId, Description
```

**Expected output:**
- `max_TIMESTAMP`: Last time the alert was observed — compare with mitigation time
