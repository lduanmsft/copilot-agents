# Login Failures - Knowledge Base

## Monitor Definitions

### Login Failures Runner

Raises an incident when a frontend keeps having non-user-error failed logins above a certain percentage threshold. This monitor detects backend-side login failures that are not caused by customer mistakes.

**ICM Title Pattern:** Contains "Login Failures Runner" or similar phrasing.

### LoginFailureCause (CRGW0001)

Fires when login success rate for a database drops below 99%. The alert includes a `LoginFailureCause` classification:

**ICM Title Pattern:**
```
{{SLO}} [Sev-3 LoginFailureCause: {{LOGIN_FAILURE_CAUSE}}] [{{CLUSTER_SHORT_NAME}}/AIMS://AZURE SQL DB/Availability] Sterling CRGW0001: Login success rate is below 99%
```

**LoginFailureCause values** (extracted from ICM title, routes to owning team):

**Availability-owned causes:**

| Cause | Description | Route To |
|-------|-------------|----------|
| `IsUnplacedReplica` | Replica has no available node for placement | `unplaced-replicas` skill |
| `IsReplicaInBuild` | Replica is being built/seeded | Check replica health |
| `IsPartitionInReconfigurationMostly` | Partition in extended reconfiguration | `failover` skill |
| `IsSqlPartitionInErrorStateFromWinFabHealth` | SF health reports partition error | Check WinFab health |
| `HasSqlDump` | SQL process crash/dump occurred | `dump` skill |
| `LoginErrorsFound_40613_4_master` | Error 40613 state 4 — database cannot reach logical master | Check master DB health |
| `LoginErrorsFound_40613_127` | Error 40613 state 127 — database in warmup, cannot open | `error-40613-state-127` skill |

**Gateway-owned causes:**

| Cause | Description | Route To |
|-------|-------------|----------|
| `IsGWProxyThrottledTCPTimeoutToBackend` | Gateway TCP timeout to backend | Gateway team |
| `IsGWProxyThrottledTCPTimeoutToBackend_SingleTrAffected` | Gateway TCP timeout, single TR affected | Gateway team |
| `IsGWProxyThrottledTCPTimeoutToBackend_FewTRsAffected` | Gateway TCP timeout, few TRs affected | Gateway team |
| `IsGWProxyThrottledTCPTimeoutToBackend_FewGWsAffected` | Gateway TCP timeout, few GWs affected | Gateway team |
| `IsGatewayRoutingToWrongNode` | Gateway routing to incorrect node | Gateway team |
| `IsGwUriCacheMisroutingGlobalizationIssue` | Gateway URI cache misrouting | Gateway team |
| `LoginErrorsFound_40613_10` | Error 40613 state 10 — gateway routing error | Gateway team |
| `LoginErrorsFound_26078_33` | Error 26078 state 33 — connection routing error | Gateway team |

**GeoDR-owned causes:**

| Cause | Description | Route To |
|-------|-------------|----------|
| `UpdateSloInProgress_40613_127` | SLO change in progress causing state 127 | `update-slo` skill |

**Performance/SOS-owned causes:**

| Cause | Description | Route To |
|-------|-------------|----------|
| `HasHighLatencyLoginsTopWaitStat_PREEMPTIVE_OS_AUTHENTICATIONOPS` | High login latency — authentication ops | Performance investigation |
| `HasHighLatencyLoginsTopWaitStat_PWAIT_SECURITY_FEDAUTH_AADLOOKUP` | High login latency — AAD/Entra lookup | Security team |
| `HasHighLatencyLoginsTopWaitStat_CMEMTHREAD` | High login latency — memory thread contention | Performance investigation |

## Key Error Codes

### Error 40613 States

| State | Name | Description |
|-------|------|-------------|
| 4 | Cannot access master | User database cannot reach logical master for metadata |
| 126 | Database in transition | Role change actively executing, database temporarily unavailable |
| 127 | Cannot open during warmup | Role change complete but database still warming up |
| 129 | HADR not available | Database not in PRIMARY or SECONDARY state |
| 84 | Cannot access master | Alternative state for master access failure |

### Common SQL Engine Errors

| Error | Severity | Description |
|-------|----------|-------------|
| 823 | 24 | Operating system I/O error |
| 824 | 24 | Logical I/O error (torn page, checksum failure) |
| 825 | 10 | I/O retry succeeded after initial failure |
| 9002 | 17 | Transaction log full |
| 17883 | 1 | Scheduler appears to be non-yielding |
| 17884 | 1 | New queries not picked up by worker thread |

