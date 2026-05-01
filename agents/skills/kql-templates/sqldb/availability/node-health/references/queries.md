# Kusto Queries for Node Health Diagnostics

!!!AI Generated. To be verified!!!

## Query Parameter Placeholders

Replace these placeholders with actual values when running queries:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp in UTC (e.g., `2026-01-01 03:00:00`)
- `{OutageStartTime}`: Outage start timestamp
- `{OutageEndTime}`: Outage end timestamp
- `{Duration}`: Time duration (e.g., `1h`, `101m`, `24h`)

**Resource identifiers:**
- `{LogicalServerName}`: Logical server name (e.g., `myserver.database.windows.net`)
- `{LogicalDatabaseName}`: Logical database name

**Infrastructure parameters:**
- `{ClusterName}`: Service Fabric cluster name (tenant_ring_name from get-db-info)
- `{DBNodeName}`: The database node name (e.g., `_DB_22`)
- `{AppName}`: Application name (sql_instance_name from get-db-info)

---

## Step 1: Locate Database Node

### NH100 - Locate Database Node

**Purpose:** Identifies which node(s) hosted the database during the incident window.

**What to look for:**
- ClusterName and NodeName for subsequent queries
- Multiple nodes may indicate failover occurred
- Use this to get the `{DBNodeName}` parameter for other queries

```kql
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ "process_login_finish"
| where AppTypeName =~ "Worker" or AppTypeName startswith "Worker.ISO"
| distinct ClusterName, NodeName
```

**Expected output:**
- `ClusterName`: Service Fabric cluster name
- `NodeName`: Database node name(s)

---

## Step 2: Check Service Fabric Node State

### NH200 - Check Service Fabric Node State Changes

**Purpose:** Retrieves Service Fabric node state changes, showing health_state and node_status transitions.

**What to look for:**
- Transitions from `health_state = Ok` to `Warning` or `Error`
- Node status changes (Up → Down, Up → Disabling)
- Small `node_up_time` indicates recent restart

```kql
MonClusterLoad
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where event contains "node_state_report"
| where ClusterName =~ '{ClusterName}'
| where node_name =~ '{DBNodeName}'
| project originalEventTimestamp, health_state, node_status
| sort by originalEventTimestamp asc
| extend PrevTime = prev(originalEventTimestamp)
| extend NextTime = next(originalEventTimestamp)
| extend PrevHealthstate = prev(health_state)
| extend PrevNodestate = prev(node_status)
| where 
    isnull(PrevTime) or 
    isnull(NextTime) or 
    (health_state != PrevHealthstate) or 
    (node_status != PrevNodestate)
| project originalEventTimestamp, health_state, node_status
| sort by originalEventTimestamp asc
```

**Expected output:**
- `originalEventTimestamp`: Timestamp of state change
- `health_state`: Node health state (Ok, Warning, Error)
- `node_status`: Node status (Up, Down, Disabling, Disabled)

---

### NH210 - Check Node Health Issues

**Purpose:** Query MonClusterLoad for nodes with health issues during the incident window.

**What to look for:**
- Any `health_state != 'Ok'` or `node_status != 'Up'`
- Small `node_up_time` indicates recent restart
- Correlate with incident timeline

```kql
MonClusterLoad 
| where TIMESTAMP between (datetime({StartTime})..{Duration})
| where event =~ "node_state_report" 
| where ClusterName =~ '{ClusterName}'
| where node_name =~ '{DBNodeName}'
| where health_state != 'Ok' or node_status != 'Up'
| project node_name, TIMESTAMP, health_state, node_status, node_up_time
| order by node_name, TIMESTAMP asc
```

**Expected output:**
- `node_name`: Node identifier
- `health_state`: Current health state
- `node_status`: Current node status
- `node_up_time`: Time since node came up (small = recent restart)

---

## Step 3: Check Infrastructure Health Events

### NH300 - Check Node Health Events

**Purpose:** Queries MonSQLInfraHealthEvents for infrastructure health issues on the node.

**What to look for:**
- Any infrastructure faults affecting the node
- Correlation with outage timing
- Fault types (network, storage, compute)

**Note:** Uses extended time window (12h before to 24h after outage) to capture related events.

```kql
cluster('sqlstage.kusto.windows.net').database('sqlazure1').MonSQLInfraHealthEvents
| where FaultTime between (datetime({OutageStartTime})-12h..datetime({OutageEndTime})+24h)
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| project-away IngestionTime, L2, L3
| distinct *
```

**Expected output:**
- Various health event fields depending on the fault type
- Fault descriptions and timing

---

## Step 4: Check for Bugcheck Events

### NH400 - Check for Bugcheck Events

**Purpose:** Searches system event logs for bugcheck/crash events and extracts bugcheck codes.

**What to look for:**
- Bugcheck codes (e.g., `0x0000007E`)
- Timestamp of crash relative to outage
- Multiple bugchecks may indicate hardware issue

