---
name: control-ring-nodes-unhealthy
description: 'Diagnose cluster-level Health Hierarchy alerts where ≥20% of Gateway nodes are unhealthy, triggered by Geneva rollup monitor `SQLConnectivity-Cluster-ControRing-Nodes-Unhealthy`. Identifies which nodes are unhealthy, determines which health signal(s) are breaching (login success rate, LSASS stress, TCP rejections, GW process health), checks for cluster-wide patterns (deployment, drill, auto-mitigation), and delegates to node-level skills for deep investigation. Use when ICM title contains "Gateway nodes are unhealthy", "Control Ring Nodes Unhealthy", or "At least 20% of Gateway nodes". Accepts ICM ID or direct parameters (cluster name, time window).'
---

# Control Ring Nodes Unhealthy — Cluster-Level Triage

Diagnose cluster-level Health Hierarchy alerts where ≥20% of Gateway nodes in a Control Ring are unhealthy. These incidents are triggered by Geneva rollup monitor `SQLConnectivity-Cluster-ControRing-Nodes-Unhealthy`.

## Overview

This is a **Geneva Health Rollup Monitor** that aggregates node-level health signals at the cluster level. A Gateway node can become "unhealthy" for multiple reasons — login success rate degradation is the most common, but LSASS CPU stress, TCP rejections, and GW process crashes also contribute. When ≥20% of GW nodes in a cluster are unhealthy, this cluster-level alert fires.

```
┌─────────────────────────────────────────────────────────┐
│  CLUSTER-LEVEL (this monitor)                           │
│  SQLConnectivity-Cluster-ControRing-Nodes-Unhealthy     │
│  Fires when: ≥ 20% of GW nodes are unhealthy           │
└───────────────────────┬─────────────────────────────────┘
                        │ aggregates
    ┌───────────────────▼──────────────────────────────┐
    │  NODE-LEVEL (per GW node health assessment)       │
    │  A node is "unhealthy" if ANY health signal fails  │
    └───────────────────┬──────────────────────────────┘
                        │ health signals
    ┌───────────────────▼──────────────────────────────┐
    │  HEALTH SIGNALS (per-node monitors)               │
    │  ├── Login Success Rate  ← most common            │
    │  │   Monitor: GatewayNodeLowLoginSuccessRate      │
    │  │   Skill: gateway-node-low-login-success-rate   │
    │  ├── LSASS CPU Stress                             │
    │  │   Counter: \Process(Lsass)\% Privileged Time   │
    │  ├── TCP Rejections                               │
    │  │   Skill: xdbhost-high-tcp-rejections           │
    │  └── GW Process Health / Restarts                 │
    │       Skill: gateway-health-and-rollout           │
    └──────────────────────────────────────────────────┘
```

**Critical context:** When this cluster-level incident fires, node-level incidents (e.g., `GatewayNodeLowLoginSuccessRate`) often already exist. This skill's job is to understand the **cluster-wide picture** and delegate to node-level skills for deep investigation.

**Common patterns from real incidents:**
- Common root causes: Azure Disaster Recovery Drill, Upgrade/Deployment in progress
- `healthmanagesvc` may auto-mitigate after ~1 hour of consecutive healthy watchdog reports, but this is not guaranteed — the DRI **must always** complete the full investigation workflow regardless of auto-mitigation expectations

## Required Information

**Supported inputs:** Provide an ICM incident ID **or** the following direct parameters:

### From User or ICM:
- **ClusterName** (Control Ring FQDN) — e.g., `cr6.chinanorth2-a.control.database.chinacloudapi.cn`
- **RegionName** — e.g., `East US 2 EUAP`
- **StartTime** (UTC)
- **EndTime** (UTC)

### From `.github/skills/Common/execute-kusto-query/SKILL.md`:
- **kusto-cluster-uri**
- **kusto-database**
- **region**

