// Gateway Health Check — Pre-built Kusto Queries
// Usage: Replace <CLUSTER_NAME> with the target cluster name
//        Replace <TIME_FILTER> with the FULL time predicate, including column name:
//          - ago style:     TIMESTAMP > ago(14d)
//          - between style: TIMESTAMP between(datetime(2026-03-01) .. datetime(2026-03-11))
//        For Query 19 (MonRolloutProgress), use originalEventTimestamp instead of TIMESTAMP
//        For Query 20 (MonWatsonAnalysis), use DumpCrashTime instead of TIMESTAMP

// =============================================================================
// QUERY 1: Detect code package versions in the time window
// =============================================================================
// Purpose: Identify if a version change occurred and when
// Run this FIRST to determine if version comparison is needed

MonLogin
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where AppTypeName has "Gateway"
| where event == "process_login_finish"
| summarize
    MinTime = min(TIMESTAMP),
    MaxTime = max(TIMESTAMP),
    LoginCount = count(),
    DistinctNodes = dcount(NodeName)
    by code_package_version
| order by MinTime asc

// =============================================================================
// QUERY 2: Login success rate over time (15-minute bins)
// =============================================================================
// Purpose: Track login success rate trend, optionally filtered by version
// LoginSuccessRate = (total - system_errors) / total — only system failures count
// User errors (bad password, DB not found, etc.) are NOT treated as failures

let TargetCluster = "<CLUSTER_NAME>";
let TargetVersion = ""; // Set to specific version, or leave empty for all
MonLogin
| where <TIME_FILTER>
| where ClusterName =~ TargetCluster
| where AppTypeName has "Gateway"
| where event == "process_login_finish"
| where isempty(TargetVersion) or code_package_version == TargetVersion
| summarize
    TotalLogins = count(),
    SuccessfulLogins = countif(is_success == true),
    FailedLogins = countif(is_success == false),
    UserErrors = countif(is_success == false and is_user_error == true),
    SystemErrors = countif(is_success == false and is_user_error == false)
    by bin(TIMESTAMP, 15m), code_package_version
| extend
    LoginSuccessRate = round(100.0 * (TotalLogins - SystemErrors) / TotalLogins, 4)
| order by TIMESTAMP asc

// =============================================================================
// QUERY 3: Login success rate — aggregated per version
// =============================================================================
// Purpose: Single summary row per version for side-by-side comparison
// LoginSuccessRate = (total - system_errors) / total — only system failures count
// User errors are reported separately; call out top user errors from Query 4

MonLogin
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where AppTypeName has "Gateway"
| where event == "process_login_finish"
| summarize
    TotalLogins = count(),
    SuccessfulLogins = countif(is_success == true),
    FailedLogins = countif(is_success == false),
    UserErrors = countif(is_success == false and is_user_error == true),
    SystemErrors = countif(is_success == false and is_user_error == false),
    MinTime = min(TIMESTAMP),
    MaxTime = max(TIMESTAMP),
    DistinctNodes = dcount(NodeName)
    by code_package_version
| extend
    LoginSuccessRate = round(100.0 * (TotalLogins - SystemErrors) / TotalLogins, 4),
    SystemErrorRate = round(100.0 * SystemErrors / TotalLogins, 4),
    UserErrorRate = round(100.0 * UserErrors / TotalLogins, 2),
    LoginsPerMinute = iff(datetime_diff('minute', MaxTime, MinTime) > 0, round(1.0 * TotalLogins / datetime_diff('minute', MaxTime, MinTime), 1), 0)
| order by MinTime asc

// =============================================================================
// QUERY 4: Top login errors by error code
// =============================================================================
// Purpose: Identify the most common login failures and compare across versions
// IMPORTANT: Call out top user errors (is_user_error==true) that contribute
// to high failure counts — these are not gateway system issues but are useful
// for understanding the overall failure landscape

MonLogin
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where AppTypeName has "Gateway"
| where event == "process_login_finish"
| where is_success == false
| summarize
    ErrorCount = count()
    by error, state, state_desc, is_user_error, code_package_version
| order by ErrorCount desc
| take 20

// =============================================================================
// QUERY 5: Resource usage over time (15-minute bins)
// =============================================================================
// Purpose: Track memory, threads, and cache usage trends

