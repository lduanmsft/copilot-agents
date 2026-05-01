---
name: SQLDB Connectivity Investigation
description: Diagnoses Azure SQL Database connectivity issues including login failures, session disconnects, gateway health, XdbHost restarts, and network problems. Uses a triage-first approach.
source: SQLLivesiteAgents/Connectivity
distilled: 2026-05-01
---

# SQLDB Connectivity Investigation

> 登录流: Client → xdbgateway(CR/GW Node) → xdbhost(TR/DB Node) → sqlservr(TR/DB Node)
>
> - **CR** = Connectivity Ring (Gateway 集群, 如 `cr11.eastasia1-a.control.database.windows.net`)
> - **TR** = Tenant Ring (数据库所在集群, 如 `tr9591.southcentralus1-a.worker.database.windows.net`)

## Required Inputs

| Parameter | Source | Example |
|-----------|--------|---------|
| LogicalServerName | User/ICM | `my-server` |
| LogicalDatabaseName | User/ICM | `my-db` |
| StartTime | User/ICM | `2026-01-01 02:00:00` (UTC) |
| EndTime | User/ICM | `2026-01-01 03:00:00` (UTC) |
| KustoClusterUri | execute-kusto-query | `https://sqlazureeas2.kusto.windows.net:443` |
| KustoDatabase | execute-kusto-query | `sqlazure1` |
| AppName | get-db-info | sql_instance_name |
| ClusterName | get-db-info | tenant_ring_name |
| NodeName | get-db-info | DB node |
| deployment_type | get-db-info | GP/BC, ZR/non-ZR |

## Phase 0: Prerequisites

1. **execute-kusto-query**: Resolve DNS → region → Kusto cluster URI + database. NEVER hardcode cluster URIs.
2. **get-db-info**: Retrieve AppName, ClusterName, NodeName, physical_database_id, fabric_partition_id, SLO, deployment_type.

## Phase 1: Triage — Determine Issue Type

Analyze user keywords / ICM title to select diagnostic route:

| Keywords | Route | Confidence |
|----------|-------|------------|
| login failure, connectivity, login error, authentication | `login-failure` | High |
| session disconnect, timeout, connection lost | `session-disconnect` | High |
| GatewayNodeLowLoginSuccessRate | `gateway-node-low-login` | High |
| Control Ring Nodes Unhealthy, 20% of Gateway nodes | `control-ring-unhealthy` | High |
| HasXdbHostRestarts, xdbhost restart | `xdbhost-restart` | High |
| BRAIN detected, Login Success-Rate | `brain-login-alert` | High |
| TCP rejection, high tcp | `xdbhost-tcp-rejections` | High |
| *(default)* | `login-failure` | Low |

## Phase 2: Login Failure Investigation (Steps 2-12)

**Condition**: `route == login-failure`

### Step 2: Determine Login Target

Identify target TR ring and DB node.

- **KQL**: `connectivity-base/kql-livesite.yaml` → `LS-CONN-BASE-04`
- **Also used by**: xdbhost-restart, brain-login-alert

### Step 3: Determine Connectivity Ring

Identify which CR(s) served the login requests.

- **KQL**: `connectivity-base/kql-livesite.yaml` → `LS-CONN-BASE-03`
- Typically 2 CRs per data slice; >2 suggests slice migration
- Compare TotalLogins vs LoginWithError between CRs

### Step 4: Check Login Outage Records

Check if any outage is recorded for this server/database.

- **KQL**: `connectivity-base/kql-livesite.yaml` → `LS-CONN-BASE-01`

### Step 5: Determine Connection Type

Identify Proxy/Redirect, Public/Private/Service Endpoint.

- **KQL**: `connectivity-base/kql-livesite.yaml` → `LS-CONN-BASE-07`
- Check `proxy_override` vs actual `result` for mismatch
- Private Endpoint + Default policy + Redirect = legacy `redirection_map_id`
- Outdated drivers may force Proxy even when Redirect is configured

### Step 6: Determine Prevailing Error

Screen prevailing errors in MonLogin, determine impact scope.

