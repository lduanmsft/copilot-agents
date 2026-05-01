# Kusto Queries for Worker.CL Health Debugging

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (ISO 8601 format, e.g., 2026-03-26T10:00:00Z)
- `{EndTime}`: End timestamp in UTC (ISO 8601 format)

**Resource identifiers:**
- `{AppName}`: Worker.CL application name (e.g., `f4624352230a`) - **REQUIRED**
- `{ClusterName}`: Service Fabric cluster name (e.g., `tr2.lkgtst1-a.worker.sqltest-eg1.mscds.com`) - **REQUIRED**
- `{LogicalServerName}`: Managed Instance logical server name - **OPTIONAL** (used for storage/GeoDR queries; fallback to AppName if not available)
- `{LogicalDatabaseName}`: Logical database name - **OPTIONAL**

---

## Step 0: Parameter Resolution

### QL000 - Parameter Resolution

**Purpose:** Resolve missing parameters (AppName, LogicalServerName, ClusterName) when only one identifier is available.

**What to look for:**
- `AppName` (sql_instance_name) — Worker.CL application name
- `LogicalServerName` (logical_server_name) — Managed Instance logical server name
- `ClusterName` (tenant_ring_name) — Service Fabric cluster name

**Expected output:**
- A single row with all three identifiers populated
- If no rows returned, the provided identifier may not exist in the time range

```kusto
// When AppName is available:
MonAnalyticsDBSnapshot
| where sql_instance_name =~ "{AppName}"
| summarize arg_max(TIMESTAMP, logical_server_name, tenant_ring_name) by sql_instance_name
| project AppName = sql_instance_name, LogicalServerName = logical_server_name, ClusterName = tenant_ring_name, TIMESTAMP
```

```kusto
// When LogicalServerName is available:
MonAnalyticsDBSnapshot
| where logical_server_name =~ "{LogicalServerName}"
| summarize arg_max(TIMESTAMP, sql_instance_name, tenant_ring_name) by logical_server_name
| project AppName = sql_instance_name, LogicalServerName = logical_server_name, ClusterName = tenant_ring_name, TIMESTAMP
```

---

## Step 1: Verify Unhealthy State

### QL100 - Application Health State Timeline

**Purpose:** Determine if application is currently in unhealthy state and for how long. Creates a timeline chart showing health state transitions.

**What to look for:**
- State value = 0 (Unhealthy - Red) in the time window
- Duration of unhealthy state
- Time of first transition to unhealthy
- Pattern: Sustained vs. intermittent vs. transient spike
- Current state at end of time window

**Expected output:**
- Time series chart with state values over time
- Timestamp of last state change
- State transitions (Healthy → Warning → Unhealthy or direct)

```kusto
AlrWinFabHealthApplicationState
| where PreciseTimeStamp > datetime({StartTime})
| where PreciseTimeStamp < datetime({EndTime})
| where ClusterName =~ '{ClusterName}'
| where ApplicationName contains "Worker.CL"
| where ApplicationName contains "{AppName}"
| order by PreciseTimeStamp desc
| extend state = iff(HealthState =~ "Ok", 2, iff(HealthState =~ "Warning", 1, 0))
| project PreciseTimeStamp, state
| render timechart
```

**Interpretation:**
- Chart entirely at value 2 → Application is healthy; issue resolved
- Chart showing value 0 sustained → Ongoing unhealthy state; investigate
- Single spike to 0 → Transient issue; likely self-resolved if back to 2
- Oscillation (0 ↔ 1 ↔ 2) → Underlying issue causing recurrence

---

## Step 2: Check Exclusions

### QL200 - Check Update SLO Target Status

**Purpose:** Verify SLO update status using Kusto telemetry.

**What to look for:**
- `state =~ "UpdatingPricingTier"` indicates SLO update in progress
- `target_sql_instance_name` matches the application
- Timestamp of state change

**Expected output:**
- If rows returned: SLO update ongoing; no further action needed
- If no rows: No active SLO update; proceed with diagnostics

```kusto
let app_name = "{AppName}";
MonManagedServers
| summarize arg_max(PreciseTimeStamp, state) by name, managed_server_id
| where state =~ "UpdatingPricingTier"
| join kind=inner (
    MonChangeManagedServerInstanceReqs
    | summarize arg_max(PreciseTimeStamp, target_sql_instance_name) by managed_server_id
    ) on managed_server_id
| where target_sql_instance_name =~ app_name
| project name, state, PreciseTimeStamp, target_sql_instance_name
```

