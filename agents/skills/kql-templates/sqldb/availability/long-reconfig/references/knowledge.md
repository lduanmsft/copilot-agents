# Terms and Concepts

!!!AI Generated. To be verified!!!

## Core Concepts

### Reconfiguration

Reconfiguration is the process by which Service Fabric changes the replica set configuration for a partition. This can include changing the primary replica, adding or removing secondary replicas, or changing replica roles. Reconfiguration is a normal part of the Azure SQL Database and Managed Instance lifecycle but should complete within expected timeframes.

### Long Reconfiguration (LongReconfigDatabase)

A long reconfiguration occurs when a database partition reconfiguration takes longer than expected. This is detected by Service Fabric health monitoring and triggers an `AlrWinFabHealthPartitionEvent` alert with the description "Partition reconfiguration is taking longer than expected."

**Impact:**
- Customer-facing unavailability during the reconfiguration period
- Database remains in "Reconfiguring" state in SFE
- Writes and reads may be blocked depending on the reconfiguration phase

### Partition States

| State | Description | Customer Impact |
|-------|-------------|-----------------|
| **Ready** | Partition is healthy and serving requests | None |
| **Reconfiguring** | Partition is changing its replica configuration | Potential unavailability |
| **QuorumLoss** | Partition has lost a majority of replicas | Full unavailability |

## Known Causes of Long Reconfiguration

### Case 1: Error 41614 State 27 - ERR_STATE_HADR_DB_MGR_DOES_NOT_EXIST

- **Observed on:** GP (General Purpose) instances only
- **Symptom:** Quorum catchup constantly failing with error code 41614, state 27
- **Root Cause:** The HADR Database Manager does not exist for the target database during reconfiguration
- **Mitigation:** Kill old primary; if unresolved, kill new primary too (safe because database is still being created)

### Case 2: Inconsistent Remote Replicas

- **Symptom:** Error 5120, Severity 16, State 5 in MonSQLSystemHealth
- **Root Cause:** Remote replica metadata is inconsistent between replicas
- **Mitigation:** Follow TSGCL0069.2 (backup restore team) or TSGCL0069.1 (surface area team)

### Case 3: Error 5173 - DSK_DB_FILE_MISMATCH

- **Symptom:** Error 5173, Severity 16, State 1 - file metadata discrepancy between GeoSecondary and GeoPrimary
- **Error Message:** "One or more files do not match the primary file of the database..."
- **Mitigation:** Reseed GeoSecondary (SOPCL00104.3), then mitigate inconsistent remote replicas (TSGCL0069.1)

### Case 4: Long Running Checkpoint

- **Symptom:** Checkpoint start event in MonFabricDebug without corresponding checkpoint finish event
- **Key Traces:** `HaDrDbMgr::CheckpointDBInternal: Starting checkpoint` and `HaDrDbMgr::CheckpointDBInternal: Finished checkpoint`
- **Mitigation:** Take a dump for investigation, then kill primary SQL process

### Case 5: Instance Boot Deadlock

- **Symptom:** `HaDrDbMgr::DelayKillingSessionsHoldingReplMasterLocks - Waiting` message in MonSQLSystemHealth
- **Root Cause:** Deadlock during instance boot process where sessions holding replication master locks cannot be released
- **Mitigation:** Kill the stuck SQL process

### Case 6: Unknown Issue

- **Symptom:** None of the above cases match
- **Investigation:** Check MonSQLSystemHealth for errors during the issue window
- **Mitigation:** Take a dump, try killing SQL process, escalate if unresolved

### Case 7: XEvent Dispatcher Deadlock

- **Symptom:** Message "XE Engine dispatcher pool for sessions that has long running targets" in MonSQLSystemHealth
- **Root Cause:** The XEvent engine dispatcher pool gets stuck with long running targets, blocking SQL process operations
- **Mitigation:** Kill the SQL process on the affected node

### Case 8: Stuck Backup on Secondary Blocking Primary

- **Symptom:** `BACKUP LOG started` on a secondary without corresponding `BACKUP LOG finished`, followed by HADR transport timeouts on the primary
- **Root Cause:** A backup-on-secondary operation gets stuck (e.g., XStore/blob write hangs). The primary's `SendBackupCmdMsgAndWaitForResponse` blocks synchronously waiting for the backup result. This freezes the primary's HaDrDbMgr thread, making the primary unresponsive to all secondaries. All secondaries then lose sync and the partition enters long reconfiguration.
- **Key evidence:**
  - On secondary: `BACKUP LOG started` for msdb/managed_model without `BACKUP LOG finished`
  - On primary: Last log is `ProcessBackupCmdResultMsg` for one database, then silence
  - MonDmDbHadrReplicaStates: All secondaries go `NOT SYNCHRONIZING` simultaneously (primary-side issue)
  - MonUcsConnections: Error 10060 (TCP timeout) between nodes
  - HADR Transport: `Timeout Detected 90 s` on all sessions
- **Critical code path:** `SendBackupCmdMsgAndWaitForResponse` → `HadrMessageConversation::WaitForResponse` → `WaitForEvent(timeout, m_event)` — synchronous SOS_EventManual wait that blocks the thread
- **Mitigation:** Kill the primary SQL process (breaks the blocked wait, forces fresh reconfiguration with clean HADR state)

