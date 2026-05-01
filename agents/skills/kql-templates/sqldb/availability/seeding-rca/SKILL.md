---
name: seeding-rca
description: Root-cause a specific seeding failure for Azure SQL Database (Standard / Premium). Given a timestamp + cluster + server + database, or a time range (startTime/endTime) + cluster + server + database, or an IcM ID, walks through a structured investigation to determine why seeding failed, what engine errors occurred, and whether the issue is persistent or transient. Use when a specific database has seeding problems and you need to find the root cause. For fleet-wide overview and pattern discovery, use seeding-monitor instead.
---

# Seeding Failure Root Cause Analysis

!!!AI Generated. To be verified!!!

Investigate a specific seeding failure for a given database and determine root cause. This skill follows a 5-phase workflow: Identify → Context → Seeding Trace → Engine Correlation → Root Cause.

## Input

The user provides ONE of:

**Option A — Direct identifiers (all required):**
- `{Timestamp}` — approximate time of the failure (UTC), OR `{StartTime}` and `{EndTime}` — UTC time range bracketing the failure
- `{ClusterName}` — Service Fabric cluster (e.g., `tr69519.eastus1-a.worker.database.windows.net`)
- `{LogicalServerName}` — customer-facing server name
- `{LogicalDatabaseName}` — logical database name

If the user provides a single `{Timestamp}`, derive `{StartTime}` = `{Timestamp} - 2h` and `{EndTime}` = `{Timestamp} + 5h` for initial queries.

If the user does not know the cluster name, ask them to provide it. The cluster name is required to connect to the correct Kusto cluster and filter data accurately.

**Option B — IcM ID:**
- `{IcmId}` — IcM incident ID; extract cluster, server, database, and timestamp from the incident details

## Investigation Workflow

```
Phase 1: Identify the Target
  ↓
Phase 2: Get Database Context + Topology
         MonAnalyticsDBSnapshot → DB info (size, SLO, AppName)
         MonDmContinuousCopyStatus → Does this DB have GeoDR?
  ↓
Phase 3: Find Seeding Failures + Determine Local vs. Geo
         MonDbSeedTraces → failure codes, seeding GUIDs
         Correlate Source ↔ Destination → compare role_desc + ClusterName
         → Is THIS failure local seeding or geo seeding?
  ↓
Phase 3.6: Check Concurrent Operations
         MonManagementOperations → management ops during the seeding period
         MonNonPiiAudit → user/customer operations during the seeding period
         → Were there interfering operations?
  ↓
Phase 4: Correlate with Engine Telemetry
         MonSQLSystemHealth → engine errors
         MonFabricApi / MonFabricDebug → Fabric lifecycle
  ↓
Phase 5: Determine Root Cause
         Match to known pattern → provide conclusion
         If resource-related → check MonRgLoad / MonDmLogSpaceInfo
```

---

### Phase 1: Identify the Target

**Goal:** Get the 4 identifiers needed for all subsequent queries: Timestamp, ClusterName, LogicalServerName, DatabaseName/AppName.

**If user provides Option A (direct):** Proceed to Phase 2.

**If user provides Option B (IcM ID):**
1. Use the IcM MCP tools to get incident details (title, description, impacted resources)
2. Extract: cluster name, server name, database name, and incident creation time
3. If the IcM doesn't contain enough detail, ask the user for the missing identifiers
4. **Report the IcM context block immediately** (before any queries):

```
## Incident Context
| Field | Value |
|---|---|
| IcM ID | {IcmId} |
| Title | {IcM title} |
| Severity | {sev} |
| Time Range | {impactStartTime} — {mitigateTime or now} (UTC) |
| Region | {region from IcM} |
| Cluster | {ClusterName} |
| Logical Server | {LogicalServerName} |
| Logical Database | {LogicalDatabaseName} |
| Logical Database ID | {logical_database_id from RCA-100} |
| Physical Database ID | {physical_database_id from RCA-100} |
| Fabric Partition ID | {fabric_partition_id from RCA-100} |
| Seeding Start | {earliest seeding event from RCA-198/200} |
| Seeding End | {latest seeding event, or "ongoing" if still active} |
| State | {IcM state: ACTIVE / MITIGATED} |
| Impacted DBs | {count, if multiple DBs listed} |
```

**Note:** The Logical Database ID, Physical Database ID, Fabric Partition ID, and Seeding Start/End fields are populated after running RCA-100 (Phase 2) and RCA-198/200 (Phase 3). Include them in the output as soon as they are available — update the Incident Context block after each phase completes.

**Multi-DB / Multi-Server Incidents:** If the IcM title or description mentions seeding failures across **multiple databases or multiple servers** (e.g., "repeated seeding failures on 15 databases in ProdXxxTR1234"), do NOT attempt to investigate every database individually. Instead:
1. Note the total scope (number of DBs/servers mentioned) in the Incident Context.
2. **Pick 1–2 representative databases as samples** for the full detailed analysis (Phases 2–5). Prefer databases with the highest failure counts or the ones explicitly named in the IcM.
3. After completing the sample analysis, state the assumption: "Analyzed {N} of {Total} affected databases as samples. If the root cause differs across databases, further per-DB investigation may be needed."
4. If the user wants a specific database analyzed, they can specify it — otherwise use the sampling approach.

**Output:** Confirmed `{Timestamp}`, `{ClusterName}`, `{LogicalServerName}`, `{LogicalDatabaseName}`

**Note:** The cluster name determines which Kusto cluster to connect to for all subsequent queries. Without it, queries may return data from the wrong cluster or no data at all.

