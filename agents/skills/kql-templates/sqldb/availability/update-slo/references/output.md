# Update SLO Investigation Output Format

**MANDATORY**: Whenever presenting timestamps in output, always include the date as well, using the format `yyyy-MM-dd HH:mm:ss`.

---

## State Machine Timeline

**MANDATORY**: Generate a chronological table of all FSM state transitions from USLO210 query results.

**Format:**

| Timestamp | State Machine | Old State | New State | Duration | Status |
|-----------|---------------|-----------|-----------|----------|--------|
| yyyy-MM-dd HH:mm:ss | UpdateSloStateMachine | Pending | CreatingTargetSqlInstance | — | ✅ |
| yyyy-MM-dd HH:mm:ss | UpdateSloStateMachine | CreatingTargetSqlInstance | Copying | 2m 15s | ✅ |
| yyyy-MM-dd HH:mm:ss | UpdateSloStateMachine | Copying | CheckingRedoQueueSize | 45m 30s | ✅ |
| yyyy-MM-dd HH:mm:ss | UpdateSloStateMachine | CheckingRedoQueueSize | (still in this state) | 4h 22m | 🚩 STUCK |

**Instructions:**
- List ALL FSM state transitions from USLO210 query results
- Sort by timestamp chronologically
- Calculate duration from previous transition
- Apply Principle 3 (State Routing Table) to mark each state as ✅ or 🚩
- Use actual timestamps from query results — DO NOT estimate or create timestamps
- Highlight the stuck state (if any) with 🚩 and note the sub-TSG

---

## Update SLO Operation Summary

| Property | Value |
|----------|-------|
| Logical Server | {LogicalServerName} |
| Logical Database | {LogicalDatabaseName} |
| Request ID | {request_id} |
| Operation Type | UpdateDatabase |
| Source SLO | {source_slo} |
| Target SLO | {target_slo} |
| Direction | Upgrade / Downgrade |
| Update Mode | ContinuousCopyV2 / DetachAttach / InPlace |
| Source AppName | {source_app_name} |
| Target AppName | {target_app_name} |
| Start Time | yyyy-MM-dd HH:mm:ss |
| Current Duration | {hours}h {minutes}m |
| Current State | {stuck_state} |
| Status | ✅ Completed / 🚩 Stuck / ❌ Failed |

---

## Exceptions and Errors

If exceptions found in USLO300:

| Timestamp | Event | State Machine | Action | Exception Type | Sanitized Details |
|-----------|-------|---------------|--------|----------------|-------------------|
| yyyy-MM-dd HH:mm:ss | fsm_executed_action_failed | UpdateSloStateMachine | {action} | {exception_type} | {type + top frame + sanitized message — redact connection strings, tokens, and customer PII} |

---

## Replication Status (ContinuousCopyV2 only)

If USLO400 was executed:

| Timestamp | Replication Lag (sec) | Replication State | Percent Complete |
|-----------|-----------------------|-------------------|-----------------|
| yyyy-MM-dd HH:mm:ss | {lag} | {state} | {percent}% |

---

## Stuck State Analysis

🚩 **Stuck State: {state_name}**

| Property | Value |
|----------|-------|
| Duration in State | {duration} |
| Expected Duration | {expected} (from Principle 3) |
| Applicable Sub-TSG | {sub_tsg_id}: {sub_tsg_name} |
| Exception Present | Yes/No |
| Exception Details | {exception_summary} |

**Root Cause**: {description based on principles and evidence}

**Recommended Mitigation**:
1. {step 1 from applicable sub-TSG}
2. {step 2}
3. {step 3}

---

## SLO Transition History

From USLO600:

| First Seen | Last Seen | SLO | Edition | State | Cluster |
|------------|-----------|-----|---------|-------|---------|
| yyyy-MM-dd HH:mm:ss | yyyy-MM-dd HH:mm:ss | {slo} | {edition} | {state} | {cluster} |

---

## Summary of Findings

### Root Cause
{Clear, evidence-based root cause statement}

### Impact
- **Operation Duration**: {total duration}
- **Database Availability**: {was database available during the stuck operation?}
- **Customer Impact**: {describe impact}

### Mitigation
{Specific mitigation steps or confirmation that the operation completed}

### Relevant TSGs
- {TSG_ID}: {TSG_Name} — {brief reason}
- {TSG_ID}: {TSG_Name} — {brief reason}

### Escalation (if needed)
- **Team**: {team name from knowledge.md routing}
- **Reason**: {why escalation is needed}
