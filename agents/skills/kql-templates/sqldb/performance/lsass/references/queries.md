# LSASS Telemetry Hole Triage Queries

These Kusto queries are used for triaging LSASS-related incidents where telemetry holes are observed. They analyze CPU usage, XStore IO, watchdog events, IO stalls, and infrastructure changes.

## Query Parameter Placeholders

Replace these placeholders with actual values:
- `{StartTime}`: Start timestamp (e.g., `2026-03-05 04:00:00`)
- `{EndTime}`: End timestamp (e.g., `2026-03-05 10:00:00`)
- `{ClusterName}`: Tenant ring/cluster name (e.g., `tr2512.brazilsouth1-a.worker.database.windows.net`)
- `{DBNodeName}`: DB node name (e.g., `_DB_9`)

---

## LSASS100 - Total CPU Usage (Processor _Total)

Check total processor CPU usage at the node level to identify CPU saturation during the telemetry hole window.

**Purpose**: Determine if overall CPU was pegged, which could explain telemetry collection failures.

**What to look for**:
- Sustained CPU > 90% correlating with the telemetry gap
- 🚩 CPU at 100% for extended periods indicates severe contention

```kql
// LSASS100 - Total CPU Usage (Processor _Total)
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonCounterOneMinute
| where TIMESTAMP >= datetime({StartTime})
| where TIMESTAMP <= datetime({EndTime})
| where ClusterName =~ '{ClusterName}' and NodeName =~ '{DBNodeName}'
| where CounterName contains "Processor Time" and CounterName contains "Processor(_Total)"
| project TIMESTAMP, CounterName, CounterValue
| render timechart
```

---

## LSASS200 - Per-Core CPU Analysis (Pegged Cores)

Identify individual CPU cores running at near-maximum capacity while overall CPU may appear moderate.

**Purpose**: Detect CPU core saturation that indicates resource contention or scheduling issues.

**What to look for**:
- Individual cores with MaxVal > 90%
- Patterns where specific cores are consistently pegged
- 🚩 Multiple cores pegged simultaneously indicates severe CPU contention

```kql
// LSASS200 - Per-Core CPU Analysis (Pegged Cores)
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonCounterOneMinute
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| where TIMESTAMP >= datetime({StartTime}) and TIMESTAMP <= datetime({EndTime})
| where CounterName contains "Processor Time" and CounterName contains "\\Processor(" and CounterName !contains "Total"
| extend cpuID = extract("Processor\\(([0-9.]+)\\)", 1, CounterName, typeof(int))
| project TIMESTAMP, MaxVal, cpuID
| where MaxVal > 90
| summarize max(MaxVal), make_set(cpuID) by bin(TIMESTAMP, 30m)
```

---

## LSASS300 - LSASS Process CPU Usage

Check LSASS process-level CPU consumption to determine if it is the dominant CPU consumer.

**Purpose**: Identify if LSASS is causing high CPU. High LSASS CPU can cause authentication delays and telemetry collection failures.

**What to look for**:
- LSASS consuming > 5% CPU consistently
- 🚩 LSASS as the dominant CPU consumer correlates with authentication failures and telemetry holes

```kql
// LSASS300 - LSASS Process CPU Usage
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonCounterOneMinute
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| where TIMESTAMP >= datetime({StartTime}) and TIMESTAMP <= datetime({EndTime})
| where CounterName endswith "\\% Processor Time"
| where CounterName startswith "\\Process("
| where CounterName contains "lsass"
| project PreciseTimeStamp, CounterName, CounterValue, MaxVal
| order by PreciseTimeStamp asc
| render timechart
```

---

## LSASS350 - MonLogin (Login Activity Correlation)

Analyze login activity at the node level to correlate LSASS CPU spikes with login volume.

**Purpose**: LSASS handles TLS handshakes for logins. A spike in login volume (especially with TLS) can directly drive LSASS CPU usage. Correlating MonLogin totals with LSASS CPU spikes identifies login-driven LSASS issues.

**What to look for**:
- Total login counts spiking at the same time as LSASS CPU spikes
- System error login failures coinciding with LSASS spikes — indicates LSASS-driven authentication failures
- 🚩 Login spike correlating with LSASS spike confirms **login-driven LSASS** pattern
- 🚩 LSASS spike WITHOUT login spike suggests **XStore-driven** or **residual LSASS** pattern

