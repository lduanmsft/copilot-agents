# Kusto Queries for Gateway Node Low Login Success Rate Diagnosis

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (ISO 8601 format)
- `{EndTime}`: End timestamp in UTC (ISO 8601 format)

**Infrastructure identifiers:**
- `{ClusterName}`: Control Ring FQDN (e.g., `cr6.chinanorth2-a.control.database.chinacloudapi.cn`)
- `{NodeName}`: Affected GW node (e.g., `_GW_10`)

---

## Step 2: Scope Assessment

### GNLSR100 - Per-Node Login Success Rate Across the Cluster

**Purpose:** Scope assessment — determine if issue is isolated to the alerted node or extends to other nodes. Computes login success rate per node across the entire cluster.

**What to look for:**
- Nodes with `LoginSuccessRate` < 95% are failing
- If only 1 node is below threshold → node-isolated
- If multiple nodes are below threshold → multiple nodes affected
- 🚩 Multiple nodes affected with > 100 `DistinctServers` → escalate

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

### GNLSR110 - Count Distinct Impacted Servers

**Purpose:** Determine scale of impact — if > 100 distinct servers have system errors, potential CRISIS per TSG.

**What to look for:**
- `DistinctServersWithErrors` > 100 → 🚩 multiple nodes impacted, consider escalation
- Compare with GNLSR100 to confirm scope

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where is_success == false and is_user_error == false
| summarize
    DistinctServersWithErrors = dcount(logical_server_name),
    TotalSystemErrors = count()
```

**Expected output:**
- **DistinctServersWithErrors**: Number of unique servers experiencing system errors
- **TotalSystemErrors**: Total system error count across the cluster

---

## Step 3: Check Known Issues

### GNLSR200 - Trident Testing in Canary Rings

**Purpose:** Check if 40613/4 errors are from Trident testing. Match criteria: significant portion of failures in `TridentSqlResourceGroup`.

**What to look for:**
- `resource_group` = `TridentSqlResourceGroup` with high `NumberOfUniqueServers`
- If dominant → known issue, transfer to Synapse DW / Client Experiences team

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where AppTypeName =~ 'Gateway'
| where is_success == false
| where error == 40613 and state == 4
| summarize
    NumberOfUniqueServers = dcount(logical_server_name),
    any(logical_server_name)
    by lookup_state, resource_group, ClusterName
```

**Expected output:**
- **lookup_state**: The lookup state associated with the failure
- **resource_group**: Resource group name — look for `TridentSqlResourceGroup`
- **NumberOfUniqueServers**: Count of unique servers in this resource group with errors

---

### GNLSR210 - SQL Alias Failover + Cache Backoff (Error Check)

**Purpose:** Check for 40613/4 with `lookup_error_code = 2147500037` (E_FAIL) skewed to one node, indicating SQL Alias failover combined with cache backoff timer.

**What to look for:**
- `lookup_error_code = 2147500037` concentrated on one `NodeName`
- If found, also run GNLSR220 to confirm cache backoff timer activity
- 🚩 If both match → known issue: kill/restart GW process or wait for cache backoff to expire

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where AppTypeName =~ 'Gateway'
| where is_success == false
| where error == 40613 and state == 4
| summarize count() by error, state, is_success, is_user_error, NodeName, lookup_state, lookup_error_code
| order by count_ desc
```

**Expected output:**
- **NodeName**: Which GW node has the errors
- **lookup_error_code**: Look for `2147500037` (E_FAIL)
- **count_**: Error count — if skewed to one node, confirms node-isolated alias issue

---

### GNLSR220 - SQL Alias Cache Backoff Timer Activity

**Purpose:** Confirm alias cache backoff timer is active on the affected node. Run after GNLSR210 matches.

**What to look for:**
- Redirector events per node over time
- If the affected node shows reduced or absent cache refresh events → backoff timer is active

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRedirector
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event != 'error_log'
| summarize count() by strcat(event, '/', NodeName), bin(originalEventTimestamp, 1m)
| render stackedareachart
```

**Expected output:**
- Time-series chart showing redirector event activity per node
- A gap or drop in events on the affected node confirms cache backoff

---

### GNLSR230 - SF Version Behavior Change

**Purpose:** Check for `SERVICE_FABRIC-DOES-NOT_EXISTS` in `lookup_state` during deployments. This is a known SF behavior change.

