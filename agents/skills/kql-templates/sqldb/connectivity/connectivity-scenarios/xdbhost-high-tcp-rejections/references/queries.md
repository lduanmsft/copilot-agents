!!!AI Generated. To be verified!!!

# Kusto Queries for XDBHost High TCP Rejections Diagnosis

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**

- `{StartTime}`: Start timestamp in UTC (ISO 8601 format)
- `{EndTime}`: End timestamp in UTC (ISO 8601 format)

**Infrastructure identifiers:**

- `{ClusterName}`: Tenant ring/cluster name (e.g., `tr6730.southeastasia1-a.worker.database.windows.net`)
- `{DBNodeName}`: DB node name (e.g., `_DB_59`)

**Resource identifiers (optional — used when logical names are known):**

- `{LogicalServerName}`: Logical server name (e.g., `csbphprdtdlsaassql`)
- `{LogicalDatabaseName}`: Logical database name (e.g., `htrunk`)

---

## Step 1: Confirm TCP Rejections

### TR100 - TCP Rejected Connections/sec on Node

**Purpose:** Confirm that TCP rejections are occurring on the node and determine the rejection window. This validates the Health Hierarchy alert.

**What to look for:**

- Sustained non-zero `MaxVal` values confirm TCP rejections
- 🚩 MaxVal > 50/sec indicates significant rejection pressure
- Identify the start and end of the rejection window
- Compare the rejection window against the LSASS stress window (TR200)

```kql
let StartTime = todatetime('{StartTime}');
let EndTime = todatetime('{EndTime}');
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonCounterOneMinute
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar
| where NodeName =~ _NodeNameVar
| where CounterName == '\\Microsoft Winsock BSP\\Rejected Connections/sec'
| project TIMESTAMP, MaxVal
| order by TIMESTAMP asc
```

**Expected output:**

- **TIMESTAMP**: When the measurement was taken
- **MaxVal**: Peak rejected connections per second in that minute

---

## Step 2: Check LSASS CPU Stress

### TR200 - LSASS % Privileged Time on Node

**Purpose:** Determine if LSASS (Local Security Authority Subsystem Service) is under CPU stress, which is the most common driver of XdbHost high TCP rejections. LSASS handles Kerberos authentication; when it is overloaded, XdbHost IOCP threads stall waiting for authentication completions.

**What to look for:**

- Normal: LSASS % Privileged Time < 10%
- 🚩 > 50% indicates authentication stress
- 🚩 Sustained > 100% directly correlates with XdbHost stalls and TCP rejections
- Correlate the LSASS elevation start with the TCP rejection start from TR100

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonCounterOneMinute
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar
| where NodeName =~ _NodeNameVar
| where CounterName == '\\Process(Lsass)\\% Privileged Time'
| project TIMESTAMP, MaxVal
| order by TIMESTAMP asc
```

**Expected output:**

- **TIMESTAMP**: When the measurement was taken
- **MaxVal**: Peak LSASS privileged CPU time percentage in that minute

---

## Step 3: Confirm XdbHost Crash Loop

### TR300 - Detect XdbHost Process ID Changes (Crash Loop Confirmation)

**Purpose:** Confirm that XdbHost is in a crash-restart loop by detecting multiple process_id changes. Unlike a single XdbHost restart (xdbhost-restart skill), high TCP rejection incidents typically show many rapid process_id changes.

**What to look for:**

- Multiple process_id values (> 3) = crash loop, not a single restart
- 🚩 > 10 process IDs in a 2-hour window = severe crash loop
- Short-lived processes (< 5 minutes each) indicate the process crashes shortly after starting
- Record the total number of restarts and the overall crash loop duration

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonXdbhost
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar and NodeName =~ _NodeNameVar
| summarize min_time = min(TIMESTAMP), max_time = max(TIMESTAMP)
    by process_id
| order by min_time asc
```

**Expected output:**

- **process_id**: XdbHost process identifier — many different values confirm crash loop
- **min_time / max_time**: First and last seen timestamp for each process — short-lived processes indicate rapid cycling

---

## Step 4: Analyze Dump Activity

### TR400 - XdbHost Dump Activity on Node

**Purpose:** Identify the dump types driving the crash loop. The pattern of dump types reveals whether the crash is caused by IOCP stalls (Stalled IOCP Listener) or unhandled exceptions (SqlDumpExceptionHandler).

**What to look for:**

