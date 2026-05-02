# Kusto Tables Reference for Gateway Health Check

## Data Sources

### 1. MonLogin (Login Telemetry)

**Cluster**: `sqladhoc.kusto.windows.net`  
**Database**: `sqlazure1`  
**Source XEvent**: `process_login_finish` (from Gateway login processing)  
**MDS Event Name**: `MonLogin`

#### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `TIMESTAMP` | datetime | Event timestamp |
| `ClusterName` | string | Service Fabric cluster name |
| `NodeName` | string | SF node name |
| `AppTypeName` | string | SF application type (filter for `Gateway` variants) |
| `code_package_version` | string | Code package version from SF activation context |
| `event` | string | Event type — filter on `process_login_finish` |
| `is_success` | bool | Whether login succeeded |
| `is_user_error` | bool | Whether failure was a user error (bad password, etc.) |
| `error` | int | Error code (0 = success) |
| `state` | int | Login error state |
| `state_desc` | string | Human-readable state description |
| `logical_server_name` | string | Logical server name |
| `database_name` | string | Target database |
| `AppName` | string | Client application name |
| `fedauth_library_type` | int | Authentication type (0=SQL, 2=Token, 3=AAD) |

#### Common AppTypeName Values for Gateway

- `GatewayType` / `Gateway` — Standard gateway
- Check for `has "Gateway"` to cover all variants

---

### 2. MonGatewayResourceStats (Resource Usage)

**Cluster**: `sqladhoc.kusto.windows.net`  
**Database**: `sqlazure1`  
**Source XEvent**: `gw_memory_perf_stats` (from `xdbgateway_resource_stats` session)  
**Source Session**: `xdbgateway_resource_stats` in `xdbgateway.xevents.xml`  
**MDS Event Name**: `MonGatewayResourceStats`  
**Collection Interval**: Every `sm_iMemoryPerfStatsIntervalSeconds` (default: 60s)

#### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `TIMESTAMP` | datetime | Event timestamp |
| `ClusterName` | string | Service Fabric cluster name |
| `NodeName` | string | SF node name |
| `code_package_version` | string | Code package version (from XEvent action `xdbwinfab.code_package_version`) |
| `current_commit_pages` | long | Currently committed SOS memory pages |
| `non_sos_usage_pages` | long | Non-SOS memory usage in pages |
| `memory_usage_pages` | uint64 | Total memory usage in pages |
| `current_target_pages` | long | Current target memory pages |
| `current_job_memory_cap_pages` | uint64 | Job memory cap in pages |
| `node_available_physical_memory_pages` | uint64 | Available physical memory on node |
| `node_available_page_file_pages` | uint64 | Available page file pages |
| `thread_count` | int | Active thread count |
| `alias_cache_entries` | long | Number of entries in alias cache |
| `uri_cache_entries` | long | Number of entries in URI cache |
| `kb_per_entry_ratio` | float | Kilobytes per cache entry |
| `internal_caches_kb` | long | Internal caches total size in KB |
| `internal_caches_limit_kb` | long | Internal caches size limit in KB |

#### Also Captured in Same Session

- `clock_hand_stats` — SOS clock hand statistics
- `resource_monitor_ring_buffer_recorded` — Resource monitor events

---

### 3. MonMdsPerfCounters (Process-Level Counters)

**Source**: MDS CounterSets configured in `MonitoringGatewayMDSAgentConfig_template.xml`  
**Collection Interval**: Every 5 seconds

#### Gateway-Specific Counters

| Counter Path | What It Measures |
|--------------|-----------------|
| `\Process(xdbgatewaymain)\% Processor Time` | CPU utilization |
| `\Process(xdbgatewaymain)\Private Bytes` | Private memory bytes |
| `\Process(xdbgatewaymain)\Thread Count` | Thread count |
| `\Process(xdbgatewaymain)\Working Set - Private` | Private working set |
| `\Process(xdbgatewaymain)\Handle Count` | OS handle count |

---