**What to look for:**
- Non-zero counts of 40613/4 with `SERVICE_FABRIC-DOES-NOT_EXISTS` during the incident window
- If correlates with a deployment (check Step 9) → self-mitigates after deployment finishes
- Fixed in GW.18+ which treats this error as retriable/waitable

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where AppTypeName =~ 'Gateway'
| where is_success == false
| where error == 40613 and state == 4
| where lookup_state has "SERVICE_FABRIC-DOES-NOT_EXISTS"
| summarize count() by NodeName, bin(originalEventTimestamp, 5m)
| order by originalEventTimestamp asc
```

**Expected output:**
- **NodeName**: Affected nodes
- **originalEventTimestamp**: Time bins showing when errors occurred
- **count_**: Error volume per 5-minute bin

---

## Step 4: Error Distribution on Affected Node(s)

### GNLSR300 - Error/State Distribution (System Errors)

**Purpose:** Identify prevailing errors on the affected node, separating system vs user errors. If PG/MySQL `AppTypeName` is top contributor, transfer to RDBMS Open Source queue.

**What to look for:**
- Top `error`/`state` combination by `total` — this drives the investigation path
- `AppTypeName` = PG or MySQL → transfer to RDBMS Open Source queue
- `lookup_state` = `DATABASE_ALIAS` or `LOGICAL_MASTER_ALIAS` → AliasDB pattern (prioritize Step 7)
- Empty `fabric_instance_uri_type` → GW never reached backend

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
let _NodeName = '{NodeName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where NodeName =~ _NodeName
| where event == "process_login_finish"
| where is_success == false and is_user_error == false
| extend server_and_dbs = strcat("[", logical_server_name, ", ", database_name, "]")
| extend fabric_instance_uri_type = extract("fabric:/Worker.(.*)/(.*)/", 2, fabric_instance_uri, typeof(string))
| summarize
    total = count(),
    distinct_dbs = dcount(server_and_dbs),
    makelist(server_and_dbs)
    by AppTypeName, error, state, lookup_error_code, lookup_state, fabric_instance_uri_type
| order by total desc
```

**Expected output:**
- **AppTypeName**: Application type (Gateway, PG, MySQL)
- **error/state**: Error code and state — the primary classification axis
- **lookup_state**: Sub-classification for 40613/4 errors
- **total**: Error count per category
- **distinct_dbs**: Number of unique server/database pairs affected

---

### GNLSR310 - Server-Level Breakdown with Target Rings

**Purpose:** Identify if errors concentrate on specific logical servers, TR rings, or DB nodes. Helps differentiate customer-specific vs infrastructure issues.

**What to look for:**
- Errors concentrated on one `TargetTRRing` → backend issue on that ring
- Errors concentrated on one `logical_server_name` → customer-specific or DB-node issue
- Errors spread across many servers → infrastructure-level issue
- 🚩 Empty `instance_name` / `TargetTRRing` → GW never reached backend (AliasDB resolution failed)

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
let _NodeName = '{NodeName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where NodeName =~ _NodeName
| where event == "process_login_finish"
| where is_success == false and is_user_error == false and error > 0
| extend TargetTRRing = substring(instance_name, indexof(instance_name, ".") + 1)
| extend sqlInstance = tolower(split(instance_name, '.')[0])
| summarize
    error_count = count()
    by err = strcat("error:", error, " state:", state),
       sqlInstance,
       logical_server_name,
       database_name,
       fabric_node_name,
       TargetTRRing
| order by error_count desc
| take 20
```

**Expected output:**
- **err**: Error code and state combined
- **sqlInstance/TargetTRRing**: Backend target — confirms where the GW was trying to route
- **error_count**: Volume per target — high concentration points to specific backend issues

---

### GNLSR320 - Most Impacted Logical Servers and Databases

**Purpose:** Extract the top impacted `logical_server_name` + `database_name` pairs from system errors on the affected node. Use these as parameters for error-specific skills that require server/database context.

**What to look for:**
- Row 1 = most impacted server/database pair → use as parameters for Step 5
- If results are empty (e.g., AliasDB failures where `logical_server_name` is empty), use `get-db-info` skill

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
let _NodeName = '{NodeName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where NodeName =~ _NodeName
| where event == "process_login_finish"
| where is_success == false and is_user_error == false and error > 0
| where isnotempty(logical_server_name) and isnotempty(database_name)
| summarize
    SystemErrors = count(),
    DistinctErrors = dcount(strcat(error, "_", state))
    by logical_server_name, database_name
| order by SystemErrors desc
| take 5
```

