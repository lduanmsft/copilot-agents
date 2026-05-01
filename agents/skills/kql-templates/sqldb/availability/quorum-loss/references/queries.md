# Kusto Queries for Quorum Loss Debugging

!!!AI Generated. To be verified!!!

## Query Parameter Placeholders

Replace these placeholders with actual values when running queries:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp in UTC

**Resource identifiers:**
- `{LogicalServerName}`: Logical server name (e.g., `myserver.database.windows.net`)
- `{LogicalDatabaseName}`: Logical database name
- `{physical_database_id}`: Physical database ID (GUID)
- `{fabric_partition_id}`: Service Fabric partition ID (GUID)
- `{logical_database_id}`: Logical database ID (GUID)

**Service Fabric identifiers:**
- `{ClusterName}`: Service Fabric cluster name (from `tenant_ring_name`)
- `{AppName}`: Application name (from `sql_instance_name`)
- `{ServiceName}`: Fabric service name (format: `fabric://app-guid/service-guid`)
- `{NodeName}`: Fabric node name
- `{PrimaryNodeName}`: Primary replica node name

---

## Step 1: Identify When Quorum Loss Occurred

### QL100 - FTQuorumLoss Events

**Purpose:** Identify when the partition entered quorum loss by checking for FTQuorumLoss and FTQuorumRestored events in WinFabLogs.

**What to look for:**
- FTQuorumLoss events indicate quorum was lost
- FTQuorumRestored indicates quorum has been restored
- Time range between these events shows duration of quorum loss

```kql
WinFabLogs 
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime})) 
| where Id =~ "{fabric_partition_id}" or Text contains "{fabric_partition_id}"
| where EventType in ('FTQuorumLoss', 'FTQuorumRestored') 
| project ETWTimestamp, NodeName, TaskName, EventType, Text 
| order by ETWTimestamp asc
| take 5555
```

**Expected output:**
- `ETWTimestamp`: When the event occurred
- `EventType`: FTQuorumLoss or FTQuorumRestored
- `Text`: Additional details about the quorum event

---

### QL110 - Quorum Loss Time Ranges

**Purpose:** Identify continuous time ranges where quorum loss occurred and calculate total duration.

**What to look for:**
- `RangeStart` and `RangeEnd` show each quorum loss period
- `DurationMinutes` shows how long quorum was lost
- Multiple ranges may indicate recurring quorum loss

```kql
let START_TIME = datetime({StartTime});
let END_TIME = datetime({EndTime});
let PARTITION_ID = "{fabric_partition_id}";
WinFabLogs
| where TIMESTAMP >= START_TIME and TIMESTAMP <= END_TIME
| where EventType =~ 'FTQuorumLoss'
| where Text has PARTITION_ID
| summarize by TimeBucket = bin(PreciseTimeStamp, 1m)
| order by TimeBucket asc
| serialize
| extend PrevBucket = prev(TimeBucket)
| extend IsNewRange = isnull(PrevBucket) or (TimeBucket - PrevBucket) > 1m
| extend RangeId = row_cumsum(toint(IsNewRange))
| summarize RangeStart = min(TimeBucket), RangeEnd = max(TimeBucket) by RangeId
| extend RangeEnd = RangeEnd + 1m
| extend DurationMinutes = datetime_diff('minute', RangeEnd, RangeStart)
| project RangeStart, RangeEnd, DurationMinutes
| order by RangeStart asc
```

**Expected output:**
- Time ranges with continuous quorum loss and their durations

---

## Step 2: Check Partition and Service State

### QL200 - Partition Service Lifecycle

**Purpose:** Check if the partition is stuck in creation or has lifecycle issues. If you don't see logs in replica tables but see activity here, the partition may be stuck in creation.

**What to look for:**
- Partition creation events
- Service lifecycle state changes
- Stuck or incomplete partition creation (symptom: no replica logs but service exists)

**Note:** A partition stuck in creation is NOT considered leaked.

```kql
// Service must follow format: fabric://<app-guid>/<service-guid>
BindableFabricServiceLifeCyle
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where Service == "{ServiceName}"
| project-reorder TIMESTAMP, Service, LifecycleState, Details
| order by TIMESTAMP asc
```

**Expected output:**
- Service creation/deletion events
- Current lifecycle state
- Any anomalies in service initialization

---

### QL210 - WinFab Event Timeline