---

## Step 3: Check for TDE Certificate Issues

### QL300 - TDE Certificate and Key Vault Issues

**Purpose:** Identify Azure Key Vault (TDE) errors that would block all SQL operations.

**What to look for:**
- Error messages containing "Azure Key Vault"
- "Cannot find server asymmetric key with thumbprint"
- Error 15507: "A key required by this operation appears to be corrupted"
- Exclude false positives: "Triggering deny external connections db due to Azure Key Vault Client Error"
- Timestamp of errors

**Expected output:**
- If messages found: TDE/AKV issue identified
- If no messages: No TDE issue; proceed to next diagnostic

```kusto
MonSQLSystemHealth
| where PreciseTimeStamp > datetime({StartTime})
| where PreciseTimeStamp < datetime({EndTime})
| where AppTypeName contains "Worker.CL"
| where AppName =~ "{AppName}"
| where (message has "Azure Key Vault" or message has "Cannot find server asymmetric key with thumbprint" or error_id == 15507)
| where not (message has "Triggering deny external connections db due to Azure Key Vault Client Error")
| summarize arg_max(PreciseTimeStamp, message) by AppName, message
| project PreciseTimeStamp, AppName, message
```

**Escalation trigger:** If any results returned → Transfer to **TDE** team immediately.

---

## Step 4: Check for CodePackage Launch Failures

### QL400 - CodePackage Launch Failures

**Purpose:** Identify code package activation failures (SQL Engine launchers, MDS, etc.) that prevent application startup.

**What to look for:**
- `EventType =~ "ProcessUnexpectedTermination"` with XdbPackageLauncherSetup error
- `EventType =~ "CodePackageInstance"` with "failed to start" 
- Program name: XdbPackageLauncher.exe, MDS, or other packages
- `transfer_queue` indicating escalation path: "Perf" or "Telemetry"
- Error count and time range of failures

**Expected output:**
- Row with `transfer_queue` = "Perf" → Transfer to Mi Perf
- Row with `transfer_queue` = "Telemetry" → Transfer to Telemetry
- No rows → No CodePackage issue

**Note:** This query is optimized for XdbPackageLauncherSetup; MDS support coming soon.

```kusto
let app_name = "{AppName}";
let cluster_name = "{ClusterName}";
let app_start_time = datetime({StartTime});
let app_end_time = datetime({EndTime});
WinFabLogs
| where ETWTimestamp > app_start_time
| where ETWTimestamp < app_end_time
| where ClusterName =~ cluster_name
| where Level in ("Warning", "Error")
| extend isLauncherSetupIssue = EventType =~ "ProcessUnexpectedTermination" and Text has "XdbPackageLauncherSetup"
| extend isLaunchingIssue = EventType =~ "CodePackageInstance" and Text has "Program = XdbPackageLauncher.exe" and Text has "failed to start"
| where isLauncherSetupIssue or isLaunchingIssue
| parse Text with * "Program = " programName ", " *
| parse Text with * "ApplicationId " applicationId " " *
| summarize min_time=min(ETWTimestamp), max_time=max(ETWTimestamp), failure_count=count() by isLauncherSetupIssue, programName, ClusterName, Id, EventType, applicationId
| extend transfer_queue = iff(programName has "MDS", "Telemetry", iff(isLauncherSetupIssue or programName has "XdbPackageLauncher", "Perf", ""))
| join kind=leftsemi (
    WinFabLogs
    | where ETWTimestamp > app_start_time
    | where ETWTimestamp < app_end_time
    | where ClusterName =~ cluster_name
    | where EventType =~ "EventDispatcher"
    | where Text contains app_name
    | parse Text with * "ApplicationName=fabric:/Worker.CL" * "/" detected_app_name ", " *
    | where detected_app_name =~ app_name
    | project app_id_from_dispatcher=Id
    ) on $left.applicationId == $right.app_id_from_dispatcher
| project min_time, max_time, failure_count, programName, transfer_queue, EventType
```

