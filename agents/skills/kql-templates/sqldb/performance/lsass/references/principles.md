# Debug Principles for LSASS Telemetry Hole Analysis

## Principle 1: Correlation-Based Classification

Every LSASS spike must be classified by correlating it with login volume and XStore IO at the **same timestamp**. The classification determines root cause and escalation path.

**Decision Tree:**

```
LSASS CPU spike detected (> 5%)
├── Does MonLogin show a login volume spike at the same time?
│   ├── YES → Check temporal ordering
│   │   ├── Login spike BEFORE/SIMULTANEOUS with LSASS spike → Login-driven LSASS (Pattern 1)
│   │   │   └── Action: Investigate login surge (retry storm, pool reset, deployment)
│   │   └── Login spike AFTER LSASS spike → LSASS Cascade (Pattern 4)
│   │       └── Action: LSASS caused auth stall → retry storm amplified it
│   └── NO → Continue
├── Does MonSQLXStoreIOStats show an IO request spike at the same time?
│   ├── YES → XStore-driven LSASS (Pattern 2)
│   │   └── Action: Escalate to storage/XStore team
│   └── NO → Continue
├── Is LSASS showing a sustained step-change rather than a sharp spike?
│   ├── YES → LSASS Step-Change (Pattern 5)
│   │   └── Action: Check for ongoing crypto operations, investigate root cause
│   └── NO → Continue
└── Neither login nor XStore correlation found
    └── Check: Did system service replicas (ImageStore) land on this node?
        ├── YES → ImageStore-driven LSASS (Pattern 6)
        │   └── Action: Confirm via LSASS1100/1200 queries; escalate to SF/ImageStore team
        └── NO → Residual LSASS (Pattern 3)
            ├── Check: Did guest OS version change during the window?
            ├── Check: Is total CPU pegged (>90%)?
            └── Action: Escalate to OS/infrastructure team
```

## Principle 2: Temporal Alignment

When correlating across tables, use **matching time bins** to avoid false positives:
- LSASS CPU (MonCounterOneMinute): 1-minute granularity via TIMESTAMP
- MonLogin: bin to 10-minute intervals
- MonSQLXStoreIOStats: bin to 1-minute or 2-minute intervals
- Ensure overlap windows account for telemetry reporting delays (up to 2-3 minutes)

## Principle 3: LSASS CPU Severity Thresholds

| LSASS CPU % | Severity | Expected Impact |
|-------------|----------|-----------------|
| < 5% | Normal | No impact |
| 5–50% | Elevated | Possible authentication latency |
| 50–200% | High | 🚩 Likely causing login delays, may cause telemetry gaps |
| > 200% | Critical | 🚩 Severe — expect telemetry holes, authentication failures |
| > 1000% | Extreme | 🚩 System-wide impact — full CPU saturation likely |

Note: LSASS CPU % can exceed 100% on multi-core systems as the counter reflects aggregate across cores.

## Principle 4: Total CPU Correlation

- If Total Processor Time (_Total) is pegged (>90%) AND LSASS is the dominant process → LSASS is the root cause of CPU saturation
- If Total Processor Time is pegged but LSASS is NOT the dominant process → other processes are contributing; investigate per-process CPU
- If Total Processor Time is NOT pegged but LSASS is elevated → LSASS is causing isolated contention (e.g., authentication delays) without full CPU saturation

## Principle 5: OS Version Change Significance

When `LSASS900` (MonRgLoad) shows multiple `guest_os_version` values:

1. **Check temporal gap** between last data of old version and first data of new version
   - Gap indicates reboot/upgrade window
   - This gap often explains telemetry holes
2. **Check if LSASS spikes correlate with post-upgrade window**
   - Post-upgrade LSASS spikes are common (certificate operations, policy refresh)
   - These are **Residual LSASS** pattern
3. **Common upgrade patterns observed**:
   - Windows Server 2022 → Windows Server 2025: Major version upgrade
   - Empty `guest_os_version` rows may appear during transitional state

