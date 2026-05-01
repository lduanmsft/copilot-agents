# Seeding RCA Queries

!!!AI Generated. To be verified!!!

All queries run against the **specific production cluster** where the failure occurred.

## RCA-100: Database Context (MonAnalyticsDBSnapshot)

```kql
let st = datetime({Timestamp}) - 2h;
let et = datetime({Timestamp}) + 5h;
MonAnalyticsDBSnapshot 
| where TIMESTAMP between (st .. et)
| where ClusterName has "{ClusterName}"
| where logical_server_name =~ "{LogicalServerName}"  
| where logical_database_name =~ "{LogicalDatabaseName}"
| project TIMESTAMP, AppName, sql_instance_name, state, 
    service_level_objective, logical_database_id, physical_database_id, 
    fabric_partition_id, tenant_ring_name, logical_resource_pool_id, 
    logical_server_name, logical_database_name, ClusterName, 
    sql_database_id, zone_resilient
```

## RCA-110: Geo-Replication Detection (MonDmContinuousCopyStatus)

```kql
MonDmContinuousCopyStatus
| where PreciseTimeStamp between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName =~ "{AppName}"
| where link_type == "LAG_REPLICA_LINK_TYPE_CONTINUOUS_COPY"
| summarize arg_max(PreciseTimeStamp, *) by partner_server
| project PreciseTimeStamp, LogicalServerName, partner_server, partner_database,
    replication_state_desc, replication_lag_sec, is_target_role, link_type
```

## RCA-120: Replica State (MonDmDbHadrReplicaStates)

```kql
MonDmDbHadrReplicaStates
| where PreciseTimeStamp between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName =~ "{AppName}"
| where logical_database_name =~ "{LogicalDatabaseName}"
| where is_local == 1 or is_forwarder == 1
| project PreciseTimeStamp, NodeName, is_primary_replica, is_local,
    synchronization_state_desc, internal_state_desc, database_state_desc,
    is_forwarder, redo_queue_size, quorum_commit_time, is_seeding_in_progress,
    logical_database_name, last_hardened_lsn, truncation_lsn, end_of_log_lsn,
    database_id, replica_id
| order by PreciseTimeStamp asc
```

## RCA-198: Seeding Activity Check (MonDbSeedTraces)

Quick check whether any seeding activity occurred on this instance during the incident window.

```kql
MonDbSeedTraces
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName == "{AppName}"
| summarize
    TotalEvents = count(),
    FailEvents = countif(failure_code != 0),
    DistinctDBs = dcount(database_name),
    DistinctGuids = dcount(local_seeding_guid),
    FirstEvent = min(TIMESTAMP),
    LastEvent = max(TIMESTAMP)
```

If TotalEvents == 0, check MonDbSeedTraces retention:
```kql
MonDbSeedTraces | summarize min(TIMESTAMP)
```

## RCA-199: Multi-DB Failure Summary (MonDbSeedTraces)

Check all databases on the instance to determine if the problem is DB-specific or instance-wide.

```kql
MonDbSeedTraces
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName == "{AppName}"
| summarize
    FailCount = countif(failure_code != 0),
    AllCount = count(),
    FailCodes = make_set(failure_code),
    FirstFail = minif(TIMESTAMP, failure_code != 0),
    LastFail = maxif(TIMESTAMP, failure_code != 0)
    by database_name
| order by FailCount desc
```

## RCA-200: Seeding Failure History (MonDbSeedTraces)

```kql
MonDbSeedTraces
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName == "{AppName}"
| where database_name =~ "{PhysicalDatabaseId}"
| where failure_code != 0
| project TIMESTAMP, event, role_desc, internal_state_desc,
    failure_code, failure_message, local_seeding_guid, remote_seeding_guid,
    database_size_bytes, transferred_size_bytes,
    database_name, LogicalServerName, ClusterName
| order by TIMESTAMP asc
```

## RCA-210: Source ↔ Destination Correlation