**Escalation trigger:**
- If `transfer_queue = "Perf"` → Transfer to **Mi Perf**
- If `transfer_queue = "Telemetry"` → Transfer to **Telemetry**

---

## Step 5: Check for Storage Limit Hits

### QL500 - Instance Storage Utilization

**Purpose:** Check if the Managed Instance has hit its storage quota limit.

**What to look for:**
- `storage_space_used_mb >= reserved_storage_mb` condition
- Time when quota was exceeded
- Current utilization percentage

**Expected output:**
- If rows found: Storage limit hit; cannot allocate more
- If no rows: Storage not at limit

```kusto
MonManagedInstanceResourceStats
| where TIMESTAMP > datetime({StartTime})
| where TIMESTAMP < datetime({EndTime})
| where LogicalServerName =~ "{LogicalServerName}" // Optional: omit this line if LogicalServerName unknown
| project TIMESTAMP, LogicalServerName, storage_space_used_mb, reserved_storage_mb
| where storage_space_used_mb >= reserved_storage_mb
| order by TIMESTAMP desc
```

**Interpretation:**
- If results found → Instance storage quota exceeded; escalate to **Mi Perf**
- Used >= Reserved → Cannot grow databases; blocking all writes

**If LogicalServerName is unknown:** Remove the `where LogicalServerName` clause; results will show all MIs with storage quota issues. Verify the LogicalServerName in results matches your target instance by checking cluster context.

---

### QL501 - Storage Account Quota Exceeded

**Purpose:** Check if the remote storage account (Azure Storage) has hit its quota limit.

**What to look for:**
- `event =~ "xio_failed_request"` with `errorcode =~ "AccountQuotaExceeded"`
- Timestamps of failures
- Count of blocked actions

**Expected output:**
- If rows found: Storage account quota exceeded
- If no rows: Storage account has capacity

```kusto
MonSQLXStore
| where TIMESTAMP > datetime({StartTime})
| where TIMESTAMP < datetime({EndTime})
| where LogicalServerName =~ "{LogicalServerName}" // Optional: omit if LogicalServerName unknown
| where event =~ "xio_failed_request" 
| where errorcode =~ "AccountQuotaExceeded"
| summarize blocked_action_count=count() by LogicalServerName, TIMESTAMP
| order by TIMESTAMP desc
```

**Escalation trigger:** If any results → Transfer to **Mi Perf**

**If LogicalServerName is unknown:** Remove the LogicalServerName filter; verify results match your cluster/instance context.

---

## Step 6: Check for Remote Storage Connectivity Issues

### QL600 - Remote Storage Request Failures

**Purpose:** Identify failures in remote storage (Azure Storage) communication with detailed error classification.

**What to look for:**
- `event =~ "xio_failed_request"` indicating failed storage request
- Error codes:
  - 12007, 12017, 12175: Network connectivity issues (customer-side)
  - 12002, 12030: Service-side storage issues
  - 87: File metadata too large
- `is_zero_request = 1`: Request never reached storage (network infrastructure)
- `retry_count > 10`: Multiple failed retries
- `file_path`, `account`: Which storage account affected

**Expected output:**
- If network errors with `is_zero_request = 1` → Transfer to **Connectivity**
- If network errors with `retry_count > 10` → Transfer to **Connectivity**
- If SQL errors (12002, 12030, 87) → Transfer to **Mi Perf**
- No rows → No remote storage issue

```kusto
let app_name = "{AppName}";
let query_start = datetime({StartTime});
let query_end = datetime({EndTime});
MonSQLXStore
| where TIMESTAMP > query_start
| where TIMESTAMP < query_end
| where AppName =~ app_name
| where event =~ "xio_failed_request"
| where isnotempty(file_path) 
| where retry_count > 10
| where mapped_errorcode in (87, 12002, 12030, 12007, 12017, 12175)
| extend account=extract("https://([a-z0-9]*)[.*]", 1, file_path, typeof(string))
| extend is_zero_request=iff((request_id =~ "00000000-0000-0000-0000-000000000000"), 1, 0)
| summarize 
    failure_count=count(), 
    unique_accounts=dcount(account), 
    first_error=min(TIMESTAMP), 
    last_error=max(TIMESTAMP) 
    by NodeName, ClusterName, account, AppName, mapped_errorcode, is_zero_request, SubscriptionId
| order by last_error desc
```

