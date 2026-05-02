---
name: login-failure
description: Debug Azure SQL Database login failure issues including authentication errors, access denied messages, and related problems. Use when investigating SQL Database login issues, authentication failures, or authorization problems. Accepts either ICM ID or direct parameters (logical server name, database name, time window). Executes Kusto queries via Azure MCP to analyze telemetry data including login events, authentication attempts, and security-related information.
---

# Debug Azure SQLDB login failure issues

## Required Information

This skill requires the following inputs (should be obtained by the calling agent):

### From User or ICM:
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

OR

- **Connectivity Ring Name** (e.g., `cr11.eastasia1-a.control.database.windows.net`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill (one or more configurations):
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **logical_database_id**
- **physical_database_id**
- **fabric_partition_id**
- **service_level_objective**
- **zone_resilient**
- **deployment_type** (e.g., "GP without ZR", "GP with ZR", "BC")
- **config_start_time** (when this configuration was active from)
- **config_end_time** (when this configuration was active until)
- All other database environment variables

**Note**: The calling agent should use the `execute-kusto-query` skill and the `get-db-info` skill before invoking this skill. If multiple database configurations exist (e.g., tier change during incident), the agent should invoke this skill separately for each configuration with its respective time window.

## Workflow

**Important**: Output the results from each step as specified, and ensure to complete the execution verification checklist before providing any conclusions or summaries to the user.

### 1: Validate Inputs

Ensure all required parameters are provided:
- From user/ICM: LogicalServerName, LogicalDatabaseName, StartTime, EndTime
- From execute-kusto-query: kusto-cluster-uri, kusto-database, region
- From get-db-info: AppName, ClusterName, physical_database_id, fabric_partition_id, deployment_type, config_start_time, config_end_time, and all other database variables

**Note**: If analyzing a specific database configuration (when multiple exist), use config_start_time and config_end_time to scope the analysis to that configuration's active period.

Calculate `Duration` between StartTime and EndTime (e.g., `1h`, `101m`).

### 2: Determine login target
Follow **.github/skills/Connectivity/connectivity-base/determine-login-target/SKILL.md** skill.

### 3: Check for failover/availability events
Follow **.github/skills/Availability/failover/SKILL.md** to check if there are any failover or availability events during the time window. If failover/availability issues are found, treat the login failure as a consequence, instead of treating it as an independent issue.

### 4: Determine the connectivity ring(s) involved for the given logical server name/database name
Follow **.github/skills/Connectivity/connectivity-base/determine-connectivity-ring/SKILL.md** skill and output the result.

### 5: Determine Connection type
Follow **.github/skills/Connectivity/connectivity-base/connectivity-connection-type/SKILL.md** skill and output the overall connection type including Proxy or Redirect mode and client type (Public/Private Endpoint/Service Endpoint).

### 6: Determine the prevailing error and the scope
Follow **.github/skills/Connectivity/connectivity-base/determine-prevailing-error/SKILL.md** skill and output the data analysis.
Do not draw any conclusion yet. We will further troubleshoot in the next steps.

**Important**: 

If you find any Error 40613 State 22 or DueToProxyConnextThrottle, do not consider this as root cause. We will further diagnose the case in the next step.

### 7: Analyze the error
 
**🚨🚨🚨 MANDATORY ERROR-SPECIFIC SKILL EXECUTION - STOP GATE 🚨🚨🚨**
 
**⛔⛔⛔ HARD STOP: You CANNOT proceed to Task 8 until ALL applicable error-specific skills are FULLY executed. This is NON-NEGOTIABLE. ⛔⛔⛔**
 
For each distinct non-user error code and state found in Task 6, look up an error-specific skill using the **folder naming convention** under `.github/skills/Connectivity/connectivity-errors/`:
 
**Skill Lookup Order** (for each error code + state):
1. **Exact match**: `.github/skills/Connectivity/connectivity-errors/error-{code}-state-{state}/SKILL.md`
2. **Code-only fallback**: `.github/skills/Connectivity/connectivity-errors/error-{code}/SKILL.md`
3. **No skill found**: Document "No specific skill found for Error {code} State {state}" and proceed.
 
> Example: Error 40613 State 22 → first try `error-40613-state-22/SKILL.md`, if missing try `error-40613/SKILL.md`.
 
For each matching skill found, read and execute **ALL** steps defined in that skill file, run **ALL** Kusto queries, and output results before proceeding to the next error.
 
**📝 MANDATORY OUTPUT FORMAT** before proceeding to Task 8:
```
### Task 7: Error-Specific Skill Execution Summary
 
| Error | State | Skill Path | Steps Completed | Key Findings |
|-------|-------|------------|-----------------|---------------|
| {code} | {state} | error-{code}-state-{state}/ | N/N ✅ | ... |
| {code} | {state} | No skill found | N/A | General analysis from Task 6 |
```

### 8: Check if there are any anomalies in the connectivity ring(s)

For the connectivity ring(s) identified in Task 4 or the specific connectivity ring specified by the user, run the connectivity-ring-health skill against the connectivity ring(s) to check the health.

**Important**:

1. If there were no Error 40613, State 22 found in task 6 while you found SNAT port exhaustion events from the connectivity-ring-health skill, in root cause summary list SNAT port exhaustion as warning only (instead of critical finding) and suggest user should verify if this correlates to the exact problem time window.

2. **🚩 TRIGGER CONDITIONS - Execute EagleEye Analysis:**
   If ANY of these errors/conditions are found in Task 6:
   - Error 40613 State 22 (DueToProxyConnextThrottle)
   - Error 40613 State 84  
   - Error 26078
   - lookup_state 10060 (TCP timeout)
   - SNAT port exhaustion (from GW1100)
   - ProxyOpen timeouts > 5000ms
   - Error related to Networking disconnection, timedout
   
     **→ IMMEDIATELY execute:** 
   ".github/skills/Connectivity/connectivity-utilities/access-eagleeye/SKILL.md" to analyze the connectivity between the source and the destination and output the analysis.
   
   This is MANDATORY.

**⚠️ CRITICAL: Proceed to Task 9 after this task - DO NOT STOP HERE**

### 9: Check if there are any anomalies on the DB node

Run the node-health skill to check if there are any anomalies on the DB node(s) associated with the login failure issue.

**🚨🚨🚨 MANDATORY NODE-HEALTH QUERIES - STOP GATE 🚨🚨🚨**

**⛔⛔⛔ HARD STOP: You CANNOT proceed to Task 10 or provide any conclusions until ALL queries below are executed and logged. This is NON-NEGOTIABLE. ⛔⛔⛔**

**EXECUTION REQUIREMENT**: For EACH query below, you MUST:
1. Execute the actual Kusto query (not just describe it)
2. Log the query parameters used
3. Record the result (even if empty - "0 rows returned" is valid)
4. Mark status as ✅ COMPLETE only AFTER execution

| Step | Query ID | Description | Query Executed? | Result Summary |
| ---- | -------- | ----------- | --------------- | -------------- |
| 9.1 | NH100 | Locate database node(s) | ⬜ REQUIRED | |
| 9.2 | NH200 | Check SF node state changes | ⬜ REQUIRED | |
| 9.3 | NH210 | Check node health issues | ⬜ REQUIRED | |
| 9.4 | NH300 | Check MonSQLInfraHealthEvents | ⬜ REQUIRED | |
| 9.5 | NH400 | Check for bugcheck events | ⬜ REQUIRED | |
| 9.6 | NH500 | Check node up/down in WinFabLogs | ⬜ REQUIRED | |
| 9.7 | NH600 | Check node repair tasks | ⬜ REQUIRED | |
| 9.8 | NH700 | Check RestartCodePackage actions | ⬜ REQUIRED | |

**⛔ ENFORCEMENT RULES (STRICTLY ENFORCED):**
1. **ALL 8 queries (9.1-9.8) are MANDATORY** - you MUST call mcp_azure_mcp_kusto for each one
2. **Empty results = still required** - "0 rows" is a valid finding, not a reason to skip
3. **No shortcuts** - you cannot combine queries or skip "obvious" ones
4. **NH300 extended window** - query from (OutageStart - 12h) to (OutageEnd + 24h)
5. **VERIFICATION GATE** - Before Task 10, output this exact table with ALL ✅ marks

**🔴 FAILURE MODE**: If you proceed to Task 10 or conclusions without executing ALL 8 queries, the investigation is INCOMPLETE and INVALID. Go back and execute missing queries.

**📋 MANDATORY OUTPUT FORMAT** - You MUST output this section in your report:
```
### Node Health Analysis (Task 9)
| Query | Parameters | Rows Returned | Key Findings |
| ----- | ---------- | ------------- | ------------ |
| NH100 | ClusterName=X, StartTime=Y | N rows | ... |
| NH200 | ... | ... | ... |
| NH210 | ... | ... | ... |
| NH300 | ... | ... | ... |
| NH400 | ... | ... | ... |
| NH500 | ... | ... | ... |
| NH600 | ... | ... | ... |
| NH700 | ... | ... | ... |
```

### 10: Check XDBHOST health

Run the skill ".github/skills/Connectivity/connectivity-utilities/xdbhost-metric-check/SKILL.md" to check XDBHOST health.

### 11: Check app health

Run the skill ".github/skills/Connectivity/connectivity-utilities/app-health/SKILL.md" to check app health.

### 12: Execution Verification (MANDATORY FINAL CHECK)

**🔴🔴🔴 STOP - COMPLETE THIS CHECKLIST BEFORE PROVIDING ANY CONCLUSIONS 🔴🔴🔴**

Before providing final summary to the user, you MUST complete this verification checklist. Output this exact table with actual values:

```
## ✅ Execution Verification Checklist

| Task | Description | Queries Run | Status |
| ---- | ----------- | ----------- | ------ |
| 1 | Validate Inputs | N/A | ⬜ |
| 2 | Determine login target | Skill executed | ⬜ |
| 3 | Check Failover/Availability | mcp_azure_mcp_kusto called | ⬜ |
| 4 | Determine connectivity ring | Skill executed | ⬜ |
| 5 | Determine Connection type | Skill executed | ⬜ |
| 6 | Determine prevailing error | MonLogin queries run | ⬜ |
| 7 | Analyze Error (connectivity-errors) | **ALL steps in each error-specific skill** | ⬜ |
| 8 | Check Connectivity Ring Health | GW queries run | ⬜ |
| 9 | Node Health Analysis | **ALL 8 queries (NH100-NH700)** | ⬜ |
| 10 | XDBHOST Health | XDBHOST skill executed | ⬜ |
| 11 | App Health | App Health skill executed | ⬜ |
```

**⛔ CRITICAL VALIDATION:**
1. If ANY row shows ⬜, you MUST go back and execute that task NOW
2. **Task 7 validation**: For EACH error found, verify:
   - Error-specific skill was navigated to (e.g., `error-40613-state-84/SKILL.md`)
   - ALL steps in that skill were executed (e.g., 8/8 steps for error-40613-state-84)
   - The skill's execution verification checklist shows ALL ✅
3. Task 9 MUST show "ALL 8 queries" - partial execution is INVALID
4. Do NOT provide conclusions if any task is incomplete
5. Each ✅ requires actual tool execution, not just reading skill docs

**📋 Task 7 Error-Specific Skill Verification (MANDATORY):**

| Error Code | State | Skill Path | Steps in Skill | Steps Completed | Status |
|------------|-------|------------|----------------|-----------------|--------|
| 40613 | 84 | error-40613-state-84/ | 8 | ? | ⬜ |
| 18456 | 113 | error-18456-state-113/ | 4 | ? | ⬜ |
| (add rows for each error found) | | | | | |

**⛔ If ANY error-specific skill shows incomplete steps, go back and complete it NOW.**

**📝 If a task was intentionally skipped, you MUST:**
- State which task was skipped
- Provide explicit justification (e.g., "No connectivity ring errors found in Task 6, network analysis trigger conditions not met")
- Get user confirmation before proceeding