- **KQL**: `connectivity-base/kql-livesite.yaml` → `LS-CONN-BASE-05` (general screen) + `LS-CONN-BASE-06` (narrow by node)
- Distinguish `is_user_error=true` (customer) from `false` (platform)
- Check `avg_total_time_ms > 4000ms` for delay patterns
- **For error 33155**: MUST check `fedauth_token_wait_time_ms` — if ≈ total_time_ms, client token acquisition is the bottleneck

**Branching**:
- Error 40613/22 → Continue to Step 7 + Step 8 (network analysis)
- Error 17900/25 → Route to session-disconnect (`connectivity-errors/error-17900-state-25/`)
- Error 33155/1 → Continue to Step 7 — even though `is_user_error=true`, need fedauth timing decomposition
- User error only (EXCEPT 33155) → Report as customer-side issue
- System error → Continue to Step 7

### Step 7: Error-Specific Skill Lookup

For each distinct error code and state from Step 6, look up under `connectivity-errors/`:

1. **Exact match**: `connectivity-errors/error-{code}-state-{state}/`
2. **Code-only fallback**: `connectivity-errors/error-{code}/`
3. **Not found**: Document "No specific skill found" and proceed

**Known error skills**:

| Error | State | Description | Action |
|-------|-------|-------------|--------|
| 40613 | 22 | DueToProxyConnextThrottle — GW proxy throttling | Check SNAT (Step 8), network analysis |
| 40613 | 81 | IPv6 prefix mismatch on PaaSv2 clusters | 3 KQL (CONN81-100/200/300) |
| 40613 | 84 | Proxy connect timeout — SNIOpen failure | 6 KQL chain (Q100-Q600), network analysis mandatory |
| 40613 | 10 | CantFindRequestedInstance — instance not found | 5 KQL (verify node, GW switch, SF notification, format, health) |
| 40613 | 13 | XDBHost login queue lock timeout | → xdbhost-metric-check |
| 40613 | 15 | XDBHost queue timeout (system error) | → xdbhost-metric-check |
| 18456 | *(multi)* | Login failed for user | 6 KQL (state distribution, DB health, login DDL, substep failure, fedauth, DosGuard) |
| 18456 | 113 | DosGuard rejected connection | 6 KQL (confirm, timeline, root cause, apps, fedauth, detail) |
| 17900 | 25 | TDS protocol error — session disconnect | 1 KQL (connection trace) |
| 26078 | 15 | XDBHost queue timeout | → xdbhost-metric-check |
| 33155 | 1 | **AAD Login Timeout** — Gateway waiting for client fedauth token | Check `fedauth_token_wait_time_ms` vs `total_time_ms`. TSG: ENTRA0010 |
| 40532 | 150 | VNET firewall rule rejected login | 3 KQL (pattern, timeline, same-VNET comparison) |
| 47073 | 172 | Deny Public Network Access (DPNA) | 3 KQL (rejection pattern, endpoint config, intermittent check) |

### Step 8: Connectivity Ring Health Check

Run full CR health check.

- **KQL**: `connectivity-base/connectivity-ring-health/kql-livesite.yaml` (GW1100-GW1130)

| Query | Name | When |
|-------|------|------|
| GW1100 | SNAT Port Exhaustion | Always; mandatory if 40613/22. Requires `azslb.kusto.windows.net` |
| GW1110 | GW Process Restart Detection | Always |
| GW1111 | GW Code Package Version | Always |
| GW1112 | GW Deployment Traces | Always |
| GW1114 | GW Process Restart Event (XE) | If restart detected |
| GW1116 | GW Process Restart Duration | If restart detected |
| GW1117 | Node Repair Tasks | Always |
| GW1120 | AliasDB SF App Health | Always |
| GW1121 | AliasDB Partition Event | If AliasDB issue suspected |
| GW1122 | Node Health Events | Always |
| GW1123 | Alias Cache Refresh Latency | P90 > 1000ms = attention |
| GW1130 | DNS Cache Errors | Always |