### 4. MonGatewayBeacon (Gateway Heartbeat)

**MDS Event Name**: `MonGatewayBeacon`  
**Purpose**: Gateway heartbeat/health beacon — useful for verifying that Gateway nodes are reporting

---

### 5. MonRedirector (Redirector / Fabric Resolution Events)

**Cluster**: `sqladhoc.kusto.windows.net`  
**Database**: `sqlazure1`  
**Source XEvent Session**: `xdbgateway` in `xdbgateway.xevents.xml`  
**MDS Event Name**: `MonRedirector`  
**Source Packages**: `xdbgateway`, `xdbwinfab`, `xdbgatewaymain`

The MonRedirector table is a catch-all table for the primary Gateway XEvent session. It captures events from multiple packages covering fabric resolution, alias cache, URI cache, lookup retries, configuration, and error logging.

#### Key Event Types (filter via `event` column)

| Event Name | Package | Description | Health Signal |
|------------|---------|-------------|---------------|
| `fabric_end_resolve` | xdbwinfab | SF partition resolution result | Non-zero `result` = resolution failure |
| `fabric_begin_resolve` | xdbwinfab | SF partition resolution start | Baseline for latency |
| `fabric_notify_resolve_change` | xdbwinfab | SF notification of partition change | Spike = partition movement |
| `fabric_force_refresh_uricache` | xdbwinfab | Forced URI cache refresh | High count = instability |
| `fabric_notify_stale_version` | xdbwinfab | Stale version notification | Frequent = upgrade in progress |
| `fabric_health_report` | xdbwinfab | SF health report from Gateway | `health_state` indicates status |
| `xdb_uricache_insert` | xdbwinfab | URI cache entry added | High rate = churn |
| `xdb_uricache_delete` | xdbwinfab | URI cache entry removed | High rate with inserts = instability |
| `xdb_lookup_retry_begin` | xdbwinfab | Lookup retry initiated | High count = resolution issues |
| `xdb_lookup_retry_end` | xdbwinfab | Lookup retry completed | Pair with begin for duration |
| `xdb_lookup_retry_cleanup_task_end` | xdbwinfab | Cleanup of expired retries | `expired_count` > 0 = timeouts |
| `sql_alias_cache_insert` | xdbgateway | Alias cache entry added | Normal cache population |
| `sql_alias_cache_update` | xdbgateway | Alias cache entry updated | Normal after refresh |
| `sql_alias_cache_delete` | xdbgateway | Alias cache entry removed | Check if unexpected |
| `sql_alias_cache_refresh` | xdbgateway | Alias cache ODBC refresh | Should occur periodically |
| `sql_alias_odbc_failure` | xdbgateway | Alias DB ODBC connectivity failure | Any occurrence = problem |
| `sql_alias_cache_backoff_timer` | xdbgateway | Backoff after cache failure | Indicate recovery attempts |
| `networksxmlmanager_traces` | xdbgateway | Network config loading | Used by `AlrLoadNetworksXml` derived event |
| `sos_wait_statistics` | xdbgateway | SOS wait type contention | Top waits show bottlenecks |
| `mgmtsvc_http_call_statistics` | xdbgateway | Mgmt service HTTP call metrics | Latency/failure tracking |
| `mds_gw_memory_clerk_stats` | xdbgateway | Memory clerk breakdown | Per-clerk memory usage |
| `mds_gw_cache_entry_stats` | xdbgateway | Cache entry counts | Alias + URI cache size |
| `error_log` | xdbgatewaymain | Gateway error log entries | Error diagnostics |
| `trace_print` | xdbgatewaymain | Gateway trace output | Debugging |

#### Key Columns by Event Type

**`fabric_end_resolve`**:
| Column | Type | Description |
|--------|------|-------------|
| `result` | uint32 | FABRIC_ERROR_CODE — 0 = success |
| `is_force_refreshed` | bool | Whether refresh was forced |
| `resolve_duration_in_micro_seconds` | uint64 | Resolution latency |
| `partition_id` | guid | SF partition identifier |
| `service_name` | string | SF service URI |

