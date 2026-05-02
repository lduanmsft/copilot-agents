---
name: readonly-rca-statementsqlhash-singleton
description: Analyzes the ratio of statementSqlHash to queryHash to identify potential QDS issue.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Memory Overbooking Issues Skill

## Skill Overview

This skill analyzes the ratio of statementSqlHash to queryHash in Query Data Store (QDS) execution statistics. A high ratio indicates that ad-hoc queries are not being parameterized, which can lead to excessive memory and disk consumption, potentially causing QDS to enter read-only mode (readonlyReason 65536, 131072, or 262144). The analysis helps identify opportunities for query parameterization to improve QDS stability and performance.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |



## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let highRatioThreshold=3;
let RatioMessage = (dcount_statementSqlHash_all:long,dcount_queryHash_all:long,dcount_statementSqlHash_Captured:long,dcount_queryHash_Captured:long,readonly131072_Count:int)
{
let undecidedQueriesCount=dcount_statementSqlHash_all-dcount_statementSqlHash_Captured;
let Ratio_undecidedQueries_to_Captured=undecidedQueriesCount*1.0/dcount_statementSqlHash_Captured;
let Ratio_statementSqlHash_to_queryHash=round(dcount_statementSqlHash_all*1.0/dcount_queryHash_all,1);
let highUndicidedQueriesMessage=case( highRatioThreshold>Ratio_undecidedQueries_to_Captured,"",
strcat(" Please note, there were ",dcount_statementSqlHash_all," queries held in memory, waiting evaluation by QDS to determine if they were qualified to be persisted. However, only ",dcount_statementSqlHash_Captured," were ultimately persisted. ",
iff(readonly131072_Count==0,"Although QDS Readonly with ReadonlyReason 131072 didn't happen, that still consume StmtHashMapMemory"," This is one of the reason QDS ran into Readonly with ReadonlyReason 131072."),
iff(highRatioThreshold>Ratio_statementSqlHash_to_queryHash," .If this is an concern, "," Besides of parameterization, ")," You may consider reducing the capture_policy_stale_threshold_hours settting to reduce the StmtHashMap memory usage(avoding 13172).")
);
let sideEffectMessage="Such redundancy increases consumption of both disk space and memory resources, and may potentially cause QDS to enter read-only mode, triggered by various readonlyReason including 65536, 131072, and 262144. This issue is typically caused by ad-hoc queries that are not parameterized. Please engage customer's T-SQL developers to implement query parameterization. ";
let resourceUsageMessage=strcat("For this specifc Azure Db {LogicalServerName}, over the past 7 day up to the specified time period, a cumulative total of ",dcount_statementSqlHash_Captured," entries were persisted in the QDS, while ",dcount_statementSqlHash_all," entries have consumed BufferedItems/StmtHashMap Memory.");
let improvementMessage=case(dcount_queryHash_Captured>dcount_statementSqlHash_Captured,
strcat("Benefits of Parameterization:",resourceUsageMessage," If parameterization was fully implemented, the number of entries consuming BufferedItems/StmtHashMap/QDSRUNTIMESTATS Memory would drop from ",dcount_statementSqlHash_all," to ",dcount_queryHash_all,". That's a massive reduction in memory usage, which would greatly improve QDS stability and performance."),
strcat("Benefits of Parameterization:",resourceUsageMessage," If parameterization was fully implemented, the number of entries persisted to QDS would drop from ",dcount_statementSqlHash_Captured," to ",dcount_queryHash_Captured," and the number of entries consuming BufferedItems/StmtHashMap/QDSRUNTIMESTATS Memory would drop from ",dcount_statementSqlHash_all," to just ",dcount_queryHash_all,". That's a massive reduction in memory usage and storage overhead, which would greatly improve QDS stability and performance.")
);
case(
3>=Ratio_statementSqlHash_to_queryHash,strcat("The ratio of statement_sql_hash to query_hash is ",Ratio_statementSqlHash_to_queryHash,", which is within an acceptable range. This indicates that each query_hash corresponds to approximately ",Ratio_statementSqlHash_to_queryHash," times entries, either persisted in the QDS, consuming QDS related memory(StmtHashMap,BufferedItems and QDSRUNTIMESTATS Memory), or both. This is typically caused by queries issued with different drivers, ANSI settings or ad-hoc queries.",highUndicidedQueriesMessage),
Ratio_statementSqlHash_to_queryHash>3 and 6>=Ratio_statementSqlHash_to_queryHash,strcat("The ratio of statement_sql_hash to query_hash is ",Ratio_statementSqlHash_to_queryHash,", indicating that each query_hash corresponds to approximately ",Ratio_statementSqlHash_to_queryHash," times entries, either persisted in the QDS, consuming QDS related memory(StmtHashMap,BufferedItems and QDSRUNTIMESTATS Memory), or both. This is typically caused by queries issued with different drivers, ANSI settingor ad-hoc queries.",improvementMessage,highUndicidedQueriesMessage),
strcat("We observed a high ratio of statement_sql_hash to query_hash, measured at ",Ratio_statementSqlHash_to_queryHash,". This indicates that each query_hash corresponds to approximately ",Ratio_statementSqlHash_to_queryHash," times entries, either persisted in the QDS, consuming QDS related memory(StmtHashMap,BufferedItems and QDSRUNTIMESTATS Memory), or both. ",sideEffectMessage,improvementMessage,highUndicidedQueriesMessage )
)
};
let readonly131072_Count=toscalar(MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName=~'{LogicalServerName}'
| where event =~'query_store_stmt_hash_map_over_memory_limit' or (event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_StmtHashMapMemory')
| summarize count());
MonWiQdsExecStats
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName=~'{LogicalServerName}'
| summarize dcount_statementSqlHash_all=dcount(statement_sql_hash),dcount_queryHash_all=dcount(query_hash),
dcount_statementSqlHash_Captured=dcountif(statement_sql_hash,runtime_stats_exhaust_type=~'x_Captured'),
dcount_queryHash_Captured=dcountif(query_hash,runtime_stats_exhaust_type=~'x_Captured')
| extend ratioMessage=RatioMessage(dcount_statementSqlHash_all,dcount_queryHash_all,dcount_statementSqlHash_Captured,dcount_queryHash_Captured,readonly131072_Count)
| extend ratio1=round(dcount_statementSqlHash_all*1.0/dcount_queryHash_all,1)
| extend ratio2=round((dcount_statementSqlHash_all-dcount_statementSqlHash_Captured)*1.0/dcount_statementSqlHash_Captured,1)
| extend IssueDetected=iff(ratio1 >highRatioThreshold or ratio2>highRatioThreshold,'true','false')
| project ratioMessage,IssueDetected
```

#### Output
1. If the Task3 returns results, please display the exact message from the 'finalMessage' column without any modifications.
2. If the Task3 doesn't return any result, it indicates MonWiQdsExecStats doesn't have any data. Please display the following sentence exactly as written:"MonWiQdsExecStats doesn't have any data, we can't process the Ratio of statementSqlHash to queryHash analysis"

