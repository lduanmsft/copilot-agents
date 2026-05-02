---
name: error-40613-state-84
description: This skill focuses on diagnosing login error 40613 with state 84. The error indicates the User DB could not access the master DB. The skill will guide you through troubleshooting steps to resolve this connectivity issue.
---

## Important:
1. MUST follow all the steps in this skill to accurately diagnose the cause of error 40613 with state 84. Skipping steps may lead to incorrect conclusions.
2. Output all the results from each step, even if you find an issue in the early steps. This information is crucial for a comprehensive analysis and to avoid missing any contributing factors.
3. Do not change any of the provided Kusto queries except for the variables at the top of each query. If you need to modify the queries, please document the changes and the reasons for those changes.

## Step 1: Determine where the user DB and master DB are located:

### Instruction: Run the kusto query e40613s84q100.kql
#### Input:
In the kusto query, the variables are:
servername: the logical server name of the database, based on input
dbname: the user database name, based on input 
masterdbname: the master database name, always "master"
startTime: the start time of the query range, based on the input
endTime: the end time of the query range, based on the input
### Sample Output:
database_name	min_TIMESTAMP	max_TIMESTAMP	instance	TargetTRRing	DBNode	count_
master	2026-02-28 05:00:04.5502913	2026-03-02 14:49:51.9368261	e2550b1949de	tr42788.westeurope1-a.worker.database.windows.net	_DB_57	16965
133710_104790	2026-02-28 06:00:06.5438459	2026-03-02 14:49:56.2998973	e585bc90bcac	tr41482.westeurope1-a.worker.database.windows.net	_DB_30	2276

In this example, you can know in the time range, the user DB (133710_104790) was on TR:tr41482.westeurope1-a.worker.database.windows.net, node: _DB_30, and the master DB was on TR:tr42788.westeurope1-a.worker.database.windows.net, node: _DB_57. The connection was from user DB to master DB through the connectivity ring. The output will be used in future steps.

## Step 2: Get details of the error 40613 with state 84:
### Instruction: Run the kusto query e40613s84q200.kql
#### Input:
servername: the logical server name of the database, based on input
dbname: the user database name, based on input 
startTime: the start time of the query range, based on the input
endTime: the end time of the query range, based on the input
### Sample Output:
```
TIMESTAMP	logical_server_name	database_name	error	state	is_contained_user	lookup_state	peer_address	xodbc_authentication_time_ms	connection_id	application_name	message	total_time_ms
2026-03-02 12:30:00.0000000	t08pite552	133710_104790	40613	84	True		178.230.111.x	23801	FC4EF645-7271-4E72-8D7A-7445A4DBBF6B	SnelStart	<waitstats><wait name="DISPATCHER_QUEUE_SEMAPHORE" requests="1" time="409" signalTime="0" maxTime="409"/><wait name="MEMORY_ALLOCATION_EXT" requests="9" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHENTICATIONOPS" requests="2" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHORIZATIONOPS" requests="1" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_CRYPTOPS" requests="5" time="1469" signalTime="0" maxTime="1469"/><wait name="PREEMPTIVE_OS_CRYPTACQUIRECONTEXT" requests="7" time="295" signalTime="0" maxTime="293"/><wait name="PREEMPTIVE_ODBCOPS" requests="3" time="23801" signalTime="0" maxTime="23797"/></waitstats>	23802
2026-03-02 14:30:00.0000000	t08pite552	133710_104790	40613	84	True		178.230.111.x	18233	9A52CA8B-A638-41E2-AD45-0443749C5F1E	SnelStart	<waitstats><wait name="DISPATCHER_QUEUE_SEMAPHORE" requests="1" time="339" signalTime="0" maxTime="339"/><wait name="MEMORY_ALLOCATION_EXT" requests="9" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHENTICATIONOPS" requests="2" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHORIZATIONOPS" requests="1" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_CRYPTOPS" requests="5" time="1334" signalTime="0" maxTime="1334"/><wait name="PREEMPTIVE_OS_CRYPTACQUIRECONTEXT" requests="7" time="299" signalTime="0" maxTime="298"/><wait name="PREEMPTIVE_ODBCOPS" requests="3" time="18233" signalTime="0" maxTime="18233"/></waitstats>	18235
2026-03-02 12:06:00.0000000	t08pite552	133710_104790	40613	84	True		178.230.111.x	16310	6575DA07-9351-4382-A3F3-C5C863B02C53	SnelStart	<waitstats><wait name="DISPATCHER_QUEUE_SEMAPHORE" requests="1" time="4849" signalTime="0" maxTime="4849"/><wait name="MEMORY_ALLOCATION_EXT" requests="9" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHENTICATIONOPS" requests="2" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHORIZATIONOPS" requests="1" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_CRYPTOPS" requests="5" time="2002" signalTime="0" maxTime="2002"/><wait name="PREEMPTIVE_OS_CRYPTACQUIRECONTEXT" requests="7" time="1613" signalTime="0" maxTime="1612"/><wait name="PREEMPTIVE_ODBCOPS" requests="3" time="16309" signalTime="0" maxTime="16309"/></waitstats>	16311
2026-03-02 12:21:00.0000000	t08pite552	133710_104790	40613	84	True		178.230.111.x	15526	75118E56-9A6F-431B-A63F-714A85B3765C	SnelStart	<waitstats><wait name="DISPATCHER_QUEUE_SEMAPHORE" requests="1" time="541" signalTime="0" maxTime="541"/><wait name="MEMORY_ALLOCATION_EXT" requests="13" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHENTICATIONOPS" requests="2" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHORIZATIONOPS" requests="1" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_CRYPTOPS" requests="7" time="3034" signalTime="0" maxTime="2666"/><wait name="PREEMPTIVE_OS_CRYPTACQUIRECONTEXT" requests="9" time="413" signalTime="0" maxTime="245"/><wait name="PREEMPTIVE_ODBCOPS" requests="3" time="15526" signalTime="0" maxTime="15526"/></waitstats>	15527
```

