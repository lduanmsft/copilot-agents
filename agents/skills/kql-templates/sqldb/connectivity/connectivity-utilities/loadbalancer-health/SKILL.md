---
name: loadbalancer-health
description: This Skill helps to check the health status of LoadBalancer of both Connectivity Rings and Tenant Rings. It can help to identify if there is any LoadBalancer issue which causes connectivity problem.
---


## Kusto Query to  Check Avaliability of LoadBalancer VIP on port 1433, 9000, 9003

Sample Kusto Query:
```
let ClusterNameVar = "cr3.southeastus1-a.control.database.windows.net";
let _endTime = datetime(2026-02-11T05:11:53Z);
let _startTime = datetime(2026-02-11T02:11:53Z);
let searchVip = 
cluster('sqlstage.kusto.windows.net').database('sqlazure1').SqlTenant_cache_VIP_tb
| where ClusterName =~ ClusterNameVar
| summarize max(ingestionTime) by ipv4_address
| distinct ipv4_address
| project LB_IP= ipv4_address;
let  VIP= toscalar (searchVip);
let SLB = cluster('sqlstage.kusto.windows.net').database('sqlazure1').SqlTenantVIPMdMmapping_cache_tb
| where ipv4_address == VIP
| summarize max(ingestionTime) by ipv4_address, MdmAccountName;
let startTime = _startTime ;
let endTime = _endTime;
let SLBv2MDMAccount = toscalar(SLB| distinct MdmAccountName| take 1) ;
let LBquery = strcat(@"metricNamespace('Health').metric('VipAvailability').dimensions('IsDipProbeEnabled','LoadBalancerArmId','PublicIpArmId','Reason','VipAddress','VipOrIlbPA','VipPort','VnetId').samplingTypes('NullableAverage') | where VipAddress == '", VIP, "'");
evaluate geneva_metrics_request(SLBv2MDMAccount, LBquery, startTime, endTime)
| where VipPort in (1433,9000,9003)
| project TimestampUtc, VipPort, Availability= NullableAverage
```

Note:
1. The 2 kusto cache talbes mentioned in the query are fixed, even SQL ClusterName is in different regions:
cluster('sqlstage.kusto.windows.net').database('sqlazure1').SqlTenant_cache_VIP_tb 
cluster('sqlstage.kusto.windows.net').database('sqlazure1').SqlTenantVIPMdMmapping_cache_tb 
2. The variables are:
ClusterNameVar: the connectivity ring or tenant ring to be checked
_startTime: issue start time
_endTime: issue end time

If the output of the query shows availability is below 90, which means there is a problem with the LoadBalancer VIP.

In this case, suggest a URL to let the user further check the LoadBalancer health.

## Generate the LoadBalancer dashboard URL and share with user:

1. Use the sample kusto query:

```
let ClusterNameVar = "cr3.southeastus1-a.control.database.windows.net";
let searchVip1=cluster('sqlstage.kusto.windows.net').database('sqlazure1').SqlTenant_cache_VIP_tb
| where ClusterName =~ ClusterNameVar
| summarize arg_max(ingestionTime,*) by ipv4_address
| distinct ipv4_address
| project LB_IP= ipv4_address;
let searchVip= toscalar (searchVip1);
let sourceTable=
cluster("azslb.kusto.windows.net").database("azslbmds").VipMetadataSnapshotRecord
| where env_time > ago(6h)
| where Vip == searchVip or AltAddress == searchVip
| project Vip, VipUri, Type, SKU, AltAddress, VmLocs, CountHosts, Region, env_time
| summarize arg_max(env_time, *) by Vip
| top 1 by env_time desc;
let muxDetails=cluster("azslb.kusto.windows.net").database("azslbmds").DSMulticastGroupEvent
| where env_time > ago(3h) and SegmentName != "0.0.0.0_0" and SegmentName != "::_0"
| where Uri has "MuxPoolManager"
| project env_time, env_cloud_name, SegmentName, GroupIncarnationId, MulticastGroup, Uri
| summarize arg_max(env_time, *) by SegmentName, Uri
| extend CidrString = replace_string(SegmentName, "_", "/")
| extend Ipv4Cidr = iff(CidrString has ":", "", CidrString), Ipv6Cidr = iff(CidrString has ":", CidrString, "")
| where ipv6_is_in_range(searchVip, Ipv6Cidr) or ipv4_is_in_range(searchVip, Ipv4Cidr)
| extend SlbRing = replace_string(GroupIncarnationId, "-azr", "-az,r"), Region=env_cloud_name
;
let vipSourceTabe=sourceTable | join kind=leftouter muxDetails on Region
| join kind=leftouter (
    cluster("azslb.kusto.windows.net").database("azslbmds").SlbMetadataVersionRecord
    | where env_time  > ago(1h)
    | summarize by Region, MdmAccountName
    | extend HPAccountName = strcat("slbhp", substring(MdmAccountName, 5))
    ) on $left.Region == $right.Region
| project-away Region1, Region2, env_time1;
let resourceTable_has_records = toscalar(vipSourceTabe | summarize count() > 0);
union 
(vipSourceTabe | where resourceTable_has_records == true),
(datatable(Vip:string)[''] | where resourceTable_has_records == false)
| extend DipAvailbility= strcat('https://portal.microsoftgeneva.com/dashboard/slbv2prod/AzureMonitor/DipAvailability_HealthProbeStatus?overrides=[{"query":"//dataSources","key":"account","replacement":"',MdmAccountName,'"},{"query":"//*[id=',"'VipAddress']",'","key":"value","replacement":"', Vip, '"}]')
| extend SNAT= strcat('https://portal.microsoftgeneva.com/dashboard/slbv2prod/AzureMonitor/SnatAvailability?overrides=[{"query":"//dataSources","key":"account","replacement":"', HPAccountName,'"},{"query":"//*[id=',"'VipAddress'",']","key":"value","replacement":"', Vip, '"}]')
| extend DDOS= strcat('https://portal.microsoftgeneva.com/dashboard/CNS/CRI?overrides=[{"query":"//*[id=',"'DestinationVIP'",']","key":"value","replacement":"', Vip,'"}]')
| project Pack = bag_pack("VIP", Vip,  "DipAvailbility Link", DipAvailbility, "SNAT Link", SNAT, "DDOS Link", DDOS,"IP-Cidr", Ipv4Cidr, "VipUri", VipUri, "LB SKU", SKU,  "SLB-Ring",SlbRing, "SLB Mdm Account", MdmAccountName, "HP Account", HPAccountName,"========","================" )
| mv-expand Pack
| extend Object = tostring(bag_keys(Pack)[0])
| project Object, List= tostring( Pack[Object])
```

Note: 
1. Only replace ClusterNameVar with the ring you want to check.
2. Kusto clusters and tables in the query are fixed, even SQL ClusterName is in different regions.
3. The output of the query will have 3 links for each LoadBalancer VIP, which are "DipAvailbility Link", "SNAT Link" and "DDOS Link". You can share these links to user to let them further check the LoadBalancer health status in different aspects.
4. If the user encounters a permission error on the Kusto return, they may not have access to the Kusto cluster 'azslb.kusto.windows.net'. Please notify the user to request permission from [AznwKustoReader Group](https://idwebelements.microsoft.com/GroupManagement.aspx?Group=AznwKustoReader&operation=join). For more Networking Kusto permissions, refer the CSS wiki [AZN Data Access Tools Reference](https://msazure.visualstudio.com/AzureWiki/_wiki/wikis/AzureWiki.wiki/985089/AZN-Data-Access-Tools-Reference).
