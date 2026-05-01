# KQL Extraction Report — SQLLivesiteAgents Performance Skills (Batch 2)
# Categories: BLOCKING, MEMORY, COMPILATION, OUT-OF-DISK, MISCELLANEOUS, SQLOS, QUERY-STORE

---

# ═══════════════════════════════════════════════════════════════
# 1. BLOCKING
# ═══════════════════════════════════════════════════════════════

## 1.1 blocking-detection.md
- **Path**: `/.github/skills/Performance/Blocking/references/blocking-detection.md`
- **Name**: `blocking-detection`
- **Description**: Detect and analyze blocking
- **Severity Levels**: Small (≤1%), Moderate (1-2%), Massive (2-10%), Severe (10-30%), Extremely Severe (>30%)
- **Threshold**: blockeeSessionPercent based on worker thread capacity (WorkersLimitPerDB)
- **IssueDetected**: blockeeSessionPercent > 1 (or true if capacity unavailable)

### KQL Query 1 — Peak Blocking Detection
```kql
let BlockingStatus = (blockeeSessionPercent: real) {
    case(
    blockeeSessionPercent <= 1, "Small blocking detected, and You may run the skill 'Lead Blocker Sessions' to get more details if the blocking is a concern.",
    blockeeSessionPercent > 1 and blockeeSessionPercent <= 2, "Moderate blocking detected.",
    blockeeSessionPercent > 2 and blockeeSessionPercent <= 10, "Massive blocking detected. Please note that this condition may lead to noticeable performance issues, including but not limited to query slowness, timeouts, and deadlocks.",
    blockeeSessionPercent > 10 and blockeeSessionPercent <= 30, "Severe blocking detected! Please note that this condition may result in significant performance degradation, including but not limited to query slowness, timeouts, deadlocks and CPU usage decreasing.",
    "Extremely severe blocking detected! Please note that this condition may lead to worker thread exhaustion, potentially impacting system stability."
    )
    };
let WorkersLimitPerDB=(MonDmDbResourceGovernance
| where PreciseTimeStamp>datetime_add('day',-2,datetime({StartTime})) and PreciseTimeStamp<datetime_add('day',2,datetime({EndTime}))
| where LogicalServerName =~ '{LogicalServerName}' and database_name  =~ '{LogicalDatabaseName}'
| extend WorkersLimitPerDB = primary_group_max_workers
| extend WorkersLimitPerPool = primary_pool_max_workers
| summarize  WorkersLimitPerPool = take_any(WorkersLimitPerPool), WorkersLimitPerDB = take_any(WorkersLimitPerDB) by AppName
| project WorkersLimitPerDB  ,AppName);
MonBlockedProcessReportFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| extend monitorLoop = extract('monitorLoop=\x22([0-9]+)\x22',1,blocked_process_filtered, typeof(int))
| parse blocked_process_filtered with anystr3:string '<blocked-process>' blockee '</blocked-process>' discard1
| parse blocked_process_filtered with anystr4:string'<blocking-process>' blocker '</blocking-process>' discard2
| extend blockee_session_id = extract('spid=\x22([0-9]+)\x22', 1, blockee, typeof(int))
| extend blocker_session_id = extract('spid=\x22([0-9]+)\x22', 1, blocker, typeof(int))
| project originalEventTimestamp,monitorLoop,blockee_session_id,blocker_session_id,AppName
| summarize blockees = make_set(blockee_session_id), blockers = make_set(blocker_session_id),timestamp=format_datetime(min(originalEventTimestamp),'yyyy-MM-dd HH:mm:ss') by monitorLoop,AppName
| extend MergedList = array_concat(blockees, blockers)
| summarize blockingSessionArray=make_set(MergedList),arg_min(timestamp,blockees) by monitorLoop,AppName
| extend  blockingChainSessionCount= array_length(blockingSessionArray)
| extend  blockeeSessionCount= array_length(blockees)
| where blockeeSessionCount>0
| project-away blockingSessionArray
| order by blockeeSessionCount desc
| take 1
| join kind=leftouter (WorkersLimitPerDB) on AppName
| extend blockeeSessionPercent = iff(isnull(WorkersLimitPerDB) or WorkersLimitPerDB == 0, real(-1), round(100.0*blockeeSessionCount/WorkersLimitPerDB,1))
| extend IssueDetected = iff(blockeeSessionPercent < 0, true, blockeeSessionPercent > 1)
| extend blockingStatus = iff(blockeeSessionPercent < 0, 
    strcat("Blocking detected but worker thread capacity is unavailable. The peak BLOCKING occurred at ", timestamp, ", ", blockeeSessionCount, " session(s) were blocked. Unable to calculate percentage due to missing resource governance data."),
    strcat(BlockingStatus(blockeeSessionPercent), " The peak BLOCKING occurred at ", timestamp, ", ", blockeeSessionCount, " session(s) were blocked, accounting for ", blockeeSessionPercent, "% of the total capacity(", WorkersLimitPerDB, ")."))
```

### KQL Query 2 — Blocking Events Distribution (Hourly)
```kql
MonBlockedProcessReportFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize BlockingEventCount=count() by bin(originalEventTimestamp, 1h)
| order by originalEventTimestamp asc
```

---

## 1.2 deadlock-detection.md
- **Path**: `/.github/skills/Performance/Blocking/references/deadlock-detection.md`
- **Name**: `deadlock-detection`
- **Description**: Detect and analyze deadlocks
- **IssueDetected**: TotalDeadlocks > 5

### KQL Query 1 — Deadlock Summary
```kql
let DeadlockData = MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered';
let HourlyAvg = toscalar(DeadlockData 
    | summarize count() by bin(originalEventTimestamp, 1h)
    | summarize avg(count_));
DeadlockData
| summarize TotalDeadlocks = count(), 
            FirstDeadlock = min(originalEventTimestamp), 
            LastDeadlock = max(originalEventTimestamp)
| extend HourlyAverage = round(HourlyAvg, 1)
| extend IssueDetected = TotalDeadlocks > 5
```

### KQL Query 2 — Deadlock Distribution (15-min intervals)
```kql
let Interval = 15min;
MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered'
| summarize DeadlockCount = count() by bin(originalEventTimestamp, Interval)
| order by originalEventTimestamp asc
```

### KQL Query 3 — Hourly Deadlock Summary
```kql
MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered'
| summarize DeadlockCount = count() by bin(originalEventTimestamp, 1h)
| order by originalEventTimestamp asc
```

---

## 1.3 lead-blocker-sessions.md
- **Path**: `/.github/skills/Performance/Blocking/references/lead-blocker-sessions.md`
- **Name**: `lead-blocker-sessions`
- **Description**: Find the lead blocking header session IDs (root of the blocking chain)
- **Required Extra Param**: `{monitorLoop}` — the specific monitor loop to analyze

### KQL Query — Lead Blocker Sessions
```kql
// Find lead blocker session IDs for a specific monitorLoop
// Lead blockers are sessions that appear as blocker_session_id but NOT as blockee_session_id
MonBlockedProcessReportFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| extend monitorLoop = extract('monitorLoop=\x22([0-9]+)\x22',1,blocked_process_filtered, typeof(int))
| parse blocked_process_filtered with anystr3:string '<blocked-process>' blockee '</blocked-process>' discard1
| parse blocked_process_filtered with anystr4:string'<blocking-process>' blocker '</blocking-process>' discard2
| extend blockee_session_id = extract('spid=\x22([0-9]+)\x22', 1, blockee, typeof(int))
| extend blockee_status = extract('status=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_status = iff(isempty(blockee_status) or isnull(blockee_status), "NULL", blockee_status)
| extend blockee_transactionid = extract('xactid=\x22([0-9]+)\x22', 1, blockee, typeof(long))
| extend blockee_frames = extract(@'\s*<stackFrames>\s*(.*?)\s*</stackFrames>\s*', 1, blockee, typeof(string))
| extend blockee_waittime_ms = extract('waittime=\x22([0-9]+)\x22', 1, blockee, typeof(int))
| extend blockee_transactionname = extract('transactionname=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_clientapp = extract('clientapp=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_clientapp = iff(isempty(blockee_clientapp) or isnull(blockee_clientapp), "NULL", blockee_clientapp)
| extend blockee_trancount = extract('trancount=\x22([0-9]+)\x22', 1, blockee, typeof(int))
| extend blockee_lasttranstarted = extract('lasttranstarted=\x22(.*?)\x22', 1, blockee, typeof(datetime))
| extend blockee_queryhash = extract('queryhash=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_isolationlevel = extract('isolationlevel=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blockee_lastbatchstarted = extract('lastbatchstarted=\x22(.*?)\x22', 1, blockee, typeof(datetime))
| extend blockee_lastbatchcompleted = extract('lastbatchcompleted=\x22(.*?)\x22', 1, blockee, typeof(datetime))
| extend blockee_waitresource = extract('waitresource=\x22(.*?)\x22', 1, blockee, typeof(string))
| extend blocker_session_id = extract('spid=\x22([0-9]+)\x22', 1, blocker, typeof(int))
| extend blocker_waitresource = extract('waitresource=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_status = extract('status=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_status = iff(isempty(blocker_status) or isnull(blocker_status), "NULL", blocker_status)
| extend blocker_clientapp = extract('clientapp=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_clientapp = iff(isempty(blocker_clientapp) or isnull(blocker_clientapp), "NULL", blocker_clientapp)
| extend blocker_trancount = extract('trancount=\x22([0-9]+)\x22', 1, blocker, typeof(int))
| extend blocker_transactionid = extract('xactid=\x22([0-9]+)\x22', 1, blocker, typeof(long))
| extend blocker_frames = extract(@'\s*<stackFrames>\s*(.*?)\s*</stackFrames>\s*', 1, blocker, typeof(string))
| extend blocker_queryhash = extract('queryhash=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_isolationlevel = extract('isolationlevel=\x22(.*?)\x22', 1, blocker, typeof(string))
| extend blocker_lastbatchstarted = extract('lastbatchstarted=\x22(.*?)\x22', 1, blocker, typeof(datetime))
| extend blocker_lastbatchcompleted = extract('lastbatchcompleted=\x22(.*?)\x22', 1, blocker, typeof(datetime))
| where isnotnull(blocker_session_id) and isnotnull(blockee_session_id)
| where monitorLoop=={monitorLoop}
| summarize arg_max(originalEventTimestamp, blockee_waittime_ms,blockee_transactionid,blockee_isolationlevel,blockee_clientapp,blockee_queryhash,blockee_waitresource,blockee_lastbatchstarted,
blockee_lastbatchcompleted,blocker_waitresource,blocker_transactionid,blocker_trancount, blocker_status,blocker_isolationlevel,blocker_clientapp,blocker_queryhash,blocker_waitresource,blocker_lastbatchstarted,blocker_lastbatchcompleted)
by monitorLoop,blockee_session_id,blocker_session_id
```