```kql
// LSASS350 - MonLogin (Login Activity Correlation)
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonLogin
| where TIMESTAMP > datetime({StartTime}) and TIMESTAMP < datetime({EndTime})
| where ClusterName =~ '{ClusterName}' and NodeName =~ '{DBNodeName}'
| where event == "process_login_finish"
| summarize
    sum_nb_connection_accept_finish = sum(iff(is_success == 1 and (package == "sqlserver" or package == "mpdw"), 1, 0)),
    sum_nb_connection_accept_only = toint(0),
    sum_nb_connection_accept_failure = toint(0),
    sum_nb_connection_accept_failure_finish = sum(iff(is_success == 0 and is_user_error == 1, 1, 0)),
    sum_nb_connection_accept_failure_finish_is_system_error = sum(iff(is_success == 0 and is_user_error == 0, 1, 0))
    by bin(TIMESTAMP, 10m)
| extend total_succeed = sum_nb_connection_accept_finish
| extend total_failures_system_error = sum_nb_connection_accept_only + sum_nb_connection_accept_failure + sum_nb_connection_accept_failure_finish_is_system_error
| extend total_failures_user_error = sum_nb_connection_accept_failure_finish
| extend total_logins = total_succeed + total_failures_system_error + total_failures_user_error
| project TIMESTAMP,
    ['Total Logins'] = total_logins,
    ['Failed Logins Due to System Error'] = total_failures_system_error,
    ['Failed Logins Due to User Error'] = total_failures_user_error
| sort by TIMESTAMP asc
| render timechart
```

---

## LSASS400 - XStore Total Request Counts

Check XStore request volume to identify IO stalls or connectivity issues.

**Purpose**: Sudden drops in XStore requests indicate IO stalls or storage connectivity problems that correlate with telemetry holes.

**What to look for**:
- Sudden drops in request counts
- Gaps in XStore request data
- 🚩 Zero or near-zero requests during the telemetry hole window
- Compare IOPM and IOPS to identify burst vs sustained IO patterns

```kql
// LSASS400 - XStore Total Request Counts
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonSQLXStoreIOStats
| where TIMESTAMP >= datetime({StartTime}) and TIMESTAMP <= datetime({EndTime})
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| summarize IOPM = sum(total_requests) / 5, IOPS = sum(total_requests) / 5 / 60 by bin(TIMESTAMP, 5m)
| project TIMESTAMP, IOPM, IOPS
```

---

## LSASS500 - XStore IO Throughput (MBps)

Analyze XStore read/write throughput per AppType and AppName.

**Purpose**: Identify storage throughput anomalies. Zero throughput periods correlate with telemetry holes.

**What to look for**:
- Periods of zero read/write throughput
- Abnormal throughput patterns (sudden drops or extreme spikes)
- 🚩 Sustained zero throughput correlating with the incident window

```kql
// LSASS500 - XStore IO Throughput (MBps)
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonSQLXStoreIOStats
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where event == "xstore_io_stats" and (total_write_bytes > 0 or total_read_bytes > 0)
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| extend
    write_mbps = round(total_write_bytes / 1024. / 1024. / (period_ms / 1000.0), 1),
    read_mbps = round(total_read_bytes / 1024. / 1024. / (period_ms / 1000.0), 1)
| project originalEventTimestamp, AppTypeName, AppName, file_path, read_mbps, write_mbps
| summarize sum(read_mbps), sum(write_mbps) by bin(originalEventTimestamp, 5m), strcat_delim("_", AppTypeName, AppName)
| render timechart
```

---

## LSASS600 - XStore IO Request Counts (Granular)

Fine-grained XStore IO request count analysis at 1-minute granularity.

**Purpose**: Detect brief IO stalls or gaps that may not be visible at coarser granularity.

**What to look for**:
- Gaps or sharp drops in per-minute IO request counts
- Correlate with LSASS500 throughput data
- 🚩 Missing data points indicate the node was unresponsive

```kql
// LSASS600 - XStore IO Request Counts (Granular)
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonSQLXStoreIOStats
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where event == "xstore_io_stats" and (total_write_bytes > 0 or total_read_bytes > 0)
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| extend
    write_mbps = round(total_write_bytes / 1024. / 1024. / (period_ms / 1000.0), 1),
    read_mbps = round(total_read_bytes / 1024. / 1024. / (period_ms / 1000.0), 1)
| project originalEventTimestamp, AppTypeName, AppName, file_path, read_mbps, write_mbps, total_xio_requests
| summarize sum(total_xio_requests) by bin(originalEventTimestamp, 1m)
| render timechart
```

---

## LSASS700 - Machine Local Watchdog (Sluggish/Frozen VM)

Detect sluggish and frozen VM conditions via the MonMachineLocalWatchdog table.

**Purpose**: Identify infrastructure-level VM responsiveness issues. Sluggish/frozen VMs directly cause telemetry holes.

**What to look for**:
- "Sluggish VM" categories (sluggish detection thread messages)
- "Frozen VM" categories (Disk IO spent messages)
- 🚩 TimeInSec > 30s for sluggish detections indicates severe VM unresponsiveness
- 🚩 Any frozen VM detection indicates storage hangs causing telemetry holes

