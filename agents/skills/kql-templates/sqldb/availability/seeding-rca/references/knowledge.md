# Seeding RCA Knowledge Reference

## Seeding Failure Codes (from MonDbSeedTraces)

| Code | Message | Root Cause? |
|---|---|---|
| 14 | Remote side failure | No — cascade from remote side. Check the paired Destination. |
| 15 | VDI Client failed | Partial — VDI channel broke. Check engine errors for the real cause. |
| 16 | VDI Outcome failed | Partial — VDI outcome check failed. Often paired with certificate (33111). |
| 17 | Timed out | Yes — seeding exceeded timeout. Check DB size and transfer rate. |
| 3601 | IExecSql Failed | Partial — BACKUP/RESTORE T-SQL failed. Check engine errors. |
| 1008/1009/1010 | Cancel variants | No — cleanup codes. Look for the paired failure. |
| 1019/1022 | VD_E_ABORT | No — abort cleanup. Look for what triggered the abort. |

## Key Engine Errors (from MonSQLSystemHealth)

| Error | Category | Description | Persistent? |
|---|---|---|---|
| 3257 | Disk Space | S:\\ drive full — RESTORE can't allocate files | Yes — until space freed |
| 33111 | Certificate | AG endpoint cert not found — transport can't connect | Yes — until cert fixed |
| 41620 | Fabric | Build cancelled by Fabric reconfiguration | No — transient |
| 3271/3202/3203 | VDI I/O | OS error 995 — VDI teardown symptom, NOT root cause | N/A |
| 18210 | Backup | Backup device failure — secondary to VDI teardown | N/A |
| 3013 | RESTORE | RESTORE terminating abnormally — result of the failure | N/A |
| 701 | Memory | Out of memory in resource pool | Varies |
| 926 | SUSPECT | 🚩 Database marked SUSPECT — escalate | Yes |
| 3313/3414 | Recovery | Redo/recovery error — possible data corruption | Yes |
| 9001 | Log | Transaction log unavailable | Varies |

## Known Patterns (from seeding-monitor analysis, Feb-Mar 2026)

### Disk Space Exhaustion (~55% of failures)
- Engine: 3257 → 3119 → 3013 → VDI teardown (3271, 3202, 18210)
- Origin: Destination
- Seed codes: Dest=[15], Source=[14]
- Persistent until S:\\ space is freed

### Fabric Cancellation (~33% of Premium failures)
- Engine: 41620 → VDI teardown (3271, 18210, 3200)
- Origin: Fabric (not SQL engine)
- Seed codes: Source=[15], Dest=[14]
- Causal chain: secondary faults → Fabric cancels build → VDI tears down → OS 995 cascade
- Transient — self-heals in ~35 seconds

### Certificate Missing (~44% of Standard failures)
- Engine: 33111 → 3013 → 41621:OPEN_EXISTING_DB_DOES_NOT_EXIST
- Origin: Both sides see the cert error
- Seed codes: Dest=[16], Source=[14]
- Persistent until certificate is fixed

## Causal Ordering Rule

**DO NOT assume I/O errors (3271, 3202, 3203, OS 995) are the root cause.** They are 3rd-order symptoms of VDI teardown. Always check:
1. Was there a `Build replica cancelled` message BEFORE the I/O errors? → Fabric cancelled first.
2. Was there a disk space (3257) or cert (33111) error BEFORE the I/O errors? → That's the root cause.
3. Did the secondary `is_primary=false` fail BEFORE the primary? → Root cause is on the secondary.

## Geo vs Local Seeding Detection

**Important:** A GeoDR-enabled database can have BOTH local and geo seeding failures. Phase 2 detects the topology (does this DB have geo?). Phase 3 determines which type of seeding actually failed.

### Phase 2: Topology Detection (does geo exist?)

| Method | Table | Logic |
|---|---|---|
| **Primary** | `MonDmContinuousCopyStatus` | Rows with `link_type = 'LAG_REPLICA_LINK_TYPE_CONTINUOUS_COPY'` exist → DB has geo. No rows → local-only. |
| **Fallback** | `MonDmDbHadrReplicaStates` | `internal_state_desc` contains `GLOBAL_PRIMARY` or `FORWARDER` → DB has geo. Only `PRIMARY` → local-only. |

### Phase 3: Determine if THIS failure is local or geo

| Signal | How | Result |
|---|---|---|
| **`role_desc`** | Check MonDbSeedTraces | Contains `Forwarder` / `ForwarderDestination` → **geo seeding failure** |
| **Cluster comparison** | Compare Source vs Dest `ClusterName` | Same → **local**. Different → **geo**. |
| **AppName comparison** | Compare Source vs Dest `AppName` | Same AppName = local (same Fabric app). Different = likely geo. |
| **One side missing** | Only Source or Dest visible, no pair | If DB has GeoDR and missing side would be on partner cluster → likely geo. Query partner cluster. |

