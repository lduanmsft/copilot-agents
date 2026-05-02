---
name: appnameandnodeinfo
description: Constructs metadata for Kusto queries including AppName, NodeName, ClusterName, time ranges, CPU metrics, edition, and Elastic Pool info. This skill is heavily used by other performance skills to obtain metadata.
tools: ['search', 'fetch', 'githubRepo', 'kusto']
---

# Construct metadata for Kusto queries: AppName, NodeName, ClusterName, time ranges, CPU metrics, edition, and Elastic Pool info

## Skill Overview

This skill outputs the metadata string consisting of appName, application name, cluster Name, node Name and time range.

**⚠️ IMPORTANT: This skill has 6 tasks. You MUST execute ALL tasks to retrieve all output variables.**

### Output Variables Summary

| Variable | Source Task | Description |
|----------|-------------|-------------|
| `{KustoClusterUri}` | Task 1 | Kusto cluster URI for the region |
| `{KustoDatabase}` | Task 1 | Kusto database name |
| `{AppNamesOnly}` | Task 2 | Comma-separated list of AppNames |
| `{AppNamesNodeNamesWithOriginalEventTimeRange}` | Task 2 | Filter string for queries using originalEventTimestamp |
| `{AppNamesNodeNamesWithPreciseTimeRange}` | Task 2 | Filter string for queries using PreciseTimeStamp |
| `{ApplicationNamesNodeNamesWithOriginalEventTimeRange}` | Task 2 | Filter string using application_name |
| `{NodeNamesWithOriginalEventTimeRange}` | Task 2 | Filter string for NodeName with originalEventTimestamp |
| `{NodeNamesWithPreciseTimeRange}` | Task 2 | Filter string for NodeName with PreciseTimeStamp |
| `{AppNamesNodeNamesWith7DayOriginalEventTimeRange}` | Task 3 | 7-day historical filter string |
| `{SumCpuMillisecondOfAllApp}` | Task 4 | Total CPU milliseconds across all apps |
| `{ActualSumCpuMillisecondOfAllApp}` | Task 5 | Actual CPU milliseconds consumed |
| `{edition}` | Task 6 | Database service tier (Basic, Standard, Premium, GeneralPurpose, BusinessCritical, Hyperscale, Free) |
| `{isInElasticPool}` | Task 6 | Whether database is in an Elastic Pool (true/false) |
| `{service_level_objective}` | Task 6 | Service Level Objective (SLO) of the database |

## Workflow Overview

**This skill has 6 tasks.**

| Task | Description | Condition |
|------|-------------|-----------|
| Task 1 | Get Kusto cluster info | Always |
| Task 2 | Get AppNames, NodeNames, time ranges | Always |
| Task 3 | Get 7-day historical filter | Always |
| Task 4 | Calculate SumCpuMillisecond | Always |
| Task 5 | Calculate ActualSumCpuMillisecond | Always |
| Task 6 | Get edition and isInElasticPool | Always |

## Prerequisites

- Access to Kusto clusters for SQL telemetry
- Understanding of Azure SQL HA architecture (see [Architecture](../../../Architecture/))
- Knowledge of Extended Events (XEvents): `hadr_fabric_api_replicator_begin_change_role`, `hadr_fabric_api_replicator_end_change_role`

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: YYYY-MM-DD HH:MM:SS | `2026-01-15 10:00:00` |
| `{EndTime}` | Investigation end time | UTC: YYYY-MM-DD HH:MM:SS | `2026-01-15 12:00:00` |
| `{replica_role}` | Replica role to filter on. **Default: 0** if not specified | integer | `0` |

### replica_role Values

| Value | Description |
|-------|-------------|
| `0` | Primary replica (default) |
| `1` | Secondary replica (also known as: readonly secondary, readonly secondary replica, local secondary) |
| `2` | Forwarder |



## Execution Steps