---

## 1.4 long-running-transactions.md
- **Path**: `/.github/skills/Performance/Blocking/references/long-running-transactions.md`
- **Name**: `long-running-transactions`
- **Description**: Analyze and debug long running transactions in Azure SQL Database
- **Threshold**: duration > 1 hour flagged for attention

### KQL Query — Long Running Transactions
```kql
MonDmTranActiveTransactions
| where {AppNamesNodeNamesWithPreciseTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and (user_db_name =~ '{LogicalDatabaseName}' or 4>= database_id)
| extend category = iff(user_db_name == 'tempdb', 'tempdb', iff(accessed_tempdb == 0, 'user_db', 'user_db_with_accessed_tempdb'))
| extend duration_hour = round((end_utc_date - transaction_begin_time) / time(1h),1)
| extend negativeSessionCount=0>session_id
| extend IsSystemTask=program_name in ('DmvCollector', 'TdService', 'BackupService', 'MetricsDownloader')
| summarize max_duration_hour = arg_max(duration_hour,
session_id,
transaction_begin_time,
transaction_type,
transaction_state,
IsSystemTask,
status,
accessed_tempdb,category,
report_time = end_utc_date)
by transaction_id,negativeSessionCount
| summarize count(),max(max_duration_hour),avg(max_duration_hour),percentile(max_duration_hour,50) by IsSystemTask,accessed_tempdb,negativeSessionCount
| summarize totalCount=sum(count_), negativeSessionCount=sumif(count_,negativeSessionCount==true),systemTaskSessionCount=sumif(count_,IsSystemTask==true),max_duration_hour=max(max_max_duration_hour),avg_duration_hour=round(avg(avg_max_duration_hour),1),median_duration_hour=round(avg(percentile_max_duration_hour_50),1)
| where totalCount>0
| project totalCount, max_duration_hour, avg_duration_hour, median_duration_hour, systemTaskSessionCount, negativeSessionCount
```

---

## 1.5 top-deadlock-queries.md
- **Path**: `/.github/skills/Performance/Blocking/references/top-deadlock-queries.md`
- **Name**: `top-deadlock-queries`
- **Description**: Display the top N query hashes involved in deadlocks
- **Extra Param**: `{TopN}` — number of deadlock events to analyze

### KQL Query 1 — Top Deadlock Queries (by event)
```kql
MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered'
| extend Complete_Deadlock_Graph = trim_end(@'[ \t\r\n]+', xml_report_filtered) endswith '</deadlock>'
| order by Complete_Deadlock_Graph desc nulls last, originalEventTimestamp desc nulls last
| take {TopN}
| extend Complete_Deadlock_Graph = iff(Complete_Deadlock_Graph == 1, 'true', 'false')
| project originalEventTimestamp, xml_report_filtered, NodeName, Complete_Deadlock_Graph
| extend query_hashes = extract_all(@'queryhash=\x22([^\s]+)\x22', xml_report_filtered)
| extend query_plan_hashes = extract_all(@'queryplanhash=\x22([^\s]+)\x22', xml_report_filtered)
| extend query_hashes = set_difference(query_hashes, dynamic(['0x0000000000000000']))
| extend query_plan_hashes = set_difference(query_plan_hashes, dynamic(['0x0000000000000000']))
| extend query_hashes = iif(array_length(query_hashes) > 0, query_hashes, '')
| extend query_plan_hashes = iif(array_length(query_plan_hashes) > 0, query_plan_hashes, '')
| project originalEventTimestamp, NodeName, Complete_Deadlock_Graph, query_hashes, query_plan_hashes
```

### KQL Query 2 — Aggregate Query Hash Frequency
```kql
MonDeadlockReportsFiltered
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where event =~ 'xml_deadlock_report_filtered'
| extend query_hashes = extract_all(@'queryhash=\x22([^\s]+)\x22', xml_report_filtered)
| extend query_hashes = set_difference(query_hashes, dynamic(['0x0000000000000000']))
| mv-expand query_hash = query_hashes to typeof(string)
| where isnotempty(query_hash)
| summarize DeadlockCount = count(), 
            FirstOccurrence = min(originalEventTimestamp), 
            LastOccurrence = max(originalEventTimestamp) 
    by query_hash
| order by DeadlockCount desc
| take 10
```

---

# ═══════════════════════════════════════════════════════════════
# 2. MEMORY
# ═══════════════════════════════════════════════════════════════

## 2.1 overbooking.md
- **Path**: `/.github/skills/Performance/memory/references/overbooking.md`
- **Name**: `overbooking`
- **Description**: Debug Memory Overbooking issue (MRG/DRG detection)

### KQL Query 1 — MRG Detection
```kql
MonRgManager
| where {NodeNamesWithOriginalEventTimeRange}
| where event == 'multi_instance_mem_rg_recliam_target'
| where multi_instance_mem_rg_instance_name has_any ({AppNamesOnly})
| summarize count=count()
```

### KQL Query 2 — DRG Detection
```kql
MonRgManager
| where {NodeNamesWithOriginalEventTimeRange}
| where event == 'dynamic_rg_cap_change' and resource=='MEMORY'
| extend AppName = extract(@"/([^/]+)/\(Code,SQL\)", 1, instance_name)
| where AppName has_any ({AppNamesOnly})
| summarize count=count()
```

---

## 2.2 oom-summary.md
- **Path**: `/.github/skills/Performance/memory/references/oom-summary.md`
- **Name**: `oom-summary`
- **Description**: Check if SQL Server runs into Out of memory and deliver action plans
- **Routing**: Complex oomCause-based routing to different teams

### KQL Query — OOM Summary
```kql
MonSQLSystemHealth
| where AppName in ({AppNamesOnly})
| where originalEventTimestamp between(datetime({StartTime})..datetime({EndTime}))
| where event == "summarized_oom_snapshot"
| extend topClerks = parse_json(top_memory_clerks)
| extend topPools = parse_json(top_memory_pools)
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
topClerks[0], topClerks[1], topClerks[2], topPools[0], oom_memory_pool,ratioOftop1Clerk_poolTarget,leaked_memory_clerk
```

---

## 2.3 bufferpool-decrease.md
- **Path**: `/.github/skills/Performance/memory/references/bufferpool-decrease.md`
- **Name**: `bufferpool-decrease`
- **Description**: Check if MEMORYCLERK_SQLBUFFERPOOL had decreased ≥ 20%
- **Threshold**: warningThreshold = 20 (percent drop)

### KQL Query — Buffer Pool Drop Detection
```kql
let AggInterval_do_NOT_change = time(5m);
let warningThreshold=20;
MonSqlMemoryClerkStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName=~'{LogicalServerName}'
| where memory_clerk_type =~'MEMORYCLERK_SQLBUFFERPOOL'
| summarize MemoryInMB=sum(pages_kb)/1024 by bin(originalEventTimestamp, AggInterval_do_NOT_change),process_id
| extend timestamp=format_datetime(originalEventTimestamp, 'yyyy-MM-dd HH:mm')
| project timestamp, MemoryInMB,process_id
| order by timestamp asc
| serialize
| extend prevMemoryInMB = prev(MemoryInMB),prevProcess_id=prev(process_id),prevTimestamp=prev(timestamp)
| project timestamp,prevTimestamp,MemoryInMB,prevMemoryInMB,dropInMB=prevMemoryInMB-MemoryInMB,prevProcess_id,process_id
| extend percentage=round(dropInMB*100.0/prevMemoryInMB,1)
| where dropInMB >0
| where percentage >=warningThreshold
| where prevProcess_id==process_id//filter out sql restart
| summarize count=count(),arg_max(dropInMB,percentage,prevMemoryInMB,prevTimestamp,MemoryInMB,timestamp)
```

### KQL Query — Buffer Pool Timechart (verification)
```kql
let AggInterval_do_NOT_change = time(5m);
MonSqlMemoryClerkStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName=~'{LogicalServerName}'
| where memory_clerk_type =~'MEMORYCLERK_SQLBUFFERPOOL'
| summarize MemoryInMB=sum(pages_kb)/1024 by bin(originalEventTimestamp, AggInterval_do_NOT_change)
| order by originalEventTimestamp asc nulls first
| render timechart
```

---

# ═══════════════════════════════════════════════════════════════
# 3. COMPILATION
# ═══════════════════════════════════════════════════════════════

## 3.1 failed-compilation-summary.md
- **Path**: `/.github/skills/Performance/Compilation/references/failed-compilation-summary.md`
- **Name**: `failed-compilation-summary`
- **Description**: Display failed compilation queries