---

### Data Retention Check

**Goal:** Before running any queries, verify that the incident timestamp falls within the retention window of the key Kusto tables. If data has expired, notify the user immediately rather than running queries that return empty results.

**Run this check right after resolving the Kusto cluster URL:**

```kql
MonDbSeedTraces | summarize MinTime = min(TIMESTAMP);
MonAnalyticsDBSnapshot | summarize MinTime = min(TIMESTAMP);
MonFabricApi | summarize MinTime = min(TIMESTAMP);
MonSQLSystemHealth | summarize MinTime = min(TIMESTAMP)
```

> **Note:** Do NOT filter by `{AppName}` here — it has not been resolved yet (AppName is obtained from RCA-100 in Phase 2). These retention checks are table-level and do not require per-database filtering.

**Evaluate retention vs incident time:**

| Table | Typical Retention | If incident is older |
|---|---|---|
| MonDbSeedTraces | ~30 days | No seeding trace data — cannot determine seeding GUIDs, failure codes, or Source/Dest pairing |
| MonAnalyticsDBSnapshot | ~45 days | No DB metadata — cannot get AppName, physical_database_id, SLO, fabric_partition_id |
| MonFabricApi | ~30-50 days | No Fabric lifecycle — cannot see role changes, faults, build events |
| MonFabricDebug | ~28 days | No build FSM — cannot see state transitions |
| MonSQLSystemHealth | ~60-90 days | Longest retention — may be the only source for old incidents |

**Action based on retention:**

- **All key tables have data** → Proceed normally with full investigation
- **Some tables expired** → Report which tables are missing and adjust the investigation to use available tables only. Example:
  > "🚩 **Data retention warning:** This incident occurred on {date}. The following tables have no data for this time: MonDbSeedTraces (retention starts {date}), MonFabricApi (retention starts {date}). The investigation will rely on MonSQLSystemHealth only, which limits the analysis."
- **All tables expired (including MonSQLSystemHealth)** → Stop investigation and report:
  > "🚩 **Cannot investigate:** This incident occurred on {date}, which is outside the retention window of all available Kusto tables. No telemetry data remains for this incident. The IcM metadata and any attached comments are the only available information."

---

### Phase 2: Get Database Context and Topology

**Goal:** Understand what kind of database this is — size, SLO, tier — and whether it has geo-replication. Note: even if a database has GeoDR, the seeding failure could be local OR geo. Phase 2 captures the topology; Phase 3 determines which type actually failed.

**Query: RCA-100 — Database Snapshot**

Run on the production cluster identified in Phase 1. See `references/queries.md` RCA-100 for the full query.
Key parameters: `{Timestamp}`, `{ClusterName}`, `{LogicalServerName}`, `{LogicalDatabaseName}`

**What to capture:**
- `AppName` — needed for all subsequent queries
- `sql_instance_name` — the SQL Server instance name on the node (this is also the `AppName` used in MonDbSeedTraces)
- `state` — database state (e.g., ONLINE, RECOVERING, SUSPECT)
- `service_level_objective` — **critical: determines GP vs BC** (see below)
- `physical_database_id` — used in MonFabricDebug and MonDbSeedTraces (`database_name`)
- `logical_database_id` — the logical DB GUID
- `fabric_partition_id` — used in MonFabricApi queries
- `tenant_ring_name` — identifies the ring (e.g., prod, staging)
- `zone_resilient` — whether the database is zone-redundant
- `ClusterName` — confirm the cluster

**Determine GP vs BC from SLO:**

| SLO pattern | Tier | Seeding behavior |
|---|---|---|
| `SQLDB_GP_*`, `GP_*`, `ElasticPool_GP_*` | **General Purpose** | Remote storage (XStore). Seeding restores from XStore snapshot — no VDI data transfer between replicas. Failures are typically XStore I/O errors or snapshot issues. No local data files to exhaust disk space. |
| `SQLDB_BC_*`, `BC_*`, `SQLDB_BC_COPT_*`, `ElasticPool_BC_*` | **Business Critical** | Local SSD storage. Seeding streams data via VDI from Source replica to Destination replica over the network. Failures include VDI abort (OS 995), disk space exhaustion on S:\\, network timeout (code 17), memory/thread pressure (code 1007). |
| `SQLDB_HS_*`, `HS_*` | **Hyperscale** | Page server architecture. **STOP analysis.** This skill does not apply to Hyperscale. Transfer to Socrates Data Plane team. |

**🚩 If Hyperscale:** Stop the investigation immediately. Report:
> "This database is Hyperscale (SLO: {slo}). Hyperscale uses a page-server architecture with fundamentally different seeding mechanics. This seeding-rca skill does not apply. Please transfer to the **Socrates Data Plane** team for investigation."

**Why this matters:**
- **BC seeding** uses VDI streaming between replicas → susceptible to disk space, memory, network, and Fabric reconfiguration issues. Most seeding-rca queries (RCA-300 through RCA-410) are designed for this path.
- **GP seeding** restores from XStore → different failure modes. If the DB is GP, focus on XStore errors in MonSQLSystemHealth and check for storage account throttling rather than VDI/disk space issues.
- Report the tier prominently in the output.

**If no results:** The database may have been dropped, moved, or the cluster name is wrong. Ask user to verify.

**Query: RCA-110 — Geo-Replication Detection (MonDmContinuousCopyStatus)**

