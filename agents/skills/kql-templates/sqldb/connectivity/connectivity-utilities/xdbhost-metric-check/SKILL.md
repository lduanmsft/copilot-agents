---
name: xdbhost-metric-check
description: This skill helps to check the common metrics on the DB node where XDBHOST resides. Metrics include TCP rejection, Average Time spent in SSL APIs, CPU usage, Memory usage, etc. The skill can help to screen if there is any issue on XDBHOST which causes the connectivity problem.
---

Please perform the following checks to see if there is any issue on the XDBHOST which causes the connectivity problem. 

**Important**: Please perform all the steps and substeps in the skill, and output the result after each step. Human judgement is required for the output of each step, please DO NOT skip any step.

## Step 1: Check if there is TCP rejection on the DB node where XDBHOST resides.
Use the following Kusto query to check if there is TCP rejection on the DB node where XDBHOST resides:

```
//Sample Kusto Query:
let _ClusterNameVar ='tr8843.westus1-a.worker.database.windows.net';
let _NodeNameVar = '_DB_39';
let _endTime = datetime(2026-01-17T21:40:00Z);
let _startTime = datetime(2026-01-17T18:47:00Z);
MonCounterOneMinute
| where TIMESTAMP between (_startTime.._endTime)
| where ClusterName =~ _ClusterNameVar and NodeName =~ _NodeNameVar
| where CounterName == "\\Microsoft Winsock BSP\\Rejected Connections/sec"
| project TIMESTAMP, CounterName, CounterValue
```

Sample Output:
TIMESTAMP	CounterName	CounterValue
2026-01-17 20:04:00.0000000	\Microsoft Winsock BSP\Rejected Connections/sec	8.14192778737544
2026-01-17 20:05:00.0000000	\Microsoft Winsock BSP\Rejected Connections/sec	58.6890418689547
2026-01-17 20:06:00.0000000	\Microsoft Winsock BSP\Rejected Connections/sec	189.732681758511
2026-01-17 20:07:00.0000000	\Microsoft Winsock BSP\Rejected Connections/sec	132.762095137017
2026-01-17 20:08:00.0000000	\Microsoft Winsock BSP\Rejected Connections/sec	166.408860186657
2026-01-17 20:09:00.0000000	\Microsoft Winsock BSP\Rejected Connections/sec	154.160288099886
2026-01-17 20:10:00.0000000	\Microsoft Winsock BSP\Rejected Connections/sec	200.904628090222
2026-01-17 20:11:00.0000000	\Microsoft Winsock BSP\Rejected Connections/sec	139.968141508049


Note:
1. The variables are:
   - `_ClusterNameVar`: The name of the Tenant Ring cluster.
   - `_NodeNameVar`: The name of the DB node.
   - `_startTime`: The start time for the query.
   - `_endTime`: The end time for the query.

2. If the counter value of "\Microsoft Winsock BSP\Rejected Connections/sec" is above 80, output a warning message to the user, which means there is TCP rejection on the DB node where XDBHOST resides.

## Step 2: Check if there is high Average Time spent in SSL APIs on the DB node where XDBHOST resides.
Use the following Kusto query to check if there is high Average Time spent in SSL APIs on the DB node where XDBHOST resides:

```
//Sample Kusto Query:
let _ClusterNameVar ='tr8843.westus1-a.worker.database.windows.net';
let _NodeNameVar = '_DB_39';
let _endTime = datetime(2026-01-17T21:40:00Z);
let _startTime = datetime(2026-01-17T18:47:00Z);
MonLogin
| where originalEventTimestamp between (_startTime.._endTime)
| where ClusterName =~ _ClusterNameVar and NodeName =~ _NodeNameVar
| where event =~ 'process_login_finish' and AppName =~ 'worker'
| project originalEventTimestamp, ssl_secure_call_time_ms
|summarize avg(ssl_secure_call_time_ms) by bin(originalEventTimestamp, 1m)
```
Note:
1. The variables are: 
    - `_ClusterNameVar`: The name of the Tenant Ring cluster.
    - `_NodeNameVar`: The name of the DB node.
    - `_startTime`: The start time for the query.
    - `_endTime`: The end time for the query.
