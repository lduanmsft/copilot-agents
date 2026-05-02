# Debug Principles for XDBHost High TCP Rejections

!!!AI Generated.  To be verified!!!

## Triage Principles

1. **This is a node-level alert, not a database-level alert**: The ICM title contains the ClusterName and NodeName. Logical server/database names are usually NOT in the ICM — they must be discovered from telemetry (MonLogin instance_name, MonAnalyticsDBSnapshot reverse lookup).

2. **High TCP rejections = sustained issue, not a single event**: Unlike a single XdbHost restart, this alert fires only when **both** conditions are sustained for 1 hour (12/12 evaluations): `\Microsoft Winsock BSP\Rejected Connections/sec` > 150 **AND** `\Process(_Total)\Handle Count` > 600,000. Expect a crash-dump-restart loop lasting 30 minutes to 2+ hours, not a brief 1-2 minute restart window.

3. **Handle count signals resource exhaustion**: Each login creates two handles (one on XDBHost, one on SQL). Unreleased handles cause handle leaks → socket exhaustion → TCP rejections. A handle count > 600K alongside rejections confirms resource exhaustion rather than transient network congestion.

4. **LSASS is the most common root cause**: Check LSASS CPU before investigating XdbHost internals. If LSASS % Privileged Time is elevated (> 50%) during the TCP rejection window, the XdbHost stalls are secondary to authentication pressure.

5. **Dumps are both a symptom and an amplifier**: The `Stalled IOCP Listener` dump is a diagnostic response, but the dump process itself is heavyweight and often causes XdbHost to crash. The dump-crash-restart cycle is self-reinforcing.

## Diagnosis Principles

### Principle 1: Correlate TCP Rejections with LSASS Stress

- TCP rejections (TR100) should align temporally with LSASS elevation (TR200)
- If LSASS elevation starts BEFORE TCP rejections → LSASS is the driver
- If TCP rejections start WITHOUT LSASS elevation → investigate other causes (port exhaustion, XdbHost internal issue)
- 🚩 LSASS > 100% Privileged Time is a strong signal of authentication overload

### Principle 2: Count Process IDs to Classify Severity

- 1-2 process IDs → Single restart, reroute to `xdbhost-restart` skill
- 3-10 process IDs → Moderate crash loop
- 🚩 > 10 process IDs → Severe crash loop, likely requires manual failover
- 🚩 > 20 process IDs in 2 hours → Critical, node is in continuous crash cycle

### Principle 3: Classify Dumps to Understand the Crash Pattern

- **Stalled IOCP Listener only** → XdbHost is stalling but not crashing from the dump (unusual)
- **Alternating Stalled IOCP Listener → SqlDumpExceptionHandler** → Classic crash-dump-restart cycle
- **SqlDumpExceptionHandler only** → XdbHost is crashing without a preceding stall dump (investigate unhandled exceptions)
- Stack traces with `SocketDupInstance::DestroyConnectionObjects_v2` → ConnectionCloseDumps pattern

### Principle 4: Identify the Workload Driver

- Check login volume by instance (TR600) — one instance may dominate
- High login volume from one database can overwhelm LSASS on the node
- 🚩 > 100,000 logins from a single instance in a 2-hour window = likely workload driver
- If login volume is normal across all instances, the LSASS stress may be from XStore IO TLS operations, ImageStore CRL operations (during upgrades), Frozen VM backlog bursts, or other non-login sources — run [Performance/LSASS skill](../../../../Performance/LSASS/SKILL.md) for deeper classification

### Principle 5: Check Automation Before Suggesting Mitigation

- SqlRunner typically tries DumpProcess → KillProcess on xdbhostmain; if that fails, may escalate to KillProcess on sqlservr
- 🚩 KillProcess on sqlservr indicates the issue has escalated beyond XdbHost
- **Always check TR500 results** before recommending manual XDBHost restart:
  - If `KillProcess` targeting `xdbhostmain` found **AND** last process_id in TR300 stable > 10 min **AND** login volume (TR610) normalized → automation already mitigated; monitor only
  - If `KillProcess` found but crash loop persists → automation failed; recommend manual XDBHost restart or failover
  - If no automation action found → suggest manual XDBHost restart as first-line mitigation

### Principle 6: Self-Mitigation vs Manual Failover

- If the crash loop stops on its own (final process_id stabilizes for > 10 minutes) → self-mitigated
- If a manual failover was performed (visible in ICM discussion or MonNonPiiAudit) → manual mitigation
- 🚩 Issue did NOT self-mitigate if the ICM mitigation mentions "failover" — the node was still unhealthy

## Expected Timings

| Event | Normal | Warning | Critical |
|-------|--------|---------|----------|
| LSASS % Privileged Time | < 10% | 10-50% | > 50% |
| TCP rejections sustained duration | < 5 minutes | 5-30 minutes | > 30 minutes |
| Number of XdbHost process IDs | 1-2 | 3-10 | > 10 |
| Number of dumps | 0-2 | 3-10 | > 10 |
| Login volume per instance | < 500/min | 500-2500/min | > 2500/min |
| Time to mitigation | < 15 minutes | 15-60 minutes | > 60 minutes |

## Root Cause Classification

| Evidence Pattern | Root Cause | RCA Label |
|-----------------|------------|-----------|
| LSASS > 100% + one instance with high login volume | High login volume from one DB driving LSASS stress | ConnectionCloseDumps / HighLoginVolume |
| LSASS > 100% + no dominant instance | General node-level authentication pressure | ConnectionCloseDumps / LsassStress |
| LSASS normal + Stalled IOCP Listener dumps | XdbHost internal stall (not LSASS-driven) | ConnectionCloseDumps / IOCPStall |
| LSASS > 100% + no dominant instance + XStore spike | XStore IO TLS operations driving LSASS | Defer to Performance/LSASS skill (XStore-driven) |
| LSASS > 100% + no dominant instance + OS upgrade window | ImageStore replica build CRL/TLS operations | Defer to Performance/LSASS skill (ImageStore-driven) |
| LSASS > 100% + Frozen VM watchdog events | VM-level hang → LSASS backlog burst on unfreeze | Defer to Performance/LSASS skill (Frozen VM) |
| Worker/session at 100% + crash loop | Instance resource exhaustion contributing to node stress | ConnectionCloseDumps / ResourceExhaustion |
| No clear pattern | Unknown — escalate | Escalate to engineering |

## Escalation Criteria

- 🚩 Crash loop does not self-resolve after 1 hour
- 🚩 Manual failover was required (issue did not self-mitigate)
- 🚩 Same node experiences repeat incidents within 7 days
- 🚩 LSASS elevation has no clear workload driver
- 🚩 Unknown crash pattern (no Stalled IOCP Listener, no SqlDumpExceptionHandler)
- 🚩 Stack traces show new/unfamiliar code paths