See `references/queries.md` RCA-110 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`

**Interpretation:**
- **Rows returned** → database has **geo-replication** (GeoDR)
  - `is_target_role = 0` → this server is the **Geo Primary**
  - `is_target_role = 1` → this server is the **Forwarder** (geo secondary local)
  - `partner_server` → the geo partner server name
  - `replication_state_desc = 'SEEDING'` → geo seeding is currently in progress
- **No rows** → database is **local-only** (no GeoDR)

**Fallback: RCA-120 — Replica State Check (MonDmDbHadrReplicaStates)**

See `references/queries.md` RCA-120 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`, `{LogicalDatabaseName}`

**Interpretation:**
- `internal_state_desc` contains `GLOBAL_PRIMARY` or `is_forwarder == 1` → database has **geo-replication**
- Only `PRIMARY` / `SECONDARY` with `is_forwarder == 0` → **local-only** (no geo)
- `is_seeding_in_progress == 1` → seeding was active at this timestamp
- `database_state_desc` → check for SUSPECT, RECOVERING, or other abnormal states
- `redo_queue_size` → large values indicate the replica is falling behind
- `synchronization_state_desc` → SYNCHRONIZED, SYNCHRONIZING, NOT SYNCHRONIZING

**Why this matters for seeding RCA:**
- A GeoDR-enabled database has **both local replicas and geo replicas**. The failure could be at either layer.
- Phase 2 tells you the **topology** (does geo exist?). Phase 3 tells you **which seeding actually failed** (local or geo).
- If the database has geo: expect `Forwarder` and `ForwarderDestination` roles in MonDbSeedTraces for geo seedings, and `Source` + `Destination` for local seedings — on the same database, at the same time.

---

### Phase 3: Find Seeding Failures and Determine Local vs. Geo

**Goal:** Get the seeding failure history, identify the specific seeding GUID(s) that failed, the failure codes, the Source↔Destination pairing, and **determine whether this specific failure is local or geo seeding**.

#### Step 3a: Determine if Seeding is Involved

Before diving into failure details, first check whether **any seeding activity** (success or failure) occurred on this instance during the incident window. This is critical for incidents that may not be directly seeding-related (e.g., OutOfRPO, SpoLoginFailed) but where seeding could be a contributing factor.

**Query: RCA-198 — Seeding Activity Check**

See `references/queries.md` RCA-198 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`

**Interpretation:**
- **TotalEvents > 0** → Seeding was active on this instance during the incident. Continue with Step 3b.
- **TotalEvents == 0 and the incident is a seeding IcM** → MonDbSeedTraces data may be outside retention (check `min(TIMESTAMP)` for the table). Fall back to MonSQLSystemHealth for seeding evidence (look for "Build replica", "BACKUP", "RESTORE", "streaming" messages).
- **TotalEvents == 0 and the incident is NOT a seeding IcM** (e.g., OutOfRPO, SpoLoginFailed) → Seeding may not be involved. Check MonSQLSystemHealth for indirect seeding evidence (flow control, build replica messages, VDI activity). If no seeding evidence found, report: "No seeding activity detected on this instance during the incident window. The root cause is likely unrelated to seeding."

#### Step 3b: Multi-DB Triage (if multiple databases on the same instance)

First, check how many databases have seeding failures on this instance. This reveals whether the problem is DB-specific or instance-wide.

**Query: RCA-199 — Multi-DB Failure Summary**

See `references/queries.md` RCA-199 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`

**Interpretation:**
- **All/most DBs failing with the same code** → instance-wide issue (resource pressure, node fault, reconfiguration)
- **Only one DB failing** → DB-specific issue (disk space for that DB, corruption, geo partner issue)
- **Mix of successes and failures** → contention or intermittent issue; investigate the failing DB(s)

**When multiple DBs have failures:**
1. Report the overall summary (how many DBs, which codes, success vs failure counts)
2. **Pick 1–2 representative failing DBs** for detailed per-DB analysis (prefer those with the most failures, or the ones matching the IcM title). Do not analyze every DB — sampling is sufficient unless the user requests otherwise.
3. Continue Phase 3 with each sampled DB's `physical_database_id`
4. If all sampled DBs share the same failure code/pattern, state the root cause applies broadly. If they differ, note the divergence and suggest investigating additional DBs.

#### Step 3b: Per-DB Seeding Failure History

**Query: RCA-200 — Seeding Failure History**

See `references/queries.md` RCA-200 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`, `{PhysicalDatabaseId}`

**What to look for:**
- `failure_code` — the seeding-level error (14=Remote side failure, 15=VDI Client failed, 3601=IExecSql, etc.)
- `role_desc` — Source or Destination? This tells you which side the failure trace came from
- `transferred_size_bytes` vs `database_size_bytes` — how far seeding got before failing (0 = failed at startup)
- `local_seeding_guid` / `remote_seeding_guid` — use to correlate Source ↔ Destination

**Query: RCA-210 — Correlate Source and Destination**

See `references/queries.md` RCA-210 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`, `{PhysicalDatabaseId}`

**Note:** RCA-200 filters by `database_name` (physical DB ID) to focus on the specific database. RCA-210's second part does NOT filter by database_name because the paired side (Destination) may have a different AppName and the GUID join already scopes it correctly.

**What to look for:**
- Are Source and Destination on the **same cluster**? (local seeding) or different clusters? (geo seeding)
- Which side reports the failure first? (check timestamps)
- Do failure codes match a known cascade pattern? (e.g., Source=14 + Dest=15 = VDI channel breakdown)

**Determining Local vs. Geo for this specific failure:**

