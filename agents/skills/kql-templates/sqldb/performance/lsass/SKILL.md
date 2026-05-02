---
name: LSASS
description: Diagnoses LSASS-related incidents with telemetry holes by analyzing CPU usage (total and per-core), LSASS process CPU, login activity correlation (MonLogin), XStore IO stats, local watchdog sluggish/frozen VM detection, virtual file IO stalls, resource governor load, guest OS version changes, and Service Fabric ImageStore replica build correlation. Classifies LSASS spikes as login-driven, XStore-driven, ImageStore-driven, residual, or cascade. Use when investigating LSASS high CPU, telemetry gaps, or node-level resource contention.
---

# LSASS Telemetry Hole Analysis

## Skill Overview

This skill diagnoses LSASS-related incidents where telemetry holes are observed. It investigates the problem from multiple angles:

1. **Total CPU usage** at the node level (Processor(_Total))
2. **Per-core CPU analysis** to detect pegged/saturated cores
3. **LSASS process CPU** to determine if LSASS is consuming excessive CPU
4. **Login activity** via MonLogin to correlate LSASS spikes with TLS handshake volume
5. **XStore IO stats** (request counts, read/write throughput in Mbps)
6. **Machine local watchdog** for sluggish VM and frozen VM detection
7. **Virtual file IO stalls** via MonSqlRgHistory
8. **Resource Governor load** and guest OS version via MonRgLoad

### LSASS Spike Classification

LSASS spikes fall into six observed patterns (see [references/knowledge.md](references/knowledge.md) for details):

| Pattern | LSASS Spike | Login Spike | XStore Spike | Total CPU | Description |
|---------|-------------|-------------|--------------|-----------|-------------|
| **Login-driven** | Yes | Yes (before/simultaneous) | No | May spike | Login volume drives TLS handshakes in LSASS |
| **XStore-driven** | Yes | No | Yes | May spike | XStore IO operations trigger LSASS activity |
| **Residual** | Yes | No | No | Often pegged | LSASS spike has no clear external trigger; often coincides with OS upgrade |
| **Cascade** | Yes (1K+, 8-10 min) | Yes (AFTER LSASS spike) | Varies | Often pegged | LSASS spike causes auth stall, triggering retry storms and login surge |
| **Step-change** | Sustained elevation (50-85%) | Varies | Varies | May not spike | Persistent LSASS elevation rather than sharp spike; still causes client failures |
| **ImageStore-driven** | Yes (1K-21K%, within seconds) | No (before) | No (before) | Often pegged | Strong correlation with SF ImageStore replica build during upgrade windows; CRL/TLS operations suspected trigger |

### Two-Problem Framework

Every LSASS telemetry-hole incident is classified into one of two top-level problems:

| Problem | Name | Definition | Key Signal |
|---------|------|------------|------------|
| **Problem 1** | Residual LSASS | LSASS spike causes a telemetry hole but **no significant pre-outage spike** in MonLogin or XStore is detected. No clear external trigger. Often correlates with OS upgrades or infrastructure changes. | Spike factor < 3× for both MonLogin and XStore in the pre-outage window |
| **Problem 2** | Direct LSASS | XStore and/or MonLogin spike by a **significant factor** (≥ 3×) just before the telemetry outage, directly causing the LSASS spike via TLS handshake load. | Spike factor ≥ 3× for MonLogin and/or XStore in the pre-outage window |

**Spike Factor** = (pre-outage peak value) / (baseline average). See [references/principles.md](references/principles.md) Principle 14 for computation details.

The two-problem classification is determined in **Task 13** after all individual queries have been executed.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{ClusterName}` | Tenant ring/cluster name | string | `tr2512.brazilsouth1-a.worker.database.windows.net` |
| `{DBNodeName}` | Node name hosting the replica | string | `_DB_9` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm:ss | `2026-03-05 04:00:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm:ss | `2026-03-05 10:00:00` |