**Purpose:** Get an overview of important WinFab events for the partition. Shows if key events occurred within the time window.

**What to look for:**
- `EventCount = 0` means the event didn't occur
- Look for FTUpdate, ReconfigurationSlow, UnplacedReplica events
- Correlate event timestamps for timeline analysis

```kql
let WinFabEvent=datatable(EventType:string)
[
    "FTUpdate",
    "UpdateFailoverUnit",
    "ReconfigurationSlow",
    'UnplacedReplica',
    'FTQuorumLoss',
    'FTQuorumRestored',
    'FTDataLoss'
];
WinFabEvent
| join kind=leftouter 
(WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where Id =~ "{fabric_partition_id}" 
) on EventType
| summarize EventCount=countif(isempty(ETWTimestamp)==false), Min_ETWTimestamp=min(ETWTimestamp), Max_ETWTimestamp=max(ETWTimestamp) by EventType
| order by Min_ETWTimestamp asc
```

**Expected output:**
- Summary of each event type with count and time range
- Quick identification of which events occurred

---

## Step 3: Analyze Replica Health and Status

### QL300 - Replica Health from MonDmDbHadrReplicaStates

**Purpose:** Track primary replica transitions and database state during quorum loss.

**What to look for:**
- Gaps in data may indicate database not recovered
- `database_state_desc = RECOVERING` indicates recovery in progress
- `synchronization_state_desc = REVERTING` indicates log reverting

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~'{LogicalServerName}' and logical_database_name =~'{LogicalDatabaseName}'
| where internal_state_desc in ('GLOBAL_PRIMARY', 'PRIMARY', 'FORWARDER')
| where is_local == 1
| summarize dcount(logical_database_name) by bin(PreciseTimeStamp, 5min), ClusterName, NodeName, internal_state_desc
| order by PreciseTimeStamp asc
```

**Expected output:**
- Timeline of primary nodes
- Any gaps indicate database unavailability periods

---

### QL310 - SQL Process Exits

**Purpose:** Check if SQL processes exited during the incident, which could explain replica failures.

**What to look for:**
- `ExitCode` indicates why the process exited
- `UnexpectedTermination=True` indicates crash
- Correlate with quorum loss timing

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where EventType == 'ProcessExitedOperational' and Text contains 'sqlservr.exe' and Text contains '{AppName}'
| project ETWTimestamp, ClusterName, ProcessId, ThreadId, TaskName, EventType, Text
| order by ETWTimestamp asc
| take 5555
```

**Expected output:**
- SQL process exit events with exit codes
- Timing relative to quorum loss

---

### QL320 - Database Recovery State

**Purpose:** Check if the database is stuck in RECOVERING state, which indicates replica issues.

