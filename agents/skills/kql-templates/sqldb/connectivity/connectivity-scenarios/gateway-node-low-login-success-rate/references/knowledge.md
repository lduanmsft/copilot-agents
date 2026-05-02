# Gateway Node Low Login Success Rate — Knowledge Base

## Alert Background

This alert fires when the login success rate on a Gateway node drops below threshold. The Geneva monitor is:

| Level | Monitor Name | Threshold |
|-------|-------------|-----------|
| Node | `SQLConnectivity-GatewayNodeLowLoginSuccessRate` | Per-node success rate |

**Success rate formula:**
```
LoginSuccessRate = (TotalLogins - SystemErrors) / TotalLogins
```
Only system failures (`is_success == false AND is_user_error == false`) count as failures. User errors (bad password, DB not found, etc.) are NOT treated as system failures.

## Known Issues

### 1. Trident Testing in Canary Rings

**Observed since:** 2023-03-24

**Symptoms:** Daily alerts around 18:00 PST on canary control rings (`useuapeast2-a`, `useuapcentral1-a`). Failures are 40613/4 concentrated in `TridentSqlResourceGroup`.

**Detection:** GNLSR200 — check if `resource_group` = `TridentSqlResourceGroup`.

**Action:** Transfer to Synapse DW / Client Experiences team.

### 2. SQL Alias Failover + Cache Backoff

**Observed since:** 2021-08-06

**Symptoms:** 40613/4 errors with `lookup_error_code = 2147500037` (E_FAIL) skewed to one node. SQL Alias failover combines with the cache backoff timer, causing one GW node to fail logins because it cannot reach the SQL Alias.

**Detection:** GNLSR210 (error check) + GNLSR220 (cache backoff timer activity).

**Action:** Kill/restart GW process on the affected node, or wait for cache backoff timer to expire.

**Sample incidents:** 254642172, 253666042

### 3. SF Version Behavior Change

**Observed since:** 2021-02-04

**Symptoms:** 40613/4 errors during SF reconfigurations with `SERVICE_FABRIC-DOES-NOT_EXISTS` in lookup_state. Caused by a behavior change in newer SF versions where an extra notification is sent during reconfiguration.

**Detection:** GNLSR230 — check for `SERVICE_FABRIC-DOES-NOT_EXISTS` in lookup_state.

**Action:** Self-mitigates after deployments finish. Fixed in GW.18+ which treats this error as retriable/waitable.

### 4. AliasDB Lookup Failures (DATABASE_ALIAS / LOGICAL_MASTER_ALIAS)

**Observed since:** 2026-04-17 (documented from ICM 781624132)

**Symptoms:** 40613/4 errors with `state_desc = WinFabOrSqlAliasLookupFailure` and `lookup_state` in (`DATABASE_ALIAS`, `LOGICAL_MASTER_ALIAS`). The GW node cannot resolve database aliases through AliasDB. Typically node-isolated but may coincide with concurrent AliasDB-related incidents on the same cluster.

**Detection:** GNLSR300 — check for 40613/4 with `state_desc = WinFabOrSqlAliasLookupFailure` and `lookup_state = DATABASE_ALIAS` or `LOGICAL_MASTER_ALIAS`. Confirm with GNLSR640 (AliasDB SF app health).

**Key differentiation from Known Issue #2:**
- Issue #2 has `lookup_error_code = 2147500037` (E_FAIL) — alias failover + cache backoff.
- Issue #4 has `lookup_state = DATABASE_ALIAS` / `LOGICAL_MASTER_ALIAS` — broader AliasDB connectivity failure (secret rotation, replica health, network).

**Action:**
1. Check AliasDB replicas health from SFE (query GNLSR640).
2. Check for credential/secret rotation timing that correlates with failure window.
3. Check for concurrent AliasDB-related incidents on the same cluster.
4. If node-isolated: restart GW process on the affected node.
5. If cluster-wide: escalate to AliasDB on-call.

**Sample incidents:** 781624132

## Key Error Codes

