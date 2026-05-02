---
name: brain-low-login-success-rate
description: BRAIN SLI Login Success Rate alerts fire when the ratio of successful login attempts to total login attempts for Azure SQL Databases over a defined window drops below the defined SLI threshold (only system‑caused login failures are counted as failures). These incidents require the DRI to determine whether the success rate drop is caused by service-side issues (Gateway, DB node) or platform.
---


## Step 1. Parse ICM Title and context for BRAIN Alert context
With the ICM ID provided, parse the following information from the ICM title and description to determine the context of the BRAIN alert:
1. Region
Sample title: [BRAIN detected an unusual trend in SLI "Login Success-Rate - Azure SQL DB" for SQL Database  in West US]
So the region is West US. Please note the region is important as it will help us determine which Kusto cluster to query for telemetry data.

2. Start Time
3. End Time

## Step 2. Convert the region to the corresponding Kusto cluster

Use the following Kusto query to find the cluster:

```sample kusto
let _inputRegion = "West US"; //input the Region parsed from ICM title
let _clustername = cluster('sqlstage.kusto.windows.net').database('sqlazure1').MonSQLTenantSnapshot // always query from sqlstage.kusto.windows.net
|distinct AzureRegion , Region
| where AzureRegion =~ _inputRegion
| extend _cluster= tolower(Region)
| distinct _cluster;
cluster('sqladhoc.kusto.windows.net').database('sqlazure1').KustoConnectionConfiguration // always query from sqladhoc.kusto.windows.net
| extend ClusterName = tolower(ClusterName)
| where ClusterName in (_clustername)
| project DataSource, InitialCatalog
| take 1
```

Sample output:
DataSource	InitialCatalog
https://sqlazurewus1.kusto.windows.net:443	sqlazure1
The Kusto cluster URI is in the DataSource column, and the database is in the InitialCatalog column. In this example, the Kusto cluster URI is https://sqlazurewus1.kusto.windows.net:443 and the database is sqlazure1.

For the rest of the steps, please follow the instructions in the skill `execute-kusto-query` to execute Kusto queries on the correct cluster to analyze the login success rate issue.

## Step 3. Analyze the login success rate issue on Connectivity Rings

3.1 Output connectivity rings with high system error rates:

``` Sample Kusto Query
let _startTime = datetime(2026-04-10T03:50:00Z);
let _endTime = datetime(2026-04-10T13:40:00Z);
 MonLogin 
| where TIMESTAMP between (_startTime .._endTime )
| where package =~ "xdbgateway" and AppName == "Gateway"
| where event == "process_login_finish"
| extend LoginResult = iff(is_success == 1, 'Success', iff(is_user_error == 0 or total_time_ms > 10000, 'SystemError', 'UserError'))
| summarize Total=count(), SysErr=  countif(LoginResult == "SystemError") by ClusterName
| extend SysErrRate =  round(100.0 * todouble(SysErr) / todouble(Total), 2)
| sort by SysErrRate desc 
```

Note: _startTime and _endTime should be the start time and end time parsed from the ICM title/description. 

Sample Results:
ClusterName	Total	SysErr	SysErrRate
cr16.eastus2-a.control.database.windows.net	21338280	54691	1.03
cr18.eastus2-a.control.database.windows.net	21639638	42252	1.02
cr22.useuapeast2-a.control.database.windows.net	233864	12	0.01
cr2.useuapeast2-z.control.database.windows.net	23420	0	0
cr21.useuapeast2-a.control.database.windows.net	230014	11	0

Output: Entries with SysErrRate higher than 1% are considered as having a significant impact on the login success rate. Please identify if there are any connectivity rings with high system error rates and investigate further into those rings for potential issues.

3.2 For the connectivity rings with high system error rates, analyze the error code and error state distribution and target Tenant Rings and DB nodes with high error rates for further investigation.


``` Sample Kusto Query
let _startTime = datetime(2026-04-10T03:50:00Z);
let _endTime = datetime(2026-04-10T13:40:00Z);
let _cr = dynamic([
    "cr16.eastus2-a.control.database.windows.net",
    "cr18.eastus2-a.control.database.windows.net"
]);
 MonLogin 
| where TIMESTAMP between (_startTime .._endTime )
| where  ClusterName in~ (_cr)
| where event == "process_login_finish" and is_user_error == 0 and is_success == 0 and error >0
| extend TargetTRRing = substring(instance_name, indexof(instance_name, ".") + 1)
| summarize count() by err=strcat("error:",error, " state:", state ), cr_node=strcat(ClusterName, ":", NodeName), TargetTRRing, fabric_node_name
| summarize impacted_cr_nodes=dcount(cr_node), sum(count_) by err, TargetTRRing, fabric_node_name
| sort by sum_count_ desc , impacted_cr_nodes desc 
```

Note: 
1. _startTime and _endTime should be the start time and end time parsed from the ICM title/description. 
2. _cr should be the list of ClusterName with high system error rates identified from the previous query.

Sample Results:

err	TargetTRRing	fabric_node_name	impacted_cr_nodes	sum_count_
error:40613 state:4			168	20291
error:40613 state:22	tr14923.eastus2-a.worker.database.windows.net	DB00000A\_DB_10	84	1050
error:40613 state:22	tr51623.eastus2-a.worker.database.windows.net	DB000014\_DB_40	150	521
error:40613 state:22	tr51623.eastus2-a.worker.database.windows.net	DB00001I\_DB_54	106	198

Analyze the top 4 error code and state distribution to identify if there are specific error codes and states that are more prevalent. Also, identify if there are specific Tenant Rings and DB nodes that are more impacted by the login failures. This will help narrow down the investigation to specific areas in the infrastructure.

In this sample, error code 40613 state 4 indicates the Gateway node is not able to locate the backend SQL instance for the login request, which is likely a SQL alias DB related issue, and that is the reason why we are not seeing a specific Tenant Ring and DB node for that error code and state. 

## Step 4. Use output from the above analysis and refer to a skill

Refer to .github/skills/Connectivity/connectivity-scenarios/login-failure/SKILL.md, start from "6: Determine the prevailing error and the scope" and finish all rest of the steps in that skill.

## Step 5. Output
5.1 Drill Calendar link: https://global.azure.com/drillmanager/calendarView 
This is a MUST output to have the user to check if there is any ongoing or recent maintenance activities for the region. 

5.2 Service Health Dashboard: https://portal.microsoftgeneva.com/s/ABEE2745?overrides=[{"query":"//*[id='Region']","key":"value","replacement":""}]%20
This is a MUST output.

5.3 Top 2 loadbalancer health metrics according to skill:
.github/skills/Connectivity/connectivity-utilities/loadbalancer-health/SKILL.md
This is a MUST check.

5.4 Top 2 EagleEye analysis for the impacted Tenant Ring and DB node:
.github/skills/Connectivity/connectivity-utilities/access-eagleeye/SKILL.md
This is a MUST check.

5.5 All remaining findings in Step 4
