---
name: determine-sql-node
description: SQL Node includes Gateway Nodes, MN Nodes and DB nodes are Virtual Machines, this skill would help to map SQL Node to the VM metadata including ContainerId, VirtualMachineUniqueId and etc. The VM infomation is helpful to further VM analisys, network analisys, storage connectivity analisys.
---

# Kusto Table has the mapping info

## Sample Kusto Query
```
let _clustername= "cr2.austriaeast1-a.control.database.windows.net";
let _nodename= "_GW_29";
cluster('sqlstage.kusto.windows.net').database('sqlazure1').MonSQLNodeSnapshot
| where ClusterName =~ _clustername and NodeName =~ _nodename
| summarize min(IngestionTime), max(IngestionTime) by VirtualMachineUniqueId, ContainerId,NodeId,ComputeMDM,VfpAccount,OSDiskStorageAccount,OSDiskStorageStamp
```

Note:
1. The kusto cluster sqlstage.kusto.windows.net is fixed, even SQL ClusterName is in different regions
2. _clustername and _nodename are variables inputs
3. The MonSQLNodeSnapshot updates from time to time. For example, if the "IngestionTime" filed shows "2026-01-12 21:48:00.0413127", this means the snapshot took on the timestamp. If the problem has a time window, try to find the closet record during min_IngestionTime and max_IngestionTime.
4. The important output fields are:
VirtualMachineUniqueId,
ContainerId,
NodeId,
ComputeMDM,
VfpAccount,
OSDiskStorageAccount,
OSDiskStorageStamp

These output would be helpful to further VM analisys, network analisys, eagleai analysis, storage connectivity analisys
