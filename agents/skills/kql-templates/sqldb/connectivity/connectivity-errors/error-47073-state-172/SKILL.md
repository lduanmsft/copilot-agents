---
name: error-47073-state-172
description: This skill focuses on diagnosing login error 47073 state 172 - Public Network Access Denied. This error occurs when a connection was blocked because Deny Public Network Access is enabled on the Azure SQL logical server.
---
## Background Information
Error 47073 with state 172 indicates that a Deny Public Network Access setting is enabled on SQL Logical Server Level. In this mode, only Private Link (private endpoint) connections are allowed. This error occurs when:
- Connection attempts coming in via the public endpoint.
- Connection attempts coming in via Service Endpoint Tunneling.
- Customer has Private Endpoint configured but traffic is not going through Private Link path due to misconfiguration on DNS or routing.
- Customer may see the following error message in their application:
Error 47073, an instance-specific error occurred while establishing a connection to SQL Server.

**Important Note:**
- Customer-facing message: "The public network interface on this server is not accessible. To connect to this server, use the Private Endpoint from inside your virtual network."

## Required Information from Previous Steps

Before using this skill, ensure you have:
- **LogicalServerName**: From user input or IcM
- **LogicalDatabaseName**: From user input or IcM (if applicable)
- **StartTime** and **EndTime**: From user input or IcM to define the analysis window
- **kusto-cluster-uri** and **kusto-database**: From "execute-kusto-query" skill

## Critical Telemetry Interpretation: Gateway vs Database Nodes

> ⚠️ **IMPORTANT**: MonLogin logs events at TWO stages for each connection attempt. Misinterpreting this can lead to incorrect RCA conclusions.

### Two-Stage Login Process

| Stage | NodeRole | What Happens | is_success Meaning |
|-------|----------|--------------|--------------------|
| 1. Gateway | GW | Firewall check, initial routing | Passed firewall (NOT final login result) |
| 2. Database | DB | Authentication, DPNA enforcement | **Actual login result** |

### Why This Matters for Error 47073

When DPNA is enabled, you may observe:
- **Gateway (GW)**: Shows SUCCESS for public connections (firewall passed)
- **Database (DB)**: Shows FAILURE with error 47073 state 172 (DPNA blocked)

This creates **two events per blocked connection** - one success at GW, one failure at DB. Do NOT interpret GW successes as evidence that public connections are working.

### Correct Analysis Approach

**Always filter on `NodeRole = 'DB'`** when analyzing error 47073 to see actual login outcomes:

```kusto
MonLogin
| where NodeRole == 'DB'  // Critical: Only look at Database-level results
| where is_success == false and error == 47073 and state == 172
```

**Red Flags for Misinterpretation:**
- Seeing ~50/50 success/fail ratio from the same IP addresses
- "Successful" connections with empty `session_id` values
- `is_relogin = null` on success events vs `is_relogin = false` on failures


## Step 1: Identify Error Pattern, and verify if connections are coming from Public Endpoint or Service Endpoint Tunneling
Execute the following query to understand whether public endpoints or service endpoint tunneling are attempting connections from:
```kusto
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let TargetServer = '{LogicalServerName}';
MonLogin
      | where originalEventTimestamp between (StartTime .. EndTime)
      | where logical_server_name =~ TargetServer
      | where NodeRole == 'DB'  // Important: Only Database-level events show actual DPNA enforcement
      | where event == "process_login_finish" and is_success == false
      | where error == 47073 and state == 172
      | summarize ErrorCount = count() by is_vnet_address, is_vnet_private_access_address, logical_server_name, database_name
      | order by ErrorCount desc
```
**Output Analysis:**
- **is_vnet_address**: Identify whether the connection attempt is coming from a VNet (true) or public endpoint (false).
- **is_vnet_private_access_address**: This field indicates whether it's a Private Link connection (true) or Service Endpoint Tunneling (false).
- **ErrorCount**: Number of failed connection attempts

**Example Output:**

| is_vnet_address | is_vnet_private_access_address | logical_server_name	 | database_name | ErrorCount | 
|------|-------|-------------------------------|----------------|----|
| false | false | dataomo |database_omo |258131|     

**Interpretation:**
- `is_vnet_address = false`: Connections are from public, not from a specific VNet
- `is_vnet_private_access_address = false`: Connections are not coming from Private Link.

## Step 2: Check Public Endpoint/Private Endpoint Setting in MonConnectivityFeatureSnapshot