```kql
MonSystemEventLogErrors
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{DBNodeName}'
| where EventDescription startswith "The computer has rebooted from a bugcheck"
| extend bugcheck = extract(@"0x[0-9a-fA-F]+", 0, EventDescription)
```

**Expected output:**
- `TIMESTAMP`: Event timestamp
- `ClusterName`: Cluster name
- `NodeName`: Node name
- `EventDescription`: Bugcheck description
- `bugcheck`: Extracted bugcheck code

---

## Step 5: Check Node Up/Down Events

### NH500 - Check Node Up/Down in WinFabLogs

**Purpose:** Searches WinFabLogs for NodeUp/NodeDown events to provide timeline of node state transitions.

**What to look for:**
- NodeUp/NodeDown events for the target node
- Sequence of events leading to outage
- Duration of down state

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ClusterName}'
| where Text contains "NodeUp " or Text contains "NodeDown " or Text contains "NodeUp:" or Text contains "NodeDown:"
| where Text contains '{DBNodeName}'
| project ETWTimestamp, NodeName, TaskName, EventType, Text
| sort by ETWTimestamp asc
```

**Expected output:**
- `ETWTimestamp`: Event timestamp
- `NodeName`: Node reporting the event
- `TaskName`: Service Fabric task name
- `EventType`: Event type
- `Text`: Event details

---

## Step 6: Check Node Repair Tasks

### NH600 - Check Node Repair Tasks

**Purpose:** Identifies repair tasks targeting the node, showing task state transitions and timing.

**What to look for:**
- Active repair tasks during incident
- Task state progression (Created → Preparing → Approved → Executing → Completed)
- Stuck tasks (same state for extended period)

**Note:** Uses extended window (+3 days) to capture long-running tasks.

```kql
WinFabLogs
| where ETWTimestamp between (datetime({OutageStartTime})..datetime({OutageEndTime})+3d)
| where ClusterName =~ '{ClusterName}'
| where Text contains "RepairTask[scope=ClusterRepairScopeIdentifier, taskId="
| parse kind = regex Text with * "taskId=" TaskId ", version" * "state=" State ", flags" * "target=NodeRepairTargetDescription\\[nodeList = \\(" Node "\\)\\], executor" *
| where Node =~ '{DBNodeName}'
| project ClusterName, ETWTimestamp, TaskId, State, Node
| evaluate pivot(State, min(ETWTimestamp))
```

**Expected output:**
- `ClusterName`: Cluster name
- `TaskId`: Repair task identifier
- `Node`: Target node name
- Various state columns (pivoted): Timestamps for each state transition

---

## Step 7: Check Restart Actions

### NH700 - Check RestartCodePackage Actions

**Purpose:** Identifies if the RepairPolicyEngine or watchdogs restarted the SQL code package on the node.

**What to look for:**
- `bot_action = 'RestartCodePackage'` targeting the node
- Reason for restart
- Correlation with incident timing

```kql
MonRingWatchdogs
| where originalEventTimestamp between (datetime({StartTime})..{Duration})
| where event contains 'action' and event != 'unsafe_bot_action' and event !contains 'throttled'
| where ClusterName =~ '{ClusterName}'
| where bot_action =~ 'RestartCodePackage'
| where application_name contains '{AppName}'
| project originalEventTimestamp, ClusterName, node_name, event, bot_action, reason, application_type_name, application_name, service_name, partition_id
```

**Expected output:**
- `originalEventTimestamp`: When restart occurred
- `node_name`: Node where restart happened
- `bot_action`: Action type (RestartCodePackage)
- `reason`: Why the restart was initiated

---

## Query Execution Tips

1. **Start with NH100** to identify which nodes hosted the database
2. **Use the NodeName** from NH100 as `{DBNodeName}` in subsequent queries
3. **Check state changes first** (NH200) before investigating root causes
4. **Use extended time windows** for infrastructure events and repair tasks
5. **Correlate timestamps** across different telemetry sources

## Common Patterns

**Node restart detected:**
- Small `node_up_time` in NH210
- NodeDown/NodeUp sequence in NH500
- Possibly bugcheck in NH400

**Degraded node (SF shows Ok but issues exist):**
- health_state = Ok in NH200
- But infrastructure events in NH300
- Or login failures in MonLogin not explained by state

**Planned maintenance:**
- Repair task present in NH600
- Task progressing through states
- Expected behavior

---

## Error Handling

**Common Issues:**

1. **No results from NH100:**
   - Verify logical server/database names
   - Check if the time window is correct
   - Database may not have had logins during window

2. **Cross-cluster queries (NH300):**
   - MonSQLInfraHealthEvents uses cross-cluster access to sqlstage
   - Ensure you have permissions to query the target cluster

3. **No repair tasks found:**
   - May be normal - not all issues trigger repair tasks
   - Check if the time window is sufficient

## Related Documentation

- [Terms and Concepts](knowledge.md)
- [Debug Principles](principles.md)
- [Investigate node health issues TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/sqlmh008-investigate-node-health-issues)
