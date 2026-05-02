# Control Ring Nodes Unhealthy — Knowledge Base

## Alert Background

This alert fires when ≥20% of Gateway nodes in a Control Ring cluster are unhealthy, as determined by the Geneva Health rollup monitor.

| Level | Monitor Name | Threshold |
|-------|-------------|-----------|
| Cluster (rollup) | `SQLConnectivity-Cluster-ControRing-Nodes-Unhealthy` | ≥ 20% of GW nodes unhealthy |

**Note:** The monitor name contains a typo ("ControRing" instead of "ControlRing") — this is the actual production name.

## Geneva Health Rollup Architecture

### What Is a Rollup Monitor?

The `SQLConnectivity-Cluster-ControRing-Nodes-Unhealthy` monitor is a **Geneva Health Rollup Monitor**. Unlike node-level monitors that evaluate a single signal on a single node, rollup monitors **aggregate** the health status of multiple entities (in this case, GW nodes) and fire when a threshold percentage is breached.

### How the Rollup Works

```
Cluster Health Assessment
│
├── GW Node 1: Healthy (all signals passing)
├── GW Node 2: Unhealthy (Login Success Rate < threshold)
├── GW Node 3: Healthy
├── GW Node 4: Unhealthy (LSASS CPU > threshold)
├── GW Node 5: Healthy
│
Result: 2/5 = 40% unhealthy → ≥ 20% → ALERT FIRES
```

A node is marked **unhealthy** if **ANY** of its health signals breach their individual thresholds. The rollup does not distinguish which signal caused the node to be unhealthy — it only counts unhealthy vs healthy nodes.

### CorrelationId Structure

Cluster-level alerts have a **3-segment** CorrelationId, unlike node-level alerts which have 4 segments:

| Alert Level | CorrelationId Format | Segments |
|-------------|---------------------|----------|
| Cluster | `HH-SQLConnectivity-Cluster/{RegionName}->{ClusterFQDN}->{MonitorGUID}` | 3 |
| Node | `HH-SQLConnectivity-Cluster/{RegionName}->{ClusterFQDN}->{NodeName}->{MonitorGUID}` | 4 |

### Resource Identifier Format

```
resource://AzureDbProduction{region}/SQLConnectivity-HealthResource-Cluster/{ClusterFQDN}_{RegionName}
```

## Health Signals That Make a GW Node Unhealthy

A Gateway node is assessed as "unhealthy" when any of the following health signals breach their individual thresholds:

### 1. Login Success Rate (Most Common)

| Property | Value |
|----------|-------|
| Monitor | `SQLConnectivity-GatewayNodeLowLoginSuccessRate` |
| Metric | Login success rate per GW node |
| Threshold | Per-node success rate drops below configured level |
| Formula | `(TotalLogins - SystemErrors) / TotalLogins` |
| Investigation skill | `gateway-node-low-login-success-rate` |

Login success rate is the most frequently breaching signal. Common causes include AliasDB resolution failures (40613/4), Trident testing in canary rings, SF version behavior changes during deployments, SNAT port exhaustion, and AliasDB ODBC connectivity failures.

