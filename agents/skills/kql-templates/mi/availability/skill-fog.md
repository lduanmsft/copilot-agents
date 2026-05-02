# Skill: FOG (Failover Group) Investigation

**Scope**: All MI Failover Group lifecycle issues — create, seeding, failover, drop, health check.

This is a **generic** skill. It does not assume a specific symptom. The Phase 1 query produces evidence; Phase 2 maps that evidence to the right sub-investigation. **Always run Phase 0 → Phase 1 → Phase 2 first**, then enter the matching branch.

**Source**: dlinger ⟷ lduan-mi-sea, real cases 2026-04-29 (happy seeding) and 2026-04-16 (45143 failure due to stale TDE DEK protector). Investigated 2026-05-02.

---

## Phase 0: Collect parameters & narrow the question

Required:
- **ServerName** — the MI logical server name the user is asking about (could be primary or secondary)
- **Region** — region of `ServerName`
- **TimeRange** — when the issue started / when the user attempted the FOG operation. Prefer narrow windows (2-6h). For "just happened" use last 2-4h.

Ask user **what they want to know**:
- A. **Create failed / stuck** — FOG creation didn't succeed
- B. **Seeding slow / stuck** — FOG was created, but seeding is slow or stalled
- C. **Failover failed / unexpected** — manual or auto-failover did not produce expected result
- D. **Drop / cleanup issues** — DropFOG had side effects (orphan DBs, listener still resolving, etc.)
- E. **Health check / current state** — just want to see FOG status

Optional context that narrows root cause significantly:
- Did user recently do AKV / TDE permission experiments?
- Did user drop+recreate the same DB recently?
- Did user delete a previous FOG with the same name?
- Did user just stop/start the MI?

Don't proactively ask all these — but if A/B branch results are inconclusive, come back and probe.

---

## Phase 1: Identify the FOG and pull the operation log

**One query** to get the FOG configuration:

```kql
MonGeoDRFailoverGroups
| where TIMESTAMP >= ago({Window})
| where logical_server_name =~ '{ServerName}' or partner_server_name =~ '{ServerName}'
| summarize arg_max(TIMESTAMP, *) by failover_group_name, logical_server_name
| project TIMESTAMP, failover_group_name, logical_server_name, partner_server_name,
          partner_region, role, failover_group_type, failover_policy, failover_group_create_time
```

If empty → user may be asking about a **failed-to-create** FOG that never got recorded here, or one that was already dropped. Continue to Phase 1b without this info.

**Phase 1b — pull all FOG-related management operations on the primary**:

⚠️ KQL `has` is token-based; CamelCase tokens like `CreateManagedFailoverGroup` rarely match. Use `contains` for type names.

```kql
MonManagementOperations
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where operation_parameters has '{ServerName}'
| where operation_type contains 'FailoverGroup'
   or operation_type contains 'GeoSecondary'
   or operation_type == 'MakeAllManagedDatabasesAccessible'
| summarize FirstTs=min(PreciseTimeStamp), LastTs=max(PreciseTimeStamp),
            DurMin=datetime_diff('minute', max(PreciseTimeStamp), min(PreciseTimeStamp)),
            Result=tostring(make_set(operation_result, 5)),
            EventSet=tostring(make_set(event, 5)),
            ErrorCode=max(error_code),
            ErrorMsg=tostring(take_any(error_message)),
            FogName=tostring(take_any(extract(@'<FailoverGroupName>([^<]+)', 1, operation_parameters))),
            DbList=tostring(take_any(extract(@'<Databases>(.*?)</Databases>', 1, operation_parameters))),
            DbId=tostring(take_any(extract(@'<ManagedDatabaseId>([^<]+)', 1, operation_parameters)))
            by operation_type, request_id
| order by FirstTs asc
```

Cluster: Follower for **the primary's region**. Look up via `~/.copilot/agents/skills/kql-templates/shared/SQLClusterMappings.Followers.csv`.

This single result table is the primary evidence. Read it carefully:

