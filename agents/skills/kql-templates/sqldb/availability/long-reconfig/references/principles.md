# Debug Principles for Long Reconfiguration Database Investigation

!!!AI Generated. To be verified!!!

## Triage Principles

### 1. Check If Issue Is Still Active

Before proceeding with investigation, verify the issue has not already self-healed or been mitigated by automation.

1. **Check AlrWinFabHealthPartitionEvent:** Look for recent "Partition reconfiguration is taking longer than expected" alerts
2. **Check SFE:** Verify database partition state
   - ❌ **State = Reconfiguring:** Issue is still active — proceed with investigation
   - ✅ **State = Ready:** Issue has self-healed — mitigate the incident

### 2. Systematic Case Identification

Work through the known cases in order. Each case has specific verification queries:

| Priority | Case | Verification Method | Applies To |
|----------|------|---------------------|------------|
| 1 | Error 41614 state 27 | MonFabricApi: error_code 41614, error_state 27 | GP instances only |
| 2 | Inconsistent Remote Replicas | MonSQLSystemHealth: error_id 5120 | All tiers |
| 3 | Error 5173 file mismatch | MonSQLSystemHealth: error_id 5173 | GeoDR scenarios |
| 4 | Long Running Checkpoint | MonFabricDebug: checkpoint start without finish | All tiers |
| 5 | Instance Boot Deadlock | MonSQLSystemHealth: DelayKillingSessionsHoldingReplMasterLocks | All tiers |
| 6 | Unknown | MonSQLSystemHealth: general error survey | All tiers |

### 3. Always Dump Before Mitigating Unknown Issues

- 🚩 For any unknown issue, **always take a dump before killing the process**
- Document the dump link in the incident
- CAS commands for dump and kill can be found in the "Database Replicas.xts" view under CAS commands tab

## Mitigation Principles

### 4. Mitigation Order

1. **Check self-heal first** — Issue may have already resolved
2. **Identify the specific case** — Run verification queries for each known case
3. **Check infrastructure health (Step 2b)** — Verify container and networking are healthy before any SQL-level mitigation
4. **🚩 If infrastructure issue found (NC failures, container crashes):** Do NOT kill SQL processes — escalate to **SQL MI: Connectivity and Networking**. Killing SQL will not fix networking/container issues and may worsen the situation.
5. **Apply case-specific mitigation** — Follow the documented fix for the identified case (only if infrastructure is healthy)
6. **If unknown case and infrastructure is healthy:** Take dump → Kill SQL process → If no improvement, restart node from SFE

### 5. Post-Mitigation Verification

After mitigation:

1. **Wait 15 minutes** for changes to take effect
2. **Check SFE:** Database should show "Ready" state (not "Reconfiguring")
3. **Run verification query:** Check AlrWinFabHealthPartitionEvent for new timestamps
   - ✅ Last timestamp before mitigation — Issue is healed
   - ❌ New timestamps after mitigation — Issue persists, try alternative mitigation or escalate

## Expected Timings

| Event | Normal | Warning | Critical |
|-------|--------|---------|----------|
| Partition reconfiguration | < 2 min | 2-10 min | > 10 min |
| Checkpoint completion | < 5 min | 5-30 min | > 30 min |
| Process kill effect | < 2 min | 2-5 min | > 5 min |
| Post-mitigation verification | ~15 min | — | — |

## Escalation Criteria

- 🚩 Issue persists after kill + node restart
- 🚩 None of the known cases match and general error investigation is inconclusive
- 🚩 Multiple databases on the same instance affected

**Escalation path:**
- **Primary:** SQL Managed Instance: Availability
- **After hours:** SQL Managed Instance Expert: HA & GeoDR
