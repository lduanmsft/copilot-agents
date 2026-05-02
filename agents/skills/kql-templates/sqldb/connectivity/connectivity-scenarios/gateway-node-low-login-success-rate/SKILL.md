---
name: gateway-node-low-login-success-rate
description: 'Diagnose Gateway node low login success rate incidents triggered by Geneva monitor `SQLConnectivity-GatewayNodeLowLoginSuccessRate`. Checks if the issue is isolated to one node or extends to other nodes, investigates known issues, analyzes error distributions, SNAT exhaustion, AliasDB/redirector health, and GW process state. Delegates to login-failure skill for error-specific deep dives. Use when ICM title contains "Gateway node low login success rate", "GatewayNodeLowLoginSuccessRate", or "low login success rate" on a Gateway node.'
---

# Gateway Node Low Login Success Rate

Diagnose incidents where a Gateway node in a Control Ring reports low login success rate. These incidents are triggered by Geneva monitor `SQLConnectivity-GatewayNodeLowLoginSuccessRate`.

## Overview

When a Gateway node's login success rate drops below the threshold, the Geneva monitor fires a node-level alert. The investigation must:
1. Confirm whether the issue is isolated to the alerted node or extends to other nodes
2. Short-circuit on known issues
3. Identify the prevailing errors
4. Delegate to error-specific skills for deep analysis

## Required Information

**Supported inputs:** Provide an ICM incident ID **or** the following direct parameters:

### From User or ICM:
- **ClusterName** (Control Ring FQDN) — e.g., `cr6.chinanorth2-a.control.database.chinacloudapi.cn`
- **NodeName** (affected GW node) — e.g., `_GW_10`
- **StartTime** (UTC)
- **EndTime** (UTC)

### Optional (used for delegated deep-dives):
- **LogicalServerName** — e.g., `myserver.database.windows.net`
- **DatabaseName** — e.g., `mydb`

### From `.github/skills/Common/execute-kusto-query/SKILL.md`:
- **kusto-cluster-uri**
- **kusto-database**
- **region**

**Note**: The calling agent should use the `.github/skills/Common/execute-kusto-query/SKILL.md` skill before invoking this skill.

## Workflow

### Step 1: Parse Geneva Alert Context & Generate Links

**1a.** Extract ClusterName, NodeName, and MonitorGUID.

**Primary source — CorrelationId:** Node-level alerts have 4 segments: `Region→Cluster→Node→Monitor`. Extract NodeName from segment 3.

**Secondary source — ICM Title:** The title contains ClusterName and NodeName inline: `Node {NodeName} on {ClusterName} is unhealthy - Gateway node low login success rate`. Use this to **validate** CorrelationId extraction, or as **fallback** if CorrelationId parsing fails.

**1b.** Generate Geneva Health link — **MANDATORY OUTPUT for DRI.**

Read and follow `.github/skills/Connectivity/connectivity-utilities/access-geneva-health/SKILL.md` using the CorrelationId, occuringLocation.datacenter, and CreatedDate from the ICM incident.

**Required inputs for the skill:**

| Input | Source | Example |
|-------|--------|---------|
| `correlationId` | ICM `CorrelationId` field | `HH-SQLConnectivity-Node/Central US EUAP->cr18.useuapcentral1-a.control.database.windows.net->_GW_13->4ce9db6b-b684-45ea-a7ca-1fdb2b6a8a96` |
| `occuringLocation.datacenter` | ICM `occuringLocation.datacenter` field | `Central US EUAP` |
| `createdDate` | ICM `CreateDate` field | `2026-04-17T20:55:52.213Z` |

**Verification:** After generating the link, output it in a clearly visible block:

```
🔗 Geneva Health Link (for DRI):
{generated_url}
```

If the link cannot be generated (missing CorrelationId, not a Geneva alert, malformed data), output:
```
🚩 Geneva Health link could NOT be generated. Reason: {reason}
Manual fallback: Open https://portal.microsoftgeneva.com/ and search for the cluster/node manually.
```

**1c.** Output the following dashboard links:
- **Global Health**: `https://portal.microsoftgeneva.com/s/B0A2575D`
- **Drill Calendar**: `https://global.azure.com/drillmanager/calendarView`

---

### Step 2: Scope Assessment — Confirm Node Isolation

Determine if the problem is isolated to the alerted node or if other nodes in the cluster are also affected.

**Execute query:** GNLSR100 from [references/queries.md](references/queries.md)