**Geo seeding has additional failure modes:**
- Cross-region network latency → timeouts (code 17)
- Partner cluster disk space exhaustion
- Certificate mismatch between clusters (33111)
- Forwarder operation failures (`DbForwarderOperation`)
- Data only visible on one Kusto cluster — may need to query both Source and Destination clusters separately

## Architecture Reference

See `.github/skills/Availability/seeding-monitor/references/knowledge.md` for:
- Seeding architecture components (FabricReplicaBuildController, DbSeedingOperation, VDI)
- Build Replica FSM states and triggers
- VDI data flow (Primary → hadrTransport → Secondary)
- MonFabricApi event descriptions

See `.github/skills/Availability/seeding-monitor/references/prep/Automatic Seeding - SQL Server and SQL DB.pptx` for the original presentation.

---

## Automatic Seeding Architecture (Presentation Summary)

> Summarized from: `seeding-monitor/references/prep/Automatic Seeding - SQL Server and SQL DB.pptx`
> Authors: Jingyang Sui, Dong Cao

### What Is Automatic Seeding?

In SQL Server 2012/2014, the only way to initialize a secondary replica was backup-copy-restore. SQL Server 2016 introduced **automatic seeding**, which uses the log stream transport to stream the backup via VDI to the secondary replica for each database in the availability group, using the configured endpoints.

In Azure SQL DB, seeding streams the database backup using VDI to the secondary replica. Basic usage scenarios:

- Build local secondary replica
- Build geo forwarder
- UpdateSLO (scale operation triggers rebuild)

### Component Hierarchy

```
FabricReplicatorProxy
  └─ FabricReplicaController
       └─ FabricReplicaBuildController        ← main seeding manager
            └─ DbSeedingOperation
                 └─ VDI (Virtual Device Interface)

FabricReplicaManager                          ← manages replica lifecycle
AsyncOpAdmin                                  ← async operation scheduling
```

For geo/forwarder seeding, additional components:

```
LayeredAgReplicaController
  └─ ForwarderFabricReplicaBuildController    ← geo-specific build controller
       └─ DbForwarderOperation               ← coordinates between geo primary and all geo secondaries
```

### Component Responsibilities

#### FabricReplicaBuildController
- **Main component managing seeding** — most build replica methods live here
- Manages concurrent build replica operations
- Manages physical seeding operations
- Responsibilities:
  - Initiate build replica operations it receives
  - Track build operations and manage build replica FSM
  - Provide build cancellation API
  - Notify Service Fabric on operation completion
- `ForwarderFabricReplicaBuildController` is a special flavor for geo forwarder builds

#### DbSeedingOperation
- Created by `FabricReplicaBuildController`
- Serves as a **bridge between VDI/backup/restore and the network**
- Updates DMV and maintains state
- Handles failures from disk and network
- Three sub-types:
  - **DbBackupOperation** — seeding source side
  - **DbRestoreOperation** — seeding target side
  - **DbForwarderOperation** — forwarder coordinating between geo primary and all geo secondary replicas

#### VDI (Virtual Device Interface)
- Allows backup/restore data from/to SQL Server like a file interface
- **No additional disk is required for backup** — streams directly over the network
- Driven by the database seeding operation

### Control Flow — Local Seeding

```
Primary Replica                              Secondary Replica
┌──────────────────────────┐                ┌──────────────────────────┐
│ ServiceFabric            │                │                          │
│   ↓                      │   Control msg  │                          │
│ FabricReplicatorProxy    │ ──────────────→│ FabricReplicaManager     │
│   ↓                      │                │   ↓                      │
│ FabricReplicaController  │                │ FabricReplicaController  │
│   ↓                      │                │   ↓                      │
│ FabricReplicaBuildCtrl   │                │ FabricReplicaBuildCtrl   │
│   ↓                      │                │   ↓                      │
│ DbBackupOperation        │  Data transfer │ DbRestoreOperation       │
│   ↓                      │ ──────────────→│   ↓                      │
│ BackupVDI                │  hadrTransport │ RestoreVDI               │
└──────────────────────────┘                └──────────────────────────┘
```

### Control Flow — Geo Seeding

```
Geo Primary's                    Geo                          Geo Secondary's
Primary Replica                  Forwarder                    Local Secondary
┌─────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│ FabricReplicaBuild   │   │ ForwarderFabricReplica│  │ FabricReplicaBuild   │
│   Controller         │   │   BuildController     │  │   Controller         │
│   ↓                  │   │   ↓                   │  │   ↓                  │
│ LayeredAgFabric      │   │ LayeredAgFabric        │  │                      │
│   ReplicaController  │   │   ReplicaController    │  │ FabricReplicaManager │
│   ↓                  │   │   ↓                   │  │   ↓                  │
│ DbBackupOperation    │──→│ DbForwarderOperation  │──→│ DbRestoreOperation   │
│   ↓                  │   │                       │  │   ↓                  │
│ BackupVDI            │   │ RestoreVDI             │  │ RestoreVDI           │
│   ↓                  │   │   ↓                   │  │   ↓                  │
│ hadrTransport  ──────│──→│ hadrTransport ────────│──→│ hadrTransport        │
└─────────────────────┘   └──────────────────────┘   └──────────────────────┘
```

