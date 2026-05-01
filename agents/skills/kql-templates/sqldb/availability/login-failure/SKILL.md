---
name: login-failure-triage
description: Availability-side triage for non-user-error login failures triggered by LoginFailureCause (CRGW0001) or Login Failures Runner alerts. Performs quick pattern assessment, then invokes the Connectivity login-failure skill for full investigation while running supplemental Availability-only checks (failover correlation, replica health, error logs, unplaced replicas, management operations). Use when investigating login failure spikes, "login success rate below 99%", CRGW0001 alerts, or Login Failures Runner incidents.
---

# Login Failures Diagnostics (Availability Triage)

## Overview

This skill is the **Availability-side entry point** for non-user-error login failure incidents. It performs quick pattern assessment, runs Availability-specific checks, and invokes the comprehensive [Connectivity login-failure skill][connectivity-login-failure] for the full investigation workflow.

### Monitors That Trigger This Skill

1. **Login Failures Runner**: Fires when a frontend keeps having non-user-error failed logins above a percentage threshold.
2. **LoginFailureCause** (CRGW0001): Fires when login success rate drops below 99% for a database, categorized by cause (e.g., `LoginErrorsFound_40613_4_master`, `IsUnplacedReplica`, `LoginErrorsFound_40613_127`).

**Key distinction**: This skill focuses on **platform-side** login failures (`is_user_error == 0`), not customer-caused errors (wrong password, firewall blocks, etc.).

### Relationship to Connectivity Login-Failure Skill

The [Connectivity login-failure skill][connectivity-login-failure] provides a comprehensive 11-step investigation covering login target identification, connectivity ring analysis, prevailing error diagnosis, error-specific sub-skills, ring health, node health, and XDBHOST health. **This Availability skill does NOT duplicate that workflow.** Instead, it:

1. Provides alert-specific context (CRGW0001/Login Failures Runner)
2. Runs a quick pattern check to assess severity
3. Invokes the Connectivity skill for the full investigation
4. Runs supplemental Availability-only checks not covered by Connectivity

## Required Information

### From User or ICM:
- **LogicalServerName** (e.g., `my-server`)
- **LogicalDatabaseName** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From [execute-kusto-query] skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)

### From [get-db-info] skill:
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **fabric_partition_id** (PartitionId)
- **DatabaseId** (sql_database_id) — needed for elastic pool databases where AppName is shared
- **FailoverGroupId** (failover_group_id) — if applicable

## Workflow

### 1. Quick Pattern Assessment

Execute query **LF-100** from [references/queries.md](references/queries.md) to:
- Confirm non-user-error login failures are occurring
- Identify error codes, states, and affected packages (`sqlserver` vs `xdbhost`)
- Determine failure volume per minute and affected nodes

**Quick assessment:**

| Pattern | Assessment | Action |
|---------|------------|--------|
| Brief spike (< 30 sec), single error/state | ✅ Likely transient failover | Cross-check with failover events (Step 3) |
| Sustained failures (> 2 min), single node | ⚠️ Node-level issue | Invoke Connectivity skill (Step 2) + check replica health (Step 4) |
| Sustained failures, multiple nodes | 🚩 Cluster or partition issue | Check quorum, unplaced replicas (Step 5) |
| ReadOnlyIntent failures only | ⚠️ Secondary replica issue | Check replica health (Step 4) |
| Post-failover warmup (state 127) > 5 min | 🚩 Stuck warmup | Invoke [`error-40613-state-127`][error-40613-state-127] skill |
| Unplaced replica events > 10 min | 🚩 Persistent placement failure | Invoke [`unplaced-replicas`][unplaced-replicas] skill |

### 2. Invoke Connectivity Login-Failure Skill

Invoke the full [Connectivity login-failure skill][connectivity-login-failure] for comprehensive investigation:

```
Skill: .github/skills/Connectivity/connectivity-scenarios/login-failure/SKILL.md
```

This covers:
- Login target identification (MonLogin)
- Failover/availability check (calls back to Availability/failover)
- Connectivity ring determination
- Connection type analysis
- Prevailing error diagnosis and error-specific sub-skills
- Connectivity ring health (SNAT, gateway restarts, deployments)
- Node health queries (NH100–NH700)
- XDBHOST health

**⚠️ Do NOT duplicate**: The following areas are fully handled by the Connectivity skill and should NOT be re-run:
- MonLogin error screening → handled by `determine-prevailing-error`
- LoginOutages queries → handled by `determine-login-outage`
- Error-specific analysis (40613 states, 18456) → handled by `connectivity-errors/` sub-skills
- Node deactivation events → handled by node-health queries

