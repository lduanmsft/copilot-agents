!!!AI Generated.  To be verified!!!

# Terms and Concepts

## Core Concepts

### XdbHost Process
XdbHost is the SQL Server host process running on DB nodes in Azure SQL Database. It handles incoming connections (via socket duplication from the gateway proxy), query execution, and database operations. When XdbHost restarts, all in-flight connections and new login attempts to that node fail until the process fully reinitializes and registers its instances.

### HasXdbHostRestarts (LoginFailureCause)
`HasXdbHostRestarts` is a login failure cause tag assigned by the CRGW0001 alert monitor when it detects that XdbHost process restarts occurred on the DB node during the alert window. This indicates that the login failures are a direct consequence of the XdbHost process cycling, not a networking or authentication issue.

### Socket Duplication (SocketDup)
Azure SQL Database gateway uses socket duplication to hand off client connections from the gateway proxy to the XdbHost process on the DB node. During an XdbHost restart, this handoff mechanism fails, producing a characteristic cascade of 40613 errors with different state codes depending on which phase of the handoff failed.

### XdbHost Restart Error Cascade
When XdbHost restarts, login failures follow a predictable sequence of 40613 substates:

| State | State Description | Phase | Meaning |
|-------|-------------------|-------|---------|
| 12 | FailedToPrepareDuplicatedData | Socket dup preparation | Cannot prepare socket duplication data for the target instance |
| 44 | LoginRequestSqlFailedToDuplicateLoginFromXdbHost | Socket dup handoff | Socket duplication request to XdbHost failed |
| 10 | CantFindRequestedInstance | Instance lookup | Instance not found — bulk of errors during restart window |
| 13 | FailedToSendDuplicateData | Data transfer | SNIOpen failures during socket duplication |
| 126 | LoginSessDb_DbNotFound | Post-restart recovery | Database not yet registered after XdbHost restarts |
| 22 | DueToProxyConnextThrottle | Gateway throttling | Gateway proxy-login timeout from backlogged requests |

### Process ID Change (Restart Confirmation)
The definitive way to confirm an XdbHost restart is via `MonXdbhost`, where the `process_id` changes on a node. Two different process_id values with a temporal gap confirm a restart occurred. The gap duration approximates the restart time.

## Common XdbHost Restart Triggers

### Automation / Bot Actions
- **ResolveUnavailability bot**: Kills the Primary replica when login failure rate exceeds thresholds. Often triggered by customer-side authentication error floods (e.g., 18456/132 FedAuthAADLoginJWTUserError).
- **Proxy throttle mitigator runner**: Restarts XdbHost to clear proxy-login throttle conditions when pending connections exceed thresholds.

### XdbHost Dumps / Crashes
XdbHost process crashes and produces dump files. This causes immediate proxy login failures as the socket duplication target process is gone.

### CAS KillProcess
Manual or automated CAS (Cluster Administration Service) action that terminates the XdbHost process. Used during incident mitigation or maintenance.

## Key Telemetry Tables

| Table | Purpose in This Skill |
|-------|----------------------|
| **MonLogin** | Login success/failure analysis — error codes, state descriptions, user vs. system errors, volume per time bin |
| **MonXdbhost** | XdbHost process logs — SNIOpen failures, InitSendData errors, throttling parameters, SocketDupInstance errors |
| **MonCounterOneMinute** | TCP rejection counters — high rejected connections indicate node-level resource pressure |

## Related Documentation

All source materials used to build and maintain this skill. These URLs are fetched during skill creation and updates to extract knowledge, principles, and queries.

### ICM Incidents Analyzed
- ICM 771384169 — ProdSCus1a, Mar 27, 2026 (Runner restart + CAS KillProcess)
