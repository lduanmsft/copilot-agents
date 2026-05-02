# Terms and Concepts

!!!AI Generated.  To be verified!!!

## Core Concepts

### XdbHost High TCP Rejections

A node-level Health Hierarchy alert indicating that the XdbHost process on a DB node is rejecting incoming TCP connections at a rate above the configured threshold. Unlike a simple XdbHost restart (single process_id change), high TCP rejection incidents involve a **crash-dump-restart loop** where XdbHost repeatedly crashes, dumps, and restarts — never stabilizing long enough to serve connections.

## Alert Definition

**Monitor Name**: XDBHost TCP Rejections (Unhealthy)

**Incident Title Pattern**:

```
[Health Hierarchy alert - {Monitor.Dimension.RegionName}] Node {Monitor.Dimension.NodeName} is unhealthy - XDBHost high TCP rejections
```

| Property | Value |
|----------|-------|
| **Health Status** | Unhealthy |
| **Severity** | 3 |
| **Time to detect** | 60 minutes |
| **Condition Type** | Regular |
| **Evaluation** | 12 out of 12 (consecutive) |

**Threshold Conditions** (both must be true for 1 hour):

1. `\Microsoft Winsock BSP\Rejected Connections/sec` > **150**
2. `\Process(_Total)\Handle Count` > **600,000**

**Why both conditions matter**:

- TCP rejections are done by the OS and indicate network congestion on the node
- High handle counts indicate resource exhaustion risk — each login creates two handles (one on XDBHost, one on SQL). If both handles are not released, it leads to a handle leak → socket exhaustion → TCP rejections
- The combination of sustained rejections AND high handle counts avoids alerting on transient spikes

### LSASS (Local Security Authority Subsystem Service)

LSASS is a critical Windows system process that handles user authentication, security policies, and auditing. It is involved when creating/managing HTTPS connections from clients and to backend services. When LSASS is under CPU stress (elevated % Privileged Time), all authentication-dependent operations stall — including XdbHost's IOCP listener threads that wait for authentication completions. This causes a cascading failure:

1. LSASS CPU spike → authentication delays
2. XdbHost IOCP threads stall waiting for auth → `Stalled IOCP Listener` detected
3. Dump is triggered → XdbHost crashes → restarts → encounters same LSASS pressure → repeats

**Common LSASS spike drivers** (see [Performance/LSASS skill](../../../../Performance/LSASS/SKILL.md) for full classification):

- **Login-driven**: High login volume (TLS handshakes per login) — check MonLogin
- **XStore-driven**: High storage IO (TLS-dependent XStore requests) — check MonSQLXStoreIOStats
- **ImageStore-driven**: SF ImageStore replica builds triggering CRL/TLS operations — check WinFabLogs
- **Frozen VM**: VM-level hang causing LSASS backlog burst on unfreeze — check MonMachineLocalWatchdog
- **Residual**: No clear external trigger, often correlates with OS upgrades

### Stalled IOCP Listener

An XdbHost self-diagnostic that detects when IOCP (I/O Completion Port) listener threads have not processed completions within an expected timeout. When detected, XdbHost triggers a diagnostic dump (`Stack Trace` / `Stalled IOCP Listener`) to capture the thread state. The dump itself is heavyweight and often causes the process to crash or be killed, restarting the cycle.

### ConnectionCloseDumps

An ICM RCA label applied when the crash loop is caused by the connection close code path. The stack trace typically shows:

```
xdbhost!SocketDupInstance::DestroyConnectionObjects_v2
xdbhost!SocketDupInstance::ErrorHandlingForSOSEnqueueTaskDirect
xdbhost!HostToInstanceControllerWriteDoneHandler_v2
xdbhost!SNIWriteDone
```

This indicates XdbHost is crashing in the socket duplication cleanup path, often triggered by high connection volume combined with LSASS delays.

### SqlDumpExceptionHandler

A dump error text indicating that XdbHost encountered an unhandled exception and crashed. Typically follows a `Stalled IOCP Listener` dump — the dump process itself destabilizes XdbHost, causing a fault. The alternating pattern of `Stalled IOCP Listener` → `SqlDumpExceptionHandler` is the signature of the crash-dump-restart loop.

### Winsock BSP Rejected Connections/sec

