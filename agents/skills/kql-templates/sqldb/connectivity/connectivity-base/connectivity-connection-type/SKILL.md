---
name: connectivity-connection-type
description: This skill helps determine the Connection Policy used for Azure SQL connections during a specific time window, and whether the actual connection type used (Proxy vs Redirect) matches the expected behavior based on the documented rules for Connection Policy for public, service, and private endpoints. 
---

## Required information
To use this skill, you will need the following information:
- Logical Server Name
- Logical Database Name (optional but preferred, if not provided, the skill will analyze at the server level instead of the database level)
- Time window to analyze (start time and end time)

## Background information
Azure SQL server can have three connection policies:
Proxy, Redirect, and Default.
The intended behavior for Default is: 
- For Public connections, Default will use Proxy for connections coming from outside of Azure, and Redirect for connections from within Azure. 
- For Private connections, Default will use Proxy always.

## Workflow
### 1. Determine source connection details

Use the following query to find what connection types were used for the given logical server name/database name.
```
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ "process_login_finish"
| where package =~'xdbgateway'
| where proxy_override != 'eProxyOverrideBehaviorInvalid' and isnotempty( proxy_override) //Failure during pre-login that results in no connection policy details provided
| summarize min(originalEventTimestamp),max(originalEventTimestamp), count() by  proxy_override, 
result, 
is_azure_ip,  
is_vnet_address, 
is_vnet_private_access_address, redirection_map_id, 
validated_driver_name_and_version, vnet_gre_key, vnet_subnet_id, vnet_link_identifier
| sort by min_originalEventTimestamp
```

Note: in the kusto query, the variables are:
- {StartTime}: the start of the time window to analyze
- {EndTime}: the end of the time window to analyze
- {LogicalServerName}: the logical server name of the Azure SQL instance to analyze
- {LogicalDatabaseName}: the logical database name of the Azure SQL instance to analyze. If you want to analyze at the server level instead of the database level, you can remove the "and database_name =~ '{LogicalDatabaseName}'" line from the query.

### 2.  Analyze the results

Analyze the Kusto results using the following steps:

#### 2.1 Analyze the Connection Policy set on the server
- If proxy_override is eProxyOverrideBehaviorForceProxy, the Connection Policy is set to Proxy.
- If proxy_override is eProxyOverrideBehaviorForceRedirect, the Connection Policy is set to Redirect.
- If proxy_override is eProxyOverrideBehaviorDefault, the Connection Policy is set to Default.

If there are multiple valid proxy_override results, that means the server's connection policy was changed.

#### 2.2 Analyze the connection privacy type

- If is_vnet_private_access_address is true, the connection is using a Private Endpoint.
- If is_vnet_private_access_address is false and is_vnet_address is false, the connection is using Public endpoint.
- if is_vnet_private_access_address is false and is_vnet_address is true, the connection is using a Service endpoint. Service endpoints use a subcategory of Public Endpoint. 
- If is_azure_ip is true, the connection is considered to be from within Azure. If it is false, it is considered to be from outside of Azure. This distinction only matters for Public Endpoint.

An alternative way to distinguish is:
- If vnet_gre_key is 0, it is using a public endpoint
- If vnet_gre_key is greater than 0 and vnet_link_identifier is 0, it is using a service endpoint
- If vnet_gre_key is greater than 0 and vnet_link_identifier is greater than 0, it is using a private endpoint

#### 2.3 Analyze if the connection type used matches the policy

- If result is e_crContinueSameState, the actual connection is using Proxy.
- If result is e_crContinue, the actual connection is using Redirect.

| Actual Connection Type | Connection Policy | Endpoint Privacy | Cause |
|------------------------|-------------------|------------------|-------|
| Proxy | Proxy | ANY | Working as intended |
| Proxy | Default | Public - Not Azure | Working as intended |
| Proxy | Default | Public - Within Azure | Likely an outdated third party driver |
| Proxy | Default | Private | Working as intended |
| Proxy | Redirect | Public | Likely an outdated third party driver |
| Proxy | Redirect | Private | The driver does not support private redirect. (Refer to Note 2 underneath) |
| Redirect | Redirect | ANY | Working as intended |
| Redirect | Default | Public | Working as intended if is_azure_ip column is true |
| Redirect | Default | Private | Server has a redirection map and is not behaving according to documented rules. (Refer to Note 1 underneath) |

## Notes:
### 1. Why is there a Redirect connection if the connection policy is Default and the connection is using a Private endpoint?

If a private connection has a Default connection policy but is still using Redirect as the actual connection type used, more than likely it means that the redirection_map_id column is filled out.
This can occur for certain customers who either had PG apply a redirection map ID directly, such as those who did private preview of Private Endpoint redirect.
Or this can be a customer in the first few regions that received the Private Redirect feature, which had a different behavior for Default that led to most private endpoints using Redirect under Default. Although Default was later changed to use Proxy for private endpoint, customers who already received a redirection map id did not have this automatically changed. 

If this is an issue and there is a need to mitigate, asking the customer to change the connection policy to Proxy or Redirect, and then change it back to Default, will allow Default to work as expected.

