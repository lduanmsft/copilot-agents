# Worker.CL Application Health — Concepts and Architecture

## Terms and Concepts

### Service Fabric Health States

Application health in Azure Service Fabric has three discrete levels:

| State | Value | Color | Meaning |
|-------|-------|-------|---------|
| Healthy | 2 | Green | Application is operating normally, all replicas healthy |
| Warning | 1 | Yellow | Application is degraded; Can be operational or no, depending on the specific Warning case. |
| Unhealthy | 0 | Red | Application cannot serve requests; critical issues with replicas or dependencies |

Health state is determined by:
- Replica health status (up/down, synced/not synced)
- System health events from platform
- Application-level health reports (if configured)
- Infrastructure dependencies (storage, network, TDE)

### Worker.CL Application

**Worker.CL** is a Azure Service Fabric application type running on SQL Managed Instance that hosts SQL database workloads.

**Application naming convention:**
- Fabric application name: `fabric:/Worker.CL/{instance-id}`
- Example: `fabric:/Worker.CL/f4624352230a`

The application contains:
- **Primary replica**: Handles read-write operations
- **Secondary replicas**: Maintain synchronized data copies (typically 2-3 replicas)
- **Service instances**: SQL Engine services hosting the database

### Replica States in Service Fabric

- **Ready**: Replica is healthy and ready to serve requests
- **InBuild**: Replica is being built/synchronized (expected during failover or copy operations)
- **Dropped**: Replica is no longer part of the replica set
- **InBuildSecondary**: Secondary replica in build process
- **InBuildPrimary**: Primary replica being rebuilt (rare, indicates severity)

### Clustername and Physical Infrastructure

**ClusterName format:** `{ring-name}.{region}.worker.sqltest-{environment}.mscds.com`

Example: `tr2.lkgtst1-a.worker.sqltest-eg1.mscds.com`

The cluster name identifies:
- Physical Service Fabric cluster hosting the tenant ring
- Geographic region (East, West, etc.)
- Environment (production, test, staging)

## Worker.CL Application Lifecycle

### Normal Healthy State

1. **Primary replica**: Running, accepting connections
2. **Secondary replicas**: Synchronized with primary
3. **Data replication**: Continuous log shipping to secondaries
4. **Health reports**: Regular heartbeats received from replicas
5. **Storage**: Connecting successfully to remote storage for data files

### Transition to Unhealthy

Application transitions to unhealthy when:

1. **Primary replica fails**: Cannot restart/recover
2. **Replicas cannot build/synchronize**: Infrastructure or dependency issue
3. **Critical dependency fails**: TDE keys, storage access, network connectivity
4. **Code packages fail to launch**: SQL Engine or launcher executable crashes
5. **Storage quota exceeded**: Cannot allocate more space
6. **Long-running database operations blocked**: Database create/copy/restore stuck

### Recovery Actions

- **Transient issues**: Automatic replica rebuild/failover (seconds to minutes)
- **Persistent issues**: Manual intervention required from support
- **Escalation to specialist**: Route to appropriate support queue

## Common Root Causes for Unhealthy Worker.CL

### 1. TDE Certificate / Azure Key Vault Issues

**Symptom**: Application cannot access Transparent Data Encryption key stored in customer's Azure Key Vault.

**Root causes:**
- Customer revoked or deleted key
- Key permissions changed
- Network connectivity to AKV blocked
- Service principal authentication failed

**Impact**: Cannot decrypt database pages; all queries fail.

**Resolution**: Restore key or permissions; coordinate with customer.

### 2. CodePackage Launch Failure

**Symptom**: SQL Engine or supporting services fail to start on replica.

**Root causes:**
- Binary corruption (deployment issue)
- Resource exhaustion (CPU, memory)
- File system issue
- Launcher crash preventing service startup

**Components:**
- **XdbPackageLauncher**: Responsible for starting SQL Engine processes
- **XdbPackageLauncherSetup**: Setup/initialization of launcher
- **MDS package**: Monitoring/diagnostics service

**Impact**: Replica cannot start; stays InBuild or transitions to Dropped.

### 3. Storage Quota Limits

**Symptom**: Instance storage or storage account quota exhausted.

**Error indicators:**
- `storage_space_used_mb >= reserved_storage_mb`
- `AccountQuotaExceeded` errors in XStore requests
- Write failures with storage-related errors

**Impact**: Database cannot grow; operations blocked.

**Root causes:**
- Databases using more space than allocated
- Insufficient SLO tier provisioning
- Data file growth exceeding limits
- Backup files not cleaned up

### 4. Remote Storage Connectivity Issues

