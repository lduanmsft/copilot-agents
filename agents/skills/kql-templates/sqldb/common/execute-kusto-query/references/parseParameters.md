Parse and replace parameters in Kusto queries

When you see pattern {ParamaterName} in Kusto queries, replace it with actual
values provided by user.  If User has not provided values, ask user for the values.
In the example below, replace {LogicalServerName} and {LogicalDatabaseName} with actual values
```
// Obtain information about ClusterName, NodeName, ApplicationNameUri, is_primary_replica
//
MonDmDbHadrReplicaStates
| where PreciseTimeStamp >ago(1h)
| where LogicalServerName =~'{LogicalServerName}'  and logical_database_name =~'{LogicalDatabaseName}'
//| where LogicalServerName =~'i0zlmt2rs9'  and logical_database_name =~'DedicatedContent_67629_108'
| where is_local == 1
| summarize arg_max(PreciseTimeStamp, *) by replica_id
| extend ApplicationNameUri = strcat ('fabric:/', AppTypeName, '/', AppName)
| project ClusterName, NodeName, internal_state_desc, AppName, AppTypeName, is_primary_replica, ApplicationNameUri
```