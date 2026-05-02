---
name: error-40532-state-150
description: This skill focuses on diagnosing login error 40532 state 150 - VNET Firewall rule rejected the login. This error occurs when a connection attempt is blocked by Virtual Network firewall rules.
---

## Background Information

Error 40532 with state 150 indicates that a Virtual Network (VNET) firewall rule rejected the login attempt. This error occurs when:

- The customer has configured VNET firewall rules for specific subnets
- The connection attempt is coming from a different subnet than the one allowed by the rule
- VNET firewall rules are applied per subnet, not per entire VNET


**Important Note:**
- `vnet_gre_key` and `vnet_subnet_id` are internal implementation identifiers
- Do NOT share these raw values with customers
- Customer-facing message: "You have a VNET Firewall rule for Subnet A, but you are connecting from Subnet B"

## Required Information from Previous Steps

Before using this skill, ensure you have:
- **LogicalServerName**: From user input
- **LogicalDatabaseName**: From user input
- **StartTime** and **EndTime**: From user input
- **kusto-cluster-uri** and **kusto-database**: From "execute-kusto-query" skill

## Step 1: Identify Error Pattern and Connection Sources

Execute the following query to understand which VNETs and subnets are attempting connections:

```kusto
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let servername = '{LogicalServerName}';
let dbname = '{LogicalDatabaseName}';
MonLogin 
| where TIMESTAMP between (StartTime..EndTime)
| where logical_server_name =~ servername
| where database_name =~ dbname
| where error == 40532 and state == 150
| where event == "process_login_finish"
| summarize ErrorCount = count(), 
            min_time = min(TIMESTAMP), 
            max_time = max(TIMESTAMP),
            sample_connection_id = take_any(connection_id)
    by database_name, vnet_gre_key, vnet_subnet_id, package
| order by ErrorCount desc
```

**Output Analysis:**
- **vnet_gre_key**: Internal identifier for the VNET (maps to `vnet_traffic_tag` in CMS)
- **vnet_subnet_id**: Internal identifier for the subnet (maps to `subnet_traffic_tag` in CMS)
- **ErrorCount**: Number of failed connection attempts
- Multiple rows indicate connections from different subnets

**Example Output:**

| database_name | vnet_gre_key | vnet_subnet_id | ErrorCount | min_time | max_time |
|---------------|--------------|----------------|------------|----------|----------|
| master        | 392878998    | 2              | 74         | 2026-01-22 12:03:10 | 2026-01-22 14:29:40 |
| master        | 0            | 0              | 3          | 2026-01-22 12:06:53 | 2026-01-22 13:16:30 |

**Interpretation:**
- `vnet_gre_key = 392878998`: Connections from a specific VNET
- `vnet_subnet_id = 2`: Connections from subnet ID 2 within that VNET
- `vnet_gre_key = 0` and `vnet_subnet_id = 0`: Connections from outside any configured VNET

---

## Step 2: Check VNET Firewall Rules in CMS

** CRITICAL: This requires CMS database access**:
Note: Please notify the user that this query is not to be executed by the agent


Use AdhocCMSQuery tool or Sterling CMS Browser to check configured VNET firewall rules(do not excute this, just show the query here for reference, you can let user know this query):

```sql
SELECT 
    rule_name, 
    vnet_name, 
    subnet_name, 
    vnet_traffic_tag, 
    subnet_traffic_tag,
    is_rule_disabled
FROM vnet_firewall_rules 
WHERE logical_server_name = '{LogicalServerName}'
ORDER BY rule_name;
```

**Expected Output:**

| rule_name | vnet_name | subnet_name | vnet_traffic_tag | subnet_traffic_tag | is_rule_disabled |
|-----------|-----------|-------------|------------------|--------------------|------------------|
| Allow-Subnet1 | MyVNET | Subnet-1 | 392878998 | 1 | 0 |
| Allow-Subnet3 | MyVNET | Subnet-3 | 392878998 | 3 | 0 |

---

## Step 3: Compare MonLogin Data with CMS Configuration

**Cross-reference the data:**

1. **Match VNET**: 
   - `vnet_gre_key` from MonLogin should equal `vnet_traffic_tag` from CMS
   - If they match, the connection is from the correct VNET

2. **Match Subnet**:
   - `vnet_subnet_id` from MonLogin should equal `subnet_traffic_tag` from CMS
   - If they DO NOT match, this is the root cause

**Example Analysis:**

From Step 1 (MonLogin):
- `vnet_gre_key = 392878998`  (matches VNET)
- `vnet_subnet_id = 2`  (does not match any allowed subnet)

From Step 2 (CMS):
- Allowed subnets: `subnet_traffic_tag = 1` and `subnet_traffic_tag = 3`

**Root Cause Confirmed:**
- Customer is connecting from Subnet 2
- Only Subnets 1 and 3 are allowed by firewall rules
- VNET firewall rules are configured per subnet, not per entire VNET

---

## Step 4: Additional Diagnostic Queries

### Query 1: Timeline of Failed Connections

