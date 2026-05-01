---
name: unhealthy-worker-cl
description: Triages unhealthy SQL Managed Instance Worker.CL applications. Checks TDE errors, CodePackage failures, storage limits, remote storage, containers, node health, and GeoDR connectivity and DB service health to route to the correct team. MI-only — not for SQL DB or Hyperscale.
---

# Triage Unhealthy Worker.CL Applications (Managed Instance Only)

> **Scope**: This skill applies to **Azure SQL Managed Instance** ICMs only. It is **not applicable** to Azure SQL Database (single database, elastic pool) or Hyperscale. Worker.CL is a Managed Instance-specific Service Fabric application type.

Investigate SQL Managed Instance Worker.CL.* applications (Worker.CL.WCOW, Worker.CL.WCOW.SQL22...) detected in an unhealthy state. This skill systematically checks for common root causes and determines the appropriate escalation path.

## Overview

Worker.CL applications in Azure SQL Managed Instance can transition to unhealthy state when underlying infrastructure, database operations, or system conditions cause issues. This skill provides a systematic investigation workflow to identify the root cause and route to the appropriate support team.

Application health states:
- **Healthy (2)**: Green - Normal operation
- **Warning (1)**: Yellow - Degraded but functional  
- **Unhealthy (0)**: Red - Service impact

## Required Information

- `{StartTime}` / `{EndTime}`: Time window for investigation (ISO 8601 format) — extracted from ICM/user
- `{ClusterName}`: Service Fabric cluster name (e.g., `tr2.lkgtst1-a.worker.sqltest-eg1.mscds.com`) — extracted from ICM/user or resolved from Kusto
- **At least ONE of** `{AppName}` or `{LogicalServerName}` (the other will be resolved automatically):
  - `{AppName}`: Worker.CL application name (e.g., `f4624352230a`)
  - `{LogicalServerName}`: Managed Instance logical server name (e.g., `myserver`)

### Parameter Resolution Rules

**Always attempt to resolve any missing parameter** using the Kusto resolution query below.

| Provided | Missing | Action |
| -------- | ------- | ------ |
| Both AppName + LogicalServerName + ClusterName | — | Proceed with all queries |
| AppName only | LogicalServerName | Resolve via Kusto. If resolved → proceed with all queries. If not → proceed, **skip Batch B/C** (QL500, QL501, QL903, QL800) |
| LogicalServerName only | AppName | Resolve via Kusto. If resolved → proceed. If not → ❌ **FAIL** — request AppName from caller |
| Neither | Both | ❌ **FAIL** — request at least AppName or LogicalServerName from caller |
| ClusterName missing | ClusterName | Resolve via Kusto (tenant_ring_name). If not resolved → ❌ **FAIL** — request ClusterName from caller |

#### Kusto Resolution Query