MonGatewayResourceStats
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| summarize
    AvgMemoryUsagePages = avg(memory_usage_pages),
    MaxMemoryUsagePages = max(memory_usage_pages),
    AvgCommitPages = avg(current_commit_pages),
    MaxCommitPages = max(current_commit_pages),
    AvgNonSosPages = avg(non_sos_usage_pages),
    AvgThreadCount = avg(thread_count),
    MaxThreadCount = max(thread_count),
    AvgAliasCacheEntries = avg(alias_cache_entries),
    MaxAliasCacheEntries = max(alias_cache_entries),
    AvgUriCacheEntries = avg(uri_cache_entries),
    MaxUriCacheEntries = max(uri_cache_entries),
    AvgKbPerEntry = avg(kb_per_entry_ratio),
    AvgInternalCachesKb = avg(internal_caches_kb),
    AvgInternalCachesLimitKb = avg(internal_caches_limit_kb)
    by bin(TIMESTAMP, 15m), code_package_version
| extend
    TotalMemoryKb = round((AvgCommitPages + AvgNonSosPages) * 4.0, 0),
    CacheUtilPct = round(100.0 * AvgInternalCachesKb / AvgInternalCachesLimitKb, 1)
| order by TIMESTAMP asc

// =============================================================================
// QUERY 6: Resource usage — aggregated per version
// =============================================================================
// Purpose: Single summary row per version for side-by-side comparison

MonGatewayResourceStats
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| summarize
    AvgMemoryUsagePages = avg(memory_usage_pages),
    P95MemoryUsagePages = percentile(memory_usage_pages, 95),
    MaxMemoryUsagePages = max(memory_usage_pages),
    AvgCommitPages = avg(current_commit_pages),
    AvgNonSosPages = avg(non_sos_usage_pages),
    AvgThreadCount = avg(thread_count),
    P95ThreadCount = percentile(thread_count, 95),
    MaxThreadCount = max(thread_count),
    AvgAliasCacheEntries = avg(alias_cache_entries),
    MaxAliasCacheEntries = max(alias_cache_entries),
    AvgUriCacheEntries = avg(uri_cache_entries),
    MaxUriCacheEntries = max(uri_cache_entries),
    AvgKbPerEntry = avg(kb_per_entry_ratio),
    AvgInternalCachesKb = avg(internal_caches_kb),
    SampleCount = count()
    by code_package_version
| extend TotalMemoryKb = round((AvgCommitPages + AvgNonSosPages) * 4.0, 0)

// =============================================================================
// QUERY 7: Process-level CPU and memory counters
// =============================================================================
// Purpose: Get CPU %, private bytes, handles from MDS perf counters

MonMdsPerfCounters
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where CounterName has "xdbgatewaymain"
| summarize
    AvgValue = avg(CounterValue),
    P95Value = percentile(CounterValue, 95),
    MaxValue = max(CounterValue)
    by bin(TIMESTAMP, 15m), CounterName
| order by CounterName, TIMESTAMP asc

// =============================================================================
// QUERY 8: Gateway node availability check
// =============================================================================
// Purpose: Verify Gateway nodes are reporting healthy beacons

MonGatewayBeacon
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| summarize
    BeaconCount = count(),
    LastBeacon = max(TIMESTAMP),
    FirstBeacon = min(TIMESTAMP)
    by NodeName
| extend MinutesSinceLastBeacon = datetime_diff('minute', now(), LastBeacon)
| order by LastBeacon desc

// =============================================================================
// QUERY 9: MonRedirector — Fabric resolution failures
// =============================================================================
// Purpose: Detect failed service partition resolutions (non-zero result)

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event == "fabric_end_resolve"
| where result != 0
| summarize
    FailureCount = count(),
    DistinctPartitions = dcount(partition_id),
    AvgResolveDurationUs = avg(resolve_duration_in_micro_seconds)
    by bin(TIMESTAMP, 15m), result, code_package_version
| order by TIMESTAMP asc

// =============================================================================
// QUERY 10: MonRedirector — Fabric resolution latency (success only)
// =============================================================================
// Purpose: Track resolution latency trends for successful lookups

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event == "fabric_end_resolve"
| where result == 0
| summarize
    Count = count(),
    AvgDurationUs = avg(resolve_duration_in_micro_seconds),
    P50DurationUs = percentile(resolve_duration_in_micro_seconds, 50),
    P95DurationUs = percentile(resolve_duration_in_micro_seconds, 95),
    P99DurationUs = percentile(resolve_duration_in_micro_seconds, 99),
    MaxDurationUs = max(resolve_duration_in_micro_seconds)
    by bin(TIMESTAMP, 15m), code_package_version
| order by TIMESTAMP asc

// =============================================================================
// QUERY 11: MonRedirector — Alias cache ODBC failures
// =============================================================================
// Purpose: Detect alias database connectivity failures

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event == "sql_alias_odbc_failure"
| summarize FailureCount = count()
    by bin(TIMESTAMP, 15m), NodeName, code_package_version