- Sort by `FirstTs` to see chronology
- `DurMin > 20` for `Create*` / `*Failover*` = **silent retry exhausted** (plumbing issue)
- `EventSet` containing `management_operation_failure` + `ErrorCode != 0` = explicit failure
- All `Succeeded` but user still sees problem = **branch B/C/D** (post-create issue), not a control-plane problem

---

## Phase 2: Decision tree — pick the right branch based on Phase 1 evidence

| Phase 1 evidence | Branch to enter |
|---|---|
| Found a **failed** `CreateManagedFailoverGroup` / `AutomaticGeoSecondaryCreate` in the window | **Branch A — create-failed** |
| `CreateManagedFailoverGroup` succeeded, but user reports seeding slow/stuck | **Branch B — seeding** |
| Found `Failover*` op with failure or unexpected role swap | **Branch C — failover** |
| Found `DropManagedFailoverGroup` with downstream issues | **Branch D — drop-cleanup** |
| All ops Succeeded, user wants current state | **Branch E — health-check** |
| Phase 1 shows nothing at all | User may be querying wrong region; or operations are too old; expand window |

If the user told you the problem type up front (Phase 0), still run Phase 1 — the evidence may surprise you (e.g. user thinks "FOG seeding is slow" but actually FOG never finished creating).

---

## Branch A — Create failed / stuck

**Step A1: Map the error_code to a hypothesis**

| error_code | Message snippet | Most likely root cause |
|---|---|---|
| **45143** | `The source database '<guid>' does not exist` | Source DB rejected by FOG validator. Most often **stale TDE DEK protector** (verify in A2). Less often: DB was actually dropped during the retry window. |
| **45939** | `ManagedInstanceNoConditionToMakeDatabaseAccessible` | DB recovery from prior AKV outage hasn't fully completed. |
| **40982** | `Instance failover group cannot be created because the secondary instance has user databases` | Secondary MI has leftover DBs (orphan from previous FOG, or independent DBs). |
| **45330** | `requires the 'Key Vault Crypto Service Encryption User' RBAC role` (or AKV permission list) | Secondary MI lost AKV access. Restore RBAC/access policy. |
| Timeout (no explicit code, just long DurMin then Failed) | — | Try Phase 1 with wider window; check secondary's `MonManagementOperations` too. |

**Step A2: Verify TDE/DEK hypothesis (when error_code == 45143)**

This is the non-obvious case that took the longest to find on 2026-05-02. Error message says "does not exist" but `MonAnalyticsDBSnapshot` shows the DB is `Ready`. The control-plane filter excludes it because the DEK is encrypted by a stale (revoked/replaced) AKV key thumbprint.

A2.1 — Find source DB's `logical_database_id`:
```kql
MonAnalyticsDBSnapshot
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where logical_server_name =~ '{ServerName}'
| where logical_database_name =~ '{DbName}'
| summarize arg_max(TIMESTAMP, *) by logical_database_name
| project logical_database_name, logical_database_id, physical_database_id, state
```

The `logical_database_id` should match the GUID quoted in the 45143 error message.

A2.2 — Trace DEK encryptor thumbprint over the failure window:
```kql
MonDatabaseEncryptionKeys
| where TIMESTAMP between (datetime({Start}) .. datetime({End}))
| where LogicalServerName =~ '{ServerName}'
| where logical_database_id =~ '{LogicalDatabaseId}'
| project TIMESTAMP, encryption_state, is_encrypted,
          encryptor_type, encryptor_thumbprint
| order by TIMESTAMP asc
```

**Smoking gun**: `encryptor_thumbprint` flips from a "good" thumbprint (the AKV key user just re-activated) back to an old one (the previously revoked AKV key). If you see this flip occur shortly before the user's FOG create attempt, hypothesis confirmed.

**Workaround (verified)**: Drop the source DB and recreate it. The new DB inherits the current server protector and is FOG-eligible. (Re-rotating the DEK back to the new key without DB recreate was not tested in the case data we have.)