Use the **QL000** resolution queries in [queries.md](references/queries.md#ql000---parameter-resolution) to resolve missing parameters. Filter by whichever identifier is available (AppName or LogicalServerName).

- Use returned values to fill in any missing parameters (AppName, LogicalServerName, ClusterName)
- If query returns empty and AppName is still missing → ❌ **FAIL** — request AppName from caller
- If query returns empty and LogicalServerName is still missing → proceed without it (skip Batch B/C)
- If query returns empty and ClusterName is still missing → ❌ **FAIL** — request ClusterName from caller

## Performance Optimization — MI-Specific Shortcuts

> **Speed Matters**

### Skip DBINFO100 for Worker.CL Incidents

For Managed Instance Worker.CL incidents, **SKIP the `get-db-info` skill entirely**. The required identifiers (AppName, ClusterName, LogicalServerName) are extracted from **ICM custom fields** or resolved via the Kusto resolution query.

- `AppName` → Parsed From Incident Title (`fabric:/Worker.CL.WCOW.SQL22/{AppName}`) or ICM custom field "AppName" 
- `ClusterName` → Parsed from Incident Title (e.g., tr4431.useuapeast2-a.worker.database.windows.net) or ICM custom field "Primary Tenant Ring"
- `LogicalServerName` → ICM custom field "Server Name" or "ServerName"
- If `AppName` is missing from ICM but `LogicalServerName` is available → resolve AppName from Kusto (see Parameter Resolution Rules above)

Populate a simplified Database Environment table from ICM data — do NOT run DBINFO100.

### Extract Region from ClusterName Directly

For MI, extract the region from ClusterName instead of DNS lookup:
- ClusterName: `tr4431.useuapeast2-a.worker.database.windows.net`
- Region: `useuapeast2` (second dot-segment, strip trailing `-a`/`-b`/etc.)
- Then look up the Kusto cluster from the XML/query as usual.

---

## Investigation Workflow

> **⚡ Performance Optimization**: ALL queries (validation + diagnostic) run in a **single parallel batch**. Interpret QL100/QL200 first for early exit; if no early exit, proceed to interpret the rest without re-querying.

### Single Parallel Batch — Run ALL Queries At Once

**⚡ CRITICAL**: Execute **ALL** queries below in **one parallel batch**. Do NOT wait for QL100/QL200 before running diagnostic queries. The early-exit checks (Steps 1-2) are evaluated during **interpretation**, not during execution.

**Why**: Running QL100+QL200 sequentially before Phase 2 adds 1-2 minutes of overhead. Since early exits are rare (~5% of cases), it is faster to always run everything in parallel and discard diagnostic results if QL100/QL200 indicate early exit.

**Batch A — Main Kusto cluster** (run these 10 queries in parallel):

| Query | Step | Check | Table |
| ----- | ---- | ----- | ----- |
| QL100 | 1 | Application health state timeline | AlrWinFabHealthApplicationState |
| QL200 | 2 | Update SLO in progress | MonManagedServers + MonChangeManagedServerInstanceReqs |
| QL300 | 3 | TDE/AKV certificate issues | MonSQLSystemHealth |
| QL400 | 4 | CodePackage launch failures | WinFabLogs |
| QL600 | 6 | Remote storage failures | MonSQLXStore |
| QL700 | 7 | Database InCreate mode | MonManagement + MonAnalyticsDBSnapshot |
| QL901 | 9a | SQL process running in container | MonNodeTraceETW |
| QL902 | 9b | Container/ByoVnet hosting events | WinFabLogs |
| QL904 | 11 | Node telemetry emission | MonNodeTraceETW |
| QL905 | 12 | DB services health state | AlrWinFabHealthServiceState |

**Batch B — Main cluster, requires LogicalServerName** (run in parallel with Batch A if LogicalServerName available; skip if not):

| Query | Step | Check | Table |
| ----- | ---- | ----- | ----- |
| QL500 | 5a | Instance storage utilization | MonManagedInstanceResourceStats |
| QL501 | 5b | Storage account quota exceeded | MonSQLXStore |
| QL903 | 10 | Managed Instance disabled state | MonManagedServers |

**Batch C — NorthEurope cluster override** (run in parallel with Batches A/B; requires LogicalServerName — skip if not):

| Query | Step | Check | Table |
| ----- | ---- | ----- | ----- |
| QL800 | 8 | GeoDR connectivity | MonMIGeoDRFailoverGroupsConnectivity |

> **⚠️ Cluster Override for QL800:** Execute on `https://sqlazureneu2.kusto.windows.net:443` / `sqlazure1` regardless of which cluster is used for other queries.

---

> **Note**: Related/similar incident search is handled by the agent-level `similar-incidents` skill (see Availability.agent.md Step 6). Pass `AppName` and `ClusterName` as MI-specific identifiers, along with `DynamicSearchTerms` collected from Phase 2 results.

---

## Interpretation Order

After ALL queries return, interpret results in this order:

### Early Exit Checks (interpret first)

#### Step 1: Verify Unhealthy State (QL100 results)

- Application state = 0 (Unhealthy) persisting in the time window → **Continue to diagnostic interpretation**
- Application state = 2 (Healthy) throughout → Issue already resolved. **⛔ STOP — report as resolved.**

#### Step 2: Check Update SLO Exclusion (QL200 results)

- Rows returned with `UpdatingPricingTier` → No action; wait for SLO completion. **⛔ STOP.**
- No rows → **Continue to diagnostic interpretation.**

### Diagnostic Interpretation Guide

After confirming unhealthy state and no SLO update, analyze remaining query results per the guide below.

### Step 3: TDE Certificate Issue (QL300)

- Messages containing "Azure Key Vault" errors or "Cannot find server asymmetric key with thumbprint"
- Exclude: "Triggering deny external connections db due to Azure Key Vault Client Error"
- **If found**: 🚩 Transfer to **Azure SQL DB / SQL Managed Instance: TDE**

### Step 4: CodePackage Launch Failure (QL400)

- `ProcessUnexpectedTermination` events for XdbPackageLauncherSetup
- "failed to start" events for XdbPackageLauncher.exe or MDS
- `transfer_queue` field → "Perf" or "Telemetry"
- **Launcher/XdbPackage issue**: Transfer to **Mi Perf - Azure SQL DB / SQL Managed Instance: SQL Engine Performance and Reliability**
- **MDS issue**: Transfer to **Telemetry - Azure SQL DB / Telemetry, Monitoring, Runners**

### Step 5: Storage Limit Hit (QL500/QL501)

- Storage used >= reserved storage (quota exceeded)
- `AccountQuotaExceeded` errors in XStore requests
- **If found**: 🚩 Transfer to **Mi Perf - Azure SQL DB / SQL Managed Instance: SQL Engine Performance and Reliability**

### Step 6: Remote Storage Connectivity Issues (QL600)

- Error codes:
  - **12007, 12017, 12175**: Network/connectivity issues (customer network setup)
  - **12002, 12030**: SQL cannot reach remote storage service
  - **87**: File metadata too large
- `is_zero_request = 1`: Request never reached remote storage (network infrastructure issue)
- **Network errors (12007/12017/12175)**: Transfer to **Azure SQL Managed Instance Connectivity and Networking**
- **SQL errors (12002, 12030, 87)**: Transfer to **Mi Perf - Azure SQL DB / SQL Managed Instance: SQL Engine Performance and Reliability**

### Step 7: Database InCreate Mode (QL700)

- `create_mode` values: "Copy", "Normal", "Restore"
- **Copy mode**: Transfer to **GeoDR - Azure SQL DB / SQL Managed Instance: GeoDR**
- **Normal mode**: Transfer to **DB CRUD - Azure SQL DB / SQL Managed Instance: Database CRUD**
- **Restore mode**: Transfer to **B/R - Azure SQL DB / SQL Managed Instance: Backup and Restore**

### Step 8: GeoDR Connectivity Issue (QL800)

- `MonMIGeoDRFailoverGroupsConnectivity` records indicating connectivity loss between regions
- Multiple rows returned = ongoing connectivity issue
- `ConnectivityIssue` and `RCA` fields provide root cause details
- This is typically customer error; upgrade can proceed with InBuild replicas
- 🚩 Note: Transfer to **GeoDR - Azure SQL DB / SQL Managed Instance: GeoDR** if customer request requires investigation

### Step 9: SQL Process Not Started in Container (QL901/QL902)

> **Key insight**: The SQL process runs inside a Windows container (Worker.CL.WCOW). When QL901 returns no rows, it means the SQL process was **NOT** running — this is fundamentally a **container issue**. Either the container failed to start, the container became unresponsive, or the container started but SQL process within it could not launch. QL902 provides hosting-layer context on what went wrong with the container.

- QL901: MonNodeTraceETW messages with CodePackageName = "Code" and Worker.CL.WCOW indicate the SQL process **IS** running. **No rows returned** means the SQL process was **NOT** running during the incident — this is a container-level failure.
- QL902: Hosting, container, or ByoVnetProvider events with Warning or Error level provide additional context on container infrastructure failures (e.g., fabricdns blocking NC creation, CRL import slowdown, containerd service issues).
- **If SQL process was NOT running (QL901 returns NO rows)**: 🚩 Container issue confirmed. Transfer to **Azure SQL Managed Instance Connectivity and Networking**
  - Common root causes from historical incidents:
    - `fabricdns` process blocking network connection creation → kill fabricdns to unblock
    - Certificate Revocation List (CRL) import slowdown during container startup
    - `containerd` service issues requiring node/service restart

### Step 10: SQL MI Disabled State (QL903)

- Instance `state` = "Disabled"
- Compare with DB service health (should remain Healthy/Warning)
- **If MI in Disabled state**: Transfer to **SQL MI CRUD - SQL MI Provisioning team** (not an availability issue)

### Step 11: Unresponsive Node (QL904)

- Any rows returned: Node is emitting telemetry (healthy node)
- No rows returned: Node is unresponsive and not emitting telemetry
- **If node is unresponsive**: 🚩 Transfer to **SQL MI Platform and T-Train Deployment queue**

### Step 12: Database Services Unhealthy (QL905)

- State 2 (Green) = Healthy, State 1 (Yellow) = Warning, State 0 (Red) = Unhealthy
- **DB services unhealthy (state 0)**: → Run **Step 12a** (invoke the `StorageEngine/database-recovery` skill) to check for database recovery. Then transfer to **Azure SQL DB / Managed Instance: Availability queue**
- **DB services healthy but app unhealthy**: Check the unhealthy event source from QL100 or ICM alert details:
  - If the unhealthy event is **"Container connectivity check resulted in a failure"** (SourceId contains `ContainerShare.Code`, Property = `Periodic container connectivity check`) → This is a **container issue**. Transfer to **Azure SQL Managed Instance Connectivity and Networking**
  - Otherwise → Analyze the event and what component it is related to; Default transfer location is **Azure SQL DB / Managed Instance: SQL Platform and T-Train Deployments**

### Step 12a: Database Recovery In Progress

> **When to run**: Only when Step 12 (QL905) shows DB services in unhealthy state (state 0).

**Action**: Invoke the **`StorageEngine/database-recovery`** skill (`../../StorageEngine/database-recovery/SKILL.md`) to check whether databases on this instance are in recovery.

**Parameters to pass to the skill**:
- `AppName`: From the current investigation context
- `physical_database_id`: Use `*` or iterate over known database IDs if multiple databases exist on the instance
- `ClusterName`: From the current investigation context
- `NodeName`: Use the node(s) where QL905 reported unhealthy state
- `StartTime` / `EndTime`: Same time window as the current investigation
- `kusto-cluster-uri` / `kusto-database`: Already resolved by the `execute-kusto-query` skill

**Interpreting the skill output** — correlate with the QL905 unhealthy window:

- **Recovery detected with timeline overlapping the QL905 unhealthy window** → Database recovery is the likely root cause of the unhealthy DB service state. Include in the RCA: which database was under recovery, recovery duration, and max recovery percentage reached.
- **Recovery reaching 100% near the time QL905 transitions back to healthy** → **Confirms** recovery as root cause.
- **Correlation rule**: Recovery is the root cause only if the recovery timeline overlaps the QL905 unhealthy window AND no higher-priority check (Steps 3–11) already identified the issue. If recovery rows exist but a higher-priority root cause was also found (e.g., TDE, storage), treat recovery as a consequence rather than a cause.

**Escalation**: Transfer to **Azure SQL DB / Managed Instance: Availability queue** for all recovery scenarios.


## Decision Tree

```
Is Application Health State = 0 (Unhealthy)?
├─ NO → Issue resolved; verify with customer
└─ YES
   ├─ Update SLO in Progress? (QL200)
   │  ├─ YES → No action; wait for SLO completion
   │  └─ NO → Continue
   │
   ├─ TDE/AKV Error Found? (QL300)
   │  ├─ YES → Transfer to TDE
   │  └─ NO → Continue
   │
   ├─ CodePackage Launch Failure? (QL400)
   │  ├─ YES (Launcher) → Transfer to Mi Perf
   │  ├─ YES (MDS) → Transfer to Telemetry
   │  └─ NO → Continue
   │
   ├─ Storage Limit Hit? (QL500-501)
   │  ├─ YES → Transfer to Mi Perf
   │  └─ NO → Continue
   │
   ├─ Remote Storage Error? (QL600)
   │  ├─ YES (Network) → Transfer to Connectivity
   │  ├─ YES (SQL) → Transfer to Mi Perf
   │  └─ NO → Continue
   │
   ├─ Database InCreate? (QL700)
   │  ├─ YES (Copy) → Transfer to GeoDR
   │  ├─ YES (Normal) → Transfer to DB CRUD
   │  ├─ YES (Restore) → Transfer to B/R
   │  └─ NO → Continue
   │
   ├─ GeoDR Connectivity Issue? (QL800)
   │  ├─ YES → Note and potentially transfer to GeoDR
   │  └─ NO → Continue
   │
   ├─ SQL Process NOT Running in Container? (QL901-902)
   │  ├─ YES (QL901 returns NO rows → Container issue: SQL not running in Worker.CL.WCOW) → Transfer to Connectivity
   │  │  └─ (Common causes: fabricdns block, CRL import slowdown, containerd failure)
   │  └─ NO (QL901 returns rows → SQL was running) → Continue
   │
   ├─ Managed Instance Disabled? (QL903)
   │  ├─ YES → Transfer to MI CRUD/Provisioning (not availability issue)
   │  └─ NO → Continue
   │
   ├─ Node Unresponsive? (QL904)
   │  ├─ YES (No telemetry) → Transfer to SQL MI Platform & T-Train
   │  └─ NO → Continue
   │
   ├─ Database Services Unhealthy? (QL905)
   │  ├─ YES (state 0) → Run Step 12a (invoke StorageEngine/database-recovery skill)
   │  │  ├─ Recovery progressing (% increasing)? → No-op; let recovery finish → Availability queue (no action needed)
   │  │  ├─ Recovery stuck (% not advancing)? → Availability queue (additional investigation required)
   │  │  ├─ Recovery resets X%→0% multiple times? → SQL process likely killed → Availability queue + warn user: DO NOT kill SQL process
   │  │  └─ No recovery / no overlap → Transfer to Availability queue (unknown DB service cause)
   │  ├─ NO (state 2, but app unhealthy)
   │  │  ├─ Unhealthy event = "Container connectivity check failed"? → Transfer to Connectivity & Networking
   │  │  └─ Other event → Analyze the event and what component it is related to; Default to Platform & T-Train queue
   │  └─ NO → Continue
   │
   └─ UNKNOWN ROOT CAUSE
      ├─ Agent-level similar-incidents skill will search for related incidents (AppName, ClusterName, DynamicSearchTerms)
      ├─ 🚩 ESCALATE to **On-Call DRI** with all query results
      └─ Provide health timeline, query outputs, time window
```

## Reference

- [knowledge.md](references/knowledge.md) — Definitions, application architecture, and related documentation
- [principles.md](references/principles.md) — Debug principles and escalation criteria
- [queries.md](references/queries.md) — All Kusto queries used in investigation