```kql
// LSASS700 - Machine Local Watchdog (Sluggish/Frozen VM)
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonMachineLocalWatchdog
| where TIMESTAMP between (datetime({StartTime}) .. datetime({EndTime}))
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| extend Category = iff(message_systemmetadata contains 'sluggish detection thread', 'Sluggish VM',
    iff(message_systemmetadata contains 'Disk IO spent ', 'Frozen VM', ''))
| where Category != ''
| extend TimeInSec = toreal(extract(@"[Ss]pent ([^ ]+) sec", 1, message_systemmetadata))
| summarize max(TimeInSec) by bin(TIMESTAMP, 10m), Category
| render timechart
```

---

## LSASS800 - Virtual File IO Stalls

Analyze IO stall percentages from aggregated virtual file IO history.

**Purpose**: Detect storage-level bottlenecks via IO stall metrics. High stall percentages indicate the node is spending excessive time waiting on IO.

**What to look for**:
- delta_io_stall_read_ms_perc or delta_io_stall_write_ms_perc > 50%
- 🚩 High IO stall percentages indicate storage-level bottleneck
- Correlate with XStore throughput drops from LSASS400-600

```kql
// LSASS800 - Virtual File IO Stalls
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonSqlRgHistory
| where originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime}))
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| where event == "aggregated_virtual_files_io_history"
| where file_path startswith "S:"
| where delta_num_of_writes > 0 or delta_num_of_reads > 0
| project originalEventTimestamp, strcat_delim("_", AppTypeName, AppName),
    delta_io_stall_read_ms_perc = delta_io_stall_read_ms * 1.0 / duration_time_ms * 100,
    delta_io_stall_write_ms_perc = delta_io_stall_write_ms * 1.0 / duration_time_ms * 100
| render timechart
```

---

## LSASS900 - Guest OS Version Changes (MonRgLoad)

Check for guest OS version changes during the incident window.

**Purpose**: Identify host updates or reboots that coincide with the telemetry gap. OS version changes can indicate infrastructure maintenance events.

**What to look for**:
- Multiple distinct guest_os_version values during the window
- 🚩 OS version change timestamps coinciding with the telemetry gap — indicates a host update/reboot

```kql
// LSASS900 - Guest OS Version Changes (MonRgLoad)
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonRgLoad
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| where TIMESTAMP >= datetime({StartTime}) and TIMESTAMP <= datetime({EndTime})
| summarize min(TIMESTAMP), max(TIMESTAMP) by guest_os_version
```

---

## LSASS1000 - Azure Compute VM Details (TenantID, NodeID, Unique VM ID)

Resolve Azure compute-level identifiers for the SQL node to enable Azure Host Analyzer investigation.

**Purpose**: Map the SQL-level node name to Azure compute identifiers (TenantID, NodeID, VirtualMachineUniqueId). These are needed for cross-team escalation and to generate an Azure Host Analyzer link for the DRI to inspect host-level events (reboots, live migrations, hardware failures).

> **⚠️ MANDATORY CONNECTION CHANGE**: Execute this query against cluster `https://sqlstage.kusto.windows.net` with database `sqlazure1`. This is a FIXED cluster regardless of the SQL region. Do NOT use the region-specific Kusto cluster (`{KustoClusterUri}`) from Task 1. You must explicitly set `cluster-uri` to `https://sqlstage.kusto.windows.net` when calling `mcp_azure_mcp_kusto`.

**What to look for**:
- `VirtualMachineUniqueId` — the VM identity for Azure Host Analyzer
- `NodeId` — the physical node hosting the VM
- `ContainerId` — the compute container ID
- 🚩 If multiple rows are returned with different NodeId values, the VM was live-migrated during the window

```kql
// LSASS1000 - Azure Compute VM Details
// Required Parameters: {ClusterName}, {DBNodeName}
// ⚠️ MUST run against cluster: https://sqlstage.kusto.windows.net database: sqlazure1
//
MonSQLNodeSnapshot
| where ClusterName =~ '{ClusterName}' and NodeName =~ '{DBNodeName}'
| top 1 by IngestionTime desc
| project VirtualMachineUniqueId, ContainerId, NodeId, ComputeMDM, ClusterName, NodeName, IngestionTime
```

**Expected Output:**

| VirtualMachineUniqueId | ContainerId | NodeId | ComputeMDM | ClusterName | NodeName | IngestionTime |
|------------------------|-------------|--------|------------|-------------|----------|---------------|
| (VM GUID) | (container GUID) | (node GUID) | (MDM account) | {ClusterName} | {DBNodeName} | (timestamp) |

### Azure Host Analyzer Link

After running the query, construct the Azure Host Analyzer URL for the DRI:

```
https://asi.azure.ms/services/Azure%20Host/pages/Azure%20VM?containerId={ContainerId}&nodeId={NodeId}&virtualMachineUniqueId={VirtualMachineUniqueId}&globalFrom={StartTimeISO}&globalTo={EndTimeISO}
```