### KQL Query 1 — Total Failed Compilations
```kql
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed, 16)))
| where event =~'failed_compilation'
| summarize FailedCount=count()
| where FailedCount > 0
```

### KQL Query 2 — Failed Compilation by Error Code
```kql
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed, 16)))
| where event =~'failed_compilation'
| summarize FailedCount=count() by error_code
```

### KQL Query 3 — Failed Compilation by Query Hash with CPU/Duration
```kql
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed, 16)))
| where event =~'failed_compilation'
| summarize compile_cpu_ms=sum(compile_cpu),compile_duration_ms=sum(compile_duration),FailedCount=count() by query_hash
```

---

## 3.2 cpu-usage-of-failed-compilation.md
- **Path**: `/.github/skills/Performance/Compilation/references/cpu-usage-of-failed-compilation.md`
- **Name**: `cpu-usage-of-failed-compilation`
- **Description**: Analyze CPU usage from failed query compilations
- **Threshold**: CPU_Percent >= 10 → IssueDetected

### KQL Query — Failed Compilation CPU %
```kql
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event =~'failed_compilation'
| summarize compile_cpu_ms=sum(compile_cpu)
| project CPU_Percent = round(100.0 * (compile_cpu_ms/{SumCpuMillisecondOfAllApp}), 1)
| extend IssueDetected=CPU_Percent>=10
| extend ResultMessage = iff(IssueDetected == 'True', 
    strcat("Failed compilation consumed a significant amount of CPU resources, accounting for {CPU_Percent}%. Identifying high CPU usage from failed query compilations"),
    strcat("Failed compilation didn't consume a significant amount of CPU resources, with usage at {CPU_Percent}%"))
```

---

## 3.3 cpu-usage-of-successful-compilation.md
- **Path**: `/.github/skills/Performance/Compilation/references/cpu-usage-of-successful-compilation.md`
- **Name**: `cpu-usage-of-successful-compilation`
- **Description**: Analyze CPU usage from successful query compilations
- **Threshold**: CPU_Percent >= 10 → IssueDetected

### KQL Query — Successful Compilation CPU %
```kql
MonWiQueryParamData
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend compile_code=iff(compile_code =='Success','Compilation','Recompile')
| summarize compile_cpu_time_ms=sum(compile_cpu_time+auto_update_stats_cpu_time)/1000
| project CPU_Percent = round(100.0 * (compile_cpu_time_ms/{SumCpuMillisecondOfAllApp}), 1)
| extend IssueDetected = CPU_Percent >= 10
| extend ResultMessage = iff(IssueDetected == 'True', 
    strcat("Successful compilation consumed a significant amount of CPU resources, accounting for ", CPU_Percent, "%. Identifying high CPU usage from query compilations."),
    strcat("Successful compilation did not consume a significant amount of CPU resources, with usage at ", CPU_Percent, "%"))
```

---

## 3.4 query-compile-gateway.md
- **Path**: `/.github/skills/Performance/Compilation/references/query-compile-gateway.md`
- **Name**: `query-compile-gateway`
- **Description**: Detect query compilation waiting for gateway resources
- **Severity**: Minor (1-5), Moderate (6-20), Significant (21-50), Severe (>50) based on max_waiter_count

### KQL Query — Compile Gateway Detection
```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where message has_cs 'Gateway' and message has_cs 'MSR-'
| extend name = extract('(.*)Value', 1, message, typeof(string))
| extend max_count = extract('Configured Units[ ]+([0-9]+)', 1, message, typeof(int))
| extend available_count = extract('Available Units[ ]+([0-9]+)', 1, message, typeof(int))
| extend active_count = extract('Acquires[ ]+([0-9]+)', 1, message, typeof(int))
| extend waiter_count = extract('Waiters[ ]+([0-9]+)', 1, message, typeof(int))
| extend threshold_mb = round(extract('Threshold[ ]+([0-9]+)', 1, message, typeof(long)) / 1024.0 / 1024, 1)
| where active_count > 0 and waiter_count > 0
| summarize max_max_count = max(max_count), max_waiter_count = max(waiter_count), max_active_count = max(active_count), min_originalEventTimestamp = min(originalEventTimestamp), max_originalEventTimestamp = max(originalEventTimestamp)
 by CompileGatewayName = name, NodeName
```

---

## 3.5 top-failed-compilation-ranked-by-cpu-usage.md
- **Path**: `/.github/skills/Performance/Compilation/references/top-failed-compilation-ranked-by-cpu-usage.md`
- **Name**: `top-failed-compilation-ranked-by-cpu-usage`

### KQL Query — Top Failed Compilations by CPU
```kql
MonQueryProcessing
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend query_hash = strcat('0x', toupper(tohex(query_hash_signed, 16)))
| where event =~'failed_compilation'
| summarize compile_cpu_ms=sum(compile_cpu),compile_duration_ms=sum(compile_duration) by query_hash
| order by compile_cpu_ms desc
| take {TopN}
```

---

## 3.6 top-successful-compilation-ranked-by-cpu-usage.md
- **Path**: `/.github/skills/Performance/Compilation/references/top-successful-compilation-ranked-by-cpu-usage.md`
- **Name**: `top-successful-compilation-ranked-by-cpu-usage`

### KQL Query — Top Successful Compilations by CPU
```kql
MonWiQueryParamData
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| extend compile_duration_sec=round(compile_duration/1000.0/1000,1)
| extend compile_cpu_time_sec=round(compile_cpu_time/1000.0/1000,1)
| extend compile_memory_mb=round(compile_memory/1024,1)
| summarize count=count(),max_compile_duration_sec=max(compile_duration_sec),max_compile_cpu_time_sec=max(compile_cpu_time_sec) by query_hash
| project-reorder max_compile_cpu_time_sec,max_compile_duration_sec,count
| order by max_compile_cpu_time_sec desc
| take {TopN}
```

---

# ═══════════════════════════════════════════════════════════════
# 4. OUT-OF-DISK
# ═══════════════════════════════════════════════════════════════

## 4.1 drive-out-of-space.md
- **Threshold**: drive_usage_percentage >= 96 → IssueDetected

### KQL Query — Drive Usage
```kql
MonRgLoad
| extend originalEventTimestamp = originalEventTimestampFrom
| extend AppName = tostring(split(application_name, '/')[-1])
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where event == 'directory_quota_report_load' and target_directory endswith 'work\\data'
| extend drive_name = substring(target_directory, 4, 3)
| summarize by drive_name,ClusterName, application_name, NodeName, target_directory, event
| join kind = inner (
                      MonRgLoad
                      | extend originalEventTimestamp = originalEventTimestampFrom
                      | where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
                      | where event == 'drive_usage_report_load' and drive_name != '' and drive_capacity_in_bytes > 0
                      | where ClusterName in ({HistoricalTenantRingNames}) and NodeName in ({NodeNames})
                      | summarize arg_max(round(drive_usage_percentage, 1), originalEventTimestampFrom) by ClusterName, NodeName, drive_name, drive_capacity_in_gb = toint(drive_capacity_in_bytes / 1024.0 / 1024 / 1024), drive_usage_alert_threshold_percentage
 ) on ClusterName, NodeName, drive_name
| project originalEventTimestampFrom, NodeName, drive_name, drive_capacity_in_gb, drive_usage_percentage, drive_available_space_gb = toint(drive_capacity_in_gb*(100-drive_usage_percentage)/100.0), drive_usage_alert_threshold_percentage, target_directory, application_name, ClusterName
| extend IssueDetected=drive_usage_percentage>=96
```

## 4.2 directory-quota-hit-limit.md

### KQL Query — Directory Quota
```kql
MonRgLoad
| extend originalEventTimestamp = originalEventTimestampFrom
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| extend AppName = split(application_name, '/')[-1]
| where AppName in ({AppNamesOnly})
| where event =~ 'directory_quota_report_load'
| extend quota_limit_in_GB = quota_limit_in_bytes/1024.0/1024/1024, quota_usage_in_GB = quota_usage_in_bytes/1024.0/1024/1024
| summarize arg_max(quota_usage_in_GB, *) by NodeName
| extend QuotaLimitHit = iff(quota_usage_in_GB >= quota_limit_in_GB, 1, 0)
| summarize sum(QuotaLimitHit)
| extend DirectoryQuotaLimitHit = sum_QuotaLimitHit > 0
| project DirectoryQuotaLimitHit
```

## 4.3 data-or-log-reached-max-size.md

### KQL Query 1 — Max Size Hit Detection
```kql
MonSqlRgHistory
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~'{LogicalServerName}' 
| where event =~ 'aggregated_virtual_files_io_history'
| where (type_desc =~ 'ROWS' or type_desc =~ 'LOG')
| where (database_id > 4 and database_id < 32700) or database_id == 2
| extend size_on_disk_GB = round(size_on_disk_bytes / 1024.0 / 1024 / 1024, 0),
         max_size_GB = round(max_size_mb / 1024.0, 0)
| summarize max(max_size_GB), max(size_on_disk_GB) by type_desc, file_id, database_id,db_name
| extend MaxSizeHit = iff(max_size_on_disk_GB >= max_max_size_GB, 1, 0)
| summarize MaxSizeHit = avg(MaxSizeHit) by database_id, type_desc
| summarize maxif(MaxSizeHit, database_id != 2 and type_desc =~ 'ROWS'),
            maxif(MaxSizeHit, database_id != 2 and type_desc =~ 'LOG'),
            maxif(MaxSizeHit, database_id == 2 and type_desc =~ 'ROWS'),
            maxif(MaxSizeHit, database_id == 2 and type_desc =~ 'LOG')
| extend UserdbDataMaxSizeHit = maxif_MaxSizeHit == 1,
         UserdbLogMaxSizeHit = maxif_MaxSizeHit1 == 1,
         TempdbDataMaxSizeHit = maxif_MaxSizeHit2 == 1,
         TempdbLogMaxSizeHit = maxif_MaxSizeHit3 == 1
| project UserdbDataMaxSizeHit, UserdbLogMaxSizeHit, TempdbDataMaxSizeHit, TempdbLogMaxSizeHit
```

