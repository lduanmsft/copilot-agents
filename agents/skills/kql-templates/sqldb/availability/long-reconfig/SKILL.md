---
name: long-reconfig-database
description: Debug Azure SQL Managed Instance long reconfiguration database issues (TSGCL0212) where a database partition reconfiguration takes longer than expected. Applies ONLY to Managed Instance incidents (AppTypeName Worker.CL*). Investigates known causes including Error 41614 state 27 (GP only), inconsistent remote replicas, file metadata mismatch, long running checkpoints, instance boot deadlocks, XEvent deadlocks, stuck forwarder databases, and msdb upgrade script stuck on metadata lock. Use when troubleshooting LongReconfigDatabase alerts, stuck reconfiguration, or database partitions stuck in Reconfiguring state.
---

# Debug Azure SQL Managed Instance Long Reconfiguration Database Issues

!!!AI Generated. To be verified!!!

> **⚠️ SCOPE: This skill applies ONLY to Azure SQL Managed Instance incidents where `AppTypeName` is `Worker.CL*` (e.g., `Worker.CL.WCOW.SQL22`). If the app type is different (e.g., `Worker.ISO.*` for SQL DB), this skill does not apply.**

Debug scenarios where a database partition reconfiguration is taking longer than expected, causing customer-facing unavailability.

## Overview

This skill investigates long reconfiguration scenarios (TSGCL0212) where a Service Fabric partition reconfiguration is stuck or delayed. Long reconfiguration can cause customer-facing unavailability and should be mitigated promptly.

**Common causes:**
- Error 41614 state 27 — ERR_STATE_HADR_DB_MGR_DOES_NOT_EXIST (GP only)
- Inconsistent remote replicas (Error 5120)
- File metadata mismatch between GeoSecondary and GeoPrimary (Error 5173)
- Long running checkpoint
- Instance boot deadlock
- Unknown issues requiring dump and process kill

**Potential mitigations:**
- Kill SQL process (primary or secondary depending on scenario)
- Take dump before killing for investigation
- Follow scenario-specific TSGs for complex cases
- Restart node from SFE as a fallback

⚠️ **Note:** For any unknown issue, always take a dump before mitigating. If you did take a dump, leave the link in the incident.

## Required Information

This skill requires the following inputs:

### From User or ICM:
- **AppName** — Application name (e.g., `fabric:/sterling-dpseastus2-lnxsqlmi02/Sterling.User.c7c3b2a1-...`)
- **PartitionId** — Partition ID of the affected database
- **StartTime** — When the issue started (UTC format: `2026-01-01 02:00:00`)
- **EndTime** — When the issue ended (UTC, optional)

### Optional:
- **NodeName** — Node name where the issue was detected
- **DbName** — Logical database name
- **DatabaseId** — Database ID for trace filtering
- **ProcessId** — SQL process ID
- **ThreadId** — Thread ID for detailed trace filtering

### From execute-kusto-query skill:
- **cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **database** (e.g., `sqlazure1`)

## Investigation Workflow

### 1. Check If Issue Is Still Active

Before proceeding, verify the issue has not already self-healed or been mitigated by automation.

Execute query **LR100** from [references/queries.md](references/queries.md).

Also check database state in SFE:
- ❌ **State = Reconfiguring:** Issue is still active — proceed with investigation
- ✅ **State = Ready:** Issue has self-healed — mitigate the incident

### 2. Identify Specific Case

Work through each known case in order. Execute the verification query for each case to determine the root cause.

**⚠️ IMPORTANT: Always run Step 2a (Performance Pressure Check) in parallel with case identification queries.** Performance pressure can be a root cause or contributing factor and must not be skipped.

**Case 1: Error 41614 State 27 (GP Only)**
- Execute **LR200** — Check for ERR_STATE_HADR_DB_MGR_DOES_NOT_EXIST
- If results found: Kill old primary. If that doesn't resolve, kill new primary too.

**Case 2: Inconsistent Remote Replicas**
- Execute **LR210** — Check for Error 5120
- If results found: Follow TSGCL0069.2 (backup restore team) or TSGCL0069.1 (surface area team)

**Case 3: Error 5173 - File Metadata Mismatch**
- Execute **LR220** — Check for Error 5173
- If results found: Reseed GeoSecondary (SOPCL00104.3), then follow TSGCL0069.1