| order by TIMESTAMP asc

// =============================================================================
// QUERY 12: MonRedirector — Alias cache refresh activity
// =============================================================================
// Purpose: Verify alias cache is being refreshed regularly

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event == "sql_alias_cache_refresh"
| summarize
    RefreshCount = count(),
    DistinctNodes = dcount(NodeName)
    by bin(TIMESTAMP, 1h), code_package_version
| order by TIMESTAMP asc

// =============================================================================
// QUERY 13: MonRedirector — Lookup retries
// =============================================================================
// Purpose: Detect resolution instability via retry storms

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event in ("xdb_lookup_retry_begin", "xdb_lookup_retry_end", "xdb_lookup_retry_cleanup_task_end")
| summarize Count = count() by bin(TIMESTAMP, 15m), event, code_package_version
| order by TIMESTAMP asc

// =============================================================================
// QUERY 14: MonRedirector — URI cache churn
// =============================================================================
// Purpose: Detect fabric instability via high URI cache insert/delete rates

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event in ("xdb_uricache_insert", "xdb_uricache_delete")
| summarize Count = count() by bin(TIMESTAMP, 15m), event, code_package_version
| order by TIMESTAMP asc

// =============================================================================
// QUERY 15: MonRedirector — SOS wait statistics
// =============================================================================
// Purpose: Identify top contention points inside the Gateway process

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event == "sos_wait_statistics"
| summarize
    TotalWaitTimeMs = sum(wait_time),
    TotalWaitRequests = sum(wait_requests),
    MaxSingleWaitMs = max(max_wait_time)
    by wait_name, code_package_version
| order by TotalWaitTimeMs desc
| take 20

// =============================================================================
// QUERY 16: MonRedirector — Mgmt service HTTP call stats
// =============================================================================
// Purpose: Track management service call volume across versions

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event == "mgmtsvc_http_call_statistics"
| summarize Count = count()
    by bin(TIMESTAMP, 15m), code_package_version
| order by TIMESTAMP asc

// =============================================================================
// QUERY 17: MonRedirector — Fabric notification and resolve change events
// =============================================================================
// Purpose: Track partition movement notifications that trigger re-resolution

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event in ("fabric_notify_resolve_change", "fabric_notify_stale_version", "fabric_force_refresh_uricache")
| summarize Count = count() by bin(TIMESTAMP, 15m), event, code_package_version
| order by TIMESTAMP asc

// =============================================================================
// QUERY 18: MonRedirector — Aggregated redirector health per version
// =============================================================================
// Purpose: Single summary per version for side-by-side comparison

MonRedirector
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where event in ("fabric_end_resolve", "sql_alias_odbc_failure", "xdb_lookup_retry_begin", "xdb_uricache_insert", "xdb_uricache_delete")
| summarize
    FabricResolveTotal = countif(event == "fabric_end_resolve"),
    FabricResolveFailures = countif(event == "fabric_end_resolve" and result != 0),
    OdbcFailures = countif(event == "sql_alias_odbc_failure"),
    LookupRetries = countif(event == "xdb_lookup_retry_begin"),
    UriCacheInserts = countif(event == "xdb_uricache_insert"),
    UriCacheDeletes = countif(event == "xdb_uricache_delete")
    by code_package_version
| extend FabricResolveSuccessRate = iff(FabricResolveTotal > 0, round(100.0 * (FabricResolveTotal - FabricResolveFailures) / FabricResolveTotal, 2), 100.0)

// =============================================================================
// QUERY 19: Gateway deployment traces (MonRolloutProgress)
// =============================================================================
// Purpose: Detect Gateway deployments — start, progress, completion, pause/resume
// Source: GW1112 from Debug-Connectivity.md
// NOTE: <TIME_FILTER> must use originalEventTimestamp (not TIMESTAMP) for this table
//       e.g., originalEventTimestamp > ago(14d)

MonRolloutProgress
| where <TIME_FILTER>
| where cluster_name =~ "<CLUSTER_NAME>"
| where application_type_name == "Gateway" or application_name == "fabric:/Gateway"
| where event in ("start_upgrade_app_type", "app_instance_upgrade_progress", "start_upgrade_app_instance", "start_pause_upgrade_app_type", "start_resume_upgrade_app_type", "set_start_post_bake_blast")
| project originalEventTimestamp, event, cluster_name, target_version, rollout_key, upgrade_state, upgrade_progress, bake_start_time, bake_duration
| extend RolloutKeyCab = extract("^([0-9]*)_(.*)", 1, rollout_key)
| project-away rollout_key
| order by originalEventTimestamp asc