Do not show any warnings or observations about this unless there is a clear indication that the a redirection_map_id was used, with a result of e_crContinue when proxy_override was eProxyOverrideBehaviorDefault.

### 2. What drivers support redirect?

Most modern drivers support public redirect. However, legacy drivers might not support any form of redirect, such as ODBC 8, ODBC 11, OLEDB 8, and JDBC 4.

For private redirect, the SQL Gateway returns an ENVCHANGE token to provide new routing information to the client, allowing it to connect directly to the SQL instance on the backend node. For public redirect, the new routing address is provided in the format `<appname>.<tr#>.<region>1-a.worker.database.windows.net`. However, for private endpoint logins, the format is `<servername>.database.windows.net\<appname>`. In this case, the client must recognize that `<appname>` refers to a named instance and should include this named instance when connecting to the backend.

Drivers that do not support private redirect will either default to Proxy or the connection will fail the DNS call and the connection to the redirect node will not be attempted at all.

Redirect support is included in ODBC, OLE DB, .NET SqlClient Data Provider, Core .NET SqlClient Data Provider, and JDBC (version 9.4 or above) drivers. Connections originating from all other drivers are proxied.

https://learn.microsoft.com/en-us/azure/azure-sql/database/private-endpoint-overview?view=azuresql&source=recommendations#use-redirect-connection-policy-with-private-endpoints

The Gateway maintains a list of drivers that support named instances for private endpoint redirect. If the driver and version is not on the list, the connection will be proxied even if the connection policy is Redirect or Default with Private Endpoint.


### 3. Other reasons why a redirect connection was not established if the driver is up to date and should support redirect:
- If the connection is going through a NAT, web proxy (Zscaler), or SSL Inspection device that does not support TLS redirection.



## Output
Provide the following table to the user.
Connection Endpoint Type (Public endpoint within Azure, Public endpoint outside Azure, Service endpoint, Private Endpoint), Connection Policy (Proxy vs Redirect vs Default), Actual Connection Type (Proxy vs Redirect), Driver Name and Version, Redirection Map ID if applicable, VNET and Subnet if applicable, Datetime range (yyyy-mm-dd hh:mm:ss, min - max), Connection Count, and a "Matching" check box for whether the connection policy and actual connection type are matching (If Connection Policy is Proxy and Connection Type is Proxy, use a green checkbox; If Connection Policy is Redirect and connection type is redirect, use a green checkbox; If connection type is Default, use a green checkbox if the actual type used matches the documented behavior in the Background section. Use a red flag for all other scenarios), and an "Reason for the Mismatch" column that explains why it is using Proxy such as "Default connection policy with Private Endpoint" or "Check driver support" or why it is using Redirect when the documented intended behavior is supposed to be Proxy such as "Private endpoint has a redirect map".

This is a sample output of this table:
|Connection Endpoint Type|Connection Policy|Actual Connection Type|Driver Name and Version|Redirection Map ID|VNET and Subnet|Datetime Range (yyyy-mm-dd hh:mm:ss)|Connection Count|Matching|Reason for the Mismatch
|------------------------|-------------------|----------------------|-----------------------|------------------|----------------|-----------------------------------|----------------|--------|-----------------------|
|Private Endpoint|Redirect|Redirect|Framework Microsoft SqlClient Data Provider 6.13|10F2F82B-EE73-48A8-AF54-24F71F11B8D6|GRE: 628214071, Subnet: 1, Link: 620757144|2026-03-18 18:33:43 - 2026-03-18 18:34:06|4|✅|-|
|Private Endpoint|Default|Proxy|Framework Microsoft SqlClient Data Provider 6.13|-|GRE: 628214071, Subnet: 1, Link: 620757144|2026-03-18 18:25:41 - 2026-03-18 18:26:13|5|✅|-|
|Service Endpoint|Default|Redirect|Framework Microsoft SqlClient Data Provider 6.13|-|GRE: 628214071, Subnet: 1|2026-03-18 18:08:54 - 2026-03-18 18:17:39|19|✅|-|
|Public Endpoint within Azure|Default|Redirect|Framework Microsoft SqlClient Data Provider 6.13|-|-|2026-03-18 17:59:46 - 2026-03-18 18:02:17|8|✅|-|
|Public Endpoint outside Azure|Proxy|Proxy|Framework Microsoft SqlClient Data Provider 5.15|-|-|2026-03-18 16:36:37 - 2026-03-18 16:36:53|3|✅|-|
|Public Endpoint within Azure|Proxy|Proxy|Framework Microsoft SqlClient Data Provider 5.15|-|-|2026-03-18 16:33:35 - 2026-03-18 16:33:38|3|✅|-|
|Private Endpoint|Redirect|Proxy|Unrecognized Driver(go-mssqldb 6.0)|72CEFF81-BC3B-473D-9EDC-9F84FCDADF81|GRE: 443285094, Subnet: 21, Link: 16792378|2026-03-24 00:00:11 - 2026-03-24 23:59:41|2,880|🚩|Driver does not support private redirect|


Along with the following analyses undernearth:
- Did the connection policy change during the time window?
- If the above table shows a mismatch, elaborate further on mitigation steps if any, and provide documentation links for reference.