**Analysis:**

| Condition | Classification | Recommended Action |
|-----------|---------------|-------------------|
| Only 1 node < 95% success rate | **Node-isolated** | Continue investigation focused on the affected node |
| Multiple nodes < 95% | **Multiple nodes affected** | 🚩 Issue extends beyond this node — continue investigation but note broader impact for escalation |

**Execute query:** GNLSR110 from [references/queries.md](references/queries.md) to count distinct impacted servers.

---

### Step 3: Check Known Issues

Run these checks in order. If any match, output the finding and recommended action. **Do not stop** — continue the investigation but note the match.

#### 3a: Trident Testing in Canary Rings

**Execute query:** GNLSR200 from [references/queries.md](references/queries.md)

**Match criteria:** Significant portion of 40613/4 failures belong to `TridentSqlResourceGroup`.

**If matched:** 🚩 "Known issue: Trident testing in canary rings. Consider transferring to Synapse DW / Client Experiences team."

#### 3b: SQL Alias Failover + Cache Backoff

**Execute query:** GNLSR210 from [references/queries.md](references/queries.md)

**Match criteria:** 40613/4 errors with `lookup_error_code = 2147500037` (E_FAIL) skewed to one node.

**If matched:** Also run GNLSR220 to confirm alias cache backoff timer activity.

**Execute query:** GNLSR220 from [references/queries.md](references/queries.md)

**If both match:** 🚩 "Known issue: SQL Alias failover + Cache backoff. Mitigation: Kill/restart GW process on the affected node, or wait for cache backoff timer to expire."

#### 3c: SF Version Behavior Change

**Execute query:** GNLSR230 from [references/queries.md](references/queries.md)

**Match criteria:** 40613/4 errors where `lookup_state` contains `SERVICE_FABRIC-DOES-NOT_EXISTS` during a deployment window.

**If matched:** 🚩 "Known issue: SF version behavior change. Self-mitigates after deployments finish."

---

### Step 4: Error Distribution on Affected Node(s)

**Execute query:** GNLSR300 from [references/queries.md](references/queries.md) — error/state distribution on the affected node, separating system vs user errors.

**Analysis:**
- If PG/MySQL `AppTypeName` is top contributor → "🚩 Transfer to RDBMS Open Source queue."
- Identify the top 3-5 system error codes and states.

**🚩 AliasDB Pattern Detection:**
If the prevailing error is **40613/4** with `state_desc = WinFabOrSqlAliasLookupFailure` and `lookup_state` in (`DATABASE_ALIAS`, `LOGICAL_MASTER_ALIAS`, `SERVICE_ENDPOINT`):
- This indicates **AliasDB lookup failures** — the GW node cannot resolve database aliases.
- **Prioritize Step 7** (Redirector & AliasDB Health) — especially sub-steps 7a, 7b, and 7e (AliasDB SF app health).
- Check for **concurrent AliasDB-related incidents** on the same cluster (search ICM for the ClusterName).
- Check for **credential/secret rotation** timing that may correlate with the failure window.

**Execute query:** GNLSR310 from [references/queries.md](references/queries.md) — server-level breakdown with target rings for system errors.

**Analysis:**
- Determine if errors concentrate on specific logical servers / TR rings / DB nodes.
- If errors are spread across many servers → infrastructure-level issue.
- If errors concentrate on one server → customer-specific or DB-node issue.
- If 40613/4 errors have empty `instance_name` / `TargetTRRing` → confirms GW never reached backend (AliasDB resolution failed before routing).

---

### Step 5: Delegate to login-failure Skill for Error-Specific Deep Dives

**5a. Extract most impacted servers/databases:**

**Execute query:** GNLSR320 from [references/queries.md](references/queries.md) — returns the top 5 most impacted `logical_server_name` + `database_name` pairs by system error count on the affected node.

Use the **top result** (row 1) as parameters for error-specific skills:
- `LogicalServerName` ← `logical_server_name` from GNLSR320 row 1
- `LogicalDatabaseName` ← `database_name` from GNLSR320 row 1
- `ConnectivityRingName` ← `{ClusterName}` from Step 1

If GNLSR320 returns empty results (e.g., AliasDB failures where GW never reached backend and `logical_server_name` is empty), use the `.github/skills/Common/get-db-info/SKILL.md` skill with the extracted server/database to obtain `AppName`, `ClusterName` (tenant ring), and other DB environment variables needed by error-specific skills.