// =============================================================================
// QUERY 20: Gateway crash dumps (MonWatsonAnalysis)
// =============================================================================
// Purpose: Detect Gateway process crash dumps in the time window
// IMPORTANT: MonWatsonAnalysis is a centralized table that lives ONLY on sqladhoc.
//   Execute this query on: https://sqladhoc.kusto.windows.net / sqlazure1
//   Do NOT run on the regional cluster — the table does not exist there.
// NOTE: <TIME_FILTER> must use DumpCrashTime (not TIMESTAMP) for this table
//       e.g., DumpCrashTime > ago(14d)

MonWatsonAnalysis
| where <TIME_FILTER>
| where ClusterName =~ "<CLUSTER_NAME>"
| where AppName =~ "Gateway" or AppName =~ "xdbgatewaymain"
| summarize arg_max(DumpCrashTime, *) by DumpUID
| extend DumpURL = strcat("https://azurewatson.microsoft.com/dumpuid/", DumpUID)
| project DumpCrashTime, NodeName, ClusterName, AppName, DumpUID, DumpURL, BucketId, code_package_version
| order by DumpCrashTime asc

// =============================================================================
// NODE-LEVEL ANOMALY DETECTION
// =============================================================================
// Queries 21-23 compute per-node stats, compare against cluster-wide baselines,
// and surface only nodes that deviate beyond 2 standard deviations.
// Run these AFTER cluster-level queries identify a version of interest.

// =============================================================================
// QUERY 21: Node Login Anomaly Detection
// =============================================================================
// Purpose: Flag nodes with login success rate significantly below cluster avg
//          or system error rate significantly above cluster avg

let PerNodeLogin =
    MonLogin
    | where <TIME_FILTER>
    | where ClusterName =~ "<CLUSTER_NAME>"
    | where AppTypeName has "Gateway"
    | where event == "process_login_finish"
    | summarize
        TotalLogins = count(),
        SuccessLogins = countif(is_success == true),
        SystemErrors = countif(is_success == false and is_user_error == false)
        by NodeName, code_package_version
    | where TotalLogins >= 100 // ignore nodes with negligible traffic
    | extend
        LoginSuccessRate = round(100.0 * (TotalLogins - SystemErrors) / TotalLogins, 4),
        SysErrRate = round(100.0 * SystemErrors / TotalLogins, 4);
let ClusterLoginStats =
    PerNodeLogin
    | summarize
        AvgLoginSuccessRate = avg(LoginSuccessRate),
        StdLoginSuccessRate = stdev(LoginSuccessRate),
        AvgSysErrRate = avg(SysErrRate),
        StdSysErrRate = stdev(SysErrRate),
        NodeCount = count()
        by code_package_version;
PerNodeLogin
| join kind=inner ClusterLoginStats on code_package_version
| where LoginSuccessRate < (AvgLoginSuccessRate - 2 * StdLoginSuccessRate)
     or SysErrRate > (AvgSysErrRate + 2 * StdSysErrRate)
| extend
    LoginSuccessRateDeviation = round(LoginSuccessRate - AvgLoginSuccessRate, 4),
    SysErrDeviation = round(SysErrRate - AvgSysErrRate, 4)
| project NodeName, code_package_version, TotalLogins, LoginSuccessRate, AvgLoginSuccessRate, LoginSuccessRateDeviation, SysErrRate, AvgSysErrRate, SysErrDeviation
| order by LoginSuccessRateDeviation asc

// =============================================================================
// QUERY 22: Node Resource Usage Anomaly Detection
// =============================================================================
// Purpose: Flag nodes with memory, threads, or cache usage significantly above
//          the cluster average (hot/overloaded nodes)

let PerNodeResource =
    MonGatewayResourceStats
    | where <TIME_FILTER>
    | where ClusterName =~ "<CLUSTER_NAME>"
    | summarize
        AvgMemPages = avg(memory_usage_pages),
        P95MemPages = percentile(memory_usage_pages, 95),
        AvgThreads = avg(thread_count),
        P95Threads = percentile(thread_count, 95),
        AvgAliasCacheEntries = avg(alias_cache_entries),
        AvgInternalCachesKb = avg(internal_caches_kb),
        SampleCount = count()
        by NodeName, code_package_version
    | where SampleCount >= 10; // ignore nodes with negligible samples
let ClusterResourceStats =
    PerNodeResource
    | summarize
        ClusterAvgMem = avg(AvgMemPages),    ClusterStdMem = stdev(AvgMemPages),
        ClusterAvgThreads = avg(AvgThreads), ClusterStdThreads = stdev(AvgThreads),
        ClusterAvgCache = avg(AvgInternalCachesKb), ClusterStdCache = stdev(AvgInternalCachesKb),
        NodeCount = count()
        by code_package_version;
