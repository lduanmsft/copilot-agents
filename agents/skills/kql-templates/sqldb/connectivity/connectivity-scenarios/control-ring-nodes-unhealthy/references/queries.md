# Kusto Queries for Control Ring Nodes Unhealthy Diagnosis

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (ISO 8601 format)
- `{EndTime}`: End timestamp in UTC (ISO 8601 format)

**Infrastructure identifiers:**
- `{ClusterName}`: Control Ring FQDN (e.g., `cr6.chinanorth2-a.control.database.chinacloudapi.cn`)

**Note:** This skill operates at the **cluster level** — there is no `{NodeName}` parameter. Queries aggregate across all GW nodes in the cluster.

---

## Step 2: Scope Assessment

### CRNU100 - Per-Node Login Success Rate Across the Cluster

**Purpose:** Scope assessment — identify which GW nodes are unhealthy and compute the percentage of unhealthy nodes. This is the primary scoping query for the cluster-level alert.

**What to look for:**
- Nodes with `LoginSuccessRate` < 95% are unhealthy
- Count unhealthy nodes / total nodes → confirm ≥20% threshold that triggered the alert
- If ALL nodes below 95% → cluster-wide failure (AliasDB, networking, deployment)
- If a subset → node-specific signals are breaching

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where AppTypeName =~ 'Gateway'
| summarize
    TotalLogins = count(),
    SystemErrors = countif(is_success == false and is_user_error == false),
    UserErrors = countif(is_success == false and is_user_error == true),
    DistinctServers = dcount(logical_server_name)
    by NodeName
| extend LoginSuccessRate = round(100.0 * (TotalLogins - SystemErrors) / TotalLogins, 2)
| extend SystemErrorRate = round(100.0 * SystemErrors / TotalLogins, 2)
| order by LoginSuccessRate asc
```

**Expected output:**
- **NodeName**: GW node identifier (e.g., `_GW_10`)
- **TotalLogins**: Total login attempts processed by the node
- **SystemErrors**: Non-user errors (infrastructure failures)
- **UserErrors**: User-caused errors (excluded from success rate)
- **DistinctServers**: Number of unique logical servers with traffic
- **LoginSuccessRate**: `(Total - SystemErrors) / Total * 100`
- **SystemErrorRate**: `SystemErrors / Total * 100`

---

### CRNU110 - Node Health Summary (Total vs Unhealthy)

**Purpose:** Aggregate CRNU100 results into a single summary showing the percentage of unhealthy nodes and confirming the rollup alert threshold.

**What to look for:**
- `UnhealthyPercentage` ≥ 20% → confirms the alert triggered correctly
- `UnhealthyPercentage` < 20% → alert may have auto-resolved or the issue was transient

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
let PerNodeStats = MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where AppTypeName =~ 'Gateway'
| summarize
    TotalLogins = count(),
    SystemErrors = countif(is_success == false and is_user_error == false)
    by NodeName
| extend LoginSuccessRate = round(100.0 * (TotalLogins - SystemErrors) / TotalLogins, 2)
| extend IsUnhealthy = iff(LoginSuccessRate < 95, true, false);
PerNodeStats
| summarize
    TotalNodes = dcount(NodeName),
    UnhealthyNodes = dcountif(NodeName, IsUnhealthy),
    MinSuccessRate = min(LoginSuccessRate),
    AvgSuccessRate = round(avg(LoginSuccessRate), 2)
| extend UnhealthyPercentage = iff(TotalNodes == 0, real(null), round(100.0 * UnhealthyNodes / TotalNodes, 1))
```

**Expected output:**
- **TotalNodes**: Total GW nodes in the cluster
- **UnhealthyNodes**: Nodes with LoginSuccessRate < 95%
- **UnhealthyPercentage**: UnhealthyNodes / TotalNodes * 100
- **MinSuccessRate**: Worst-performing node's success rate
- **AvgSuccessRate**: Average success rate across the cluster

---