```kql
let my_guids = 
    MonDbSeedTraces
    | where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
    | where AppName == "{AppName}"
    | where database_name =~ "{PhysicalDatabaseId}"
    | where failure_code != 0
    | distinct local_seeding_guid;
MonDbSeedTraces
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where remote_seeding_guid in (my_guids) or local_seeding_guid in (my_guids)
| where failure_code != 0
| project TIMESTAMP, event, role_desc, failure_code, failure_message,
    AppName, ClusterName, LogicalServerName,
    local_seeding_guid, remote_seeding_guid, internal_state_desc
| order by local_seeding_guid, TIMESTAMP asc
```

## RCA-215: Remote Side DB Context (MonAnalyticsDBSnapshot)

Run on the PARTNER cluster (resolved from RCA-110 partner_server).

```kql
MonAnalyticsDBSnapshot
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where logical_server_name =~ "{PartnerServerName}"
| where logical_database_name =~ "{LogicalDatabaseName}"
| project TIMESTAMP, AppName, sql_instance_name, tenant_ring_name, ClusterName,
    logical_server_name, logical_database_name, logical_database_id,
    physical_database_id, fabric_partition_id, service_level_objective
| take 1
```

## RCA-250: Check for UpdateSLO / Management Operations (MonManagementOperations)

```kql
MonManagementOperations
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where logical_server_name =~ "{LogicalServerName}"
| where logical_database_name =~ "{LogicalDatabaseName}"
| where operation in ("ALTER", "UPDATE", "SCALE", "SLO_CHANGE")
    or operation_friendly_name has_any ("UpdateSlo", "ScaleDatabase", "UpdateDatabase", "AlterDatabase")
| project TIMESTAMP, operation, operation_friendly_name, state, 
    start_time, end_time, error_code, error_message, error_severity,
    old_slo = old_service_level_objective, new_slo = new_service_level_objective,
    logical_server_name, logical_database_name
| order by TIMESTAMP asc
```

## RCA-251: Check MonManagement for SLO Change Evidence

Fallback query when RCA-250 returns no results.

```kql
MonManagement
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName =~ "{AppName}" or logical_server_name =~ "{LogicalServerName}"
| where message has_any ("UpdateSlo", "SLO", "ScaleDatabase", "service_objective", "AlterDatabase")
| project TIMESTAMP, event, message
| order by TIMESTAMP asc
```

## RCA-260: Management Operations During Seeding Period (MonManagementOperations)

```kql
MonManagementOperations
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where logical_server_name =~ "{LogicalServerName}"
| where logical_database_name =~ "{LogicalDatabaseName}"
| project TIMESTAMP, operation, operation_friendly_name, state,
    start_time, end_time, error_code, error_message, error_severity,
    logical_server_name, logical_database_name
| order by TIMESTAMP asc
```

## RCA-261: User/Customer Operations During Seeding Period (MonNonPiiAudit)

```kql
MonNonPiiAudit
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName =~ "{AppName}" or server_principal_name != ""
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| where action_id in ("AL", "DR", "CR", "UNDO", "FG", "LO", "DBCC")
    or statement has_any ("ALTER", "DROP", "CREATE", "FAILOVER", "KILL", "DBCC", "BACKUP", "RESTORE")
| project TIMESTAMP, action_id, statement=substring(statement, 0, 300),
    server_principal_name, client_ip,
    succeeded, additional_information=substring(additional_information, 0, 200)
| order by TIMESTAMP asc
```

## RCA-262: Broader Audit Summary (MonNonPiiAudit)

Use when RCA-261 returns many rows.

```kql
MonNonPiiAudit
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName =~ "{AppName}" or server_principal_name != ""
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| summarize Count=count(), FirstSeen=min(TIMESTAMP), LastSeen=max(TIMESTAMP)
    by action_id, succeeded
| order by Count desc
```

---

## Calibrate Time Window for Phase 4+

After running RCA-200/210, set the tight time window for all remaining queries based on the failed seeding GUID's lifecycle.

**Step 1:** Pick the seeding GUID to investigate from RCA-200 results.