PerNodeResource
| join kind=inner ClusterResourceStats on code_package_version
| where AvgMemPages > (ClusterAvgMem + 2 * ClusterStdMem)
     or AvgThreads > (ClusterAvgThreads + 2 * ClusterStdThreads)
     or AvgInternalCachesKb > (ClusterAvgCache + 2 * ClusterStdCache)
| extend
    MemDeviation = round(AvgMemPages - ClusterAvgMem, 0),
    ThreadDeviation = round(AvgThreads - ClusterAvgThreads, 1),
    CacheKbDeviation = round(AvgInternalCachesKb - ClusterAvgCache, 0),
    AnomalyFlags = strcat(
        iff(AvgMemPages > (ClusterAvgMem + 2 * ClusterStdMem), "HIGH_MEM ", ""),
        iff(AvgThreads > (ClusterAvgThreads + 2 * ClusterStdThreads), "HIGH_THREADS ", ""),
        iff(AvgInternalCachesKb > (ClusterAvgCache + 2 * ClusterStdCache), "HIGH_CACHE", ""))
| project NodeName, code_package_version, AnomalyFlags, AvgMemPages, ClusterAvgMem, MemDeviation, P95MemPages, AvgThreads, ClusterAvgThreads, ThreadDeviation, P95Threads, AvgInternalCachesKb, ClusterAvgCache, CacheKbDeviation
| order by MemDeviation desc

// =============================================================================
// QUERY 23: Node Redirector Anomaly Detection
// =============================================================================
// Purpose: Flag nodes with elevated fabric resolution failures, ODBC errors,
//          or abnormally high resolution latency

let PerNodeRedirector =
    MonRedirector
    | where <TIME_FILTER>
    | where ClusterName =~ "<CLUSTER_NAME>"
    | where event in ("fabric_end_resolve", "sql_alias_odbc_failure", "xdb_lookup_retry_begin")
    | summarize
        FabricResolveTotal = countif(event == "fabric_end_resolve"),
        FabricResolveFails = countif(event == "fabric_end_resolve" and result != 0),
        OdbcFailures = countif(event == "sql_alias_odbc_failure"),
        LookupRetries = countif(event == "xdb_lookup_retry_begin"),
        AvgResolveDurationUs = avgif(resolve_duration_in_micro_seconds, event == "fabric_end_resolve" and result == 0)
        by NodeName, code_package_version
    | where FabricResolveTotal >= 50 // ignore nodes with negligible resolve traffic
    | extend
        FailRate = round(100.0 * FabricResolveFails / FabricResolveTotal, 2);
let ClusterRedirStats =
    PerNodeRedirector
    | summarize
        ClusterAvgFailRate = avg(FailRate),   ClusterStdFailRate = stdev(FailRate),
        ClusterAvgLatency = avg(AvgResolveDurationUs), ClusterStdLatency = stdev(AvgResolveDurationUs),
        ClusterAvgOdbc = avg(OdbcFailures),   ClusterStdOdbc = stdev(OdbcFailures),
        ClusterAvgRetries = avg(LookupRetries), ClusterStdRetries = stdev(LookupRetries),
        NodeCount = count()
        by code_package_version;
PerNodeRedirector
| join kind=inner ClusterRedirStats on code_package_version
| where FailRate > (ClusterAvgFailRate + 2 * ClusterStdFailRate)
     or AvgResolveDurationUs > (ClusterAvgLatency + 2 * ClusterStdLatency)
     or OdbcFailures > (ClusterAvgOdbc + 2 * ClusterStdOdbc)
     or LookupRetries > (ClusterAvgRetries + 2 * ClusterStdRetries)
| extend
    AnomalyFlags = strcat(
        iff(FailRate > (ClusterAvgFailRate + 2 * ClusterStdFailRate), "HIGH_FAIL_RATE ", ""),
        iff(AvgResolveDurationUs > (ClusterAvgLatency + 2 * ClusterStdLatency), "HIGH_LATENCY ", ""),
        iff(OdbcFailures > (ClusterAvgOdbc + 2 * ClusterStdOdbc), "HIGH_ODBC_ERR ", ""),
        iff(LookupRetries > (ClusterAvgRetries + 2 * ClusterStdRetries), "HIGH_RETRIES", ""))
| project NodeName, code_package_version, AnomalyFlags, FailRate, ClusterAvgFailRate, AvgResolveDurationUs, ClusterAvgLatency, OdbcFailures, LookupRetries
| order by FailRate desc
