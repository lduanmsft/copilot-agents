---
name: determine-login-target
description: This skill would verify the target database node for the login requests based on the input logical server name/database name and time window. 
---

## Determine the target database node and tenant ring for the login requests

Use the following kusto query:

```
let _logical_server_name = '{LogicalServerName}';
let _database_name = '{LogicalDatabaseName}';
let _StartTime=datetime({StartTime});
let _EndTime= datetime({EndTime});
MonLogin
| where TIMESTAMP  between ((_StartTime -30min)..(_EndTime +30min) ) 
| where logical_server_name =~ _logical_server_name or LogicalServerName =~ _logical_server_name
| where database_name =~ _database_name
| where package == "xdbgateway"
| where event == "process_login_finish"
| extend TargetTRRing = substring(instance_name, indexof(instance_name, ".") + 1)
| extend instance = tostring( split(instance_name, ".")[0])
| where TargetTRRing != ""
| extend TargetDBNode = tostring(split(fabric_node_name, "\\")[1])
| summarize count(), min(TIMESTAMP), max(TIMESTAMP) by instance_name, TargetTRRing, TargetDBNode
```

## Output
Output the table result.
Aslo, remember the instance_name, TargetTRRing, TargetDBNode for each line, as they will be used in further steps.