Replace:
- `{ContainerId}` — from query result
- `{NodeId}` — from query result
- `{VirtualMachineUniqueId}` — from query result
- `{StartTimeISO}` / `{EndTimeISO}` — investigation window in ISO 8601 format (e.g., `2026-03-05T04%3A00%3A00.000Z`)

---

## LSASS1100 - System Service Replica Movements (ImageStore Correlation)

Identify Service Fabric system service replica movements (ImageStore, NamingService, etc.) that landed on the affected node. ImageStore replica builds are the confirmed root cause of most upgrade-related LSASS spikes.

**Purpose**: Determine if an ImageStore (or other system service) replica was placed on the node immediately before the LSASS spike / telemetry hole.

> **⚠️ CONNECTION**: Execute against the MFA Kusto cluster for the region (e.g., `sqlazurewus2.kustomfa.windows.net`). The `WinFabLogs` table may not be available on the standard cluster.

**What to look for**:
- ImageStoreService `AddSecondary` or `MoveSecondary` landing on the node within 10 minutes before the LSASS spike
- Multiple system service replicas landing simultaneously (bursts of 2-3 in the same second are common)
- FaultDomain constraint violations driving the moves
- 🚩 ImageStore landing at the exact second telemetry goes dark is the **strongest signal** — this is Pattern 6

```kql
// LSASS1100 - System Service Replica Movements
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
// ⚠️ Run against MFA Kusto cluster (e.g., sqlazurewus2.kustomfa.windows.net)
// Note: Replace {KustoMfaCluster} with the appropriate MFA cluster for the region
//
let regExNodeName="([A-Z0-9\\.\\_]+)";
let regExNodeInfo=strcat("([a-z0-9]+) ", regExNodeName, " \\(");
let nodeInfo = materialize (
    WinFabLogs
    | where ClusterName =~ '{ClusterName}'
    | where EventType == "NodeLoads" and TaskName == "PLB"
    | extend node_info = split(Text, "\r")
    | mvexpand node_info
    | extend TargetNodeId = extract(regExNodeInfo, 1, trim("\t", tostring(node_info)), typeof(string))
    | extend TargetNodeName = extract(regExNodeInfo, 2, trim("\t", tostring(node_info)), typeof(string))
    | where isnotempty(TargetNodeId) and isnotempty(TargetNodeName)
    | summarize by ClusterName, NodeId=TargetNodeId, NodeName=TargetNodeName
);
WinFabLogs
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where ClusterName =~ '{ClusterName}'
| where TaskName == "CRM" and EventType == "Operation"
| where Text contains "Phase: " and Text contains "Action: " and Text contains "DecisionId: "
| extend ServiceName = extract("Service: ([\\.\\-/:a-zA-Z|0-9]+) \r", 1, Text)
| where ServiceName !contains "SQL.LogicalServer" and ServiceName !contains "Worker.ISO"
| extend Phase = extract("Phase: ([A-Za-z]+) \r", 1, Text),
    Action = extract("Action: ([A-Za-z]+) \r", 1, Text),
    SourceNodeId = extract("SourceNode: ([a-zA-Z0-9]+)\r", 1, Text),
    TargetNodeId = extract("TargetNode: ([a-zA-Z0-9]+)\r", 1, Text)
| extend DecisionId = toguid(extract("DecisionId: ([[a-z|A-Z|0-9|-]+)\r", 1, Text))
| join kind=leftouter
    (
    WinFabLogs
    | where ETWTimestamp between(datetime({StartTime}) .. datetime({EndTime}))
    | where ClusterName =~ '{ClusterName}'
    | where TaskName == "PLB" and EventType == "SchedulerAction"
    | where Text contains "Constraint Violations: "
        and ((Text contains " NodeCapacity"
            and Text contains "[MetricName, Load, Capacity, NodeId, NodeName")
        or (Text contains " Affinity ")
        or (Text contains "FaultDomain"))
    | extend DecisionId = toguid(extract("DecisionId: (.+)[[:space:]]Affects Service", 1, Text)),
        ConstraintType = extract("--\\[([a-zA-Z0-9_]+), [0-9]+, [0-9]+, [a-zA-Z0-9]+, [A-Z0-9\\.\\_]+, N/A\\]", 1, Text)
    | extend ConstraintType = iff(isempty(ConstraintType)
        and Text !contains "[MetricName, Load, Capacity, NodeId, NodeName, ApplicationName]",
        iff(Text contains "Affinity", "Affinity", "FaultDomain"), ConstraintType)
    | project ClusterName, DecisionId, ConstraintType
    )
    on ClusterName, DecisionId
| join kind=leftouter (nodeInfo | project-rename SourceNodeName=NodeName)
    on ClusterName, $left.SourceNodeId == $right.NodeId
| join kind=leftouter (nodeInfo | project-rename TargetNodeName=NodeName)
    on ClusterName, $left.TargetNodeId == $right.NodeId
| where Action in ("AddSecondary", "MoveSecondary", "MovePrimary", "SwapPrimarySecondary")
| project ETWTimestamp, ServiceName, Phase, Action, ConstraintType,
    SourceNodeName, TargetNodeName
| where TargetNodeName =~ '{DBNodeName}' or SourceNodeName =~ '{DBNodeName}'
| order by ETWTimestamp asc
```