**Step A3: Other 45143 sub-hypotheses (when A2 thumbprint history looks clean)**
- DB was actually dropped between FOG submit and validator (look for `DropManagedDatabase` on this DB during the retry window)
- DB physical_database_id changed mid-retry (e.g. recovery-restart) — compare `MonAnalyticsDBSnapshot.physical_database_id` at retry start vs retry end

**Step A4: For 40982 — find the offending secondary DB**
```kql
MonAnalyticsDBSnapshot
| where TIMESTAMP >= ago(2h)
| where logical_server_name =~ '{PartnerServerName}'
| where database_type == 'SQL.ManagedUserDb'
| summarize arg_max(TIMESTAMP, *) by logical_database_name
| project logical_database_name, logical_database_id, state, create_mode
```
Drop those DBs on the secondary, retry FOG create.

---

## Branch B — Seeding slow / stuck (FOG was created successfully)

**Step B1: Confirm FOG is actually past the create stage**
Phase 1's `CreateManagedFailoverGroup` should be `Succeeded`. If not, re-route to Branch A.

**Step B2: Pull seeding traces on the secondary side**

Look up the secondary region's Follower cluster, then run:

```kql
MonDbSeedTraces
| where TIMESTAMP >= ago({Window})
| where AppTypeName startswith 'Worker.CL'
| where LogicalServerName =~ '{PartnerServerName}'
| where event in ('hadr_physical_seeding_progress', 'hadr_physical_seeding_failure', 'hadr_physical_seeding_state')
| extend rate_mb_s = round(transfer_rate_bytes_per_second / 1024.0 / 1024.0, 2)
| extend pct = round(todouble(transferred_size_bytes) * 100.0 / todouble(database_size_bytes), 2)
| project originalEventTimestamp, database_name, pct, rate_mb_s,
          internal_state_desc, role_desc, failure_code, failure_message
| order by originalEventTimestamp desc
| take 100
```

Three outcomes:
1. **Rows present, progress increasing**: actually working, just large DB. Use `database_size_bytes` to estimate ETA.
2. **Rows present, but state = Failure** or `failure_code != 0`: read `failure_message`, often points at AKV / network / disk.
3. **No rows at all**: `MonDbSeedTraces` is for **physical seeding** (BC instances actively shipping log+pages). Empty doesn't always mean "stuck" — see B3.

**Step B3: Check `MonDmContinuousCopyStatus` for high-level link state**
```kql
MonDmContinuousCopyStatus
| where TIMESTAMP >= ago({Window})
| where LogicalServerName =~ '{ServerName}' or LogicalServerName =~ '{PartnerServerName}'
| summarize arg_max(TIMESTAMP, *) by partner_database, partner_server
| project TIMESTAMP, partner_server, partner_database, replication_state_desc,
          replication_lag_sec, is_interlink_connected, is_rpo_limit_reached
```
`replication_state_desc` shows `SEEDING` / `CATCH_UP` / `Catchup` / etc. If stuck in `SEEDING` for >1h on a small DB → check secondary side errors (B4).

**Step B4: Check secondary side SQL errors**
```kql
MonSQLSystemHealth
| where TIMESTAMP >= ago({Window})
| where LogicalServerName =~ '{PartnerServerName}'
| where error_id > 0
| summarize Cnt=count(), MsgSample=tostring(take_any(message)) by error_id
| order by Cnt desc
```
(Note: this table has `error_id` only, no `error_severity` column.)

---

## Branch C — Failover failed or unexpected

**Step C1**: Find the `Failover*` operation in Phase 1 evidence. Identify if it was planned (`*Failover*`, `*Switch*`) or forced (`*ForcedFailover*`).

**Step C2: Check FOG state transitions during the failover window**
```kql
MonGeoDRFailoverGroups
| where TIMESTAMP between (datetime({Start}-30m) .. datetime({End}+30m))
| where failover_group_name =~ '{FogName}'
| project TIMESTAMP, logical_server_name, role, partner_server_name
| order by TIMESTAMP asc
```
You should see role flip from `Primary` → `Secondary` (and vice versa). If not, failover didn't complete.

