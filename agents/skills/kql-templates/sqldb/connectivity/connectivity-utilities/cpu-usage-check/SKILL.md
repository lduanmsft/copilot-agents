---
name: cpu-usage-check
description: This Skill helps to check the CPU usage of DB nodes. It can help to identify if there is any CPU usage issue on the node which causes connectivity problem.
---

##Query
// GW1207
// Check DB node CPU usuage. The nodes are Virtual Machines, please emit a table of the CPU usage, alert user if the CPU usuage is higher than 70 percent.
// The main idea of the following kusto query is to find the  VirtualMachineUniqueId and MDM account based on compute cluster and execute resets based on time window. This mapping information is only in kusto cluster "sqlstage.kusto.windows.net" regardless of the SQL region.
//
let startTime = datetime({StartTime});
let endTime = datetime({EndTime});
let ClusterNameVar = '{TenantRingName}';
let NodeNameVar = '{DBNodeName}';
let _tempID=cluster("sqlstage.kusto.windows.net").database("sqlazure1").MonSQLNodeSnapshot
| where ClusterName  == ClusterNameVar and NodeName  =~ NodeNameVar
| summarize max(IngestionTime) by VirtualMachineUniqueId, ComputeMDM;
let shoeboxAccount= toscalar(_tempID| distinct ComputeMDM) ;
let vmId= toscalar(_tempID| distinct VirtualMachineUniqueId);
let query_vmcachediops = strcat(@"metricNamespace('Shoebox').metric('VM Cached IOPS Consumed Percentage').dimensions('ResourceId').samplingTypes('Average','Max') | where ResourceId == '", vmId, "'");
let query_vmuncachediops = strcat(@"metricNamespace('Shoebox').metric('VM UnCached IOPS Consumed Percentage').dimensions('ResourceId').samplingTypes('Average','Max') | where ResourceId == '", vmId, "'");
let query_vmcachedband = strcat(@"metricNamespace('Shoebox').metric('VM Cached Bandwidth Consumed Percentage').dimensions('ResourceId').samplingTypes('Average','Max') | where ResourceId == '", vmId, "'");
let query_vmuncachedband = strcat(@"metricNamespace('Shoebox').metric('VM UnCached Bandwidth Consumed Percentage').dimensions('ResourceId').samplingTypes('Average','Max') | where ResourceId == '", vmId, "'");
let query_cpu = strcat(@"metricNamespace('Shoebox').metric('Percentage CPU').dimensions('ResourceId').samplingTypes('Average','Max') | where ResourceId == '", vmId, "'");
evaluate geneva_metrics_request(shoeboxAccount, query_cpu, startTime, endTime)
| project TimestampUtc, AvgCPU = column_ifexists("Average",0), MaxCPU = column_ifexists("Max",0)
| where isnotempty(TimestampUtc)
|project-reorder  TimestampUtc, AvgCPU, MaxCPU
```