### KQL Query 2 — File Size Details (conditional)
```kql
let AggInterval_do_NOT_change = time(15m);
MonSqlRgHistory
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where event == 'aggregated_virtual_files_io_history'
| where LogicalServerName =~ '{LogicalServerName}' and db_name =~ '{LogicalDatabaseName}'
| summarize file_space_used_gb = round(sum(spaceused_mb / 1024.0), 1),
            file_space_reserved_gb = round(sum(size_on_disk_bytes / 1024.0 / 1024.0 / 1024.0), 1),
            maximum_gb = sum(max_size_mb / 1024.0)
   by type_desc, bin(originalEventTimestamp, AggInterval_do_NOT_change)
| summarize max(file_space_used_gb), max(file_space_reserved_gb) by maximum_gb, type_desc
| where max_file_space_reserved_gb>=maximum_gb and max_file_space_used_gb>=maximum_gb
| project type_desc, maximum_gb, max_file_space_reserved_gb, max_file_space_used_gb
```

### KQL Query 3 — Log Truncation Holdup (conditional on log full)
```kql
MonFabricThrottle
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| where log_truncation_holdup !~ 'NoHoldup'
| summarize count(), min(TIMESTAMP), max(TIMESTAMP) by log_truncation_holdup, NodeName, ClusterName
```

## 4.4 has-out-of-space-issue.md
- **Error Codes**: 3257, 9002, 5149, 1105, 1101

### KQL Query — Space Allocation Failures in Errorlog
```kql
MonSQLSystemHealth
| where PreciseTimeStamp between ((datetime({StartTime}) - 12h) .. datetime({EndTime}))
| where AppName in {AppNamesOnly}
| where event in ('errorlog_written', 'systemmetadata_written') and (message contains 'Error: 3257' or message contains 'Error: 9002' or message contains 'Error: 5149' or message contains 'Error: 1105' or message contains 'Error: 1101')
| extend required_space = extract('requires ([0-9]+)', 1, message, typeof(real)) / 1024 / 1024 / 1024
| extend available_space = extract('only ([0-9]+)', 1, message, typeof(real)) / 1024 / 1024 / 1024
| extend errorMessage=substring(message,124,strlen(message))
| summarize StartTime = min(PreciseTimeStamp),(LastSeenTime, RequiredSpaceGB, AvailableSpaceGB) = arg_max(PreciseTimeStamp, required_space, available_space, errorMessage, error_id) by AppName, ClusterName, NodeName
| project AppName, NodeName, AvailableSpaceGB, RequiredSpaceGB, LastSeenTime, errorMessage, ErrorId=error_id, ClusterName, StartTime, sourceName = 'MonSQLSystemHealth aka Errorlog'
| top 10 by LastSeenTime desc
```

## 4.5 tempdb-full-analysis.md

### KQL Query — Tempdb Full Detection
```kql
let AllocationErrorCount=toscalar( MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where error_id in (1101,1104,1105,5149)
| count
);
let AggInterval_do_NOT_change = time(15m);
let TempdbFileFullResult = MonSqlRgHistory
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event=='aggregated_virtual_files_io_history'
| where database_id == 2
| where type_desc =~'ROWS'
| where AllocationErrorCount>0
| summarize
spaceused_gb = round(sum(spaceused_mb / 1024.0),1),
size_on_disk_gb = round(sum(size_on_disk_bytes / 1024.0 / 1024.0 / 1024.0),1),
max_size_gb=round(sum(max_size_mb/1024.0),1)
by  type_desc, bin(originalEventTimestamp, AggInterval_do_NOT_change)
| project originalEventTimestamp,file_type=type_desc,spaceused_gb,size_on_disk_gb,max_size_gb
| where size_on_disk_gb==max_size_gb
| extend Timestamp=originalEventTimestamp
| summarize Timestamp=max(Timestamp),countTempdbFileFull=count();
TempdbFileFullResult
| extend IssueDetected = countTempdbFileFull > 0
| extend ResultMessage = iff(countTempdbFileFull > 0, 
    strcat("Tempdb database file was full, with first occurrence around ", format_datetime(Timestamp, 'yyyy-MM-dd HH:mm'), "."),
    "Tempdb is not full.")
| project Timestamp, countTempdbFileFull, IssueDetected, ResultMessage
```

## 4.6 out-of-space-nodes.md
- **Same KQL as has-out-of-space-issue.md** (identical query)

## 4.7 xstore-error-analysis.md

### KQL Query — XStore Error Analysis
```kql
let ErrorMessage=(totalCount: int,errorcodeArray:string,
count_TopError: int,mapped_errorcode: int,dcount_errorcode: int
)
{
let noErrorMessage="We didn't detect any XStore related errors.";
let summary=strcat(
"The Azure DB Storage run into error ",totalCount, iif(totalCount == 1, " time", " times"),
" with ",dcount_errorcode, iif(dcount_errorcode == 1, " single error ", " different errors"),errorcodeArray,".");
let topError=iif(dcount_errorcode ==1,"",
strcat(" The top error was ",mapped_errorcode, ", happening ",count_TopError, iif(count_TopError == 1, " time", " times")));
iif(totalCount == 0, noErrorMessage, strcat(summary,topError))
};
MonSQLXStore
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~ '{LogicalServerName}'
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where event =='xio_failed_request'
| where file_path contains '.mdf' or file_path contains '.ndf' or file_path contains '.ldf'
| summarize count_=count() by mapped_errorcode
| summarize totalCount=sum(count_),errorcodeArray=make_set(mapped_errorcode),count_TopError=arg_max(count_, mapped_errorcode),dcount_errorcode=dcount(mapped_errorcode)
| extend errorMessage=ErrorMessage(totalCount,errorcodeArray,count_TopError,mapped_errorcode,dcount_errorcode)
| project errorMessage
```

---

# ═══════════════════════════════════════════════════════════════
# 5. MISCELLANEOUS
# ═══════════════════════════════════════════════════════════════

## 5.1 worker-thread-exhaustion-analysis.md

### KQL Query — Worker Thread Exhaustion
```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where message contains 'The request limit for the database' or message contains 'The request limit for the elastic pool'
| summarize count=count() by bin(originalEventTimestamp,1h)
| order by originalEventTimestamp asc
```

## 5.2 worker-session-similarity-analysis.md
- **Threshold**: similarity > 0.9 → IssueDetected (cosine similarity)

### KQL Query — Worker-Session Cosine Similarity
```kql
let SimilarityMessage=(similarity: real)
{
let highSimilarityMessage="The pattern of worker threads and sessions is very similar. The increased number of worker threads may be caused by sessions spawned by user applications. Please review the ASC Report 'Database Resource Consumption Statistics' to confirm.";
let noCorrelationMessage="No correlation between worker threads and session spike has been detected.";
iif(similarity > 0.9, highSimilarityMessage, noCorrelationMessage)
};
MonDmRealTimeResourceStats
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
| summarize Max_Worker = max(max_worker_percent), Max_Session = max(max_session_percent) by bin(originalEventTimestamp, 15s)
| sort by originalEventTimestamp asc nulls last
| summarize workers=make_list(Max_Worker),sessions=make_list(Max_Session)
| extend similarity = series_cosine_similarity(workers, sessions)
| extend resultMessage=SimilarityMessage(similarity)
| project resultMessage, similarity, IssueDetected=similarity > 0.9
```

## 5.3 database-corruption-detection.md
- **Error IDs**: 211, 823, 824, 825, 829, 2533, 2570, 2576, 3203, 7985, 7989, 8909, 8914, 8916, 8928, 8939, 8942, 8948, 8964, 8965, 8978, 8992, 8998, 8999

### KQL Query A — Non-Hyperscale
```kql
MonSQLSystemHealth
| where AppName in ({AppNamesOnly})
| where LogicalServerName =~ '{LogicalServerName}'
| where error_id in (211,823,824,825,829,2533,2570,2576,3203,7985,7989,8909,8914,8916,8928,8939,8942,8948,8964,8965,8978,8992,8998,8999) 
| summarize totalCount=count(),dcount=dcount(error_id),StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp)
| summarize count(),take_any(message),StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp) by error_id,NodeName
```

### KQL Query B — Hyperscale
```kql
let appNames=materialize (
MonSocrates
| where  (originalEventTimestamp between (datetime({StartTime})..datetime({EndTime})))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where isnotempty(foreign_file_id)
| summarize by AppName,AppTypeName
);
MonSQLSystemHealth
| where  (originalEventTimestamp between (datetime({StartTime})..datetime({EndTime})))
| where LogicalServerName =~ '{LogicalServerName}' 
| join kind=inner(appNames) on AppName
| where error_id in (211,823,824,825,829,2533,2570,2576,3203,7985,7989,8909,8914,8916,8928,8939,8942,8948,8964,8965,8978,8992,8998,8999) 
| summarize count(),take_any(message),StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp) by error_id,NodeName
```

## 5.4 akv-error-detection.md
- **AKV Error IDs**: 33183, 37412, 33184, 37542, 37566-37574, 37576, 40981, 45320-45330, 45362, 45415, 45463, 45472, 45494, 45532, 45538, 45539, 45654, 45656, 45720, 45731, 45746, 45747, 49981

