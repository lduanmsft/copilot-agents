---
name: hyperscale-georestore-metrics
description: Analyze weekly Hyperscale geo-restore metrics and investigate individual failure reasons. Runs a weekly summary query to identify failed Hyperscale geo-restore requests, then drills into each failure's root cause using region-specific Kusto queries. The time window is fixed to the past 7 days.
---

# Debug Hyperscale Geo-Restore Failures

Analyze weekly Hyperscale geo-restore metrics and investigate individual failure reasons across Kusto regions.

## Purpose

This skill provides a two-phase analysis:
1. **Weekly Metrics Summary** — Run the weekly Hyperscale geo-restore metrics query to identify all failed requests
2. **Per-Failure Root Cause Drill-Down** — For each failed request, query the specific Kusto region to determine the failure reason

## Required Information

No user input required — the query automatically analyzes the past 7 days using `ago(7d)`.

### Derived by Skill:
- **Region-specific kusto-cluster-uri** — Determined from failure records for drill-down queries
- **Failed request details** — Extracted from weekly summary (request IDs, server names, database names, regions)

## When to Use This Skill

- Weekly Hyperscale geo-restore metrics review
- Investigating patterns of Hyperscale geo-restore failures
- Triaging recurring failure types across regions
- Generating weekly summary reports for on-call or team reviews

## Workflow

### Phase 1: Weekly Metrics Summary