**Expected output:**
- **logical_server_name**: Logical server name for error-specific skill delegation
- **database_name**: Database name for error-specific skill delegation
- **SystemErrors**: Total system errors for this server/database pair
- **DistinctErrors**: Number of distinct error/state combinations

---

## Step 6: Check SNAT Port Exhaustion

### GNLSR400 - SNAT Port Exhaustion Check

**Purpose:** Check for `SnatPortExhaustion` / `HighSnatPortUsage` events on the cluster. Only execute if Error 40613 State 22 (`DueToProxyConnextThrottle`) was found in Step 4.

**What to look for:**
- Non-zero counts of `SnatPortExhaustion` or `HighSnatPortUsage` events
- Correlate timing with the login failure window from GNLSR100
- 🚩 Requires access to `azslb.kusto.windows.net` — see SKILL.md for permission note

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonFabricClusters
| where name =~ _ClusterName
| distinct ipv4_address
| join kind=inner (
    cluster('azslb.kusto.windows.net').database('azslbmds').SlbHealthEvent
    | where env_time between (StartTime..EndTime)
    | where HealthEventType in ("SnatPortExhaustion", "HighSnatPortUsage")
    | where env_name == "##Microsoft.Networking.Slb.Core.Monitoring.SlbHealthEvent"
) on $left.ipv4_address == $right.VipOrIlbPA
| summarize count() by HealthEventType, bin(env_time, 5m)
| render timechart
```

**Expected output:**
- Time-series chart of SNAT events
- **HealthEventType**: `SnatPortExhaustion` (critical) or `HighSnatPortUsage` (warning)
- **count_**: Event count per 5-minute bin

---

## Step 7: Redirector & AliasDB Health

### GNLSR600 - Alias Cache ODBC Failures Per Node

**Purpose:** Detect alias database connectivity failures on the affected node. High ODBC failure rates indicate the GW node cannot reach AliasDB.

**What to look for:**
- Non-zero `FailureCount` on the affected node
- Compare failure rates across nodes — if only one node has failures → node-local issue
- 🚩 High failure count (> 10 per 5-min) indicates sustained AliasDB connectivity problem

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRedirector
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "sql_alias_odbc_failure"
| summarize
    FailureCount = count()
    by bin(originalEventTimestamp, 5m), NodeName
| order by originalEventTimestamp asc
```

**Expected output:**
- **originalEventTimestamp**: Time bin
- **NodeName**: Which node experienced the failure
- **FailureCount**: Number of ODBC failures in that time bin

---

### GNLSR610 - Alias Cache Refresh Activity

**Purpose:** Verify alias cache is being refreshed regularly. Gaps in refresh activity indicate cache issues.

**What to look for:**
- Regular `sql_alias_cache_refresh` and `sql_alias_cache_update` events across all nodes
- Gaps on the affected node → cache backoff or connectivity issue
- Compare refresh cadence between affected and healthy nodes

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRedirector
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event in ("sql_alias_cache_refresh", "sql_alias_cache_update")
| summarize
    Count = count()
    by bin(originalEventTimestamp, 15m), event, NodeName
| order by originalEventTimestamp asc
```

**Expected output:**
- **event**: Type of cache activity (`sql_alias_cache_refresh` or `sql_alias_cache_update`)
- **Count**: Number of events per 15-minute bin — look for consistency across nodes

---

### GNLSR620 - Fabric Resolution Failures

**Purpose:** Detect failed service partition resolutions (non-zero result). These indicate Service Fabric issues preventing the GW from resolving backend endpoints.

**What to look for:**
- Non-zero `FailureCount` — any failures indicate resolution problems
- High `DistinctPartitions` → broad resolution failure affecting many partitions
- 🚩 If failures correlate with login failures on multiple nodes → backend TR ring is unreachable

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRedirector
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "fabric_end_resolve"
| where result != 0
| summarize
    FailureCount = count(),
    DistinctPartitions = dcount(partition_id)
    by bin(originalEventTimestamp, 5m), result, NodeName
| order by originalEventTimestamp asc
```

**Expected output:**
- **result**: Non-zero result code from fabric resolution
- **FailureCount**: Number of resolution failures per time bin
- **DistinctPartitions**: Number of unique partitions that failed to resolve