**Symptom**: SQL Engine cannot communicate with XStore service hosting data files.

**Network errors (customer-side):**
- Error 12007, 12017, 12175: Network connectivity blocked
- Firewall, NSG, or user-defined routes preventing traffic

**Service errors (platform-side):**
- Error 12002, 12030: Platform cannot reach storage service
- Error 87: File metadata too large
- Transient Azure Storage service issues

**Impact**: Replica cannot read/write data; stuck InBuild or read-only.

### 5. Database InCreate/InCopy/InRestore Mode

**Symptom**: Database is stuck during long-running operations.

**Operations:**
- **Create**: New database creation in progress
- **Copy**: Geo-replication or database copy (mirroring/mirrored link)
- **Restore**: Point-in-time restore or backup restore

**Impact**: Application unhealthy while operation proceeds; transitions to healthy upon completion (unless blocked).

**Root causes:**
- Operation blocked by infrastructure issue
- Replicas cannot build for copy/restore
- Seeding/data transfer stuck

### 6. GeoDR Connectivity Issues

**Symptom**: Geo-replicated database has connectivity problem to partner region.

**Scenario**: Replicas in InBuild state due to:
- Network partition between regions
- Service Fabric cluster issue on partner side
- Storage synchronization blocked

**Impact**: Secondary databases cannot synchronize; upgrade may proceed.

**Root causes:**
- Customer network changes (VNet peering, routing)
- Azure networking infrastructure issues (transient)
- Partner cluster maintenance/outage

### 7. SQL Process Not Started in Container

**Symptom**: Either the container itself failed to start, or the container is running but the SQL process inside it is not. Usually tied to container issues (often at startup).

**Key characteristic**: The replica will be InBuild not only on the Worker.CL application but also on the Marker service (`Managed.Server.RS` or `Managed.Server.LS` depending on the edition). This distinguishes container issues from other InBuild causes.

**Root causes:**
- Container runtime issue (containerd service failure)
- Certificate Revocation List (CRL) import slowdown during container startup
- Node-level networking preventing container communication
- Resource constraints on node

**Impact**: Replica cannot start; stays InBuild or transitions to Dropped.

**Detection**: If MonNodeTraceETW has no events for this Worker.CL.WCOW app with `CodePackageName = "Code"`, that confirms SQL is not running inside the container.

**Escalation**: Transfer to **Connectivity & Networking** team

### 8. Managed Instance Disabled State

**Symptom**: Managed Instance in "Disabled" administrative state.

**Note**: This is NOT an availability issue; it's an operational state.

**Expected behavior:**
- MB services remain **Healthy** or **Warning** (not affected)
- Database accessibility unchanged
- Maintenance jobs may be aware of disabled state

**When this occurs:**
- Planned administrative maintenance
- Scheduled operations requiring MI to be offline temporarily
- Expected and non-urgent

**Escalation**: Transfer to **SQL MI Provisioning** team (CRUD queue), not Availability

### 9. Unresponsive Node

**Symptom**: Service Fabric node is not emitting telemetry for extended period.

**Causes:**
- Node connectivity issue (network isolated)
- Node performance degraded (CPU/memory exhausted)
- Node process crashed
- Hardware failure

**Detection**: No MonNodeTraceETW events for 45+ minutes

**Impact**: Cannot deploy new replicas to this node; may affect workload placement

**Escalation**: Transfer to **SQL MI Platform and T-Train Deployment queue**

### 10. Database Services Unhealthy

**Symptom**: Database service health state is unhealthy (state 0), separate from application health.

**Distinction:**
- **Application health** (QL100 - AlrWinFabHealthApplicationState) → Management layer
- **Service health** (QL905 - AlrWinFabHealthServiceState) → SQL database services

**Scenarios:**
- DB services unhealthy but DB layer working → DB service issue
- App unhealthy but services healthy → Management/orchestration issue
- Both unhealthy → Root cause in DB layer

**Root causes:**
- SQL engine service crashes
- Replica communication failures
- Data consistency issues
- Service Fabric partition issues
- **Database under recovery** (see below)

**Escalation:**
- If DB services unhealthy: Transfer to **SQL Managed Instance: Availability queue**
- If DB services healthy but app unhealthy: Transfer to **SQL Platform and T-Train Deployments**

### 11. Database Under Recovery

**Symptom**: One or more databases within the Worker.CL application are actively performing recovery. During recovery, the DB service reports as unhealthy (state 0), which causes the Worker.CL application health to drop to Unhealthy.