| Signal | How to Check | Result |
|---|---|---|
| **`role_desc`** | Check RCA-200/210 results | Contains `Forwarder` or `ForwarderDestination` → **geo seeding** |
| **Cluster comparison** | Compare `ClusterName` of Source vs Destination in RCA-210 | Same cluster → **local seeding**; Different clusters → **geo seeding** |
| **AppName comparison** | Source AppName vs Destination AppName | Same AppName = local (Source and Dest live in same app); different = could be geo |

**Decision:**
- If `role_desc` contains `Forwarder` or `ForwarderDestination` → **confirmed geo seeding**
- Else if Source and Destination have the **same ClusterName** → **local seeding** (even if the DB has GeoDR, this particular failure is on the local HA replicas)
- Else if Source and Destination have **different ClusterNames** → **geo seeding**
- If only one side is visible (Source only or Destination only, no pair found) → Check if the database has GeoDR from Phase 2. If geo exists and the missing side would be on a different cluster, it's likely a geo seeding where the remote cluster's data isn't available on this Kusto cluster. Try querying the partner cluster.

**Implications for root cause:**
- **Local seeding failure:** Investigate disk space (3257), VDI issues (15), Fabric reconfiguration (41620), or certificate (33111) on the local cluster
- **Geo seeding failure:** Additionally consider: cross-region network latency/timeout (code 17), partner cluster disk space, Forwarder operation failures, geo endpoint connectivity

#### Step 3c: Report Source and Target Context

**Goal:** After completing Steps 3a/3b and RCA-210, compile a summary of both the Source and Target (Destination) sides and report them as a table. This provides a clear picture of the seeding topology and makes the investigation traceable.

Gather this information from Phase 2 (RCA-100, RCA-110) and Phase 3 (RCA-200, RCA-210) results. For the remote side, retrieve its context by querying `MonAnalyticsDBSnapshot` on the partner cluster (if accessible) or use the data already captured in RCA-210.

**Query: RCA-215 — Remote Side DB Context (if needed)**

See `references/queries.md` RCA-215 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{PartnerServerName}`, `{LogicalDatabaseName}`

**Output: Source and Target Context Table**

Always produce this table in the output after Phase 3:

```
## Source and Target Context
| Field | Source (Primary) | Target (Secondary / Destination) |
|---|---|---|
| Cluster (Tenant Ring) | {source cluster / ring} | {target cluster / ring} |
| Server Name | {source LogicalServerName} | {target LogicalServerName} |
| Database Name | {source LogicalDatabaseName} | {target LogicalDatabaseName} |
| Instance Name (AppName) | {source AppName} | {target AppName} |
| Logical Database ID | {source logical_database_id} | {target logical_database_id} |
| Physical Database ID | {source physical_database_id} | {target physical_database_id} |
| Fabric Partition ID | {source fabric_partition_id} | {target fabric_partition_id} |
| Is UpdateSLO | {Yes/No from Phase 3.5} | — |
| Seeding Role | Source / Forwarder | Destination / ForwarderDestination |
| Seeding Type | {Local / Geo DR} | {Local / Geo DR} |
```

**How to populate:**
- **Source side:** Use the `AppName`, `ClusterName`, and identifiers from RCA-200/210 rows where `role_desc` = `Source` or `Forwarder`
- **Target side:** Use the `AppName`, `ClusterName`, and identifiers from RCA-200/210 rows where `role_desc` = `Destination` or `ForwarderDestination`. If the target is on a different cluster, use RCA-215 to get its identifiers.
- **Is UpdateSLO:** Populated after Phase 3.5 — set to Yes if an UpdateSLO/ScaleDatabase operation was found, No otherwise
- **Seeding Type:** Local if same cluster, Geo DR if different clusters (determined in Step 3b)

---

### Calibrate Time Window for Phase 4+

**Goal:** Derive a precise `{FailStart}` / `{FailEnd}` window based on the failed seeding GUID's actual lifecycle in MonDbSeedTraces.

**Step 1:** Pick the seeding GUID to investigate from RCA-200 results.

**Step 2:** Query all events (not just failures) for that GUID to find its full timeline. See `references/queries.md` "Calibrate Time Window" section for the query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`, `{SeedingGuid}`

**Step 3:** Derive `{FailStart}` and `{FailEnd}`:

| Condition | `{FailStart}` | `{FailEnd}` |
|---|---|---|
| **Timeline ≤ 40 min** (typical) | `EarliestEvent - 5min` | `LatestEvent + 5min` |
| **Timeline > 40 min** (long-running seed) | `FirstFailure - 20min` | `FirstFailure + 20min` |

**Example:** If `FirstFailure` = 13:00 → `{FailStart}` = 12:40, `{FailEnd}` = 13:20

All Phase 4 and Phase 5 queries use these derived values.
---

### Phase 3.5: Determine if Geo Seeding is Actually an UpdateSLO Operation

**Goal:** When Phase 3 classifies the failure as **geo seeding** (different clusters, Forwarder/ForwarderDestination roles), determine whether the seeding was triggered by a customer **UpdateSLO** (scale up/down, tier change) rather than a true geo-replication operation. UpdateSLO uses the same geo-seeding mechanism internally, but has different root-cause implications and different remediation steps.

**Skip this step if Phase 3 determined the failure is local seeding.**

**Query: RCA-250 — Check for UpdateSLO / Management Operations**

See `references/queries.md` RCA-250 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{LogicalServerName}`, `{LogicalDatabaseName}`

**Fallback: RCA-251 — Check MonManagement for SLO Change Evidence**

See `references/queries.md` RCA-251 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`, `{LogicalServerName}`

**Interpretation:**