Run the weekly Hyperscale geo-restore metrics query to get an overview of all requests and identify failures.

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Get weekly Hyperscale backup restore metrics summary (past 7 days)"
- parameters: 
  {
    "cluster-uri": "https://sqlstage.kusto.windows.net",
    "database": "sqlazure1",
    "query": "let restoresInGivenPeriod = ago(7d); let chunkSize = 4; let SingleCluster = (clstr: string){ cluster(clstr).database('sqlazure1').MonRestoreRequests | where TIMESTAMP > restoresInGivenPeriod | where ClusterName !contains 'lkg' and ClusterName !contains 'onebox' | extend restore_request_id = tolower(restore_request_id) | join kind=inner ( cluster(clstr).database('sqlazure1').MonManagement | where originalEventTimestamp > restoresInGivenPeriod | where ClusterName !contains 'lkg' and ClusterName !contains 'onebox' | where operation_parameters has '<IsCrossServerRestore>false</IsCrossServerRestore>' | extend restore_id = tolower(extract('<RestoreId>(.*)</RestoreId>', 1, operation_parameters)) | project mo_request_id = request_id, isGeoRestore=true, restore_id ) on $left.restore_request_id == $right.restore_id | join (cluster(clstr).database('sqlazure1').MonManagement | where state_machine_type == 'RestoreRequestStateMachine' | summarize by keys, request_id) on $left.restore_id == $right.['keys'] | extend operation_request_id = request_id | where source_edition == 'Hyperscale' | summarize arg_min(TIMESTAMP, start_time), arg_min(TIMESTAMP, end_time) by ClusterName, subscription_id, restore_request_id, state, operation_request_id, mo_request_id, source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name | project ClusterName, restore_request_id, state, start_time, end_time, StartTimeForState = TIMESTAMP, operation_request_id, mo_request_id, source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name, subscription_id | summarize arg_max(StartTimeForState, *) by restore_request_id | project ClusterName, restore_request_id, mo_request_id, state, start_time, end_time = iff(end_time == datetime(1601-01-01 00:00:00.0000000), now(), end_time), source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name, operation_request_id, subscription_id | project ClusterName, restore_request_id, mo_request_id, RestoreEndState = state, RestoreDurationMin = todouble(datetime_diff('Minute', end_time, start_time)), source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name, operation_request_id, subscription_id | join kind=leftouter ( cluster(clstr).database('sqlazure1').MonManagement | where originalEventTimestamp > restoresInGivenPeriod | where (event=='management_operation_success' or event=='management_operation_failure' or event=='management_operation_cancel' or event=='management_operation_fatal_error') | extend TargetLogicalDbId = toupper(tostring(parse_xml(operation_result).OutputParameters.LogicalDatabaseId)) | project ClusterName, event, RestoreCompleteTime = originalEventTimestamp, subscription_id, request_id, TargetLogicalDbId, RestoreDurationFromMOMin = todouble(round(elapsed_time_milliseconds/60000, 1)) | summarize arg_max(RestoreDurationFromMOMin, *) by request_id ) on $left.mo_request_id == $right.request_id | project ClusterName, subscription_id, restore_request_id, request_id = mo_request_id, source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name, TargetLogicalDbId, RestoreCompleteTime, RestoreEndState, RestoreDuration = iff(RestoreDurationFromMOMin > RestoreDurationMin, RestoreDurationFromMOMin, RestoreDurationMin) | extend RestoreResult = iff(RestoreEndState == 'WaitingForOperationToComplete' or RestoreEndState == 'WaitingForRollbackToComplete' or RestoreEndState == 'PostConditionCheck', iff(RestoreDuration > 60 or isnull(RestoreDuration), 'In Progress Long Running', ''), RestoreEndState) | project ClusterName, subscription_id, restore_request_id, request_id, source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name, TargetLogicalDbId, RestoreDuration, RestoreResult, RestoreCompleteTime | extend Env = iff(ClusterName has 'sqltest', 'Test', 'Prod') | extend Customer = iff(toupper(subscription_id) == 'CC5C9C30-E97B-4698-90D8-2D31E535EA88' or toupper(subscription_id) == '1422D516-3EE5-4DEF-8A2E-91574676C4D7' or toupper(subscription_id) == toupper('3547812f-a248-4853-8b52-fe1a16336f97'), 'Internal Runner Subscription', 'Customer') | where Env == 'Prod' and Customer == 'Customer' | project ClusterName, subscription_id, restore_request_id, source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name, TargetLogicalDbId, RestoreDuration, RestoreResult, RestoreCompleteTime, request_id, logical_db_id = TargetLogicalDbId | join kind=leftouter ( cluster(clstr).database('sqlazure1').MonSocrates | where TIMESTAMP > datetime_add('day', -1, restoresInGivenPeriod) | where AppTypeName == 'Vldb.XLog' | distinct logical_db_id, AppName ) on logical_db_id | join kind=leftouter ( cluster(clstr).database('sqlazure1').MonXlogSrv | where TIMESTAMP > datetime_add('day', -1, restoresInGivenPeriod) | where event contains 'xlog_output' | where message contains 'snipLTPostLZRestore' | join ( cluster(clstr).database('sqlazure1').MonXlogSrv | where event contains 'xlog_output' | project AppName, LTEol = iff(message contains 'snipLTPostLZRestore', extract('BSN: (0x[\\da-f]+)', 1, message), ''), FirstVlfId = iff(message contains 'FirstVlfId : ', extract('FirstVlfId : \\[(\\d+)\\]', 1, message), ''), VlfSizeInMb = iff(message contains 'VlfSizeInMb', extract('VlfSizeInMb : \\[(\\d+)\\]', 1, message), '') | summarize LTEol = tolong(anyif(LTEol, isnotempty(LTEol))), FirstVlfId = toint(anyif(FirstVlfId, isnotempty(FirstVlfId))), VlfSizeInMb = toint(anyif(VlfSizeInMb, isnotempty(VlfSizeInMb))) by AppName ) on AppName | project originalEventTimestamp, AppName, NodeName, collect_current_thread_id, message, VlfSizeInMb, FirstVlfId, LTEol | project AppName, BSN = tolong(extract('BSN: (0x[0-9a-fA-F]+),', 1, message)), VlfSizeInMb, FirstVlfId, LTEol | extend vlfId = FirstVlfId + LTEol * 512 / (VlfSizeInMb * 1024 * 1024), vlfOffset = LTEol * 512 % (VlfSizeInMb * 1024 * 1024) / 512 | extend BSNLSN = toupper(strcat(tohex(vlfId, 8), ':', tohex(vlfOffset, 8), ':0001')) ) on AppName | join kind=leftouter ( cluster(clstr).database('sqlazure1').MonManagement | where TIMESTAMP > datetime_add('day', -1, restoresInGivenPeriod) | where event == 'vldb_restore_plan_generation_troubleshooting' | where message_systemmetadata contains 'The chosen page server snapshots are' | extend array = extract_all('PageServerId: ([0-9]+), ReplicaId: ([0-9]+), SnapshotTime: ([0-9APM:/ ]+)', message_systemmetadata) | project request_id, array | mv-expand array | project request_id, PageServerId = tostring(array[0]), ReplicaId = tostring(array[1]), SnapshotTime = tostring(array[2]) ) on request_id | join kind=leftouter ( cluster(clstr).database('sqlazure1').MonManagement | where TIMESTAMP > datetime_add('day', -1, restoresInGivenPeriod) | where event == 'vldb_restore_plan_generation_troubleshooting' | where message_systemmetadata contains 'Including potential snapshot' | extend BeginLSN = extract('BeginLSN: ([0-9:A-F]+),', 1, message_systemmetadata), PageServerId = extract('PageServerId: ([0-9]+),', 1, message_systemmetadata), SnapshotTime = extract('SnapshotTime: ([0-9APM:/ ]+)', 1, message_systemmetadata), ReplicaId = extract('ReplicaId: ([0-9]+),', 1, message_systemmetadata) | project request_id, BeginLSN, PageServerId, ReplicaId, SnapshotTime ) on request_id, PageServerId, ReplicaId, SnapshotTime | extend PSLsnSegment1 = tostring(split(BeginLSN, ':')[0]), PSLsnSegment2 = tostring(split(BeginLSN, ':')[1]) | extend vlfIdOfLsnPSLsnSegment1InByte = toint(strcat('0x', PSLsnSegment1)), blockOffsetOfLsnPSLsnSegment2InByte = toint(strcat('0x', PSLsnSegment2)) | extend PSvlfsSinceBaseVlf = vlfIdOfLsnPSLsnSegment1InByte - FirstVlfId | extend PStotalBytesOfLsn = (PSvlfsSinceBaseVlf * VlfSizeInMb * 1024 * 1024) + blockOffsetOfLsnPSLsnSegment2InByte*512 | extend PStotalBytesOfLsnToBsn = PStotalBytesOfLsn / 512 | extend psStartBsn = PStotalBytesOfLsnToBsn | extend PSRedoSizeInBytes = (BSN - psStartBsn) * 512 | extend PSRedoSizeInMB = PSRedoSizeInBytes/1024/1024 | project ClusterName, subscription_id, restore_request_id, source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name, RestoreDuration, RestoreResult, RestoreCompleteTime, request_id, logical_db_id, PageServerId, ReplicaId, SnapshotTime, BeginLSN, BSN, BSNLSN, isCorrupt = strcmp(BeginLSN, BSNLSN), PSRedoSizeInMB | summarize sum(PSRedoSizeInMB) by RestoreDuration, RestoreResult, ClusterName, subscription_id, restore_request_id, source_logical_server_name, source_logical_database_name, target_logical_server_name, target_logical_database_name, logical_db_id, request_id | extend TargetLogicalDbId = logical_db_id | join kind=leftouter ( cluster(clstr).database('sqlazure1').MonBlobClient | where event == 'blobclient_copy_blob_from_snapshot_begin' and source_file_path_format contains 'snapshot' | join kind=leftouter ( cluster(clstr).database('sqlazure1').MonBlobClient | where event == 'blobclient_copy_blob_from_snapshot_complete' ) on copy_id | extend totalTime = datetime_diff('second', PreciseTimeStamp1, PreciseTimeStamp) | where totalTime > 0 | project mbPerSec = bytes_copied1 / 1024 / 1024 / totalTime, TargetLogicalDbId = toupper(tostring(split(target_file_name, '_', 0)[0])) | summarize avg(mbPerSec) by TargetLogicalDbId ) on $left.TargetLogicalDbId == $right.TargetLogicalDbId | join kind=leftouter ( cluster(clstr).database('sqlazure1').MonBlobClient | where TIMESTAMP > restoresInGivenPeriod | where api_name == 'WritePagesFromUri' | where request_id == toupper(request_id) | as MonBlobClientRequestId | where event == 'cloud_blob_client_operation_begin' | where extractjson('$.Parameters.targetContainerName', parameters_with_scrubbed_values_resource_name, typeof(string)) contains 'pageserver-' | join kind=leftouter ( MonBlobClientRequestId | where event == 'cloud_blob_client_operation_complete' ) on azure_storage_client_request_id | summarize arg_min(originalEventTimestamp, uri, request_id), arg_max(originalEventTimestamp1, uri, request_id), count() by uri, request_id | extend CopyTimeInSecPerBlob = datetime_diff('Second', originalEventTimestamp1, originalEventTimestamp) | extend ChunkCopyMbPerSecPerBlob = count_ * chunkSize / CopyTimeInSecPerBlob | summarize avg(ChunkCopyMbPerSecPerBlob) by request_id ) on request_id | extend RegionName = extract(@'^[^.]+\\.(?<region>[^-.]+)', 1, ClusterName) | project RestoreDuration, RestoreResult, RegionName, restore_request_id, PSRedoSize = strcat(sum_PSRedoSizeInMB, ' MB'), ServerAsyncCopy = iff(isempty(avg_mbPerSec), 'N/A', strcat(round(avg_mbPerSec, 2), ' MB/s')), ChunkCopy = iff(isempty(avg_ChunkCopyMbPerSecPerBlob), 'N/A', strcat(round(avg_ChunkCopyMbPerSecPerBlob, 2), ' MB/s')), source_logical_database_name, target_logical_server_name, target_logical_database_name }; _ExecuteForProdAndStageClusters | order by RestoreResult asc, RestoreDuration desc"
  }
