---
name: error-40613-state-22
description: This skill focuses on diagnosing login error 40613 with state 22. 
---

## Background Information
In SQL Azure proxy login, Connection (a TCP-open task) from GW to backend DB is a slow IO and synchronous operations can cause delays and inefficiencies. Additionally, when a spike in proxy login workload occurs, involving multiple threads running the synchronous, slow I/O operations, Gateway can become stuck or unresponsive due to high thread count issue. To address these challenges, a dispatch pool is employed to throttle SOS worker usage under large volume workloads. This approach helps balance resource allocation and improve overall Gateway performance. To further optimize the dispatch pool, strategies such as limiting the number of request tasks for each Database sent to the pool, implementing a waiting queue for excess tasks, setting a maximum worker limit, introducing timeouts, and incorporating a fail-fast feature can be utilized.

Error 40613 state 22 typically indicates a proxy-login timeout.
Before a proxy-open is executed by the dispatcher-pool, there will be a timeout checking to examine if the proxy-open task has been pending for 25 seconds or more (configurable setting), if pending time is longer than the threshold (25 seconds), it will return error 40613 state 22 with lookup_state 1460, otherwise will continue with the TCP open to the target Tenant Ring node.

If TCP open fails, Gateway will return error 40613 state 22, with lookup_state containing the actual TCP open error, e.g. 10060 (TCP timeout).

An open task will be put in the pending list if more than 20 proxy opens (to the same xdbhost instance endpoint) is being executed. If the length of the pending list exceeds 500 (configurable setting), process_login_finish with error 40613 state 24 will be emitted and connection attempt will terminate.

One of the reasons that can cause 40613/22 error is SNAT port exhaustion on the Gateway node, refer **.github/skills/Connectivity/connectivity-scenarios/understand-snat/SKILL.md** for more information.

## 🚨🚨🚨 MANDATORY: access-eagleeye Network Analysis 🚨🚨🚨

**⛔ CRITICAL**: The `access-eagleeye` skill (`.github/skills/Connectivity/connectivity-utilities/access-eagleeye/SKILL.md`) is **MANDATORY** for Error 40613 State 22 investigations. 

**Why**: Error 40613/22 with lookup_state 10060 is a TCP timeout between Gateway and DB node. The most common root cause is a networking issue (SNAT exhaustion, load balancer probe failure, fabric/infrastructure network disruption). Skipping network analysis leaves the most likely root cause uninvestigated.

**When to execute**:
- **Single DB node impacted** → Run eagleeye between Gateway VMSS and the suspected DB node (Step 1.4.1 below)
- **Multiple DB nodes impacted** → Run eagleeye for at least 2 suspected DB nodes across different Tenant Rings (Step 2.3 below)
- **Only skip if**: All errors are explained by a confirmed non-network cause (e.g., authentication storm with error 18456, confirmed XDBHOST crash with process restart evidence)

## Narrowing down the impacted scope (MUST Follow)

### Step 1. Detect problems related to single Tenant Ring or database 
1. Use the skill **.github/skills/Connectivity/connectivity-base/determine-connectivity-ring/SKILL.md** to identify which Connectivity Rings are involved for the given logical server name/database name and time window. 

2. Once Connectivity Rings are identified, use the following Kusto query to analyze if the problem is related to single Tenant Ring or Database. Please replace the variables defined in the query, here is the sample query:

```
let StartTime=datetime(2026-01-22 21:30:00);
let EndTime= datetime(2026-01-22 22:30:00);
let ConnectivityRings = dynamic(["cr15.southcentralus1-a.control.database.windows.net", "cr14.southcentralus1-a.control.database.windows.net"]);
MonLogin
| where TIMESTAMP  between (StartTime..EndTime) 
| where ClusterName in~ (ConnectivityRings)
| where package == "xdbgateway"
| where error == 40613 and state == 22
| where event == "process_login_finish"
| extend TargetTRRing = substring(instance_name, indexof(instance_name, ".") + 1)
| extend instance = tostring( split(instance_name, ".")[0])
| where TargetTRRing != ""
| extend DBNode = tostring(split(fabric_node_name, "\\")[1])
| summarize count(), min(TIMESTAMP), max(TIMESTAMP) by instance, TargetTRRing, DBNode
```
Sample Output:
```
instance	TargetTRRing	DBNode	count_	min_TIMESTAMP	max_TIMESTAMP
cb8aa4b0e3a9	tr9591.southcentralus1-a.worker.database.windows.net	_DB_31	443	2026-01-22 21:30:03.5197190	2026-01-22 22:29:55.3699648
```
In this sample output, we can see all the errors are related to the same TargetTRRing and DBNode, which suggests the problem is likely related to this specific DB node or the connectivity between GWs and this DB node.

However, multiple impacted Tenant Rings or DB nodes typically represent a broader outage. If multiple impacted Tenant Rings or DB nodes are detected, you can skip to step 2 to further analyze the problem.

3. If single DB node is suspected, you can further analyze if the problem is related to huge login volume in a short time to this DB node.

Sample query:
```
let StartTime=datetime(2026-01-22 21:30:00);
let EndTime= datetime(2026-01-22 22:30:00);
let DBNode = "_DB_31";
let TargetTRRing= "tr9591.southcentralus1-a.worker.database.windows.net";
let ConnectivityRings = dynamic(["cr15.southcentralus1-a.control.database.windows.net", "cr14.southcentralus1-a.control.database.windows.net"]);
MonLogin
| where TIMESTAMP  between (StartTime..EndTime) 
| where ClusterName in~ (ConnectivityRings)
| where package == "xdbgateway"
| where fabric_node_name contains DBNode
| where event == "process_login_finish"
| where TargetTRRing =~ TargetTRRing
| summarize TotalLogins=count(), LoginWithError=countif(is_success == false) by instance_name,  bin(TIMESTAMP, 1m)
```
Note: 
1. DBNode, TargetTRRing can be refer to the output from previous query. ConnectivityRings can be refer to the output from previous skill "determine-connectivity-ring"
2. Must: Raise an alert if there is a sudden spike of login volume to this DB node in a short time. 
Threshold:If there are more than 2500 logins within 1 minute continuously, or if the login volume is much higher than normal baseline.

