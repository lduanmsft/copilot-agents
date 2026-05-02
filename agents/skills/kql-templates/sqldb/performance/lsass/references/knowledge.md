# LSASS Telemetry Hole - Terms and Concepts

## Core Concepts

### LSASS (Local Security Authority Subsystem Service)
Windows process (`lsass.exe`) responsible for enforcing security policy, handling user authentication (including TLS handshakes), and managing access tokens. In Azure SQL Database worker nodes, LSASS processes TLS handshakes for both incoming logins and XStore IO operations.

### Telemetry Hole
A gap or missing window in telemetry data where expected monitoring signals (MonCounterOneMinute, MonSQLXStoreIOStats, etc.) are absent. Telemetry holes indicate the node was unresponsive or unable to emit telemetry — typically caused by CPU saturation, VM-level hangs, or storage stalls.

### TLS Handshake
Cryptographic negotiation establishing a secure connection. LSASS handles TLS handshakes for:
- **SQL logins**: Client connections to SQL Server trigger TLS negotiation through LSASS
- **XStore IO**: Storage operations to Azure XStore use TLS, with handshakes proportionally dependent on IO request volume

## LSASS Spike Patterns

### Pattern 1: Login-Driven LSASS
**Characteristics**:
- LSASS CPU spike correlates with MonLogin volume spike
- No distinguishable XStore IO request spike during the same window
- Total Processor Time may or may not spike

**Mechanism**: A surge in client connections causes a proportional increase in TLS handshakes processed by LSASS. Each login requires a TLS negotiation, so bulk connection attempts (retry storms, connection pool resets, new deployments) directly drive LSASS CPU.

**Observed pattern**: Clear correlation between LSASS spike and MonLogin total logins with stable XStore IO request counts.

### Pattern 2: XStore-Driven LSASS
**Characteristics**:
- LSASS CPU spike correlates with XStore IO request count spike
- No corresponding MonLogin volume spike
- Total Processor Time may spike depending on IO volume

**Mechanism**: XStore IO operations use TLS connections, with handshake overhead proportional to IO request count. A spike in XStore IO (e.g., heavy reads/writes from database workloads) drives TLS handshake volume in LSASS.

**Observed pattern**: LSASS spike (100-200%+) correlating with XStoreIOStats spike, with no corresponding login volume spike.

### Pattern 3: Residual LSASS
**Characteristics**:
- LSASS CPU spike with **no clear correlation** to either MonLogin or XStore IO
- Total Processor Time often simultaneous and pegged to CPU bound (~94-100%)
- May coincide with OS version upgrade or infrastructure maintenance
- Telemetry loss observed during spike

**Mechanism**: Unknown direct trigger. The LSASS spike appears to be a secondary effect of broader system contention rather than a direct response to login or IO volume. Often observed during or after OS upgrades where the security subsystem may be performing additional cryptographic operations (certificate re-enrollment, key regeneration, policy refresh).

**Observed pattern**: Massive LSASS spike (1000%+) with total CPU pegged at ~94-100%. No correlation with XStore IO or MonLogin. OS version upgrade (e.g., Windows Server 2022 → 2025) occurring during the same window.

### Pattern 4: LSASS Cascade (LSASS → Login Failures)
**Characteristics**:
- LSASS CPU spikes to extreme levels (1K+%) for 8–10 minutes
- Login request spikes occur **after** the LSASS spike (not before/simultaneously)
- Client-side login failures, timeouts, and connection pool exhaustion observed
- No node failovers during the incident, but node movement may occur 30–60 minutes later
- Worker thread exhaustion may develop as a secondary effect
- VM becomes unresponsive from the client perspective

**Mechanism**: Extreme LSASS CPU consumption starves the system, causing authentication processing to stall. As pending logins queue up and time out, clients retry aggressively (retry storms), which amplifies the login volume spike *after* LSASS starts to recover. The cascading effect produces connection pool exhaustion on the client side.

**Key distinction from Pattern 1 (Login-driven)**: In Pattern 1, login volume *causes* the LSASS spike. In Pattern 4, the LSASS spike *causes* the login surge through retry storms. The temporal ordering is critical: LSASS spike first, then login spike.