---

## LSASS1200 - Telemetry Gaps with System Service Move Correlation

Identify telemetry gaps on the affected node and correlate them with system service replica movements. This is the key query for proving Pattern 6 (ImageStore-driven LSASS).

**Purpose**: Detect telemetry dark periods and check if they were preceded by ImageStore or other system service replica arrivals.

**What to look for**:
- Telemetry gaps > 2 minutes on the node
- System service moves (especially ImageStore) arriving within 15 minutes before the gap
- 🚩 ImageStore landing at the exact start of the telemetry gap is the strongest evidence for Pattern 6

```kql
// LSASS1200 - Telemetry Gaps with System Service Move Correlation
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}
// ⚠️ Run against MFA Kusto cluster
//
let _gapThreshold = 2m;
let regExNodeName="([A-Z0-9\\.\\_]+)";
let regExNodeInfo=strcat("([a-z0-9]+) ", regExNodeName, " \\(");
let nodeInfo = materialize (
    WinFabLogs
    | where ClusterName =~ '{ClusterName}'
    | where EventType == "NodeLoads" and TaskName == "PLB"
    | extend node_info = split(Text, "\r")
    | mvexpand node_info
    | extend TargetNodeId = extract(regExNodeInfo, 1, trim("\t", tostring(node_info)), typeof(string))
    | extend TargetNodeName = extract(regExNodeInfo, 2, trim("\t", tostring(node_info)), typeof(string))
    | where isnotempty(TargetNodeId) and isnotempty(TargetNodeName)
    | summarize by ClusterName, NodeId=TargetNodeId, NodeName=TargetNodeName
);
let telemetryGaps =
    MonCounterOneMinute
    | where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
    | where ClusterName =~ '{ClusterName}'
    | summarize by NodeName, Minute=bin(TIMESTAMP, 1m)
    | sort by NodeName asc, Minute asc
    | serialize
    | extend PrevMinute = prev(Minute), PrevNode = prev(NodeName)
    | where NodeName == PrevNode and Minute - PrevMinute > _gapThreshold
    | project Timestamp=PrevMinute, NodeName,
        Signal="TELEMETRY_DARK",
        Detail=strcat("Dark from ", format_datetime(PrevMinute, 'HH:mm:ss'),
            " to ", format_datetime(Minute, 'HH:mm:ss'),
            " (", Minute - PrevMinute, " gap)");
let sysServiceMoves =
    WinFabLogs
    | where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
    | where ClusterName =~ '{ClusterName}'
    | where TaskName == "CRM" and EventType == "Operation"
    | where Text contains "Phase: " and Text contains "Action: " and Text contains "DecisionId: "
    | extend ServiceName = extract("Service: ([\\.\\-/:a-zA-Z|0-9]+) \r", 1, Text)
    | where ServiceName !contains "SQL.LogicalServer" and ServiceName !contains "Worker.ISO"
    | extend Phase = extract("Phase: ([A-Za-z]+) \r", 1, Text),
        Action = extract("Action: ([A-Za-z]+) \r", 1, Text),
        SourceNodeId = extract("SourceNode: ([a-zA-Z0-9]+)\r", 1, Text),
        TargetNodeId = extract("TargetNode: ([a-zA-Z0-9]+)\r", 1, Text)
    | join kind=leftouter (nodeInfo | project-rename TargetNodeName=NodeName)
        on ClusterName, $left.TargetNodeId == $right.NodeId
    | join kind=leftouter (nodeInfo | project-rename SourceNodeName=NodeName)
        on ClusterName, $left.SourceNodeId == $right.NodeId
    | where Action in ("AddSecondary", "MoveSecondary", "MovePrimary", "SwapPrimarySecondary")
    | project Timestamp=ETWTimestamp, NodeName=TargetNodeName,
        Signal=iif(isnotempty(Phase), strcat("SYS_MOVE:", Phase), "SYS_MOVE"),
        Detail=strcat(Action, " ", ServiceName, " from ", SourceNodeName);
telemetryGaps
| union sysServiceMoves
| where isnotempty(NodeName)
| order by NodeName asc, Timestamp asc
```

---

## LSASS1300 - LoginOutages Wait Type Classification

Check LoginOutages for the LSASS-specific wait type signature that confirms authentication delays caused by LSASS/CRL operations.

**Purpose**: Identify if login outages are classified with LSASS-related wait types (`PREEMPTIVE_OS_AUTHENTICATIONOPS`, `PREEMPTIVE_OS_CRYPTACQUIRECONTEXT`).

