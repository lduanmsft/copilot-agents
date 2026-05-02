---
name: error-18456-state-113
description: This skill focuses on diagnosing login error 18456 state 113 (DosGuard rejected the connection). This error occurs when connection rate from a given IP exceeds thresholds.
---

## Background Information

Too many user failures from a given IP address will block further connection attempts from going through due to DosGuard (also known as **Password Protection** in the Gateway). This means when DosGuard is active both good and bad logins will be rejected for the blackout period for that IP. The DosGuard error is 18456 and state 113.

**How DosGuard Works (from ADO Wiki - DosGuard-Explained):**
- A login failure with error 18456 triggers DosGuard registration if it is from an IP that is **not allowed through the server/database firewall rules**
- New logins from this IP are failed for **5 minutes** with the DosGuard error (18456/113)
- DosGuard errors themselves are excluded from triggering more DosGuard activations
- Related states that can trigger DosGuard: `FirewallBlockedAddressAllowAzureIpRulePresent`

**Important:** The presence of DosGuard is not public information - do NOT disclose it to external customers. Query MonLogin to see what user errors are causing failures for this database and triggering DosGuard, and follow mitigation instructions for that error and state. If DosGuard is triggered by a client error that the customer cannot control (e.g. bad login, bad password), they can suppress DosGuard for a given client IP by explicitly adding that IP to the firewall rules. To get more details, you will have to get access to PIILogin table.

**Common Triggers for DosGuard:**
1. **Empty passwords** - Logins with empty passwords trigger DosGuard (from CRI-Escalation-Checklist-for-Gateway)
2. **FedAuth/AAD failures** - Too many failed AAD login attempts from same IP
3. **Missing permissions** - Application connecting before permissions are configured
4. **Invalid credentials** - Wrong password or non-existent login

**Package:** sqlserver (SQL Engine)
- Ring: Tenant
- MDS: MonLogin
- NodeRole: DB
- Event: process_login_finish

## Required Information from Previous Steps

Before using this skill, ensure you have:
- **LogicalServerName**: From user input
- **LogicalDatabaseName**: From user input  
- **StartTime** and **EndTime**: From user input
- **ConnectivityRingName(s)**: From "determine-connectivity-ring" skill
- **kusto-cluster-uri** and **kusto-database**: From "execute-kusto-query" skill


## Step 1: DosGuard Triage

### Step 1: Confirm DosGuard is Active

**Goal:** Quickly confirm we have DosGuard errors (18456/113) and understand the scope.

```kusto
// Step 1: Confirm DosGuard errors exist and get scope
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event == "process_login_finish"
| where is_success == 0
| where error == 18456 and state == 113
| summarize DosGuardCount = count(), 
            FirstSeen = min(originalEventTimestamp), 
            LastSeen = max(originalEventTimestamp)
    by state_desc
```

**Expected Output:** If rows return with `state_desc == "DosGuardRejectedConnection"`, DosGuard is confirmed.

**If no rows returned:** This is NOT a DosGuard issue - investigate other 18456 states using parent skill.

---

## Step 2: Visualize Timeline and Duration

**Goal:** Understand when DosGuard started, how long it lasted, and if it's still active.

```kusto
// Step 2: Timeline showing DosGuard vs other errors over time
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event == "process_login_finish"
| where is_success == 0
| extend ErrorType = case(
    state == 113, "DosGuard_113",
    state == 5, "SecGetLogin2_5",
    state == 8, "IncorrectPassword_8",
    strcat("Other_", state))
| summarize count() by ErrorType, bin(originalEventTimestamp, 15m)
```

**Analysis:**
- Look for the **first spike** of non-DosGuard errors (state 5, 8, etc.) - this is the trigger
- DosGuard errors (113) should appear **after** the trigger errors
- If DosGuard stops in the chart, the 5-minute blackout has expired

---

## Step 3: Identify Root Cause Error

**Goal:** Find which error triggered DosGuard. This is the MOST IMPORTANT step.

```kusto
// Step 3: Find root cause errors (what triggered DosGuard)
MonLogin
| where originalEventTimestamp between (datetime({StartTime}) - 15m .. datetime({EndTime})) // Look 15min before
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event == "process_login_finish"
| where is_success == 0 and is_user_error == 1
| where state != 113 // Exclude DosGuard errors - we want the root cause
| summarize ErrorCount = count(), 
            FirstSeen = min(originalEventTimestamp),
            SamplePeerAddress = take_any(peer_address)
    by error, state, state_desc
| order by ErrorCount desc
```

**Common Root Causes:**
| State | Description | Action |
|-------|-------------|--------|
| 5 | SecGetLogin2 - Login not found | Check if login exists, permissions configured |
| 8 | Incorrect password | Verify credentials |
| 46 | Token validation failure | Check AAD token configuration |
| 65 | Incorrect password | Verify credentials |
| Empty password | Logins with empty passwords | Fix application configuration |

**Next:** The top error in this list is your root cause. Fix that error to prevent DosGuard.

---

## Step 4: Identify Affected Applications

**Goal:** See which applications are affected and the authentication method they use.

```kusto
// Step 4: Applications affected by DosGuard
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event == "process_login_finish"
| where error == 18456
| extend authentication = case(
    fedauth_library_type == 0 and fedauth_adal_workflow == 0, "SQL Auth",
    fedauth_library_type == 2 and fedauth_adal_workflow == 0, "Token Auth",
    fedauth_library_type == 3, "AAD Auth",
    "Other")
| summarize 
    DosGuardErrors = countif(state == 113),
    OtherErrors = countif(state != 113),
    TotalErrors = count()
    by application_name, authentication, peer_address
| order by TotalErrors desc
| take 20
```