## Principle 6: Multi-Spike Analysis

A single incident may contain multiple LSASS spikes with **different classifications**:

| Time | LSASS % | Login Correlation | XStore Correlation | Classification |
|------|---------|-------------------|--------------------|----------------|
| 07:22 | 168% | No | Yes | XStore-driven |
| 09:31 | 1151% | No | No | Residual |

Each spike must be analyzed and classified independently. Do NOT assume all spikes in the same incident have the same root cause.

## Principle 7: XStore TLS Dependency

XStore IO operations depend on TLS connections, which LSASS processes:
- XStore request count spike → proportional TLS handshake increase → LSASS CPU increase
- This is mechanical/expected for high IO workloads
- The absence of this correlation (high LSASS without high XStore) is the key signal for Residual LSASS

## Principle 8: Telemetry Hole Confirmation

A telemetry hole is confirmed when:
1. **Expected periodic data is missing** from MonCounterOneMinute, MonSQLXStoreIOStats, or other tables
2. **The gap duration aligns** with LSASS spike or VM sluggish/frozen detection
3. **MonMachineLocalWatchdog** may or may not report during the hole (it depends on the watchdog thread itself being responsive)

🚩 If watchdog data is ALSO missing during the gap, the VM was likely completely unresponsive (frozen VM).

## Expected Timings

| Event | Normal | Warning | Critical |
|-------|--------|---------|----------|
| LSASS CPU | < 5% | 5–50% | > 50% |
| Total CPU (_Total) | < 80% | 80–90% | > 90% |
| Login volume change | < 2x normal | 2–5x normal | > 5x normal |
| XStore request spike | < 2x normal | 2–5x normal | > 5x normal |
| Watchdog TimeInSec | < 10s | 10–30s | > 30s |
| OS version gap | None | < 30 min | > 30 min |
| LSASS spike duration | < 1 min | 1–5 min | > 8 min |

## Principle 9: Temporal Ordering (Cascade Detection)

**CRITICAL**: When both LSASS spike and login spike are observed, determine which came FIRST:

| LSASS spike timing vs Login spike | Classification | Explanation |
|-----------------------------------|----------------|-------------|
| Login spike **before** LSASS spike | Pattern 1: Login-driven | Logins are the cause |
| Login spike **simultaneous** with LSASS spike | Pattern 1: Login-driven (likely) | Concurrent — logins likely driving |
| Login spike **after** LSASS spike (2–10 min delay) | Pattern 4: LSASS Cascade | LSASS stalled auth → retries amplified |

The 2–10 minute delay between LSASS spike and login spike is characteristic of the cascade pattern: clients experience timeouts, then retry, creating the login surge.

## Principle 10: Client-Side Impact Chain

When LSASS cascade (Pattern 4) is identified, the full impact chain is:

```
LSASS CPU spike (1K+%, 8-10 min)
  → Authentication processing stalls
    → Login requests queue and time out
      → Clients detect failures, begin retrying
        → Login request spike (retry storm)
          → Connection pool exhaustion on client side
            → Application-level failures
```

Key observations from App Service incidents:
- 🚩 No node failovers during the incident (LSASS impact ≠ failover)
- 🚩 Node movement may occur 30–60 minutes AFTER the incident (delayed response)
- 🚩 Worker thread exhaustion may develop as a secondary effect

## Principle 11: LSASS Step-Change Detection

Not all LSASS issues present as dramatic spikes. A **step-change** is:
- LSASS CPU rises to a sustained elevated level (50–85%) and stays there
- The elevation may last 10+ minutes
- Client impact occurs at lower thresholds than spike scenarios

**Detection**: Compare LSASS CPU baseline (before incident) vs. during incident:
- If LSASS was consistently < 5% and rises to 50–85% → step-change
- If LSASS shows a brief spike (1–2 min) then returns → transient spike (may be benign)
- If LSASS sustains > 50% for > 5 minutes → 🚩 step-change, likely impactful even without extreme values

