
---
name: specific-query-wait-type-analysis
description: Analyze wait types for a specific query to identify performance bottlenecks and the top wait categories consuming query execution time.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Specific Query Top Wait Type Analysis

## Skill Overview

This skill analyzes wait types for a specific query identified by query_hash or query_id. It identifies the top wait categories that are consuming query execution time, helping diagnose performance bottlenecks such as CPU waits, parallelism issues, I/O waits, and other resource contentions.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |
| `{query_hash}` | The query hash to analyze | string | `0x73E64DD291EBBF6E` |
| `{query_id}` | The query ID to analyze | bigint | `12345` |
| `{TopN}` | Number of top wait types to analyze (default: 2) | int | `2` |



## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the Kusto query below | Always |
| Task 2 | Provide Suggestions Based on Top Wait Types | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
let WaitTypeSummary=(dcount_wait_category:int,TopWaitTypeNames:string,top1WaitTypeName:string,secondWaitTypeName:string,total_wait_time_ms:long,top1WaitType_wait_time_ms:long,secondWaitType_wait_time_ms:long)
{
let WaitTypeSummary_onlyOneWaitType=case(dcount_wait_category==1,strcat("The Top 1 Waitype of this query was ",top1WaitTypeName,", and this was the only waitType detected. The total wait time of ",total_wait_time_ms," milliseconds."),"");
let WaitTypeSummary_twoWaitType=case(dcount_wait_category==1,"",strcat("The top 2 wait types were:",TopWaitTypeNames,". The [",top1WaitTypeName,"] accounted ",top1WaitType_wait_time_ms, " milliseconds of wait time, representing ",round(top1WaitType_wait_time_ms*100.0/total_wait_time_ms,1),
"% of total; The second one [",secondWaitTypeName,"] account for ",round(secondWaitType_wait_time_ms*100.0/total_wait_time_ms,1),"% of the total wait time."));
strcat(WaitTypeSummary_onlyOneWaitType,WaitTypeSummary_twoWaitType)
//Sample output1:The top 2 wait types were:["PARALLELISM","CPU"]. The [PARALLELISM] accounted 1315363883 milliseconds of wait time, representing 70.1% of total; The second one [CPU] account for 13.6% of the total wait time.
};
let total_wait_time_ms=toscalar(MonWiQdsWaitStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where (isnotempty('{query_hash}') and query_hash =~ '{query_hash}') or (isnotempty({query_id}) and query_id == {query_id})
| summarize sum(total_query_wait_time_ms)
);
MonWiQdsWaitStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where (isnotempty('{query_hash}') and query_hash =~ '{query_hash}') or (isnotempty({query_id}) and query_id == {query_id})
| summarize individual_query_wait_time_ms=sum(total_query_wait_time_ms) by wait_category
| order by individual_query_wait_time_ms desc nulls first
| take {TopN}
| summarize dcount_wait_category=dcount(wait_category),TopWaitTypeNames=make_set(wait_category) ,(top1WaitType_wait_time_ms,top1WaitTypeName)=arg_max(individual_query_wait_time_ms,wait_category),(secondWaitType_wait_time_ms,secondWaitTypeName)=arg_min(individual_query_wait_time_ms,wait_category)
| extend waitTypeSummary=WaitTypeSummary(dcount_wait_category,TopWaitTypeNames,top1WaitTypeName,secondWaitTypeName,total_wait_time_ms,top1WaitType_wait_time_ms,secondWaitType_wait_time_ms)
| extend TopWaitTypeNames=strcat_array(TopWaitTypeNames, ";")
| project waitTypeSummary,TopWaitTypeNames
```

#### Output
Follow these instructions exactly. Only display output when specified:

1. Display the exact message from `waitTypeSummary` without any modification

2. **If the query returns empty results**: 
   - Display the following message exactly as written:
   - "Oops, telemetry data from the MonWiQdsWaitStats table does not exist. It appears the query executed extremely quickly, without being blocked or waiting on any resources."

### Task 2: Provide Suggestions Based on Top Wait Types

Based on the `Keywords` (TopWaitTypeNames) returned from Task 1, provide targeted troubleshooting suggestions using the mapping below.

#### Wait Category Suggestions Reference

| Wait Category | Description | Troubleshooting Suggestions |
|---------------|-------------|----------------------------|
| **UNKNOWN** | Unclassified wait types | Review system health, check for unusual activity patterns. Consider enabling extended events for deeper analysis. |
| **CPU** | CPU scheduling waits (SOS_SCHEDULER_YIELD) | Query is CPU-bound. Optimize query logic, review execution plan for expensive operators (sorts, hash joins), add appropriate indexes, consider query hints to reduce CPU usage. |
| **WORKERTHREADS** | Thread pool exhaustion (THREADPOOL) | SQL Server is running out of worker threads. Check for blocking chains, long-running queries, or consider increasing max worker threads. Review connection pooling settings. |
| **LOCK** | Lock contention (LCK_M_%) | Blocking is occurring. Identify blocking chains, optimize transaction scope, consider using READ COMMITTED SNAPSHOT isolation, review index strategy to reduce lock escalation. |
| **LATCH** | Non-buffer latch contention (LATCH_%) | Internal synchronization waits. Often related to tempdb contention or memory pressure. Check tempdb configuration, consider adding tempdb data files. |
| **BUFFERLATCH** | Buffer latch contention (PAGELATCH_%) | Hot page contention in memory. Common causes: last-page insert contention on identity columns, PFS/GAM/SGAM contention. Consider OPTIMIZE_FOR_SEQUENTIAL_KEY, hash partitioning, or reverse indexes. |
| **BUFFERIO** | Buffer I/O waits (PAGEIOLATCH_%) | Data is being read from disk rather than memory. Add more memory, optimize queries to read less data, improve indexing strategy, check disk I/O subsystem performance. |
| **COMPILATION** | Query compilation waits (RESOURCE_SEMAPHORE_QUERY_COMPILE) | Too many concurrent compilations. Reduce ad-hoc queries, use parameterized queries, increase memory for query compilation, review plan cache efficiency. |
| **SQLCLR** | CLR execution waits (CLR%, SQLCLR%) | CLR code is causing delays. Review CLR stored procedures/functions, optimize CLR code, consider converting to T-SQL if possible. |
| **MIRRORING** | Database mirroring waits (DBMIRROR%) | Mirroring synchronization delays. Check network latency between mirror partners, review mirror queue size, consider asynchronous mirroring for non-critical workloads. |
| **TRANSACTION** | Transaction-related waits (XACT%, DTC%, TRAN_MARKLATCH_%) | Distributed transaction or transaction log delays. Review transaction scope, minimize distributed transactions, check transaction log throughput. |
| **IDLE** | Idle/background waits (SLEEP_%, LAZYWRITER_SLEEP, etc.) | Generally not a concern - indicates idle time. If unexpected, check for application connection pooling issues. |
| **PREEMPTIVE** | Preemptive waits (PREEMPTIVE_%) | SQL Server is waiting on external resources (OS calls, linked servers, extended stored procedures). Review external dependencies, check linked server performance. |
| **SERVICEBROKER** | Service Broker waits (BROKER_%) | Service Broker queue processing delays. Review queue activation procedures, check for poison messages, optimize message processing logic. |
| **TRANLOGIO** | Transaction log I/O waits (LOGMGR, WRITELOG, etc.) | Transaction log write bottleneck. Move transaction log to faster storage, ensure log file is properly sized, check for frequent log flushes from small transactions. |
| **NETWORKIO** | Network I/O waits (ASYNC_NETWORK_IO, NET_WAITFOR_PACKET) | Client is not consuming results fast enough. Review client application, check network latency, optimize result set size, implement pagination. |
| **PARALLELISM** | Parallelism waits (CXPACKET, CXCONSUMER, EXCHANGE, etc.) | Parallel query execution overhead. Consider adjusting MAXDOP, review cost threshold for parallelism, check for skewed parallel distribution, optimize query to reduce parallel complexity. |
| **MEMORY** | Memory grant waits (RESOURCE_SEMAPHORE, CMEMTHREAD, etc.) | Memory pressure or excessive memory grants. Review queries with large memory grants, add indexes to reduce sorts/hashes, consider Resource Governor to limit memory grants. |
| **USERWAIT** | User-initiated waits (WAITFOR, WAIT_FOR_RESULTS) | Application is explicitly waiting. Review application logic for WAITFOR statements, check for intentional delays. |
| **TRACING** | Tracing/profiling waits (TRACEWRITE, SQLTRACE_%) | Extended events or profiler overhead. Reduce tracing scope, use lightweight events, disable unnecessary traces. |
| **FULLTEXTSEARCH** | Full-text search waits (FT_%, FULLTEXT GATHERER, MSSEARCH) | Full-text indexing or search delays. Review full-text index population schedule, optimize full-text queries, check FTHost process health. |
| **OTHERDISKIO** | Other disk I/O waits (ASYNC_IO_COMPLETION, IO_COMPLETION, BACKUPIO) | General disk I/O delays. Check disk subsystem health, review backup schedules, ensure adequate I/O bandwidth. |
| **REPLICATION** | Replication waits (SE_REPL_%, REPL_%, HADR_%) | Replication or Always On AG synchronization delays. Check network latency to replicas, review replica health, consider asynchronous commit for distant replicas. |
| **LOGRATEGOVERNOR** | Log rate governor waits (LOG_RATE_GOVERNOR, POOL_LOG_RATE_GOVERNOR, etc.) | Azure SQL Database log rate throttling. Reduce transaction log generation rate, batch small transactions, consider upgrading service tier for higher log throughput limits. |

#### Output Format

After displaying the `waitTypeSummary`, provide suggestions for each wait type found in `Keywords`. Note, this is Azure SQL DB instead of sql server on premise:

```
**Suggestions for [WaitTypeName]:**
- [Relevant suggestions from the table above]
```