- **Stalled IOCP Listener** (DumpErrorDetails) — XdbHost IOCP threads are blocked, often due to LSASS contention
- **SqlDumpExceptionHandler** (DumpErrorText) — XdbHost crashed after a dump was triggered
- Stack traces containing `SocketDupInstance::DestroyConnectionObjects_v2` — confirms connection close path issues
- 🚩 Alternating `Stalled IOCP Listener` → `SqlDumpExceptionHandler` confirms the dump-crash-restart cycle
- Count total dumps and classify by DumpErrorText

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonSqlDumperActivity
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar
| where NodeName =~ _NodeNameVar
| project DumperStartTime, TargetProcess, DumpUID, DumpErrorText, DumpErrorDetails
| order by DumperStartTime asc
```

**Expected output:**

- **DumperStartTime**: When the dump was initiated
- **TargetProcess**: Process being dumped (typically `xdbhostmain.exe`, sometimes `sqlservr.exe`)
- **DumpUID**: Unique dump identifier
- **DumpErrorText**: Dump trigger category (`Stack Trace`, `Program fault handler`)
- **DumpErrorDetails**: Specific reason (`Stalled IOCP Listener`, `SqlDumpExceptionHandler`)

---

## Step 5: Check Automation Actions

### TR500 - Audit Trail for Automation/User Actions on Node

**Purpose:** Check if SqlRunner or other automation issued DumpProcess or KillProcess actions targeting XdbHost on this node during the incident.

**What to look for:**

- `DumpProcess` targeting `xdbhostmain` — SqlRunner triggered a diagnostic dump
- `KillProcess` targeting `xdbhostmain` — SqlRunner killed XdbHost to attempt recovery
- `KillProcess` targeting `sqlservr` — indicates escalation to SQL Server process kill
- 🚩 Multiple KillProcess actions indicate automated recovery attempts failed
- Correlate action timestamps with the crash loop timeline from TR300

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonNonPiiAudit
| where TIMESTAMP between (_startTime.._endTime)
| where * contains _ClusterNameVar and * contains _NodeNameVar
| where request_action !in~ ('ExecuteCMSQuery', 'FabricClusters()', 'FabricNodes()', 'ExecuteCMSQueryJSON', 'ExecuteQuery') and request_action !startswith 'Get'
| project time_created, username, request_action, request, parameters
| order by time_created asc
```

**Expected output:**

- **time_created**: When the action was executed
- **username**: Who initiated the action (e.g., `sqlrunnerv2.sqltelemetry.azclient.ms`)
- **request_action**: Action type (`DumpProcess`, `KillProcess`)
- **request**: Full request URI — check for `xdbhostmain` to confirm XdbHost targeting
- **parameters**: Additional parameters — check for `xdbhostmain`

---

## Step 6: Identify Impacted Instances and Login Volume

### TR600 - Login Count by Instance on Node

**Purpose:** Determine which instances on the node were impacted and whether one instance dominates login volume, potentially driving the LSASS stress.

**What to look for:**

- One instance with vastly more logins than others may be the driver
- 🚩 > 100,000 logins from a single instance in a 2-hour window is very high
- Total login count across all instances on the node during the window

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonLogin
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar
| where NodeName =~ _NodeNameVar
| where event == 'process_login_finish'
| where package == 'xdbhost'
| summarize LoginCount = count() by instance_name
| order by LoginCount desc
```

**Expected output:**

- **instance_name**: SQL instance on the node
- **LoginCount**: Total logins during the window

### TR610 - Login Volume per XdbHost Process ID (5-min bins)

**Purpose:** Visualize the crash-restart cycle from the login perspective. Each process_id series should show a spike then drop as the process crashes.

**What to look for:**

- Each process_id series shows a spike then abrupt drop — confirms crash pattern
- High login volume on each new process = immediate reconnect storm after each restart
- 🚩 > 60,000 logins per 5-minute bin on the node = extreme login pressure

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonLogin
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar
| where NodeName =~ _NodeNameVar
| where event == 'process_login_finish'
| where package == 'xdbhost'
| summarize LoginCount = count()
    by strcat(process_id, '__', code_package_version), bin(originalEventTimestamp, 5m)
| order by originalEventTimestamp asc
```

**Expected output:**

- **process_id__version**: Process ID and code version — each unique value = one XdbHost instance lifecycle
- **originalEventTimestamp**: 5-minute time bin
- **LoginCount**: Login attempts in that bin for that process

---

## Step 7: Check Instance Resource Utilization

### TR700 - Instance Resource Stats on Node

**Purpose:** Determine if resource exhaustion on a specific instance contributed to the node stress. High worker/session/CPU percentages indicate the instance is saturated.

**What to look for:**