In this example, you can see the details of the error 40613 with state 84, including the peer address, connection id, application name, wait stats and total time spent on the error. This information can help you understand the context of the error and identify potential causes.

Take one or two samples with the highest total_time_ms, parse the message column (sample:  <waitstats><wait name="DISPATCHER_QUEUE_SEMAPHORE" requests="1" time="409" signalTime="0" maxTime="409"/><wait name="MEMORY_ALLOCATION_EXT" requests="9" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHENTICATIONOPS" requests="2" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_AUTHORIZATIONOPS" requests="1" time="0" signalTime="0" maxTime="0"/><wait name="PREEMPTIVE_OS_CRYPTOPS" requests="5" time="1469" signalTime="0" maxTime="1469"/><wait name="PREEMPTIVE_OS_CRYPTACQUIRECONTEXT" requests="7" time="295" signalTime="0" maxTime="293"/><wait name="PREEMPTIVE_ODBCOPS" requests="3" time="23801" signalTime="0" maxTime="23797"/></waitstats> ) to get the time spent on each wait type, and analyze which wait type is the most time-consuming. 

Also, take 2 connection_id with the longest total_time_ms, as an input in step 3. In this sample the connection_id are FC4EF645-7271-4E72-8D7A-7445A4DBBF6B, 9A52CA8B-A638-41E2-AD45-0443749C5F1E, and 6575DA07-9351-4382-A3F3-C5C863B02C53.

## Step 3: Check MonXOdbcWrapper log
### Instruction: Run the kusto query e40613s84q300.kql
#### Input:
startTime: the start time of the query range, based on the input
endTime: the end time of the query range, based on the input
ConnectionID: the connection_id with the longest total_time_ms from step 2, based on the input, can be multiple connection ids in an array format.

### Sample Output:
Output the "message" column. The message may contain additional error details or context that can help you identify the root cause of the connectivity issue.
Then, based on the output, there is a column named "odbc_cr_connection_id", try to use the output as another round of input to query the MonLogin table to see the connection handled by the master DB side. 

## Step 4: Check XODBC connection 
### Instruction: Run the kusto query e40613s84q400.kql
#### Input:
startTime: the start time of the query range, based on the input
endTime: the end time of the query range, based on the input
Cr_Connection_ID: the odbc_cr_connection_id from the output of step 3, based on the input, can be multiple connection ids in an array format.
### Sample Output:
Please output the result of this step. 
Sometimes, we can see Gateway node retruns error 17830 state 105, it indicates the GW (on the master DB side) killed the connection due to SNI readtimeout, probably user DB node cpu was high and LSASS couldn't do clienthello within 5 seconds. If you see the behavior, inform the user.

## Step 5: Check CPU core usage on DB node
### Instruction: Run the kusto query e40613s84q500.kql
#### Input:
startTime: the start time of the query range, based on the input
endTime: the end time of the query range, based on the input
TenantRing: the tenant ring where the user DB is located, from the output of e40613s84q100.kql in Step 1
DBNode: the DB node where the user DB is located, from the output of e40613s84q100.kql in Step 1

### Sample Output:
Please output the result of this step. 
Match the TIMESTAMP with the Kusto query output in Step 2 and determine whether there is a correlation with the occurrence of Error 40613/84.
Output your analysis. In the analysis, please mention which CPU cores had high usage, for example:

\Processor Information(0,13)
\Processor Information(1,20)

Use the "CounterName" column to identify the CPU cores.

Sometimes, we can see Gateway node retruns error 17830 state 105, it indicates the GW (on the master DB side) killed the connection due to SNI readtimeout, probably user DB node cpu was high and LSASS couldn't do clienthello within 5 seconds. If you see the behavior, inform the user.

## Step 6: Correlation analysis and CPU-Instance mapping verification (Critical)
### Instruction: Run the kusto query e40613s84q600.kql
#### Input:
The Kusto variables used are as follows:

_clustername: The cluster name where the user database is located
_nodename: The DB node where the user database is located
_startTime: Issue start time, based on user input
_endTime: Issue end time, based on user input
_high_cpu_cores: A dynamic array derived from the output of e40613s84q500.kql in **step 5**. For example: dynamic(["Processor Information(0,13)", "Processor Information(1,20)"]) 

Note: DO NOT change the rest of the query input.

### Sample Output:
The Kusto query output identifies instances mapped to the high‑CPU cores.
Instances are stored in the application_name column, for example, if the content is "fabric:/Worker.ISO.Premium/f2598a5543d5", then the instance is "f2598a5543d5". 
 Please match the kusto output with the instance of the user DB. Output your analysis.

If the user database instance contributes to the high CPU core usage, explicitly state this.
If not, identify which instance(s) are associated with the high‑CPU cores.

## Step 7: Check if the node that hosts the Master DB is under high load or not
"Refer to the skill: .github/skills/Connectivity/connectivity-utilities/xdbhost-metric-check/SKILL.md"

## Step 8: Generate an eagleeye output from the user DB to the master DB

1. Refer .github/skills/Connectivity/connectivity-utilities/determine-sql-node/SKILL.md to get the VirtualMachineUniqueId: 

-Source: User DB node VirtualMachineUniqueId
-Destination: Master DB node VirtualMachineUniqueId

2. Follow the `.github/skills/Connectivity/connectivity-utilities/access-eagleeye/SKILL.md` to generate the EagleEye output.
