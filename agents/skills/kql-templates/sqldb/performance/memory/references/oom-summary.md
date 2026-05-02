---
name: oom-summary
description: This skill will check if SQL Server runs into Out of memory and deliver action plans
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug OUt of Memory(OOM)

## Skill Overview

This skill will check if SQL Server runs into Out of memory(OOM) and deliver action plans based on the oomCause and other factors

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

**This skill has 3 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute the OOM Summary Query | Always |
| Task 2 | Route based on oomCause | Always |
| Task 3 | Display Results | Always |

## Execution Steps

### Task 1: Execute the OOM Summary Query

If required variables (e.g., `{AppNamesOnly}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
MonSQLSystemHealth
| where AppName in ({AppNamesOnly})
| where originalEventTimestamp between(datetime({StartTime})..datetime({EndTime}))
| where event == "summarized_oom_snapshot"
| extend topClerks = parse_json(top_memory_clerks)
| extend topClerk = topClerks[0].clerk_type_name
| extend topPools = parse_json(top_memory_pools)
| extend topPool = topPools[0].pool_name
| extend top1Clerk_size_mb=tolong(topClerks[0]['page_allocated_mb'])+tolong(topClerks[0]['vm_committed_mb'])
| extend top1Pool_target_mb=tolong(topPools[0]['pool_target_mb'])
| extend ratioOftop1Clerk_poolTarget=round(top1Clerk_size_mb*100.0/top1Pool_target_mb,1)
| extend non_sos_usage_pct = non_sos_usage_mb * 100 / current_job_cap_mb
| extend oom_pool_name = parse_json(oom_memory_pool).pool_name
| extend is_oom_pool_system_pool = oom_pool_name !contains "SloSharedPool" and  oom_pool_name !contains "UserPool"
| extend oom_cause = iff(non_sos_usage_pct < 60 and oom_factor == 5 and is_oom_pool_system_pool, 10, oom_cause) 
| extend oomCause = case(oom_cause == 1, 'HEKATON_POOL_MEMORY_LOW', oom_cause == 2, 'MEMORY_LOW', oom_cause == 3, 'OS_MEMORY_PRESSURE',
oom_cause == 4, 'OS_MEMORY_PRESSURE_SQL', oom_cause == 5, 'NON_SOS_MEMORY_LEAK', oom_cause == 6, 'SERVERLESS_MEMORY_RECLAMATION',
oom_cause == 7, 'MEMORY_LEAK', oom_cause == 8, 'SLOW_BUFFER_POOL_SHRINK', oom_cause == 9, 'INTERNAL_POOL', oom_cause == 10, 'SYSTEM_POOL',
oom_cause == 11, 'QUERY_MEMORY_GRANTS', oom_cause == 12, 'REPLICAS_AND_AVAILABILITY', 'UNKNOWN')
| project originalEventTimestamp, ClusterName, NodeName, AppTypeName, instance_rg_size,
is_non_sos_usage_leaked, oom_factor, oomCause, available_physical_memory_mb, current_job_cap_mb, process_memory_usage_mb,
non_sos_usage_mb, committed_target_mb, committed_mb, allocation_potential_memory_mb,
topClerk,topPool, oom_memory_pool,ratioOftop1Clerk_poolTarget,leaked_memory_clerk
| summarize totalCount=count(),distinctNodes=dcount(NodeName),arg_min(originalEventTimestamp,topClerk,topPool,instance_rg_size,available_physical_memory_mb, current_job_cap_mb, process_memory_usage_mb,
non_sos_usage_mb, committed_target_mb, committed_mb, allocation_potential_memory_mb,oom_factor,ratioOftop1Clerk_poolTarget) by  AppTypeName,leaked_memory_clerk,oomCause,oom_memory_pool
| order by totalCount
```

**If query returns empty results**: Display "No OOM events detected during the investigation time window." and terminate.

### Task 2: Route based on oomCause

Follow the routing rules below based on the `oomCause` value from Task 1 query results.

#### 2.1 Direct oomCause Routing

| `oomCause` Value | Action |
|------------------|--------|
| `OS_MEMORY_PRESSURE_SQL` | Display the exact message: "Because the oomCause is OS_MEMORY_PRESSURE_SQL, please transfer to SQL DB Perf : InterProcessRG/ResourceLimits" |
| `OS_MEMORY_PRESSURE` | Display the exact message: "Because the oomCause is OS_MEMORY_PRESSURE, please transfer to SQL DB Perf : InterProcessRG/ResourceLimits" |
| `NON_SOS_MEMORY_LEAK` | Display the exact message: "Because the oomCause is NON_SOS_MEMORY_LEAK, please go to Recent known leaks impact SQL DBs" |
| `MEMORY_LEAK` | Display the exact message: "Because the oomCause is MEMORY_LEAK, please transfer to the appropriate queue based on leaked_memory_clerk: {leaked_memory_clerk}" |
| `SERVERLESS_MEMORY_RECLAMATION` | Display the exact message: "Because the oomCause is SERVERLESS_MEMORY_RECLAMATION, please go to MM0001-6-Serverless-OOMs" |
| `HEKATON_POOL_MEMORY_LOW` | Display the exact message: "Because the oomCause is HEKATON_POOL_MEMORY_LOW, please transfer to Hekaton Storage" |
| `REPLICAS_AND_AVAILABILITY` | Display the exact message: "Because the oomCause is REPLICAS_AND_AVAILABILITY, please transfer to SQL DB Availability" |

#### 2.2 QUERY_MEMORY_GRANTS Handling

If `oomCause` = `QUERY_MEMORY_GRANTS`:
- This indicates some queries required a large amount of memory grants
- **Check condition**: If `ratioOftop1Clerk_poolTarget` > 40% OR overall usage > 60% of SOS Target
- **Action**: Display the exact message: "Because the oomCause is QUERY_MEMORY_GRANTS, please transfer to SQL DB Perf : Query Processing"
- **CRITICAL — Identify the offending query**: You MUST also execute the [Top Memory Queries](/.github/skills/Performance/Queries/references/top-memory-queries.md) reference to identify which specific query hash(es) are consuming the memory grants. This uses `MonWiQdsExecStats` with `max_max_query_memory_pages` to find the actual queries. Without this step, the OOM analysis is incomplete — knowing the oomCause is `QUERY_MEMORY_GRANTS` is not actionable unless the offending query_hash and query_plan_hash are identified.

#### 2.3 SYSTEM_POOL, INTERNAL_POOL, or UNKNOWN Handling

If `oomCause` is one of: `SYSTEM_POOL`, `INTERNAL_POOL`, or `UNKNOWN`, evaluate in order:

| Condition | Check Value | Action |
|-----------|-------------|--------|
| Top memory pool is `DmvCollectorPoolOom` | `topPool` | Display the exact message: "Because the oomCause is {oomCause} and top memory pool is DmvCollectorPoolOom, please transfer to Telemetry, Monitoring, Runners" |
| Top memory pool is `InMemXdbLoginPool` | `topPool` | Display the exact message: "Because the oomCause is {oomCause} and top memory pool is InMemXdbLoginPool, please transfer to Gateway" |
| Top memory clerk is `OBJECTSTORE_SNI_PACKET` | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is OBJECTSTORE_SNI_PACKET, please transfer to Gateway" |
| Top memory clerk is `MEMORYCLERK_SQLTRACE` | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is MEMORYCLERK_SQLTRACE, please go to Recent known leaks impact SQL DBs" |
| Top memory clerk is `MEMORYCLERK_SQLFABRIC` | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is MEMORYCLERK_SQLFABRIC, please go to Recent known leaks impact SQL DBs" |
| Top memory clerk is `USERSTORE_SCHEMAMGR` | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is USERSTORE_SCHEMAMGR, please go to Recent known leaks impact SQL DBs" |
| Top memory clerk is `OBJECTSTORE_LOCK_MANAGER` | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is OBJECTSTORE_LOCK_MANAGER, please go to MM0001-2-Large-OBJECTSTORE_LOCK_MANAGER-usage" |
| Top memory clerk is `MEMORYCLERK_SQLSTORENG` AND during recovery | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is MEMORYCLERK_SQLSTORENG during recovery, please transfer to Storage Engine (PVS, CTR, AM, Logging, Recovery, XFCB)" |
| Top memory clerk is `MEMORYCLERK_PARALLEL_REDO` | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is MEMORYCLERK_PARALLEL_REDO, please transfer to Storage Engine (PVS, CTR, AM, Logging, Recovery, XFCB)" |
| Top memory clerk is `MEMORYCLERK_XTP` AND usage > 60% of SOS target | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is MEMORYCLERK_XTP with usage > 60% of SOS target, please transfer to Hekaton Storage" |
| Top memory clerk is `USERSTORE_SXC` | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is USERSTORE_SXC, please go to MM0001-7 Large USERSTORE_SXC usage" |
| Top memory clerk is `OBJECTSTORE_SERVICE_BROKER` | `topClerk` | Display the exact message: "Because the oomCause is {oomCause} and top memory clerk is OBJECTSTORE_SERVICE_BROKER, please transfer to SQL DB Availability" |

#### 2.4 MEMORY_LOW Handling

If `oomCause` = `MEMORY_LOW`:
- **Default recommendation**: Display the exact message: "Because the oomCause is MEMORY_LOW, please suggest customer to update SLO"

Then evaluate top memory clerk for additional routing:

| Top Memory Clerk | Additional Condition | Action |
|------------------|---------------------|--------|
| `MEMORYCLERK_SQLQERESERVATIONS` | User Pool usage > 50% of target OR overall > 60% of SOS Target | Display the exact message: "Because the oomCause is MEMORY_LOW and top memory clerk is MEMORYCLERK_SQLQERESERVATIONS, please transfer to SQL DB Perf : Query Processing" |
| `MEMORYCLERK_SQLQUERYEXEC` | User Pool usage > 30% of target OR overall > 60% of SOS Target | Display the exact message: "Because the oomCause is MEMORY_LOW and top memory clerk is MEMORYCLERK_SQLQUERYEXEC, please transfer to SQL DB Perf : Query Processing" |
| `CACHESTORE_OBJCP` | - | Display the exact message: "Because the oomCause is MEMORY_LOW and top memory clerk is CACHESTORE_OBJCP, please transfer to SQL DB Perf: Frontend" |
| `CACHESTORE_SQLCP` | - | Display the exact message: "Because the oomCause is MEMORY_LOW and top memory clerk is CACHESTORE_SQLCP, please transfer to SQL DB Perf: Frontend" |

#### 2.5 Fallback for Unmatched Conditions

Display this exact message verbatim:

> "Please reach out to the SQL SOS team for assistance or try the bluebird-mcp-sql to investigate the issue further."

**⚠️ DO NOT** explain why the fallback was triggered, list the unmatched conditions, or provide any reasoning. Just display the message above exactly as written.


### Task 3: Display Results

Display **ONLY** the following information (do NOT add additional metrics, tables, or sections):
1. `oomCause` value
2. Top memory clerk: `topClerk`
3. Top memory pool: `topPool`
4. `ratioOftop1Clerk_poolTarget` percentage
5. Recommended action based on the routing rules in Task 2

**⚠️ RESTRICTION**: Do NOT display extra fields from the query results (such as `current_job_cap_mb`, `process_memory_usage_mb`, `ClusterName`, `NodeName`, etc.) unless they are explicitly listed above or needed to evaluate routing conditions in Task 2.