**Historical example**: TR37719 / _DB_62 (Nov 2025) — LSASS at 68.5%, 85.3%, 39.7% caused 20+ minutes of client-side unresponsiveness. Networking team confirmed VM was unresponsive (not a network issue).

## Principle 12: VM Unresponsiveness Confirmation

When networking team reports packet drops:
- If EagleEye shows packet loss but NIC drops are < 0.1% → VM is unresponsive, not a network issue
- If VM is not responding with SYNACKs → VM-level problem (LSASS CPU saturation, frozen VM, or storage hang)
- This is a strong signal for LSASS cascade or residual patterns

## Principle 13: No-Failover Signal

🚩 The **absence** of node failovers during an LSASS incident is itself diagnostic:
- LSASS issues typically do NOT trigger node failovers
- The node remains "up" from Service Fabric's perspective but is unresponsive to clients
- Node movement (if any) occurs 30–60 minutes after the incident
- This distinguishes LSASS incidents from traditional availability issues (which involve failovers)

## Principle 14: Spike Factor Computation (Two-Problem Classification)

Every LSASS telemetry-hole incident must be classified as **Problem 1 (Residual)** or **Problem 2 (Direct)** using spike-factor analysis.

### Definitions

| Term | Definition |
|------|------------|
| **Telemetry hole start** | First missing or zero-value row in MonCounterOneMinute (or gap > 2× normal reporting interval) |
| **Telemetry hole end** | First row where monitoring data resumes after the gap |
| **Pre-outage window** | 30 minutes immediately before the telemetry hole start |
| **Baseline window** | 60 minutes of calm data — use the first 60 min of the investigation window; if that overlaps with the incident, use the last 60 min instead |
| **Baseline average** | Mean of the metric values during the baseline window |
| **Pre-outage peak** | Maximum of the metric values during the pre-outage window |
| **Spike factor** | Pre-outage peak ÷ baseline average |

### Spike Factor Thresholds

| Factor | Classification | Meaning |
|--------|---------------|---------|
| < 2× | No significant spike | Normal variance |
| 2×–3× | Borderline | Worth noting, but not conclusive on its own |
| ≥ 3× | **Significant spike** | 🚩 Strong signal that this metric contributed to the LSASS spike |
| ≥ 5× | **Major spike** | 🚩 Very likely a direct cause of the LSASS spike |
| ≥ 10× | **Extreme spike** | 🚩 Almost certainly the primary trigger |

### Classification Rules

```
Compute MonLogin spike factor (from LSASS350 data)
Compute XStore spike factor (from LSASS400/LSASS600 data)

IF MonLogin factor ≥ 3× OR XStore factor ≥ 3×:
    → Problem 2: Direct LSASS
    ├── MonLogin ≥ 3× only → Login-driven (check temporal order for Pattern 1 vs 4)
    ├── XStore ≥ 3× only → XStore-driven (Pattern 2)
    └── Both ≥ 3× → Combined trigger (identify which peaked first)
ELSE:
    → Problem 1: Residual LSASS (Pattern 3)
    └── Check for OS upgrade, infrastructure changes
```

### Edge Cases

- If the baseline window itself is anomalous (e.g., already elevated), note this and use the **lower** of the two windows as the true baseline
- If the pre-outage window has sparse data (telemetry already degrading), use the last available data points before the gap
- If multiple LSASS spikes exist, compute factors independently for each spike's pre-outage window

## Principle 15: Pre-Outage Temporal Correlation

For Problem 2 (Direct LSASS) incidents, **temporal ordering** between the external spike and the LSASS spike is critical.

### Correlation Window

The external spike (MonLogin or XStore) must peak **within 5 minutes before or simultaneous with** the LSASS CPU spike onset to be considered a direct cause.