### KQL Query A — Non-Hyperscale
```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and AppName in ({AppNamesOnly})
| where error_id in (33183 , 37412,33184,37542,37566,37567,37568,37569,37570,37571,37572,37573,37574,37576,40981,45320,45321,45322,45324,45325,45326,45327,45329,45330,45362,45415,45463,45472,45494,45532,45538,45539,45654,45656,45720,45731,45746,45747,49981)
| summarize count=count(), message=take_any(message), StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp) by error_id,NodeName
| order by count desc
```

### KQL Query B — Hyperscale
```kql
let appNames=materialize (
MonSocrates
| where  (originalEventTimestamp between (datetime({StartTime})..datetime({EndTime})))
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where isnotempty(foreign_file_id)
| summarize by AppName,AppTypeName
);
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| join kind=inner(appNames) on AppName
| where error_id in (33183 , 37412,33184,37542,37566,37567,37568,37569,37570,37571,37572,37573,37574,37576,40981,45320,45321,45322,45324,45325,45326,45327,45329,45330,45362,45415,45463,45472,45494,45532,45538,45539,45654,45656,45720,45731,45746,45747,49981)
| summarize count=count(), message=take_any(message), StartTime=min(originalEventTimestamp), EndTime=max(originalEventTimestamp) by error_id,NodeName
| order by count desc
```

## 5.5 sql-restart-and-failover-detection.md

### KQL Query — Restart/Failover Detection
```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithPreciseTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| summarize StartTime=min(PreciseTimeStamp), EndTime=max(PreciseTimeStamp) by process_id, NodeName
| order by StartTime asc
```

## 5.6 kill-command.md

### KQL Query — Kill Command Detection
```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithPreciseTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where message contains "Kill"
| summarize KillEventCount=count() by bin(PreciseTimeStamp, 1h)
| order by PreciseTimeStamp asc
```

## 5.7 azure-profiler-trace.md

### KQL Query — Azure Profiler Traces
```kql
let rg_server_traces =(MonRgManager
| where {ApplicationNamesNodeNamesWithOriginalEventTimeRange}
| where event =='rg_process_azure_profiler_request'
| where is_success==1
| extend trace_name = tostring(split(message, ':', 1)[0])
| extend trace_name = replace_regex(trace_name, @'\s+', '')
| extend trace_name = trim('"', trace_name)
| project TIMESTAMP,application_name, trace_name,NodeName,ClusterName);
let casCommand_traces=(MonManagement
| extend ClusterName = ring_name
| extend NodeName = node_name
| extend application_name
| where {NodeNamesWithOriginalEventTimeRange}
| where event =~ 'cas_workflow_take_azure_profiler_trace_complete'
| extend trace_name = strcat(NodeName,'_',ClusterName)
| project TIMESTAMP, application_name, trace_name,NodeName,ClusterName);
union rg_server_traces,casCommand_traces
| project-away ClusterName
| order by TIMESTAMP asc
```

## 5.8 analyze-azure-profiler-trace.md
- **No KQL query** — uses external CLI tool `azure-profiler-mcp.exe`
- PowerShell command:
```powershell
& "$env:USERPROFILE\.dotnet\tools\azure-profiler-mcp.exe" get-hottest-methods `
    --group   "{group}" `
    --role    "{traceName}" `
    --date    "{date}" `
    --process "{process}" `
    --sort    exclusive `
    --top     {topN}
```

## 5.9 xevent-session-detection.md

### KQL Query — XEvent Sessions
```kql
let mapping=datatable(buffer_flush_policy:long, EVENT_RETENTION_MODE:string, buffer_flush_policyName:string) 
[ 
    0, 'ALLOW_SINGLE_EVENT_LOSS', 'XESBP_DROP_EVENT', 
    1, 'NO_EVENT_LOSS', 'XESBP_BLOCK', 
    2, 'Unknown', 'XESBP_ALLOC', 
    3, 'ALLOW_MULTIPLE_EVENT_LOSS', 'XESBP_DROP_BUFFER',      
]; 
MonXeventsTelemetry
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where event != 'xio_failed_request'
| where LogicalServerName =~ '{LogicalServerName}'
| join kind=leftouter (mapping) on buffer_flush_policy 
| project TIMESTAMP, AppName, database_name, event, session_name, EVENT_RETENTION_MODE, NodeName, ClusterName
| order by TIMESTAMP
| take 100
```

## 5.10 process-id-display.md

### KQL Query — Process IDs
```kql
MonSQLSystemHealth
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| summarize startTime=min(PreciseTimeStamp), endTime=max(PreciseTimeStamp) by NodeName, process_id,AppName
| project-reorder startTime, endTime, NodeName, process_id,AppName
| order by startTime asc
```

---

# ═══════════════════════════════════════════════════════════════
# 6. SQLOS
# ═══════════════════════════════════════════════════════════════

## 6.1 non-yielding.md

### KQL Query 1 — Non-Yielding Count
```kql
MonSqlRmRingBuffer
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event =~'nonyield_copiedstack_ring_buffer_recorded'
| summarize Totalcount=count()
| where Totalcount > 0
| extend nonYieldingMessage=strcat("Non-yielding scheduler happened ", PluralOrSingular(Totalcount,"time")," This may lead to various performance issues, including but not limited to query slowness, system task failure, Azure DB hanging, and worker thread exhaustion. Please review the callstack to investigate.")
| project nonYieldingMessage
```

### KQL Query 2 — Non-Yielding Callstack Details
```kql
MonSqlRmRingBuffer
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event =~'nonyield_copiedstack_ring_buffer_recorded'
| summarize count(), StartTime=arg_min(originalEventTimestamp,dispatcher_pool_name,user_mode_time,kernel_mode_time,
scheduler_id,thread_id,system_thread_id,session_id,
worker,task,request_id,nonyield_type,worker_wait_stats),EndTime=max(originalEventTimestamp) by stack_frames
| extend duration_minutes=datetime_diff('minute',EndTime,StartTime)
| project-reorder count_,stack_frames,StartTime,EndTime,duration_minutes
| order by StartTime asc
```

---

# ═══════════════════════════════════════════════════════════════
# 7. QUERY-STORE
# ═══════════════════════════════════════════════════════════════

## 7.1 readonly-detection-singleton.md
- **Description**: QDS Readonly detection for Singleton databases

### KQL Query — QDS Readonly (Singleton)
```kql
let ReadonlyMessage = (totalCount:int, dcount:int,readOnlyReasonArray:string)
{
case(
dcount==1 and totalCount==1,strcat("Query Store run into readonly one time due to readonly_reason:",readOnlyReasonArray),
strcat("Query Store run into readonly ",totalCount," times due to readonly_reason:",readOnlyReasonArray))
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~'{LogicalServerName}' and logical_database_name =~'{LogicalDatabaseName}'
| where event in ('query_store_resource_total_over_instance_limit','query_store_stmt_hash_map_over_memory_limit','query_store_buffered_items_over_memory_limit','query_store_disk_size_over_limit','query_store_database_out_of_disk_space')
| extend readOnlyReason=case(
event=~'query_store_disk_size_over_limit',"65536",
event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_StmtHashMapMemory',"131072",
event=~'query_store_stmt_hash_map_over_memory_limit',"131072",
event=~'query_store_buffered_items_over_memory_limit',"262144",
event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_BufferedItemsMemory',"262144",
event=~'query_store_database_out_of_disk_space',"524288",event
)
| summarize totalCount=count(),dcount_=dcount(readOnlyReason),readOnlyReasonArray=make_set(readOnlyReason)
| where totalCount>0
| extend readOnlyReasonArray=tostring(readOnlyReasonArray)
| extend readOnlyReasonArray=replace_string(readOnlyReasonArray,"[","")
| extend readOnlyReasonArray=replace_string(readOnlyReasonArray,"]","")
| extend readOnlyReasonArray=replace_string(readOnlyReasonArray,"\"","")
| extend Keywords=replace_string(readOnlyReasonArray,",",";")
| extend finalMessage=ReadonlyMessage(totalCount,dcount_,readOnlyReasonArray)
| project finalMessage,Keywords
```

## 7.2 readonly-detection-ep.md
- **Description**: QDS Readonly detection for Elastic Pool databases