**`sql_alias_odbc_failure`**:
| Column | Type | Description |
|--------|------|-------------|
| (event-level columns) | | Occurrence itself is the signal |

**`sos_wait_statistics`**:
| Column | Type | Description |
|--------|------|-------------|
| `wait_name` | string | SOS wait type name |
| `wait_time` | uint64 | Cumulative wait time |
| `wait_requests` | uint64 | Number of wait requests |
| `max_wait_time` | uint64 | Maximum single wait time |
| `wait_completed` | uint64 | Number of completed waits |

**`xdb_lookup_retry_cleanup_task_end`**:
| Column | Type | Description |
|--------|------|-------------|
| `queue_size` | uint32 | Items in retry queue |
| `expired_count` | uint32 | Expired (timed-out) retries |

#### Common Columns (all events)
| Column | Type | Description |
|--------|------|-------------|
| `TIMESTAMP` | datetime | Event timestamp |
| `ClusterName` | string | SF cluster name |
| `NodeName` | string | SF node name |
| `code_package_version` | string | Code package version (XEvent action) |
| `event` | string | Event name (use for filtering) |
| `process_id` | int | Gateway process ID |

---

## Page Size Conversion

Gateway memory stats are reported in OS pages. The OS page size is **4 KB** (4096 bytes).

> **Note**: This is the OS page size (4 KB), not the SQL Server page size (8 KB).

```
Memory in KB = pages * 4
Memory in MB = pages * 4 / 1024
Memory in GB = pages * 4 / 1024 / 1024
```

For `gw_memory_perf_stats`, the code computes total bytes as:
```cpp
totalBytes = (currentCommit + currentNonSosUsage) * OsPageSize / BYTES_PER_KB;
```

Where `OsPageSize` = 4096 bytes and `BYTES_PER_KB` = 1024.

So effective conversion: `total_kb = (current_commit_pages + non_sos_usage_pages) * 4`

---

## Report Template

When multiple code package versions are detected, present a side-by-side comparison using this format:

```markdown
## Gateway Health Report: <CLUSTER_NAME>
**Time Range**: <start> to <end>
**Versions Detected**: <version_old> → <version_new>
**Version Transition Time**: <timestamp>

### Login Success Rate Comparison

| Metric | Version: <old> | Version: <new> | Delta |
|--------|---------------|---------------|-------|
| Total Logins | X | Y | +/- |
| Login Success Rate (%) | X% | Y% | +/- pp |
| System Errors | X | Y | +/- |
| System Error Rate (%) | X% | Y% | +/- pp |
| User Errors | X | Y | +/- |
| User Error Rate (%) | X% | Y% | +/- pp |

### Top User Errors (by volume)

Call out the top user errors (is_user_error==true) that contribute to high failure counts. These are **not** gateway system issues but help explain the overall failure landscape.

| Error Code | State | Description | Old Count | New Count | Delta |
|------------|-------|-------------|-----------|-----------|-------|
| NNNNN | N | desc | X | Y | +/- % |

> **Note**: User errors like 17830 (redirect), 42132 (DbNotInAliasDB), 42131 (FabricDatabaseHardPaused) are expected and do not indicate gateway health problems.

### Resource Usage Comparison

| Metric | Version: <old> | Version: <new> | Delta |
|--------|---------------|---------------|-------|
| Avg Memory (pages) | X | Y | +/- % |
| Max Memory (pages) | X | Y | +/- % |
| Avg Thread Count | X | Y | +/- |
| Avg Alias Cache Entries | X | Y | +/- |
| Avg URI Cache Entries | X | Y | +/- |
| Avg KB/Entry Ratio | X | Y | +/- % |
| Avg CPU % | X | Y | +/- pp |

### Redirector Health Comparison

| Metric | Version: <old> | Version: <new> | Delta |
|--------|---------------|---------------|-------|
| Fabric Resolve Failures | X | Y | +/- |
| Avg Resolve Latency (us) | X | Y | +/- % |
| P95 Resolve Latency (us) | X | Y | +/- % |
| ODBC Failures | X | Y | +/- |
| Lookup Retries | X | Y | +/- |
| URI Cache Inserts | X | Y | +/- |
| Top SOS Wait Type | name | name | — |

### Assessment

- ✅ / ⚠️ / ❌ **Login Success Rate**: <assessment>
- ✅ / ⚠️ / ❌ **Memory Usage**: <assessment>
- ✅ / ⚠️ / ❌ **CPU Usage**: <assessment>
- ✅ / ⚠️ / ❌ **Cache Health**: <assessment>
- ✅ / ⚠️ / ❌ **Fabric Resolution**: <assessment>
- ✅ / ⚠️ / ❌ **Alias Cache / ODBC**: <assessment>
- ✅ / ⚠️ / ❌ **Lookup Retries**: <assessment>
```