**Case 4: Long Running Checkpoint**
- Execute **LR230** and **LR231** — Compare checkpoint start vs. finish events
- If start exists without corresponding finish: Take dump, then kill primary SQL process

**Case 5: Instance Boot Deadlock**
- Execute **LR240** — Check for DelayKillingSessionsHoldingReplMasterLocks
- If results found: Kill the stuck SQL process

### 2a. Performance Pressure Check (Always Run)

> **⚠️ Run these queries in parallel with case identification. Do not skip this step.**

Performance pressure (CPU, memory, I/O) can cause or contribute to long reconfigurations by starving HADR threads, blocking log transport, or preventing quorum catchup.

- Execute **LR250** — CPU and I/O pressure (instance-level resource stats)
- Execute **LR252** — Memory pressure (resource pool memory grant timeouts)
- Execute **LR254** — I/O pressure (virtual file stats latency)
- Execute **LR256** — Wait stats analysis (resource contention wait types)
- Execute **LR258** — Performance error indicators (non-yielding, OOM, I/O stalls)

🚩 If any of these indicate severe pressure, it may be the root cause or a contributing factor — document in the incident.

### 2b. Container and Networking Infrastructure Check (Always Run)

> **⚠️ Run these queries in parallel with case identification. Do not skip this step.**
> **If non-SQL services (e.g., marker service) are also stuck in Reconfiguring, the issue is likely at the infrastructure/networking layer, not SQL/HADR.**

Leaked network containers, failed pod sandboxes, or crashed containers can break HADR transport across all nodes. These issues cannot be resolved by killing SQL processes — they require Connectivity and Networking team engagement.

- Execute **LR260** — Active containers per node (is the container running?)
- Execute **LR262** — Container starts per node (crash loops?)
- Execute **LR264** — Network container create/delete results (NC failures?)
- Execute **LR266** — Container lifecycle timeline (when did crashes/restarts happen?)
- Execute **LR268** — Service package activation failures (cascaded from NC failures?)

🚩 If NC create/delete returns `E_FAIL`, this is an infrastructure root cause. Escalate to **SQL MI: Connectivity and Networking**. Killing SQL processes will NOT help.

**Case 10: msdb Upgrade Script Stuck (known issue — PBI 4448193)**
- Execute **LR305** — Check if msdb upgrade script started but never completed
- 🚩 If `originalEventTimestamp1` is NULL → upgrade is stuck on DBCC UPDATEUSAGE metadata lock
- **This is the most common cause of msdb-only LongReconfig incidents**
- Killing secondaries does NOT help — kill the primary SQL process

### 3. General Investigation (Unknown Issue)

If none of the above cases match, run these queries to identify the root cause:

- Execute **LR300** — General error survey
- Execute **LR310** — Check for XEvent dispatcher deadlock (known cause)
- Execute **LR320** — SQL process lifetime analysis (check for crashes/restarts)
- Execute **LR330** — Forwarder redo queue size (large redo queue blocks reconfig)
- Execute **LR340** — Database recovery time (stuck recovery blocks reconfig)

### 3a. Deep Investigation (Transport/Connectivity)

If general investigation is inconclusive, investigate transport-level issues:

- Execute **LR360** — Replica sync state timeline (when did secondaries lose sync?)
- Execute **LR370** — UCS connection errors (check for TCP 10060 timeouts)
- Execute **LR380** — Backup on secondary activity (stuck backups can block primary)
- Execute **LR390** — HADR transport timeouts (session-level connectivity loss)
- Execute **LR395** — HADR timeout scope analysis (determines if issue is on primary or a specific secondary)

**⚠️ Decision: Kill primary or secondary?**

> 🚩 **STOP: Before recommending any SQL process kill, check Step 2b results first.** If container or networking infrastructure issues were found (NC `E_FAIL`, container crashes, service package activation failures), do NOT kill SQL processes. Killing SQL will not resolve infrastructure-level issues and may make the situation worse. Escalate to **SQL MI: Connectivity and Networking** instead.

Use LR395 results to decide mitigation **only if Step 2b showed no infrastructure issues**:
- **Only 1 secondary has timeouts** → Kill that secondary's SQL process
- **All secondaries have timeouts at ~same time** → Kill the primary SQL process
- **Cascade pattern (1 secondary first, others follow)** → Kill the primary SQL process