**Step 2:** Find the GUID's full timeline in MonDbSeedTraces (all events, not just failures):

```kql
MonDbSeedTraces
| where TIMESTAMP between(datetime({StartTime}) .. datetime({EndTime}))
| where AppName == "{AppName}"
| where local_seeding_guid == "{SeedingGuid}" or remote_seeding_guid == "{SeedingGuid}"
| summarize EarliestEvent = min(TIMESTAMP), LatestEvent = max(TIMESTAMP),
    FirstFailure = minif(TIMESTAMP, failure_code != 0)
```

**Step 3:** Derive `{FailStart}` and `{FailEnd}`:

- **Default:** `{FailStart}` = `EarliestEvent - 5min`, `{FailEnd}` = `LatestEvent + 5min`
- **If timeline > 40 minutes** (e.g., long-running seeding that eventually failed): use `FirstFailure - 20min` to `FirstFailure + 20min` instead
- Example: if `FirstFailure` = 13:00, then `{FailStart}` = 12:40, `{FailEnd}` = 13:20

This ensures Phase 4+ queries see the causal context without pulling excessive data.

---

## RCA-300: Engine Error Log — Full Timeline (MonSQLSystemHealth)

Keeps ALL messages (not just errors) to show the full picture of what was happening on the instance.
`IsError` and `IsSeeding` flags highlight the key rows while preserving surrounding context for causal tracing.

```kql
MonSQLSystemHealth
| where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
| where AppName == "{AppName}"
| where event in ("errorlog_written", "systemmetadata_written")
| extend MsgTime = extract(@"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", 1, message)
| extend ErrorCode = toint(extract(@"Error:\s*(\d+)", 1, message))
| extend Severity = toint(extract(@"Severity:\s*(\d+)", 1, message))
| extend IsError = message has "Error:" or message has "Severity:"
    or message has "exception" or message has "fail" or message has "abort"
| extend IsSeeding = message has "seeding" or message has "Build replica"
    or message has "BACKUP" or message has "RESTORE" or message has "streaming"
    or message has "VDI" or message has "DbCopy"
| extend MsgShort = substring(message, 0, 400)
| project MsgTime, ErrorCode, Severity, IsError, IsSeeding, MsgShort
| order by MsgTime asc
```

## RCA-310: Fabric API Lifecycle (MonFabricApi + WinFabLogs)

```kql
MonFabricApi
| where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
| where AppName has "{AppName}" and (partition_id == "{FabricPartitionId}" or event == "stack_trace") and event != "hadr_fabric_api_callback_invoke"
| extend replica_other=extract(@'pipe\\(.+?)-', 1, replicator_address_other)
| extend replicas_current1=extract(@'^.*?pipe\\(.+?)-', 1, replica_infos_current)
| extend replicas_current2=extract(@'^.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_current)
| extend replicas_current3=extract(@'^.*?pipe\\.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_current)
| extend replicas_current4=extract(@'^.*?pipe\\.*?pipe\\.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_current)
| extend replicas_current = iff(replicas_current1 !="", strcat(replicas_current1, iff(replicas_current2 != "", strcat(", ", replicas_current2), ""), iff(replicas_current3 != "", strcat(", ", replicas_current3), ""), iff(replicas_current4 != "", strcat(", ", replicas_current4), "")), "")
| extend replicas_previous1=extract(@'^.*?pipe\\(.+?)-', 1, replica_infos_previous)
| extend replicas_previous2=extract(@'^.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_previous)
| extend replicas_previous3=extract(@'^.*?pipe\\.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_previous)
| extend replicas_previous4=extract(@'^.*?pipe\\.*?pipe\\.*?pipe\\.*?pipe\\(.+?)-', 1, replica_infos_previous)
| extend replicas_previous = iff(replicas_previous1 !="", strcat(replicas_previous1, iff(replicas_previous2 != "", strcat(", ", replicas_previous2), ""), iff(replicas_previous3 != "", strcat(", ", replicas_previous3), ""), iff(replicas_previous4 != "", strcat(", ", replicas_previous4), "")), "")
| extend isEventBuildReplica = (event == "hadr_fabric_api_replicator_end_build_replica")
| extend seeding_performed_desc = iff(isEventBuildReplica, iff(seeding_performed, "true", "false"), "")
| extend result = iff(isnull(result), 0, result)
| extend error_code = iff(isnull(error_code), 0, error_code)
| extend event = iff(event == "hadr_fabric_api_return_result", strcat(event, "::", split(api_name, "::")[1]), event)
| extend originalEventTimestamp = tostring(originalEventTimestamp)
| distinct originalEventTimestamp, NodeName, event, current_state_desc, new_role_desc, open_mode_desc, catch_up_mode_desc, current_write_status_desc, work_id, replica_other, seeding_performed_desc, write_quorum_current, replicas_current, write_quorum_previous, replicas_previous, result, result_desc, error_code, error_state, fault_type_desc, fault_reason_desc, current_write_status, from_sequence_number, last_sequence_number, fabric_replica_id_other, api_name, error_message, replicator_address_other, replica_infos_current, dump_class, message
| union(
    WinFabLogs
    | where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
    | where TaskName == "FabricNode" and EventType == "NodeOpened"
    | project ClusterName, NodeName, originalEventTimestamp = ETWTimestamp
    | join kind=inner (
        MonRgLoad
        | where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
        | where AppName has "{AppName}" and partition_id == "{FabricPartitionId}"
        | summarize count() by ClusterName, NodeName
    ) on $left.ClusterName == $right.ClusterName and $left.NodeName == $right.NodeName
    | project tostring(originalEventTimestamp), NodeName, event = "node_startup", error_code = 0, result = 0
)
| order by originalEventTimestamp asc
```

