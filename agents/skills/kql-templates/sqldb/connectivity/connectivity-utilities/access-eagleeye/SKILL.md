---
name: access-eagleeye
description: eagleai is a helpful tool to analyze networking problems. This skill would query eagleai MCP and respond with EagleEye analysis to help user get aware of potential networking issues between source and destination.
---


## eagleai MCP
The eagleai MCP is configured in .vscode/mcp.json

## Format to engage eagleai MCP

    - Source: Can be Source VirtualMachineUniqueId (preferred), VMSS resource URI, public IP address. Source is usally a Gateway Node (VMSS instance) or the Gateway VMSS resource URI.
    - Destination: Can be Destination VirtualMachineUniqueId (preferred), VMSS resource URI, public IP address. Destination is usually a SQL DB Node (VMSS instance) or the SQL Node VMSS resource URI.
    - StartTime: issue start time
    - EndTime: issue end time
    - CustomerProblemCategory: "short" or "long", if time window is less then one hour, use "short", otherwise use "long".

Sample input to engage eagleai MCP:
```
#eagleai  Check Connectivity issues between source "/subscriptions/12475289-e754-4cb5-9294-cccafdf764c1/resourceGroups/wasd-prod-ukwest1-a-cr10/providers/Microsoft.Compute/virtualMachineScaleSets/GW" to destination "b8a58d46-bba6-4af0-8578-3f24f21c52ab" for the given time duration 2026-03-14 20:35 and 2026-03-14 21:35
```

If source and destination or others are unclear according to the context, you may prompt the user to provide the information manually.

## How to get source and destination
- If the input is a single VM, refer the skill "determine-sql-node".
- If the input is a Cluster, which can either be a Connectivity Ring or a Tenant Ring, refer the following sample kusto query to get the whole VMSS resource ID:

```
let _ClusterName="cr1.austriaeast1-a.control.database.windows.net";
// the _ClusterName can also be a Tenant Ring, such as "tr16316.southcentralus1-a.worker.database.windows.net"
// the Kusto cluster sqlstage.kusto.windows.net is fixed
cluster('sqlstage.kusto.windows.net').database('sqlazure1').MonSQLTenantSnapshot
| where ClusterName =~ _ClusterName
| extend VMSS_RID= iff(ClusterName startswith "cr", strcat("/subscriptions/",SubscriptionId,"/resourceGroups/", RingName, "/providers/Microsoft.Compute/virtualMachineScaleSets/GW"), strcat("/subscriptions/",SubscriptionId,"/resourceGroups/", RingName, "/providers/Microsoft.Compute/virtualMachineScaleSets/DB") )
| summarize arg_max(IngestionTime,*)
| project EagleAI_Input= VMSS_RID
```

- If a user prefers to define the eagleai input manually, prompt them that they can input "VM container ID, VirtualMachineUniqueId(prefered), VMSS resource URI, public IP address"


## Output
1. When this skill is hit and query has been sent to the eagleai MCP, immediately notify the user that the query has been submitted and is being processed and may take about 5 minutes to complete, please keep session active and wait for the results.

2. Output the potential networking issues suggested by eagleai MCP based on the analysis of the connectivity between the source and the destination for the given time duration.