### Task 1:  Obtain Kusto cluster information for the logical server
**CRITICAL:** Always identify the correct cluster - do NOT use default clusters
Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../execute-kusto-query/references/getKustoClusterDetails.md](../execute-kusto-query/references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Use mcp_azure_mcp_kusto tool to execute the kusto query below to construct string variables `AppNamesNodeNamesWithOriginalEventTimeRange`,`AppNamesNodeNamesWithPreciseTimeRange`,`ApplicationNamesNodeNamesWithOriginalEventTimeRange` , `NodeNamesWithOriginalEventTimeRange` and `AppNamesOnly`

```kql
MonDmRealTimeResourceStats
| where replica_role == {replica_role} // Default: 0 (primary replica) if not specified
| where AppTypeName !contains 'Worker.Vldb.Storage'
| where LogicalServerName =~'{serverName}' and database_name =~'{dbName}'
| where originalEventTimestamp >=datetime({startTime}) and originalEventTimestamp<=datetime({endTime})
| order by originalEventTimestamp asc nulls first
| serialize
| extend prevNodeName = prev(NodeName)
| extend nextNodeName = next(NodeName)
| extend isFirst = (NodeName != prevNodeName)
| extend isLast = (NodeName != nextNodeName)
| where isFirst == true or isLast == true
| extend EndTime = next(originalEventTimestamp)
| extend StartTime = originalEventTimestamp
| where isFirst == true
| extend IsManagedInstance = SourceNamespace in ('AzWcowProdSql', 'AzMiProdSql')
| project StartTime,EndTime,AppName,NodeName,ClusterName,IsManagedInstance
| where isnotnull( EndTime) and isnotnull( StartTime);//bug 3980325
```

#### 🚩 Managed Instance Check

**CRITICAL:** After executing Task 2, check the `IsManagedInstance` value from the query results.

**If `IsManagedInstance` is `true` for ANY row:**
- **STOP** - Do NOT proceed with subsequent tasks
- **Terminate this skill immediately** and display the following message to the user:

> ⚠️ **This is a Managed Instance, we don't support yet.**

- **If this skill was invoked by another skill (caller skill):** The caller skill MUST also terminate immediately. This skill provides required metadata variables that the caller skill depends on. Without these variables, the caller skill cannot proceed and should display the same termination message to the user.

The skill is only applicable to Azure SQL Database. Managed Instances (identified by `SourceNamespace` values `AzWcowProdSql` or `AzMiProdSql`) require different troubleshooting approaches and are not supported by this skill.

**If `IsManagedInstance` is `false` for ALL rows:** Continue processing.


#### Store Variables

If signle row is returned, store these variables for subsequent queries. Please note, the strings wrappred in '{}' are placeholder, need to replace with actual values.
Samples
| Variable Name | Actual value|
|--------------|---------------|
| `AppNamesOnly` | `'{AppName}'` |
| `AppNamesNodeNamesWithOriginalEventTimeRange` | ("AppName=~'{AppName}' and originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |
| `AppNamesNodeNamesWithPreciseTimeRange` | ("AppName=~'{AppName}' and PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'
{ClusterName}')" |
| `ApplicationNamesNodeNamesWithOriginalEventTimeRange` | ("application_name contains '{AppName}' and originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'
{ClusterName}')" |
| `NodeNamesWithOriginalEventTimeRange` | "(originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |
| `NodeNamesWithPreciseTimeRange` | "(PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |


If multiple rows are returned, store these variables for subsequent queries and use "or" to concatenate the strings of each row.  Please note, the strings wrappred in '{}' are placeholder, need to replace with actual values.
Samples
| Variable Name | Actual value|
|--------------|---------------|
| `AppNamesOnly` | `'{AppName1}','{AppName2}'` (comma-separated list of all unique AppNames) |
| `AppNamesNodeNamesWithOriginalEventTimeRange` | ("AppName=~'{AppName}' and originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}') or (originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |
| `AppNamesNodeNamesWithPreciseTimeRange` | ("AppName=~'{AppName}' and PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'
{ClusterName}') or (PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |
| `ApplicationNamesNodeNamesWithOriginalEventTimeRange` | ("application_name contains '{AppName}' and originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'
{ClusterName}') or (PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |
| `NodeNamesWithOriginalEventTimeRange` | "(originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}') or (originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |
| `NodeNamesWithPreciseTimeRange` | "(PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}') or (PreciseTimeStamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |


### Task 3: Use mcp_azure_mcp_kusto tool to execute the kusto query below to construct string variable `AppNamesNodeNamesWith7DayOriginalEventTimeRange`

```kql
MonDmRealTimeResourceStats
| where replica_role == {replica_role} // Default: 0 (primary replica) if not specified
| where AppTypeName !contains 'Worker.Vldb.Storage'
| where LogicalServerName =~'{serverName}' and database_name =~'{dbName}'
| where originalEventTimestamp >=datetime_add('day', -7, datetime({startTime})) and originalEventTimestamp<=datetime({startTime})
| order by originalEventTimestamp asc nulls first
| serialize
| extend prevNodeName = prev(NodeName)
| extend nextNodeName = next(NodeName)
| extend isFirst = (NodeName != prevNodeName)
| extend isLast = (NodeName != nextNodeName)
| where isFirst == true or isLast == true
| extend EndTime = next(originalEventTimestamp)
| extend StartTime = originalEventTimestamp
| where isFirst == true
| extend IsManagedInstance = SourceNamespace in ('AzWcowProdSql', 'AzMiProdSql')
| project StartTime,EndTime,AppName,NodeName,ClusterName
| where isnotnull( EndTime) and isnotnull( StartTime);//bug 3980325
```

#### Store Variables

If signle row is returned, store these variables for subsequent queries. Please note, the strings wrappred in '{}' are placeholder, need to replace with actual values.
Samples
| Variable Name | Actual value|
|--------------|---------------|
| `AppNamesNodeNamesWith7DayOriginalEventTimeRange` | ("AppName=~'{AppName}' and originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |

If multiple rows are returned, store these variables for subsequent queries and use "or" to concatenate the strings of each row.  Please note, the strings wrappred in '{}' are placeholder, need to replace with actual values.
Samples
| Variable Name | Actual value|
|--------------|---------------|
| `AppNamesNodeNamesWith7DayOriginalEventTimeRange` | ("AppName=~'{AppName}' and originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}') or (originalEventTimestamp between (datetime({StartTime}) .. datetime({EndTime})) and NodeName=~'{NodeName}' and ClusterName=~'{ClusterName}')" |

### Task 4: Use mcp_azure_mcp_kusto tool to execute the kusto query below to construct variable `SumCpuMillisecondOfAllApp`

```kql
MonDmRealTimeResourceStats
| where replica_role == {replica_role} // Default: 0 (primary replica) if not specified
| where LogicalServerName =~'{serverName}' and database_name =~'{dbName}'
| where originalEventTimestamp >=datetime({startTime}) and originalEventTimestamp<=datetime({endTime})
| order by originalEventTimestamp asc nulls first
| serialize
| extend prevCpuCap = prev(cpu_cap_in_sec)
| extend nextCpuCap = next(cpu_cap_in_sec)
| extend isFirst = (cpu_cap_in_sec != prevCpuCap)
| extend isLast = (cpu_cap_in_sec != nextCpuCap)
| where isFirst == true or isLast == true
| extend EndTime = next(originalEventTimestamp)
| extend StartTime = originalEventTimestamp
| where isFirst == true
| project StartTime,EndTime,cpu_cap_in_sec,AppName
| extend duration = datetime_diff('millisecond', EndTime, StartTime)
| extend CpuTimeMillisecond = duration * cpu_cap_in_sec
| project StartTime,EndTime,duration,cpu_cap_in_sec,CpuTimeMillisecond,AppName
| summarize SumCpuMillisecondOfAllApp=sum(CpuTimeMillisecond)
| project SumCpuMillisecondOfAllApp= tolong(SumCpuMillisecondOfAllApp)
```

### Task 5: Use mcp_azure_mcp_kusto tool to execute the kusto query below to construct variable `ActualSumCpuMillisecondOfAllApp`

```kql
MonDmRealTimeResourceStats
| where replica_role == {replica_role} // Default: 0 (primary replica) if not specified
| where LogicalServerName =~'{serverName}' and database_name =~'{dbName}'
| where originalEventTimestamp >=datetime({startTime}) and originalEventTimestamp<=datetime({endTime})
| summarize arg_max(avg_cpu_percent, cpu_cap_in_sec) by originalEventTimestamp//remove duplicate entries
| summarize ActualSumCpuMillisecondOfAllApp=tolong(sum(avg_cpu_percent*cpu_cap_in_sec)*15*1000/100)
```


### Task 6: Use mcp_azure_mcp_kusto tool to execute the kusto query below to get the variables `isInElasticPool` and `edition`

Determine if database is in Elastic Pool and retrieve its edition

**Purpose**: This task queries the `MonAnalyticsDBSnapshot` table to determine two important database characteristics:
1. Whether the database belongs to an Elastic Pool
2. The service tier/edition of the database
3. The Service Level Objective of the database

```kql
MonAnalyticsDBSnapshot
| where fabric_application_uri!contains 'Worker.Vldb.Storage'  and fabric_application_uri !contains 'Worker.Vldb.LogReplica'
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~'{LogicalServerName}' and logical_database_name =~'{LogicalDatabaseName}'
| extend isInElasticPool=isnotempty(logical_resource_pool_id)
| distinct isInElasticPool,edition,service_level_objective
```

#### Store Variables

| Variable Name | Data Type | Description | Possible Values |
|--------------|-----------|-------------|-----------------|
| `isInElasticPool` | boolean | Indicates if the database is part of an Elastic Pool. `true` if `logical_resource_pool_id` is not empty. | `true`, `false` |
| `edition` | string | The service tier/edition of the database | `Basic`, `Standard`, `Premium`, `GeneralPurpose`, `BusinessCritical`, `Hyperscale`, `Free` |

#### Interpretation Rules

1. **If `isInElasticPool` is `true`**: The database is part of an Elastic Pool. Resource limits are shared with other databases in the pool.
2. **If `isInElasticPool` is `false`**: The database is a singleton database with dedicated resources.
3. **Use `edition`** to determine appropriate queries and thresholds for performance analysis (e.g., Hyperscale has different architecture than other tiers).

#### Example Output

| isInElasticPool | edition |
|-----------------|---------|
| true | GeneralPurpose |

Or for a singleton Business Critical database:

| isInElasticPool | edition |
|-----------------|---------|
| false | BusinessCritical |


## Example

**Input**:
- LogicalServerName: `spartan-srv-nam-crmcorenam-56a83bc9d159`
- LogicalDatabaseName: `db_crmcorenam_20210329_10395390_e723`
- StartTime: `2025-12-09 06:00:00`
- EndTime: `2025-12-09 14:00:00`

**Output of single row**:
```
AppNamesOnly:'apxoasi123'

AppNamesNodeNamesWithOriginalEventTimeRange: "(AppName=~'apxoasi123' and originalEventTimestamp between (datetime(2025-12-09 07:00) .. datetime(2025-12-09 13:25) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

AppNamesNodeNamesWithPreciseTimeRange: "(AppName=~'apxoasi123' and PreciseTimeStamp between (datetime(2025-12-09 07:00) .. datetime(2025-12-09 08:25)) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

ApplicationNamesNodeNamesWithOriginalEventTimeRange: "(application_name contains 'apxoasi123' and originalEventTimestamp between (datetime(2025-12-09 07:00) .. datetime(2025-12-09 08:25)) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

NodeNamesWithOriginalEventTimeRange: "(originalEventTimestamp between (datetime(2025-12-09 07:00) .. datetime(2025-12-09 13:25)) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

AppNamesNodeNamesWith7DayOriginalEventTimeRange: "(AppName=~'apxoasi123' and originalEventTimestamp between (datetime(2025-12-02 07:00) .. datetime(2025-12-09 07:00) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

SumCpuMillisecondOfAllApp:567890

ActualSumCpuMillisecondOfAllApp:56789

isInElasticPool:true

edition:GeneralPurpose
```

**Output of multiple rows**:
```
AppNamesOnly:'apxoasi123','apxoasi456'

AppNamesNodeNamesWithOriginalEventTimeRange: "(AppName=~'apxoasi123' and originalEventTimestamp between (datetime(2025-12-09 07:00) .. datetime(2025-12-09 08:25)) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net') or (AppName=~'apxoasi456' and originalEventTimestamp between ((datetime(2025-12-09 08:30) .. datetime(2025-12-09 13:25)) and NodeName=~'_DB_62' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

AppNamesNodeNamesWithPreciseTimeRange: "(AppName=~'apxoasi123' and PreciseTimeStamp between (datetime(2025-12-09 07:00) .. datetime(2025-12-09 08:25)) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net') or (AppName=~'apxoasi456' and PreciseTimeStamp between (datetime(2025-12-09 08:30) .. datetime(2025-12-09 13:25)) and NodeName=~'_DB_62' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

ApplicationNamesNodeNamesWithOriginalEventTimeRange: "(application_name contains 'apxoasi123' and originalEventTimestamp between (datetime(2025-12-09 07:00) .. datetime(2025-12-09 08:25)) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net') or (application_name contains 'apxoasi456' and originalEventTimestamp between (datetime(2025-12-09 08:30) .. datetime(2025-12-09 13:25)) and NodeName=~'_DB_62' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

NodeNamesWithOriginalEventTimeRange: "(originalEventTimestamp between (datetime(2025-12-09 07:00) .. datetime(2025-12-09 08:25)) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net') or (originalEventTimestamp between (datetime(2025-12-09 08:30) .. datetime(2025-12-09 13:25)) and NodeName=~'_DB_62' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')

AppNamesNodeNamesWith7DayOriginalEventTimeRange: "(AppName=~'apxoasi123' and originalEventTimestamp between (datetime(2025-12-02 07:00) .. datetime(2025-12-09 07:00) and NodeName=~'_DB_61' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net') or (AppName=~'apxoasi456' and originalEventTimestamp between (datetime(2025-12-09 08:30) .. datetime(2025-12-09 13:25) and NodeName=~'_DB_62' and ClusterName=~'tr34037.eastus1-a.worker.database.windows.net')"

SumCpuMillisecondOfAllApp:567890

edition:GeneralPurpose
```
