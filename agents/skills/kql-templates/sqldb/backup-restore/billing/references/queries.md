# Kusto Query Reference Index

This file documents all KQL queries used by the `backup billing` skill.

## Query Inventory


## Investigate Billed Quantity

The following query will report the usage that gets sent to Microsoft commerce team (responsible for translating SQL DB's reported usage to an actual monetary bill).

```kusto
// Query: Investigate Billed Quantity - Report usage sent to Microsoft commerce
// Required Parameters: {LogicalServerName}, {LogicalDatabaseName}
// Optional Parameters: {pool_name}
//
let HoursPerMonth = 744;
PostReportedUsage2
| where InfoFieldMeteredServiceType == "SQL Database RAGRS Backup Storage"
| where ServerName =~ "{LogicalServerName}" or ElasticPoolName =~ "{pool_name}" or DatabaseName =~ "{LogicalDatabaseName}"
| project EventDateTime, ResourceUri, ServerName, ElasticPoolName, DatabaseName, ElasticPoolId, DatabaseId, UsageResourceQuantity, CurrentCumulativeBackupConsumptionInGB = UsageResourceQuantity*HoursPerMonth
```

### Hourly Consumption Report

This should match billing details:

```kusto
// Query: Hourly Consumption Report - Daily aggregated backup consumption
// Required Parameters: {StartTime}, {EndTime}, {LogicalServerName}
//
PostReportedUsage2
| where EventDateTime >= datetime({StartTime}) and EventDateTime <= datetime({EndTime})
| where ServerName =~ '{LogicalServerName}'
| where InfoFieldMeteredServiceType == "SQL Database RAGRS Backup Storage"
| extend RestorableDroppedDB = iif(ResourceUri contains "restorableDroppedDatabase", substring(ResourceUri, indexof(ResourceUri, "restorableDroppedDatabase")+27),'')
| summarize sum(UsageResourceQuantity), count(UsageResourceQuantity) by tolower(ResourceUri), ServerName, ElasticPoolName, DatabaseName, RestorableDroppedDB, bin(EventDateTime, 1d)
| project-rename BackupConsumptionInGB = sum_UsageResourceQuantity, NumberOfHourlyRecords = count_UsageResourceQuantity, Date = EventDateTime
| project Date, ServerName, DatabaseName, ElasticPoolName, RestorableDroppedDB, NumberOfHourlyRecords, round(BackupConsumptionInGB,4)
| order by Date asc
```

> **Note:** It seems like PostReportedUsage2 doesn't contain logs anymore. If this info could be consulted somewhere else, please update this section to indicate where we can find that data.

## Get Insight into Charges

Execute the following query to get detailed billing insights:

```kusto
// Query: Get Insight into Charges - Detailed billing breakdown by backup type
// Required Parameters: {logical_database_id}
//
MonManagement
| where event =~ 'sqldb_backup_billing_complete' and logical_database_id =~ '{logical_database_id}'
| project billingCalculationTimestamp=originalEventTimestamp, logical_database_id, full_backup_cumulative_size_mb=full_backup_cumulative_size,
diff_backup_cumulative_size_mb=diff_backup_cumulative_size, log_backup_cumulative_size_mb=log_backup_cumulative_size, cumulative_backup_storage_size_mb=todouble(backup_storage_size)
| extend full_ratio = full_backup_cumulative_size_mb/cumulative_backup_storage_size_mb, diff_ratio=diff_backup_cumulative_size_mb/cumulative_backup_storage_size_mb,
log_ratio=log_backup_cumulative_size_mb/cumulative_backup_storage_size_mb
| join kind=inner
(MonAnalyticsDBSnapshot
| where logical_database_id =~ '{logical_database_id}'
| project logicalDbSnapshotTimestamp=TIMESTAMP, logical_server_name, logical_database_name, logical_database_id=tolower(logical_database_id), logical_resource_pool_id,
logical_database_max_size_mb=max_size_bytes/1024.0/1024.0, backup_retention_days, sql_instance_name=tolower(sql_instance_name), physical_database_id=tolower(physical_database_id) )
on logical_database_id
| where billingCalculationTimestamp > logicalDbSnapshotTimestamp
| summarize arg_max(logicalDbSnapshotTimestamp, *) by billingCalculationTimestamp, logical_database_id
| join kind=inner
(MonDmIoVirtualFileStats
| where logical_database_id =~ '{logical_database_id}'
| where type_desc == 'ROWS' and is_primary_replica == 1
| summarize physical_database_size_on_disk_mb=sum(size_on_disk_bytes)/1024.0/1024.0 by TIMESTAMP, logical_database_id
| project physicalDbSnapshotTimestamp=TIMESTAMP, physical_database_size_on_disk_mb, logical_database_id=tolower(logical_database_id)
) on logical_database_id
| where billingCalculationTimestamp > physicalDbSnapshotTimestamp
| summarize arg_max(physicalDbSnapshotTimestamp, *) by billingCalculationTimestamp, logical_database_id
| project-away logical_database_id1, logical_database_id2, sql_instance_name, physical_database_id
| project billingCalculationTimestamp, logical_server_name, logical_database_name, full_backup_cumulative_size_mb, diff_backup_cumulative_size_mb,
log_backup_cumulative_size_mb, cumulative_backup_storage_size_mb, logical_database_max_size_mb, backup_retention_days
| project-rename BillingCalculationTimestamp=billingCalculationTimestamp, ServerName=logical_server_name, DatabaseName = logical_database_name,
FullBackupCumulativeSizeMB=full_backup_cumulative_size_mb, DiffBackupCumulativeSizeMB=diff_backup_cumulative_size_mb, LogBackupCumulativeSizeMB=log_backup_cumulative_size_mb,
CumulativeBackupStorageMB=cumulative_backup_storage_size_mb, DatabaseMaxSizeMB=logical_database_max_size_mb, BackupRetentionDays=backup_retention_days
| order by BillingCalculationTimestamp asc
```

### Alternative Query by Server Name

Alternative query version by Matteo Teruzzi:

```kusto
// Query: Alternative Query by Server Name - Get billing insights for all databases on a server
// Required Parameters: {LogicalServerName}
//
MonAnalyticsDBSnapshot
| where logical_server_name =~ '{LogicalServerName}'
| project logicalDbSnapshotTimestamp=TIMESTAMP, logical_server_name, logical_database_name, logical_database_id=tolower(logical_database_id), logical_resource_pool_id, logical_database_max_size_mb=max_size_bytes/1024.0/1024.0, backup_retention_days, sql_instance_name=tolower(sql_instance_name), physical_database_id=tolower(physical_database_id)
| join (
MonManagement
| where event =~ "sqldb_backup_billing_complete"
| project billingCalculationTimestamp=originalEventTimestamp, logical_database_id, full_backup_cumulative_size, diff_backup_cumulative_size, log_backup_cumulative_size, backup_storage_size
) on logical_database_id
| where billingCalculationTimestamp > logicalDbSnapshotTimestamp
| project billingCalculationTimestamp, logicalDbSnapshotTimestamp, logical_database_id, logical_database_name, full_backup_cumulative_size_mb=full_backup_cumulative_size, diff_backup_cumulative_size_mb=diff_backup_cumulative_size, log_backup_cumulative_size_mb=log_backup_cumulative_size, cumulative_backup_storage_size_mb=todouble(backup_storage_size), sql_instance_name, physical_database_id
| extend full_ratio = full_backup_cumulative_size_mb/cumulative_backup_storage_size_mb, diff_ratio=diff_backup_cumulative_size_mb/cumulative_backup_storage_size_mb, log_ratio=log_backup_cumulative_size_mb/cumulative_backup_storage_size_mb
| summarize arg_max(logicalDbSnapshotTimestamp, *) by billingCalculationTimestamp, logical_database_id, logical_database_name
| join kind=inner
(MonDmIoVirtualFileStats
| where type_desc == "ROWS" and is_primary_replica == 1
| summarize physical_database_size_on_disk_mb=sum(size_on_disk_bytes)/1024.0/1024.0 by TIMESTAMP, logical_database_id
| project physicalDbSnapshotTimestamp=TIMESTAMP, physical_database_size_on_disk_mb, logical_database_id=tolower(logical_database_id)
) on logical_database_id
| where billingCalculationTimestamp > physicalDbSnapshotTimestamp
| summarize arg_max(physicalDbSnapshotTimestamp, *) by billingCalculationTimestamp
| project-away logical_database_id1, logical_database_id, sql_instance_name, physical_database_id
```

### Query All Databases on a Server

```kusto
// Query: Query All Databases on a Server - Get billing summary for all databases
// Required Parameters: {LogicalServerName}, {StartTime}
// Note: Uses relative time range (50 days ago from StartTime)
//
let ServerName = "{LogicalServerName}";
let TimeRange = datetime({StartTime}) - 50d;
MonAnalyticsDBSnapshot
| where TIMESTAMP >= TimeRange
| where logical_server_name =~ ServerName
| distinct logical_database_id, logical_database_name
| join kind=leftouter (
MonManagement
| where TIMESTAMP >= TimeRange
| where event =~ "sqldb_backup_billing_complete"
| project billingCalculationTimestamp=originalEventTimestamp, logical_database_id = toupper(logical_database_id),
full_backup_cumulative_size, diff_backup_cumulative_size, log_backup_cumulative_size, backup_storage_size
) on logical_database_id
| order by logical_database_name asc, billingCalculationTimestamp asc
| project logical_database_name, billingCalculationTimestamp, full_backup_cumulative_size,
diff_backup_cumulative_size, log_backup_cumulative_size, backup_storage_size
```

## Investigating the Billing Pipeline

### ScopePostReportedUsage Query

Start by looking in `ScopePostReportedUsage`. This is the data which is generated by the billing pipeline and which we actually send to PAV2.

```kusto
// Query: ScopePostReportedUsage - Data sent to PAV2 (Microsoft commerce)
// Required Parameters: {customer_subscription_id}
// Note: This table contains VLDB backup billing data only
//
ScopePostReportedUsage
| where SubscriptionId =~ "{customer_subscription_id}"
| where BillingProductType contains "BackupStorage"
```

### MonBillingPitrBackupSize Query

Next, look at `MonBillingPitrBackupSize` which is generated by DMV Collector and fed into the billing pipeline.

```kusto
// Query: MonBillingPitrBackupSize - Backup size data from DMV Collector
// Required Parameters: {logical_database_id}
//
MonBillingPitrBackupSize
| where database_id =~ "{logical_database_id}"
```
## Additional Billing Queries

### Query UAE Usage Data for Specific Resource

Use this query to get billing data for a specific resource and product:

```kusto
// Query: UAE Usage Data - Get billing data for specific resource from UAE API
// Required Parameters: {customer_subscription_id}, {StartTime}, {EndTime}
// Note: Update resource_uri and product_name as needed for specific resources
//
let subscription_id = "{customer_subscription_id}"; 
let resource_uri = "/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{server_name}/databases/{database_name}"; 
let product_name = "SQL Database Hyperscale - Storage"; 
let usage_start_date = datetime({StartTime}); 
let usage_end_date = datetime({EndTime}); 
getUAEUsageData() 
| where usage_date_time >= usage_start_date and usage_date_time < usage_end_date 
| where resource_provider == "SqlAzure" 
| where entitlement_id == subscription_id  
| where resourceUri =~ resource_uri 
| join kind=inner AllMeters on $left.metered_resource_id == $right.BillingMeterId 
| where ProductName == product_name 
| project 
   resource_provider, 
    ProductName, 
    ProductType, 
    BillingMeterId, 
    usage_date_time, 
    resourceUri, 
    location, 
    quantity
```

### Query P360 Consumption Units - Weekly Summary by Product

Use this query to get weekly consumption data for a specific subscription and product:

```kusto
// Query: P360 Consumption Units Weekly Summary - Weekly consumption by product
// Required Parameters: {customer_subscription_id}
// Note: Requires access to P360 consumption cluster
//
let service_family = "Databases"; 
let service_name = "SQL Database"; 
let product = "SQL Database SingleDB Hyperscale - Storage"; 
let subscription_id = "{customer_subscription_id}"; 
cluster('https://consumptionrptwus3prod.westus3.kusto.windows.net').database('consumptiondatadb').P360ConsumptionUnitsPROD 
    | where workload_dimensions_service_level_1 == service_family 
    | where workload_dimensions_service_level_2 == service_name 
    | where workload_dimensions_service_level_4 == product 
    | where CustomerSubscriptionId =~ subscription_id 
    | where Weekly_0_Quantity > 0 or Weekly_1_Quantity > 0 or Weekly_2_Quantity > 0 or Weekly_3_Quantity > 0 
| summarize sum(Weekly_1_Quantity),  
    sum(Weekly_2_Quantity),  
    sum(Weekly_3_Quantity),  
    sum(Weekly_4_Quantity),  
    sum(Weekly_5_Quantity),  
    sum(Weekly_6_Quantity),  
    sum(Weekly_7_Quantity),  
    sum(Weekly_8_Quantity),  
    sum(Weekly_9_Quantity),  
    sum(Weekly_10_Quantity)    
by workload_dimensions_service_level_4;
```

### Query P360 Consumption Units - Daily Summary by Product

Use this query to get daily consumption data for all products under a specific service:

```kusto
// Query: P360 Consumption Units Daily Summary - Daily consumption by product
// Required Parameters: {customer_subscription_id}
// Note: Requires access to P360 consumption cluster, limited to 10 results
//
let service_family = "Databases"; 
let service_name = "SQL Database"; 
//let product = "SQL Database SingleDB Hyperscale - Storage"; 
let subscription_id = "{customer_subscription_id}"; 
cluster('https://consumptionrptwus3prod.westus3.kusto.windows.net').database('consumptiondatadb').P360ConsumptionUnitsPROD 
    | where workload_dimensions_service_level_1 == service_family 
    | where workload_dimensions_service_level_2 == service_name 
    | where CustomerSubscriptionId =~ subscription_id 
    | where Daily_0_Quantity > 0 or Daily_1_Quantity > 0 or Daily_2_Quantity > 0 or Daily_3_Quantity > 0 
    | limit 10 
| summarize sum(Daily_1_Quantity),  
    sum(Daily_2_Quantity),  
    sum(Daily_3_Quantity),  
    sum(Daily_4_Quantity),  
    sum(Daily_5_Quantity),  
    sum(Daily_6_Quantity),  
    sum(Daily_7_Quantity),  
    sum(Daily_8_Quantity),  
    sum(Daily_9_Quantity),  
    sum(Daily_10_Quantity)    
by workload_dimensions_service_level_4;
```

## Execution via Azure MCP

All queries should be executed using the `mcp_azure_mcp_kusto` tool:

## Related References

- [SKILL.md](../SKILL.md) - Main skill definition