**5b. Delegate to error-specific skills:**

For each distinct non-user error code and state found in Step 4, delegate to the `.github/skills/Connectivity/connectivity-scenarios/login-failure/SKILL.md` skill's error-specific workflow.

Follow `.github/skills/Connectivity/connectivity-scenarios/login-failure/SKILL.md`, starting from **Task 7: Analyze the error**, using the error-specific skill lookup convention:

1. **Exact match**: `.github/skills/Connectivity/connectivity-errors/error-{code}-state-{state}/SKILL.md`
2. **Code-only fallback**: `.github/skills/Connectivity/connectivity-errors/error-{code}/SKILL.md`
3. **No skill found**: Document "No specific skill found for Error {code} State {state}."

**Skills that work without server/database context** (infrastructure-level only):
- `error-26078-state-15`, `error-40613-state-15`, `error-40613-state-13` — these delegate to `xdbhost-metric-check` which uses `ClusterName` + `NodeName` only.

Execute ALL steps in each matched error-specific skill.

**Output:**

| Error | State | Skill Path | LogicalServerName Used | Steps Completed | Key Findings |
|-------|-------|------------|----------------------|-----------------|--------------|
| {code} | {state} | error-{code}-state-{state}/ | {from GNLSR320} | N/N ✅ | ... |

---

### Step 6: Check SNAT Port Exhaustion

**Trigger:** Only execute if Error 40613 State 22 (DueToProxyConnectThrottle) was found in Step 4.

**Execute query:** GNLSR400 from [references/queries.md](references/queries.md)

> **Note:** If the user gets a Kusto permission error for `azslb.kusto.windows.net`, notify them to request access from `https://idwebelements.microsoft.com/GroupManagement.aspx?Group=AznwKustoReader&operation=join`.

**If SNAT events found:** Cross-reference with `.github/skills/Connectivity/connectivity-scenarios/understand-snat/SKILL.md` for context.

Also execute:
- "determine-sql-node" skill (`.github/skills/Connectivity/connectivity-utilities/determine-sql-node/SKILL.md`) — map nodes to VMs
- "access-eagleeye" skill (`.github/skills/Connectivity/connectivity-utilities/access-eagleeye/SKILL.md`) — generate network analysis links

---

### Step 7: Redirector & AliasDB Health

**Execute queries from** [references/queries.md](references/queries.md):

| Sub-step | Query | What it checks |
|----------|-------|----------------|
| 7a | GNLSR600 | Alias cache ODBC failures per node (`sql_alias_odbc_failure`) |
| 7b | GNLSR610 | Alias cache refresh activity |
| 7c | GNLSR620 | Fabric resolution failures (`fabric_end_resolve` with result != 0) |
| 7d | GNLSR630 | Lookup retries (resolution instability) |
| 7e | GNLSR640 | AliasDB SF application health state |

**Analysis:**
- High ODBC failures on the affected node → AliasDB connectivity issue.
- Fabric resolution failures → Backend resolution problem.
- Lookup retry storms → Resolution instability.
- AliasDB app health state not "Ok" → AliasDB infrastructure issue; check replicas.

**🚩 If AliasDB lookup failures detected (Step 4):**
- Sub-step 7e is **mandatory** — verify AliasDB SF app health.
- If AliasDB is unhealthy: Check AliasDB replicas from SFE, check for secret/credential rotation, check for concurrent AliasDB incidents on the cluster.
- If AliasDB is healthy but ODBC failures persist on one node: likely node-local issue (stale cache, process state) → restart GW process.

---

### Step 8: GW Process Health

**Execute queries from** [references/queries.md](references/queries.md):

| Sub-step | Query | What it checks |
|----------|-------|----------------|
| 8a | GNLSR700 | GW process restarts on affected node (process_id changes) |
| 8b | GNLSR710 | GW process restart events (XE session start) |
| 8c | GNLSR720 | GW process restart gap duration |
| 8d | GNLSR730 | Node-specific resource usage (memory, threads, cache) |

**Analysis:**
- Multiple process restarts → GW process instability; check for dumps.
- High memory / thread count → Resource pressure on the node.
- Long restart gap → Extended unavailability window.

---

### Step 9: Check Deployment / Maintenance

**Execute queries from** [references/queries.md](references/queries.md):

| Sub-step | Query | What it checks |
|----------|-------|----------------|
| 9a | GNLSR800 | GW deployment traces |
| 9b | GNLSR810 | Repair tasks on nodes |