**Observed pattern**: Multiple incidents across stamps where LSASS spikes to 1K+ for 8–10 minutes were followed by login request surges. Client-side symptoms included login failures, timeouts, and connection pool exhaustion. No node failovers occurred during incidents.

### Pattern 5: LSASS Step-Change
**Characteristics**:
- LSASS CPU shows a persistent step-change (elevation) rather than a sharp spike
- LSASS counters may not reach extreme levels (50–85% range is common)
- Still correlates with outage timing
- May not produce telemetry holes but degrades authentication performance

**Mechanism**: A sustained moderate increase in LSASS CPU (e.g., from ongoing cryptographic operations, certificate validation overhead, or Kerberos ticket processing) that doesn't produce a dramatic spike but still impacts login latency enough to cause client-side failures.

**Observed pattern**: LSASS counters showing step-changes (50-85% range) correlating with outage windows, causing 20+ minutes of client-side unresponsiveness even without extreme LSASS spikes.

### Pattern 6: ImageStore-Driven LSASS (Strong Correlation with Upgrade-Window Spikes)
**Characteristics**:
- LSASS CPU spikes to extreme levels (1,000–21,000%) within seconds of ImageStore replica landing
- Occurs during OS upgrade windows when Service Fabric moves system service replicas between nodes
- Telemetry goes dark at the **exact second** ImageStore lands
- Strong correlation observed: majority of extreme spikes (>1000%) were preceded by ImageStore moves
- Highest-severity spikes showed the strongest ImageStore correlation

**Mechanism (hypothesis)**: When Service Fabric places an ImageStore replica (AddSecondary, MoveSecondary) on a node, it triggers heavy certificate chain validation and CRL checks via `CertGetCertificateChain()`. With cold/expired CRL cache, LSASS opens network connections to external CRL/OCSP endpoints. Concurrent TLS handshakes with network timeouts stacking cause LSASS CPU to spike.

**Key distinction from Pattern 3 (Residual)**: Pattern 3 has no identified trigger. Pattern 6 shows a strong temporal correlation with ImageStore replica builds. Incidents previously classified as Pattern 3 during upgrade windows should be checked for Pattern 6 correlation.

## Guest OS Version Changes

OS version changes during an incident window are a **correlating signal** — they indicate the node was part of an upgrade wave, but the OS upgrade itself may not be the direct cause of the LSASS spike. The actual trigger may be related infrastructure activity (e.g., ImageStore replica movements, host preparation) that happens during the upgrade window.

When analyzing:
- Check MonRgLoad for `guest_os_version` changes (LSASS900)
- Gaps between the last data of the old OS version and the first data of the new version represent the actual upgrade/reboot window
- Empty `guest_os_version` rows may indicate transitional state
- **Do NOT conclude** that the OS upgrade caused the LSASS spike — investigate ImageStore movements (LSASS1100/1200) and other triggers first

## Telemetry Tables

| Table | Data | Relevance |
|-------|------|-----------|
| **MonCounterOneMinute** | Windows performance counters (CPU, process stats) | Total CPU, per-core CPU, LSASS process CPU |
| **MonLogin** | SQL login events (success/failure) | Login volume correlation with LSASS |
| **MonSQLXStoreIOStats** | XStore storage IO statistics | IO request counts, throughput correlation |
| **MonMachineLocalWatchdog** | VM health watchdog | Sluggish/frozen VM detection |
| **MonSqlRgHistory** | Resource governor history, virtual file IO | IO stall metrics |
| **MonRgLoad** | Resource governor load, OS version | Guest OS version changes |

## Related Documentation
- [LSASS Queries](queries.md) - Kusto queries for triage
- [LSASS Principles](principles.md) - Correlation analysis rules

## Two-Problem Framework

### Problem 1: Residual LSASS
LSASS spike causes a telemetry hole but neither MonLogin nor XStore shows a significant pre-outage spike (spike factor < 3×). The LSASS spike has no clear external trigger. Often correlates with OS upgrades, infrastructure maintenance, or unknown internal contention. Corresponds to **Pattern 3** in the spike classification.

### Problem 2: Direct LSASS
An external workload driver — MonLogin (login volume) and/or XStore (IO requests) — spikes by a significant factor (≥ 3×) in the 30-minute window before the telemetry hole, directly causing the LSASS spike via TLS handshake load. Corresponds to **Pattern 1** (login-driven), **Pattern 2** (XStore-driven), or a combination of both.