**What to look for:**
- `database_state_desc = RECOVERING` indicates recovery in progress
- `synchronization_state_desc = REVERTING` indicates log reverting
- Extended time in these states is 🚩 problematic

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~'{LogicalServerName}' and logical_database_name =~'{LogicalDatabaseName}'
| where database_state_desc == 'RECOVERING'
| project PreciseTimeStamp, NodeName, synchronization_state_desc, database_state_desc
| take 5555
```

**Expected output:**
- Periods when database was in recovery state
- Correlation with quorum loss timing

---

### QL330 - Replica Build State Change Stuck

**Purpose:** Check if replicas are stuck during the build process. Error 41614 state 3 indicates a transient fabric error during replica rebuild, which can block quorum restoration.

**What to look for:**
- Repeated state changes without progress (e.g., stuck in same old/new state)
- `trigger_desc` values indicating what's blocking the build
- 🚩 Prolonged time between state transitions indicates stuck replica build

```kql
MonFabricDebug
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~'{AppName}'
| where event in ('hadr_fabric_build_replica_operation_state_change')
| where physical_database_id =~'{physical_database_id}'
| where NodeName =~'{PrimaryNodeName}'
| project originalEventTimestamp, event, old_state_desc, new_state_desc, is_primary, NodeName, trigger_desc, remote_endpoint_url
```

**Expected output:**
- `old_state_desc` / `new_state_desc`: Track state machine transitions
- `trigger_desc`: What triggered the state change
- `is_primary`: Whether this is on the primary replica

---

### QL340 - Database Recovery Trace

**Purpose:** View the full database recovery timeline from start to completion. Shows recovery phases, estimated time remaining, and completion details. More detailed than QL320 which only checks state.

**What to look for:**
- `Starting database recovery` - when recovery began
- `Recovery of database ... is N% complete` - progress messages with estimated time
- `Recovery completed for database ... in N second(s)` - completion with analysis/redo/undo breakdown
- 🚩 Long gaps between progress messages or no completion message
- **Note**: `database_name` in MonRecoveryTrace can contain either the physical DB ID or the logical DB name, so we filter on both

```kql
MonRecoveryTrace
| where originalEventTimestamp between (datetime({StartTime})-1h..datetime({EndTime}))
| where AppName =~ '{AppName}' and (database_name =~ '{physical_database_id}' or database_name =~ '{LogicalDatabaseName}')
| where event == "database_recovery_trace" and trace_message has "Recovery"
| project originalEventTimestamp, process_id, NodeName, database_name, database_id, trace_message
| order by originalEventTimestamp asc, process_id
| limit 5555
```

**Expected output:**
- Recovery timeline with phase progression
- Estimated completion times
- Final recovery duration breakdown (analysis, redo, undo)

---

### QL350 - Long Recovery Detection

**Purpose:** Quick check if database recovery took longer than 10 minutes, which is a 🚩 red flag indicating potential issues.

**What to look for:**
- `total_elapsed_time_sec > 600` (10 minutes) = 🚩 problematic
- Multiple recovery events may indicate repeated failures
- Correlate with quorum loss timeline
- Note: `physical_db_id` column is empty in MonRecoveryTrace; use `database_name` which contains either the physical DB GUID or the logical database name

```kql
MonRecoveryTrace
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}'
| where database_name =~ '{physical_database_id}' or database_name =~ '{LogicalDatabaseName}'
| where event in ('database_recovery_complete')
| project originalEventTimestamp, event, ClusterName, NodeName, process_id, total_elapsed_time_sec
```

**Expected output:**
- `total_elapsed_time_sec`: Total recovery time in seconds
- 🚩 Any value > 600 seconds warrants investigation

---

## Step 4: Infrastructure Investigation

### QL400 - Infrastructure Health Events

**Purpose:** Check for infrastructure-level issues (bugchecks, reboots, failures) affecting the nodes hosting replicas.

**What to look for:**
- Node failures or bugchecks during quorum loss period
- Correlation between infrastructure events and replica failures
- Pattern of failures across multiple nodes

```kql
MonSQLInfraHealthEvents
| where FaultTime between (datetime({StartTime})-12h..datetime({EndTime})+24h)
| where ClusterName =~ '{ClusterName}'
| where NodeName in ('{PrimaryNodeName}')
| project-away IngestionTime
| distinct *
```

**Expected output:**
- Infrastructure fault events on affected nodes
- Root cause of node-level failures

---

### QL410 - SQL Process Start Events

**Purpose:** Track SQL process lifecycle - when processes started on each node.

**What to look for:**
- Process start events following quorum loss
- Delays in process startup
- Failed startup attempts

```kql
MonNodeTraceETW
| where PreciseTimeStamp between (datetime({StartTime})-1h..datetime({EndTime})+1h)
| where ClusterName =~'{ClusterName}'
| where Message has '{AppName}'
| where Message contains 'ServiceManifest Name' and Message contains 'SQL' and Message contains '[InitFabric] Started InitFabric'
| where isnotnull(Pid) and Pid > 0
| summarize arg_max(PreciseTimeStamp, *) by NodeName, Pid
| project PreciseTimeStamp, EventType='SQLProcessStarted', NodeName, Pid, Message
| order by PreciseTimeStamp asc 
```

**Expected output:**
- SQL process start times on each node
- Process IDs for correlation

---

## Step 5: Service Fabric Reconfiguration Events

### QL500 - Reconfiguration Status

**Purpose:** Check if the partition is stuck in reconfiguration during quorum loss recovery.

**What to look for:**
- ReconfigurationStarted without matching ReconfigurationCompleted = stuck
- ReconfigurationSlow events indicate prolonged reconfiguration
- Multiple slow events with same start time = 🚩 problematic

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime})+1h)
| where Text contains "{fabric_partition_id}" or Id =~ "{fabric_partition_id}"
| where TaskName =~'FM'
| where EventType in ('ReconfigurationStartedOperational', 'ReconfigurationStarted', 'ReconfigurationCompleted') 
| extend activity_id = extract('ActivityId: ([a-zA-Z0-9-]+)', 1, Text) 
| extend OldPrimaryNodeName = extract(@"OldPrimaryNodeName:\s*(\S+)", 1, Text), NewPrimaryNodeName = extract(@"NewPrimaryNodeName:\s*(\S+)", 1, Text)
| project ETWTimestamp, TaskName, EventType, OldPrimaryNodeName, NewPrimaryNodeName, Id, activity_id, Text
| order by ETWTimestamp asc
```

