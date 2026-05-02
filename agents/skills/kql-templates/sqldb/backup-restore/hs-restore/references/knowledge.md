# Knowledge Base: Hyperscale (VLDB) Restore Investigation

This file documents domain knowledge for diagnosing Hyperscale restore failures, stuck restores, and slow restores. Contains architecture, exception patterns, known issues, and reference tables. For debug methodology and interpretation rules, see [principles.md](principles.md).

---

## 1. Hyperscale Restore Architecture

### The 4-Phase Model

Every Hyperscale (VLDB) restore proceeds through 4 sequential phases:

| Phase | Name | What Happens | Key Tables |
|-------|------|-------------|------------ |
| **1** | Destage Wait + Plan Creation | Orchestrator waits for source DB XLog to destage required log data, then creates a restore plan selecting snapshot per page server | MonManagement, MonXlogSrv |
| **2** | App Creation | Target database's Service Fabric apps (Compute, Page Servers, XLog) are provisioned on the tenant ring | MonManagement, MonFabricClient, WinFabLogs |
| **3** | Data Copy | Page server snapshot blobs are copied from source to target storage containers | MonBlobClient, MonSQLXStore |
| **4** | Redo | Transaction log is replayed on target page servers to bring data to the requested point-in-time | MonSocrates, MonRecoveryTrace, MonSQLSystemHealth |

### Phase Completion Milestones (from QHR20)

| Phase | Completion Message |
|-------|--------------------|
| 1 | `"Restore plan was created successfully in {N} seconds."` |
| 2 | `"Restore target db's apps were created. Beginning to start copy of snapshot and destaged blobs."` |
| 3 | `"Copy of {N} page server snapshot and XLog files finished successfully."` |
| 4 | `"The database has been restored successfully."` |

### Orchestrator State Sequence (from QHR100)

Expected ~15-17 state transitions in `VldbRestoreRequestStateMachine`:

`RestoreStart` → `PerformingSafetyChecks` → `WaitingForDestaging` → `CreatingRestorePlan` → `CreateRestorePlanReady` → `CopyingPageServerFiles` → `CopyXLogFiles` → `WaitingForBlobCopyBatchToComplete` → `DropBlobCopyMachines` → `ValidateXStoreCopyRequests` → `FixupMetadataOfTargetBlobs` → `RestoreDatabase` → `ValidateXLogSnipBsn` → `RestoringDatabase` → `ReplicationFixup` → `CleanupBeforeTerminal` → `Ready`

---

## 2. Exception Pattern Reference

### Common Exception Types (QHR40A)

| Exception Type | Phase | Meaning |
|----------------|-------|---------|
| `TimeoutException` | All | Repeated timeouts — fabric calls, blob copy, recovery |
| `FiniteStateMachineDeadlockVictimException` | All | FSM lock contention — usually transient, retry |
| `AggregateException` | All | Wrapper — unwrap to find root cause |
| `COMException` | All | Underlying infrastructure issue |

### Phase-Specific Exception Patterns (QHR40B)

**App Creation (Branch A):**
- `FabricApplicationStateMachine.TransitionCreatingToReady` → Fabric app creation timeout
- `IFabricApplicationManagementClient10.EndCreateApplication` → Native fabric API call failing
- `FiniteStateMachineBaseSqlContext.LoadInternal` → Deadlock in FSM lock acquisition
- HRESULT codes (e.g., `0x80071BFF`) → Specific fabric/storage errors

**Data Copy (Branch B):**
- Blob copy failures, storage timeout exceptions, cross-account copy errors
- `ServerBusy` / `ThrottlingException` → Azure Storage throttling
- `BlobNotFound` / `ContainerNotFound` → Source blob missing or aged out
- `ConditionNotMet` / HTTP 412 → Blob modified between snapshot and copy
- `CopyFailed` → Azure async blob copy failed

**Redo (Branch C):**
- Recovery exceptions, page redo failures, BSN validation errors
- RBPEX allocation failures → Fallback to remote storage reads
- XLog delivery stalls → BSN gaps

### PII Exception Lookup

If `message` references `PiiManagementExceptions with error identifier '{GUID}'`:
- The full exception text was PII-scrubbed
- Use the GUID to look up in `PiiManagementExceptions` table

---

## 3. Known Issues & ICM References

### Stuck Replica Creation (ICM 728004373, ICM 738740724)

**Pattern**: Page Server app replicas stuck in "resolving" state, never reaching target replica count. Management Service perceives apps as still creating, blocking restore indefinitely.

**Signal**: QHR60 returns results with `WaitingTimeForReplica > 30m`.

**ICM 728004373** (ProdEus2a, Dec 2025): Restore running 2 days. Mitigated by restarting processes to unblock stuck Page Server creation.

**ICM 738740724** (ProdWeu1a, Jan 2026): PITR restore stuck at 61%. Mitigated by restarting PS apps perceived as resolving by Management Service.