A Windows performance counter (`\\Microsoft Winsock BSP\\Rejected Connections/sec`) that measures the rate of TCP connection rejections at the Winsock Base Service Provider level on the node. Non-zero values indicate that incoming TCP connections are being refused — either because the listening process (XdbHost) is not available, or because the TCP backlog queue is full.

## Crash Loop Mechanism

The typical crash loop sequence:

```
1. LSASS stress begins (high authentication load on node)
   ↓
2. XdbHost IOCP listener stalls (waiting for auth completions)
   ↓
3. Stalled IOCP Listener detected → diagnostic dump triggered
   ↓
4. Dump is heavyweight → XdbHost destabilized
   ↓
5. SqlDumpExceptionHandler → XdbHost crashes
   ↓
6. New XdbHost process starts (new process_id)
   ↓
7. Immediately encounters same LSASS stress → back to step 2
   ↓
8. TCP rejections occur throughout because XdbHost is cycling
```

## Automation Responses

### SqlRunner DumpProcess + KillProcess

When the Health Hierarchy alert fires, SqlRunner (`sqlrunnerv2.sqltelemetry.azclient.ms`) may execute:

1. `DumpProcess` targeting `xdbhostmain` (fabric:/Worker) — captures diagnostic dump
2. `KillProcess` targeting `xdbhostmain` — terminates the process to force a clean restart

If XdbHost-level intervention fails, SqlRunner may escalate to:
3. `KillProcess` targeting `sqlservr` — kills a SQL Server instance on the node

### Manual Failover

If the crash loop does not self-resolve, an on-call engineer may failover the affected database to move it off the unhealthy node. This is the most common manual mitigation for persistent high TCP rejection incidents.

### Manual XDBHost Restart (Mitigation)

The primary mitigation for an ongoing XDBHost crash loop is to restart the XDBHost process via DSConsole. This is appropriate when automation (SqlRunner) has not already resolved the issue.

**Risks:** There is only one XDBHost process per node. Killing it affects all SQL instances on the node and all connections targeted at them — both new connections and those still in the XDBHost queue. Databases on the node are momentarily unavailable for new connections (order of seconds) until Service Fabric relaunches xdbhostmain.

**Procedure:** Collect a process dump first (skip if it takes > 1 minute), then kill the XDBHost process, then wait 10–15 minutes for stabilization. See SKILL.md Step 10 for the executable commands and post-mitigation verification steps.

## Key Telemetry Tables

| Table | Purpose in This Skill |
|-------|----------------------|
| **MonCounterOneMinute** | TCP rejection rates (`\\Microsoft Winsock BSP\\Rejected Connections/sec`) and LSASS CPU (`\\Process(Lsass)\\% Privileged Time`) |
| **MonXdbhost** | XdbHost process lifecycle — process_id changes confirm crash loop |
| **MonSqlDumperActivity** | Dump records — type classification (`Stalled IOCP Listener`, `SqlDumpExceptionHandler`) |
| **MonNonPiiAudit** | Automation actions — `DumpProcess`, `KillProcess` targeting `xdbhostmain` |
| **MonLogin** | Login volume and distribution by instance — identifies workload driving stress |
| **MonDmRealTimeResourceStats** | Instance resource utilization — worker/session/CPU exhaustion |
| **AlrWinFabHealthNodeEvent** | TCP port statistics — port availability, connection states |

## Differences from XdbHost Restart (xdbhost-restart skill)

| Aspect | XdbHost Restart | XdbHost High TCP Rejections |
|--------|----------------|----------------------------|
| **Alert type** | CRGW0001 LoginFailureCause: HasXdbHostRestarts | Health Hierarchy: XDBHost high TCP rejections |
| **Process IDs** | 1-2 (single restart) | Many (> 3, often > 20 in crash loop) |
| **Duration** | < 5 minutes typically | 30 minutes to 2+ hours |
| **Root cause** | Automation/bot kill, single crash | LSASS stress, sustained node pressure |
| **Dump pattern** | Usually 0-1 dumps | Many alternating dumps |
| **Primary queries** | MonLogin (error distribution) | MonCounterOneMinute (TCP rejections, LSASS CPU) |
| **Mitigation** | Self-mitigates | Often requires manual XDBHost restart or failover |