### 3. Correlate with Failover Events (Availability-Only)

Execute query **LF-300** to:
- Check if login failures align with failover timing
- Identify `ReconfigurationType` (planned vs unplanned)
- Determine if login failures persist after failover completes

**Correlation logic:**
- Login failures DURING failover window → expected, check failover duration
- Login failures AFTER failover ends → check recovery (state 127), warmup delays
- Login failures with NO corresponding failover → check replica health, unplaced replicas

### 4. Check Replica Health (Availability-Only)

Execute query **LF-400** to:
- Analyze replica states and transitions during the incident
- Identify replicas in unhealthy states (e.g., NOT_SYNCHRONIZED, RESTORING)
- Detect replicas that went offline or had state changes

**Warning signs:**
- 🚩 Primary replica changed `database_state_desc` to non-ONLINE
- 🚩 All replicas in non-SYNCHRONIZED state simultaneously
- 🚩 `is_suspended = 1` on replicas

### 5. Check for Unplaced Replicas (Availability-Only)

Execute query **LF-600** to:
- Detect unplaced replica events from Service Fabric
- Determine if replica placement failures caused login failures

### 6. Check Error Logs (Availability-Only)

Execute query **LF-500** to:
- Extract SQL error log messages during incident window
- Identify specific error codes (e.g., 823, 824, 825 for I/O errors)
- Detect process failures, assertion errors, or resource issues

### 7. Check for Management Operations (Availability-Only)

Execute query **LF-700** to:
- Identify customer or platform operations that may have triggered the issue
- Check for SLO changes, geo-replication operations, failover group changes

## Decision Tree

```
Non-user-error login failures detected (LF-100)
│
├─ Invoke Connectivity login-failure skill (Step 2)
│   └─ Connectivity determines: prevailing error, ring health,
│      node health, XDBHOST health, LoginOutages
│
├─ Failover events found? (LF-300)
│   ├─ YES, failures align with failover window
│   │   └─ Duration < 30s → Normal transient, canned RCA
│   │   └─ Duration > 2min → Invoke failover skill
│   └─ NO failover found
│       └─ Check replica health (LF-400)
│
├─ Replica health issues? (LF-400)
│   ├─ Primary offline → Escalate, check node-health skill
│   ├─ Synchronization issues → Invoke sync-replica-recovery
│   └─ Replicas healthy → Check error logs (LF-500)
│
├─ Unplaced replicas? (LF-600)
│   └─ Events found → Invoke unplaced-replicas skill
│
└─ Management operations? (LF-700)
    └─ SLO change in progress → Invoke update-slo skill
```

## Root Cause Categories

| Category | Description | Typical Duration | Action |
|----------|-------------|------------------|--------|
| **Failover-related** | Login failures during planned/unplanned failover | < 30 sec | Canned RCA if transient |
| **Unplaced replica** | No node available for replica placement | Variable | Invoke [`unplaced-replicas`][unplaced-replicas] skill |
| **Quorum loss** | Majority of replicas unavailable | Variable | Invoke [`quorum-loss`][quorum-loss] skill |
| **SQL process issue** | SQL Server crash, assertion, resource exhaustion | Variable | Check dumps, error logs |
| **Gateway issue** | GwProxy or frontend routing problem | Variable | Diagnosed by [Connectivity login-failure skill][connectivity-login-failure] |
| **Xdbhost issue** | Xdbhost process unhealthy | Variable | Diagnosed by [Connectivity login-failure skill][connectivity-login-failure] |
| **Long logins** | Login processing delays at backend | Variable | Check resource contention |
| **Platform update** | Node maintenance causing replica movements | Minutes | Diagnosed by [Connectivity login-failure skill][connectivity-login-failure] (node-health) |
| **SLO change** | Tier change operation in progress | Minutes | Invoke [`update-slo`][update-slo] skill |
| **Customer action** | Administrative operation triggered outage | Variable | Document operation details |

## Execute Queries

Execute queries from [references/queries.md](references/queries.md):

**Step 1: Quick Pattern Assessment**
- LF-100 (Login Failure Volume and Timeline)

**Step 2: Full Investigation (Connectivity Skill)**
- Invoke [Connectivity login-failure skill][connectivity-login-failure]

**Step 3: Failover Correlation (Availability-Only)**
- LF-300 (SqlFailovers)