```kusto
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let servername = '{LogicalServerName}';
let dbname = '{LogicalDatabaseName}';
MonLogin 
| where TIMESTAMP between (StartTime..EndTime)
| where logical_server_name =~ servername
| where database_name =~ dbname
| where error == 40532 and state == 150
| where event == "process_login_finish"
| summarize FailedConnections = count() by bin(TIMESTAMP, 5m), vnet_gre_key, vnet_subnet_id
| order by TIMESTAMP asc
| render timechart
```

**Purpose**: Visualize when connection failures occurred and from which subnets

### Query 2: Check for Recent Firewall Rule Changes

**Check CMS for recent modifications:**

Note: Please notify the user that this query is not to be executed by the agent

```sql
-- Check audit logs for VNET firewall rule changes
SELECT 
    operation_time,
    operation_type,
    rule_name,
    vnet_name,
    subnet_name,
    operated_by
FROM vnet_firewall_rules_audit 
WHERE logical_server_name = '{LogicalServerName}'
    AND operation_time >= DATEADD(day, -7, GETUTCDATE())
ORDER BY operation_time DESC;
```

**Look for:**
- Recent rule deletions
- Rule modifications
- Disabled rules

### Query 3: Check for Successful Connections from Same VNET

```kusto
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let servername = '{LogicalServerName}';
let dbname = '{LogicalDatabaseName}';
let ProblematicVNET = 392878998; // Replace with actual vnet_gre_key from Step 1
MonLogin 
| where TIMESTAMP between (StartTime..EndTime)
| where logical_server_name =~ servername
| where database_name =~ dbname
| where vnet_gre_key == ProblematicVNET
| where event == "process_login_finish"
| summarize SuccessfulLogins = countif(is_success == true),
            FailedLogins = countif(is_success == false)
    by vnet_subnet_id
| order by vnet_subnet_id asc
```

**Purpose**: Determine which subnets within the same VNET are successful vs. failing

---

## Root Cause Summary

After completing the investigation, determine the root cause:

**Scenario 1: Customer Configuration Error**
- Customer has VNET firewall rules configured
- Application is connecting from a subnet NOT allowed by the rules
- **Customer Action Required**: Update application to connect from allowed subnet OR add new firewall rule for the subnet

**Scenario 2: Firewall Rule Not Applied/Deleted**
- Customer expects rule to be present but it's missing in CMS
- Rule was recently deleted or modified
- **Customer Action Required**: Recreate or re-enable the firewall rule

**Scenario 3: Rule Configuration Mismatch**
- Rule exists in CMS but with wrong subnet configuration
- **Customer Action Required**: Update firewall rule with correct subnet information

**Scenario 4: Connection from Outside VNET**
- `vnet_gre_key = 0` and `vnet_subnet_id = 0` indicates connection from public IP or different VNET
- **Customer Action Required**: Ensure connection originates from configured VNET

---

## Mitigation Steps

### For Customer Configuration Issues:

1. **Add Missing Firewall Rule:**
   - Guide customer to Azure Portal  SQL Server  Firewalls and virtual networks
   - Add new VNET firewall rule for the subnet attempting to connect
   - Allow 5-10 minutes for rule propagation

2. **Update Application Configuration:**
   - Ensure application is deployed in/connected to the correct subnet
   - Verify VNET peering is configured if connecting across VNETs

3. **Verify Service Endpoint:**
   - Ensure subnet has `Microsoft.Sql` service endpoint enabled
   - Check: Azure Portal  Virtual Network  Subnets  Service Endpoints

### Validation Query (Run After Changes):

```kusto
let servername = '{LogicalServerName}';
let dbname = '{LogicalDatabaseName}';
MonLogin 
| where TIMESTAMP > ago(10m)
| where logical_server_name =~ servername
| where database_name =~ dbname
| where event == "process_login_finish"
| summarize SuccessCount = countif(is_success == true), 
            FailureCount = countif(is_success == false) 
    by vnet_gre_key, vnet_subnet_id
```

---

## Important Reminders

1. **VNET Firewall Rules are Per-Subnet:**
   - Rules apply to specific subnets within a VNET, not the entire VNET
   - Each subnet requiring access must have its own rule

2. **Internal Identifiers:**
   - Do NOT share `vnet_gre_key` or `vnet_subnet_id` values with customers
   - These are internal Azure implementation details
   - Use human-readable names from CMS (vnet_name, subnet_name)

3. **Rule Propagation:**
   - Firewall rule changes can take 5-10 minutes to propagate
   - Advise customer to wait before retrying

4. **Service Endpoint Requirement:**
   - Subnet must have `Microsoft.Sql` service endpoint enabled
   - This is a prerequisite for VNET firewall rules

---

## Output to User

1. **Error Details:**
- **The meaning of the Error Message**: "Cannot open server requested by the login. The login failed"
- **Finding about the error**: VNET Firewall rule rejected the connection

2. **Related TSG Link:**
https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/connection/login-errors/error-40532-cannot-open-server-login-failed