**Classification and escalation:**
- If `mapped_errorcode in (12007, 12017, 12175)` and `is_zero_request = 1` → **Connectivity** (transient network)
- If `mapped_errorcode in (12007, 12017, 12175)` and `retry_count > 10` → **Connectivity** (persistent network)
- If `mapped_errorcode in (12002, 12030, 87)` → **Mi Perf** (platform storage issue)

---

## Step 7: Check for Database InCreate/InCopy/InRestore Mode

### QL700 - Database Create/Copy/Restore Mode Status

**Purpose:** Identify databases stuck in long-running create, copy, or restore operations.

**What to look for:**
- `property_name =~ "IsInCreate"` with `event =~ "fabric_property_updating"`
- `create_mode` values: "Copy" (geo-replication), "Normal" (standard), "Restore" (restore operation)
- `transfer_queue` indicating escalation path
- Timestamps showing how long operation has been in progress

**Expected output:**
- Rows indicate database stuck in operation
- `transfer_queue` value determines escalation: GeoDR, DB CRUD, or Backup & Restore
- No rows → No database stuck in create/copy/restore

```kusto
let app_name = "{AppName}";
let query_start = datetime({StartTime});
let query_end = datetime({EndTime});
MonManagement
| where keys contains "Worker.CL"
| where keys contains app_name
| where property_name =~ "IsInCreate"
| summarize arg_max(TIMESTAMP, event) by keys
| parse keys with * "Worker.CL" * "/" sql_instance_name "/SQL.ManagedUserDb/" database_id
| extend database_id=toupper(database_id)
| join kind=inner (
    MonAnalyticsDBSnapshot
    | where TIMESTAMP > query_start
    | where TIMESTAMP < query_end
    | summarize arg_max(TIMESTAMP, create_mode) by logical_database_id, physical_database_id, logical_server_name, sql_instance_name
    ) on $left.sql_instance_name == $right.sql_instance_name and $left.database_id == $right.logical_database_id
| where event =~ "fabric_property_updating"
| extend transfer_queue=iff(create_mode =~ "Copy", "GeoDR", iff(create_mode =~ "Normal", "DB CRUD", "Backup and Restore"))
| project TIMESTAMP, sql_instance_name, logical_server_name, logical_database_id, create_mode, transfer_queue
| order by TIMESTAMP desc
```

**Escalation:**
- If `create_mode = "Copy"` → Transfer to **GeoDR**
- If `create_mode = "Normal"` → Transfer to **DB CRUD**
- If `create_mode = "Restore"` → Transfer to **Backup and Restore**

---

## Step 8: Check for GeoDR Connectivity Issues

### QL800 - GeoDR/Mirrored DR Connectivity Status

**Purpose:** Identify geographic replication connectivity problems preventing replica synchronization.

**⚠️ CRITICAL — Cluster Override:** This query MUST always run on the **NorthEurope** Kusto cluster regardless of which cluster is used for other queries. The `MonMIGeoDRFailoverGroupsConnectivity` table exists **only** on this cluster.
- **Cluster URI:** `https://sqlazureneu2.kusto.windows.net:443`
- **Database:** `sqlazure1`

**What to look for:**
- `ManagedServerName == "{LogicalServerName}"` or `PartnerServerName == "{LogicalServerName}"`
- Multiple rows returned = ongoing connectivity issue
- `ConnectivityIssue` and `RCA` fields provide details about the root cause
- PartnerServerName (remote region database)

**Expected output:**
- No rows: GeoDR connectivity healthy
- Rows found: GeoDR connectivity issue present — check `ConnectivityIssue` and `RCA` columns for details
- Note: Replicas in InBuild state when connectivity issue exists

```kusto
// ⚠️ MUST run on NorthEurope cluster: https://sqlazureneu2.kusto.windows.net:443 / sqlazure1
let server_name = "{LogicalServerName}"; // Optional: if unknown, modify query per instructions below
MonMIGeoDRFailoverGroupsConnectivity
| where TIMESTAMP > datetime({StartTime})
| where TIMESTAMP < datetime({EndTime})
| where (ManagedServerName == server_name or PartnerServerName == server_name)
| order by TIMESTAMP desc
```

