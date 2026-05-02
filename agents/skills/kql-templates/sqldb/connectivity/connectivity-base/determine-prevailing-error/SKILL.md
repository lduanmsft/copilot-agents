---
name: determine-prevailing-error
description: This skill screens prevailing error in the MonLogin table, trying to scope the errors' impact, such as on all connectivity rings, on single node, on single instance, etc.
---

## Determine Prevailing Error using kusto query
1. Use the following query to general screen the errors involved for the given logical server name/database name. 

```
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ "process_login_finish"
| where is_success == false 
| summarize min(originalEventTimestamp), max(originalEventTimestamp), count(), take_any(message, extra_info), avg(total_time_ms) by ClusterName,package, AppTypeName, is_success, is_user_error, error, state, state_desc, lookup_state, read_only_intent = toint(login_flags / 2097152) % 2
```

2. Analyze the kusto return:
2.1 Analyze error source.
Context: understand that normal SQL login flow is from user client --> xdbgateway(resides on Connectivity Ring\Gateway Node) --> xdbhost (Resides on Tenant Ring\DB node) --> sqlserver (Resides on Tenant Ring\DB nod)
Errors can be emited from one or multiple packages.
2.2 Analyze if the error is user error or system error, this can be idenitified under column "is_user_error"
2.3 Analyze the return of "avg_total_time_ms", identify if any component took much more time than others. take 4 seconds as a throshold.
If the time is long, Analysis the "message" and "extra_info" field from Monlogin to find out where the delay or timeout or broken happens.
For output, please emit a table of time take of each state, 
such as:
Process/Wait Type	Requests	Total Time (ms)	Max Time (ms)	Description
PREEMPTIVE_XHTTP	4	21,213	21,213	🚩 AAD HTTP authentication calls
DISPATCHER_QUEUE_SEMAPHORE	1	40	40	Login dispatcher queue wait
PWAIT_SECURITY_FEDAUTH_AADLOOKUP	7	0	0	AAD federated auth lookups
PREEMPTIVE_OS_AUTHENTICATIONOPS	1	0	0	OS authentication operations
PREEMPTIVE_OS_CRYPTOPS	1	0	0	Cryptographic operations
MEMORY_ALLOCATION_EXT	40	0	0	Memory allocations

2.4 Analyze other column such as count_, time window (min(originalEventTimestamp)~max(originalEventTimestamp))

3. Further narrow down to see if specific GW/DB node impacted

3.1 You can refer the following kusto query:

```
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ "process_login_finish"
| summarize min(originalEventTimestamp), max(originalEventTimestamp), TotalLogins=count(), LoginWithError=countif(is_success == false),  avg(total_time_ms) by ClusterName,NodeName, error, state
```

3.2 For specific node if you suspect a problem, you can refer a sample kusto query:

```
MonLogin
| where originalEventTimestamp between (datetime(2026-01-22 21:30:00)..datetime(2026-01-22 22:30:00)) 
| where logical_server_name =~ 'l0imreebat' and database_name =~ 'LogoBuilderShadow'
| where event =~ "process_login_finish"
| where ClusterName =~"tr9591.southcentralus1-a.worker.database.windows.net" and NodeName =~"_DB_31"
| summarize TotalLogins=count(), LoginWithError=countif(is_success == false),  avg(total_time_ms) by bin(TIMESTAMP,1m), strcat("error: ", error, "-state: ", state)
```
Note: originalEventTimestamp ,logical_server_name, database_name, ClusterName , NodeName can be replaced 

In this way, you can identify if specific node has problem and if the problem has a connection with login volume.

## Output
Output if any possible prevailing errors you found;
What is the impact radius of them;
Patten such as high login volume assosicated;
if you see any delay in the login
