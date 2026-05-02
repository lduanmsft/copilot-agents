---
name: xdbhost-restart
description: Diagnose Azure SQL Database login failures caused by XdbHost process restarts. Use when ICM title or alert contains "HasXdbHostRestarts" LoginFailureCause, or when multiple 40613 substates (10, 12, 13, 44, 126) appear in a concentrated time window. Determines what triggered the restart, the impact scope, and whether the issue self-mitigated. Accepts either ICM ID or direct parameters (logical server name, database name, time window). Executes Kusto queries via Azure MCP to analyze telemetry.
---

# XdbHost Restart Diagnosis

Investigate login failures triggered by XdbHost process restarts on the DB node. These incidents present as CRGW0001 alerts with `LoginFailureCause: HasXdbHostRestarts` and typically produce a cascade of 40613 errors with multiple state codes.

## Overview

When the XdbHost process restarts on a DB node (due to automation, dumps, kill commands, or failover), in-flight and new login/connection requests fail with a predictable error cascade:

1. **State 12** (FailedToPrepareDuplicatedData) — socket duplication preparation fails
2. **State 44** (LoginRequestSqlFailedToDuplicateLoginFromXdbHost) — socket dup handoff fails
3. **State 10** (CantFindRequestedInstance) — instance not found (bulk of errors)
4. **State 13** (FailedToSendDuplicateData) — SNIOpen failures
5. **State 126** (LoginSessDb_DbNotFound) — DB not yet registered after restart
6. **State 22** (DueToProxyConnextThrottle) — gateway-level throttling from backlog

The goal is to determine: (a) what triggered the restart, (b) was the restart duration normal, (c) was the impact amplified by external factors (e.g., high login volume, user errors), and (d) is the issue self-mitigated.

## Required Information

### From User or ICM:
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill:
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **DBNodeName** (DB node hosting the primary replica)
- All other database environment variables

**Note**: The calling agent should use the `execute-kusto-query` skill and the `get-db-info` skill before invoking this skill.

## Investigation Workflow

**Important**: Output the results from each step as specified. Complete all steps before providing conclusions.

### 1: Confirm XdbHost Restart via Process ID Change

Query `MonXdbhost` to detect process_id changes for the instance, which confirms a restart occurred.

**Execute query:** XR100 from [references/queries.md](references/queries.md)

**What to look for:**
- Two different `process_id` values with a gap between `max(TIMESTAMP)` of the old process and `min(TIMESTAMP)` of the new process
- The gap duration = approximate restart time
- Normal: < 30 seconds
- 🚩 Gap > 60 seconds is unusual and warrants investigation

**Decision:**
- **No process_id change found** → This is NOT an XdbHost restart. Reroute to `.github/skills/Connectivity/connectivity-scenarios/login-failure/SKILL.md` for general login failure investigation.
- **Process_id change confirmed** → Record restart gap duration and continue to Step 2.

### 2: Determine Restart Trigger

Query `MonXdbhost` for the instance to identify what caused the restart.

**Execute query:** XR200 from [references/queries.md](references/queries.md)

**Classify the trigger based on patterns found:**

| Pattern Found | Likely Trigger |
|--------------|----------------|
| No XdbHost errors before restart | CAS KillProcess |
| Dump files referenced in logs | XdbHost dump/crash |

### 3: Check for Automation / Bot Actions

Determine if the restart was triggered by automation such as `ResolveUnavailability` bot, CAS KillProcess, or a runner action.

**Execute query:** XR300 from [references/queries.md](references/queries.md)

**What to look for:**
- `OutageReasonLevel1 = "CAS"` and `OutageReasonLevel2 = "KillProcess"` — manual or automated process kill
- `OutageReasonLevel1 = "Bot"` with `ResolveUnavailability` mention — bot killed primary due to login thresholds
- Runner restart actions for proxy throttle mitigation

**Execute query:** XR310 from [references/queries.md](references/queries.md)

**What to look for:**
- Entries where `request` or `parameters` contain `xdbhostmain` — these are actions directly targeting the XdbHost process and are strong indicators of an externally triggered restart
- Entries targeting other processes (e.g., `sqlservr`) — list as informational context only; they may correlate but are not direct XdbHost triggers
- `request_action` values such as `KillProcess`, `ExecuteKillProcess` are high-signal indicators
- Correlate `time_created` of the action with the restart gap from Step 1

