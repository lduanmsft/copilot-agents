---
name: billing
description: Debug Azure SQL Database billing issues, including analysis of backup unit consumption. Required inputs from calling agent - kusto-cluster-uri, kusto-database, logical server name, logical database name, and time window.
---

## Required Information

### From User or ICM:
- **LogicalServerName** - The logical server name (e.g., `genesisonline-server`)
- **LogicalDatabaseName** - The logical database name (e.g., `genesisonlinegraph-db`)
- **customer_subscription_id** - Customer subscription ID (optional - will be discovered if not provided)
- **StartTime** - Query window start time (UTC format: `2026-01-01 02:00:00`)
- **EndTime** - Query window end time (UTC format: `2026-01-01 02:00:00`)

**Note:** Parameter names follow the normalized naming convention defined in [normalize-query-params.prompt.md](../../prompts/normalize-query-params.prompt.md)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill (one or more configurations):
- **AppName** - Application/workload name (sql_instance_name)
- **ClusterName** - Tenant ring/cluster name (tenant_ring_name)
- **logical_database_id** - Logical database identifier (GUID)
- **physical_database_id** - Physical database identifier (GUID)
- **fabric_partition_id** - Service Fabric partition identifier (GUID)
- **service_level_objective** - Database service tier (e.g., SQLDB_HS_Gen5_4)
- **zone_resilient** - Zone redundancy setting (boolean)
- **deployment_type** - Deployment configuration (e.g., "GP without ZR", "GP with ZR", "BC")
- **config_start_time** - Configuration active from timestamp
- **config_end_time** - Configuration active until timestamp
- **customer_subscription_id** - Customer subscription identifier (GUID)
- All other database environment variables

## Workflow

### 1. Validate Inputs

Ensure all required parameters are provided:
- From user/ICM: `{LogicalServerName}`, `{LogicalDatabaseName}`, `{StartTime}`, `{EndTime}`
- From execute-kusto-query: kusto-cluster-uri, kusto-database, region
- From get-db-info: `{AppName}`, `{ClusterName}`, `{physical_database_id}`, `{fabric_partition_id}`, `{deployment_type}`, `{config_start_time}`, `{config_end_time}`, and all other database variables
- Optional: `{customer_subscription_id}` (will be discovered if not provided)

 ### Task 3 Obtain Database information
 Use this Kusto query to get database information for subsequent usage.  
 Save the output into variables
 
 ```
MonDmRealTimeResourceStats
| where PreciseTimeStamp between (todatetime('{StartTime}') .. todatetime('{EndTime}'))
| where LogicalServerName =~'{LogicalServerName}' and LogicalDatabaseName =~ '{LogicalDatabaseName}'
| where replica_type ==0
| summarize by ClusterName, PrimaryNodeName=NodeName, AppName, physical_database_guid, LogicalServerName, LogicalDatabaseName
 
 ```
 
 ### 4. Execute billing queries 

Execute Query Inventory from [references/queries.md](references/queries.md).

Output results in tabular format.

 ### 5. Generate Output 

Generate as specified in [references/output.md](references/output.md) - this provides a detailed billing analysis.