| Signal | Conclusion |
|---|---|
| `operation_friendly_name` contains `UpdateSlo` or `ScaleDatabase` and the operation's time window overlaps the seeding failure | **This is an UpdateSLO seeding**, not a geo-replication seeding |
| `old_slo` ≠ `new_slo` with overlapping timestamps | Confirms SLO change in progress |
| `state` = `Failed` or `error_code` ≠ 0 | The SLO change itself failed — the seeding failure is a symptom |
| No UpdateSLO/ScaleDatabase operations found | **This is genuine geo-replication seeding** — continue with Phase 4 as normal |

**Why this matters:**
- **UpdateSLO seeding** creates a new physical database at the target SLO and seeds data into it using the same Forwarder→ForwarderDestination channel as geo. If this seeding fails, the SLO change fails and the database stays at the old SLO. The remediation is to retry the SLO change or investigate why the target SLO environment couldn't accept the seed (e.g., target tier disk space, resource constraints on the target ring).
- **Geo-replication seeding** is about maintaining a geo-secondary for DR. Failure leaves the geo-secondary out of sync. Remediation focuses on the cross-region link, partner cluster health, and geo endpoint connectivity.

**If UpdateSLO is confirmed:**
1. Report it prominently:
   > "This seeding failure is part of an **UpdateSLO operation** ({old_slo} → {new_slo}), not a geo-replication seeding. The geo-seeding mechanism is used internally to transfer data to the new SLO target."
2. Add the SLO change details (old SLO, new SLO, operation state, error) to the RCA output
3. In Phase 5, consider SLO-specific root causes: target ring capacity, incompatible SLO transition, platform throttling, or quota limits
4. Continue with Phase 4 — the engine/Fabric telemetry analysis is still relevant for understanding the seeding failure mechanics

---

### Phase 3.6: Check for Concurrent Management and User Operations

**Goal:** Determine whether any management operations (platform-initiated or customer-initiated) or user DDL/DML operations were running on this database during the seeding period. Concurrent operations can interfere with seeding (e.g., an SLO change, geo-failover, database copy, or heavy user workload) and may be the root cause or a contributing factor.

**Always run this phase.** Even if the root cause appears clear from Phase 3/3.5, concurrent operations provide important context for the RCA.

**Query: RCA-260 — Management Operations During Seeding Period**

See `references/queries.md` RCA-260 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{LogicalServerName}`, `{LogicalDatabaseName}`

**Query: RCA-261 — User/Customer Operations During Seeding Period (MonNonPiiAudit)**

See `references/queries.md` RCA-261 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`, `{LogicalServerName}`, `{LogicalDatabaseName}`

**Query: RCA-262 — Broader Audit Summary (if RCA-261 returns many rows)**

See `references/queries.md` RCA-262 for the full query.
Key parameters: `{StartTime}`, `{EndTime}`, `{AppName}`, `{LogicalServerName}`, `{LogicalDatabaseName}`

**Interpretation:**

| Signal | Impact on Seeding | Action |
|---|---|---|
| `operation_friendly_name` contains `FailoverDatabase` or `ForceFailoverDatabase` | Geo-failover during seeding will cancel the seeding and restart it | Note in timeline; seeding should self-heal after failover completes |
| `operation_friendly_name` contains `CopyDatabase` or `CreateDatabaseCopy` | Database copy uses similar seeding resources; may cause contention | Check if copy completed; may need to wait for copy to finish |
| `operation_friendly_name` contains `DeleteDatabase` or `DropDatabase` on the partner server | Partner DB was deleted — geo-replication link is broken | Root cause: geo link removed; seeding cannot complete |
| `statement` contains `ALTER DATABASE` with TDE/encryption changes | TDE changes can invalidate certificates used during seeding | Correlate with Error 33111 — may explain missing certificate |
| `statement` contains `KILL` or `DBCC` | User may have killed a seeding-related process | Check if the killed SPID matches the RESTORE spid from Phase 4 |
| High volume of DDL/DML operations | Heavy workload can cause resource contention during seeding | Correlate with MonRgLoad in Phase 5 |
| No concurrent operations found | Seeding failure is not caused by external interference | Continue with Phase 4 |

**Output: Concurrent Operations Summary**

Always produce this in the output after Phase 3.6:

```
### Concurrent Operations During Seeding
| Time (UTC) | Type | Operation | State | Detail |
|---|---|---|---|---|
| {time} | Management | {operation_friendly_name} | {state} | {error or context} |
| {time} | User | {action_id}: {statement excerpt} | {succeeded} | {client_ip / principal} |
| ... | | | | |
```

If no concurrent operations are found, report:
> "No concurrent management or user operations detected during the seeding period."

---

### Phase 4: Correlate with Engine Telemetry

**Goal:** Find what SQL engine errors and Fabric events occurred at the same time as the seeding failure.

**Query: RCA-300 — Engine Error Log — Full Timeline (MonSQLSystemHealth)**

Keeps ALL messages (not just errors) to show what was happening on the instance. `IsError` and `IsSeeding` flags highlight key rows while preserving surrounding context for causal tracing.

See `references/queries.md` RCA-300 for the full query.
Key parameters: `{FailStart}`, `{FailEnd}`, `{AppName}`

**Key engine errors to look for:**

| Error | Meaning | Next Step |
|---|---|---|
| 3257 | Disk space insufficient on S:\\ | → Disk space is the root cause |
| 3271 / 3202 / 3203 | VDI I/O abort (OS 995) | → Symptom of teardown, check what caused the cancel |
| 33111 | AG certificate missing | → Certificate config issue |
| 3313 / 3414 | Redo/Recovery error | → Database corruption, escalate |
| 926 | Database SUSPECT | → 🚩 Escalate immediately |
| 701 | Out of memory | → Check MonRgLoad (Phase 5) |
| 41620 | Build cancelled by Fabric | → Fabric reconfiguration, check MonFabricApi |
| 41621 | Partition error | → Check substate (BUILD_FAILED, DB_SUSPECT, etc.) |