---

### GNLSR630 - Lookup Retries (Resolution Instability)

**Purpose:** Detect resolution instability via retry storms. High retry counts indicate the GW is repeatedly failing and retrying endpoint resolution.

**What to look for:**
- High `Count` of retry events → resolution instability
- `xdb_lookup_retry_begin` without matching `xdb_lookup_retry_end` → retries not completing
- Compare across nodes — if only one node has retries → node-local issue

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRedirector
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event in ("xdb_lookup_retry_begin", "xdb_lookup_retry_end", "xdb_lookup_retry_cleanup_task_end")
| summarize Count = count()
    by bin(originalEventTimestamp, 5m), event, NodeName
| order by originalEventTimestamp asc
```

**Expected output:**
- **event**: Type of retry event
- **Count**: Retry count per 5-minute bin — high counts indicate instability

---

### GNLSR640 - AliasDB SF Application Health State

**Purpose:** Check AliasDB SF application health during incident window. If `HealthState` != "Ok", AliasDB infrastructure is degraded on this cluster.

**What to look for:**
- Health report events mentioning "AliasDB" or "SqlAlias"
- `HealthState` in the event text — look for "Warning", "Error", or "Unknown"
- 🚩 If AliasDB is unhealthy → check replicas from SFE, check secret/credential rotation

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonSFEvents
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "HM.ApplicationHealthReportCreated" or event == "HM.ApplicationNewHealthReport"
| where text has "AliasDB" or text has "SqlAlias"
| project originalEventTimestamp, NodeName, event, text
| order by originalEventTimestamp asc
```

**Expected output:**
- **originalEventTimestamp**: When the health report was created
- **text**: Health report content — parse for HealthState value

---

## Step 8: GW Process Health

### GNLSR700 - GW Process Restarts (Process ID Changes)

**Purpose:** Detect GW process restarts via distinct process IDs. Multiple process IDs indicate process instability.

**What to look for:**
- `total_processes` > 1 → process restarted during the incident window
- 🚩 `total_processes` > 3 → crash loop pattern
- Compare across nodes — if only the affected node shows restarts → node-local issue

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where package =~ 'xdbgateway'
| summarize total_processes = dcount(process_id, 4) by NodeName
| where total_processes > 1
```

**Expected output:**
- **NodeName**: Node with process restarts
- **total_processes**: Number of distinct process IDs — 1 is normal, > 1 indicates restarts

---

### GNLSR710 - GW Process Restart Events (XE Session Start)

**Purpose:** Confirm GW process restart by detecting XE session initialization. Each process start initializes the `xdbgateway_logins` XE session.

**What to look for:**
- Multiple "Started XE session xdbgateway_logins" entries on the same node → multiple restarts
- Timestamps show the restart cadence

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRedirector
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where AppTypeName == "Gateway"
| where text startswith "Started XE session xdbgateway_logins"
| project originalEventTimestamp, NodeName, process_id, text
```

**Expected output:**
- **originalEventTimestamp**: When each process started
- **process_id**: Process ID — each unique ID is a separate GW process instance

---

### GNLSR720 - GW Process Restart Gap Duration

**Purpose:** Measure the gap between old process ending and new process starting. Long gaps indicate extended unavailability.

**What to look for:**
- `GapInSecond` > 60 → 🚩 extended unavailability window
- Short gaps (< 10s) → normal restart behavior
- Long gaps may correlate with dump generation or node issues

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRedirector
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where AppTypeName =~ "Gateway"
| summarize ST = min(originalEventTimestamp), ET = max(originalEventTimestamp) by NodeName, process_id
| order by NodeName, ST asc
| extend GapInSecond = iff(next(NodeName) == NodeName, datetime_diff('second', next(ST), ET), long(0))
| extend StartTime = ET, EndTime = next(ST), Restart = strcat(process_id, " -> ", next(process_id))
| where GapInSecond != 0
| project NodeName, Restart, StartTime, EndTime, GapInSecond
| sort by StartTime asc
```

**Expected output:**
- **Restart**: Previous process_id → new process_id
- **GapInSecond**: Seconds between old process end and new process start

---

### GNLSR730 - Node-Specific Resource Usage

**Purpose:** Check memory, threads, cache usage on the affected node. High resource usage may indicate the root cause of process instability.

**What to look for:**
- `MaxMemoryUsagePages` trending up → memory leak
- `MaxThreadCount` unusually high → thread exhaustion
- `AvgAliasCacheEntries` dropping to 0 → cache cleared (restart or corruption)

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
let _NodeName = '{NodeName}';
MonGatewayResourceStats
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where NodeName =~ _NodeName
| summarize
    AvgMemoryUsagePages = avg(memory_usage_pages),
    MaxMemoryUsagePages = max(memory_usage_pages),
    AvgThreadCount = avg(thread_count),
    MaxThreadCount = max(thread_count),
    AvgAliasCacheEntries = avg(alias_cache_entries),
    MaxAliasCacheEntries = max(alias_cache_entries),
    AvgUriCacheEntries = avg(uri_cache_entries),
    MaxUriCacheEntries = max(uri_cache_entries)
    by bin(TIMESTAMP, 5m)
| order by TIMESTAMP asc
```