**Expected output:**
- Reconfiguration start and completion events
- Old and new primary node names
- Gaps between start and complete indicate long reconfigurations

---

### QL510 - Reconfiguration Slow Events

**Purpose:** Identify prolonged reconfigurations that may be blocking quorum restoration.

**What to look for:**
- Multiple ReconfigurationSlow events with same start time
- Pending replica transitions (S/N = Secondary to None)
- Phase3_Deactivate stuck with S/N transition is 🚩 problematic

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})-2h..datetime({EndTime})+4h)
| where ClusterName =~'{ClusterName}'
| where EventType in ('ReconfigurationSlow')
| where Id =~ "{fabric_partition_id}" or Text contains "{fabric_partition_id}"
| extend ReconfigPhaseStartTime= todatetime(extract(@"Reconfiguration phase start time:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", 1, Text))
| summarize min(ETWTimestamp), max(ETWTimestamp), count(), any(Text) by ReconfigPhaseStartTime
```

**Expected output:**
- Reconfiguration phases that are taking too long
- Count of slow events per phase (high count = 🚩)

---

### QL520 - Reconfiguration Duration Summary

**Purpose:** Calculate total time for failover reconfigurations.

**What to look for:**
- `TotalDuration` indicates overall reconfiguration time
- `Phase2Duration` (Catchup) - variable based on log size
- `Phase3Duration` (Deactivate) - should be quick; long duration is 🚩

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where Id contains "{fabric_partition_id}" or Text contains "{fabric_partition_id}"
| extend ReconfigType = extract("ReconfigurationType = ([a-zA-Z]+)", 1, Text)
| where ReconfigType == "Failover"
| extend CatchupDuration = extract("Phase2Duration: ([0-9.]+)", 1, Text), DeactivateDuration = extract("Phase3Duration: ([0-9.]+)", 1, Text), TotalDuration = extract("TotalDuration: ([0-9.]+)", 1, Text)
| project ETWTimestamp, ClusterName, NodeName, EventType, TaskName, ReconfigType, CatchupDuration, DeactivateDuration, TotalDuration
```

**Expected output:**
- Reconfiguration phase durations
- Identification of slow phases

---

## Step 6: Check for Unplaced Replicas and Data Loss

### QL600 - Unplaced Replica with Data Loss

**Purpose:** Check if replicas cannot be placed and if data loss occurred.

**What to look for:**
- UnplacedReplica events indicate replicas cannot find suitable nodes
- FTDataLoss joined with UnplacedReplica = 🚩 critical situation

```kql
WinFabLogs
| where TIMESTAMP between (datetime({StartTime})-1h..datetime({EndTime})+1h)
| where EventType =~ 'UnplacedReplica' and Text contains '{AppName}'
| project TIMESTAMP, Id, Text
| top 1 by TIMESTAMP
| join kind = inner(
    WinFabLogs
    | where EventType =~ 'FTDataLoss'
) on $left.Id == $right.Id
| take 1
| project Text, TIMESTAMP, NodeName, ClusterName
```

**Expected output:**
- Indicates data loss scenario if results returned
- 🚩 Escalate immediately if data loss confirmed

---

### QL610 - Node Deactivation Events

**Purpose:** Check if nodes are being deactivated, which could prevent replica placement.

**What to look for:**
- DeactivateNode events on nodes hosting replicas
- SafetyCheck values indicating waiting for replicas
- Phase values showing deactivation progress

```kql
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ClusterName}'
| where Text contains '{fabric_partition_id}' or Id =~ '{fabric_partition_id}'
| where EventType == 'DeactivateNode' and TaskName == 'FM'
| extend DBNodeName = extract(@"NodeName=\s*([\d\w_]+)", 1, Text), Phase = extract(@"Phase=\s*(\S+)", 1, Text), SafetyCheck = extract(@"SafetyCheck=\s*(\S+),", 1, Text)
| project ETWTimestamp, TaskName, EventType, DBNodeName, Phase, SafetyCheck, Text
| take 5555 
```