---

## Assessment Criteria

| Metric | ✅ Healthy | ⚠️ Warning | ❌ Critical |
|--------|-----------|------------|------------|
| Login Success Rate | ≥ 99.5% | 98% - 99.5% | < 98% |
| System Error Delta | ≤ 5% increase | 5-20% increase | > 20% increase |
| Memory Delta | ≤ 10% increase | 10-25% increase | > 25% increase |
| CPU Delta | ≤ 5pp increase | 5-15pp increase | > 15pp increase |
| Thread Count Delta | ≤ 10% increase | 10-30% increase | > 30% increase |
| Fabric Resolve Failures | 0 | 1-10 per 15m | > 10 per 15m |
| Fabric Resolve p95 Latency | ≤ 500,000µs (500ms) | 500,000-2,000,000µs (0.5-2s) | > 2,000,000µs (>2s) |
| ODBC Failures | 0 | 1-5 per hour | > 5 per hour |
| Lookup Retries Delta | ≤ 10% increase | 10-50% increase | > 50% increase |
| URI Cache Churn Delta | ≤ 20% increase | 20-50% increase | > 50% increase |

---

## Source Code References

- Gateway XEvent sessions: `Sql/xdb/manifest/svc/gateway/xdbgateway.xevents.xml`
- Gateway MDS config: `Sql/xdb/manifest/svc/gateway/MDS/MonitoringGatewayMDSAgentConfig_template.xml`
- Gateway resource stats implementation: `Sql/Ntdbms/xdb/gateway/common/gateway.cpp` (see `ResourceStatsTimerFunction`)
- MonLogin reference query: `Developer/vstojanovic/OnCall/Kusto_queries/Login-Stats.kql`
- `gw_memory_perf_stats` XEvent definition: `Sql/Ntdbms/xdb/gateway/common/xe/xexdbgatewaycommon.xe`
- MonRedirector XEvent session: `Sql/xdb/manifest/svc/gateway/xdbgateway.xevents.xml` (session `xdbgateway`)
- Fabric resolution XEvents: `Sql/Ntdbms/xdb/winfab/xexdbwinfabpkg.xe` (`fabric_end_resolve`, `xdb_uricache_*`, `xdb_lookup_retry_*`)
- Alias cache XEvents: `Sql/Ntdbms/xdb/gateway/common/xe/xexdbgatewaycommon.xe` (`sql_alias_cache_*`, `sql_alias_odbc_failure`)
- Gateway ServiceSettings: `Sql/xdb/manifest/svc/gateway/ServiceSettings_Gateway_Common.xml`
- DB ServiceSettings: `Sql/xdb/manifest/svc/sql/manifest/ServiceSettings_SQLServer_Common.xml`
- MS ServiceSettings: `Sql/xdb/manifest/svc/mgmt/` (fsm, clients, workflows)
- Feature Switch diff script: `diffFS.ps1` (PowerShell alternative using ADO REST API + PAT)
- Source repo: `DsMainDev` in `Database Systems` project on `msdata.visualstudio.com`