**Network analysis trigger** (if any of these found → run determine-sql-node + access-eagleeye):
- Error 40613/22 or 40613/84 or 26078
- `lookup_state` 10060 (TCP timeout)
- SNAT port exhaustion (GW1100)
- ProxyOpen timeouts > 5000ms

### Step 9: DB Node Health Check

Check infrastructure health on the DB node(s). ALL 8 queries are MANDATORY:

| Query | Check |
|-------|-------|
| NH100 | Locate database node(s) |
| NH200 | SF node state changes |
| NH210 | Node health issues |
| NH300 | MonSQLInfraHealthEvents (extended: -12h to +24h) |
| NH400 | Bugcheck events |
| NH500 | Node up/down in WinFabLogs |
| NH600 | Node repair tasks |
| NH700 | RestartCodePackage actions |

### Step 10: XDBHOST Health Check

- **KQL**: `connectivity-utilities/xdbhost-metric-check/kql-livesite.yaml` (6 queries)
- TCP rejection, SSL API time, login volume, LSASS+XdbHost CPU, process restart, automation actions

### Step 11: App Health Check (sqlservr)

- **KQL**: `connectivity-utilities/app-health/kql-livesite.yaml` (AH100-AH305)

| Query | Name | Note |
|-------|------|------|
| AH305 | Known Warning Pattern Aggregation | **Run FIRST**. 8 categories: I/O_slow, Memory_pressure, Deadlock, StackDump, Crash, IO_error, Long_recovery, Connectivity_issue |
| AH305-pre | Pre-Window Check | Compare 2h before incident → chronic vs acute |
| AH100 | Process ID Change Detection | sqlservr restart |
| AH200 | LoginOutages Audit | |
| AH210 | MonNonPiiAudit Trail | |
| AH300 | Raw Messages | Drill-down only after AH305 finds a pattern |

### Step 12: Failover / Availability Cross-Check

Cross-check if login failures are a consequence of failover/availability events. If failover found, treat login failure as secondary symptom.

---

## Branch A: XdbHost Restart (Step 20)

**Condition**: `route == xdbhost-restart`
**KQL**: `connectivity-scenarios/xdbhost-restart/kql-livesite.yaml` (XR100-XR700)
**Error cascade**: State 12 → 44 → 10 → 13 → 126 → 22

1. **XR100**: Confirm restart — detect `process_id` change in MonXdbhost. No change → reroute to login-failure.
2. **XR200**: Classify trigger — check MonXdbhost logs for fail/stuck patterns
3. **XR300**: Check automation — MonNonPiiAudit for KillProcess/DumpProcess
4. **XR400/XR410**: Error distribution — separate user errors (pre-restart) from restart errors. If user errors >> system errors before restart → customer error flood triggered automation.
5. **XR600**: Login volume — > 2500/min = extremely high, amplifies restart impact
6. **XR700**: Self-mitigation — verify SuccessCount resumes, RestartErrors drop to 0

## Branch B: Session Disconnect (Step 30)

**Condition**: `route == session-disconnect`
**KQL**: `connectivity-scenarios/session-disconnect/kql-livesite.yaml` (SD-01, SD-02)

1. **SD-01**: Disconnect events summary — top error/state by count
2. **SD-02**: Connection trace — trace top 3 `connection_peer_id`s end-to-end. If dominant error is 17900/25 → route to `connectivity-errors/error-17900-state-25/`

**Correlation**: Gateway↔Backend via `peer_activity_id + peer_activity_seq`; XdbHost↔sqlserver via `connection_peer_id`

**MUST output**: Suggest client-side networking trace + verify end-to-end network path (NVA, Zscaler, etc.)

## Branch C: Gateway Node Low Login Success Rate (Step 40)

**Condition**: `route == gateway-node-low-login`
**KQL**: `connectivity-scenarios/gateway-node-low-login-success-rate/kql-livesite.yaml` (GNLSR100-GNLSR900)