**How it manifests**:
- QL905 shows DB services unhealthy (state 0) for an extended period
- `MonSQLSystemHealth` contains "Recovery of database '{database-id}'" messages with increasing recovery percentage
- The unhealthy state self-resolves once recovery completes (reaches 100%)
- No infrastructure-level issues (TDE, storage, network, container) are found by Steps 3–11

**Root causes:**
- SQL process restart requiring database redo/undo recovery
- Failover causing replicas to replay transaction log
- Large transaction rollback after unexpected termination
- Node restart requiring all hosted databases to recover

**Detection** (via `StorageEngine/database-recovery` skill):
- Invoke the `StorageEngine/database-recovery` skill
- The skill returns recovery completion status, duration, and progress timeline
- Correlate recovery timeline with the QL905 unhealthy window

**Correlation rules:**
- Recovery is the root cause only if the recovery timeline overlaps the QL905 unhealthy window
- If recovery rows exist but a higher-priority root cause was also found (e.g., TDE, storage), treat recovery as a consequence of the original issue, not the root cause
- Recovery reaching 100% near the time the application returns to healthy confirms the diagnosis

**Impact**: Database is unavailable or read-only during recovery. Duration depends on the amount of transaction log to replay.

**Expected behavior**: Recovery is a normal part of SQL Server's crash recovery mechanism. The unhealthy state is expected to self-resolve once recovery completes.

**Escalation**: Transfer to **SQL Managed Instance: Availability queue** for all recovery scenarios.

## Investigation Principles

### 1. State Verification First

- Always start by confirming unhealthy state is ongoing (not transient)
- Use health state timeline to identify pattern
- Distinguish: single spike vs. persistent unhealthy state

### 2. Exclusions Before Deep Dive

- Check for expected administrative operations (SLO update, maintenance)
- Verify no related incidents on other queues
- Identify if multiple resources affected (points to platform issue)

### 3. Error Message Prioritization

- 🚩 TDE/AKV errors → highest priority (blocks all SQL operations)
- CodePackage launch failures → application cannot run
- Storage quota → prevents growth, operations blocked
- Remote storage → replica building blocked
- Database operations → long-running, may self-resolve

### 4. Escalation Routing

Route based on specific error/root cause, not generic "unhealthy" classification:
- **TDE**: TDE support team
- **Storage**: Performance/Reliability team
- **Connectivity**: Networking team
- **CodePackage**: Performance/Telemetry team based on component
- **Database Operations**: Appropriate CRUD/GeoDR/Backup team

## Service Fabric Explorer Checks

When investigating, use **ServiceFabricExplorer (SFE)** for the relevant cluster:

**URL pattern**: `https://{clustername}:19080/Explorer`

**What to check:**
1. **Applications**: Find `fabric:/Worker.CL/{app-id}` application
2. **Replicas**: Check replica states (Ready, InBuild, InBuildSecondary, Dropped)
3. **Health Events**: View recent health reports and warnings
4. **Partition Status**: Verify partition is in quorum
5. **Recent Activity**: Check for failovers, replica drops, transitions

**Unhealthy indicators in SFE:**
- Primary replica not ready
- All secondaries InBuild (cannot build)
- Secondary replica count < quorum
- Deployment/uptime history showing continuous restarts

## Related Documentation

### Internal Documentation (eng.ms / ADO Wiki)

- [TSGCLAVAIL0004 - Unhealthy Worker.CL Application](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-MI-Availability)
- Azure SQL Managed Instance HA Architecture documentation
- Service Fabric concepts and troubleshooting

### Azure SQL Documentation

- [Azure SQL Managed Instance - High Availability](https://learn.microsoft.com/en-us/azure/azure-sql/managed-instance/high-availability-sla)
- [Service Fabric Health Model](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-health-introduction)
- [Service Fabric Explorer](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-visualizing-your-cluster)

### Support Escalation Teams

- **Azure SQL DB / SQL Managed Instance: TDE** — Transparent Data Encryption and Key Vault issues
- **Mi Perf - Azure SQL DB / SQL Managed Instance: SQL Engine Performance and Reliability** — Storage, CodePackage, SQL engine issues  
- **Azure SQL DB / SQL Managed Instance: Database CRUD** — Create, Read, Update, Delete database operations
- **Azure SQL DB / SQL Managed Instance: GeoDR** — Geo-replication and database copy issues
- **Azure SQL DB / SQL Managed Instance: Backup and Restore** — Backup, restore, and recovery operations
- **Azure SQL DB / Telemetry, Monitoring, Runners** — Monitoring service and runner issues
- **Azure SQL Managed Instance Connectivity and Networking** — Connection issues, network paths, NSG/firewall