**Query: RCA-310 — Fabric API Lifecycle + Node Startups (MonFabricApi + WinFabLogs)**

Use `{FabricPartitionId}` from RCA-100 output. This query shows the full Fabric API event chain for the partition, including role changes, build replica start/end, faults, aborts, replica set changes, and node startup events.

```kql
// See queries.md RCA-310 for the full query
// Key parameters: {AppName}, {FabricPartitionId}, {FailStart}, {FailEnd}
```

**What to look for:**
- `hadr_fabric_replica_fault` → the replica faulted, triggering the cancellation
- `result_desc = E_FAIL` on `replicator_end_open` → secondary failed to open
- `new_role_desc = NONE` → Fabric demoted the replica
- `result_desc = E_ABORT` on `end_build_replica` → build was aborted

**Query: RCA-320 — Build Replica FSM (MonFabricDebug)**

See `references/queries.md` RCA-320 for the full query.
Key parameters: `{FailStart}`, `{FailEnd}`, `{AppName}`, `{PhysicalDatabaseId}`

**What to look for — identify the exact FSM failure point:**

The build replica FSM goes through these stages in order:
```
PENDING → CHECK_IF_SEEDING_NEEDED → SENDING_FILE_LIST → SEEDING → CATCHUP → COMPLETED
                                                                   ↓ (any stage)
                                                                 FAILED
```

| FSM Transition | What it means | Typical cause |
|---|---|---|
| CHECK → FAILED | Failed before seeding even started | Destination not ready (`0x80071c28`), partition error |
| SENDING_FILE_LIST → FAILED | File list exchange failed | Remote connectivity issue, destination rejected |
| SEEDING → FAILED (trigger=BUILD_FAILED) | Failed during data transfer | VDI abort, disk space, timeout, remote cancel |
| CATCHUP → FAILED | Seeding completed but log catch-up failed | Redo errors, log truncation, resource pressure |

- `is_primary` = true → this is the **Source** (primary) side FSM
- `is_primary` = false → this is the **Destination** (secondary) side FSM
- **The side that transitions to FAILED first is the originating side** of the failure
- Report the exact transition (e.g., "SEEDING → FAILED on Source side, trigger=BUILD_FAILED")
- **If MonFabricDebug returns 0 rows**, use RCA-325 below as the primary FSM state source instead.

**Query: RCA-325 — FabricReplicaBuildController State Changes (MonSQLSystemHealth)**

When MonFabricDebug has no data (common on some clusters/SKUs), the build replica FSM state transitions are still captured in MonSQLSystemHealth as `[HADR Fabric]` engine log messages. This query extracts them into structured columns.

See `references/queries.md` RCA-325 for the full query.
Key parameters: `{FailStart}`, `{FailEnd}`, `{AppName}`

**How to use RCA-325 output:**
- Each row is a state transition: `OldState → NewState` for a given `OperationId` (which maps to the seeding GUID lifecycle)
- The normal success path is: `PENDING → CHECK_IF_SEEDING_NEEDED → SENDING_FILE_LIST → SEEDING → CATCHUP → COMPLETED`
- A failing cycle typically shows: `PENDING → CHECK_IF_SEEDING_NEEDED → SENDING_FILE_LIST → SEEDING → FAILED`, then a new `OperationId` starts
- **Include each state transition as a row in the Detailed Event Timeline** with:
  - Source = `BuildFSM`
  - FSM State = `{OldState}→{NewState}`
  - Side = `Dest` (these messages are logged on the destination/secondary side)
- **Correlate `OperationId`** with the seeding GUID from MonDbSeedTraces — both map to the same build attempt

**Query: RCA-330 — Unified Timeline (MonFabricApi + MonSQLSystemHealth + MonDbSeedTraces)**

This is the **key correlation query**. It merges Fabric API events, engine error log messages, and seeding traces into a single chronological timeline. Read it top-to-bottom to see the exact sequence: what Fabric did → what the engine reported → what seeding observed.

```kql
// See queries.md RCA-330 for the full query
// Key parameters: {AppName}, {FabricPartitionId}, {SeedingGuid}, {FailStart}, {FailEnd}
```

**How to read the unified timeline:**

| `Source` | What it shows |
|---|---|
| `FabricApi` | Fabric lifecycle: role changes, build start/end, faults, aborts, reconfigurations |
| `Engine` | SQL error log: errors, warnings, informational messages from the engine |
| `Seeding` | Seeding events: start, progress, failure with codes and transfer progress |

**Causal ordering rule:** The root cause is the **first abnormal event** in the timeline. Everything after it is a consequence. Look for:
- A `FabricApi` fault/abort event that precedes the `Seeding` failure → Fabric caused the cancel
- An `Engine` error (disk space, OOM, certificate) that precedes both → engine-level root cause
- A `Seeding` failure with no prior abnormal events → seeding-internal issue (VDI, network, etc.)

**Backward causal tracing at the initial failure point:**

Once you identify the first failure event, trace backwards through the preceding events to understand WHY it failed:

1. **Locate the first failure** — the earliest event in the timeline with an error, fault, or failure code
2. **Read the 5-10 events immediately before** the failure — these are the causal context:
   - Engine messages: Was there a build replica response code (e.g., `0x80071c28` = FABRIC_NOT_READY)? An error from the HADR transport layer? A BACKUP/RESTORE error?
   - Fabric events: Was there a `change_role`, `replica_fault`, or `abort` just before?
   - Seeding events: Did the seeding start normally (WaitingForRestoreToStart) or fail immediately (0 bytes transferred)?
3. **Determine the initiating side:**
   - If the Source started normally but got a rejection response from the Destination → problem is on the Destination side
   - If the Source never started (immediate failure) → problem may be local (resource pressure, config)
   - If the Destination started but the Source cancelled → check Source-side engine errors
4. **Cross-reference with MonFabricDebug** (RCA-320) or **MonSQLSystemHealth** (RCA-325): Match the FSM `old_state_desc → FAILED` transition time with the unified timeline to see what happened just before the FSM transition
5. **Report the causal chain**: Present the sequence as: `[Trigger Event] → [Intermediate Effect] → [Seeding Failure]`

Example: `Destination returns 0x80071c28 (NOT_READY) → Source receives remote cancellation (code 1010) → Seeding fails with code 14 (Remote side failure) → IExecSql error 3601`

---

### Phase 5: Determine Root Cause

**Goal:** Match findings from Phases 3-4 to a known root cause pattern and provide a conclusion.

**Decision Tree:**

```
Found Error 3257 in Phase 4?
  → YES: Root cause = Disk Space Exhaustion
         S:\ drive full. Check DB size vs available space.
         Persistent until space freed.

Found Error 33111 in Phase 4?
  → YES: Root cause = Certificate Missing
         AG endpoint cert mismatch. Persistent config issue.

Found Error 41620 (Build Cancelled) in Phase 4?
  → YES: Check MonFabricApi (RCA-310)
         If hadr_fabric_replica_fault fires first:
           → Root cause = Secondary Replica Fault (transient)
         If no fault, just cancellation:
           → Root cause = Fabric Reconfiguration (transient)
         Self-heals in ~35 seconds.

Found Error 926 or 3313/3414 in Phase 4?
  → YES: 🚩 Root cause = Database Corruption / SUSPECT
         Escalate. Do NOT force rebuild.

Found Error 701 in Phase 4?
  → YES: Root cause = Memory Pressure
         Check MonRgLoad (RCA-400 below).

No clear engine error found?
  → Check if seeding transferred 0 bytes (Phase 3)
    → YES: Failure at initialization — check for VDI setup errors
  → Check if transferred > 0 but < database_size
    → YES: Failure mid-transfer — likely I/O or network issue
  → Run RCA-400 to check resource pressure
```

**Query: RCA-400 — Resource Pressure (if needed)**

See `references/queries.md` RCA-400 for the full query.
Key parameters: `{FailStart}`, `{FailEnd}`, `{AppName}`

**Query: RCA-410 — Log/RG History (if log-related)**

See `references/queries.md` RCA-410 for the full query.
Key parameters: `{FailStart}`, `{FailEnd}`, `{AppName}`

---

## Output Format

Provide a structured RCA summary with the sections below. **Always include the Detailed Event Timeline.**