### Case 10: msdb Upgrade Script Stuck on Metadata Lock (DBCC UPDATEUSAGE)

- **Symptom:** msdb partition stuck in LongReconfig. Error log shows `"Database 'msdb' is upgrading script 'Sql.Msdb.Sql'"` without subsequent `"PerformConfigureDatabaseInternal completed"`. Commonly reported as "Unknown" root cause in the ICM title.
- **Root Cause:** When msdb transitions to PRIMARY role, the `TransitionToPrimary` code path runs `PerformConfigureDatabaseInternal` which executes the msdb upgrade script (`Sql.Msdb.Sql`). This script runs `DBCC UPDATEUSAGE` which requires metadata locks on msdb objects. If another session holds a conflicting lock on msdb (e.g., a customer query, agent job, or internal operation), `DBCC UPDATEUSAGE` blocks indefinitely — there is no lock timeout. This blocks the entire role transition, preventing msdb from becoming PRIMARY.
- **Key evidence:**
  - Error log: `"Database 'msdb' is upgrading script 'Sql.Msdb.Sql' from level X to level Y"` — present
  - Error log: `"PerformConfigureDatabaseInternal completed running of script Sql.Msdb.Sql"` — **MISSING**
  - Error log: `"Checking the size of MSDB..."` — present, but `"Setting database option TRUSTWORTHY to ON for database 'msdb'."` — **MISSING** (on the same thread/process)
  - Dump: Thread stuck in `AsyncChangeRole` → `TransitionToPrimary` → `ConfigureDatabase` → `PerformConfigureDatabaseInternal` → `DBCC UpdateUsage` → `MDL::LockObject` → `lck_lockInternal` → `LockOwner::Sleep`
  - MonDmDbHadrReplicaStates: All secondaries show `IDLE_SECONDARY` / `NOT SYNCHRONIZING` with frozen LSNs
  - Killing secondaries does NOT help — only killing the primary resolves the issue
- **Diagnostic query:** See **LR305** in [queries.md](queries.md).
  If `originalEventTimestamp1` is NULL → upgrade never completed (stuck).
  If `duration` is more than a few seconds → upgrade was slow (at risk).
- **Mitigation:** Kill the primary SQL process. The new primary will re-run the upgrade script, which typically completes in seconds when there is no lock contention.
- **Known issue:** PBI 4448193 — "MSDB upgrade script can last for 10s of minutes" (Priority 2, State: New, Area: SQL MI HADR). Related ICMs: 643700277, 722148311, 766401575.
- **Why msdb is disproportionately affected:** msdb is a system database used by SQL Agent, Service Broker, backup history, and other internal operations. These operations hold metadata locks on msdb objects. When a failover occurs, the upgrade script runs `DBCC UPDATEUSAGE` which conflicts with these locks. Other databases (user DBs, replicatedmaster, managed_model) don't run `DBCC UPDATEUSAGE` during their upgrade scripts, so they are not affected.

- **Symptom:** Error 9003 ("The log scan number is not valid — may indicate data corruption"), Error 926 ("Database marked SUSPECT"), Error 3414 ("Recovery failed")
- **Root Cause:** Log file corruption or mismatch between .ldf and .mdf on a forwarder database. The database cannot complete recovery and is marked SUSPECT. The partition reports `DB_SUSPECT_CALLBACK` to Service Fabric, keeping the partition in reconfiguring state.
- **Key evidence:**
  - Error 9003 with Severity 20 — log scan number invalid
  - Error 926 — database marked SUSPECT
  - Error 3414 — recovery prevented database from restarting
  - Error 41621 with `DB_SUSPECT_CALLBACK`
  - LR340 (recovery time) returns empty — recovery never completed
  - MonDmDbHadrReplicaStates shows frozen LSNs with `last_received_lsn = 1` (no log arriving)
  - Database may report SYNCHRONIZED/HEALTHY despite being effectively dead
- **Mitigation:**
  1. Check LR355 (MonManagementOperations) for any reseed operations already in progress
  2. Initiate a **reseed** of the forwarder database from the geo-primary — this rebuilds the database and fixes log corruption
  3. If reseed times out, **escalate to the PG (product group) to investigate the timeout root cause** before retrying — blind retries may fail again
  4. Track reseed progress using LR356 (MonDbSeedTraces) — verify seeding percentage is advancing
  5. 🚩 Restarting the replica alone does NOT fix log corruption
  5. 🚩 Killing the SQL process alone does NOT fix it either — the corruption persists across restarts

## Related Documentation

- [TSGCL0212 - LongReconfigDatabase](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-managed-instance/sql-mi-availability/tsg-sql-mi-availability/index/availability/tsgcl0212-longreconfigdatabase)
- [Azure SQL Managed Instance High Availability](https://learn.microsoft.com/en-us/azure/azure-sql/managed-instance/high-availability-sla-local-zone-redundancy?view=azuresql)
- [Service Fabric Reconfiguration](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-concepts-reconfiguration)