Sample output:
```
instance_name	TIMESTAMP	TotalLogins	LoginWithError
bb9a6cfb0c63.tr15993.southcentralus1-a.worker.database.windows.net	2026-01-22 19:05:00.0000000	4265	0
b6c3c0ceab2c.tr8937.southcentralus1-a.worker.database.windows.net	2026-01-22 19:05:00.0000000	1229	0
cb8aa4b0e3a9.tr9591.southcentralus1-a.worker.database.windows.net	2026-01-22 19:05:00.0000000	72498	51
f811c1832466.tr15373.southcentralus1-a.worker.database.windows.net	2026-01-22 19:05:00.0000000	1137	0
b5cc8fae6816.tr13202.southcentralus1-a.worker.database.windows.net	2026-01-22 19:05:00.0000000	1936	0
```
In this sample output, we can see the login volume to this specific instance "cb8aa4b0e3a9.tr9591.southcentralus1-a.worker.database.windows.net" is much higher than other instances, which suggests the problem is likely related to the huge login volume to this DB node.

3.1 If the problem is related to single instance with high login volume, you must verify if the high volume has some authentication related error, usually it start with error code 18456 with different state code. You can use the following query to verify:

```
let StartTime=datetime(2026-01-22 21:30:00);
let EndTime= datetime(2026-01-22 22:30:00);
let instancename= "cb8aa4b0e3a9.tr9591.southcentralus1-a.worker.database.windows.net";
MonLogin
| where TIMESTAMP  between (StartTime..EndTime) 
|where instance_name =~ instancename
| summarize min(TIMESTAMP), max(TIMESTAMP), count() by package, instance_name, strcat(error, "_",state), is_user_error
```
Note: instance_name can be refer to the output from previous query.

Sample output:
```
package	instance_name	Column1	is_user_error	min_TIMESTAMP	max_TIMESTAMP	count_
sqlserver	cb8aa4b0e3a9.tr9591.southcentralus1-a.worker.database.windows.net	18456_132	True	2026-01-22 21:36:39.4153275	2026-01-22 22:29:59.6315851	636931
```
In this sample output, we can see there are a huge amount of error 18456 with state 132, which indicates the login failure is related to authentication failure.

4. If the output only contains one DB node, but not due to high login volume, you can also analyze if the problem is related to DB node issue or the connectivity between GW and this DB node.

4.1 🚨 **MANDATORY** — follow **.github/skills/Connectivity/connectivity-utilities/access-eagleeye/SKILL.md** to check the connectivity between the Gateway VMSS and the suspected DB node. **Do NOT skip this step.** Only skip if you have 100% confidence from telemetry evidence that networking is not involved (e.g., confirmed authentication storm or XDBHOST crash). Even if Kusto queries for SLB or node health checks return results, the EagleEye check should still NOT be skipped.

4.2 To let user check if the problem is related to DB node issue, you can use the skill **.github/skills/Connectivity/connectivity-utilities/sql-connectivity-livesite-dashboard/SKILL.md** to generate a "VM Node dashboard" for the suspected DB node.




### Step 2. Verify problems related to multi Tenant Rings or DB nodes

1. Use sample query to verify:

```
let StartTime=datetime(2026-01-22 21:30:00);
let EndTime= datetime(2026-01-22 22:30:00);
let ConnectivityRings = dynamic(["cr15.southcentralus1-a.control.database.windows.net", "cr14.southcentralus1-a.control.database.windows.net"]);
MonLogin
| where TIMESTAMP  between (StartTime..EndTime) 
| where ClusterName in~ (ConnectivityRings)
| where package == "xdbgateway"
| where error == 40613 and state == 22
| where event == "process_login_finish"
| extend TargetTRRing = substring(instance_name, indexof(instance_name, ".") + 1)
| extend instance = tostring( split(instance_name, ".")[0])
| where TargetTRRing != ""
| extend DBNode = tostring(split(fabric_node_name, "\\")[1])
| summarize count(), min(TIMESTAMP), max(TIMESTAMP) by instance, TargetTRRing, DBNode
```

You may recieve errors from multiple TargetTRRing and DB nodes, which suggests the problem is likely related to a broader issue like a networking incident.

2. If multiple tenant ring or DB nodes impacted, check LoadBlancer avaliablity for all related Connnectivity Rings and Tenant Rings
refer to skill **.github/skills/Connectivity/connectivity-utilities/loadbalancer-health/SKILL.md** to check the LoadBalancer health status for all related Connectivity Rings and Tenant Rings.
If too many rings are involved, you can prioritize the rings with more errors to check first. At least check 2 connectivity rings and 2 tenant rings to see if there is a common pattern.

3. 🚨 **MANDATORY** — Generate EagleEye output for at least 2 suspected DB nodes in the involved Tenant Ring. Follow **.github/skills/Connectivity/connectivity-utilities/access-eagleeye/SKILL.md** to check if there is any networking problem between connectivity ring VMSS and DB nodes in different Tenant Rings. Checking the output, if there is a common pattern among different rings, it suggests the problem is likely related to a broader networking issue.

   **⛔ Do NOT skip this step.** Multi-node 40613/22 errors almost always indicate a networking incident. Only skip if you have 100% confidence from telemetry evidence (e.g., every impacted node shows a confirmed non-network root cause like bugcheck or XDBHOST crash).