```
## Seeding RCA Summary

### Incident Context (if from IcM)
| Field | Value |
|---|---|
| IcM ID | {IcmId} |
| Time Range | {start} — {end} (UTC) |
| Cluster | {ClusterName} |
| Logical Server | {LogicalServerName} |
| Logical Database | {LogicalDatabaseName} |
| Logical Database ID | {logical_database_id} |
| Physical Database ID | {physical_database_id} |
| Fabric Partition ID | {fabric_partition_id} |
| Seeding Start | {earliest seeding event timestamp} |
| Seeding End | {latest seeding event, or "ongoing"} |
| SLO | {service_level_objective} |
| Tier | GP / BC / HS |
| DB Size | {database_size_bytes as human-readable} |

### Source and Target Context
| Field | Source (Primary) | Target (Secondary / Destination) |
|---|---|---|
| Cluster (Tenant Ring) | {source cluster / ring} | {target cluster / ring} |
| Server Name | {source LogicalServerName} | {target LogicalServerName} |
| Database Name | {source LogicalDatabaseName} | {target LogicalDatabaseName} |
| Instance Name (AppName) | {source AppName} | {target AppName} |
| Logical Database ID | {source logical_database_id} | {target logical_database_id} |
| Physical Database ID | {source physical_database_id} | {target physical_database_id} |
| Fabric Partition ID | {source fabric_partition_id} | {target fabric_partition_id} |
| Is UpdateSLO | {Yes/No} | — |
| Seeding Role | Source / Forwarder | Destination / ForwarderDestination |
| Seeding Type | {Local / Geo DR} | {Local / Geo DR} |

### Multi-DB Summary (if applicable)
| DB (physical_database_id) | Fail Count | Codes | Status |
|---|---|---|---|
| db1... | 9 | 1007, 17, 3601 | Failed → Retried → Succeeded |
| db2... | 0 | — | Succeeded |
| ... | | | |

### Per-DB Analysis: {selected DB}
- Seeding GUID: {guid}
- Failure code: {code} ({message})
- Role: Source / Destination
- Transferred: {bytes} / {total_bytes} ({pct}%)
- Local vs Geo: {determination}

### Concurrent Operations During Seeding
| Time (UTC) | Type | Operation | State | Detail |
|---|---|---|---|---|
| {time} | Management | {operation} | {state} | {error or context} |
| {time} | User | {action}: {statement} | {succeeded} | {principal / client_ip} |

### Detailed Event Timeline
Unified chronological view from MonDbSeedTraces + MonSQLSystemHealth + MonFabricApi.
The **Side** column identifies whether each event is from the Source (primary/sender) or Destination (secondary/receiver) perspective. The **FSM State** column shows the build replica FSM state at that moment (if applicable).

| Time (UTC) | Side | Source | FSM State | Event | Detail |
|---|---|---|---|---|---|
| 22:38:40 | Source | Fabric | PENDING→CHECK | build_replica_start | operation_id=... |
| 22:38:40 | Source | Engine | SEEDING | BACKUP DATABASE started | DB size=230GB |
| 22:38:41 | Dest | Engine | — | Response code 0x80071c28 | FABRIC_NOT_READY |
| 22:38:42 | Source | Seeding | SEEDING→FAILED | failure (14) | "Remote side failure", 0 bytes xfer |
| 22:38:42 | Source | Engine | FAILED | Build replica error | "encountered error ..." |
| 22:38:43 | Source | Fabric | FAILED | hadr_fabric_replica_fault | fault_type=Transient |
| ... | | | | | |

**→ Causal chain**: [Dest: FABRIC_NOT_READY] → [Source: remote cancellation] → [Seeding: code 14]

### Root Cause
{Pattern name}: {description}
Persistent: Yes/No
Self-healed: Yes/No (retried at {time}, succeeded at {time})

### Recommended Action
{What to do next}

### Potential Transfer Targets
If the root cause requires action by another team, list the candidate IcM owning teams for transfer:

| Root Cause Pattern | Transfer Target Team | Reason |
|---|---|---|
| Certificate / asymmetric key missing (Error 33111) | **YOURTEAM\Geo-Replication** or **YOURTEAM\Security** | TDE cert provisioning on destination |
| Disk space exhaustion (Error 3257) | **YOURTEAM\Storage** | S:\ drive full on node |
| Database corruption / SUSPECT (Error 926, 3313) | **YOURTEAM\Engine** | Requires engine team escalation |
| Fabric reconfiguration / quorum loss | **YOURTEAM\Fabric** | Fabric-level issue causing build cancellation |
| Resource pressure (OOM, worker exhaustion) | **YOURTEAM\Resource Governance** | Tenant resource limits hit |
| UpdateSLO-triggered seeding | **YOURTEAM\Provisioning** | SLO change side-effect |
| No clear root cause / unknown pattern | **YOURTEAM\Availability** | General availability investigation |

Replace `YOURTEAM` with the appropriate service tree path. If the IcM is already owned by the correct team, state "No transfer needed."
```

**Timeline construction:** Use RCA-330 (unified timeline query) output plus RCA-325 (build controller state changes). **IMPORTANT: Query BOTH the Source cluster and Destination cluster** — the timeline must include events from both sides to show the full causal chain (e.g., Source BACKUP completing successfully while Dest RESTORE fails). Run RCA-300, RCA-325, and seeding trace queries on each cluster using the respective `{AppName}`. Merge the results chronologically. Synthesize the sources into one readable table. For each row:
- **Side** column: Mark each event as `Source` or `Dest` based on:
  - Seeding rows: use `role_desc` (Source/Destination)
  - Engine rows: check if the message references the local replica (Source) or the remote replica (Dest)
  - Fabric rows: use `is_primary` (true=Source, false=Dest) or infer from `NodeName`
  - BuildFSM rows (RCA-325): always `Dest` (logged on secondary)
  - If the event is about the response FROM the remote side (e.g., "received build replica response"), mark as `Dest` even though it was logged on the Source
- **FSM State** column: Map the event time to the current Build Replica FSM state from RCA-320 or RCA-325. Show the state transition (e.g., `SEEDING→FAILED`) when the FSM changes. When RCA-320 returns no data, use RCA-325 as the FSM state source.
- **Source** column values: `Fabric`, `Engine`, `Seeding`, or `BuildFSM` (from RCA-325)
- **Seeding** rows: show event name, role, failure code, transfer progress
- **Engine** rows: show error code, severity, and a short message excerpt
- **Fabric** rows: show event name, role change, fault type, result

The timeline should cover the seeding GUID's full lifecycle (from first event to last), not just the failure moment. This includes the initial start, progress, failure, and any retry/success.

**Auto-follow on recommended actions:**

After determining the root cause and recommended actions, **automatically follow the most relevant action** if it involves querying additional data that is accessible:

1. **"Investigate the Destination side"** → Query the partner region's Kusto cluster (if known from MonDmContinuousCopyStatus or RCA-110) for the destination's MonFabricApi, MonFabricDebug, and MonSQLSystemHealth
2. **"Check MonRgLoad for resource pressure"** → Run RCA-400 automatically
3. **"Check disk space"** → Run MonDmIoVirtualFileStats or MonDmLogSpaceInfo queries automatically
4. **"Check the partner cluster"** → Identify the partner cluster from RCA-110, resolve its Kusto URL, and run RCA-300/310/320 on that cluster

Do NOT stop at "Recommended Action: investigate X". If you can investigate X with the tools available, do it immediately and report the findings.

## Related Skills

- `seeding-monitor` — Fleet-wide seeding health overview and top-N pattern discovery
- `quorum-loss` — Quorum loss often triggers seeding; seeding failures can prolong quorum loss

## Knowledge References

- See `.github/skills/Availability/seeding-monitor/references/knowledge.md` for error code tables, failure code descriptions, and known patterns
- See `.github/skills/Availability/seeding-monitor/references/prep/Automatic Seeding - SQL Server and SQL DB.pptx` for seeding architecture details