## LoginOutages OutageReasonLevel1 Categories

The `LoginOutages` table classifies outage causes into a 3-level hierarchy. The primary categories are:

| OutageReasonLevel1 | Description | Typical Cause |
|---------------------|-------------|---------------|
| **Failover** | Planned or unplanned replica transition | Maintenance, node failure, process crash |
| **UnplacedReplica** | No node available to host the replica | Capacity, constraints, node outage |
| **QuorumLoss** | Majority of replicas unavailable | Multiple simultaneous failures |
| **SqlServerUnhealthy** | SQL Server process issue | Crash, assertion, resource exhaustion |
| **GwProxyIssues** | Gateway proxy routing problem | Gateway-level failure |
| **XdbhostUnhealthy** | Xdbhost process issue | Frontend proxy failure |
| **LongLogins** | Login processing taking too long | Resource contention, slow I/O |
| **DACLimitsHit** | DAC connection limits reached | Too many DAC connections |
| **FrozenVM** | Virtual machine frozen | Infrastructure issue |
| **LogicalServerDisabled** | Server intentionally disabled | Administrative action |
| **UserInitiatedRestore** | Restore operation in progress | Customer-initiated restore |
| **AKVTDEIssue** | Azure Key Vault / TDE issue | Key access or rotation problem |
| **VnetRuleNotAdded** | VNet firewall rule missing | Network configuration |
| **SocketDuplicationStuck** | Socket duplication issue | Connection handoff failure |

## Platform vs User Errors

### Platform Errors (investigated by this skill)
- `is_user_error == 0` in MonLogin
- Caused by infrastructure issues, failovers, replica health
- Trigger monitors and ICM incidents
- Require engineering investigation

### User Errors (NOT investigated by this skill)
- `is_user_error == 1` in MonLogin
- Wrong password, firewall blocks, invalid database name
- Customer-side issues
- No engineering action needed

## Key Telemetry Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `MonLogin` | Login success/failure events | `error`, `state`, `is_success`, `is_user_error`, `login_flags` |
| `LoginOutages` | Platform-classified outage records | `OutageReasonLevel1/2/3`, `OutageType`, `durationSeconds` |
| `SqlFailovers` | Completed failover events | `FailoverStartTime`, `FailoverEndTime`, `ReconfigurationType` |
| `MonDmDbHadrReplicaStates` | Replica synchronization states | `synchronization_state_desc`, `database_state_desc`, `is_primary_replica` |
| `MonSQLSystemHealth` | SQL Server error log | `message`, `event` |
| `WinFabLogs` | Service Fabric logs | `EventType`, `Text` |
| `MonManagementOperations` | Control plane operations | `operation_type`, `operation_parameters` |

## ReadOnlyIntent Flag

The `login_flags` field in MonLogin contains a bitmask. Bit 21 (value 2097152) indicates a ReadOnlyIntent connection:

```
ReadOnlyIntent = (login_flags / 2097152) % 2
```

- `ReadOnlyIntent == 1`: Client requested read-only routing (connects to secondary replica)
- `ReadOnlyIntent == 0`: Standard read-write connection (connects to primary replica)

If only ReadOnlyIntent connections are failing, the issue is specific to secondary replicas.

## Related Documentation

All source materials used to build and maintain this skill. These URLs are fetched
during skill creation and updates to extract knowledge, principles, and queries.

### Internal Documentation (eng.ms / ADO Wiki)
- [CRGW0001 - Login Success Rate Below 99%](https://dev.azure.com/msdata/Database%20Systems/_wiki/wikis/TSG-SQL-DB-Availability?pagePath=%2FSQL%20DB%20Availability%20TSGs%2FHA%2FAutoTSG%2FCRGW0001%20Login%20success%20rate%20is%20below%2099%25%20LoginErrorsFound_40613_127)
  - All steps (1–16): Login failure classification, LoginOutages, failover correlation, replica health, error logs, unplaced replicas, node deactivation

### Public Documentation
- [Azure SQL Database high availability](https://learn.microsoft.com/en-us/azure/azure-sql/database/high-availability-sla)
- [Troubleshoot transient connection errors](https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-connectivity-issues)
- [Error 40613 documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-errors-issues)