**Output:**
- 📋 Drill Calendar: `https://global.azure.com/drillmanager/calendarView`
- Flag if deployment or repair activity correlates with the incident time window.

---

### Step 10: Impact Assessment

**Execute query:** GNLSR900 from [references/queries.md](references/queries.md) — count distinct impacted servers and subscriptions.

**Output:**
- Number of distinct logical servers with system errors
- Number of distinct subscriptions impacted

---

### Step 11: Mitigation & Escalation Decision Tree

Based on findings from Steps 2-10, output the applicable mitigation path:

| Condition | Recommendation |
|-----------|---------------|
| **Multiple nodes affected** (Step 2) | 🚩 Issue extends beyond this node — escalate if > 100 servers impacted |
| **Known issue: Trident** (Step 3a)| Transfer to Synapse DW / Client Experiences |
| **Known issue: AliasDB cache backoff** (Step 3b) | Kill/restart GW process on affected node |
| **Known issue: SF behavior** (Step 3c) | Self-mitigates after deployment finishes |
| **SNAT exhaustion** (Step 6) | Identify traffic source; consider GW process restart |
| **AliasDB lookup failures** (Step 4 + 7) | Check AliasDB replicas health from SFE; validate secret/credential rotation; restart GW process on affected node |
| **AliasDB ODBC failures** (Step 7) | Check AliasDB replicas health from SFE; restart GW process |
| **GW process instability** (Step 8) | Investigate dumps; restart GW process |
| **Deployment in progress** (Step 9) | Wait for deployment to complete |
| **Node-isolated, no clear root cause** | Kill GW process on the affected node; monitor recovery |

**Visual Decision Tree:**

```
                          ┌─────────────────────┐
                          │  Start: Steps 2-10   │
                          │  findings collected   │
                          └──────────┬────────────┘
                                     │
                          ┌──────────▼────────────┐
                          │  Multiple nodes     │
                          │  affected (Step 2)? │
                          └──┬───────────────────┬─┘
                          YES│                   │NO
                   ┌────────▼────────┐    ┌──────▼──────────────┐
                   │  🚩 Escalate    │    │  Known Issue (S3)?   │
                   │  if > 100       │    └──┬──────────────┬───┘
                   │  servers        │    YES│              │NO
                   └───────┬─────────┘ ┌────▼──────────┐   │
                           │           │  Match type?   │   │
                           │           └──┬──┬──┬──┬───┘   │
                           │              │  │  │  │       │
                           │              │  │  │  │  ┌────▼────────────┐
                           │              │  │  │  │  │ Error pattern?  │
        ┌──────────────────┘              │  │  │  │  └──┬──┬──┬──┬────┘
        │          ┌─────────────────────┘  │  │  │       │  │  │  │
        │          │ Trident (3a)           │  │  │       │  │  │  │
        │   ┌──────▼──────────────┐        │  │  │       │  │  │  │
        │   │ Transfer to Synapse │        │  │  │       │  │  │  │
        │   │ DW / Client Exp.    │        │  │  │       │  │  │  │
        │   └─────────────────────┘        │  │  │       │  │  │  │
        │          ┌───────────────────────┘  │  │       │  │  │  │
        │          │ AliasDB backoff (3b)     │  │       │  │  │  │
        │   ┌──────▼──────────────┐          │  │       │  │  │  │
        │   │ Kill/restart GW     │          │  │       │  │  │  │
        │   │ process on node     │          │  │       │  │  │  │
        │   └─────────────────────┘          │  │       │  │  │  │
        │          ┌─────────────────────────┘  │       │  │  │  │
        │          │ SF behavior (3c)           │       │  │  │  │
        │   ┌──────▼──────────────┐             │       │  │  │  │
        │   │ Wait for deployment │             │       │  │  │  │
        │   │ to complete         │             │       │  │  │  │
        │   └─────────────────────┘             │       │  │  │  │
        │          ┌────────────────────────────┘       │  │  │  │
        │          │ AliasDB lookup (3d)                │  │  │  │
        │   ┌──────▼──────────────────┐                │  │  │  │
        │   │ Check AliasDB replicas  │                │  │  │  │
        │   │ + secret rotation       │                │  │  │  │
        │   │ Restart GW if isolated  │                │  │  │  │
        │   └─────────────────────────┘                │  │  │  │
        │                                              │  │  │  │
        │      ┌───────────────────────────────────────┘  │  │  │
        │      │ SNAT 40613/22 (Step 6)                   │  │  │
        │   ┌──▼──────────────────┐                       │  │  │
        │   │ Identify traffic    │                       │  │  │
        │   │ source; restart GW  │                       │  │  │
        │   └─────────────────────┘                       │  │  │
        │      ┌──────────────────────────────────────────┘  │  │
        │      │ AliasDB ODBC (Step 7)                       │  │
        │   ┌──▼──────────────────┐                          │  │
        │   │ Check AliasDB reps  │                          │  │
        │   │ from SFE; restart   │                          │  │
        │   └─────────────────────┘                          │  │
        │      ┌─────────────────────────────────────────────┘  │
        │      │ GW instability (Step 8)                        │
        │   ┌──▼──────────────────┐                             │
        │   │ Investigate dumps;  │                             │
        │   │ restart GW process  │                             │
        │   └─────────────────────┘                             │
        │      ┌────────────────────────────────────────────────┘
        │      │ Deployment (Step 9)
        │   ┌──▼──────────────────┐
        │   │ Wait for deployment │
        │   │ to finish           │
        │   └─────────────────────┘
        │
        │   No clear root cause:
        ┌──▼──────────────────────┐
        │ Kill GW process on the  │
        │ affected node; monitor  │
        │ recovery                │
        └─────────────────────────┘
```