```

**Note**: This query uses `_ExecuteForProdAndStageClusters` to fan out across all production and stage clusters. It must be executed against the **sqlstage** cluster.

**Output columns:**
- **RestoreDuration** — Duration in minutes
- **RestoreResult** — Final state (e.g., success, failure, `In Progress Long Running`)
- **RegionName** — Region extracted from cluster name (e.g., `eastus2`, `northeurope`)
- **restore_request_id** — Unique restore request ID
- **PSRedoSize** — Page server redo size in MB
- **ServerAsyncCopy** — Async copy throughput (MB/s) or N/A
- **ChunkCopy** — Chunk copy throughput (MB/s) or N/A
- **source_logical_database_name** — Source database
- **target_logical_server_name** — Target server
- **target_logical_database_name** — Target database

**Analysis:**
- Count total requests, successes, failures
- Calculate success rate
- Group failures by ClusterName (region) and RestoreResult
- Identify long-running restores (RestoreDuration > 60 min)
- Flag entries with low copy throughput (ServerAsyncCopy or ChunkCopy)
- Identify top failure categories

### Phase 2: Per-Failure Root Cause Drill-Down

For each failed request from Phase 1, use the **`hs-georestore`** skill (located at `BackupRestore/hs-georestore`) to investigate the failure reason. The `hs-georestore` skill verifies the operation is a geo-restore, classifies user vs system errors, and checks whether the failure is caused by storage account geo-replication lag.

#### Step 2a: Resolve Region Kusto Cluster

Map the `RegionName` from Phase 1 results to the appropriate Kusto cluster URI. Common mappings:

| Region Keyword | Kusto Cluster |
|---------------|---------------|
| eastus | `https://sqlazureeus12.kusto.windows.net:443` |
| eastus2 | `https://sqlazureeus22.kusto.windows.net:443` |
| westus | `https://sqlazurewus1.kusto.windows.net:443` |
| westus2 | `https://sqlazurewus22.kusto.windows.net:443` |
| northeurope | `https://sqlazureneu2.kusto.windows.net:443` |
| westeurope | `https://sqlazureweu2.kusto.windows.net:443` |
| southeastasia | `https://sqlazureseas2.kusto.windows.net:443` |
| eastasia | `https://sqlazureeas2.kusto.windows.net:443` |