| External Spike Timing (relative to LSASS spike) | Interpretation |
|--------------------------------------------------|----------------|
| 5 min before → simultaneous | **Direct cause** — external load drove LSASS via TLS |
| Simultaneous (within same time bin) | **Direct cause** (likely; bin resolution may hide the ordering) |
| 1–10 min **after** LSASS spike | **Cascade effect** — LSASS stalled auth → retry storm → login surge (Pattern 4) |
| > 10 min after | **Unrelated** — likely a separate event |
| > 5 min before, not sustaining into LSASS spike | **Weak correlation** — may be coincidental; note but do not classify as direct cause |

### Confirming Causation (Problem 2)

A Problem 2 classification requires **both**:
1. Spike factor ≥ 3× for MonLogin and/or XStore in the pre-outage window
2. The spike peak occurs within 5 minutes before (or simultaneous with) the LSASS spike onset

If condition 1 is met but condition 2 is not, report the spike factor but classify as **Problem 1 with elevated baseline** rather than Problem 2.

## Principle 16: ImageStore Replica Build Correlation (Pattern 6)

The strongest predictor of extreme LSASS spikes (>1000%) during OS upgrade windows is **ImageStore replica build operations** landing on the affected node. This was confirmed across 12 clusters with 70% correlation for >1000% spikes.

### Detection Method

1. Run **LSASS1100** (System Service Replica Movements) to find ImageStore/NamingService/FaultAnalysisService moves targeting the node
2. Run **LSASS1200** (Telemetry Gaps + System Service Correlation) for the combined view
3. Check if ImageStore `AddSecondary` or `MoveSecondary` landed on the node within 10 minutes before the LSASS spike

### Correlation Strength

| ImageStore Timing vs LSASS Spike | Correlation | Classification |
|----------------------------------|-------------|----------------|
| Same second / within 1 min | **Strongest** — direct causation | Pattern 6 |
| 1–10 min before | **Strong** — likely trigger | Pattern 6 |
| 10–15 min before | **Moderate** — possible | Needs additional signals |
| > 15 min before or not present | **None** | Not Pattern 6 |

### CRL Cache Mechanism

The root cause is the CRL (Certificate Revocation List) validation in LSASS during ImageStore TLS operations:

1. `CertGetCertificateChain()` is called with network-fetching flags
2. If CRL cache is cold or expired → HTTP connections opened to external CRL/OCSP endpoints
3. Each connection blocks up to system timeout (90+ seconds observed)
4. With 90+ concurrent TLS handshakes → timeout stacking → LSASS pegs all cores
5. The offline fallback (`CERT_CHAIN_REVOCATION_CHECK_CACHE_ONLY`) only activates AFTER the first failure is cached — initial calls always hit the network

### Multiple System Services Landing Simultaneously

A burst of 2–3 system service replicas (ImageStore + NamingService + FaultAnalysisService) landing on the same node in the same second amplifies the impact. The LSASS spike severity correlates with the number of simultaneous system service placements.

## Principle 17: LoginOutages Wait Type Fingerprinting

The `LoginOutages` table provides definitive proof that LSASS is the bottleneck via SQL wait types:

| Wait Type | Duration | Confirms |
|-----------|----------|----------|
| `PREEMPTIVE_OS_AUTHENTICATIONOPS` > 10s | Login blocked in LSASS TLS | LSASS-caused delay |
| `PREEMPTIVE_OS_CRYPTACQUIRECONTEXT` > 10s | CRL/certificate validation blocked | CRL network timeout |
| No error code (error=0, state=0) on failed logins | Authentication timeout, not SQL error | LSASS-level, not SQL-level |

If LoginOutages shows `HighLatencyLogin` with `PREEMPTIVE_OS_AUTHENTICATIONOPS` or `PREEMPTIVE_OS_CRYPTACQUIRECONTEXT`, this is conclusive evidence of LSASS/CRL-caused login failures.

### Combined Trigger Analysis

When both MonLogin and XStore spike ≥ 3×:
1. Identify which peaked first — this is the **primary trigger**
2. The secondary metric may be amplifying (e.g., login surge also drives XStore TLS connections)
3. Report both factors and the temporal sequence