**Decision:**
- **Automation found** → Continue to Step 4 to check if user errors triggered the automation.
- **No automation** → If trigger is still unknown, classify based on XdbHost logs from Step 2.

### 4: Characterize the Login Error Distribution

Query `MonLogin` to understand the full error distribution and separate user errors from system errors.

**Execute queries:** XR400 and XR410 from [references/queries.md](references/queries.md)

**What to look for:**
- **User errors (is_user_error = true)**: 18456/132 (FedAuthAADLoginJWTUserError), 18456/122 (CloudEmptyUserName), 18456/170 (AadOnlyAuthenticationEnabled)
- **XdbHost restart errors (is_user_error = false)**: 40613 states 10, 12, 13, 44, 126
- **Gateway throttling**: 40613/22 (DueToProxyConnextThrottle), 42127/22
- **Timeline**: User errors often precede the restart; restart errors cluster in a tight 1-5 minute window

🚩 If user errors >> system errors in the window BEFORE the restart, the root cause is customer-side authentication error flood triggering automation.

### 5: Measure Restart Impact Duration

From Steps 1 and 4 results, determine:
- **Restart window**: Time between first state 10/12/44 error and last state 126 error
- Normal: < 2 minutes
- Warning: 2-5 minutes
- 🚩 Critical: > 5 minutes

### 6: Check Login Volume

Query `MonLogin` for the login rate per minute.

**Execute query:** XR600 from [references/queries.md](references/queries.md)

**What to look for:**
- 🚩 > 2500 logins/minute per instance = extremely high volume — amplifies the restart impact
- High volume + user errors = customer flooding with bad credentials

### 7: Verify Self-Mitigation

Confirm the issue resolved after the restart window.

**Execute query:** XR700 from [references/queries.md](references/queries.md)

**What to look for:**
- `SuccessCount` should resume and increase after restart completes
- `RestartErrors` (states 10, 12, 13, 44, 126) should drop to 0
- 🚩 If 40613/22 persists AFTER restart completes, investigate as a separate gateway/network issue
- 🚩 If any restart-related errors persist > 15 minutes after new process_id appears, escalate

## Execute Queries

Execute queries from [references/queries.md](references/queries.md):

**Step 1: Confirm Restart**
- XR100 (Detect Process ID Change)

**Step 2: Determine Trigger**
- XR200 (XdbHost Process Logs)

**Step 3: Check Automation**
- XR300 (Outage Reason Classification)
- XR310 (Audit Trail for Automation/User Actions on Node)

**Step 4: Error Distribution**
- XR400 (Login Error Breakdown)
- XR410 (Login Error Time Distribution - 1 min bins)

**Step 6: Login Volume**
- XR600 (Login Rate Per Minute)

**Step 7: Self-Mitigation**
- XR700 (Post-Restart Login Success Rate)

## Decision Tree Summary

```
HasXdbHostRestarts ICM
│
├── Step 1: Confirm restart (MonXdbhost process_id change)
│   ├── No restart found → Reroute to login-failure skill
│   └── Restart confirmed →
│
├── Step 3: Automation/user action triggered? (MonNonPiiAudit)
│   ├── Yes (CAS KillProcess or runner or bot) →
│   │   └── Step 4: Check if user errors preceded it
│   │       ├── Yes → Root cause = customer error flood → automation/user response → restart
│   │       └── No → Root cause = automation/user action (investigate why)
│   └── No →
│
├── Step 2: XdbHost dump/crash? (MonXdbhost logs)
│   ├── Yes → Root cause = xdbhost crash (report for engineering investigation)
│   └── No → Unknown trigger (escalate)
│
└── Step 7: Self-mitigated?
    ├── Yes → Close with appropriate RCA classification
    └── No → Escalate (ongoing issue)
```

## Reference

- [knowledge.md](references/knowledge.md) — XdbHost architecture, restart causes, error cascade definitions
- [principles.md](references/principles.md) — Debug principles, timing thresholds, and escalation criteria
- [queries.md](references/queries.md) — All Kusto queries (XR100-XR700)