**Problem 2 sub-variants:**
- **Login-driven (Pattern 1)**: MonLogin spike factor ≥ 3× before LSASS spike. TLS handshakes from login volume drove LSASS CPU.
- **XStore-driven (Pattern 2)**: XStore spike factor ≥ 3× before LSASS spike. TLS-dependent IO operations drove LSASS CPU.
- **Combined**: Both MonLogin and XStore spike ≥ 3× before LSASS spike.
- **Cascade (Pattern 4)**: Starts as Problem 2 but the login spike appears **after** the LSASS spike — indicating the LSASS spike caused authentication stalls which triggered retry storms.

### Spike Factor
The ratio of the **pre-outage peak** of a metric (MonLogin total logins, XStore total requests) to the **baseline average** of that same metric during a calm period. A spike factor ≥ 3× is considered significant. See [principles.md](principles.md) Principle 14 for computation details.

## Key Learnings from Triage

### Learning 1: LSASS Spike Is Often a Recovery Artifact, Not the Root Cause
In most triaged incidents, **Frozen VM** events (Disk IO hangs of 7–84 seconds detected by MonMachineLocalWatchdog) preceded the LSASS spike. The LSASS spike occurs when the VM **unfreezes** and LSASS processes the accumulated TLS handshake backlog in a burst. The causal chain is:
```
Frozen VM → XStore IO collapses → SQL backend unavailable → Login errors begin
→ VM unfreezes → LSASS processes TLS backlog → 2,600–4,900% spike
→ Clients retry → Login cascade → Connection pool exhaustion
```
Always check MonMachineLocalWatchdog **before** concluding LSASS is the root cause.

### Learning 2: Cross-Node LSASS Impact
An LSASS spike on a **neighbor node** in the same cluster can cause login failures on the hosting node **without any local LSASS spike**. Shared infrastructure contention (network, storage fabric) can propagate impact across nodes. If the hosting node shows login system errors but LSASS stays at 2-6%, check other nodes in the same cluster for LSASS spikes.

### Learning 3: Multi-Node Upgrade Waves
OS upgrade waves affect multiple nodes on the same cluster sequentially. One node's LSASS incident does not prevent the next node from being hit. When investigating, check if other nodes in the same cluster had LSASS spikes in the preceding hours — this strengthens the OS-upgrade correlation.

### Learning 4: XStore IO Collapse is a Symptom, Not a Cause
In incidents with high XStore baselines (100K+ requests/5min), XStore IO collapses to near-zero **during** Frozen VM events. This is a symptom of the VM being unresponsive, not a trigger for the LSASS spike. XStore IO recovers with a burst **after** the freeze resolves. Do not classify as XStore-driven unless XStore spiked **before** the freeze.

### Learning 5: Node Movement as Confirmation Signal
After LSASS incidents, login counts shift from the affected node to a different node within 30–60 minutes. Checking for a drop in MonLogin volume on the hosting node post-incident confirms the database was moved. This is consistent with the no-failover pattern — Service Fabric sees the node as "up" during the incident, but moves the database afterward.

### Learning 6: OS Upgrade Temporal Correlation (Not Direct Causation)
In many triaged incidents, an OS upgrade occurred on the same node within 30–90 minutes after the LSASS incident. However, **the OS upgrade itself is not the direct cause** of the LSASS spike. The causal chain involves infrastructure activity during the upgrade window — specifically, Service Fabric system service replica movements (see Learning 7). Check LSASS900 (MonRgLoad guest_os_version) for version changes, but use this as a correlating signal to investigate ImageStore movements, not as the root cause itself.

### Learning 7: ImageStore Replica Builds — Strong Correlation with LSASS Spikes

**This is the strongest correlation found across investigated incidents.** Most "Residual LSASS" spikes during OS upgrade windows were temporally correlated with **Service Fabric ImageStore replica movements** landing on the affected node.

