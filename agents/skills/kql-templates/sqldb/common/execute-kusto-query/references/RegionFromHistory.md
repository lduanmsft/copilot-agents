# Identify which region stores the telemetry for a given Logical server through kusto query.

##Step 1. Query to get the SQL region

```kusto sample
let _startTime = {StartTime}; //variable
let _endTime = {EndTime}; //variable
let _logical_Server = {LogicalServerName}; //variable
let SingleCluster = (clstr: string) //fixed
{
 cluster(clstr).database("sqlazure1").MonLogin
| where originalEventTimestamp between ((_startTime -7d).._endTime)
| where logical_server_name =~ _logical_Server and event =="process_login_finish" and package =~ "xdbgateway"
| distinct ClusterName
};
_ExecuteForProdClusters //fixed
| take 1
```

Note: 
1. There are 3 variables:
_startTime: issue start time, check with the user input. If no input, use the current date.
_endTime: issue end time, check with the user input.  If no input, use the current date.
_logical_Server: the SQL logical server name which is a short name, check with the user input.
2. Always Execute on: `https://sqladhoc.kusto.windows.net/sqlazure1`

##Step 2. Translate connectivity Ring name to a region keyword.
1. Take output of the above kusto query.
2. For example, the output is a SQL connectivity ring name, "cr18.eastus2-a.control.database.windows.net". Extract "eastus2-a" from the FQDN, then cut off "-a", the final region keyword is "eastus2".
For another example, if the output is "cr1.northeurope1-z.control.database.windows.net ", extract "northeurope1-z", then cut off "-z", final result would be "northeurope1".

Final Output: the Region Keyword