**Expected output:**
- Node deactivation events affecting the partition
- Safety checks that may be blocking operations

---

## Step 7: Impact Assessment

### QL700 - LoginOutages Impact

**Purpose:** Assess customer impact through login outage telemetry.

**What to look for:**
- `OutageType` and `OutageReasonLevel*` for root cause categorization
- `durationSeconds` for impact duration
- Multiple outages may indicate recurring issues

```kql
LoginOutages
| where outageStartTime between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ "{LogicalServerName}" and database_name =~ "{LogicalDatabaseName}"
| project outageStartTime, outageEndTime, durationSeconds, OutageType, OutageReasonLevel1, OutageReasonLevel2, OutageReasonLevel3, OwningTeam
| order by outageStartTime asc
```

**Expected output:**
- Login outage periods correlated with quorum loss
- Outage classification for RCA

---

## Step 8: Fabric API Investigation

### QL800 - FabricApi Event Timeline

**Purpose:** Get a comprehensive overview of all important Fabric API events for the partition. Shows role changes, build replica operations, quorum catchup, and write status changes.

**What to look for:**
- `EventCount = 0` means the event didn't occur
- Mismatched `begin`/`end` counts indicate stuck operations (e.g., `begin_change_role` count > `end_change_role` count)
- `result_desc` values for failed operations
- `current_write_status_desc = GRANTED` confirms failover completed from SQL perspective

```kql
let FabricApiEvent=datatable(event:string)
[
    'hadr_fabric_api_replicator_begin_change_role',
    'hadr_fabric_api_replicator_end_change_role',
    'hadr_fabric_api_partition_write_status',
    'hadr_fabric_api_replica_begin_change_role',
    'hadr_fabric_api_replica_end_change_role',
    'hadr_fabric_api_replicator_begin_build_replica',
    'hadr_fabric_api_replicator_end_build_replica',
    'hadr_fabric_api_replicator_begin_wait_for_quorum_catchup',
    'hadr_fabric_api_replicator_end_wait_for_quorum_catchup',
    'NotExistEvent'
];
FabricApiEvent
| join kind=leftouter 
(
MonFabricApi
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ '{AppName}'
| where physical_database_id =~ '{physical_database_id}'
) on event
| summarize EventCount=countif(isempty(originalEventTimestamp)==false), 
    NodesInvolved=tostring(makeset(NodeName)),
    Min_EventTimeStamp=min(originalEventTimestamp), Max_EventTimeStamp=max(originalEventTimestamp),
    Result_desc_set=tostring(makeset(result_desc)), New_role_desc_set=tostring(makeset(new_role_desc)), current_write_status_desc_set=tostring(makeset(current_write_status_desc)),
    role_other_desc=tostring(makeset(role_other_desc)), catch_up_mode_desc_set=tostring(makeset(catch_up_mode_desc))
    by event
| order by Min_EventTimeStamp asc
```

**Expected output:**
- Summary of each Fabric API event type with counts and time ranges
- Quick identification of mismatched begin/end pairs
- Role change and write status results

---

### QL810 - Write Status Granted

**Purpose:** Determine when write status was granted on the primary node, confirming that failover completed and the database became writable again from the SQL perspective.

**What to look for:**
- `current_write_status_desc = GRANTED` confirms writes are allowed
- `current_write_status_desc = NOT_PRIMARY` on a node means that node is no longer primary
- Gap between quorum restoration (QL100) and write status granted = failover completion delay

```kql
MonFabricApi
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ '{AppName}'
| where physical_database_id =~ '{physical_database_id}'
| where event =~ 'hadr_fabric_api_partition_write_status'
| project originalEventTimestamp, previous_write_status_desc, current_write_status_desc, NodeName, event, process_id, physical_database_id, fabric_replica_id
| order by originalEventTimestamp asc
```

**Expected output:**
- Write status transitions showing when primary became writable
- Node hosting the primary replica

---

### QL820 - Reconfiguration History

**Purpose:** Detailed view of reconfiguration history showing which node was primary, which were secondaries, and which were being built at each point in time. More detailed than QL500 which only shows start/complete events.