**Mechanism**:
1. During OS upgrades, Service Fabric evacuates nodes one UD (Upgrade Domain) at a time
2. System service replicas (ImageStore, NamingService, FaultAnalysisService, ResourceOrchestratorService) are moved to other nodes
3. When ImageStore builds a new replica on a node, it performs heavy TLS operations — certificate chain validation and CRL (Certificate Revocation List) checks
4. `CertGetCertificateChain()` is called with network-fetching flags (`0x40000000 | CERT_CHAIN_CACHE_END_CERT | CERT_CHAIN_REVOCATION_ACCUMULATIVE_TIMEOUT`)
5. If the CRL cache is cold or expired, lsass.exe opens HTTP connections to external CRL/OCSP endpoints for every certificate in the chain
6. Each connection blocks up to the system default timeout — with 90+ concurrent TLS handshakes, timeouts stack causing 90+ second `CertGetCertificateChain` durations
7. The CRL offline fallback (`CERT_CHAIN_REVOCATION_CHECK_CACHE_ONLY`) only kicks in **after** the first failure has been cached — the initial calls hit the network

**Evidence from multi-cluster analysis**:
- 70% of extreme LSASS spikes (>1000%) across multiple clusters were preceded by ImageStore moves within 10 minutes
- The highest-severity spikes were ALL ImageStore-correlated
- Over 50% of unexplained telemetry gaps were preceded by ImageStore arrival
- The timeline is precise: ImageStore lands on a node → telemetry goes dark within seconds → login failures begin within 2 minutes

**Key tables for investigation**:
- `WinFabLogs` (TaskName=CRM, EventType=Operation) — system service replica placement decisions
- `WinFabLogs` (TaskName=RM, EventType=Replica) — repair task timing for OS upgrade lifecycle
- `WinFabLogs` (TaskName=ImageStore/ImageStoreClient) — ImageStore internal operations

**SF configuration mitigations** (being investigated):
- `ClusterManager.ImageBuilderApplicationJobQueueMaxPendingWorkCount` — limits parallel ImageBuilder processes
- `ClusterManager.ImageBuilderUpgradeJobQueueMaxPendingWorkCount` — limits upgrade-related parallel work

### Learning 8: LoginOutages Wait Types Reveal the LSASS Signature

The `LoginOutages` table classifies outages with specific SQL wait types that fingerprint LSASS-caused delays:

| Wait Type | Meaning | LSASS Involvement |
|-----------|---------|-------------------|
| `PREEMPTIVE_OS_AUTHENTICATIONOPS` | LSASS authentication operations stalling | Direct — TLS handshake blocked in LSASS |
| `PREEMPTIVE_OS_CRYPTACQUIRECONTEXT` | Crypto context acquisition stalling | Direct — CRL/certificate validation in LSASS |
| `DISPATCHER_QUEUE_SEMAPHORE` | Internal queue contention | Indirect — system under load |

**Login failure signature**: Failures with **error=0, state=0** across GW (xdbgateway), XDBHost, and SQLServer packages simultaneously — no SQL-level error, purely authentication timeout.

### Learning 9: Node Health Lifecycle During Upgrades

`MonClusterLoad` with `event == "node_state_report"` tracks node health transitions during upgrades:

| State | Status | Meaning |
|-------|--------|---------|
| Ok | Up | Normal operation |
| Warning | Up | Pre-upgrade preparation — Frozen VM events correlate here |
| Warning | Disabling | Node being drained for upgrade |
| Error | Down | Node powered off for OS disk swap |
| Ok | Disabled | New OS booted, not yet accepting workloads |
| Ok | Up | Node back online with new OS |

The `Warning/Up` phase is when Frozen VM events and LSASS spikes typically occur — the node is still serving workloads while host infrastructure prepares for the upgrade.

### Learning 10: Slow Reconfiguration on Frozen Nodes

When a node is frozen/sluggish during upgrade preparation, Service Fabric reconfiguration operations (SwapPrimary) can take extremely long:
- `IReplicator.UpdateCatchupConfiguration()` — normally < 1s, was observed at **200 seconds** on frozen nodes
- Total reconfiguration duration: **395 seconds** (~6.5 min) vs normal ~3 seconds
- The Phase0_Demote step hangs because the SQL process on the frozen node cannot respond

This causes customer-visible downtime beyond what the LSASS spike alone explains — the database is unavailable for the entire reconfiguration duration.