## Step 3: Common Cluster-Wide Patterns

### CRNU200 - GW Deployment / Upgrade Check

**Purpose:** Check if a deployment or upgrade was in progress during the incident window. Deployments are the second most common cause of cluster-level unhealthy alerts.

**What to look for:**
- Active `MonRolloutProgress` entries → deployment in progress
- If deployment overlaps with incident window → likely self-mitigates after completion, but continue investigation in case the deployment itself is the trigger

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRolloutProgress
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where application_type_name == "Gateway" or application_name == "fabric:/Gateway"
| where event in ("start_upgrade_app_type", "app_instance_upgrade_progress", "start_upgrade_app_instance", "start_pause_upgrade_app_type", "start_resume_upgrade_app_type", "set_start_post_bake_blast")
| project originalEventTimestamp, event, target_version, upgrade_state, upgrade_progress, bake_start_time, bake_duration, rollout_key
| extend RolloutKeyCab = extract("^([0-9]*)_(.*)", 1, rollout_key)
| project-away rollout_key
| order by originalEventTimestamp asc
```

**Expected output:**
- **event**: Type of deployment event (e.g., `start_upgrade_app_type`, `app_instance_upgrade_progress`)
- **target_version**: Version being deployed
- **upgrade_state / upgrade_progress**: Current deployment state
- **bake_start_time / bake_duration**: Bake window for the rollout
- **RolloutKeyCab**: Extracted CAB number from the rollout key

---

### CRNU210 - GW Process Restarts Across Cluster

**Purpose:** Detect GW process instability across the cluster by counting distinct process IDs per node. Multiple process IDs on a node indicate process restarts.

**What to look for:**
- Nodes with `TotalProcesses` > 1 → GW process restarted
- Multiple nodes with restarts simultaneously → cluster-wide issue (deployment, platform event)
- Single node with many restarts → node-isolated crash loop

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where AppTypeName =~ 'Gateway'
| summarize
    TotalProcesses = dcount(process_id, 4),
    FirstSeen = min(originalEventTimestamp),
    LastSeen = max(originalEventTimestamp)
    by NodeName
| where TotalProcesses > 1
| order by TotalProcesses desc
```

**Expected output:**
- **NodeName**: Node with process restarts
- **TotalProcesses**: Number of distinct process IDs — 1 is normal, > 1 indicates restarts
- **FirstSeen / LastSeen**: Time range of activity on this node

---

## Step 4: Breaching Health Signal Detection

### CRNU300 - LSASS CPU Stress Per Node

**Purpose:** Check LSASS % Privileged Time on each GW node to detect authentication-related stress. Elevated LSASS CPU causes authentication delays which cascade into login failures and TCP rejections.

**What to look for:**
- `AvgLsassPrivilegedTimePct` > 50% → 🚩 LSASS stress on the node
- `MaxLsassPrivilegedTimePct` > 100% → 🚩 Severe authentication overload
- Correlate with unhealthy nodes from CRNU100 — if LSASS is elevated on the same nodes, it is a contributing signal

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonCounterOneMinute
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where CounterName == '\\Process(Lsass)\\% Privileged Time'
| summarize
    AvgLsassPrivilegedTimePct = round(avg(CounterValue), 1),
    MaxLsassPrivilegedTimePct = round(max(CounterValue), 1),
    SampleCount = count()
    by NodeName