### Optional Parameters (overrides)

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{MidTime}` | Center time of incident (StartTime/EndTime derived as +/- 3h) | UTC datetime | `2026-03-05 07:02:30` |

## Execution Steps

### Task 1: Obtain Kusto cluster information

**CRITICAL:** Always identify the correct cluster - do NOT use default clusters.

Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../../Common/execute-kusto-query/references/getKustoClusterDetails.md](../../Common/execute-kusto-query/references/getKustoClusterDetails.md)

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Total CPU Usage (Processor _Total)

Execute query **LSASS100** from [references/queries.md](references/queries.md).

#### Analysis
- Look for sustained CPU > 90% which could explain telemetry holes
- Correlate CPU spikes with the telemetry gap window
- 🚩 Flag if total CPU is pegged at 100% for extended periods

### Task 3: Per-Core CPU Analysis (Pegged Cores)

Execute query **LSASS200** from [references/queries.md](references/queries.md).

#### Analysis
- Identify individual cores with MaxVal > 90%
- Look for patterns where specific cores are consistently pegged
- 🚩 Flag if multiple cores are pegged simultaneously — indicates severe CPU contention

### Task 4: LSASS Process CPU Usage

Execute query **LSASS300** from [references/queries.md](references/queries.md).

#### Analysis
- Check if LSASS is consuming significant CPU (> 5%)
- Correlate LSASS CPU spikes with telemetry gaps
- 🚩 Flag if LSASS CPU is the dominant consumer — LSASS high CPU can cause authentication delays and telemetry collection failures

### Task 5: Login Activity Correlation (MonLogin)

Execute query **LSASS350** from [references/queries.md](references/queries.md).

#### Analysis
- Compare login volume timeline against LSASS CPU timeline from Task 4
- Check for login spikes correlating with LSASS spikes
- Check for system error login failures during LSASS spikes
- 🚩 **CRITICAL — Check temporal ordering**:
  - If login spike comes **before/simultaneous** with LSASS spike → **Login-driven LSASS** (Pattern 1)
  - If login spike comes **after** LSASS spike (2–10 min delay) → **LSASS Cascade** (Pattern 4) — clients retrying after auth stall
- 🚩 If NO login spike during LSASS spike → proceed to check XStore correlation (Tasks 6-8)
- Check for connection pool exhaustion signals (sustained high failed logins)

### Task 6: XStore Request Counts

Execute query **LSASS400** from [references/queries.md](references/queries.md).

#### Analysis
- Look for sudden drops in XStore requests (indicates IO stalls or connectivity issues)
- Look for abnormal spikes in request counts
- 🚩 Flag gaps in XStore request data — correlates with telemetry holes
- 🚩 If XStore spike correlates with LSASS spike (but no login spike) → **XStore-driven LSASS** pattern

### Task 7: XStore IO Throughput (Mbps)

Execute query **LSASS500** from [references/queries.md](references/queries.md).

#### Analysis
- Check read/write throughput patterns
- Look for periods of zero throughput that correlate with the telemetry hole
- 🚩 Flag abnormal throughput patterns (sudden drops or extreme spikes)

### Task 8: XStore IO Request Counts (Granular)

Execute query **LSASS600** from [references/queries.md](references/queries.md).

#### Analysis
- Examine per-minute IO request counts for fine-grained pattern detection
- Correlate with Tasks 6-7 to confirm IO stall patterns
- 🚩 Flag gaps or drops in IO request counts

### Task 9: Machine Local Watchdog (Sluggish/Frozen VM)

Execute query **LSASS700** from [references/queries.md](references/queries.md).

#### Analysis
- Check for "Sluggish VM" detections (sluggish detection thread)
- Check for "Frozen VM" detections (Disk IO spent)
- 🚩 Flag TimeInSec > 30s for sluggish detections — indicates severe VM responsiveness issues
- 🚩 Flag any frozen VM detections — indicates storage hangs that cause telemetry holes

### Task 10: Virtual File IO Stalls

Execute query **LSASS800** from [references/queries.md](references/queries.md).

#### Analysis
- Check delta_io_stall_read_ms_perc and delta_io_stall_write_ms_perc
- 🚩 Flag if IO stall percentage > 50% — indicates storage-level bottleneck
- Correlate high IO stalls with XStore throughput drops from Tasks 6-8

### Task 11: Guest OS Version Changes (MonRgLoad)

Execute query **LSASS900** from [references/queries.md](references/queries.md).

#### Analysis
- Check if guest OS version changed during the incident window
- 🚩 Flag OS version changes that coincide with telemetry gaps — may indicate a host update/reboot

### Task 12: Azure Compute VM Details & Host Analyzer

Execute query **LSASS1000** from [references/queries.md](references/queries.md).

> **⚠️ MANDATORY CONNECTION CHANGE**: This query MUST be executed against cluster `https://sqlstage.kusto.windows.net` with database `sqlazure1`. You MUST switch the Kusto connection for this query — do NOT use the region-specific cluster from Task 1. After executing this query, switch back to the region-specific cluster for any subsequent queries.

