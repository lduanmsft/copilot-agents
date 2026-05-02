---
name: error-18456
description: This skill focuses on diagnosing login error 18456 (Login failed for user) with various state codes. This error occurs in both SQL Engine and Gateway components.
---

## Background Information

Error 18456 indicates a login failure for a user attempting to connect to SQL Database. The error is accompanied by a state code that provides specific details about the failure reason. States are split by the package emitting the error:

- **SQL Engine (package: sqlserver)**
  - Ring: Tenant
  - MDS: MonLogin
  - NodeRole: DB
  - Event: process_login_finish
  - Source code: [/DsMainDev/Sql/Ntdbms/include/ELoginFailedState.h](https://msdata.visualstudio.com/Database%20Systems/_git/DsMainDev?path=/Sql/Ntdbms/include/ELoginFailedState.h)

- **Gateway (package: xdbgateway)**
  - Ring: Connectivity
  - MDS: MonLogin
  - NodeRole: Gateway

## Required Information from Previous Steps

Before using this skill, ensure you have:
- **LogicalServerName**: From user input
- **LogicalDatabaseName**: From user input  
- **StartTime** and **EndTime**: From user input
- **ConnectivityRingName(s)**: From "determine-connectivity-ring" skill
- **kusto-cluster-uri** and **kusto-database**: From "execute-kusto-query" skill

## Step 1: Identify Error Pattern and Scope

Execute the following query to understand which states are occurring and their scope:

```kusto
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ConnectivityRings = dynamic([{ConnectivityRingNames}]); // e.g., ["cr15.southcentralus1-a.control.database.windows.net"]
MonLogin
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName in~ (ConnectivityRings)
| where error == 18456
| where event == "process_login_finish"
| where logical_server_name =~ ''{LogicalServerName}'' and database_name =~ ''{LogicalDatabaseName}''
| summarize ErrorCount = count(), 
            min_time = min(TIMESTAMP), 
            max_time = max(TIMESTAMP),
            SampleConnectionId = take_any(connection_id)
    by package, state, is_user_error, error_message
| order by ErrorCount desc
```

**Output Analysis:**
- Identify the most frequent state code(s)
- Determine if errors are user errors (`is_user_error == true`)
- Note the package (sqlserver or xdbgateway)
- Proceed to the relevant state-specific section below

## State-Specific Diagnosis and Mitigation

### State 5 - Lookup in sql_logins_table failed

**Package:** sqlserver (SQL Engine)

**Possible causes and mitigation:**

**1. Database is unavailable**

If the customer uses contained users, database unavailability will prevent successful login. Check database health:

```kusto
let AppName = ''{AppName}''; // From get-db-info skill
MonDmDbHadrReplicaStates
| where AppName == AppName
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| project TIMESTAMP, AppName, synchronization_health_desc, database_state_desc
| order by TIMESTAMP asc
```

**Interpretation:**
- If `synchronization_health_desc` is not `HEALTHY` or `database_state_desc` is not `ONLINE`, there is an availability issue
- If database is `SUSPECT`: This requires SQL process restart to force recovery. Engage Availability team if issue persists.

**2. Database was dropped but connections continue**

Check if database exists in CMS:

**Note:** Use AdhocCMSQuery.xts view or equivalent CMS query tool:

```sql
SELECT *
FROM logical_databases
WHERE logical_database_name LIKE ''{LogicalDatabaseName}'';
```

If database does not exist, this is a customer issue - application needs to be updated to stop connection attempts.

**3. Login was dropped**

Query for DROP operations:

```kusto
MonLoginUserDDL
| where TIMESTAMP between (datetime({StartTime}) - 1d .. datetime({EndTime}))
| where logical_server_name =~ ''{LogicalServerName}''
| where operation_type =~ "DROP"
| project TIMESTAMP, logical_server_name, login_name, operation_type, initiated_by
```

**Mitigation:** Ask customer to recreate the login.

**4. AAD user lacks database access**

For AAD authentication, retrieve the connection ID from error pattern query above, then check PII data:

**Note:** Requires access to "WA SQL DB Sensitive Information Access" (request via myaccess portal)

```kusto
// Check FedAuth ticket information for AAD user
let ConnectionId = ''{SampleConnectionId}''; // From Step 1 query
let TenantRing = ''{TenantRingName}''; // From get-db-info skill
let LogicalServer = ''{LogicalServerName}'';
PIIFedAuthTicketService
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ TenantRing
| where LogicalServerName =~ LogicalServer
| where sql_connection_id =~ ConnectionId
| project TIMESTAMP, claim_appid, claim_oid, user_name, sql_connection_id
```

**Action:** Share `claim_appid` or `claim_oid` with customer to verify user permissions in the database.

---

### State 7 - Login for the user is disabled

**Package:** sqlserver

**Mitigation:** User error. Login is disabled on the server. Customer needs to enable the login using `ALTER LOGIN [username] ENABLE`.

---

### State 8 - Incorrect password

**Package:** sqlserver

**Mitigation:** User error. Password does not match. Ask customer to verify credentials.

---

### States 38 or 46 - Could not find database requested by user

**Package:** sqlserver

**Possible causes:**

1. **Database does not exist** - Straightforward user error
2. **Login lacks permission to open database (typically master)**

Check for `login_substep_failure` events:

```kusto
let ConnectionIds = MonLogin
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ ''{LogicalServerName}'' and database_name =~ ''{LogicalDatabaseName}''
| where error == 18456 and state in (38, 46)
| where event == "process_login_finish"
| distinct connection_id;
MonLogin
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where connection_id in (ConnectionIds)
| where event == "login_substep_failure"
| project TIMESTAMP, connection_id, error_code, error_message, database_name
```

**Look for error_code 916:**
- Message: "The server principal ''%.*ls'' is not able to access the database ''%.*ls'' under the current security context."
- **Workaround:** Create user from login in master database:

```sql
CREATE USER [username] FROM LOGIN [username];
```

**Reference:** See [IcM incident 25692703](https://portal.microsofticm.com/imp/IncidentDetails.aspx?id=25692703)

---

### State 62 - FedAuth AAD failures

**Package:** sqlserver

**Action:** This state indicates Azure Active Directory authentication failures. 

**Next Steps:**
1. Check `MonFedAuthTicketService` table for detailed fedauth errors
2. Refer to specialized TSG: `D:\TSG-SQL-DB-Connectivity-VScode\TSG\auth-certificates-tls\aad-fed-auth-login-failures.md`

Quick diagnostic query:

```kusto
MonFedAuthTicketService
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where error_state == 62
| where event in ("fedauth_ticket_service_failure", "fedauth_webtoken_failure")
| summarize count() by event, error_code, bin(TIMESTAMP, 5m)
| render timechart
```

---

### State 65 - Incorrect password

**Package:** sqlserver

**Mitigation:** User error. Password does not match. Ask customer to verify credentials.

---

### States 102-111 - FedAuth AAD failures

**Package:** sqlserver

**Action:** Various AAD/FedAuth authentication failures. Refer to AAD/FedAuth TSG for detailed troubleshooting.

---

### State 113 - DosGuard rejected the connection

**Package:** sqlserver

**Background:** DosGuard protection is triggered when connection rate exceeds thresholds.

**Next Steps:** Refer to specialized TSG: `D:\TSG-SQL-DB-Connectivity-VScode\TSG\server-database\dosguard.md`

Quick check query:

```kusto
MonLogin
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ ''{LogicalServerName}''
| where error == 18456 and state == 113
| summarize ConnectionAttempts = count() by bin(TIMESTAMP, 1m), database_name
| render timechart
```

**Interpretation:** High connection rate spikes indicate potential DoS pattern or application misconfiguration.

**Suggest user open this TSG link: **

https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/server-database/dosguard.html

---

### States 122-124 - Empty username or password

**Package:** sqlserver (non-fedauth only)

**Mitigation:** User error. Client application is sending empty username or password. This should only occur with SQL authentication (not AAD).

---

### State 126 - Database requested by user does not exist

**Package:** sqlserver

**Mitigation:** User error. Database name provided does not exist. Customer needs to verify database name or create the database.

---

### State 132 - FedAuth AAD Login JWT User Error

**Package:** sqlserver

**Background:** JWT token validation failure - typically expired or invalid token.

**Detailed diagnostic query:**

```kusto
let server = ''{LogicalServerName}'';
let database = ''{LogicalDatabaseName}'';
let min_time = datetime({StartTime});
let max_time = datetime({EndTime});
let fedauth_data =
    MonFedAuthTicketService
    | where TIMESTAMP between (min_time..max_time)  
    | where event == "fedauth_ticket_service_failure"  
    | extend lowerConnectionId = tolower(sql_connection_id)
    | where error_state == 132
    | project-rename service_event = event
    | join kind=fullouter (
        MonFedAuthTicketService
        | where TIMESTAMP between (min_time..max_time)  
        | where event == "fedauth_webtoken_failure"  
        | extend lowerConnectionId = tolower(sql_connection_id)
        | project-rename webtoken_event = event
) on lowerConnectionId 
| extend lowerConnectionId = iff(isempty(lowerConnectionId), lowerConnectionId1, lowerConnectionId);
MonLogin
| where event =~ "process_login_finish"
| where error == 18456 and state == 132
| where logical_server_name contains server and database_name contains database
| where TIMESTAMP between (min_time..max_time)
| extend lowerConnectionId = tolower(connection_id)
| join kind = inner (fedauth_data) on lowerConnectionId 
| extend token_validity = token_validity / abs(token_validity)    // -1 for expired, 1 for valid
| summarize count() by bin(TIMESTAMP, 1h), package, token_validity, error_code1
| render timechart
```

**Analysis:**
- `token_validity == -1`: Expired tokens (customer needs to refresh)
- `token_validity == 1`: Valid tokens but other validation failed

**Action:** Refer to AAD/FedAuth TSG for detailed troubleshooting.

---

### State 133 - FedAuth AAD Login JWT System Error

**Package:** sqlserver

**Background:** System-level error during JWT processing (not user error).

**Check fedauth service health:**

```kusto
MonFedAuthTicketService
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where error_state == 133
| where event in ("fedauth_ticket_service_failure", "fedauth_webtoken_failure")
| summarize count() by event, error_code, ClusterName
```

**Action:** If widespread across clusters, potential service issue. Refer to AAD/FedAuth TSG.

---

### State 137 - Deny External Connections On

**Package:** sqlserver

**Background:** This setting is enabled during certain workflow operations (e.g., UpdateSLO, elastic pool resizing).

**Check for active workflows:**

**Action:**
1. Access Sterling CMS Browser
2. Check for active or stuck workflows for the logical server
3. Look for workflows in states: In Progress, Stuck, Failed
4. Common workflow types that trigger this:
   - UpdateSLO operations
   - Elastic pool scaling
   - Database tier changes

**Query to check recent workflow activity:**

```kusto
// Check MonManagement or MonManagementOperations for recent operations
MonManagementOperations
| where TIMESTAMP between (datetime({StartTime}) - 1h .. datetime({EndTime}) + 1h)
| where logical_server_name =~ ''{LogicalServerName}''
| where logical_database_name =~ ''{LogicalDatabaseName}''
| where operation_name has_any ("UpdateSlo", "Resize", "Scale")
| project TIMESTAMP, operation_name, operation_state, operation_id
| order by TIMESTAMP desc
```

**Mitigation:** If workflow is stuck, engage Resource Management team to resolve.

---


## Output to User

- **Error State(s) Detected:** [list states found]
- **Error Classification:** User Error / System Error / Service Issue
- **Error Description:** [provide a brief description of the error]
- **References:**  always suggest related TSGs or documentation for further reading. "https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/connection/login-errors/error-18456-login-failed-for-user"