**What to look for:**
- Primary node changes during the incident
- InBuildSecondaries indicate new replicas being constructed
- Pattern of role changes and replica set composition

```kql
MonFabricApi
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where physical_database_id =~ '{physical_database_id}'
| where AppName =~ '{AppName}'
| where event in ("hadr_fabric_api_replicator_begin_change_role", "hadr_fabric_api_replicator_update_current_replica_set_configuration", "hadr_fabric_api_replicator_update_catchup_replica_set_configuration", "hadr_fabric_api_replicator_begin_build_replica")
| extend replica_other=extract(@'pipe\\(.+?)-', 1, replicator_address_other)
| extend replicas_current1=extract(@'^.*?pipe\\(.+?)-', 1, replica_infos_current)
| extend replicas_current2=extract(@'^.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_current)
| extend replicas_current3=extract(@'^.*?pipe\\.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_current)
| extend replicas_current = iff(replicas_current1 !="", strcat(replicas_current1, iff(replicas_current2 != "", strcat(", ", replicas_current2), ""), iff(replicas_current3 != "", strcat(", ", replicas_current3), "")), "")
| extend replicas_previous1=extract(@'^.*?pipe\\(.+?)-', 1, replica_infos_previous)
| extend replicas_previous2=extract(@'^.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_previous)
| extend replicas_previous3=extract(@'^.*?pipe\\.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_previous)
| extend replicas_previous = iff(replicas_previous1 !="", strcat(replicas_previous1, iff(replicas_previous2 != "", strcat(", ", replicas_previous2), ""), iff(replicas_previous3 != "", strcat(", ", replicas_previous3), "")), "")
| order by originalEventTimestamp desc
| extend AccurateTimestamp = tostring(originalEventTimestamp)
| extend Secondaries = iff(replica_other != "" , "Same as below" , replicas_current)
| extend InBuildSecondaries = replica_other
| extend Primary = iff((new_role_desc == "PRIMARY") , NodeName ,
                iff((Secondaries != "" or InBuildSecondaries != ""), NodeName, ""))
| where Primary != "" or Secondaries != "" or InBuildSecondaries != ""
| project AccurateTimestamp, event, Primary, Secondaries, InBuildSecondaries, physical_database_id
| order by AccurateTimestamp asc
```

**Expected output:**
- `Primary`: Node currently acting as primary
- `Secondaries`: Nodes with ready secondary replicas
- `InBuildSecondaries`: Nodes with replicas being built
- Timeline of replica set composition changes

---

## Query Execution Tips

1. **Start with QL100 and QL110** to confirm quorum loss and get the exact timeframe
2. **Use the time window** from QL100 to narrow down subsequent queries
3. **Check replica health (QL300-QL320)** before investigating infrastructure
4. **Look for patterns** across multiple components (compute, network, storage)
5. **Correlate timestamps** across different telemetry sources
6. **Check for ReconfigurationSlow (QL510)** if quorum loss persists

## Common Query Patterns

**Get partition details:**
- Service name: `fabric://<app-guid>/<service-guid>`
- Partition count: Typically 1 for SQL DB
- Replica set size: Usually 3-5 replicas

**Identifying quorum:**
- For 3 replicas: Quorum = 2 (majority)
- For 5 replicas: Quorum = 3 (majority)
- Quorum loss = When fewer than quorum replicas are available

---

## Next Steps After Running Queries

1. Document the timeline of the quorum loss event
2. Identify which replicas failed and when
3. Determine the root cause (compute/network/storage)
4. Check safety requirements before any recovery action:
   - At least one healthy replica exists
   - Healthy replica has highest last_hardened_lsn
   - Node of healthy replica is UP
   - LSN is valid (0 < LSN < 4294967295429496729565535)
5. Escalate to SQL DB Availability Expert queue if:
   - Error 3456 "write lost on primary" detected
   - No healthy replica available
   - LSN validation fails
   - Data loss is unavoidable

## Related Documentation

- [Service Fabric Health Reports](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-understand-and-troubleshoot-with-system-health-reports)
- [Terms and Concepts](knowledge.md)
- [Debug Principles](principles.md)
- [TRDB1002 - Quorum Loss TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-availability-and-geodr/sql-db-availability-tsgs-new/sql-db-availability-tsgs/ha/common-unavailability-root-causes/trdb0102-quorum-loss)