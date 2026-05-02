# Debug Principles for Gateway Node Low Login Success Rate

## Triage Principles

1. **This is a node-level alert — check if other nodes are also affected**: The Geneva monitor fires per-node (`SQLConnectivity-GatewayNodeLowLoginSuccessRate`). Always run GNLSR100 first to check if the issue is isolated to the alerted node or extends to other nodes — node-isolated issues are lower risk, while multiple nodes affected may indicate a broader infrastructure problem requiring escalation.

2. **Login success rate counts only system errors**: The formula `(TotalLogins - SystemErrors) / TotalLogins` excludes user errors (`is_user_error == true`). A low success rate means infrastructure or backend failures, not customer misconfigurations.

3. **GW nodes are stateless proxies — root causes are usually upstream or downstream**: The Gateway node proxies logins to backend Tenant Rings. If the GW node itself is healthy but success rate is low, the issue is usually: AliasDB resolution failures (upstream), backend TR unavailability (downstream), or networking issues (SNAT, fabric resolution).

4. **Known issues cover the majority of cases**: Check Trident testing (canary rings), SQL Alias failover + cache backoff, SF version behavior changes, and AliasDB lookup failures before deep-diving. These known patterns have clear signatures and documented mitigations.

5. **Error 40613 State 4 is the dominant system error**: Most GW low success rate incidents involve 40613/4 (WinFabOrSqlAliasLookupFailure). The `lookup_state` field differentiates the root cause — always examine it to classify the specific failure type.

6. **AliasDB failures have distinct signatures**: When `lookup_state` is `DATABASE_ALIAS` or `LOGICAL_MASTER_ALIAS`, the GW node cannot resolve database aliases. This is different from fabric resolution failures (`SERVICE_ENDPOINT`) and SF behavior changes (`SERVICE_FABRIC-DOES-NOT_EXISTS`). Each requires a different investigation path.

## Diagnosis Principles

### Principle 1: Scope Before Deep Dive
- Run GNLSR100 before any other query to determine if the issue is isolated to the alerted node
- If multiple nodes are affected: points to shared infrastructure (AliasDB, backend TR ring, networking) — escalate
- If node-isolated: focus on node-local causes (process state, cache, ODBC connectivity)

### Principle 2: Error Distribution Drives Investigation Path
- Identify the top error/state combination from GNLSR300
- 40613/4 with known `lookup_state` → follow Known Issues path (Step 3)
- 40613/22 → SNAT/networking path (Step 6)
- Mixed errors across many error codes → infrastructure-level issue
- PG/MySQL `AppTypeName` dominant → transfer to RDBMS Open Source queue

### Principle 3: Correlate with Backend Health
- If errors target specific TR rings (GNLSR310) → backend issue on those rings
- If errors have empty `instance_name` / `TargetTRRing` → GW never reached backend (AliasDB/resolution failure)
- If errors spread across all TR rings → GW node-level or networking issue

### Principle 4: Check Fabric and AliasDB Before Blaming GW
- Fabric resolution failures (GNLSR620) indicate Service Fabric issues, not GW bugs
- AliasDB ODBC failures (GNLSR600) indicate the GW node cannot reach AliasDB
- AliasDB SF app health (GNLSR640) may show the AliasDB service itself is degraded
- 🚩 Only after ruling out fabric/AliasDB causes should you investigate GW process health

### Principle 5: Check Automation and Deployments
- Deployments (GNLSR800) and repair tasks (GNLSR810) often correlate with transient success rate drops
- If a deployment is in progress, the issue may self-mitigate when deployment completes
- Check the Drill Calendar for planned activities in the region

### Principle 6: Node-Isolated Issues Often Self-Mitigate with GW Restart
- If the issue is node-isolated and no clear infrastructure cause is found, restarting the GW process is a safe first-line mitigation
- The GW process is stateless — a restart clears caches, reconnects to AliasDB, and re-resolves fabric endpoints
- 🚩 If multiple nodes are affected, GW restart is NOT sufficient — the root cause is external to GW

## Expected Timings

| Event | Normal | Warning | Critical |
|-------|--------|---------|----------|
| Login success rate per node | > 99% | 95-99% | < 95% |
| System errors per 5-min window | < 50 | 50-500 | > 500 |
| Distinct servers with errors | < 10 | 10-100 | > 100 |
| AliasDB ODBC failures per 5-min | 0 | 1-10 | > 10 |
| Fabric resolution failures per 5-min | 0 | 1-50 | > 50 |
| GW process restarts | 0 | 1 | > 1 |
| Time from alert to escalation (multiple nodes) | — | — | < 5 minutes |

## Root Cause Classification

| Evidence Pattern | Root Cause | RCA Label |
|-----------------|------------|-----------|
| Multiple nodes + all nodes failing + fabric resolution errors | Backend TR ring(s) unreachable | FabricResolutionFailure |
| Multiple nodes + all nodes + FABRIC_E_SERVICE_OFFLINE | TR ring Service Fabric offline | ServiceFabricOffline |
| Multiple nodes + correlates with drill calendar | Planned canary drill / zone down exercise | CanaryDrill |
| Node-isolated + 40613/4 + `TridentSqlResourceGroup` | Trident testing in canary ring | TridentTesting |
| Node-isolated + 40613/4 + `lookup_error_code = 2147500037` | SQL Alias failover + cache backoff | AliasCacheBackoff |
| Node-isolated + 40613/4 + `SERVICE_FABRIC-DOES-NOT_EXISTS` | SF version behavior change during deployment | SFBehaviorChange |
| Node-isolated + 40613/4 + `DATABASE_ALIAS` / `LOGICAL_MASTER_ALIAS` | AliasDB lookup failures | AliasDBLookupFailure |
| Node-isolated + 40613/22 + SNAT events | SNAT port exhaustion | SNATExhaustion |
| Node-isolated + ODBC failures on one node | AliasDB ODBC connectivity issue on node | AliasDBODBCFailure |
| Node-isolated + multiple GW process restarts | GW process instability / crash loop | GWProcessInstability |
| Node-isolated + deployment in progress | Deployment-related transient failure | DeploymentRelated |
| No clear pattern | Unknown — escalate | EscalateToEngineering |

## Escalation Criteria

- 🚩 Multiple nodes affected with > 100 servers — escalate within 5 minutes
- 🚩 Multiple nodes affected with no clear root cause after completing all steps
- 🚩 AliasDB SF application health is degraded cluster-wide
- 🚩 Crash loop on GW process that does not self-resolve after restart
- 🚩 Same node experiences repeat incidents within 7 days
- 🚩 SNAT exhaustion with no identifiable traffic source
- 🚩 Regional outage correlation (Azure Compute, Storage, or Networking)