1. Scope assessment (GNLSR100/110) — per-node success rate; isolated vs multi-node
2. Known issues (GNLSR200/210/220/230) — Trident, AliasDB cache backoff, SF behavior change
3. Error distribution (GNLSR300/310/320) — top errors, server-level breakdown
4. Error-specific skills (per Step 7)
5. SNAT check (GNLSR400) — if 40613/22 found
6. Redirector & AliasDB health (GNLSR600-640)
7. GW process health (GNLSR700-730)
8. Deployment check (GNLSR800/810)
9. Impact assessment (GNLSR900)

## Branch D: Control Ring Nodes Unhealthy (Step 50)

**Condition**: `route == control-ring-unhealthy`
**KQL**: `connectivity-scenarios/control-ring-nodes-unhealthy/kql-livesite.yaml` (CRNU100-CRNU500)

1. Scope (CRNU100/110) — count unhealthy nodes (≥20% threshold)
2. Common patterns (CRNU200/210) — deployment, GW process restarts, DR drill
3. Health signals per node (CRNU300/310) — LSASS CPU >50%, TCP rejections >150/sec + handles >600K
4. Auto-mitigation (CRNU400) — healthmanagesvc/SqlRunner actions
5. Impact (CRNU500)

**Delegation**: Login success rate → Branch C; LSASS → Performance/LSASS; TCP rejections → Branch E; GW instability → gateway-health-and-rollout

## Branch E: XdbHost High TCP Rejections (Step 60)

**Condition**: `route == xdbhost-tcp-rejections`
**KQL**: `connectivity-scenarios/xdbhost-high-tcp-rejections/kql-livesite.yaml` (TR100-TR900)

1. Confirm TCP rejections (TR100) — >50/sec = significant
2. LSASS stress (TR200) — >50% = stress, >100% = severe
3. Crash loop (TR300) — >10 process IDs in 2h = severe
4. Dump activity (TR400) — Stalled IOCP Listener → SqlDumpExceptionHandler cycle
5. Automation actions (TR500)
6. Login volume by instance (TR600/610) — >100K from single instance in 2h = very high
7. Instance resource stats (TR700) — max_worker_percent=100% or max_session_percent=100%
8. TCP port stats (TR800) — AvailableDynamicPortsPercentage < 95%

## Branch F: BRAIN Login Alert (Step 70)

**Condition**: `route == brain-login-alert`
**KQL**: `connectivity-scenarios/brain-low-login-success-rate/kql-livesite.yaml` (BRAIN-01/02)

1. Region to Kusto cluster (LS-CONN-BASE-08)
2. CR system error rate (BRAIN-01) — SysErrRate > 1% = significant
3. Error/state with TR drill (BRAIN-02) — top errors, impacted CR nodes, target TR rings
4. Continue with login-failure Step 6+ for top errors

**Mandatory outputs**: Drill Calendar, Service Health Dashboard, top 2 LB health metrics, top 2 EagleEye links

---

## Utilities (on-demand)

| ID | Name | KQL | Trigger |
|----|------|-----|---------|
| UTIL-01 | LoadBalancer VIP Availability | `connectivity-utilities/loadbalancer-health/` | LB health check or BRAIN alert |
| UTIL-02 | LoadBalancer Dashboard URLs | `connectivity-utilities/loadbalancer-health/` | LB problem (availability < 90) |
| UTIL-03 | DB Node CPU Usage (VM-level) | `connectivity-utilities/cpu-usage-check/` | Node CPU investigation |
| UTIL-04 | SQL Node to VM Mapping | `connectivity-utilities/determine-sql-node/` | Network analysis or EagleEye |

## Route → Steps Mapping

| Route | Steps | Description |
|-------|-------|-------------|
| login-failure | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | Full login failure investigation (12 steps) |
| session-disconnect | 2, 30 | Session disconnect analysis |
| xdbhost-restart | 2, 20 | XdbHost restart diagnosis |
| gateway-node-low-login | 40 | GW node low login success rate (self-contained) |
| control-ring-unhealthy | 50 | Cluster-level unhealthy nodes (delegates to node-level) |
| xdbhost-tcp-rejections | 60 | TCP rejections on DB node |
| brain-login-alert | 2, 3, 70, 8 | Region-level BRAIN SLI alert |