Key difference: Global primary VDI **concurrently seeds all geo secondaries** (in SQL DB). In SQL Server, global primary only seeds the forwarder, and the forwarder seeds its local secondaries after its own seeding completes.

### BuildReplica FSM (Finite State Machine)

#### States (in order)

| State | Description |
|---|---|
| `INITIAL` | Operation created |
| `PENDING` | Submitted to AsyncOpAdmin, waiting to become active |
| `CHECK_IF_SEEDING_AND_CATCHUP_NEEDED` | Source asks target if seeding is needed; target checks locally and responds |
| `SENDING_FILE_LIST` | Source sends file list to target; target receives file list |
| `SEEDING` | VDI backup/restore streaming in progress |
| `REPLICA_CATCHUP` | Seeding complete, replica catching up with log |
| `COMPLETED` | Build fully complete |
| `FAILED` | Build failed (can occur from any state) |

#### Walkthrough (Source and Target in Parallel)

**Source (Primary):**
1. `INITIAL` → `PENDING` — submit operation to AsyncOpAdmin
2. `PENDING` → `CHECK_IF_SEEDING_AND_CATCHUP_NEEDED` — become active
3. `CHECK_IF_SEEDING_AND_CATCHUP_NEEDED` → `SENDING_FILE_LIST` — target confirms seeding needed
4. `SENDING_FILE_LIST` → `SEEDING` — send file list to target
5. `SEEDING` → `REPLICA_CATCHUP` — seeding complete
6. `REPLICA_CATCHUP` → `COMPLETED` — catch up complete

**Target (Secondary):**
1. `INITIAL` → `PENDING` — submit operation to AsyncOpAdmin
2. `PENDING` → `CHECK_IF_SEEDING_AND_CATCHUP_NEEDED` — become active
3. `CHECK_IF_SEEDING_AND_CATCHUP_NEEDED` → `SENDING_FILE_LIST` — check locally and respond "seeding needed" to source
4. `SENDING_FILE_LIST` → `SEEDING` — receive file list
5. `SEEDING` → `REPLICA_CATCHUP` — seeding complete
6. `REPLICA_CATCHUP` → `COMPLETED` — catch up complete

### VDI Data Flow Detail

```
Primary Replica                                    Secondary Replica
┌─────────────────────────────┐                   ┌─────────────────────────────┐
│ BACKUP DATABASE x           │                   │ RESTORE DATABASE x          │
│   TO VIRTUAL_DEVICE=guid    │                   │   FROM VIRTUAL_DEVICE=guid  │
│         ↓                   │                   │         ↓                   │
│ VdiServer (shared memory    │                   │ VdiServer (shared memory    │
│   + named events)           │                   │   + named events)           │
│         ↓                   │                   │         ↑                   │
│ VdiClient                   │                   │ VdiClient                   │
│   ├─ SqlTask (backup cmds)  │                   │   ├─ SqlTask (restore cmds) │
│   ├─ VdiTask (pull read     │   Send data       │   ├─ VdiTask (pull write    │
│   │   cmds from vdiClient)  │ ────────────────→ │   │   cmds from vdiClient)  │
│   └─ UcsTask                │   hadrTransport   │   └─ UcsTask                │
│       (enqueue read cmds,   │                   │       (enqueue write cmds,  │
│        pack msg)            │                   │        unpack msg)          │
│         ↓                   │                   │         ↑                   │
│ Buffers                     │                   │ Buffers                     │
└─────────────────────────────┘                   └─────────────────────────────┘
```

- `VdiServer` uses shared memory and named events for IPC
- `VdiClient` has three tasks: SqlTask (T-SQL), VdiTask (device I/O), UcsTask (network)
- Primary: read commands enqueued → packed → sent via hadrTransport
- Secondary: received → unpacked → write commands enqueued → restore

### SQL Server — Trigger Conditions

A database auto-seeding is triggered when:

1. A database is joined to the primary replica of an AG
2. A secondary replica is added to an AG which has joined databases
3. A Forwarder replica in DAG completes auto seeding for a database
4. A secondary replica reconnects with primary
5. Host machine or SQL Server service is restarted
6. Temporary disconnection from primary
7. AG Failover
8. Seeding mode configuration changed to AUTO
9. Customer executes: `ALTER AVAILABILITY GROUP [agname] GRANT CREATE ANY DATABASE`

In **SQL DB**, seeding is triggered through Service Fabric interface API: `CFabricReplicatorProxy::BeginBuildReplica`. Geo seeding is triggered by the GeoDR workflow at geo primary replica ChangeRole.