#### Analysis
- Extract `VirtualMachineUniqueId`, `NodeId`, and `ContainerId` for the SQL node
- 🚩 If multiple rows exist with different `NodeId` values, the VM was live-migrated during the window
- Construct the **Azure Host Analyzer** link:
  ```
  https://asi.azure.ms/services/Azure%20Host/pages/Azure%20VM?containerId={ContainerId}&nodeId={NodeId}&virtualMachineUniqueId={VirtualMachineUniqueId}&globalFrom={StartTimeISO}&globalTo={EndTimeISO}
  ```
- Present the link in the output so the DRI can inspect host-level events (planned maintenance, reboots, live migrations, hardware errors)

### Task 13: Pre-Outage Spike Factor & Correlation Analysis

This task synthesizes data from Tasks 4, 5, 6, and 8 to classify the incident as **Problem 1 (Residual)** or **Problem 2 (Direct)**.

#### Step 13a: Identify the Telemetry Hole Window

Use **LSASS1200** from [references/queries.md](references/queries.md) to programmatically detect telemetry gaps on the node. This query finds gaps > 2 minutes in MonCounterOneMinute data and correlates them with system service moves — this is more reliable than manually inspecting missing rows.

Alternatively, if LSASS1200 cannot be run (requires MFA Kusto access), manually identify gaps using the LSASS CPU data from Task 4 and Total CPU data from Task 2:
1. Identify the **telemetry hole start** — the last timestamp before monitoring data gaps begin
2. Identify the **telemetry hole end** — the first timestamp where monitoring data resumes
3. Note: Telemetry holes can be caused by LSASS spikes, Frozen VM events, OS upgrade reboots, or other infrastructure events. Do not assume a single cause — correlate with other signals.
4. Define the **pre-outage window** as the 30-minute period immediately before the telemetry hole start
5. Define the **baseline window** as the first 60 minutes of the investigation window (assumed calm period). If the incident starts close to the beginning of the window, use the last 60 minutes instead.

#### Step 13b: Compute MonLogin Spike Factor

Using the MonLogin data from Task 5:
1. Compute **baseline average** = average of `Total Logins` values during the baseline window
2. Compute **pre-outage peak** = maximum `Total Logins` value during the pre-outage window
3. **MonLogin spike factor** = pre-outage peak / baseline average
4. 🚩 If spike factor ≥ 3×, MonLogin is a significant contributor

#### Step 13c: Compute XStore Spike Factor

Using the XStore data from Tasks 6 and 8:
1. Compute **baseline average** = average of `sum_total_requests` (LSASS400) or `sum_total_xio_requests` (LSASS600) during the baseline window
2. Compute **pre-outage peak** = maximum value during the pre-outage window
3. **XStore spike factor** = pre-outage peak / baseline average
4. 🚩 If spike factor ≥ 3×, XStore is a significant contributor

#### Step 13d: Classify into Problem 1 or Problem 2

Apply the decision logic from [references/principles.md](references/principles.md) Principle 14:

| MonLogin Factor | XStore Factor | Classification | Pattern |
|-----------------|---------------|----------------|---------|
| ≥ 3× | Any | **Problem 2 (Direct)** — Login-driven | Pattern 1 or 4 (check temporal order) |
| < 3× | ≥ 3× | **Problem 2 (Direct)** — XStore-driven | Pattern 2 |
| ≥ 3× | ≥ 3× | **Problem 2 (Direct)** — Combined Login + XStore | Pattern 1/2 hybrid |
| < 3× | < 3× | **Problem 1 (Residual)** | Pattern 3 (check OS upgrade) |

#### Step 13e: Temporal Correlation Check (Problem 2 only)

If classified as Problem 2:
1. Confirm the spike **precedes or is simultaneous with** the LSASS CPU spike (from Task 4)
2. Check: Does the XStore/MonLogin spike peak occur within 5 minutes before the LSASS spike onset?
3. If the spike occurs **after** the LSASS spike, reclassify — this may be a Cascade (Pattern 4) rather than a direct cause
4. 🚩 If both XStore and MonLogin spike before LSASS, note as **combined trigger** and identify which peaked first

### Task 14: ImageStore Replica Build Correlation (Pattern 6 Detection)

This task checks whether Service Fabric system service replica movements (especially ImageStore) landed on the affected node, triggering the LSASS spike via CRL/TLS operations. This is the **confirmed root cause** for most upgrade-related LSASS spikes.

> **⚠️ IMPORTANT**: This task requires access to WinFabLogs, which may be on the MFA Kusto cluster (e.g., `sqlazurewus2.kustomfa.windows.net`) rather than the standard cluster.

#### Step 14a: Check System Service Moves

Execute query **LSASS1100** from [references/queries.md](references/queries.md).

**What to look for**:
- `ImageStoreService` operations (`AddSecondary`, `MoveSecondary`) targeting the affected node
- Other system services (NamingService, FaultAnalysisService, ResourceOrchestratorService) in the same burst
- FaultDomain constraint violations driving the moves
- 🚩 ImageStore landing within 10 minutes before the LSASS spike = **Pattern 6 confirmed**

#### Step 14b: Correlate Telemetry Gaps with System Service Moves

Execute query **LSASS1200** from [references/queries.md](references/queries.md).

**What to look for**:
- `TELEMETRY_DARK` signals aligned with `SYS_MOVE` signals on the same node
- 🚩 ImageStore landing at the exact start of a telemetry gap is the strongest evidence

#### Step 14c: Classify Pattern 6

If ImageStore correlation is found:
- Reclassify any **Problem 1 (Residual)** from Task 13 as **Pattern 6 (ImageStore-driven)**
- The root cause is CRL cache misses during ImageStore TLS operations, not an unknown trigger
- **Escalation**: SF/ImageStore team for further investigation

### Task 15: LoginOutages Wait Type Analysis (Optional)

If `{LogicalServerName}` and `{LogicalDatabaseName}` are available, execute query **LSASS1300** from [references/queries.md](references/queries.md).

**What to look for**:
- `PREEMPTIVE_OS_AUTHENTICATIONOPS` — confirms LSASS authentication bottleneck
- `PREEMPTIVE_OS_CRYPTACQUIRECONTEXT` — confirms CRL/certificate validation blocking
- 🚩 These wait types with durations > 10 seconds are conclusive evidence of LSASS-caused login outages

### Task 16: Node Health State Lifecycle (Optional)

Execute query **LSASS1500** from [references/queries.md](references/queries.md).

**What to look for**:
- The `Warning/Up` → `Disabling` → `Down` → `Disabled` → `Up` transition sequence
- The `Warning/Up` phase correlates with Frozen VM events and LSASS spikes
- `node_up_time` resets confirming the OS reboot

### Task 17: OS Upgrade Repair Task Timeline (Optional)

Execute query **LSASS1400** from [references/queries.md](references/queries.md).

**What to look for**:
- Repair task timeline showing when each UD (Upgrade Domain) was Created → Preparing → Executing → Restoring
- Correlate with the affected node's telemetry hole — did the telemetry gap overlap with a repair task window?
- 🚩 Telemetry gaps that do NOT overlap any repair task are "unexplained" and more likely ImageStore-driven (Pattern 6)