**Step C3: Check `MonDmDbHadrReplicaStates` on both sides for sync state**
```kql
MonDmDbHadrReplicaStates
| where TIMESTAMP between (datetime({Start}-15m) .. datetime({End}+15m))
| where LogicalServerName in~ ('{ServerName}', '{PartnerServerName}')
| summarize arg_max(TIMESTAMP, *) by logical_database_name, LogicalServerName
| project LogicalServerName, logical_database_name, synchronization_state_desc,
          synchronization_health_desc, is_primary_replica, secondary_lag_seconds
```
(Column is `logical_database_name` here, not `database_name`. See `mi-hot-tables.md`.)

**Step C4**: For "data loss after forced failover" — check `secondary_lag_seconds` and `MonDmContinuousCopyStatus.is_rpo_limit_reached` at the moment of failover.

---

## Branch D — Drop / cleanup issues

**Step D1: Confirm `DropManagedFailoverGroup` succeeded**
Phase 1 evidence should show it. Note the `request_id` and timestamp.

**Step D2: Check whether secondary DBs were properly cleaned up**
```kql
MonAnalyticsDBSnapshot
| where TIMESTAMP >= datetime({DropTs})
| where logical_server_name =~ '{PartnerServerName}'
| where database_type == 'SQL.ManagedUserDb'
| summarize arg_max(TIMESTAMP, *) by logical_database_name
| project logical_database_name, logical_database_id, state, create_mode
```
After Drop, secondary user DBs should either be gone or transitioned out of FOG (no longer `create_mode='Copy'` with active link). Orphans are a known issue and will block subsequent FOG creates with error 40982.

**Step D3: Check FOG listener DNS / gateway state** (if user reports stale listener)
```kql
MonGeoDRFailoverGroups
| where TIMESTAMP >= datetime({DropTs})
| where failover_group_name =~ '{FogName}'
```
Should be empty after Drop. If not, the FOG record is still around — escalate.

---

## Branch E — Health check / current state

Phase 1's `MonGeoDRFailoverGroups` query already gives the snapshot. Add:

```kql
MonDmContinuousCopyStatus
| where TIMESTAMP >= ago(30m)
| where LogicalServerName =~ '{ServerName}' or LogicalServerName =~ '{PartnerServerName}'
| summarize arg_max(TIMESTAMP, *) by partner_database
| project TIMESTAMP, LogicalServerName, partner_server, partner_database,
          replication_state_desc, replication_lag_sec
```
And the recent ops:
```kql
MonManagementOperations
| where TIMESTAMP >= ago(7d)
| where operation_parameters has '{ServerName}'
| where operation_type contains 'FailoverGroup'
| summarize Cnt=count(), LastTs=max(PreciseTimeStamp),
            Failures=countif(event == 'management_operation_failure')
            by operation_type
| order by LastTs desc
```

---

## Cross-cutting tips

1. **Always run Phase 0 → Phase 1 → Phase 2 in order**. Don't skip to a branch based on the user's hypothesis — Phase 1 evidence often refutes the hypothesis.
2. **Empty `MonDbSeedTraces` ≠ seeding stuck**. It's only meaningful when Phase 1 confirms the FOG was actually created and is past the create stage.
3. **`logical_server_name` is often empty in `MonManagementOperations` for FOG ops** — always filter via `operation_parameters has '<server>'`.
4. **Use `contains` not `has` for CamelCase operation_type values** (`CreateManagedFailoverGroup` etc.).
5. **Schema gotchas** (full list in [`mi-hot-tables.md`](../../mi-hot-tables.md)):
   - `MonGeoDRFailoverGroups.partner_server_name` (not `partner_logical_server_name`)
   - `MonDbSeedTraces.database_name` (stores GUID; not `logical_database_name`)
   - `MonDmDbHadrReplicaStates.logical_database_name` (opposite naming from above)
   - `MonSQLSystemHealth` has `error_id` only — no `error_severity`
6. **MI moves between nodes** — `MonManagedServers arg_max` across all nodes shows stale rows. Cross-reference time-series before declaring "MI was stopped".