**Expected output:**
- Resource metrics per 5-minute bin
- Compare values before, during, and after the incident to identify anomalies

---

## Step 9: Check Deployment / Maintenance

### GNLSR800 - GW Deployment Traces

**Purpose:** Check if a GW deployment was in progress during the incident. Deployments can cause transient login failures.

**What to look for:**
- Any deployment events during the incident window → correlates with the failure
- `upgrade_state` values show deployment progress
- If deployment correlates → issue likely self-mitigates after deployment finishes

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonRolloutProgress
| where originalEventTimestamp between (StartTime..EndTime)
| where cluster_name =~ _ClusterName
| where application_type_name == "Gateway" or application_name == "fabric:/Gateway"
| where event in ("start_upgrade_app_type", "app_instance_upgrade_progress", "start_upgrade_app_instance", "start_pause_upgrade_app_type", "start_resume_upgrade_app_type", "set_start_post_bake_blast")
| project originalEventTimestamp, event, cluster_name, target_version, rollout_key, upgrade_state, upgrade_progress, bake_start_time, bake_duration
| extend RolloutKeyCab = extract("^([0-9]*)_(.*)", 1, rollout_key)
| project-away rollout_key
| order by originalEventTimestamp asc
```

**Expected output:**
- **event**: Type of deployment event
- **target_version**: Version being deployed
- **upgrade_state/upgrade_progress**: Current deployment state

---

### GNLSR810 - Repair Tasks on Nodes

**Purpose:** Check for repair tasks that may indicate node issues. Repair tasks can cause temporary node unavailability.

**What to look for:**
- Repair tasks targeting the affected node during or near the incident window
- Task state progression (Created → Preparing → Executing → Completed)
- 🚩 Repair tasks on multiple nodes simultaneously → potential infrastructure maintenance

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
WinFabLogs
| where ETWTimestamp between (StartTime..EndTime + 3d)
| where ClusterName =~ _ClusterName
| where Text contains "RepairTask[scope=ClusterRepairScopeIdentifier, taskId="
| parse kind=regex Text with * "taskId=" TaskId ", version" * "state=" State ", flags" * "target=NodeRepairTargetDescription\\[nodeList = \\(" Node "\\)\\], executor" *
| project ClusterName, ETWTimestamp, TaskId, State, Node
| evaluate pivot(State, min(ETWTimestamp))
```

**Expected output:**
- **TaskId**: Repair task identifier
- **Node**: Target node for the repair
- Pivot columns showing when each state was reached

---

## Step 10: Impact Assessment

### GNLSR900 - Impacted Servers and Subscriptions

**Purpose:** Count distinct impacted servers and subscriptions for severity assessment and reporting.

**What to look for:**
- `DistinctServers` > 100 → 🚩 significant impact
- `DistinctSubscriptions` > 50 → 🚩 broad customer impact
- Use these numbers for outage declaration and severity assessment

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterName = '{ClusterName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where ClusterName =~ _ClusterName
| where event == "process_login_finish"
| where is_success == false and is_user_error == false
| summarize
    DistinctServers = dcount(logical_server_name),
    DistinctDatabases = dcount(strcat(logical_server_name, "/", database_name)),
    DistinctSubscriptions = dcount(subscription_id),
    TotalSystemErrors = count()
```

**Expected output:**
- **DistinctServers**: Number of unique logical servers with system errors
- **DistinctDatabases**: Number of unique databases with system errors
- **DistinctSubscriptions**: Number of unique subscriptions impacted
- **TotalSystemErrors**: Total system error count