**Step 4: Replica Health (Availability-Only)**
- LF-400 (Replica States)

**Step 5: Unplaced Replicas (Availability-Only)**
- LF-600 (Unplaced Replica Events)

**Step 6: Error Logs (Availability-Only)**
- LF-500 (SQL Error Log Messages)

**Step 7: Management Operations (Availability-Only)**
- LF-700 (Management Operations)

## Escalation

### Canned RCA Criteria (No Deep Investigation Needed)

A login failure incident qualifies for a canned RCA when ALL of the following are true:
1. Login failures span < 30 seconds
2. A single failover event aligns with the failure window
3. Failover completed successfully (has `FailoverEndTime`)
4. No login failures after `FailoverEndTime` + 30 seconds
5. Replica health is normal before and after (LF-400)
6. No unplaced replica events (LF-600)

### Escalation Paths

- **Transient failover-related (< 30 sec)**: No escalation - canned RCA
- **Prolonged failover**: Invoke [`failover`][failover] skill
- **Unplaced replicas**: Invoke [`unplaced-replicas`][unplaced-replicas] skill
- **Quorum loss**: Invoke [`quorum-loss`][quorum-loss] skill
- **SQL process crash/dump**: Invoke [`dump`][dump] skill
- **Repeated login failures**: Invoke [`freq-failover`][freq-failover] skill
- **State 126/127 errors**: Invoke [`error-40613-state-126`][error-40613-state-126] or [`error-40613-state-127`][error-40613-state-127] skill
- **SLO change stuck**: Invoke [`update-slo`][update-slo] skill
- **Gateway/Connectivity issues**: Diagnosed by [Connectivity login-failure skill][connectivity-login-failure]

## Related Skills

### Connectivity Skills (invoked, not duplicated)
- [`Connectivity login-failure`][connectivity-login-failure] - Full login failure investigation (11-step workflow)
- [`determine-prevailing-error`][determine-prevailing-error] - MonLogin error screening (invoked by Connectivity skill)
- [`determine-login-outage`][determine-login-outage] - LoginOutages queries (invoked by Connectivity skill)
- [`connectivity-ring-health`][connectivity-ring-health] - Gateway/SNAT health (invoked by Connectivity skill)

### Availability Skills (supplemental checks)
- [`failover`][failover] - When login failures correlate with failover events
- [`quorum-loss`][quorum-loss] - When login failures caused by quorum loss
- [`node-health`][node-health] - When login failures caused by node-level issues
- [`unplaced-replicas`][unplaced-replicas] - When LoginFailureCause is IsUnplacedReplica
- [`error-40613-state-126`][error-40613-state-126] - When login errors show state 126 (transition)
- [`error-40613-state-127`][error-40613-state-127] - When login errors show state 127 (warmup)
- [`freq-failover`][freq-failover] - When login failures recur from repeated failovers
- [`update-slo`][update-slo] - When login failures correlate with SLO change operations
- [`dump`][dump] - When SQL process crash caused the failures

## Related Categories

- Category 2: High Availability & Failover Issues

## Reference

- [knowledge.md](references/knowledge.md) — Definitions, LoginFailureCause taxonomy, error codes, and related documentation
- [queries.md](references/queries.md) — Kusto queries LF-100, LF-300, LF-400, LF-500, LF-600, LF-700

<!-- Skill link definitions (used throughout this document) -->
[execute-kusto-query]: ../../Common/execute-kusto-query/SKILL.md
[get-db-info]: ../../Common/get-db-info/SKILL.md
[failover]: ../failover/SKILL.md
[quorum-loss]: ../quorum-loss/SKILL.md
[node-health]: ../../NodeHealth/node-health/SKILL.md
[unplaced-replicas]: ../unplaced-replicas/SKILL.md
[error-40613-state-126]: ../error-40613-state-126/SKILL.md
[error-40613-state-127]: ../error-40613-state-127/SKILL.md
[freq-failover]: ../freq-failover/SKILL.md
[update-slo]: ../update-slo/SKILL.md
[dump]: ../dump/SKILL.md
[connectivity-login-failure]: ../../Connectivity/connectivity-scenarios/login-failure/SKILL.md
[determine-prevailing-error]: ../../Connectivity/connectivity-base/determine-prevailing-error/SKILL.md
[determine-login-outage]: ../../Connectivity/connectivity-base/determine-login-outage/SKILL.md
[connectivity-ring-health]: ../../Connectivity/connectivity-base/connectivity-ring-health/SKILL.md
