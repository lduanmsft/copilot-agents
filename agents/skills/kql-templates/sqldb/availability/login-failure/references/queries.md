# Kusto Queries for Login Failures Diagnostics

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp in UTC

**Resource identifiers:**
- `{LogicalServerName}`: Logical server name
- `{LogicalDatabaseName}`: Logical database name
- `{AppName}`: From get-db-info skill (sql_instance_name)
- `{ClusterName}`: From get-db-info skill (tenant_ring_name)
- `{fabric_partition_id}`: From get-db-info skill

---

## LF-100 - Login Failure Volume and Timeline

**Purpose:** Identify non-user-error login failure volume, error codes, states, and affected nodes over time. This is the primary query to confirm login failure occurrence and pattern.

**What to look for:**
- Sustained error counts per minute (vs brief transient spikes)
- Specific error codes (40613 state 126 = transition, state 127 = warmup, state 4 = master unreachable)
- Whether failures are on a single node or multiple nodes
- Whether ReadOnlyIntent connections are affected (secondary replica issue)
- Package type: `sqlserver` (backend) vs `xdbhost` (frontend proxy)

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonLogin
| where originalEventTimestamp between (StartTime .. EndTime)
| where logical_server_name =~ "{LogicalServerName}"
| where database_name =~ "{LogicalDatabaseName}"
| where event == "process_login_finish"
| where is_success == 0
| where is_user_error == 0
| extend ReadOnlyIntent = (login_flags / 2097152) % 2
| summarize
    FailureCount = count(),
    ReadOnlyIntentFailureCount = countif(ReadOnlyIntent == 1),
    Errors = make_set(error, 100),
    States = make_set(state, 100),
    Packages = make_set(package, 100),
    MachineNames = make_set(MachineName, 10),
    HostNames = make_set(host_name, 10)
    by TimeBucket = bin(originalEventTimestamp, 1m), NodeName
| order by TimeBucket asc, NodeName asc
| limit 500
```

**Assessment:**
- If failures span < 30 seconds with a single error/state → Likely transient failover, cross-check with LF-300
- If failures span > 2 minutes → Investigate further with remaining queries
- If `ReadOnlyIntentFailureCount > 0` → Secondary replica issue, check LF-400 for secondary health
- If `package` includes `xdbhost` → Xdbhost-level issue, check LoginOutages for `XdbhostUnhealthy`

---

> **Note:** LF-110 (Login Failure Percentage Over Time), LF-120 (Error/State Breakdown Over Time),
> and LF-200 (LoginOutages) have been removed from this skill. They overlap with the
> [Connectivity login-failure skill](../../Connectivity/connectivity-scenarios/login-failure/SKILL.md)
> which covers these via `determine-prevailing-error` and `determine-login-outage` sub-skills.
> See SKILL.md Step 2 for handoff details.

---

## LF-300 - Correlate with SqlFailovers

**Purpose:** Identify failover events during the login failure window to determine if failures are failover-related.

**What to look for:**
- Failovers that overlap with the login failure time window
- `ReconfigurationType`: Planned (SwapPrimary) vs Unplanned (Failover)
- `CRMAction`: What triggered the failover (e.g., NodeDown, ProcessFailure)
- Login failures that persist after `FailoverEndTime` indicate a post-failover issue

```kql
SqlFailovers
| where FailoverStartTime between (datetime({StartTime}) .. datetime({EndTime}))
| where logical_server_name =~ "{LogicalServerName}"
| where logical_database_name =~ "{LogicalDatabaseName}"
| project
    FailoverStartTime,
    FailoverEndTime,
    FailoverDurationSeconds = datetime_diff('second', FailoverEndTime, FailoverStartTime),
    ReconfigurationType,
    CRMAction,
    PLBConstraintType,
    ExitCode,
    OldPrimary,
    NewPrimary,
    PartitionId,
    ApiFaultReason
| order by FailoverStartTime asc
```

**Correlation check:**
- Login failures should occur BETWEEN `FailoverStartTime` and `FailoverEndTime`
- Errors persisting AFTER `FailoverEndTime` → check recovery (state 127) or stuck transition (state 126)
- No failovers found → investigate replica health (LF-400), node health (LF-600, LF-800)

---

## LF-400 - Replica States and Transitions

**Purpose:** Analyze the health and synchronization state of all database replicas to identify replica-level issues causing login failures.

**What to look for:**
- Replicas with `database_state_desc` != ONLINE
- Replicas transitioning to unhealthy synchronization states
- `is_suspended = 1` indicating suspended data movement
- Primary replica role changes
- All replicas in non-SYNCHRONIZED state simultaneously (possible quorum issue)

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonDmDbHadrReplicaStates
| where TIMESTAMP between (StartTime .. EndTime)
| where AppName =~ "{AppName}"
| sort by replica_id, NodeName, PreciseTimeStamp asc
| extend prev_internal_state = prev(internal_state_desc, 1, "")
| extend prev_replica = prev(replica_id), prev_node = prev(NodeName)
| extend prev_sync_state = prev(synchronization_state_desc, 1, "")
| extend prev_db_state = prev(database_state_desc, 1, "")
| extend is_first_record = (replica_id != prev_replica or NodeName != prev_node)
| extend next_replica = next(replica_id), next_node = next(NodeName)
| extend is_last_record = (replica_id != next_replica or NodeName != next_node or isnull(next_replica))
| extend internal_state_changed = (not(is_first_record) and internal_state_desc != prev_internal_state)
| extend sync_state_changed = (not(is_first_record) and synchronization_state_desc != prev_sync_state)
| extend db_state_changed = (not(is_first_record) and database_state_desc != prev_db_state)
| where is_first_record or is_last_record or internal_state_changed or sync_state_changed or db_state_changed
| project
    PreciseTimeStamp,
    replica_id,
    NodeName,
    is_primary_replica,
    internal_state_desc,
    synchronization_state_desc,
    synchronization_health_desc,
    database_state_desc,
    is_suspended,
    suspend_reason_desc,
    is_first_record,
    is_last_record,
    internal_state_changed,
    sync_state_changed,
    db_state_changed
| order by replica_id, NodeName, PreciseTimeStamp asc
```

