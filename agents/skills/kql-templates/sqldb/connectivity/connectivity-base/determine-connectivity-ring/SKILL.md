---
name: determine-connectivity-ring
description: This skill helps identify which connectivity rings processed SQL logins.
---

## Basic Query
Unless the user specified a specific connectivity ring name in the input, use the following query to determine the connectivity ring(s) involved for the given logical server name/database name. 



```
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ "process_login_finish"
| where AppTypeName =~ "Gateway"
| summarize TotalLogins=count(), LoginWithError=countif(is_success == false), min(TIMESTAMP), max(TIMESTAMP) by ConnectivityRing=ClusterName
```

Output: 

1. Time Range and ConnectivityRing discovered
    Note: DO NOT out ConnectivityRing shortname (eg. cr14), please output the FQDN. Content in ConnectivityRing will be used in further steps.
2. Compare the Totallogins and LoginWithError, if the number on one ring is more than 2 times than the other one, notify user
3. Typically logins will be served by 2 connectivity rings in a data slice. If you see more than 2 rings, it suggests a slice migration happening there. In this case tell the user "A slice migration may have happened there. If your case is about a connection disruption, it may be related to the migration process."
