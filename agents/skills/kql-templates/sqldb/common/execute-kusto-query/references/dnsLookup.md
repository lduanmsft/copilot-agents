# Identify which region stores the telemetry for a given Logical server.
**Identify which region a logical server emits telemetry**
##Step 1. For any given logical server name, expand it for FQDN.  
For example, if the input servername is "iverxue-logisql", you get FQDN as "iverxue-logisql.database.windows.net"

##Step 2. Use PoweShell Resolve-DNS to locate the SQL region
 execute the sample command in powershell: 
```
$ResolveChain=Resolve-DnsName iverxue-logisql.database.windows.net -Type A
$CR=$ResolveChain[$ResolveChain.Count-1].name
$region = ($CR -split '\.')[1]
$regionKeyword = $region -replace '-[a-z]$'
```
Note:
1. "iverxue-logisql.database.windows.net" is a sample logical server name FQDN input. Format is "{logical_server_name}.database.windows.net"
2. In this sample, the $regionKeyword is "eastus2"


##Output 
The Output is the value of $regionKeyword