**What to look for**:
- `PREEMPTIVE_OS_AUTHENTICATIONOPS` — LSASS authentication ops stalling (TLS handshake blocked)
- `PREEMPTIVE_OS_CRYPTACQUIRECONTEXT` — CRL/certificate validation stalling (network timeout)
- 🚩 These wait types with durations > 10 seconds confirm LSASS as the bottleneck

```kql
// LSASS1300 - LoginOutages Wait Type Classification
// Required Parameters: {StartTime}, {EndTime}, {LogicalServerName}, {LogicalDatabaseName}
//
LoginOutages
| where TIMESTAMP between (datetime({StartTime}) .. datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| project outageStartTime, outageEndTime, durationSeconds, OutageType,
    OutageReasonLevel1, OutageReasonLevel2, OutageReasonLevel3,
    OwningTeam, database_type, code_package_version
| sort by outageStartTime asc
```

---

## LSASS1400 - OS Upgrade Repair Task Timeline

Check WinFabLogs for repair task timing to understand the OS upgrade lifecycle on a cluster.

**Purpose**: Map repair tasks to nodes and understand the upgrade wave timing — preparing, executing, restoring phases.

**What to look for**:
- Repair task `Created` → `Preparing` → `Executing` → `Restoring` timeline for each UD (Upgrade Domain)
- 🚩 Telemetry gaps that do NOT overlap with any repair task window are "unexplained" and more likely to be ImageStore-driven

```kql
// LSASS1400 - OS Upgrade Repair Task Timeline
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}
// ⚠️ Run against MFA Kusto cluster
//
WinFabLogs
| where TIMESTAMP >= datetime({StartTime}) and TIMESTAMP < datetime({EndTime})
| where ClusterName =~ '{ClusterName}'
| where TaskName == "RM" and EventType == "Replica"
| where Text has "UpdateRepairExecutionState: RepairTask"
| extend subText = extract('(.*)JobId": "(.*)([a-zA-Z0-9])', 2, Text)
| extend JobId = extract('(.*)",(.*)([a-zA-Z0-9])', 1, subText)
| extend UD = extract('"UD"\\: ([0-9]+)', 1, subText)
| extend TaskId = extract("taskId=([a-zA-Z0-9._/-]+)", 1, Text)
| extend JobStatus = extract("result=([a-zA-Z0-9]+)", 1, Text)
| extend Action = split(extract("action=([a-zA-Z0-9.]+)", 1, Text), '.')[-1]
| extend ImpactedNodes = replace_string(replace_string(
    extract("nodeList = ([a-zA-Z0-9._() ]+)", 1, Text), '(', ''), ')', '')
| parse kind=relaxed Text with * "created=" Created ", claimed=" Claimed
    ", preparing=" Preparing "," * ", approved=" Approved
    ", executing=" Executing ", restoring=" Restoring "," *
| summarize arg_max(PreciseTimeStamp, *) by Restoring, ImpactedNodes, TaskId
| summarize arg_max(Restoring, *) by ImpactedNodes, TaskId, EventType, TaskName
| summarize arg_max(PreciseTimeStamp, *) by JobId, EventType, TaskName
| extend State = iif(JobStatus == 'Pending', 'Executing', 'Complete')
| project TaskId, UD, Created, Action,
    Preparing = iif(Preparing == '0', '', Preparing),
    Approved = iif(Approved == '0', '', Approved),
    Executing = iif(Executing == '0', '', Executing),
    Restoring = iif(Restoring == '0', '', Restoring),
    ImpactedNodes, State
| sort by Created asc
```

---

## LSASS1500 - Node Health State Lifecycle (MonClusterLoad)

Track node health state transitions during OS upgrades to understand the upgrade lifecycle.

**Purpose**: Map the node's transition through Ok/Up → Warning/Up → Disabling → Down → Disabled → Up phases.

**What to look for**:
- The `Warning/Up` phase — this is when Frozen VM events and LSASS spikes typically occur
- The transition from `Disabling` to `Down` — node being powered off for OS swap
- `node_up_time` resets when the node comes back with the new OS
- 🚩 Extended `Warning/Up` phases correlate with longer Frozen VM / LSASS impact

```kql
// LSASS1500 - Node Health State Lifecycle
// Required Parameters: {StartTime}, {EndTime}, {ClusterName}, {DBNodeName}
//
MonClusterLoad
| where event == "node_state_report"
| where TIMESTAMP between (datetime({StartTime}) .. datetime({EndTime}))
| where ClusterName =~ '{ClusterName}' and node_name =~ '{DBNodeName}'
| project TIMESTAMP, health_state, node_status, node_name, ClusterName, node_up_time
| sort by TIMESTAMP asc
```

---

## LSASS1600 - Multi-Cluster LSASS Spike + ImageStore Correlation

