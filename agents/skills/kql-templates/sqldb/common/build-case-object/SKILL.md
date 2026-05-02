---
name: build-case-object
description: Builds a comprehensive case object containing complete information about an Azure SQL Database logical server and database by querying telemetry. Retrieves physical database ID, instance names, cluster names, region, subscription, and other metadata. Use when gathering database context, preparing parameters for Kusto queries, or when user needs complete resource information for diagnostics or operations.
---

# Resource case builder

## Step 1: Get database metadata

Use [execute-kusto-query skill](.github/skills/Common/execute-kusto-query/SKILL.md) to execute following query:

```kusto
MonAnalyticsDBSnapshot
        | where TIMESTAMP > ago(2h)
        // Server names are guaranteed to be lower case. We can use == instead of =~ to take advantage of Kusto index partitioning
        | where logical_server_name == tolower('{LogicalServerName}') and logical_database_name =~ '{LogicalDatabaseName}'
        | where fabric_application_uri !startswith 'fabric:/Worker.Vldb.Storage' and fabric_application_uri !startswith 'fabric:/Worker.Vldb.LogReplica'
        | where sql_instance_name !startswith 'v-'
        | summarize max(TIMESTAMP),
            argmax(TIMESTAMP,
                    physical_database_id,
                    sql_instance_name,
                    fabric_partition_id,
                    logical_resource_pool_id,
                    tenant_ring_name,
                    ClusterName,
                    NodeName,
                    resource_group,
                    logical_database_id,
                    edition,
                    region_name,
                    fabric_application_uri,
                    service_level_objective,
                    create_mode,
                    state,
                    create_time,
                    last_update_time,
                    physical_database_state,
                    customer_subscription_id),
                    physical_database_id_collection = makeset(physical_database_id),
                    logical_database_id_collection = makeset(logical_database_id),
                    partition_id_collection = makeset(fabric_partition_id),
                    sql_instance_name_collection = makeset(sql_instance_name),
                    tenant_ring_name_collection = makeset(tenant_ring_name),
                    control_ring_name_collection = makeset(ClusterName),
                    physical_db_state_collection = makeset(physical_database_state)
                by logical_server_name, logical_database_name
                | extend physical_database_id = max_TIMESTAMP_physical_database_id
                | extend logical_database_id = max_TIMESTAMP_logical_database_id
                | extend edition = max_TIMESTAMP_edition
                | extend AppName  = max_TIMESTAMP_sql_instance_name
                | extend partition_id= max_TIMESTAMP_fabric_partition_id
                | extend logical_resource_pool_id = max_TIMESTAMP_logical_resource_pool_id
                | extend last_seen = max_TIMESTAMP
                | extend SubscriptionId = max_TIMESTAMP_customer_subscription_id
                | extend TenantRing = max_TIMESTAMP_tenant_ring_name
                | extend ControlRing = max_TIMESTAMP_ClusterName
                | extend ResourceGroup = max_TIMESTAMP_resource_group
                | extend RegionName = max_TIMESTAMP_region_name
                | extend FabricApplicationUri = max_TIMESTAMP_fabric_application_uri
                | extend ServiceLevelObjective = max_TIMESTAMP_service_level_objective
                | extend CreateMode = max_TIMESTAMP_create_mode
                | extend CreateTime = max_TIMESTAMP_create_time
                | extend State = max_TIMESTAMP_state
                | extend LastUpdateTime = max_TIMESTAMP_last_update_time
                | extend physical_database_state = max_TIMESTAMP_physical_database_state
                | project SubscriptionId, AppName, physical_database_id, last_seen, NodeName, //ClusterShortName, DAClusterName,
                    physical_database_id_collection, partition_id_collection, sql_instance_name_collection, logical_resource_pool_id,
                    TenantRing, tenant_ring_name_collection, ControlRing, control_ring_name_collection, partition_id, ResourceGroup,logical_database_id,
                    logical_database_id_collection, edition, RegionName, FabricApplicationUri, ServiceLevelObjective, CreateMode, State, CreateTime, LastUpdateTime,
                    physical_database_state, physical_db_state_collection 
```