| order by MaxLsassPrivilegedTimePct desc
```

**Expected output:**
- **NodeName**: GW node
- **AvgLsassPrivilegedTimePct**: Average LSASS CPU during the window
- **MaxLsassPrivilegedTimePct**: Peak LSASS CPU — > 50% is concerning, > 100% is critical

---

### CRNU310 - TCP Rejections Per Node

**Purpose:** Check TCP rejection rates on each GW node. Sustained rejections > 150/sec combined with handle count > 600K indicate the TCP rejection health signal is breaching.

**What to look for:**
- `AvgRejectedPerSec` > 150 AND `MaxHandleCount` > 600,000 → TCP rejection condition met
- Compare with unhealthy nodes from CRNU100 to correlate signals
- If TCP rejections present without login success degradation → non-login signal causing unhealthy

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
let TcpRejections = MonCounterOneMinute
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where CounterName == '\\Microsoft Winsock BSP\\Rejected Connections/sec'
| summarize AvgRejectedPerSec = round(avg(CounterValue), 1), MaxRejectedPerSec = round(max(CounterValue), 1) by NodeName;
let HandleCounts = MonCounterOneMinute
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where CounterName == '\\Process(_Total)\\Handle Count'
| summarize AvgHandleCount = round(avg(CounterValue), 0), MaxHandleCount = round(max(CounterValue), 0) by NodeName;
TcpRejections
| join kind=leftouter HandleCounts on NodeName
| where AvgRejectedPerSec > 0 or MaxRejectedPerSec > 0
| project NodeName, AvgRejectedPerSec, MaxRejectedPerSec, AvgHandleCount, MaxHandleCount
| order by MaxRejectedPerSec desc
```

**Expected output:**
- **NodeName**: GW node with TCP rejections
- **AvgRejectedPerSec / MaxRejectedPerSec**: TCP rejection rate
- **AvgHandleCount / MaxHandleCount**: Handle count (> 600K with rejections = resource exhaustion)

---

## Step 5: Auto-Mitigation Status

### CRNU400 - Automation Actions on the Cluster

**Purpose:** Check if `healthmanagesvc`, `SqlRunner`, or other automation has taken mitigation actions on the cluster during the incident window.

**What to look for:**
- `request_action` = `DumpProcess` or `KillProcess` targeting `xdbhostmain` or GW processes → automation acted
- `username` containing `healthmanagesvc` → auto-mitigation by health management service
- `username` containing `sqlrunnerv2` (e.g., `sqlrunnerv2.sqltelemetry.azclient.ms`) → SqlRunner automation
- Timing: If the last automation action is > 20 minutes old and health is recovering → likely mitigated

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonNonPiiAudit
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where request_action !in~ ('ExecuteCMSQuery', 'FabricClusters()', 'FabricNodes()', 'ExecuteCMSQueryJSON', 'ExecuteQuery') and request_action !startswith 'Get'
| project time_created, NodeName, username, request_action, request, parameters
| order by time_created desc
```

**Expected output:**
- **time_created**: When the action was taken
- **NodeName**: Node the action targeted
- **username**: Who initiated the action (e.g., `healthmanagesvc`, `sqlrunnerv2.sqltelemetry.azclient.ms`, or a human alias)
- **request_action**: Type of mitigation action (`DumpProcess`, `KillProcess`, `RestartCodePackage`, `RestartReplica`, etc.)
- **request / parameters**: Full request URI and parameters — inspect for `xdbhostmain` or GW process targeting

---

## Step 7: Impact Assessment

### CRNU500 - Distinct Impacted Servers and Subscriptions

**Purpose:** Quantify customer impact — count distinct logical servers and subscriptions experiencing system errors during the incident window.

**What to look for:**
- `DistinctServersWithErrors` > 100 → 🚩 significant customer-facing impact
- `DistinctSubscriptions` > 10 → 🚩 multiple customers affected
- Compare with CRNU110 to understand if impact is proportional to unhealthy node count

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where AppTypeName =~ 'Gateway'
| where is_success == false and is_user_error == false
| summarize
    DistinctServersWithErrors = dcount(logical_server_name),
    DistinctSubscriptions = dcount(subscription_id),
    TotalSystemErrors = count(),
    DistinctNodes = dcount(NodeName)
```

**Expected output:**
- **DistinctServersWithErrors**: Number of unique logical servers experiencing system errors
- **DistinctSubscriptions**: Number of unique subscriptions impacted
- **TotalSystemErrors**: Total system error count across the cluster
- **DistinctNodes**: Number of nodes contributing system errors