If the region is not in the list, use the `execute-kusto-query` skill's [findClusterFromRegion](../../Common/execute-kusto-query/references/findClusterFromRegion.md) reference to resolve the appropriate Kusto cluster URI.

#### Step 2b: Invoke hs-georestore Skill for Each Failure

For each failed request identified in Phase 1, invoke the **`hs-georestore`** skill (located at `BackupRestore/hs-georestore`) with:

| Input | Source from Phase 1 |
|-------|-------------------|
| **request_id** | `restore_request_id` from Phase 1 results |
| **Region** | `RegionName` from Phase 1 results |
| **source_logical_server_name** | `source_logical_server_name` from Phase 1 |
| **source_logical_database_name** | `source_logical_database_name` from Phase 1 |
| **target_logical_server_name** | `target_logical_server_name` from Phase 1 |
| **target_logical_database_name** | `target_logical_database_name` from Phase 1 |

The `hs-georestore` skill will:
1. Verify the operation is a geo-restore (not a database copy) using the `IsCrossServerRestore` check (QHGR05)
2. Establish the operation timeline and status (QHGR10)
3. Classify the error as User Error or System Error
4. If System Error — check storage account geo-replication lag (QHGR20) to determine if the failure is due to replication sync delay
5. If geo-replication lag is not the cause — recommend escalation to `hs-restore` for full 4-phase pipeline investigation

