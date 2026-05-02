---
name: xdbhost-high-tcp-rejections
description: Diagnose Azure SQL Database connectivity issues caused by XDBHost high TCP rejections on a node. Use when ICM title or Health Hierarchy alert contains "XDBHost high TCP rejections". These are node-level alerts indicating the XdbHost process is rejecting incoming TCP connections, typically accompanied by crash loops, LSASS stress, ConnectionCloseDumps, and Stalled IOCP Listener dumps. Accepts either ICM ID or direct parameters (cluster name, node name, time window). Executes Kusto queries via Azure MCP to analyze telemetry.
---

# XDBHost High TCP Rejections Diagnosis

Investigate node-level Health Hierarchy alerts where XdbHost is rejecting incoming TCP connections. These incidents present as `XDBHost high TCP rejections` alerts and are caused by the XdbHost process entering a crash-dump-restart loop, often driven by LSASS CPU stress or high connection volume. The crash loop produces `Stalled IOCP Listener` and `SqlDumpExceptionHandler` dumps, which further degrade the node.

## Overview

When XdbHost enters a high TCP rejection state on a DB node, the typical sequence is:

1. **LSASS stress** — Elevated LSASS privileged CPU time (often > 100%) indicates TLS/authentication pressure on the node
2. **XdbHost stalls** — IOCP listener threads stall waiting for completions, triggering `Stalled IOCP Listener` dumps
3. **Crash loop** — Dumps cause XdbHost to crash (`SqlDumpExceptionHandler`), restart, and immediately re-encounter the same conditions
4. **TCP rejections** — Winsock BSP Rejected Connections/sec spikes because XdbHost is unavailable or cycling too fast to accept connections
5. **Automation response** — SqlRunner issues `DumpProcess` + `KillProcess` actions targeting `xdbhostmain` to attempt recovery
6. **Mitigation** — Either the crash loop self-resolves (LSASS pressure subsides) or a DB failover is performed

The goal is to determine: (a) what caused the LSASS/node stress, (b) how many XdbHost restarts occurred, (c) what automation actions were taken, (d) which databases/instances were impacted, and (e) whether the issue self-mitigated or required manual failover.

## Required Information