### KQL Query — QDS Readonly (Elastic Pool)
```kql
let FiterReadOnlyReasonArray=(ReadOnlyReasonArray:string)
{
let ReadOnlyReasonArray_result= replace_string(
replace_string(
replace_string(ReadOnlyReasonArray, "[", ""),
"]", ""),
"\"", "");
ReadOnlyReasonArray_result
};
let ReadonlyMessage = (totalReadonlyCount:int, currentDB_ReadonlyCount:int,otherDBs_ReadonlyCount:int,otherDBs_Dcount:int,
currentDB_ReadOnlyReasonArray:string,otherDBs_ReadOnlyReasonArray:string,logical_database_name:string)
{
case(
totalReadonlyCount==currentDB_ReadonlyCount,
strcat("Query Store of database [",logical_database_name,"] run into readonly ",currentDB_ReadonlyCount,iff(currentDB_ReadonlyCount==1," time", " times")," due to readonly_reason:",currentDB_ReadOnlyReasonArray,". Please note, this is the only database having QDS Readonly issue in the entire ElasticPool"),
currentDB_ReadonlyCount==0,strcat("Query Store of database [",logical_database_name,"] didn't run into readonly. At the ElasticPool level, ",otherDBs_Dcount," databases ran into QDS readonly issue ",otherDBs_ReadonlyCount,iff(totalReadonlyCount==1," time"," times")," due to readonly_reason:",otherDBs_ReadOnlyReasonArray,". Please note that we will not proceed with further QDS read-only analysis at this time. To continue, please specify a database had the QDS read-only issue and try again."),
strcat("Query Store of database [",logical_database_name,"] run into readonly ",currentDB_ReadonlyCount,iff(currentDB_ReadonlyCount==1," time", " times")," due to readonly_reason:",currentDB_ReadOnlyReasonArray,". At the ElasticPool level, other ",otherDBs_Dcount," databases run into QDS readonly issue ",otherDBs_ReadonlyCount,iff(otherDBs_ReadonlyCount==1," time"," times")," due to readonly_reason:",otherDBs_ReadOnlyReasonArray,".")
)
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}'
| where event in ('query_store_resource_total_over_instance_limit','query_store_stmt_hash_map_over_memory_limit','query_store_buffered_items_over_memory_limit','query_store_disk_size_over_limit','query_store_database_out_of_disk_space')
| extend readOnlyReason=case(
event=~'query_store_disk_size_over_limit',"65536",
event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_StmtHashMapMemory',"131072",
event=~'query_store_stmt_hash_map_over_memory_limit',"131072",
event=~'query_store_buffered_items_over_memory_limit',"262144",
event=~'query_store_resource_total_over_instance_limit' and query_store_resource_type=~'x_QdsResourceType_BufferedItemsMemory',"262144",
event=~'query_store_database_out_of_disk_space',"524288",event
)
|summarize totalReadonlyCount=count(),currentDB_ReadonlyCount=countif(logical_database_name =~'{LogicalDatabaseName}'),otherDBs_ReadonlyCount=countif(logical_database_name !~'{LogicalDatabaseName}'),
otherDBs_Dcount=dcountif(logical_database_name,logical_database_name !~'{LogicalDatabaseName}'),
currentDB_ReadOnlyReasonArray=make_set_if(readOnlyReason,logical_database_name =~'{LogicalDatabaseName}'),otherDBs_ReadOnlyReasonArray=make_set_if(readOnlyReason,logical_database_name !~'{LogicalDatabaseName}')
| where totalReadonlyCount>0
| extend currentDB_ReadOnlyReasonArray=FiterReadOnlyReasonArray(currentDB_ReadOnlyReasonArray)
| extend otherDBs_ReadOnlyReasonArray=FiterReadOnlyReasonArray(otherDBs_ReadOnlyReasonArray)
| extend Keywords=replace_string(currentDB_ReadOnlyReasonArray,",",";")
| extend readonlyMessage=ReadonlyMessage(totalReadonlyCount,currentDB_ReadonlyCount,otherDBs_ReadonlyCount,otherDBs_Dcount,currentDB_ReadOnlyReasonArray,otherDBs_ReadOnlyReasonArray,'{LogicalDatabaseName}')
| project readonlyMessage,Keywords
```

## 7.3 readonly-65536.md

### KQL Query — QDS 65536 (Max Size Reached)
```kql
let ReadonlyMessage = (totalCount:int,max_size_mb:long,dcount_max_size_mb: int,startTime:string,endTime:string)
{
let optionMessage=case(10240>max_size_mb,strcat("(The max size limit is 10240 MB, you have ",10240-max_size_mb," MB to increase)"),
max_size_mb==10240,strcat("(This is not an option, as the max_storage_size_mb of QDS is already set to 10240 MB, which is the maximum limit.)"),
strcat("(This is not an option, as the max_storage_size_mb of QDS is already set to ",max_size_mb," MB, which is already greater than the 10GB limit.)")
);
let percentOfLimit=max_size_mb*100.0/10240;
let mitigationMessage=case(50>=percentOfLimit,strcat("The mitigation includes the following actions:1. Increasing max_storage_size_mb of QDS;",optionMessage," 2. Implementing query parameterization;3. Decreasing stale_query_threshold_days;4. Removing specific entries in QDS."),
90>=percentOfLimit,strcat("The mitigation includes the following actions:1. Implementing query parameterization;2. Increasing max_storage_size_mb of QDS;",optionMessage,"3. Decreasing stale_query_threshold_days;4. Removing specific entries in QDS."),
strcat("The mitigation includes the following actions:1. Implementing query parameterization;2. Decreasing stale_query_threshold_days;3. Removing specific entries in QDS.4. Increasing max_storage_size_mb of QDS;",optionMessage));
let maxSizeMessage=case(dcount_max_size_mb ==1,strcat("The max size of QDS setting was ",max_size_mb," megabyte. "),
strcat("The max size of QDS setting was ",max_size_mb," megabyte. Please note, the Max Size Setting was adjusted ",dcount_max_size_mb-1," time(s).")
);
case(totalCount ==1,
strcat("The Azure Db ran into Readonly once at ",startTime, ", with ReadonlyReason 65536(Max QDS Size is reached). ",maxSizeMessage,mitigationMessage),
strcat("The Azure Db ran into Readonly ",totalCount," times with same ReadonlyReason 65536(Max QDS Size is reached). The first occurrence happended at ",startTime, ", and the most recent happened at ",endTime,". ",maxSizeMessage,mitigationMessage)
)
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event=~'query_store_disk_size_over_limit'
| extend current_size_mb=current_size_kb/1024
| extend max_size_mb=max_size_kb/1024
| project originalEventTimestamp,current_size_mb,max_size_mb
| summarize totalCount=count(),max_size_mb=max(max_size_mb),startTime=min(originalEventTimestamp),endTime=max(originalEventTimestamp),
dcount_max_size_mb=dcount(max_size_mb)
| extend startTime=format_datetime(startTime,'yyyy-MM-dd HH:mm')
| extend endTime=format_datetime(endTime,'yyyy-MM-dd HH:mm')
| where totalCount>0
| extend readonlyMessage=ReadonlyMessage(totalCount,max_size_mb,dcount_max_size_mb,startTime,endTime)
| project readonlyMessage
```

## 7.4 readonly-131072.md

### KQL Query — QDS 131072 (StmtHashMap Over Memory Limit)
```kql
let ReadonlyMessage = (totalCount:int,incorrectCount:int)
{
let FastPathOptimizationMessage=iff(incorrectCount==0,"",
strcat("Note: we've detected abnormal memory usage that actual StmtHash memory was less than the limit, it could be due to 'FastPath Optimization', please engage QDS Expert to investigate."));
let mitigationMessage=strcat("The mitigation includes the following actions:1. Implementing query parameterization;2. Upgrading the Service Level Objective (SLO) to increase memory capacity;3. Decreasing capture_policy_stale_threshold_hours;4. Decreasing stale_query_threshold_days.");
let dbLevelLimitMessage=strcat("The ",iff(totalCount==1," occurrence was ", " occurrences were")," due to the memory usage of StmtHashMapMemory reached the database level memory threshold-—set at 5% of the total database memory. ");
let occurrenceMessage=strcat("The Azure Sql Database Query Store (QDS) ran into read-only mode due to the ReadonlyReason-131072 ",totalCount,iff(totalCount==1," time", " times."));
strcat(occurrenceMessage,dbLevelLimitMessage,iff(incorrectCount==0, mitigationMessage,FastPathOptimizationMessage))
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event=='query_store_stmt_hash_map_over_memory_limit' or
( event=='query_store_resource_total_over_instance_limit' and query_store_resource_type=='x_QdsResourceType_StmtHashMapMemory')
|summarize totalCount=count(),
incorrectCount=countif(max_stmt_hash_map_size_kb>current_stmt_hash_map_size_kb or max_instance_total_resource_size_kb>current_instance_total_resource_size_kb)
| where totalCount>0
| extend readonlyMessage=ReadonlyMessage(totalCount,incorrectCount)
| project readonlyMessage
```

## 7.5 readonly-262144.md

### KQL Query — QDS 262144 (BufferedItems Over Memory Limit)
```kql
let ReadonlyMessage = (totalCount:int,incorrectCount:int)
{
let FastPathOptimizationMessage=iff(incorrectCount==0,"",
strcat("Note: we've detected abnormal memory usage that actual Buffereditem memory was less than the limit, it could be due to 'FastPath Optimization', please engage QDS Expert to investigate."));
let mitigationMessage=strcat("The mitigation includes the following actions:1. Implementing query parameterization;2. Upgrading the Service Level Objective (SLO) to increase memory capacity;3. Decreasing flush_interval_seconds;");
let dbLevelLimitMessage=strcat("The ",iff(totalCount==1," occurrence was ", " occurrences were")," due to the memory usage of BufferedItemsMemory reached the database level memory threshold-—set at 1% of the total database memory. ");
let occurrenceMessage=strcat("The Azure Sql Database Query Store (QDS) ran into read-only mode due to the ReadonlyReason-262144 ",totalCount,iff(totalCount==1," time", " times."));
strcat(occurrenceMessage,dbLevelLimitMessage,iff(incorrectCount==0, mitigationMessage,FastPathOptimizationMessage))
};
MonQueryStoreFailures
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event=='query_store_buffered_items_over_memory_limit' or
( event=='query_store_resource_total_over_instance_limit' and query_store_resource_type=='x_QdsResourceType_BufferedItemsMemory')
|summarize totalCount=count(),incorrectCount=countif(max_buffered_items_size_kb>current_buffered_items_size_kb or max_instance_total_resource_size_kb>current_instance_total_resource_size_kb)
| where totalCount>0
| extend readonlyMessage=ReadonlyMessage(totalCount,incorrectCount)
| project readonlyMessage
```

## 7.6 readonly-rca-statementsqlhash-singleton.md

### KQL Query — StatementSqlHash to QueryHash Ratio
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

## 7.7 readonly-capturemode-analysis.md