Execute the following query to check the Public endpoint/Private endpoint setting in MonConnectivityFeatureSnapshot:
```kusto
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let TargetServer = '{LogicalServerName}';
MonConnectivityFeatureSnapshot
 | where logical_server_name =~ TargetServer
 | order by TIMESTAMP desc
 | summarize arg_max(TIMESTAMP, logical_server_name, proxy_override_value, public_data_endpoint_enabled, enforce_outbound_firewall_rules, minimal_tls_version, private_endpoint_count, outbound_firewall_rule_count
 , minimal_tls_version_name = case( minimal_tls_version == 769, 'TLS 1.0', minimal_tls_version == 770, 'TLS 1.1', minimal_tls_version == 771, 'TLS 1.2', '-' ) )
 | project LogicalServerName = logical_server_name, PublicDataEndpointEnabled = public_data_endpoint_enabled, EnforceOutboundFirewallRules = enforce_outbound_firewall_rules, PrivateEndpointCount = private_endpoint_count, OutboundFirewallRuleCount = outbound_firewall_rule_count
```

**Example Output:**
| LogicalServerName | PublicDataEndpointEnabled | EnforceOutboundFirewallRules	 | PrivateEndpointCount | OutboundFirewallRuleCount | 
|------|-------|-------------------------------|----------------|----|
| dataomo | 0 | 0 | 0 | 0 |   

**Interpretation:**
- `PublicDataEndpointEnabled = 0`: No Service Endpoint Tunneling or Public Endpoint connection is allowed, only Private Link connection is allowed.
- `PrivateEndpointCount = 0`: No Private Endpoint is configured.


## Step 3: Compare MonLogin Data with MonConnectivityFeatureSnapshot Configuration
**Example Analysis:**
1. if PublicDataEndpointEnabled = 0 and is_vnet_address = false, then the error is expected. In this case, we can guide customer to enable Public Network Access.

2. if PublicDataEndpointEnabled = 0 and is_vnet_address = true and is_vnet_private_access_address = false, then the error is caused by customer's connection attempt from service endpoint tunneling. In this case, we can guide customer to enable Public Network Access and configure the right VNet address range for service endpoint tunneling.

3. if PrivateEndpointCount > 0 and is_vnet_private_access_address = true, then further investigation is needed since the connection should be going via Private Link. We need to check customer's DNS and routing configuration to make sure the traffic can go via the right Private Link path.

## Step 4: Verify if Issue is intermittent from the same peer_address
To verify if the issue is intermittent from the same peer_address, we can run the following query to check the connection attempts and failures by peer_address and connection type (Public Endpoint, Service Endpoint Tunneling, Private Link):

> ⚠️ **Critical**: This query filters on `NodeRole == 'DB'` to avoid double-counting events (GW and DB both log each connection). Without this filter, you may see inflated success counts from Gateway-level events that don't reflect actual login outcomes.

```kusto
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let TargetServer = '{LogicalServerName}';
MonLogin
| where originalEventTimestamp between (StartTime .. EndTime)
| where logical_server_name =~ TargetServer
| where NodeRole == 'DB'  // Critical: Avoid double-counting GW + DB events
| where event == "process_login_finish"
| extend connLoginType =
    iff(is_vnet_private_access_address == true, "PrivateLink",
        iff(is_vnet_address == true, "ServiceEndpoint", "PublicEndpoint"))
| summarize
    Total = count(),
    Fail = countif(is_success == false),
    DpnaFail = countif(is_success == false and error == 47073 and state == 172)
  by peer_address, connLoginType, logical_server_name
  | where Total != Fail
  | order by DpnaFail desc, Fail desc, Total, logical_server_name desc
```
**Example Output:**
| peer_address | connLoginType | logical_server_name | Total | Fail | DpnaFail |
|------|-------|-------------------------------|----------------|----|----||
| 210.3.7.X | PublicEndpoint | qf-sql-clients-dev-ea| 25280 | 25280 | 25280 |

**Example Analysis:**
If the number of failures observed from a specific peer_address doesn't equal to Total login attempts, then it indicates intermittent connectivity issues. In this case we can check the Firewall, virtual network rules and private endpoints configuration (depends on the connection type), and make sure the settings are correct and DNS resolution is working as expected.

> **Note**: If you see a ~50/50 success/fail ratio from the same public IP AND you did NOT filter on `NodeRole == 'DB'`, this is likely due to double-counting GW + DB events. Re-run with the NodeRole filter to get accurate counts.


## Root Cause Summary
After completing the investigation, determine the root cause based on **where connections are originating from**:
### Scenario 1: Connections from Public IP Addresses
**Telemetry pattern:** `is_vnet_address = false` AND `is_vnet_private_access_address = false`

- Customer has public network access disabled (`PublicDataEndpointEnabled = 0`).
- Application is connecting from **public internet IP addresses**.
- **Customer Action Required**: Enable public network access on this Logical Server and configure firewall rules to allow the client IP address(es).