> **Cluster-wide pattern — AliasDB failures:** AliasDB issues (replica health degradation, secret rotation, ODBC connectivity failures) can cascade across multiple Gateway nodes simultaneously, causing a cluster-wide login success rate drop rather than a single-node issue. When the rollup monitor fires and login success rate is the dominant signal across many nodes, check for a common AliasDB root cause before investigating individual nodes. The delegated `gateway-node-low-login-success-rate` skill covers AliasDB diagnostics in detail (Known Issue #4, queries GNLSR600–GNLSR640).

### 2. LSASS Stress (Authentication CPU)

| Property | Value |
|----------|-------|
| Counter | `\Process(Lsass)\% Privileged Time` |
| Table | `MonCounterOneMinute` |
| Warning threshold | > 50% |
| Critical threshold | > 100% |
| Impact | Authentication delays → login stalls → cascading failures |

LSASS (Local Security Authority Subsystem Service) handles user authentication, security policies, and auditing. When LSASS **privileged CPU time** is elevated, all authentication-dependent operations stall, including XdbHost IOCP listener threads. This is distinct from general node CPU — LSASS stress specifically indicates that authentication (TLS handshakes, Kerberos) is overloaded, even if overall node CPU may appear normal.

**Common LSASS spike drivers:**
- **Login-driven**: High login volume (TLS handshakes per login)
- **XStore-driven**: High storage IO (TLS-dependent XStore requests)
- **ImageStore-driven**: SF ImageStore replica builds triggering CRL/TLS operations
- **Frozen VM**: VM-level hang causing LSASS backlog burst on unfreeze
- **Residual**: No clear external trigger, often correlates with OS upgrades

### 3. General Node CPU Stress

| Property | Value |
|----------|-------|
| Counter | `\Processor(_Total)\% Processor Time` |
| Table | `MonCounterOneMinute` |
| Warning threshold | > 80% sustained |
| Critical threshold | > 95% sustained |
| Impact | Overall node degradation, connection handling delays |

General node CPU stress differs from LSASS stress. Total Processor Time reflects overall CPU saturation across all processes on the node, while LSASS `% Privileged Time` measures authentication-specific load. A node can have high total CPU without LSASS stress (workload-driven from database or XdbHost processing), or high LSASS stress without high total CPU (authentication-specific pressure from TLS handshakes). See [Performance/LSASS skill](/.github/skills/Performance/LSASS/SKILL.md) for detailed LSASS spike classification (login-driven, XStore-driven, residual, cascade, step-change, ImageStore-driven).

### 4. TCP Rejections

| Property | Value |
|----------|-------|
| Counter | `\Microsoft Winsock BSP\Rejected Connections/sec` |
| Secondary counter | `\Process(_Total)\Handle Count` |
| Threshold conditions | Rejections > 150/sec AND Handle Count > 600,000 (sustained for 1 hour) |
| Investigation skill | `xdbhost-high-tcp-rejections` |

TCP rejections indicate that incoming TCP connections are being refused at the Winsock Base Service Provider level on the node. High handle counts indicate resource exhaustion risk — each login creates two handles (one on XDBHost, one on SQL), and if both are not released, it leads to a handle leak → socket exhaustion → TCP rejections. The combination of sustained rejections AND high handle counts distinguishes genuine resource exhaustion from transient spikes. Typically associated with XdbHost crash-dump-restart loops driven by LSASS stress. See [xdbhost-high-tcp-rejections skill](/.github/skills/Connectivity/connectivity-scenarios/xdbhost-high-tcp-rejections/SKILL.md) for the full crash-loop analysis workflow.

### 5. GW Process Health / Restarts

| Property | Value |
|----------|-------|
| Signal | GW process crash or restart |
| Detection | Multiple distinct `process_id` values in MonLogin within the time window |
| Investigation skill | `gateway-health-and-rollout` |

Gateway process instability manifests as multiple process ID changes (restarts). A single restart is usually benign; multiple restarts (> 3) indicate a crash loop.

## Common Root Causes from Real Incidents

Based on analysis of real incidents:

### Azure Disaster Recovery Drill

Planned Azure Disaster Recovery Drills that intentionally take nodes down to test resilience. Multiple nodes go unhealthy simultaneously.

**Detection:** Check the [Drill Calendar](https://global.azure.com/drillmanager/calendarView) for a scheduled drill overlapping with the incident window and region.

**Expected behavior:** Auto-mitigates after drill completes. However, the DRI should still monitor how the resources recover to identify possible issues during the recovery phase — it is not sufficient to simply wait for the drill to finish.

### Deployment / Upgrade

Gateway deployments cycle through upgrade domains, temporarily taking nodes offline. This causes transient login failures on the affected nodes until the new version stabilizes.

**Detection:** `MonRolloutProgress` shows active deployment overlapping with incident window.

**Expected behavior:** Deployments can have some impact, but it is important to understand and identify when the deployment is problematic — either due to a regression introduced by the new version, or because a process did not complete correctly. The DRI should investigate whether the deployment is the root cause or merely correlated, and escalate if impact persists beyond the expected deployment window.

### Auto-Mitigation by healthmanagesvc

The `healthmanagesvc` service can auto-mitigate cluster-level health issues by:
1. Monitoring watchdog health reports
2. Waiting for ~1 hour of consecutive healthy reports
3. Marking the node/cluster as healthy

However, auto-mitigation is not guaranteed — if the underlying issue persists, healthy reports may never arrive and the incident will not resolve. The DRI **must always** investigate the root cause regardless of whether auto-mitigation is expected or in progress.

## Relationship to Node-Level Incidents

When this cluster-level alert fires, **node-level incidents often already exist**. Common patterns:

| Cluster-Level Alert | Node-Level Incidents That May Coexist |
|--------------------|-----------------------------------------|
| Control Ring Nodes Unhealthy (this) | GatewayNodeLowLoginSuccessRate |
| Control Ring Nodes Unhealthy (this) | XDBHostHighTcpRejections |
| Control Ring Nodes Unhealthy (this) | Gateway health/restart alerts |

This skill's job is to provide the **cluster-wide perspective** — which nodes are affected, how many, and what signals are breaching — then delegate to the appropriate node-level skill for deep investigation on specific nodes.

## Key Telemetry Tables

| Table | Purpose in This Skill |
|-------|----------------------|
| `MonLogin` | Primary table — per-node login success rates, error distribution, impact assessment. Used by CRNU100, CRNU110, CRNU210, CRNU500. |
| `MonCounterOneMinute` | LSASS CPU and TCP rejection counters per node. Used by CRNU300, CRNU310. |
| `MonRolloutProgress` | Deployment/upgrade tracking for cluster-wide pattern detection. Used by CRNU200. |
| `MonNonPiiAudit` | Automation actions (DumpProcess, KillProcess) for auto-mitigation status. Used by CRNU400. |
| `MonGatewayResourceStats` | GW node resource usage (memory, threads, cache). Used by delegated skills. |
| `MonRedirector` | AliasDB cache health, fabric resolution (used by delegated GNLSR skill). |
| `MonSFEvents` | SF application health (used by delegated GNLSR skill). |

## Dashboard Links

| Dashboard | URL |
|-----------|-----|
| Global Health | `https://portal.microsoftgeneva.com/s/B0A2575D` |
| Drill Calendar | `https://global.azure.com/drillmanager/calendarView` |

## ICM Properties

| Property | Typical Value |
|----------|--------------|
| Severity | 2 |
| Created by | `MDM-Ext-azdb3-black` or `MDM-Ext-azdb3-red` |
| MonitorId | `SQLConnectivity-Cluster-ControRing-Nodes-Unhealthy` |
| OwningTeamId | SQL Connectivity |
| Title pattern | `[Health Hierarchy alert - {RegionName}] Cluster {ClusterName} is unhealthy - At least 20% of Gateway nodes are unhealthy` |
| Auto-mitigation | `healthmanagesvc` (~1 hour after consecutive healthy reports) — not guaranteed; full investigation always required |

## Related Documentation

All source materials used to build and maintain this skill. These URLs are fetched
during skill creation and updates to extract knowledge, principles, and queries.

### Internal Documentation (eng.ms / ADO Wiki)

- [Ring-wide success rate below 95% for the last 5 minutes](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/clusters-rings/ring-wide-success-rate-below-95-for-last-5-minutes)
- [Login rate drop of 95% in last 5 minutes](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/clusters-rings/login-rate-drop-of-95-in-last-5-minutes)
- [Azure SQL Gateways in region have availability problems](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/clusters-rings/azure-sql-gateways-in-region-have-availability-problems)

### Related Skills

- [gateway-node-low-login-success-rate](/.github/skills/Connectivity/connectivity-scenarios/gateway-node-low-login-success-rate/SKILL.md) — Node-level login success rate investigation
- [xdbhost-high-tcp-rejections](/.github/skills/Connectivity/connectivity-scenarios/xdbhost-high-tcp-rejections/SKILL.md) — Node-level TCP rejection investigation
- [gateway-health-and-rollout](/.github/skills/Connectivity/connectivity-scenarios/gateway-health-and-rollout/SKILL.md) — GW process health and deployment investigation
- [access-geneva-health](/.github/skills/Connectivity/connectivity-utilities/access-geneva-health/SKILL.md) — Geneva Health portal link generation
- [access-dataexplorer-dashboard](/.github/skills/Connectivity/connectivity-utilities/access-dataexplorer-dashboard/SKILL.md) — Data Explorer dashboard link generation