## RCA-320: Build Replica FSM (MonFabricDebug)

```kql
MonFabricDebug
| where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
| where AppName == "{AppName}" and physical_database_id =~ "{PhysicalDatabaseId}"
| where event == "hadr_fabric_build_replica_operation_state_change"
| project TIMESTAMP, old_state_desc, new_state_desc, trigger_desc,
    is_primary, replica_id, operation_id, physical_database_id
| order by TIMESTAMP asc
```

## RCA-325: FabricReplicaBuildController State Changes (MonSQLSystemHealth)

When MonFabricDebug has no data, the build replica FSM state transitions are still captured in MonSQLSystemHealth as `[HADR Fabric]` engine log messages.

```kql
MonSQLSystemHealth
| where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
| where AppName == "{AppName}"
| where message has "[HADR Fabric] Build replica operation on secondary database"
    and message has "transitioned from state"
| extend MsgTime = extract(@"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", 1, message)
| extend OldState = extract(@"transitioned from state (\w+) to", 1, message)
| extend NewState = extract(@"transitioned from state \w+ to (\w+)\.", 1, message)
| extend PhysicalDbId = extract(@"secondary database\[([0-9a-fA-F-]+)\]", 1, message)
| extend PartitionId = extract(@"Partition\[([0-9a-fA-F-]+)\]", 1, message)
| extend SourceReplicaId = extract(@"Replicas\[([0-9a-fA-F-]+)\]->", 1, message)
| extend DestReplicaId = extract(@"->\[([0-9a-fA-F-]+)\]", 1, message)
| extend OperationId = extract(@"Source operation ID\[([0-9a-fA-F-]+)\]", 1, message)
| project MsgTime, TIMESTAMP, OldState, NewState, PhysicalDbId, PartitionId,
    SourceReplicaId, DestReplicaId, OperationId
| order by MsgTime asc
```

## RCA-330: Unified Timeline (MonFabricApi + MonSQLSystemHealth + MonDbSeedTraces)

Merges Fabric API events, engine error log, and seeding traces into a single chronological timeline.
This is the key correlation query — it shows exactly what Fabric did, what the engine logged, and what seeding reported, all interleaved by time.