> ⚠️ **Important**: Do NOT recommend Private Endpoints for this scenario. Private Endpoints are designed for connections originating from within a Virtual Network using private IP addresses. Since the customer is connecting from public addresses, they need to enable public network access and configure IP firewall rules.

### Scenario 2: Connections from VNet via Service Endpoint Tunneling
**Telemetry pattern:** `is_vnet_address = true` AND `is_vnet_private_access_address = false`

- Customer has public network access disabled (`PublicDataEndpointEnabled = 0`).
- Application is connecting from a VNet using **Service Endpoint Tunneling**.
- **Customer Action Required**: Enable public network access on this Logical Server and configure the correct VNet/subnet rules for service endpoint tunneling.

### Scenario 3: Private Endpoint Not Created (VNet customers wanting Private Link)
**Telemetry pattern:** `is_vnet_address = true` AND customer explicitly wants Private Link connectivity

- Customer expects traffic to go through Private Link but no Private Endpoint is configured (`PrivateEndpointCount = 0`).
- **Customer Action Required**: Create a Private Endpoint for the Logical Server within their VNet.

> **Note**: Only recommend Private Endpoints when the customer is connecting from within a VNet AND explicitly wants private connectivity.

### Scenario 4: Private Endpoint Misconfiguration (DNS/Routing)
**Telemetry pattern:** `PrivateEndpointCount > 0` AND `is_vnet_private_access_address = false`

- Private Endpoint is configured but connections are not going through Private Link path.
- Likely caused by DNS or routing misconfiguration.
- **Customer Action Required**: Verify DNS resolves to private IP, check routing tables, verify VNet peering if applicable.

### Scenario 5: Azure Service Traffic Bypass (No Customer Action Required)
**Telemetry pattern:** `is_vnet_address = false` AND `is_vnet_private_access_address = false` AND `is_success = true` WHILE `PublicDataEndpointEnabled = 0`

> ⚠️ **Important Telemetry Interpretation Note**: When analyzing MonLogin data, you may observe **successful connections** flagged as `is_vnet_address=false AND is_vnet_private_access_address=false` even though DPNA is enabled (`PublicDataEndpointEnabled = 0`). This is NOT a contradiction.

**These are Azure service connections that bypass DPNA by design:**

| Azure Service | Purpose |
|--------------|---------|
| Azure Backup Service | System-level backup operations via Azure backbone |
| Geo-Replication | Azure-to-Azure replication traffic |
| Azure Management Plane | Portal, Resource Manager, health checks |
| Azure Monitor/Diagnostics | Telemetry collection agents |
| Azure Data Factory | Data integration service connections |

**Key Points:**
- These connections use Azure backbone networking and are NOT customer public internet traffic
- The `is_vnet_address` and `is_vnet_private_access_address` flags do NOT distinguish between actual public internet connections and Azure service connections
- Both may appear as `is_vnet_address=false`, but only **customer public internet traffic** is blocked by DPNA
- **No Customer Action Required** - this is expected behavior
- In RCA reports, do NOT include these connections as evidence of DPNA bypass issues

**How to Identify Azure Service Traffic:**
- Successful connections with non-VNet flags while DPNA is enabled
- Connection patterns are consistent throughout the analysis period (not clustered before a configuration change)
- IP addresses often belong to Azure datacenter ranges (e.g., `20.x.x.x`, `40.x.x.x`, `52.x.x.x`)

### Recommendation Decision Matrix

| is_vnet_address | is_vnet_private_access_address | Recommended Action |
|-----------------|-------------------------------|-------------------|
| false | false | Enable Public Network Access + Configure IP Firewall Rules |
| true | false | Enable Public Network Access + Configure VNet Rules (Service Endpoints) |
| true | true (but failing) | Check DNS/Routing for Private Endpoint |

## Expected Output
1. Configuration on this Logical Server, it has public network access enabled or not, and whether it has Private Endpoint configured.
2. Rejected connection attempts are from public endpoint or service endpoint tunneling or private link.
3. Whether the issue is intermittent from the same peer_address, and whether customer has multiple connection methods.
4. **Check for Azure service traffic**: If successful connections with `is_vnet_address=false` are observed while DPNA is enabled, verify if these are Azure service connections (consistent patterns, Azure IP ranges) - these are expected and require no customer action.
5. Root cause summary based on connection source (use Recommendation Decision Matrix above).
6. Customer action required - **ensure recommendations match where connections originate from**:
   - Public IP connections → Enable Public Network Access + IP Firewall (NOT Private Endpoints)
   - VNet Service Endpoint connections → Enable Public Network Access + VNet Rules
   - VNet Private Link connections → Configure/Fix Private Endpoint + DNS
   - Azure Service Traffic → No action required (expected behavior)