- 🚩 `max_worker_percent` at 100% = worker thread exhaustion
- 🚩 `max_session_percent` at 100% = session limit reached
- 🚩 `avg_instance_cpu_percent` > 90% = instance-level CPU exhaustion
- Correlate resource spikes with the LSASS elevation and crash loop timeline

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonDmRealTimeResourceStats
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar and NodeName =~ _NodeNameVar
| summarize max_avg_cpu = max(avg_cpu_percent),
            max_avg_memory = max(avg_memory_usage_percent),
            max_avg_instance_cpu = max(avg_instance_cpu_percent),
            max_worker_pct = max(max_worker_percent),
            max_session_pct = max(max_session_percent),
            max_login_rate_pct = max(avg_login_rate_percent)
    by AppName, bin(originalEventTimestamp, 5m)
| order by originalEventTimestamp asc
```

**Expected output:**

- **AppName**: SQL instance identifier
- **max_avg_cpu / max_avg_memory / max_avg_instance_cpu**: Resource utilization percentages
- **max_worker_pct / max_session_pct**: Worker thread and session utilization percentages
- **max_login_rate_pct**: Login rate percentage

---

## Step 8: Check TCP Port Statistics

### TR800 - TCP Port Statistics on Node

**Purpose:** Check TCP port usage and connection state on the node to identify port exhaustion or connection accumulation that could contribute to rejections.

**What to look for:**

- `Established_Conn` spike correlating with the incident window
- 🚩 `AvailableDynamicPortsPercentage` < 95% indicates port pressure
- `Bound_Ports` increase may indicate connection accumulation
- Compare CloseWait_Conn and TimeWait_Conn for connection state buildup

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
AlrWinFabHealthNodeEvent
| where TIMESTAMP between (_startTime.._endTime)
| where Property == 'PortUseWatchdog'
| where ClusterName =~ _ClusterNameVar and NodeEntityName =~ _NodeNameVar
| where Description contains 'TcpStats:'
| project TIMESTAMP, Description, NodeEntityName, ClusterName
| extend TcpStats = extract(".*?TcpStats: (.*)", 1, Description)
| extend TcpStatsArray = split(TcpStats, ",")
| mv-expand TcpStatsArray
| extend TcpStatsKeyValue = split(TcpStatsArray, "=")
| summarize TcpStatsValues = make_bag(pack(tostring(TcpStatsKeyValue[0]), tostring(TcpStatsKeyValue[1])))
    by TIMESTAMP, ClusterName, NodeEntityName
| evaluate bag_unpack(TcpStatsValues)
| order by TIMESTAMP asc
```

**Expected output:**

- **TIMESTAMP**: Measurement time
- **AvailableDynamicPortsPercentage**: Available port percentage (🚩 < 95% is concerning)
- **Established_Conn / Established_Ports**: Active TCP connections
- **Bound_Conn / Bound_Ports**: Bound socket count
- **CloseWait_Conn / TimeWait_Conn**: Connection states indicating cleanup backlog
- **Listen_Conn / SynSent_Conn**: Listening and pending connection counts

---

## Optional: Login Volume for Specific Database

### TR900 - Login Volume for Specific Logical Server/Database (1-min bins)

**Purpose:** When the logical server and database name are known (from ICM discussion or DBINFO reverse lookup), query the login volume to confirm whether a specific workload is driving the node stress.

**Requires:** `{LogicalServerName}` and `{LogicalDatabaseName}` must be known.

**What to look for:**

- Spike in login volume correlating with the crash loop window
- Compare 7-day history to determine if this is a one-off or recurring workload
- 🚩 > 5000 logins/minute for a single database is extremely high

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where TIMESTAMP between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where event == 'process_login_finish'
| summarize LoginCount = count()
    by package, bin(originalEventTimestamp, 1m)
| order by originalEventTimestamp asc
```

**Expected output:**

- **package**: Login processing package (`xdbhost`, `xdbgateway`, `sqlserver`)
- **originalEventTimestamp**: 1-minute time bin
- **LoginCount**: Login count per minute per package

### TR910 - Login Volume 7-Day History for Specific Database

**Purpose:** Determine if the login volume spike is a one-off event or a recurring pattern.

**Requires:** `{LogicalServerName}` and `{LogicalDatabaseName}` must be known.

```kql
let EndTime = datetime({EndTime});
let StartTime = EndTime - 7d;
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where TIMESTAMP between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where event == 'process_login_finish'
| summarize LoginCount = count()
    by package, bin(originalEventTimestamp, 5m)
| order by originalEventTimestamp asc
```

**Expected output:**

- **package**: Login processing package
- **originalEventTimestamp**: 5-minute time bin
- **LoginCount**: Login count per bin — look for isolated spike vs recurring pattern