**If LogicalServerName unknown:** This query requires `ManagedServerName` or `PartnerServerName`. If LogicalServerName is not available, **skip QL800** — GeoDR connectivity cannot be checked without a managed server name. Note this in the report as "QL800 skipped: LogicalServerName not available."

**Interpretation:**
- If rows returned: GeoDR connectivity issue confirmed — read `ConnectivityIssue` and `RCA` fields for root cause details
- Note: This is often customer error (network changes); upgrade can proceed even if replica is in InBuild state
- If critical: Transfer to **GeoDR** for investigation
- Replicas stuck InBuild: Check ServiceFabricExplorer (SFE); can proceed with upgrade if connectivity is customer-side

---

## Step 9: SQL Process Container Issues

### QL901 - SQL Process Container Startup Issues

**Purpose:** Verify whether the SQL process was running inside the Worker.CL.WCOW container during the incident time window. These MonNodeTraceETW messages indicate that a SQL process **IS** running. The absence of rows means the SQL process was **NOT** running.

**What to look for:**
- CodePackageName = "Code" indicating SQL code package
- Worker.CL.WCOW references in message
- Rows returned during the incident time window

**Expected output:**
- 🚩 **If NO rows returned**: SQL process was NOT running in the container during the incident — this confirms a container startup issue
- **If rows found**: SQL process WAS running — container startup is not the problem; investigate other causes

```kusto
let app_name = "{AppName}";
MonNodeTraceETW
| where TIMESTAMP > datetime({StartTime})
| where TIMESTAMP < datetime({EndTime})
| where Message contains app_name
| where NodeName contains "DB"
| where Message contains "Worker.CL.WCOW"
| where Message contains "\" CodePackageName \""
| parse Message with * "\" CodePackageName \"" packageName "\"" *
| where packageName =~ "Code"
| summarize row_count=count(), first_seen=min(TIMESTAMP), last_seen=max(TIMESTAMP) by ClusterName, NodeName
```

**Interpretation:**
- **Rows returned** → SQL process was active on these nodes during the time window. Container startup is NOT the issue.
- **No rows returned** → SQL process never started in the container during the incident window. This is a container startup failure.
  - 🚩 Transfer to: **Azure SQL Managed Instance Connectivity and Networking**

---

### QL902 - Container and Network Provider Events

**Purpose:** Alternative check for container issues via Hosting layer events (Warning/Error level).

**What to look for:**
- EventType contains "container" or "ByoVnetProvider"
- Level = "Warning" or "Error"
- Hosting task errors
- Multiple rows = persistent container issues

**Expected output:**
- If rows found: Container infrastructure issues
- If no rows: No container events detected

```kusto
let cluster_name = "{ClusterName}";
WinFabLogs
| where ClusterName =~ cluster_name
| where ETWTimestamp > datetime({StartTime})
| where ETWTimestamp < datetime({EndTime})
| where TaskName contains "Hosting"
| where Level !contains "info"
| where (EventType contains "container" or EventType =~ "ByoVnetProvider")
| project ETWTimestamp, NodeName, EventType, Level, Id, Text
```

**Escalation trigger:** Multiple Warning/Error rows → Transfer to **Connectivity & Networking**

---

## Step 10: Managed Instance State

### QL903 - Managed Instance State

**Purpose:** Check if Managed Instance is in Disabled state (expected operationally, not SQL availability issue).

**What to look for:**
- Instance state value
- State = "Disabled" indicates administrative state, not availability issue
- Compare with database health to verify services are still healthy

**Expected output:**
- state = "Disabled" → Instance administratively disabled (transfer to MI CRUD/Provisioning)
- state = "Created" or other → Instance operationally up

```kusto
let server_name = "{LogicalServerName}"; // Optional: if unknown, search by cluster context
MonManagedServers
| where name =~ server_name
| summarize arg_max(PreciseTimeStamp, state) by name
| project name, state, PreciseTimeStamp
```

**If LogicalServerName unknown:** Search by cluster instead:
```kusto
MonManagedServers
| where PreciseTimeStamp > datetime({StartTime})
| where PreciseTimeStamp < datetime({EndTime})
| where ClusterName =~ "{ClusterName}"
| summarize arg_max(PreciseTimeStamp, state) by name, ClusterName
| project name, state, PreciseTimeStamp, ClusterName
```