**⚠️ Known pattern: Stuck backup-on-secondary blocking primary**

If LR380 shows `BACKUP LOG started` without `BACKUP LOG finished` on a secondary, and LR390 shows HADR transport timeouts on the primary shortly after:
1. The secondary's backup got stuck (likely XStore/blob write hang)
2. The primary's `SendBackupCmdMsgAndWaitForResponse` blocked waiting for the result
3. This froze the primary's HaDrDbMgr thread, making it unresponsive to all secondaries
4. **Mitigation:** Kill the primary SQL process

### 3b. Check Mitigation History

- Execute **LR350** — Kill process actions (was mitigation already attempted?)

### 4. Post-Mitigation Verification

After applying mitigation, wait approximately 15 minutes, then:

- Execute **LR400** — Verify the alert is no longer active
- Check SFE: Database should show "Ready" state
- ✅ Last timestamp before mitigation — Issue is healed
- ❌ New timestamps after mitigation — Issue persists, try alternative mitigation or escalate

## Execute Queries

Execute queries from [references/queries.md](references/queries.md):

**Step 1: Confirm Issue**
- LR100 (Check Active Long Reconfiguration Alert)

**Step 2: Identify Case**
- LR200 (Case 1: Error 41614 State 27)
- LR210 (Case 2: Inconsistent Remote Replicas)
- LR220 (Case 3: Error 5173 File Mismatch)
- LR230 + LR231 (Case 4: Long Running Checkpoint)
- LR240 (Case 5: Instance Boot Deadlock)
- LR305 (Case 10: msdb Upgrade Script Stuck — **check this first if database is msdb**)

**Step 2a: Performance Pressure Check (Always Run)**
- LR250 (CPU and I/O Pressure — Instance-Level Resource Stats)
- LR252 (Memory Pressure — Resource Pool Memory Grants)
- LR254 (I/O Pressure — Virtual File Stats Latency)
- LR256 (Wait Stats Analysis — Resource Contention)
- LR258 (Performance Error Indicators — Non-Yielding, OOM, I/O Stalls)

**Step 2b: Container and Networking Infrastructure Check (Always Run)**
- LR260 (Active Containers Per Node)
- LR262 (Container Starts Per Node — Crash Loops)
- LR264 (Network Container Create/Delete Results — NC Failures)
- LR266 (Container Lifecycle Timeline)
- LR268 (Service Package Activation Failures)

**Step 3: General Investigation**
- LR300 (General Error Survey)
- LR310 (XEvent Dispatcher Deadlock)
- LR320 (SQL Process Lifetime Analysis)
- LR330 (Forwarder Redo Queue Size)
- LR340 (Database Recovery Time)

**Step 3a: Deep Investigation (Transport/Connectivity)**
- LR361 + LR362 (WinFab FTUpdate reconfiguration timeline — shows what triggered the reconfig and role changes)
- LR360 (Replica Sync State Timeline)
- LR370 (UCS Connection Errors)
- LR380 (Backup on Secondary Activity)
- LR390 (HADR Transport Timeouts)

**Step 3b: Mitigation History**
- LR350 (Mitigation Actions — dumps, kills, restarts)
- LR355 (Management Operations — reseed, SLO update)
- LR356 (Seeding Progress Tracking — monitor reseed after log corruption)

**Step 4: Verification**
- LR400 (Verify Issue Resolved)

## Query Execution Format

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "<description>"
- parameters: {"cluster-uri": "<uri>", "database": "<db>", "query": "<kql>"}
```

**Parameters must be JSON object, not string.**

## Escalation

If the issue cannot be resolved through the documented mitigations:
- **Primary:** SQL Managed Instance: Availability
- **After hours:** SQL Managed Instance Expert: HA & GeoDR

## Reference

See [knowledge.md](references/knowledge.md) for detailed definitions and known causes.
See [principles.md](references/principles.md) for debug principles and escalation criteria.

## Related Documentation

- [TSGCL0212 - LongReconfigDatabase](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-managed-instance/sql-mi-availability/tsg-sql-mi-availability/index/availability/tsgcl0212-longreconfigdatabase)
- [Azure SQL Managed Instance High Availability](https://learn.microsoft.com/en-us/azure/azure-sql/managed-instance/high-availability-sla-local-zone-redundancy?view=azuresql)
- [Service Fabric Reconfiguration](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-concepts-reconfiguration)