Scan multiple clusters for extreme LSASS spikes (>1000%) and automatically correlate each spike with ImageStore replica movements and repair task windows. This is the key evidence query for proving or disproving ImageStore as the trigger across a fleet.

**Purpose**: Across a list of clusters, find all extreme LSASS spikes, classify them as repair-explained or unexplained, and check if ImageStore moves preceded the spike.

> **⚠️ CONNECTION**: Execute against the MFA Kusto cluster. Replace `{KustoMfaCluster}` and `{ClusterList}` with actual values.

**What to look for**:
- `ImageStorePreceded = true` — ImageStore move landed on the node within 10 min before the spike
- `SpikeType = UNEXPLAINED` — spike not overlapping a repair task window (stronger signal)
- 🚩 Most severe spikes being ImageStore-correlated confirms Pattern 6 as fleet-wide root cause

```kql
// LSASS1600 - Multi-Cluster LSASS Spike + ImageStore Correlation
// Required Parameters: {StartTime}, {EndTime}, {ClusterList} (dynamic array), {KustoMfaCluster}
// ⚠️ Run against MFA Kusto cluster
//
let _kustoCluster = '{KustoMfaCluster}';
let _clusters = {ClusterList};
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
let _lsassThreshold = 1000.0;
let _repairMarginBefore = 10m;
let _imgLookback = 10m;
let regExNodeName="([A-Z0-9\\.\\_]+)";
let regExNodeInfo=strcat("([a-z0-9]+) ", regExNodeName, " \\(");
let nodeInfo = materialize (
    cluster(_kustoCluster).database("sqlazure1").WinFabLogs
    | where ClusterName in (_clusters)
    | where EventType == "NodeLoads" and TaskName == "PLB"
    | extend node_info = split(Text, "\r")
    | mvexpand node_info
    | extend TargetNodeId = extract(regExNodeInfo, 1, trim("\t", tostring(node_info)), typeof(string))
    | extend TargetNodeName = extract(regExNodeInfo, 2, trim("\t", tostring(node_info)), typeof(string))
    | where isnotempty(TargetNodeId) and isnotempty(TargetNodeName)
    | summarize by ClusterName, NodeId=TargetNodeId, NodeName=TargetNodeName
);
let repairWindows =
    cluster(_kustoCluster).database("sqlazure1").WinFabLogs
    | where TIMESTAMP between((_startTime - 1h) .. (_endTime + 1h))
    | where ClusterName in (_clusters)
    | where TaskName == "RM" and EventType == "Replica"
    | where Text has "UpdateRepairExecutionState: RepairTask"
    | extend ImpactedNodes = replace_string(replace_string(
        extract("nodeList = ([a-zA-Z0-9._() ]+)", 1, Text), '(', ''), ')', '')
    | parse kind=relaxed Text with * "created=" Created "," * "preparing=" Preparing "," *
        "executing=" Executing ", restoring=" Restoring "," *
    | where isnotempty(Executing) and Executing != "0"
    | extend NodeList = split(trim(" ", ImpactedNodes), " ")
    | mv-expand NodeName = NodeList to typeof(string)
    | where isnotempty(NodeName)
    | extend CreatedTime = todatetime(Created), RestoreTime = todatetime(Restoring)
    | summarize RepairStart=min(CreatedTime), RepairEnd=max(RestoreTime) by ClusterName, NodeName;
let lsassSpikes =
    cluster(_kustoCluster).database("sqlazure1").MonCounterOneMinute
    | where TIMESTAMP between(_startTime .. _endTime)
    | where ClusterName in (_clusters)
    | where CounterName == "\\Process(Lsass)\\% Processor Time"
    | where MaxVal >= _lsassThreshold
    | project ClusterName, NodeName, Minute=bin(TIMESTAMP, 1m), LsassCpu=MaxVal
    | sort by ClusterName asc, NodeName asc, Minute asc
    | serialize
    | extend PrevMinute = prev(Minute), PrevNode = prev(NodeName), PrevCluster = prev(ClusterName)
    | extend IsNewSpike = not(ClusterName == PrevCluster and NodeName == PrevNode and Minute - PrevMinute <= 2m)
    | extend SpikeId = row_cumsum(toint(IsNewSpike))
    | summarize SpikeStart=min(Minute), SpikeEnd=max(Minute)+1m, PeakLsass=max(LsassCpu),
        SpikeMinutes=count() by ClusterName, NodeName, SpikeId
    | project-away SpikeId;
let classifiedSpikes =
    lsassSpikes
    | join kind=leftouter (repairWindows) on ClusterName, NodeName
    | extend Overlaps = isnotempty(RepairStart) and
        SpikeStart >= (RepairStart - _repairMarginBefore) and SpikeStart <= RepairEnd
    | summarize IsExplained=max(Overlaps), SpikeStart=min(SpikeStart), SpikeEnd=min(SpikeEnd),
        PeakLsass=max(PeakLsass), SpikeMinutes=max(SpikeMinutes)
        by ClusterName, NodeName, tostring(SpikeStart), tostring(SpikeEnd)
    | extend SpikeType = iif(IsExplained, "REPAIR", "UNEXPLAINED")
    | project ClusterName, NodeName, SpikeStart, SpikeEnd, PeakLsass, SpikeMinutes, SpikeType;
let imgStoreMoves =
    cluster(_kustoCluster).database("sqlazure1").WinFabLogs
    | where TIMESTAMP between(_startTime .. _endTime)
    | where ClusterName in (_clusters)
    | where TaskName == "CRM" and EventType == "Operation"
    | where Text contains "Phase: " and Text contains "Action: " and Text contains "DecisionId: "
    | extend ServiceName = extract("Service: ([\\.\\-/:a-zA-Z|0-9]+) \r", 1, Text)
    | where ServiceName has "ImageStoreService"
    | extend Action = extract("Action: ([A-Za-z]+) \r", 1, Text),
        SourceNodeId = extract("SourceNode: ([a-zA-Z0-9]+)\r", 1, Text),
        TargetNodeId = extract("TargetNode: ([a-zA-Z0-9]+)\r", 1, Text)
    | extend DecisionId = toguid(extract("DecisionId: ([[a-z|A-Z|0-9|-]+)\r", 1, Text))
    | join kind=leftouter
        (
        cluster(_kustoCluster).database("sqlazure1").WinFabLogs
        | where ETWTimestamp between(_startTime .. _endTime)
        | where ClusterName in (_clusters)
        | where TaskName == "PLB" and EventType == "SchedulerAction"
        | where Text contains "Constraint Violations: "
            and ((Text contains " NodeCapacity"
                and Text contains "[MetricName, Load, Capacity, NodeId, NodeName")
            or (Text contains " Affinity ")
            or (Text contains "FaultDomain"))
        | extend DecisionId = toguid(extract("DecisionId: (.+)[[:space:]]Affects Service", 1, Text)),
            ConstraintType = extract("--\\[([a-zA-Z0-9_]+), [0-9]+, [0-9]+, [a-zA-Z0-9]+, [A-Z0-9\\.\\_]+, N/A\\]", 1, Text)
        | extend ConstraintType = iff(isempty(ConstraintType)
            and Text !contains "[MetricName, Load, Capacity, NodeId, NodeName, ApplicationName]",
            iff(Text contains "Affinity", "Affinity", "FaultDomain"), ConstraintType)
        | project ClusterName, DecisionId, ConstraintType
        )
        on ClusterName, DecisionId
    | join kind=leftouter (nodeInfo | project-rename SourceNodeName=NodeName)
        on ClusterName, $left.SourceNodeId == $right.NodeId
    | join kind=leftouter (nodeInfo | project-rename TargetNodeName=NodeName)
        on ClusterName, $left.TargetNodeId == $right.NodeId
    | where Action in ("AddSecondary", "MoveSecondary", "MovePrimary", "SwapPrimarySecondary")
    | project ClusterName, ImgStoreTime=ETWTimestamp, ImgNodeName=TargetNodeName,
        ImgAction=strcat(Action, " from ", SourceNodeName),
        ConstraintType;
classifiedSpikes
| join kind=leftouter (imgStoreMoves) on ClusterName, $left.NodeName == $right.ImgNodeName
| extend ImgNearSpike = isnotempty(ImgStoreTime) and
    ImgStoreTime between((todatetime(SpikeStart) - _imgLookback) .. todatetime(SpikeEnd))
| summarize
    ImgStoreDetail = strcat_array(make_list_if(
        strcat(format_datetime(ImgStoreTime, 'HH:mm:ss'), " ", ImgAction,
            iif(isnotempty(ConstraintType), strcat(" [", ConstraintType, "]"), "")),
        ImgNearSpike), "; ")
    by ClusterName, NodeName, SpikeStart, SpikeEnd, PeakLsass, SpikeMinutes, SpikeType
| extend ImageStorePreceded = isnotempty(ImgStoreDetail)
| sort by ClusterName asc, todatetime(SpikeStart) asc
| project Cluster = extract("^([a-z0-9]+)", 1, ClusterName), NodeName,
    SpikeWindow = strcat(substring(SpikeStart, 11, 5), "-", substring(SpikeEnd, 11, 5)),
    PeakLsass = round(PeakLsass, 1), SpikeMinutes, SpikeType, ImageStorePreceded, ImgStoreDetail
```

---

## Related Resources

- [SKILL.md](../SKILL.md) - Main LSASS Telemetry Hole Analysis skill documentation
- [Node Level CPU Analysis](../../CPU/references/node-level-cpu.md) - Detailed per-core CPU analysis with affinity mask parsing