**Interpretation:**
- If state = "Disabled": Not an SQL availability issue (transfer to MI CRUD)
- If state = "Created": Instance state healthy; issue is elsewhere

---

## Step 11: Node Telemetry

### QL904 - Node Telemetry Emission Check

**Purpose:** Verify if node is responsive by checking if it's emitting telemetry events.

**What to look for:**
- Any rows returned = node is healthy and emitting telemetry
- No rows returned = node is unresponsive (not sending telemetry)
- Min/Max timestamps showing telemetry coverage

**Expected output:**
- Rows found: Node is responsive and healthy
- No rows: Node not emitting telemetry for 45+ minutes (unresponsive node)

```kusto
MonNodeTraceETW
| where TIMESTAMP > datetime({StartTime})
| where TIMESTAMP < datetime({EndTime})
| where ClusterName =~ "{ClusterName}"
| summarize first_telemetry=min(TIMESTAMP), last_telemetry=max(TIMESTAMP), event_count=count() by NodeName
```

**Escalation trigger:** No rows → Node is unresponsive → Transfer to **SQL MI Platform and T-Train Deployment queue**

---

## Step 12: Database Services Health

### QL905 - Database Services Health State

**Purpose:** Determine if database services (not application) are in unhealthy state. Distinguishes DB service issue from application management issue.

**What to look for:**
- Service health state values:
  - State 2 = Healthy (Green)
  - State 1 = Warning (Yellow)
  - State 0 = Unhealthy (Red)
- Sustained unhealthy state vs. transient spike
- Timestamp of state transitions

**Expected output:**
- Chart showing service health timeline over incident window
- State values indicating health progression
- Compare: is DB service healthy even though app is unhealthy?

```kusto
AlrWinFabHealthServiceState
| where PreciseTimeStamp > datetime({StartTime})
| where PreciseTimeStamp < datetime({EndTime})
| where ApplicationName contains "Worker.CL"
| where ApplicationName contains "{AppName}"
| order by PreciseTimeStamp desc
| extend state = iff(HealthState =~ "Ok", 2, iff(HealthState =~ "Warning", 1, 0))
| project PreciseTimeStamp, state
| render timechart
```

**Interpretation:**
- State entirely at 2 (Healthy) → DB services healthy; app issue is management-related
- State at 0-1 (Warning/Unhealthy) → DB services have underlying issues

**Escalation:**
- If DB services unhealthy (state 0) → Transfer to **Availability queue**
- If DB services healthy but app unhealthy → Transfer to **SQL Platform and T-Train Deployments**

---

## Step 12a: Database Recovery In Progress

> Invoke the **`StorageEngine/database-recovery`** skill (`../../StorageEngine/database-recovery/SKILL.md`) which performs comprehensive recovery analysis using its own query set (REC100–REC500).
>
> Pass the following parameters from the current investigation context:
> - `AppName`, `ClusterName`, `NodeName` (from QL905 results or earlier resolution)
> - `physical_database_id` (use `*` or iterate if multiple databases)
> - `StartTime` / `EndTime`, `kusto-cluster-uri` / `kusto-database`
>
> Correlate the skill's output with the QL905 unhealthy window to determine if recovery is the root cause.

---

## Reference: Expected Query Outputs

### Healthy Application

**QL100 result:**
- Chart shows value 2 (green) throughout time window
- No transitions to 1 or 0
- Conclusion: Application is healthy; issue likely resolved

### Unhealthy State - TDE Issue

**QL300 result:**
```
PreciseTimeStamp: 2026-03-26 14:35:22
AppName: f4624352230a
message: Cannot find server asymmetric key with thumbprint '0x...'
```
- Action: Escalate to TDE immediately

### Unhealthy State - Storage Quota

**QL500 result:**
```
storage_space_used_mb: 1048576
reserved_storage_mb: 1048576
TIMESTAMP: 2026-03-26 14:30:00
```
- Conclusion: Storage at 100%; cannot grow
- Action: Escalate to Mi Perf

### Unhealthy State - Remote Storage Error

**QL600 result:**
```
mapped_errorcode: 12007
is_zero_request: 1
failure_count: 45
```
- Conclusion: Network error, transient infrastructure issue
- Action: Escalate to Connectivity