### Task 18: Multi-Cluster LSASS Spike + ImageStore Correlation (Optional — Fleet Analysis)

When investigating a fleet-wide LSASS issue across multiple clusters, execute query **LSASS1600** from [references/queries.md](references/queries.md).

**What to look for**:
- Provide a list of cluster names as `{ClusterList}` (dynamic array)
- The query finds all LSASS spikes > 1000%, classifies them as REPAIR or UNEXPLAINED, and checks ImageStore correlation
- 🚩 High percentage of ImageStore-correlated spikes across multiple clusters strengthens Pattern 6 classification

## Output

Generate a summary report with:

1. **Timeline**: Chronological list of events correlated across all queries
2. **Two-Problem Classification** (from Task 13):

   | LSASS Spike Time | LSASS CPU % | MonLogin Factor | XStore Factor | Pre-Outage Temporal Order | Problem | Classification |
   |-------------------|-------------|-----------------|---------------|--------------------------|---------|----------------|
   | (timestamp) | (value) | (X.X×) | (X.X×) | Login→LSASS / XStore→LSASS / None | 1 or 2 | Residual / Login-driven / XStore-driven / Combined |

3. **Root Cause Hypothesis**: Based on the classification and data, determine if the telemetry hole was caused by:
   - **Problem 2 — Direct LSASS (Login-driven)** (Pattern 1): MonLogin spiked ≥ 3× baseline before the outage → TLS handshake load drove LSASS CPU
   - **Problem 2 — Direct LSASS (XStore-driven)** (Pattern 2): XStore IO spiked ≥ 3× baseline before the outage → TLS-dependent IO drove LSASS CPU
   - **Problem 2 — Direct LSASS (Combined)**: Both MonLogin and XStore spiked ≥ 3× before the outage
   - **Problem 1 — Residual LSASS** (Pattern 3): Neither MonLogin nor XStore spiked significantly → no clear external trigger
   - **Problem 2 → Cascade** (Pattern 4): Initial LSASS spike (any cause) → auth stall → retry storm → login surge AFTER LSASS spike

   Additionally, the telemetry hole may involve:
   - **ImageStore-driven LSASS** (Pattern 6): SF ImageStore replica build correlated with the spike → CRL/TLS operations in LSASS may have caused extreme CPU. Check LSASS1100/1200 for correlation evidence. Escalate to SF/ImageStore team for further analysis.
   - **VM-level issue**: Sluggish/frozen VM condition (host infrastructure)
   - **Storage IO stalls**: XStore/disk-level bottleneck
   - **OS upgrade temporal correlation**: OS version change observed in the same window (correlating signal, not necessarily direct cause — investigate ImageStore and other triggers)
   - **LSASS Step-Change** (Pattern 5): Sustained moderate LSASS elevation (50–85%) without dramatic spike
   - **Combination of factors**: Multiple contributing causes
4. **Client-Side Impact Assessment** (for Cascade/Step-Change patterns):
   - Were node failovers observed? (typically NO for LSASS issues)
   - Was node movement observed 30–60 min after?
   - Was worker thread exhaustion detected as a secondary effect?
   - Did networking diagnostics confirm VM unresponsiveness (vs. network issues)?
5. **Evidence Table**: Key findings from each query with timestamps
5. **Recommendations**: Next steps for mitigation or escalation
   - For login-driven: investigate login surge source, connection pooling, retry storms
   - For XStore-driven: escalate to storage/XStore team
   - For residual: check for ImageStore correlation (Task 14) first; if no ImageStore correlation, investigate other infrastructure activities during the window
   - For cascade: investigate root cause of initial LSASS spike; advise clients on exponential backoff retry policies; check for worker thread exhaustion
   - For step-change: investigate sustained crypto operations; compare with pre-incident LSASS baseline
   - For OS upgrade correlation: investigate ImageStore movements (LSASS1100/1200) as the specific trigger within the upgrade window; escalate to SF/ImageStore team if correlation confirmed