> **Note**: For failures where the `hs-georestore` skill cannot determine the root cause (e.g., geo-replication lag is healthy but restore still failed), escalate to the `hs-restore` skill for deeper analysis with the full set of 24 diagnostic queries.

#### Step 2c: Classify Failure

After `hs-georestore` completes for each failure, categorize using the root cause from its report:

| Failure Category | Description | Typical Action |
|-----------------|-------------|----------------|
| User Error | Invalid point-in-time, server not found, database exists, AKV issues, quota exceeded | No action — customer issue |
| Geo-Replication Lag | Storage account geo-replication sync delay caused the restore to fail or use a stale restore point | Monitor storage account replication; retry after lag recovers |
| Not a Geo-Restore | Operation identified as database copy, not geo-restore | Route to `hs-restore` or `restore-failure` skill |
| System Error (Unknown) | System error but geo-replication lag is healthy — root cause undetermined by `hs-georestore` | Escalate to `hs-restore` for full 4-phase pipeline investigation |
| *New categories* | *Add as new failure patterns are identified* | *Document mitigation* |

> 🚩 **Unknown failure types** (System Error with healthy geo-replication) should be escalated to `hs-restore` for deeper investigation and flagged for manual review.

### Phase 3: Generate Weekly Report

First produce a concise executive summary, then optionally follow with detailed drill-down.

#### Step 3a: Concise Summary (always generate)

Group failures by distinct root cause error message. Combine failures sharing the same error/reason into one line with a count. List successes as a single line at the end.

**Format:**

> ## 📊 Weekly Hyperscale Backup Restore Report
> Week ending {MM/DD/YYYY}
> - 🚩 {count} failure(s) with unknown root cause — **needs manual investigation** (restore_request_id: {id1}, {id2}, ...)  ← only if applicable, always list first
> - {count} Customer failure(s) due to {short cause description} ({exact error message or key excerpt from the failure})
> - {count} Customer failure(s) due to {short cause description} ({exact error message or key excerpt from the failure})
> - {count} in progress (long running > 60 min) ← only if applicable
> - {success_count} success

**Rules:**
- If any failure's root cause cannot be determined after Phase 2 drill-down, list it **first** with 🚩 and include the restore_request_id(s) so the on-call engineer can investigate manually
- Deduplicate failures by root cause — combine failures with the same error message/reason into one line with a count
- Use the actual error message or key excerpt in parentheses so the reader can identify the exact error
- Keep each failure line to one sentence — short cause description + error detail
- Do not include tables or per-request breakdowns in this summary
- If there are in-progress long-running restores (> 60 min), add a separate line for them

**Example:**

> ## 📊 Weekly Hyperscale Backup Restore Report
> Week ending 4/14/2026
> - 🚩 1 failure with unknown root cause — **needs manual investigation** (restore_request_id: 928f03b5-b27a-49b8-80ff-27243c427ffb)
> - 2 Customer failures due to run out of capacity in the elastic pool (The elastic pool 'HyperscalePool1' has reached its database count limit. The database count for the elastic pool cannot exceed (25) for service tier 'Hyperscale'.)
> - 1 Customer failure due to AKV setup Azure Key Vault key URI 'https://...' is required to successfully restore the database '...' under server '...'.
> - 108 success

#### Step 3b: Detailed Drill-Down (only when user requests)

If the user asks for details, expand with per-failure analysis:

> ### Detailed Failure Analysis
> | # | Server | Database | Region | Root Cause | Error Detail |
> |---|--------|----------|--------|-----------|--------------|
> | 1 | {server} | {db} | {region} | {short cause} | {full error message} |
> 
> ### Recommended Actions
> {Numbered list of mitigation steps grouped by failure category}

## Extending This Skill

### Adding Failure Categories
Update the classification table in Step 2c as new failure patterns are identified.

## Related Skills

- **hs-georestore** — Per-failure geo-restore investigation (geo-restore verification, error classification, geo-replication lag check)
- **hs-restore** — Full Hyperscale restore investigation (4-phase pipeline with 24 queries). Escalate here when `hs-georestore` cannot determine root cause
- **backup-restore-insights** — Initial triage for general backup/restore issues
- **restore-failure** — Debug individual Sterling restore failures