### KQL Query — CaptureMode Analysis
```kql
let CaptureModeMessage= (CaptureModeAllCount:int,CaptureModeAllChange_Count:int,CustomCapture_PolicyExecutionPolicyCount:int,CustomCapture_PolicyExecutionPolicyChangeCount:int)
{
let CaptureModeAllChange_Count_message=case(CaptureModeAllChange_Count==0,"",
strcat("The CaptureMode was changed to 'All' ",CaptureModeAllChange_Count,iff(CaptureModeAllChange_Count==1," time", " times."))
);
let CaptureModeAllCount_Message=case(CaptureModeAllCount==0,"",
strcat("The CaptureMode in 'All' mode was detected ",CaptureModeAllCount,iff(CaptureModeAllCount==1," time", " times."))
);
let CustomCapture_PolicyExecutionPolicyChangeCount_message=case(CustomCapture_PolicyExecutionPolicyChangeCount==0,"",
strcat(" The CaptureMode was changed to 'Custom' with not recommended capture_policy_execution_count/capture_policy_total_compile_cpu_ms/capture_policy_total_execution_cpu_ms ",CustomCapture_PolicyExecutionPolicyChangeCount,iff(CustomCapture_PolicyExecutionPolicyChangeCount==1," time", " times."))
);
let CustomCapture_PolicyExecutionPolicyCount_message=case(CustomCapture_PolicyExecutionPolicyCount==0,"",
strcat(" The CaptureMode in 'Custom' with not recommended capture_policy_execution_count/capture_policy_total_compile_cpu_ms/capture_policy_total_execution_cpu_ms  was detected ",CustomCapture_PolicyExecutionPolicyCount,iff(CustomCapture_PolicyExecutionPolicyCount==1," time", " times."))
);
let BenefitsMessage=case(CaptureModeAllChange_Count+CaptureModeAllCount+CustomCapture_PolicyExecutionPolicyChangeCount+CustomCapture_PolicyExecutionPolicyCount==0,"",
strcat(" Please change CaptureMode to  Auto. Benefits:When CaptureMode is set to Auto, fewer entries are persisted to QDS, reducing the likelihood of encountering a QDS ReadOnly state with ReadOnlyReason 65536/262144.")
);
strcat(CaptureModeAllChange_Count_message,CaptureModeAllCount_Message,CustomCapture_PolicyExecutionPolicyChangeCount_message,CustomCapture_PolicyExecutionPolicyCount_message,BenefitsMessage)
};
let setting1=(MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name  =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_and_state'
| summarize CaptureModeAllCount=countif(capture_policy_mode =~ 'x_qdsCaptureModeAll'),CustomCapture_PolicyExecutionPolicyCount=countif(capture_policy_mode=~'x_qdsCaptureModeCustom' and (capture_policy_execution_count<30 or capture_policy_total_compile_cpu_ms<1000 or capture_policy_total_execution_cpu_ms<100))
| extend joinColumn=1);
let setting2=(MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name  =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_changed'
| summarize
captureModeAllChange_Count=countif(capture_policy_mode_old=~ 'x_qdsCaptureModeAll' or capture_policy_mode_new =~ 'x_qdsCaptureModeAll'),
CustomCapture_PolicyExecutionPolicyChangeCount=countif(
(capture_policy_execution_count_old<30 or capture_policy_total_compile_cpu_ms_old<1000 or capture_policy_total_execution_cpu_ms_old<100) or
(capture_policy_execution_count_new<30 or capture_policy_total_compile_cpu_ms_new<1000 or capture_policy_total_execution_cpu_ms_new<100)
)
|extend joinColumn=1);
setting1
| join kind=inner (setting2) on joinColumn
| where CaptureModeAllCount>0 or captureModeAllChange_Count>0 or CustomCapture_PolicyExecutionPolicyCount>0 or CustomCapture_PolicyExecutionPolicyChangeCount>0
| extend captureModeMessage=CaptureModeMessage(CaptureModeAllCount,captureModeAllChange_Count,CustomCapture_PolicyExecutionPolicyCount,CustomCapture_PolicyExecutionPolicyChangeCount)
| project captureModeMessage
```

## 7.8 qds-current-setting.md

### KQL Query — QDS Current Settings
```kql
let CapturePolicyStatus = (capture_policy_mode: string,capture_policy_execution_count:int,capture_policy_total_compile_cpu_ms:int,capture_policy_total_execution_cpu_ms:int)
{
let recommendatoin="Suggest switching to Auto mode. Current setting is not recommended because it persists all queries into Query Store and is likely to cause Query Store to enter read-only mode due to one of the following reasons: 65536, 131072, 262144.";
case(
capture_policy_mode =~'x_qdsCaptureModeAll' ,strcat("CaptureMode is set to 'Full' instead of 'Auto'. ",recommendatoin),
capture_policy_execution_count<30 or capture_policy_total_compile_cpu_ms<1000 or capture_policy_total_execution_cpu_ms<100,strcat("The capture_policy_setting allows more queries to be persisted ",recommendatoin),"We don't find obvious issue."
  )
  };
  MonQueryStoreInfo
  | where {AppNamesNodeNamesWithOriginalEventTimeRange}
  | where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
  | where event == 'query_store_db_settings_and_state'
  | extend ActualState = case (db_state_actual == 0, 'Off', db_state_actual == 1, 'ReadOnly', db_state_actual == 2, 'ReadWrite', db_state_actual == 3, 'Error', db_state_desired == 4, 'READ_CAPTURE_SECONDARY','Other')
  | extend DesiredState = case (db_state_desired == 0, 'Off', db_state_desired == 1, 'ReadOnly', db_state_desired == 2, 'ReadWrite', db_state_desired == 3, 'Error', db_state_desired == 4, 'READ_CAPTURE_SECONDARY','Other')
  |top 1  by  PreciseTimeStamp desc
  | extend capturePolicyStatus=CapturePolicyStatus(capture_policy_mode,capture_policy_execution_count,capture_policy_total_compile_cpu_ms,capture_policy_total_execution_cpu_ms)
  |project capturePolicyStatus
```

## 7.9 qds-memory.md
- **Path**: `/.github/skills/Performance/query-store/references/qds-memory.md`
- **Status**: FILE RETURNED EMPTY (no content)

## 7.10 qds-setting-change.md

### KQL Query — QDS Setting Change History
```kql
MonQueryStoreInfo
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_changed'
| extend
Change = strcat
(
iff(capture_policy_execution_count_old != capture_policy_execution_count_new, strcat(', capture_policy_execution_count:', tostring(capture_policy_execution_count_old), '->', tostring(capture_policy_execution_count_new)), ''),
iff(capture_policy_mode_old != capture_policy_mode_new, strcat(', capture_policy_mode:', capture_policy_mode_old, '->', capture_policy_mode_new), ''),
iff(capture_policy_stale_threshold_hours_old != capture_policy_stale_threshold_hours_new, strcat(', capture_policy_stale_threshold_hours:', tostring(capture_policy_stale_threshold_hours_old), '->', tostring(capture_policy_stale_threshold_hours_new)), ''),
iff(capture_policy_total_compile_cpu_ms_old != capture_policy_total_compile_cpu_ms_new, strcat(', capture_policy_total_compile_cpu_ms:', tostring(capture_policy_total_compile_cpu_ms_old), '->', tostring(capture_policy_total_compile_cpu_ms_new)), ''),
iff(capture_policy_total_execution_cpu_ms_old != capture_policy_total_execution_cpu_ms_new, strcat(', capture_policy_total_execution_cpu_ms:', tostring(capture_policy_total_execution_cpu_ms_old), '->', tostring(capture_policy_total_execution_cpu_ms_new)), ''),
iff(fast_path_optimization_mode_old != fast_path_optimization_mode_new, strcat(', fast_path_optimization_mode:', fast_path_optimization_mode_old, '->', fast_path_optimization_mode_new), ''),
iff(flush_interval_seconds_old != flush_interval_seconds_new, strcat(', flush_interval_seconds:', flush_interval_seconds_old, '->', flush_interval_seconds_new), ''),
iff(interval_length_minutes_old != interval_length_minutes_new, strcat(', interval_length_minutes:', interval_length_minutes_old, '->', interval_length_minutes_new), ''),
iff(max_plans_per_query_old != max_plans_per_query_new, strcat(', max_plans_per_query:', max_plans_per_query_old, '->', max_plans_per_query_new), ''),
iff(max_size_mb_old != max_size_mb_new, strcat(', max_size_mb:', max_size_mb_old, '->', max_size_mb_new), ''),
iff(query_store_enabled_old != query_store_enabled_new, strcat(', query_store_enabled:', query_store_enabled_old, '->', query_store_enabled_new), ''),
iff(query_store_error_state_old != query_store_error_state_new, strcat(', query_store_error_state:', query_store_error_state_old, '->', query_store_error_state_new), ''),
iff(query_store_read_only_old != query_store_read_only_new, strcat(', query_store_read_only:', query_store_read_only_old, '->', query_store_read_only_new), ''),
iff(size_based_cleanup_mode_old != size_based_cleanup_mode_new, strcat(', size_based_cleanup_mode:', size_based_cleanup_mode_old, '->', size_based_cleanup_mode_new), ''),
iff(stale_query_threshold_days_old != stale_query_threshold_days_new, strcat(', stale_query_threshold_days:', stale_query_threshold_days_old, '->', stale_query_threshold_days_new), ''),
iff(wait_stats_capture_mode_old != wait_stats_capture_mode_new, strcat(', wait_stats_capture_mode:', wait_stats_capture_mode_old, '->', wait_stats_capture_mode_new), ''),
''
)
| extend Change=trim_start(',',Change)
| where isnotempty(Change)
| project PreciseTimeStamp,AppName,NodeName,Change
| order by PreciseTimeStamp
```

## 7.11 qds-size-overtime.md

