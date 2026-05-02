---
name: sql-connectivity-livesite-dashboard
description: SQL Connectivity Livesite Dashboard is a collection of dashboards built in Azure Data Explorer. With correct input, it helps engineer check the issue in depth. This skill helps to generate a dashboard link and refer to engineer.
---

## Important Pages for SQL Connectivity Livesite Dashboard

### Gateway health dashboard
Sample Dashboard URL:
https://dataexplorer.azure.com/dashboards/ff00559d-35c6-41c1-93eb-43b67381a3cf?p-_startTime=2026-01-23T18-20-00Z&p-_endTime=2026-01-23T21-20-00Z&p-RegionFqdn=v-australiacentral2-a&p-ClusterNameVar=v-cr9.australiacentral2-a.control.database.windows.net&p-NodeRoleVar=all&p-NodeNameVar=v-_GW_1#5e91c7d7-e156-45bf-85bf-23332f6c490c

In this sample, it displays the Gateway health dashboard with the following variables:
RegionFqdn: australiacentral2-a 
Connectivity Ring: cr9.australiacentral2-a.control.database.windows.net, 
Gateway node: _GW_1,
NodeRole: All, 
Issue start time: 2026-01-23T18-20-00, 
Issue end time: 2026-01-23T21-20-00 

Note:
-Time Stamp is in UTC
-NodeRole is always All
-RegionFqdn is a part of the Ring/Cluster region string, example:
cr11.uksouth1-a.control.database.windows.net has RegionFqdn uksouth1-a
cr11.useuapcentral1-a.control.database.windows.net has RegionFqdn useuapcentral1-a
The list of all the RegionFqdn is kusto:
```
cluster('sqlstage.kusto.windows.net').database('sqlazure1').MonSQLTenantSnapshot
| where IngestionTime > ago (10d)
| distinct Region
| extend RegionName = trim_start("wasd-prod-", Region)
```

### XDBHost dashboard
Sample Dashboard URL:
https://dataexplorer.azure.com/dashboards/ff00559d-35c6-41c1-93eb-43b67381a3cf?p-_startTime=2026-01-23T18-20-00Z&p-_endTime=2026-01-23T21-20-00Z&p-RegionFqdn=v-eastus2-a&p-ClusterNameVar=v-tr43583.eastus2-a.worker.database.windows.net&p-NodeRoleVar=all&p-NodeNameVar=v-_DB_51&p-SqlInstances=v-a151c2d79ec9&p-_logicalServerName=all#90bdce43-0daf-4aec-ad80-f2cdb0b236ba

In this sample, it displays the XDBHost dashboard with the following variables:
RegionFqdn: eastus2-a (must have),
Tenant Ring: tr43583.eastus2-a.worker.database.windows.net (must have), 
DB node: _DB_51 (must have),
NodeRole: All (must have),
SqlInstances: a151c2d79ec9 (best to have. If there is no context to retrieve it, you can put in "all")
logicalServerName: usually put in "all"
Issue start time: 2026-01-23T18-20-00 (must have), 
Issue end time: 2026-01-23T21-20-00 (must have)

Note: SqlInstances can be retrieved from the kusto cluster where the ring resides.
```
MonLogin 
| where PreciseTimeStamp between (StartTime .. EndTime)
| where ClusterName =~ 'xxx.xxx.worker.database.windows.net' 
| where event =~ 'process_login_finish' and AppName =~ 'worker'
| where logical_server_name =~ "xxx" and database_name =~ "xxx"
| summarize by  NodeName, ClusterName, instance_name, logical_server_name, database_name
```
Because we have the logical server name and database name in the context, we are ok to map logical server and DB node to the instance_name. Please make sure the DB node you put into the URL must have the instance name mapped.
The SqlInstances is the prefix of the instance name, example we take a151c2d79ec9 from instance_name "a151c2d79ec9.tr43583.eastus2-a.worker.database.windows.net"


### VM Node dashboard
Sample Dashboard URL:
https://dataexplorer.azure.com/dashboards/ff00559d-35c6-41c1-93eb-43b67381a3cf?p-_startTime=2026-01-26T00-00-00Z&p-_endTime=2026-01-27T23-59-59Z&p-RegionFqdn=v-switzerlandnorth1-a&p-ClusterNameVar=v-tr2594.switzerlandnorth1-a.worker.database.windows.net&p-NodeRoleVar=all&p-NodeNameVar=v-_DB_0&p-SqlInstances=all#8214d7e9-7ff1-4313-930a-7bb0807b73fa

In this sample, it displays the VM Node dashboard  with the following variables:
RegionFqdn: switzerlandnorth1-a (must have),
Ring: tr2594.switzerlandnorth1-a.worker.database.windows.net (must have), 
VM node: _DB_0 (must have),
NodeRole: All (must have),
SqlInstances: usually put in "all"
Issue start time: 2026-01-23T18-20-00 (must have), 
Issue end time: 2026-01-23T21-20-00 (must have)

## What to provide
1. Replace variables under sample dashboard links
2. Generate Link according to the analysis / context
3. Share the link to user