**Analysis:**
- **High DosGuardErrors, Low OtherErrors:** This app is a victim (blocked due to another app's failures)
- **High OtherErrors:** This app is the culprit triggering DosGuard
- **Multiple apps from same peer_address:** All apps from that IP are blocked once DosGuard triggers

---

## Step 5: FedAuth/AAD Correlation (If Token Auth Detected)

**Goal:** If Step 4 shows "Token Auth" or "AAD Auth", correlate with FedAuth failures.

```kusto
// Step 5: Correlate with FedAuth failures (only if AAD authentication)
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let dosguard_connections = 
    MonLogin
    | where originalEventTimestamp between (StartTime..EndTime)
    | where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
    | where error == 18456 and state == 113
    | distinct connection_id;
MonFedAuthTicketService
| where TIMESTAMP between (StartTime..EndTime)
| where sql_connection_id in (dosguard_connections)
| summarize count() by event, error_code, error_state
| order by count_ desc
```

**Skip this step** if Step 4 showed "SQL Auth" only.

---

## Step 6: Detailed Event Analysis (If Needed)

**Goal:** Deep dive into specific events to understand the exact sequence.

```kusto
// Step 6: Detailed timeline with network context
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event == "process_login_finish"
| where is_success == 0
| project originalEventTimestamp, error, state, state_desc, 
          application_name, peer_address, 
          is_vnet_address, is_azure_ip, is_targeted_rule
| order by originalEventTimestamp asc
| take 100
```

**Use this to:**
- See the exact chronological order of errors
- Identify the transition from root cause errors → DosGuard activation
- Confirm if errors are coming from same IP/VNET

---

## Step 7: Identify Client IPs (Requires PII Access)

**Note:** Requires "WA SQL DB Sensitive Information Access" via myaccess portal.

```kusto
// Step 7: Get client IPs being blocked (PII access required)
PIILogin
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where error == 18456 and state == 113
| summarize DosGuardCount = count(), 
            FirstSeen = min(TIMESTAMP), 
            LastSeen = max(TIMESTAMP)
    by client_ip
| order by DosGuardCount desc
```

**Use This Info To:**
- Tell customer which IP to add to firewall rules (to bypass DosGuard)
- Identify if attack is from single IP or distributed

---

## Troubleshooting Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Confirm DosGuard (18456/113 errors exist?)          │
│         └── No rows? → Not DosGuard, use parent 18456 skill │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Timeline (When did it start? Still active?)         │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Root Cause (What error triggered DosGuard?)         │
│         → State 5 (SecGetLogin2) = Missing login/permission │
│         → State 8/65 = Wrong password                       │
│         → State 46 = AAD token issue                        │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Affected Apps (Which app is the culprit?)           │
│         High OtherErrors = Culprit app                      │
│         High DosGuardErrors only = Victim app               │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: FedAuth (If AAD auth detected in Step 4)            │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 6-7: Deep Dive (If more details needed)                │
└─────────────────────────────────────────────────────────────┘
```

## Diagnosis and Mitigation

### DosGuard Protection Triggered

**Root Cause:** DosGuard protection is triggered when connection rate exceeds thresholds from a specific IP address. Once triggered, DosGuard blocks ALL connections from that IP (both good and bad logins) for **5 minutes**.

**Mitigation Options:**

1. **Fix the underlying error** (Most Common Resolution)
   - Step 3 shows the root cause error (state 5, 8, 46, etc.)
   - Step 4 shows which application is the culprit (high OtherErrors count)
   - Fix that specific error - DosGuard will automatically stop after 5 minutes

2. **Wait for DosGuard blackout to expire**
   - DosGuard blocking is temporary (**5 minutes** per ADO wiki documentation)
   - Once the root cause is fixed, connections resume automatically
   - Monitor Step 1 - when no more rows return, DosGuard has lifted

3. **Bypass DosGuard for specific IP** (If customer cannot fix root cause)
   - Customer adds the blocked IP to explicit firewall allow rules
   - This bypasses DosGuard protection for that specific IP
   - Use Step 7 to get the client IP (requires PII access)

4. **Application-side fixes**
   - Implement connection pooling to reduce connection rate
   - Add exponential backoff on retries (avoid retry storms)
   - Ensure permissions are configured BEFORE deploying new services

**Important Notes:**
- Do NOT disclose DosGuard to external customers (it is not public information)
- Always identify the ROOT CAUSE error (Step 3), not just DosGuard itself
- DosGuard blocks ALL apps from the same IP, not just the culprit app

**TSG Reference:** 
https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/server-database/dosguard

---

## Output to User

After running the queries, provide the following summary:

- **Error State Detected:** 18456 State 113 (DosGuard)
- **Confirmed:** Yes/No [from Step 1]
- **Duration:** FirstSeen to LastSeen [from Step 1]
- **Root Cause Error:** State X (description) - Y failures [from Step 3]
- **Culprit Application:** [app with high OtherErrors from Step 4]
- **Affected Applications:** [list of apps with high DosGuardErrors from Step 4]
- **Authentication Type:** [from Step 4]
- **Client IP(s):** [from Step 7 if PII access available]
- **Status:** Active/Resolved [based on Step 2 timechart]
- **Resolution:** Fix [root cause error] in application [culprit app]

**References:** 
- TSG: https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/server-database/dosguard
- ADO Wiki: DosGuard-Explained (Database Systems wiki)

**Warning:** !!!AI Generated. To be verified!!!