### From User or ICM:
- **ClusterName** (tenant ring name, e.g., `tr6730.southeastasia1-a.worker.database.windows.net`)
- **DBNodeName** (e.g., `_DB_59`)
- **StartTime** (UTC format: `2026-04-04 20:00:00`)
- **EndTime** (UTC format: `2026-04-04 22:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureseas2.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)

### Optional (from ICM or user):
- **LogicalServerName** — if known from ICM discussion or description
- **LogicalDatabaseName** — if known from ICM discussion or description

**Note**: This is a **node-level** alert. ICM often does NOT contain LogicalServerName / LogicalDatabaseName. Extract ClusterName and DBNodeName from the ICM title pattern: `Node {DBNodeName} on {ClusterName} is unhealthy - XDBHost high TCP rejections`.

## Investigation Workflow

**Important**: Output the results from each step as specified. Complete all steps before providing conclusions.

### 0: Generate Geneva Health Monitor Link

Since this is a Health Hierarchy alert, generate a Geneva Health portal link for the DRI using the [access-geneva-health skill](/.github/skills/Connectivity/connectivity-utilities/access-geneva-health/SKILL.md). This provides direct portal access to inspect the monitor state, health timeline, and topology.

**Input**: Pass the ICM `correlationId`, `occuringLocation.datacenter`, and `createdDate` fields to the access-geneva-health skill. Pass StartTime, EndTime, ClusterName (FQDN from ICM), and NodeName to the [access-dataexplorer-dashboard skill](/.github/skills/Connectivity/connectivity-utilities/access-dataexplorer-dashboard/SKILL.md) (select the **XDBHost** page).

**Output**: Include both links as clickable markdown in the report:

🔗 **Portal Links**
- [Geneva Health Monitor]({generated_geneva_url}) — Health Hierarchy view for the impacted node/monitor
- [Data Explorer Dashboard — XDBHost]({generated_dataexplorer_url}) — XDBHost metrics for the node and time window

### 1: Confirm TCP Rejections on the Node

Query `MonCounterOneMinute` for `\\Microsoft Winsock BSP\\Rejected Connections/sec` to confirm the alert is valid and determine the rejection window.

**Execute query:** TR100 from [references/queries.md](references/queries.md)

**What to look for:**
- Sustained non-zero `MaxVal` values confirm TCP rejections
- 🚩 MaxVal > 50/sec indicates significant rejection pressure
- Identify the start and end of the rejection window

### 2: Check LSASS and XDBHost CPU Stress

Query `MonCounterOneMinute` for LSASS privileged time to determine if authentication pressure is driving the issue.

**Execute query:** TR200 from [references/queries.md](references/queries.md)

**What to look for:**
- Normal: LSASS % Privileged Time < 10%
- 🚩 > 50% indicates authentication stress; 🚩 sustained > 100% correlates directly with XdbHost stalls
- Correlate LSASS elevation window with TCP rejection window from Step 1
- **If LSASS elevated**: use the `aka.ms/sqlconnlsi` dashboard (XDBHost(Worker) page) to check AcceptSecurityContext thread count and avg SSL API time for deeper analysis

### 3: Confirm XdbHost Crash Loop

Query `MonXdbhost` to detect repeated process_id changes, confirming a crash-restart loop rather than a single restart.

**Execute query:** TR300 from [references/queries.md](references/queries.md)

**What to look for:**
- Multiple process_id values (> 3) = crash loop, not a single restart
- 🚩 > 10 process IDs in a 2-hour window = severe crash loop
- Short-lived processes (< 5 minutes each) indicate the process crashes shortly after starting
- Record the total number of restarts and the overall crash loop duration

**Decision:**
- **1-2 process IDs** → Single restart, consider rerouting to `xdbhost-restart` skill
- **3+ process IDs** → Crash loop confirmed, continue with this skill

### 4: Analyze Dump Activity

Query `MonSqlDumperActivity` to identify the dump types driving the crash loop.

**Execute query:** TR400 from [references/queries.md](references/queries.md)

**What to look for:**
- **Stalled IOCP Listener** dumps — indicate XdbHost IOCP threads are blocked, often due to LSASS contention
- **SqlDumpExceptionHandler** dumps — indicate XdbHost crashed after a dump was triggered
- **Stack traces** containing `SocketDupInstance::DestroyConnectionObjects_v2` — confirms connection close path issues
- 🚩 Alternating pattern of `Stalled IOCP Listener` → `SqlDumpExceptionHandler` confirms the dump-crash-restart cycle
- Count total dumps and classify by DumpErrorText

### 5: Check Automation Actions

Query `MonNonPiiAudit` for automation or user actions on the node during the incident.

**Execute query:** TR500 from [references/queries.md](references/queries.md)

**What to look for:**
- `DumpProcess` targeting `xdbhostmain` — SqlRunner triggered a diagnostic dump
- `KillProcess` targeting `xdbhostmain` — SqlRunner killed XdbHost to attempt recovery
- `KillProcess` targeting `sqlservr` — indicates escalation to SQL Server process kill
- Correlate action timestamps with the crash loop timeline from Step 3
- 🚩 Multiple KillProcess actions indicate automated recovery attempts failed

### 6: Identify Impacted Instances and Login Volume

Query `MonLogin` at the node level to understand which instances were impacted and the volume of login traffic.

**Execute query:** TR600 from [references/queries.md](references/queries.md)

**What to look for:**
- One instance dominating login volume may be the root cause of node stress
- 🚩 > 2500 logins/minute per instance = extremely high volume
- Total login count across all instances on the node during the window

**Execute query:** TR610 from [references/queries.md](references/queries.md)

**What to look for:**
- Login volume timeline per XdbHost process_id — shows the crash-restart pattern from the login perspective
- Each process_id series should show a spike then drop (process crash)

### 7: Check Instance Resource Utilization

Query `MonDmRealTimeResourceStats` to determine if resource exhaustion on a specific instance contributed to the crash loop.

**Execute query:** TR700 from [references/queries.md](references/queries.md)

**What to look for:**
- 🚩 `max_worker_percent` at 100% = worker thread exhaustion
- 🚩 `max_session_percent` at 100% = session limit reached
- 🚩 `avg_instance_cpu_percent` > 90% = instance-level CPU exhaustion
- Correlate resource spikes with the LSASS elevation and crash loop timeline

### 8: Check TCP Port Statistics (if available)

Query `AlrWinFabHealthNodeEvent` for TCP port usage on the node.

**Execute query:** TR800 from [references/queries.md](references/queries.md)

**What to look for:**
- `Established_Conn` spike correlating with the incident window
- 🚩 `AvailableDynamicPortsPercentage` < 95% indicates port pressure
- `Bound_Ports` increase may indicate connection accumulation

### 9: Determine Root Cause and Mitigation

Based on evidence collected from all previous steps, classify the root cause.

**Decision tree:**

```
TCP Rejections confirmed (Step 1)
│
├── LSASS elevated? (Step 2)
│   ├── Yes → LSASS stress → XdbHost stall → crash loop
│   │   └── Check if one instance dominates logins (Step 6)
│   │       ├── Yes → High login volume from one DB driving LSASS stress
│   │       └── No → Run Performance/LSASS skill for deeper analysis
│   │             (XStore-driven, ImageStore-driven, Frozen VM, or residual)
│   └── No → Check dumps (Step 4)
│       ├── Stalled IOCP Listener → XdbHost internal stall (not LSASS)
│       └── Other → Escalate for engineering investigation
│
├── Automation took action? (Step 5)
│   ├── KillProcess xdbhostmain → SqlRunner tried to recover
│   └── KillProcess sqlservr → Escalated kill
│
└── How was it mitigated?
    ├── Self-resolved (crash loop stopped) → LSASS pressure subsided
    ├── Manual failover → DB moved off the unhealthy node
    └── Not yet mitigated (crash loop still active / no stable process_id for > 10 min)
        ├── Check Step 5: Did automation (KillProcess on xdbhostmain) already run?
        │   ├── Yes + last process_id stable > 10 min (TR300) → Automation mitigated; monitor
        │   └── Yes + crash loop persists → Proceed to manual mitigation (Step 10)
        ├── No automation action found → Proceed to manual mitigation (Step 10)
        ├── Crash loop < 1 hour → Monitor; SqlRunner may still recover. If no improvement, proceed to Step 10
        ├── Crash loop > 1 hour → Execute Step 10 (XDBHost restart), or recommend failover of impacted DB(s)
        └── Repeated incidents on same node within 7 days → 🚩 Escalate via team-routing skill
```

**After determining root cause, invoke the [team-routing skill](/.github/skills/Common/team-routing/SKILL.md)** to validate the current ICM owning team and generate a transfer recommendation if needed.

### 10: Mitigation (If Incident Not Yet Resolved)

> ⚠️ **Only execute this step if the incident is NOT yet mitigated** (crash loop still active, no stable process_id for > 10 minutes in TR300).

**Pre-check — Did automation already mitigate?**

Review Step 5 (TR500) results:
- If `KillProcess` targeting `xdbhostmain` was found **AND** the last process_id in TR300 has been stable > 10 minutes **AND** TR610 shows login volume returned to normal → **Automation already mitigated**. Note this in the report and monitor for recurrence.
- If `KillProcess` was found but crash loop persists, or no automation action was found → **Proceed with manual mitigation below**.

**Manual Mitigation: Restart XDBHost Process**

> ⚠️ **Impact**: There is only one XDBHost process per node. Killing it affects **all** SQL instances on the node and all connections targeted at them. All databases on the node are momentarily unavailable for new connections (order of seconds) until Service Fabric relaunches xdbhostmain.

**Steps (via DSConsole):**

1. **Collect a process dump first** (skip if dump fails or takes > 1 minute):

```powershell
Get-FabricNode -NodeName {DBNodeName} -NodeClusterName {ClusterName} | Dump-Process -ProcessName xdbhostmain.exe -ApplicationNameUri fabric:/Worker
```

2. **Kill the XDBHost process**:

```powershell
Get-FabricNode -NodeName {DBNodeName} -NodeClusterName {ClusterName} | Kill-Process -ProcessName xdbhostmain.exe -ApplicationNameUri fabric:/Worker
```

3. **Wait 10–15 minutes** for Service Fabric to relaunch XDBHost and connections to stabilize.

**Post-Mitigation Verification:**

- Re-run **TR100** — TCP rejections should drop to 0
- Re-run **TR300** — new process_id should be stable (no further crashes)
- Re-run **TR200** — LSASS % Privileged Time should return to < 10%
- Check Service Fabric Explorer: confirm XDBHost application health is OK under the node's NodeView

If the issue recurs after restart, escalate to manual failover of the impacted database(s) off the unhealthy node.

## Reference

- [knowledge.md](references/knowledge.md) — XdbHost TCP rejection concepts, LSASS stress, dump types
- [principles.md](references/principles.md) — Debug principles, timing thresholds, escalation criteria
- [queries.md](references/queries.md) — All Kusto queries
- [Performance/LSASS skill](/.github/skills/Performance/LSASS/SKILL.md) — Deeper LSASS analysis (6-pattern classification, XStore/ImageStore/Frozen VM correlation, Two-Problem Framework)
- [access-geneva-health skill](/.github/skills/Connectivity/connectivity-utilities/access-geneva-health/SKILL.md) — Generate Geneva Health Monitor portal link from ICM incident data for Health Hierarchy view
- [access-dataexplorer-dashboard skill](/.github/skills/Connectivity/connectivity-utilities/access-dataexplorer-dashboard/SKILL.md) — Generate pre-filled Data Explorer dashboard link for Gateway, XDBHost, or VM Node metrics
- [Kill XDBHost Process TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/xdbhost/high-tcp-rejections-on-xdbhost) — Official TSG for XDBHost restart procedure, triage dashboards (`aka.ms/sqlconnlsi`), and known issues