2. If the average time spent in SSL APIs is above 500ms, output a warning message to the user.

## Step 3: Check which Instances are contributing to the high login volume on the DB node where XDBHOST resides and if this instance exceeds the threshold for the designed login capacity.

### Step 3.1: Use the following Kusto query to check which Instances are contributing to the high login volume on the DB node where XDBHOST resides:

```
//Sample Kusto Query:
let _ClusterNameVar ='tr8843.westus1-a.worker.database.windows.net';
let _NodeNameVar = '_DB_39';
let _endTime = datetime(2026-01-17T21:40:00Z);
let _startTime = datetime(2026-01-17T18:47:00Z);
MonLogin
| where originalEventTimestamp between (_startTime.._endTime)
| where ClusterName =~ _ClusterNameVar and NodeName =~ _NodeNameVar
| where event =~ 'process_login_finish' and AppName =~ 'worker'
| extend instance_id =
    iif(instance_name has @"\",
        tostring(split(instance_name, @"\")[array_length(split(instance_name, @"\")) - 1]),
        tostring(split(instance_name, ".")[0]))
| make-series count() default = 0 on originalEventTimestamp from bin(_startTime, 1m) to bin(_endTime, 1m) step 1m by instance_id
```

Note:
1. The variables are: 
    - `_ClusterNameVar`: The name of the Tenant Ring cluster.
    - `_NodeNameVar`: The name of the DB node.
    - `_startTime`: The start time for the query.
    - `_endTime`: The end time for the query.

2. If some instances have much higher login volume than others, output the instance_id of these instances to the user, which means these instances are contributing to the high login volume on the DB node where XDBHOST resides.

### Step 3.2: Check if the instance with high login volume exceeds the threshold for the designed login capacity:

#### Instruction: Run the kusto query xdbhost-metric-q320.kql
##### Input:
The Kusto variables used are as follows:

    - `ClusterNameVar`: The name of the Tenant Ring cluster.
    - `NodeNameVar`: The name of the DB node.
    - `SqlInstances`: The instance_id of the SQL instance with high login volume.
    - `_startTime`: The start time for the query.
    - `_endTime`: The end time for the query.

Note: DO NOT change the rest of the query input. tempVmSizes is a fixed table which has the designed login capacity for different VM sizes. 


#### Output:
If the ActualLogins is above the LoginRateCapPerMin, output a warning message to the user, which means the instance with high login volume exceeds the threshold for the designed login capacity, which can cause performance issues on XDBHOST and further cause connectivity problems.


## Step 4: Check if there is high CPU usage 

### Step 4.1: Use the following skill to check if there is VM-level high CPU usage on the DB node where XDBHOST resides:
Follow skill ".github/skills/Connectivity/connectivity-utilities/cpu-usage-check/SKILL.md"
Notify user if CPU usage is above 70% for a long time (over 5 minutes).

### Step 4.2: Check if the instance has high CPU Core usage

#### Instruction: Run the kusto query xdbhost-metric-q420.kql
##### Input:
The Kusto variables used are as follows:

    - `ClusterNameVar`: The name of the Tenant Ring cluster.
    - `NodeNameVar`: The name of the DB node.
    - `SqlInstances`: The instance_id of the SQL instance with high login volume.
    - `_startTime`: The start time for the query.
    - `_endTime`: The end time for the query.

Note: DO NOT change the rest of the query input.

#### Sample Output:

TIMESTAMP	CounterName	MaxVal
2026-03-05 01:24:00.0000000	\Processor Information(1,39)\% Processor Time	100
2026-03-05 01:27:00.0000000	\Processor Information(1,39)\% Processor Time	99.8660061592145
2026-03-05 01:20:00.0000000	\Processor Information(1,39)\% Processor Time	100
2026-03-05 01:30:00.0000000	\Processor Information(1,39)\% Processor Time	100
2026-03-05 01:25:00.0000000	\Processor Information(1,39)\% Processor Time	99.7374826211395
2026-03-05 01:19:00.0000000	\Processor Information(1,39)\% Processor Time	100


Note: When CPU core usage (MaxVal) is above 90% over 3 minutes, output a warning message to the user indicating which cores have high CPU usage, which can cause performance issues on XDBHOST and further cause connectivity problems.

### Step 4.3: Check if there is high CPU usage for LSASS process on the DB node where XDBHOST resides

Sample Kusto Query:

```
let ClusterNameVar ='tr11099.westus2-a.worker.database.windows.net';
let NodeNameVar= '_DB_44'; 
let _startTime = datetime(2026-03-05T01:00:00Z);
let _endTime = datetime(2026-03-05T03:00:00Z);
MonCounterOneMinute
    | where TIMESTAMP  between(_startTime.._endTime)
    | where ClusterName =~ ClusterNameVar
    | where NodeName =~ NodeNameVar
    | where CounterName contains "xdbhost" or CounterName contains "lsass"
    | where CounterName contains "Processor Time"
    | make-series MaxVal = max(MaxVal) on TIMESTAMP from bin(_startTime, 5m) to bin(_endTime, 5m) step 1m by CounterName = strcat(NodeName, CounterName)
```

Note: When CPU usage (MaxVal) for LSASS process is above 100 over 3 minutes, output a warning message to the user. LSASS metric is a little complicated, do not focus on the value itself, but more on the trend.

## Step 5: Confirm XdbHost Restart

### Step 5.1: Detect Process ID Change (Restart Confirmation)

**Purpose:** Confirm that an XdbHost restart occurred by detecting a process_id change on the DB node. This is the definitive indicator of a restart.

**What to look for:**
- Two or more distinct `process_id` values within the time window
- A temporal gap between the `max(TIMESTAMP)` of the old process and `min(TIMESTAMP)` of the new process
- The gap duration approximates the restart time
- 🚩 Gap > 60 seconds is unusual and warrants investigation

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
- **process_id**: XdbHost process identifier — two different values confirm a restart
- **min_time / max_time**: First and last seen timestamp for each process

---

### Step 5.2: Check for Automation/User Actions on Node

**Purpose:** Check if any automation or user-initiated actions were executed against the node during the incident window. This helps identify whether an external action (e.g., kill) triggered the XdbHost restart.

**What to look for:**
- Entries where `request` or `parameters` contain `xdbhostmain` — these are actions directly targeting XdbHost
- 🚩 Actions targeting XdbHost around the restart timestamp are strong indicators of an externally triggered restart
- Entries targeting other processes (e.g., `sqlservr`) — list as informational context only; these may correlate but are not direct XdbHost triggers
- `request_action` values such as `KillProcess`, `ExecuteKillProcess` are high-signal indicators
- Read-only actions (`Get*`, `ExecuteCMSQuery`, etc.) are excluded by the query filter

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonNonPiiAudit
| where TIMESTAMP between (_startTime.._endTime)
| where * contains _ClusterNameVar and * contains _NodeNameVar
| where request_action !in~ ("ExecuteCMSQuery", "FabricClusters()", "FabricNodes()", "ExecuteCMSQueryJSON", "ExecuteQuery") and request_action !startswith "Get"
| project time_created, username, request_action, request, parameters
| order by time_created asc
```

**Expected output:**
- **time_created**: When the action was executed
- **username**: Who or what initiated the action (user alias, bot identity, or automation service)
- **request_action**: The type of action performed (e.g., KillProcess)
- **request**: The request details — check for `xdbhostmain` to confirm XdbHost targeting
- **parameters**: Additional parameters — check for `xdbhostmain` to confirm XdbHost targeting