### Step 12: Mitigation Procedure

Once the decision tree in Step 11 identifies the mitigation path, follow this procedure.

#### 12a: Pre-Check — Did Automation Already Mitigate?

Before recommending manual action, check if the issue has self-resolved:

1. Re-run **GNLSR100** with a time window covering the last 15 minutes.
2. If the affected node's `LoginSuccessRate` is now > 99% → **issue self-mitigated**, monitor only.
3. Check ICM for automation actions (SqlRunner DumpProcess/KillProcess on xdbgateway).

If automation already acted AND success rate recovered → **no manual action needed**. Document the automation action and close.

#### 12b: Manual Mitigation — GW Process Restart

**When:** Node-isolated issue, AliasDB cache backoff, ODBC failures, no clear root cause.

**Pre-mitigation:**
- Confirm the issue is node-isolated (only one node affected in GNLSR100)
- Confirm no deployment is in progress (GNLSR800)

**Steps:**
1. Open DSConsole for the cluster: `https://dsconsole.trafficmanager.net/cluster/{ClusterName}`
2. Navigate to the affected node → Gateway process
3. Issue a process kill on `xdbgateway` process
4. The process will automatically restart via Service Fabric

**Post-mitigation verification:**
- Wait 2-3 minutes for GW process to restart and stabilize
- Re-run **GNLSR100** to confirm success rate recovery on the affected node
- Verify no new errors are appearing on the node

#### 12c: Post-Mitigation Verification

After any mitigation action:

1. Re-run **GNLSR100** — confirm `LoginSuccessRate` > 99% on affected node(s)
2. Re-run **GNLSR900** — confirm no new system errors are accumulating
3. Monitor for 15 minutes to ensure stability
4. Update ICM with mitigation action taken and verification results

---

## Execution Verification Checklist

Before providing conclusions, output this table:

```
## ✅ Gateway Node Low Login Success Rate — Execution Verification

| Step | Description | Queries Run | Status |
|------|------------|-------------|--------|
| 1a | Parse Geneva Alert | ClusterName, NodeName extracted | ⬜ |
| 1b | 🔗 Geneva Health Link | Link generated and displayed | ⬜ |
| 2 | Scope Assessment | GNLSR100, GNLSR110 | ⬜ |
| 3 | Known Issues Check | GNLSR200, GNLSR210, GNLSR220, GNLSR230 | ⬜ |
| 4 | Error Distribution | GNLSR300, GNLSR310 | ⬜ |
| 5 | Error-Specific Skills | Per login-failure Task 7 | ⬜ |
| 6 | SNAT Check | GNLSR400 (if 40613/22 found) | ⬜ |
| 7 | Redirector & AliasDB | GNLSR600-630 | ⬜ |
| 8 | GW Process Health | GNLSR700-730 | ⬜ |
| 9 | Deployment / Maintenance | GNLSR800-810 | ⬜ |
| 10 | Impact Assessment | GNLSR900 | ⬜ |
| 11 | Mitigation Decision | Decision tree applied | ⬜ |
| 12 | Mitigation Procedure | Pre-check, manual steps | ⬜ |
```