| Error | State | State Description | lookup_state | Typical Cause |
|-------|-------|-------------------|--------------|---------------|
| 40613 | 4 | WinFabOrSqlAliasLookupFailure | DATABASE_ALIAS | AliasDB cannot resolve database alias (connectivity, secret rotation, replica issue) |
| 40613 | 4 | WinFabOrSqlAliasLookupFailure | LOGICAL_MASTER_ALIAS | AliasDB cannot resolve logical master alias |
| 40613 | 4 | WinFabOrSqlAliasLookupFailure | SERVICE_ENDPOINT | AliasDB service endpoint resolution failure |
| 40613 | 4 | — | — | GW cannot locate backend SQL instance (WinFab lookup failure, AliasDB issue) |
| 40613 | 22 | DueToProxyConnextThrottle | — | SNAT port exhaustion, networking instability, DB node too busy |
| 40613 | 31 | FailedToComputePrivateEndpointRedirectionEndpoint | LOOKUP_ENTRY | Private endpoint redirection computation failure |
| 42127 | 22 | DueToProxyConnextThrottle | — | Gateway-level throttling (user error variant) |
| 40532 | 4 | WinFabLookupFailure | — | Service Fabric partition resolution failure |
| 26078 | 33 | ProxyLoginDisconnected | SERVICE_ENDPOINT | Proxy login disconnected during service endpoint resolution |
| 17830 | 11 | — | — | Internal error |

## Error 40613 State 22 — Root Cause Differentiation

Error 40613 State 22 (DueToProxyConnextThrottle) is NOT always SNAT. Possible root causes:

1. **SNAT port exhaustion** — CR node ran out of outbound ports to a specific destination (IP:port)
2. **Networking instability** — Load balancer, physical networking, NIC issues
3. **DB node unhealthy/unavailable** — Target node too busy to process TCP traffic
4. **Login flood** — Too many logins in a short time overwhelming XDBHost or SQL Server
5. **Other networking causes**

Refer to `.github/skills/Connectivity/connectivity-errors/error-40613-state-22/SKILL.md` for full investigation.

## Escalation Criteria

| Condition | Escalation |
|-----------|-----------|
| Multiple nodes affected AND > 100 servers | 🚩 DRI: Escalate — issue extends beyond this node |
| PG/MySQL AppTypeName is top contributor | Transfer to RDBMS Open Source queue |
| Trident resource group is top contributor | Transfer to Synapse DW / Client Experiences |
| Regional outage in same region (AzNot) | Join their bridge, add SQL as affected service |
| No telemetry results | Engage: Availability expert, Gateway expert, Telemetry on-call |

## Dashboard Links

| Dashboard | URL |
|-----------|-----|
| Global Health | `https://portal.microsoftgeneva.com/s/B0A2575D` |
| Drill Calendar | `https://global.azure.com/drillmanager/calendarView` |

## Mitigation Actions

| Action | When to Use |
|--------|------------|
| Kill/restart GW process on node | Node-isolated issue, AliasDB cache backoff, ODBC failures |
| Wait for deployment to finish | SF behavior change, deployment in progress |
| Transfer to another team | Trident testing, PG/MySQL issues |
| Declare Outage | Multiple nodes affected with > 100 servers, regional impact |
| Investigate SNAT source | 40613/22 with confirmed SNAT events |
| Check AliasDB replicas + secret rotation | 40613/4 with `DATABASE_ALIAS` / `LOGICAL_MASTER_ALIAS` lookup_state |
| Escalate to AliasDB on-call | Cluster-wide AliasDB failures, AliasDB SF app unhealthy |

## Key Telemetry Tables

| Table | Purpose in This Skill |
|-------|----------------------|
| `MonLogin` | Primary table — login outcomes, error codes, states, node/server/database mapping. Used by GNLSR100-320, GNLSR700, GNLSR900. |
| `MonRedirector` | AliasDB cache health, fabric resolution, ODBC failures, lookup retries. Used by GNLSR220, GNLSR600-640, GNLSR710-720. |
| `MonSFEvents` | Service Fabric application health events (AliasDB health state). Used by GNLSR640. |
| `MonGatewayResourceStats` | GW node resource usage (memory, threads, cache). Used by GNLSR730. |
| `MonRolloutProgress` | Deployment/upgrade tracking. Used by GNLSR800. |
| `MonFabricClusters` | Cluster infrastructure — IP addresses for SNAT cross-reference. Used by GNLSR400. |
| `WinFabLogs` | Windows Fabric logs — repair tasks and node maintenance. Used by GNLSR810. |
| `SlbHealthEvent` (azslb cluster) | SNAT port exhaustion and high port usage events. Used by GNLSR400. |

## Related Monitor

> **Note:** Control Ring-level login success rate incidents are triggered by a separate monitor (`SQLConnectivity-ControlRingLowLoginSuccessRate` / CRGW00003) and are covered by a dedicated skill. If during investigation you find multiple nodes are affected, escalate accordingly.