**Note**: This is a **cluster-level** alert. The ICM title contains `ClusterName` and `RegionName` but does NOT contain a specific `NodeName`. The CorrelationId has **3 segments** (Region→Cluster→Monitor), unlike node-level alerts which have 4 segments (Region→Cluster→Node→Monitor).

**Note**: The calling agent should use the `.github/skills/Common/execute-kusto-query/SKILL.md` skill before invoking this skill.

## Investigation Workflow

**Important**: Output the results from each step as specified. Complete all steps before providing conclusions.

### Step 0: Generate Geneva Health Monitor Link & Dashboard Links

Since this is a Health Hierarchy alert, generate a Geneva Health portal link for the DRI using the [access-geneva-health skill](/.github/skills/Connectivity/connectivity-utilities/access-geneva-health/SKILL.md). This provides direct portal access to inspect the monitor state, health timeline, and rollup topology.

**Input**: Pass the ICM `correlationId`, `occuringLocation.datacenter`, and `createdDate` fields to the access-geneva-health skill. Pass StartTime, EndTime, and ClusterName (FQDN from ICM) to the [access-dataexplorer-dashboard skill](/.github/skills/Connectivity/connectivity-utilities/access-dataexplorer-dashboard/SKILL.md) (select the **Gateway** page).

**Cluster-level CorrelationId format** (3 segments):

```
HH-SQLConnectivity-Cluster/{RegionName}->{ClusterFQDN}->{MonitorGUID}
```

Example:

```
HH-SQLConnectivity-Cluster/East US 2 EUAP->cr18.useuapeast2-a.control.database.windows.net->4ce9db6b-b684-45ea-a7ca-1fdb2b6a8a96
```

**Output**: Include all links as clickable markdown in the report:

🔗 **Portal Links**
- [Geneva Health Monitor]({generated_geneva_url}) — Health Hierarchy rollup view for the cluster
- [Data Explorer Dashboard — Gateway]({generated_dataexplorer_url}) — GW metrics for the cluster and time window
- 📋 [Global Health](https://portal.microsoftgeneva.com/s/B0A2575D)
- 📋 [Drill Calendar](https://global.azure.com/drillmanager/calendarView)

---

### Step 1: Parse Cluster-Level Alert Context

**1a.** Extract `ClusterName` and `RegionName` from the ICM.

**Primary source — CorrelationId:** Cluster-level alerts have 3 segments: `Region→Cluster→Monitor`. Extract ClusterName from segment 2.

**Secondary source — ICM Title:** The title follows the pattern:

```
[Health Hierarchy alert - {RegionName}] Cluster {ClusterName} is unhealthy - At least 20% of Gateway nodes are unhealthy
```

Use this to **validate** CorrelationId extraction, or as **fallback** if CorrelationId parsing fails.

**Output:**

```
📋 Cluster-Level Alert Context:
- ClusterName: {ClusterName}
- RegionName: {RegionName}
- CorrelationId segments: {count} (expected: 3 for cluster-level)
```

---

### Step 2: Scope Assessment — Identify Unhealthy Nodes

Determine how many GW nodes are unhealthy and which ones. This establishes the scope of the incident, applying [principles.md](references/principles.md) Triage Principle 1 (Scope Before Depth) and Diagnosis Principle 1 (the 20% threshold is meaningful).

> Note: CRNU100/CRNU110 classify nodes as unhealthy using `LoginSuccessRate < 95%` because login success rate is the dominant signal in the Geneva rollup. Nodes can also be flagged unhealthy by other signals (LSASS, TCP rejections, GW process restarts) — Step 4 surfaces those on the same nodes and may identify additional contributors not visible from login rate alone.

**Execute query:** CRNU100 from [references/queries.md](references/queries.md) — Per-node login success rate across the cluster.

**Analysis:**

| Condition | Classification | Recommended Action |
|-----------|---------------|-------------------|
| < 20% nodes below 95% | **Below rollup threshold** | Alert may have auto-resolved; verify current state |
| 20-50% nodes below 95% | **Moderate cluster impact** | Continue investigation; check for common patterns |
| > 50% nodes below 95% | **Severe cluster impact** | 🚩 Prioritize — significant portion of cluster is degraded |
| 100% nodes below 95% | **Cluster-wide failure** | 🚩 Likely infrastructure-level issue (AliasDB, networking, deployment) |

**Execute query:** CRNU110 from [references/queries.md](references/queries.md) — Node health summary with total vs. unhealthy counts.

**Output:**

```
📋 Scope Assessment:
- Total GW nodes: {count}
- Unhealthy nodes (< 95% success rate): {count} ({percentage}%)
- Threshold: 20% → Alert {confirmed/below threshold}
- Unhealthy node list: {node1, node2, ...}
```

---

### Step 3: Check Common Cluster-Wide Patterns

Run these checks in order. If any match, output the finding and recommended action. **Do not stop** — continue the investigation but note the match. Background on the patterns checked here is in [knowledge.md § Common Root Causes from Real Incidents](references/knowledge.md).

#### 3a: Azure Disaster Recovery Drill

**Check:** Review the [Drill Calendar](https://global.azure.com/drillmanager/calendarView) for the region and time window.

**Match criteria:**
- An Azure Disaster Recovery Drill is scheduled for the region/time
- Multiple nodes went unhealthy simultaneously

**If matched:** 🚩 "Known pattern: Azure Disaster Recovery Drill. Confirm drill schedule; monitor how resources recover to identify possible issues during recovery."

#### 3b: Deployment / Upgrade in Progress

**Execute query:** CRNU200 from [references/queries.md](references/queries.md) — Check GW deployment traces.

**Match criteria:** Active deployment or repair activity overlapping with the incident time window.

**If matched:** 🚩 "Known pattern: Deployment/Upgrade in progress. Nodes may be cycling through upgrade domains. Expected to self-mitigate after deployment completes."

#### 3c: GW Process Restarts Across Cluster

**Execute query:** CRNU210 from [references/queries.md](references/queries.md) — GW process restarts across all nodes in the cluster.

**Match criteria:** Multiple nodes showing GW process restarts (`process_id` changes) in the same time window indicates a cluster-wide GW instability pattern.

**If matched:** 🚩 "Cluster-wide GW process instability detected. Cross-reference with deployment (3b) and drill (3a) findings."

**Note:** CRNU210 results are also reused in Step 4d for per-node GW process health assessment.

---

### Step 4: Determine Breaching Health Signal(s) Per Unhealthy Node

For each unhealthy node identified in Step 2, determine WHICH signal(s) caused the unhealthy state. A node can have multiple breaching signals simultaneously. Signal definitions, thresholds, and underlying counters/tables are in [knowledge.md § Health Signals That Make a GW Node Unhealthy](references/knowledge.md); investigate in the order from [principles.md](references/principles.md) Triage Principle 3 (Most Common Signal First).

**4a. Login Success Rate Check:**

**Execute query:** CRNU100 results from Step 2 — nodes with `LoginSuccessRate < 95%` have this signal breaching.

**4b. LSASS CPU Stress Check:**

**Execute query:** CRNU300 from [references/queries.md](references/queries.md) — LSASS % Privileged Time per node.

**Match criteria:** `AvgLsassPrivilegedTimePct > 50%` or `MaxLsassPrivilegedTimePct > 50%` indicates LSASS stress on the node.

**4c. TCP Rejections Check:**

**Execute query:** CRNU310 from [references/queries.md](references/queries.md) — TCP rejections per node.

**Match criteria:** (`AvgRejectedPerSec > 150` or `MaxRejectedPerSec > 150`) AND (`AvgHandleCount > 600000` or `MaxHandleCount > 600000`) indicates TCP rejection condition.

**4d. GW Process Health Check:**

**Reuse:** CRNU210 results from Step 3c — GW process restarts per node.

**Match criteria:** `TotalProcesses > 1` for a node indicates GW process instability (multiple distinct process IDs observed in the window).

**Output:**

```
📋 Breaching Health Signals Per Unhealthy Node:

| Node | Login Success Rate | LSASS CPU (%) | TCP Rejections | GW Process Restarts | Primary Signal |
|------|-------------------|---------------|----------------|--------------------|----|
| _GW_01 | 82.3% 🚩 | 12% | 0/sec | 0 | Login Success Rate |
| _GW_05 | 91.1% 🚩 | 78% 🚩 | 230/sec 🚩 | 3 🚩 | LSASS + TCP Rejections |
| ... | ... | ... | ... | ... | ... |
```

---

### Step 5: Check Auto-Mitigation Status

Apply [principles.md](references/principles.md) Triage Principle 5 (Check Auto-Mitigation Early) and use Expected Investigation Timing in the same file to judge whether observed timing matches the expected window. Background on how `healthmanagesvc` decides to act is in [knowledge.md § Auto-Mitigation by healthmanagesvc](references/knowledge.md).

**Execute query:** CRNU400 from [references/queries.md](references/queries.md) — Check automation actions targeting the cluster.

**Record findings (do not branch the investigation here):**
- Whether `healthmanagesvc` automation actions were found, and the timestamp of the last action
- Whether `SqlRunner` automation actions were found
- Current observed health state (recovering / still degraded / healthy)

**Important:** Auto-mitigation status is informational only. Regardless of what is found in this step, **continue with Steps 6–9** (delegation, impact assessment, mitigation decision, recovery verification). Auto-mitigation may not succeed, the underlying root cause may persist, and the issue may recur if not properly understood.

**Output:**

```
📋 Auto-Mitigation Status:
- Automation actions found: {Yes/No}
- Last automation action: {action} at {timestamp}
- Current health state: {Recovering/Still degraded/Healthy}
```

---

### Step 6: Delegate to Node-Level Skills

Based on Step 4 findings, delegate to the appropriate node-level skill(s) for deep investigation on the most impacted nodes, per [principles.md](references/principles.md) Triage Principle 4 (Delegate to Specialized Skills) and Triage Principle 6 (Cluster vs Node Correlation).

**Delegation Matrix:**

| Primary Signal | Delegate To | Pass Parameters |
|---------------|------------|-----------------|
| Login Success Rate | [gateway-node-low-login-success-rate](/.github/skills/Connectivity/connectivity-scenarios/gateway-node-low-login-success-rate/SKILL.md) | ClusterName, NodeName, StartTime, EndTime |
| LSASS CPU Stress | [Performance/LSASS](/.github/skills/Performance/LSASS/SKILL.md) | ClusterName, NodeName, StartTime, EndTime |
| TCP Rejections | [xdbhost-high-tcp-rejections](/.github/skills/Connectivity/connectivity-scenarios/xdbhost-high-tcp-rejections/SKILL.md) | ClusterName, NodeName (as DBNodeName), StartTime, EndTime |
| GW Process Instability | [gateway-health-and-rollout](/.github/skills/Connectivity/connectivity-scenarios/gateway-health-and-rollout/SKILL.md) | ClusterName, NodeName, StartTime, EndTime |
| Multiple signals | Delegate to **primary signal** skill first, then others | Per above |

**Delegation guidelines:**
- Delegate for the **top 1-3 most impacted nodes** (highest signal breach severity)
- If ALL unhealthy nodes share the same signal → delegate for 1 representative node
- If different nodes have different signals → delegate for 1 node per signal type
- If Login Success Rate is the primary signal → this is the most common case; delegate to `gateway-node-low-login-success-rate`

**Output per delegation:**

```
📋 Delegation: {SkillName} for node {NodeName}
- Primary signal: {signal}
- Parameters passed: ClusterName={...}, NodeName={...}, StartTime={...}, EndTime={...}
- Findings: {summary from delegated skill}
```

---

### Step 7: Impact Assessment

**Execute query:** CRNU500 from [references/queries.md](references/queries.md) — Count distinct impacted servers and subscriptions.

**Output:**

```
📋 Impact Assessment:
- Unhealthy nodes: {count} / {total} ({percentage}%)
- Distinct logical servers with system errors: {count}
- Distinct subscriptions impacted: {count}
- Customer-facing impact: {Yes — server/subscription errors detected / No — infrastructure-only}
```

---

### Step 8: Mitigation & Escalation Decision Tree

Based on findings from Steps 2-7, output the applicable mitigation path. Use [principles.md § Root Cause Classification and Escalation Criteria](references/principles.md) when assigning the incident to a category and deciding whether to delegate, hold for auto-mitigation, or escalate to Connectivity Engineering.

| Condition | Recommendation |
|-----------|---------------|
| **Azure Disaster Recovery Drill** (Step 3a) | Confirm drill schedule and record in ICM; continue with signal-based delegation below; closely monitor recovery for issues |
| **Deployment/Upgrade in progress** (Step 3b) | Record deployment context in ICM; continue with signal-based delegation; identify if the deployment itself is the trigger |
| **Auto-mitigation detected by healthmanagesvc** (Step 5) | Record in ICM; continue with signal-based delegation to confirm root cause; verify recovery in Step 9 |
| **Login success rate is primary signal** (Step 4) | Delegate to `gateway-node-low-login-success-rate` for root cause and node-level mitigation |
| **LSASS stress is primary signal** (Step 4) | Delegate to Performance/LSASS skill; mitigation depends on LSASS driver classification |
| **TCP rejections breaching** (Step 4) | Delegate to `xdbhost-high-tcp-rejections`; may require XDBHost restart or failover |
| **GW process instability** (Step 4) | Delegate to `gateway-health-and-rollout`; restart GW process on affected nodes |
| **Multiple signals / no clear cause** | Escalate to Connectivity Engineering |

**Visual Decision Tree:**

The decision tree below is keyed on the **primary breaching signal** identified in Step 4. Auto-mitigation status (Step 5), drill detection (Step 3a) and deployment detection (Step 3b) do **not** short-circuit this tree — they are recorded as findings and added to the ICM update, but the agent must still walk the signal-based delegation path below and complete Steps 7 and 9.

```
                          ┌─────────────────────────────┐
                          │  Steps 2-7 findings          │
                          │  collected (signals,         │
                          │  patterns, auto-mitigation,  │
                          │  impact)                     │
                          └──────────────┬───────────────┘
                                         │
                                ┌────────▼────────┐
                                │ Primary signal? │
                                │ (from Step 4)   │
                                └──┬──┬──┬──┬─────┘
                                   │  │  │  │
            Login Success Rate ────┘  │  │  │
                  │                   │  │  │
            ┌─────▼─────────────┐     │  │  │
            │ Delegate to       │     │  │  │
            │ gw-node-low-login │     │  │  │
            └───────────────────┘     │  │  │
                                      │  │  │
            LSASS Stress ─────────────┘  │  │
                  │                      │  │
            ┌─────▼─────────────┐        │  │
            │ Delegate to       │        │  │
            │ Performance/LSASS │        │  │
            └───────────────────┘        │  │
                                         │  │
            TCP Rejections ──────────────┘  │
                  │                         │
            ┌─────▼─────────────┐           │
            │ Delegate to       │           │
            │ xdbhost-tcp-rej   │           │
            └───────────────────┘           │
                                            │
            GW Process / Multiple / Unknown ┘
                  │
            ┌─────▼───────────────────┐
            │ Delegate to             │
            │ gw-health-rollout       │
            │ OR escalate to          │
            │ Connectivity Engineering│
            └─────────────────────────┘
                  │
                  ▼
            ┌─────────────────────────────┐
            │ Continue to Step 7 (impact) │
            │ and Step 9 (verification),  │
            │ regardless of auto-         │
            │ mitigation findings         │
            └─────────────────────────────┘
```

---

### Step 9: Verification

After mitigation or auto-mitigation:

1. Re-run **CRNU100** with a time window covering the last 15 minutes
2. Confirm < 20% of nodes have `LoginSuccessRate < 95%`
3. Re-run **CRNU300** to confirm LSASS CPU has normalized on previously affected nodes
4. Re-run **CRNU310** to confirm TCP rejections have stopped
5. Check Geneva Health monitor has returned to healthy state (via Geneva Health link from Step 0)
6. Update ICM with mitigation action taken and verification results

**Verification Criteria:**

| Check | Healthy | Still Degraded |
|-------|---------|----------------|
| Unhealthy nodes < 20% | ✅ | 🚩 |
| Login success rate > 99% on previously affected nodes | ✅ | 🚩 |
| LSASS CPU < 10% on previously affected nodes | ✅ | 🚩 |
| TCP rejections = 0 on previously affected nodes | ✅ | 🚩 |
| Geneva Health monitor = Healthy | ✅ | 🚩 |

---

## Execution Verification Checklist

Before providing conclusions, output this table:

```
## ✅ Control Ring Nodes Unhealthy — Execution Verification

| Step | Description | Queries Run | Status |
|------|------------|-------------|--------|
| 0 | 🔗 Geneva Health + Dashboard Links | Geneva link, Data Explorer link | ⬜ |
| 1 | Parse Cluster-Level Alert | ClusterName, RegionName extracted | ⬜ |
| 2 | Scope Assessment | CRNU100, CRNU110 | ⬜ |
| 3 | Common Cluster-Wide Patterns | CRNU200, CRNU210, Drill Calendar | ⬜ |
| 4 | Breaching Signal(s) Per Node | CRNU100 (reuse), CRNU300, CRNU310, CRNU210 (reuse) | ⬜ |
| 5 | Auto-Mitigation Status | CRNU400 | ⬜ |
| 6 | Delegate to Node-Level Skills | Per delegation matrix | ⬜ |
| 7 | Impact Assessment | CRNU500 | ⬜ |
| 8 | Mitigation Decision | Decision tree applied | ⬜ |
| 9 | Verification | CRNU100, CRNU300, CRNU310 (re-run) | ⬜ |
```

## Reference

- [knowledge.md](references/knowledge.md) — Geneva Health Hierarchy rollup architecture, alert thresholds, health signals, root cause taxonomy
- [principles.md](references/principles.md) — Cluster-level triage principles, diagnosis principles, timing reference, root cause classification
- [queries.md](references/queries.md) — All Kusto queries (CRNU100–CRNU500)
- [gateway-node-low-login-success-rate skill](/.github/skills/Connectivity/connectivity-scenarios/gateway-node-low-login-success-rate/SKILL.md) — Node-level login success rate investigation (delegation target)
- [xdbhost-high-tcp-rejections skill](/.github/skills/Connectivity/connectivity-scenarios/xdbhost-high-tcp-rejections/SKILL.md) — Node-level TCP rejection investigation (delegation target)
- [gateway-health-and-rollout skill](/.github/skills/Connectivity/connectivity-scenarios/gateway-health-and-rollout/SKILL.md) — GW process health and deployment investigation (delegation target)
- [access-geneva-health skill](/.github/skills/Connectivity/connectivity-utilities/access-geneva-health/SKILL.md) — Generate Geneva Health Monitor portal link from ICM incident data
- [access-dataexplorer-dashboard skill](/.github/skills/Connectivity/connectivity-utilities/access-dataexplorer-dashboard/SKILL.md) — Generate pre-filled Data Explorer dashboard link for Gateway metrics