```kql
let failStart = datetime({FailStart});
let failEnd = datetime({FailEnd});
let app = "{AppName}";
let fpid = "{FabricPartitionId}";
let seedGuid = "{SeedingGuid}";
// Fabric API events
let fabric = 
    MonFabricApi
    | where TIMESTAMP between(failStart .. failEnd)
    | where AppName has app and partition_id == fpid
    | where event != "hadr_fabric_api_callback_invoke"
    | extend EventTime = tostring(originalEventTimestamp)
    | extend Source = "FabricApi"
    | extend Side = "Source"  // FabricApi events are logged on the local (Source) side
    | extend Detail = strcat(event,
        iff(new_role_desc != "", strcat(" role=", new_role_desc), ""),
        iff(result_desc != "", strcat(" result=", result_desc), ""),
        iff(fault_type_desc != "", strcat(" fault=", fault_type_desc), ""),
        iff(error_code != 0, strcat(" err=", error_code), ""),
        iff(event == "hadr_fabric_api_return_result", strcat(" api=", api_name), ""))
    | project EventTime, Source, Side, NodeName, Detail;
// Engine error log
let engine =
    MonSQLSystemHealth
    | where TIMESTAMP between(failStart .. failEnd)
    | where AppName == app
    | where event in ("errorlog_written", "systemmetadata_written")
    | extend EventTime = extract(@"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", 1, message)
    | where isnotempty(EventTime)
    | extend Source = "Engine"
    | extend Side = iff(message has "received build replica response" or message has "remote", "Dest", "Source")
    | extend Detail = substring(message, 0, 300)
    | project EventTime, Source, Side, NodeName, Detail;
// Seeding traces
let seeding =
    MonDbSeedTraces
    | where TIMESTAMP between(failStart .. failEnd)
    | where AppName == app
    | where local_seeding_guid == seedGuid or remote_seeding_guid == seedGuid
    | extend EventTime = tostring(TIMESTAMP)
    | extend Source = "Seeding"
    | extend Side = iff(role_desc == "Source" or role_desc has "Forwarder", "Source",
        iff(role_desc == "Destination" or role_desc has "ForwarderDestination", "Dest", "?"))
    | extend Detail = strcat(event, " role=", role_desc,
        iff(failure_code != 0, strcat(" FAIL=", failure_code, " ", failure_message), ""),
        " state=", internal_state_desc,
        " xfer=", transferred_size_bytes, "/", database_size_bytes)
    | project EventTime, Source, Side, NodeName = "", Detail;
// Build FSM state transitions
let fsm =
    MonFabricDebug
    | where TIMESTAMP between(failStart .. failEnd)
    | where AppName == app
    | where event == "hadr_fabric_build_replica_operation_state_change"
    | extend EventTime = tostring(TIMESTAMP)
    | extend Source = "FSM"
    | extend Side = iff(is_primary, "Source", "Dest")
    | extend Detail = strcat(old_state_desc, " → ", new_state_desc, " trigger=", trigger_desc,
        " replica=", replica_id)
    | project EventTime, Source, Side, NodeName = "", Detail;
fabric
| union engine
| union seeding
| union fsm
| order by EventTime asc
```

## RCA-400: Resource Pressure (MonRgLoad)

```kql
MonRgLoad
| where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
| where AppName == "{AppName}"
| project TIMESTAMP,
    cpu_pct = round(app_cpu_load_normalized, 1),
    mem_pct = round(app_memory_load_normalized, 1),
    iops = app_iops_load, iops_cap = app_iops_load_cap,
    node_cpu = round(cpu_load, 1)
| order by TIMESTAMP asc
```

## RCA-410: Log Space / RG History

```kql
MonDmLogSpaceInfo
| where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
| where AppName == "{AppName}"
| project TIMESTAMP, counter_name, instance_name, cntr_value
| order by TIMESTAMP asc
```

```kql
MonSqlRgHistory
| where TIMESTAMP between(datetime({FailStart}) .. datetime({FailEnd}))
| where AppName == "{AppName}"
| project TIMESTAMP, event, log_rate_limit_in_bytes_per_second,
    log_rate_governor_enabled, log_rate_limit_reason
| order by TIMESTAMP asc
```
