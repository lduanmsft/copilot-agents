# Control Ring Nodes Unhealthy — Triage Principles

## Triage Principles

### Principle 1: Scope Before Depth

Always determine the scope of the problem before diving into any single node. The cluster-level alert means multiple nodes are affected. Understanding how many and which nodes are unhealthy guides the entire investigation.

**Determine first:** "How many nodes are unhealthy and what percentage of the cluster is affected?"

### Principle 2: Pattern Recognition First

Before investigating individual nodes, check for cluster-wide patterns that explain the alert:
1. **Deployment/upgrade in progress** — most common benign cause
2. **Azure Disaster Recovery Drill** — planned infrastructure drill
3. **Auto-mitigation activity** — check if healthmanagesvc has acted, but this does not replace investigation

Even if a cluster-wide pattern explains the alert, the DRI **must still** verify recovery and investigate the root cause — patterns like drills and deployments can mask genuine issues.

### Principle 3: Most Common Signal First

When node-level investigation is needed, check health signals in order of frequency:
1. **Login Success Rate** — most common signal causing nodes to be unhealthy
2. **GW Process Restarts** — second most common, often correlated with deployments
3. **LSASS CPU Stress** — less frequent but causes cascading failures
4. **TCP Rejections** — typically a symptom of LSASS stress on GW nodes

### Principle 4: Delegate to Specialized Skills

This is an **orchestrator skill**. Once you identify which signal is breaching on specific nodes, delegate to the specialized node-level skill:
- Login issues → `gateway-node-low-login-success-rate`
- TCP rejections → `xdbhost-high-tcp-rejections`
- Process/rollout issues → `gateway-health-and-rollout`

Do not duplicate the investigation that the node-level skill performs.

### Principle 5: Check Auto-Mitigation Early

Check whether `healthmanagesvc` has taken any action early in the investigation — this provides useful context about the cluster state. However, auto-mitigation is not guaranteed and does not replace root cause analysis. The DRI **must always** complete the full investigation regardless of auto-mitigation status.

### Principle 6: Cluster vs Node Correlation

When correlated node-level ICMs exist, use them to accelerate triage:
- If node-level ICMs are already being worked → aggregate their findings at cluster level
- If no node-level ICMs exist → the rollup may have fired before individual node alerts

## Diagnosis Principles

### Principle 1: The 20% Threshold is Meaningful

The alert fires at ≥20% unhealthy nodes. The actual percentage provides context:
- **20-30%**: Subset of nodes affected, likely localized (upgrade domain, rack)
- **30-50%**: Significant portion, may indicate broader issue
- **50-100%**: Cluster-wide event (deployment, platform issue, region-wide)

### Principle 2: Signal Correlation is Key

Multiple signals breaching on the same node (e.g., LSASS CPU + TCP rejections + login failures) typically have a single root cause. The cascade is usually:
```
Root Cause → LSASS CPU ↑ → Authentication stalls → Login failures + TCP rejections
```

When you see multiple signals, look upstream for the root cause rather than treating each signal independently.

### Principle 3: Time Alignment

Verify that the health degradation aligns temporally with the alert:
- Alert fire time should correspond to when nodes started failing
- If telemetry shows nodes were already recovering at alert fire time → lag in health monitor
- If telemetry shows nodes were healthy at alert fire time → false alarm / monitor misfire

### Principle 4: Deployment Awareness

Always check for deployments before deep investigation. Deployment-related unhealthy states have characteristic patterns:
- Follow upgrade domain patterns (sequential, predictable)
- Often self-mitigate once the deployment passes through

A detected deployment is **context, not a stop condition**. The agent must still complete signal investigation, impact assessment, and recovery verification — a deployment may itself be the trigger of the unhealthy state, may stall, or may unmask a different problem on the affected nodes. Record the deployment context in ICM and continue the workflow.

### Principle 5: Impact Assessment

Always quantify customer impact separately from infrastructure impact:
- **Infrastructure impact**: X of Y nodes unhealthy
- **Customer impact**: Z distinct servers / W subscriptions experiencing errors
- High infrastructure impact with low customer impact may indicate the issue is on nodes with minimal traffic

## Expected Investigation Timing

| Step | Expected Duration | Notes |
|------|------------------|-------|
| Step 0 (Links) | < 1 min | Generate Geneva Health and dashboard links |
| Step 1 (Parse) | < 1 min | Extract cluster and region from alert |
| Step 2 (Scope) | 2-3 min | Run CRNU100 + CRNU110 to scope unhealthy nodes |
| Step 3 (Patterns) | 2-3 min | Check deployment, drill calendar, automation |
| Step 4 (Signals) | 3-5 min | Identify breaching signals per node |
| Step 5 (Auto-mitigation) | 1-2 min | Check healthmanagesvc status |
| Step 6 (Delegate) | Variable | Depends on which sub-skill is invoked |
| Step 7 (Impact) | 1-2 min | Run CRNU500 |
| Step 8 (Decision) | 1-2 min | Apply decision tree |
| Step 9 (Verify) | 2-3 min | Re-run scope queries |
| **Total (no delegation)** | **~15-20 min** | Faster for common patterns (drill, deployment) |

## Root Cause Classification

| Root Cause | Distinguishing Evidence | Typical Mitigation |
|-----------|------------------------|-------------------|
| **Azure Disaster Recovery Drill** | Drill calendar match for region, multiple nodes simultaneously | Verify drill is the cause; monitor recovery for unexpected issues |
| **Deployment / Upgrade** | MonRolloutProgress shows active upgrade, nodes affected follow UD pattern | Monitor deployment; identify if problematic |
| **Login Success Rate Drop** | CRNU100 shows nodes < 95%, signals confirmed via GNLSR queries | Delegate to `gateway-node-low-login-success-rate` |
| **LSASS CPU Stress** | CRNU300 shows LSASS > 50% on affected nodes | Delegate to Performance/LSASS |
| **TCP Rejections** | CRNU310 shows rejections > 150/sec with handle > 600K | Delegate to `xdbhost-high-tcp-rejections` |
| **GW Process Crash Loop** | CRNU210 shows > 3 process IDs per node | Delegate to `gateway-health-and-rollout` |
| **AliasDB Failure** | Login errors are 40613/4 (AliasDB resolution), cluster-wide | Escalate to Connectivity Engineering |
| **Unknown** | No clear pattern from above checks | Escalate to Connectivity Engineering |

## Escalation Criteria

Escalate to **Connectivity Engineering** when:
- The root cause does not match any known pattern above
- Multiple distinct health signals are breaching with no common root cause
- Auto-mitigation has not started after 30+ minutes
- Customer impact is high (CRNU500 shows > 100 servers or > 10 subscriptions affected)
- The same cluster has repeated alerts within 24 hours (not deployment-related)