**Warning signs:**
- 🚩 Primary replica `database_state_desc` changes to non-ONLINE
- 🚩 All replicas show `synchronization_state_desc` = NOT_SYNCHRONIZED simultaneously
- 🚩 `is_suspended = 1` on any replica
- 🚩 `internal_state_desc` shows RESOLVING or RECOVERING for extended period

---

## LF-500 - SQL Error Log Messages

**Purpose:** Extract relevant error messages from SQL Server error logs during the incident window.

**What to look for:**
- Specific error codes: 823/824/825 (I/O errors), 9002 (log full), 17883/17884 (scheduler issues)
- Process failure messages
- Assertion failures
- Resource exhaustion messages
- Recovery-related errors

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let IsRelevantMessage = (s: string)
{
    s !has "accepting vlf header" and
    s !has "CHadrTransportReplica" and
    s !has "CFabricCommonUtils" and
    s !has "HADR TRANSPOR" and
    s !has "DbMgrPartnerCommitPolicy" and
    s !has "AlwaysOn Availability Groups" and
    s !has "Querying Property Manager" and
    s has "error:"
};
MonSQLSystemHealth
| where TIMESTAMP between (StartTime .. EndTime)
| where event == "systemmetadata_written"
| where AppName =~ "{AppName}"
| where LogicalServerName =~ "{LogicalServerName}"
| where IsRelevantMessage(message)
| extend ErrorCode = extract('Error: [0-9]*, Severity: [0-9]*, State: [0-9]*', 0, message)
| extend DisplayMessage = replace('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9]+ [a-zA-Z0-9]* ', '', message)
| extend DisplayMessage = extract(@'Error: [0-9]+, Severity: [0-9]+, State: [0-9]+\.\s*([^\r\n]+?)(?:\.|\n|\n|$)', 1, DisplayMessage)
| extend DisplayMessage = trim(@'[\t\n\f\r ]+', DisplayMessage)
| summarize Count = count(), MinTime = min(TIMESTAMP), MaxTime = max(TIMESTAMP) by ErrorCode, NodeName, DisplayMessage
| extend ErrorCode = iff(ErrorCode != '', ErrorCode, '(No specific error code)')
| project Count, NodeName, MinTime, MaxTime, ErrorCode, DisplayMessage
| order by Count desc
| limit 500
```

---

## LF-600 - Unplaced Replica Events

**Purpose:** Detect unplaced replica events from Service Fabric that could cause login failures due to unavailable replicas.

**What to look for:**
- Presence of unplaced replica events during the login failure window
- Duration of unplaced state (min to max timestamp)
- High count indicates persistent placement failure

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
WinFabLogs
| where TIMESTAMP between (StartTime .. EndTime)
| where Id =~ "{fabric_partition_id}"
| where EventType == "UnplacedReplica"
| summarize
    FirstEvent = min(ETWTimestamp),
    LastEvent = max(ETWTimestamp),
    EventCount = count()
```

**Assessment:**
- If events found → Login failures likely caused by unplaced replicas. Invoke `unplaced-replicas` skill.
- If no events → Unplaced replicas not the cause, continue checking other areas.

---

## LF-700 - Management Operations

**Purpose:** Identify customer or platform management operations that may have triggered or contributed to login failures.

**What to look for:**
- SLO changes (UpdateSloTarget) during the incident
- Geo-replication operations
- Database copy or restore operations
- Failover group changes

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
MonManagementOperations
| where originalEventTimestamp between (StartTime .. EndTime)
| where operation_parameters has "{LogicalServerName}" and operation_parameters has "{LogicalDatabaseName}"
| sort by request_id, originalEventTimestamp asc
| summarize
    operation_type = take_any(operation_type),
    TIMESTAMP = min(originalEventTimestamp),
    events_timeline = make_list(bag_pack("timestamp", originalEventTimestamp, "event", event))
    by request_id
| project request_id, operation_type, TIMESTAMP, events_timeline
| order by TIMESTAMP asc
| take 500
```

**Common `operation_type` values and interpretation:**

| operation_type | Description | Impact on Login Failures |
|----------------|-------------|-------------------------|
| `UpdateDatabase` | SLO/tier change | Failover expected during transition → invoke `update-slo` skill |
| `CreateSecondary` | Geo-replication setup | May affect replica availability |
| `FailoverDatabase` | Manual or planned failover | Direct cause of login failures |
| `RemoveSecondary` | Geo-replication teardown | Replica count change |
| `CreateDatabaseCopy` | Database copy operation | Resource contention possible |
| `RestoreDatabase` | Restore operation | Database unavailable during restore |
| `RenameDatabase` | Database rename | Brief unavailability expected |
| Other | See MonManagementOperations docs | Evaluate timing correlation with failures |

If `UpdateDatabase` (SLO change) found → invoke `update-slo` skill for detailed analysis.
For other operation types, check whether the operation timing correlates with the login failure window.

---

> **Note:** LF-800 (Node Deactivation Events) has been removed from this skill. It overlaps with the
> node-health queries (NH100–NH700) run by the [Connectivity login-failure skill](../../Connectivity/connectivity-scenarios/login-failure/SKILL.md)
> at Step 9. See SKILL.md Step 2 for handoff details.

---