### KQL Query — QDS Size Over Time
```kql
let SizeMessage = (totalCount:int, count_greaterthan100:int,count_greaterthan90:int,count_greaterthan80:int)
{
let summaryMessage=case(count_greaterthan100 >0,"Issue detected. Here are the details:",
count_greaterthan80>0,"Potential issue detected. Here are the details:",
"We don't find obvious issue. Here are the details:");
strcat(summaryMessage," Over the past 7 days up to the specified time range, the size of QDS reached its size limit ",
count_greaterthan100,iff(count_greaterthan100==1," time", " times"),", exceeded 90% of limit ",count_greaterthan90,iff(count_greaterthan90==1," time", " times"),", and exceeded 80% of limit ",count_greaterthan80,
iff(count_greaterthan80==1," time", " times"),"——accounting for ",round(count_greaterthan100*100.0/totalCount,1),"%, ",round(count_greaterthan90*100.0/totalCount,1),"%, ",round(count_greaterthan80*100.0/totalCount,1),"% of the total statistical data, respectively.")
};
MonQueryStoreInfo
| where {AppNamesNodeNamesWithPreciseTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event == "query_store_disk_size_info"
| summarize totalCount=count(), count_greaterthan100=countif(current_size_kb>=max_size_kb),count_greaterthan90=countif(current_size_kb>max_size_kb*0.9), count_greaterthan80=countif(current_size_kb>max_size_kb*0.8)
| extend sizeMessage=SizeMessage(totalCount,count_greaterthan100,count_greaterthan90,count_greaterthan80)
| extend IssueDetected=iff(count_greaterthan80 >0,'true','false')
| project sizeMessage,IssueDetected
```

## 7.12 qds-sizebased-cleanup-job-analysis.md

### KQL Query — QDS Cleanup Job Analysis
```kql
let longDurationThreshold=60;
let CleanupJobMessage = (totalCount_cleanupStart:int,totalCount_CleanupFinish:int,endedWithCleanupFinish:bool,longDurationCount:int,min_duration:int,max_duration:int,avg_duration:real)
{
let longDurationMessage=case(longDurationCount >0,strcat(" Additionally, ",longDurationCount," Cleanup job took more than 60 mins to complete. The most time consuming one took ",max_duration," minutes to complete, while the average completion time was ",avg_duration, " mins. You may engage QDS experts to investigate the long-running jobs."),
isnan(avg_duration)==false,strcat("The most time consuming one took ",max_duration," minutes to complete, while the average completion time was ",toint(avg_duration), " mins"),
""
);
let potentionalFailureCount=totalCount_cleanupStart-totalCount_CleanupFinish;
let lastCleanupWithoutFinishMessage="Please note, The most recent cleanup job started but did not complete. There are two possible reasons: 1) The specified time range may not include the job's completion time. Try expanding the endTime and rerunning it. 2) The cleanup background job failed, then please engage QDS expert to investigate.";
let failedCleanupJobMessage=case(potentionalFailureCount==0,"",
endedWithCleanupFinish ==false and potentionalFailureCount==1,lastCleanupWithoutFinishMessage,
endedWithCleanupFinish ==true  and potentionalFailureCount>0, strcat(potentionalFailureCount, " of ",totalCount_cleanupStart, " started but didn't complete, indicating potential failures. Please engage QDS expert to investigate."),
strcat(potentionalFailureCount, " of ",totalCount_cleanupStart, " started but didn't complete, indicating potential failures. Please engage QDS expert to investigate. ",lastCleanupWithoutFinishMessage)
);
let succeededCleanupJobMessage=case(
potentionalFailureCount==0,strcat("Over the past 7 days up to the specified time period, QDS size-based cleanup background job(s) were executed ",totalCount_cleanupStart," time(s), no failure detected. "),
strcat("Over the past 7 days up to the specified time period, QDS size-based cleanup background job(s) were executed ",totalCount_cleanupStart," time(s), ",totalCount_CleanupFinish," of ",totalCount_cleanupStart," completed successfully. ")
);
strcat(succeededCleanupJobMessage,failedCleanupJobMessage,longDurationMessage)
};
let longRunningCleanupJob=MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
|where event in ('query_store_size_retention_cleanup_started','query_store_size_retention_cleanup_finished')
|order by originalEventTimestamp asc nulls first
| serialize
| extend preTime =iff(event=~'query_store_size_retention_cleanup_finished',prev(originalEventTimestamp), datetime(null))
| extend duration_minutes=datetime_diff('minute',originalEventTimestamp,preTime)
| extend duration_hours=datetime_diff('hour',originalEventTimestamp,preTime)
| extend originalEventTimestamp=format_datetime(originalEventTimestamp,'yyyy-MM-dd HH:mm')
| where event =~'query_store_size_retention_cleanup_finished'
| project originalEventTimestamp,preTime,duration_minutes,duration_hours,event,current_size_kb,target_delete_size_kb,deleted_plan_count,deleted_query_count,estimated_deleted_size_kb,last_deleted_query_total_cpu,max_deleted_total_cpu
| order by originalEventTimestamp asc
| summarize totalCount_LongRunningCleanupJob=countif(duration_minutes>=60),longDurationCount=countif(duration_minutes>=longDurationThreshold),min_duration=min(duration_minutes),max_duration=max(duration_minutes),avg_duration=round(avg(duration_minutes),1)
| extend joinColumn=1
;
let potentailFailedCleanupJob=MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event in ('query_store_size_retention_cleanup_started','query_store_size_retention_cleanup_finished')
| order by originalEventTimestamp asc nulls first
| serialize
| extend rn = row_number()
| summarize maxCountOfCleanupFinished=maxif(rn,event=~'query_store_size_retention_cleanup_finished' ),maxCount=max(rn),
totalCount_CleanupFinish=countif(event=~'query_store_size_retention_cleanup_finished') ,
totalCount_CleanupStart=countif(event=~'query_store_size_retention_cleanup_started' or (event=~'query_store_size_retention_cleanup_finished' and rn==1))
| extend endedWithCleanupFinish=maxCountOfCleanupFinished==maxCount
| extend potentionalFailureCount=totalCount_CleanupStart-totalCount_CleanupFinish
| extend joinColumn=1;
potentailFailedCleanupJob
| join kind=fullouter (longRunningCleanupJob) on joinColumn
| project totalCount_CleanupStart,totalCount_CleanupFinish,endedWithCleanupFinish,longDurationCount,min_duration,max_duration,avg_duration
| where totalCount_CleanupStart >=1
| extend cleanupJobMessage=CleanupJobMessage(totalCount_CleanupStart,totalCount_CleanupFinish,endedWithCleanupFinish,longDurationCount,min_duration,max_duration,avg_duration)
| extend IssueDetected=case(totalCount_CleanupStart-totalCount_CleanupFinish>1 or max_duration >=longDurationThreshold,'true','false')
| summarize count=count() ,arg_max(totalCount_CleanupStart,cleanupJobMessage,IssueDetected)
```

## 7.13 qds-sizebased-cleanupjob-disable-detection.md

### KQL Query — QDS Cleanup Disabled Detection
```kql
let SizeBasedCleanupModeMessage= (size_based_cleanup_mode_Disabled_Count:int,size_based_cleanup_mode_Disabled_Change_Count:int)
{
"QDS size_based_cleanup_mode was set to off. Please note, the size-based cleanup backgroub job doesn't run when the mode is off, which may cause QDS run into readonly with readonly issue 65536."
};
let setting1=(MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_and_state'
| where size_based_cleanup_mode =~ 'x_qdsSizeBasedCleanupModeMin'
| summarize size_based_cleanup_mode_Disabled_Count=count()
| extend joinColumn=1);
let setting2=(MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_changed'
| summarize
size_based_cleanup_mode_Disabled_Change_Count=countif(size_based_cleanup_mode_old=~ 'x_qdsSizeBasedCleanupModeMin' or size_based_cleanup_mode_new =~ 'x_qdsSizeBasedCleanupModeMin')
|extend joinColumn=1);
setting1
| join kind=inner (setting2) on joinColumn
| where size_based_cleanup_mode_Disabled_Count+size_based_cleanup_mode_Disabled_Change_Count>0
| extend sizeBasedCleanupModeMessage=SizeBasedCleanupModeMessage(CaptureModeAllCount,size_based_cleanup_mode_Disabled_Change_Count)
| project sizeBasedCleanupModeMessage
```

---

# ═══════════════════════════════════════════════════════════════
# SUMMARY STATISTICS
# ═══════════════════════════════════════════════════════════════

| Category | Files Read | KQL Queries Extracted | Notes |
|----------|-----------|----------------------|-------|
| BLOCKING | 5 | 9 | Includes blocking, deadlock, lead blocker, long txn, deadlock queries |
| MEMORY | 3 | 4 | MRG/DRG detection, OOM summary, buffer pool drop |
| COMPILATION | 6 | 7 | Failed/successful compilation CPU, gateway, top compilations |
| OUT-OF-DISK | 7 | 8 | Drive space, directory quota, max size, tempdb full, xstore errors |
| MISCELLANEOUS | 10 | 11 | Worker threads, corruption, AKV, restart, kill, profiler, xevent, PID |
| SQLOS | 1 | 2 | Non-yielding detection + callstack |
| QUERY-STORE | 13 | 13 | Readonly detection (singleton/EP), 65536/131072/262144, capture mode, settings, size, cleanup |
| **TOTAL** | **45** | **54** | qds-memory.md returned empty |

## Kusto Tables Referenced
MonBlockedProcessReportFiltered, MonDeadlockReportsFiltered, MonDmTranActiveTransactions,
MonDmDbResourceGovernance, MonRgManager, MonSQLSystemHealth, MonSqlMemoryClerkStats,
MonQueryProcessing, MonWiQueryParamData, MonRgLoad, MonSqlRgHistory, MonFabricThrottle,
MonSQLXStore, MonDmRealTimeResourceStats, MonSqlRmRingBuffer, MonQueryStoreFailures,
MonQueryStoreInfo, MonWiQdsExecStats, MonXeventsTelemetry, MonManagement, MonSocrates