**Mitigation**: Restart stuck app processes. Escalate to Socrates Data Plane / Backup Restore Hyperscale team.

### FSM Throttling (Observed in ProdWeu1a)

**Pattern**: FSM work items deprioritized (priority > 1) for extended periods during App Creation.

**Signal**: QHR50 returns results with priority != 1 and duration > 30 min.

**Context**: Cluster-wide condition when management service is under heavy load. Not restore-specific.

### Target Database Dropped During Restore

**Pattern**: User or automated process drops the target logical database while restore is in progress, causing obscure failure.

**Signal**: QHR15 returns results with `DropLogicalDatabase` or `DeleteDatabase` events during the restore window.

**Root Cause**: Concurrent operation conflict. Restore must be retried after ensuring no concurrent deletions.

---

## 4. Key Tables Reference

| Table | Purpose |
|-------|---------|
| `MonManagementOperations` | Management operation lifecycle (start, complete, fail) |
| `MonManagement` | State machine transitions (FSM events) |
| `MonManagementFSMInternal` | FSM internal queue events (throttling, priority) |
| `MonBlobClient` | Azure Storage blob copy operations |
| `MonFabricClient` | Service Fabric client operations (replica creation) |
| `WinFabLogs` | Service Fabric placement traces |
| `MonAnalyticsDBSnapshot` | Database snapshot metadata (SLO, backup type) |
| `MonSocrates` | Socrates component traces (compute, PS, xlog) |
| `MonSQLSystemHealth` | SQL system health events, error logs |
| `MonRecoveryTrace` | Database recovery traces |
| `MonXlogSrv` | XLog server traces (destage progress) |
| `MonSQLXStore` | XStore file operations, blob sizes |

---

## 5. MCP Servers

| Server | Tool | Purpose |
|--------|------|---------|
| **SqlOps** | `mcp_sqlops_query_kusto` | Execute all 24 Kusto queries (CR and TR) against any prod/staging region |
| **ICM** | `mcp_icm-prod_get_incident_details_by_id` | Read incident details, custom fields, timestamps (Path A input resolution) |

> **Note**: XTS (`mcp_xts_view_info`, `mcp_xts_execute_view`) was used during the research/design phase to discover and validate queries. It is **not a runtime dependency** — all queries are standalone KQL executed via SqlOps.

---

## 6. Investigation Variables

Variables extracted from QHR10 and carried through all subsequent queries:

| Variable | Source | Used By |
|----------|--------|---------|
| `request_id` | Input resolution (QHR00A/B/C) | QHR10, QHR20, QHR30, QHR40, QHR50, QHR60, QHR70, QHR80, QHR90, QHR100, QHR130 |
| `restore_id` | QHR10 (`operation_parameters` XML) | QHR30, QHR110, QHR190 |
| `source_logical_database_id` | QHR10 (`operation_parameters` XML) | QHR30, QHR120, QHR190 |
| `target_logical_database_id` | QHR10 (`operation_result` XML, or FSM resolution for stuck) | QHR140, QHR150, QHR160, QHR170, QHR180, QHR190 |
| `source_logical_server_name` | QHR10 (`operation_parameters` XML) | Context / display |
| `target_logical_server_name` | QHR10 (`operation_parameters` XML) | Context / display |
| `target_slo` | QHR10 (`operation_parameters` XML) | SLO identification (HS_Gen5_2, etc.) |
| `point_in_time` | QHR10 (`operation_parameters` XML) | Requested restore point |
| `source_database_dropped_time` | QHR10 (`operation_parameters` XML) | If set → restoring a deleted/dropped database |
| `restore_start_time` | QHR10 (TIMESTAMP of start event) | Time-bounded TR queries |
| `restore_end_time` | QHR10 (TIMESTAMP of completion, or `now()` if stuck) | Time-bounded TR queries |
| `restorePlanGeneratedTime` | QHR30 | Phase 1 end, Phase 2 start |
| `restoreAppsCreatedTime` | QHR30 | Phase 2 end, Phase 3 start |
| `copyDoneTime` | QHR30 | Phase 3 end, Phase 4 start |
| `restoreFinishedTime` | QHR30 | Phase 4 end |

---

## 7. Hyperscale App Types

| App Type | Fabric Service | Role |
|----------|---------------|------|
| **Compute** | `Worker.Vldb.Compute` | SQL compute node — runs queries, recovery |
| **Storage** | `Worker.Vldb.Storage` | Page Server — stores data pages, performs redo |
| **XLog** | `Vldb.XLog` | Transaction log service — manages log delivery |
| **LandingZone** | Varies | Landing zone — log staging area |

### Page Server Disk Tiers

| Size Label | `instance_rg_size` | `blob_size` Range |
|------------|--------------------|----|
| 32 GB | (default) | Not explicitly marked |
| 128 GB | (standard) | `blob_size / (1024^3) <= 128` |
| 1 TB | `SQLDB_HSPS_2` | `blob_size / (1024^3) > 128` |
