!!!AI Generated.  To be verified!!!

# Debug Principles for XdbHost Restart Diagnosis

## Triage Principles

1. **Confirm this is an XdbHost restart scenario**: The ICM title or alert contains `HasXdbHostRestarts` as the `LoginFailureCause`. If the login failures are NOT associated with an XdbHost restart, use the general `login-failure` skill instead.

2. **XdbHost restart is a symptom, not always the root cause**: The restart itself may be triggered by automation responding to another problem (e.g., user error floods, proxy throttle). Always determine what triggered the restart.

3. **Error 40613 State 22 is a consequence, not a cause**: When found alongside XdbHost restart errors (states 10, 12, 13, 44, 126), the proxy throttle (state 22) is typically the gateway response to the backlog created by the restart. Do not treat it as an independent root cause.
   - 🚩 Exception: If state 22 errors persist AFTER the restart window completes, investigate as a separate gateway/network issue.

4. **Multiple 40613 substates in a tight window = single event**: If you see states 10, 12, 13, 44, 126 all appearing within a 1-5 minute window, this is the characteristic error cascade of a single XdbHost restart, not multiple independent problems.

## Diagnosis Principles

### Principle 1: Confirm Restart Before Investigating Cause
- Always check `MonXdbhost` for process_id change FIRST
- If no process_id change found, this is NOT an XdbHost restart — reroute to `login-failure` skill
- 🚩 If process_id change found, record the restart gap (time between old process end and new process start)

### Principle 2: Classify the Restart Trigger
- Check automation/bot actions first — they account for the majority of cases
- Check for dump files via `MonXdbhost` logs — indicates a crash, not an intentional restart
- Normal behavior: No manual intervention, self-mitigates
- 🚩 Problematic: Repeated restarts on the same node within hours

### Principle 3: Assess User Error Contribution
- High-volume user authentication errors (especially 18456/132 `FedAuthAADLoginJWTUserError`) can trigger automation that kills XdbHost
- If user_error_count >> system_error_count in the window BEFORE the restart, the root cause is customer-side
- 🚩 Repeat offenders: Some applications generate sustained authentication error floods (thousands per minute)

### Principle 4: Self-Mitigation Assessment
- Most HasXdbHostRestarts incidents are self-mitigating
- The `SuppressedIncidentMitigator` typically closes these after health properties expire
- Verify recovery by checking MonLogin for successful logins resuming post-restart
- 🚩 If errors continue 15+ minutes after restart completes, escalate

## Expected Timings

| Event | Normal | Warning | Critical |
|-------|--------|---------|----------|
| XdbHost restart gap (process_id change) | < 30 seconds | 30-60 seconds | > 60 seconds |
| Error cascade duration | < 2 minutes | 2-5 minutes | > 5 minutes |
| Full recovery (successful logins resume) | < 5 minutes | 5-15 minutes | > 15 minutes |
| Login volume per minute per instance | < 500/min | 500-2500/min | > 2500/min |

## Error Cascade Timing

The XdbHost restart error cascade follows a predictable sequence:

```
Time (relative to restart):
  T+0s:    State 12 (FailedToPrepareDuplicatedData) — first failures
  T+1-5s:  State 44 (LoginRequestSqlFailedToDuplicateLoginFromXdbHost)
  T+5-30s: State 10 (CantFindRequestedInstance) — bulk of errors
  T+5-30s: State 13 (FailedToSendDuplicateData) — SNIOpen failures
  T+20-60s: State 126 (LoginSessDb_DbNotFound) — DB not yet re-registered
  T+10-60s: State 22 (DueToProxyConnextThrottle) — gateway backlog
  T+30-120s: Recovery — successful logins resume
```

## Root Cause Classification

| Trigger Found | Root Cause Category | RCA Classification |
|--------------|--------------------|--------------------|
| User error flood → bot kill | Customer-driven | User errors triggered automation → XdbHost restart |
| Runner restart for proxy throttle | Automation response | Proxy throttle mitigation → XdbHost restart |
| CAS KillProcess | Manual/automated ops | Operations action → XdbHost restart |
| XdbHost dump/crash | Infrastructure | XdbHost crash → restart |
| No identifiable trigger | Unknown | Escalate for engineering investigation |

## Escalation Criteria

- 🚩 Restart duration > 60 seconds
- 🚩 Errors persist > 15 minutes after restart completes
- 🚩 Multiple restarts on the same node within 6 hours
- 🚩 Unknown restart trigger (no automation, no failover, no dump)
- 🚩 Customer confirms ongoing impact after health property expiration
