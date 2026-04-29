# Non-Yielding Scheduler Analysis: RowsetIndexStats::GetNextAllHoBts

---

## 1. Problem Summary

A non-yielding scheduler condition occurs when querying index stats DMVs (e.g., `sys.dm_db_index_physical_stats`, `sys.dm_db_index_operational_stats`) on databases with a large number of tables, partitions, and indexes. The issue is triggered specifically when the metadata cache has a high hit rate — meaning most objects are already cached in memory.

The key finding is that the yield behavior depends on whether metadata objects are served from cache or loaded from disk. When objects are cached, the HoBt iteration loop runs as a tight CPU-bound loop with no yield opportunity, eventually triggering non-yielding scheduler detection.

---

## 2. Root Cause Analysis

### 2.1 The Core Loop — `GetNextAllHoBts()`

**Source file:** `/Sql/Ntdbms/storeng/dfs/schemamanager/source/hobtstats.cpp` (line 793-934)

The function `RowsetIndexStats::GetNextAllHoBts()` iterates over all HoBt (Heap or B-Tree) objects in a database. The core loop has **no built-in yield point**:

```cpp
// hobtstats.cpp line 816-930
do
{
    BaseSharedHoBt* pSchema = m_HashScanContext.GetNextHoBt();

    while (pSchema)   // ← tight loop, NO yield inside
    {
        // 1. Acquire KP latch on the HoBt
        // 2. Look up object metadata via CMEDProxyDatabase::GetObjectByObjectId
        // 3. Check object attributes (e.g., skip Hekaton tables)
        // 4. Release KP latch

        pSchema->m_Latch.Release(LatchBase::KP);
        pSchema = m_HashScanContext.GetNextHoBt();  // next iteration
    }
} while (Available == LockAndSetNextDatabase());
```

**Key observation:** There is no `SOS_Task::Yield()` or equivalent yield check anywhere in this `while` loop. Whether the scheduler yields or not depends entirely on what happens inside `GetObjectByObjectId`.

### 2.2 Two Execution Paths

#### Path A: Metadata Cache MISS (yields normally)

When the metadata object is **not** in cache, SQL Server must read it from disk:

```
GetObjectByObjectId
→ CMEDCatalogObject::GetCachedObjectById     (cache miss)
→ CMEDCatYukonObject::FLookupObjectFromId
→ ECatBitsYukon::FLocateObjRowById
→ CMEDScan::StartSearch
→ RowsetNewSS::FetchRowByKeyValue
→ IndexDataSetSession::FetchRowByKeyValueInternal
→ GetRowForKeyValue
→ IndexPageManager::GetPageWithKey
→ BTreeMgr::GetHPageIdWithKey
→ BTreeMgr::Seek
→ BTreeMgr::HandleRoot
→ FixPage                    ← Page I/O
→ SOS_Task::OSYield          ← ✅ YIELD HAPPENS HERE
→ SOS_Task::Sleep
```

The I/O wait in `FixPage` triggers a scheduler yield. This is why a repro with cold cache works fine — every HoBt iteration includes an I/O wait that allows other tasks to run.

#### Path B: Metadata Cache HIT (NO yield — the bug)

When the metadata object **is** in cache, the entire operation stays in memory:

```
GetObjectByObjectId
→ CMEDProxyDatabase::GetObjectByObjectId     (cache HIT — returns immediately)
→ CMEDProxyObject::~CMEDProxyObject          (cleanup)
→ SMD::ReleaseObjectLock
→ LockReference::Release                     ← ❌ NO YIELD, pure CPU
```

No I/O occurs, so no yield happens. The `while (pSchema)` loop runs as a tight CPU-bound loop. With tens of thousands of HoBts all cached, this loop can run for seconds or even minutes without yielding, triggering the non-yielding scheduler detection (default threshold: 60 seconds).

### 2.3 Visual Comparison

```
                    GetNextAllHoBts() loop
                    ┌─────────────────────┐
                    │  GetNextHoBt()       │
                    │  ↓                   │
                    │  GetObjectByObjectId │
                    │  ↓                   │
              ┌─────┴─────┐               │
         Cache MISS    Cache HIT           │
              │            │               │
         BTree Seek   Return immediately   │
              │            │               │
         FixPage       Release lock        │
              │            │               │
         ★ YIELD ★    ❌ NO YIELD          │
              │            │               │
              └─────┬─────┘               │
                    │  Next HoBt           │
                    └──────────────────────┘
```

### 2.4 Callstack Evidence

**Attempted repro (cold cache — yields normally):**

```
00 sqlmin!SOS_Task::Sleep                          ← yield point
01 sqlmin!SOS_Task::OSYield
02 sqlmin!FixPageNoCheck
03 sqlmin!FixPage
04 sqlmin!BTreeMgr::HandleRoot
05 sqlmin!BTreeMgr::Seek
06 sqlmin!BTreeMgr::GetHPageIdWithKey
07 sqlmin!IndexPageManager::GetPageWithKey
08 sqlmin!GetRowForKeyValue
...
11 sqlmin!ECatBitsYukon::FLocateObjRowById         ← metadata loaded from disk
12 sqlmin!CMEDCatYukonObject::FLookupObjectFromId
13 sqlmin!CMEDCatalogObject::GetCachedObjectById    ← cache miss
14 sqlmin!CMEDProxyDatabase::GetObjectByObjectId
15 sqlmin!RowsetIndexStats::GetNextAllHoBts
```

**Customer environment (warm cache — non-yielding):**

```
sqlmin!LockReference::Release                      ← no yield, pure CPU
sqlmin!SMD::ReleaseObjectLock
sqlmin!CMEDProxyObject::~CMEDProxyObject            ← cached object cleanup
sqlmin!CMEDProxyObject::`vector deleting destructor`
sqlmin!CMEDAccess::~CMEDAccess
sqlmin!CMEDAccess::`vector deleting destructor`
sqlmin!RowsetIndexStats::GetNextAllHoBts            ← same loop, no I/O path
sqlmin!RowsetIndexStats::InternalGetRow
sqlmin!CQScanTVFStreamNew::GetRow
sqlmin!CQScanLightProfileNew::GetRow
sqlmin!CQScanStreamAggregateNew::GetRowHelper
sqlmin!CQScanStreamAggregateNew::GetCalculatedRow
...
sqllang!process_request
```

---

## 3. Related Bugs

### Bug 2292797 — SQL Server 2022

| Field | Value |
|-------|-------|
| **Link** | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2292797 |
| **State** | New (unfixed) |
| **Area** | SQL Engine → Access Methods |
| **Version** | SQL 2022 (16.0.937.2220) |
| **Watson Bucket** | [2056126](https://azurewatson.microsoft.com/bucket/2056126) |
| **Related Legacy Bug** | [12721321](https://sqlbuvsts01/Main/SQL%20Server/_workitems#_a=edit&id=12721321) (old TFS) |

**Callstack:** Non-yielding occurs during query optimization when auto-create statistics triggers `GetRowCount` for each partition's HoBt via recursive `CStatsTree::FInitStatMan` calls (14 levels deep). All metadata is cached, so the entire recursion runs without yielding.

```
PartitionedCounter::GetCounterAndCorrectNegative  (hobtstats.inl:400)
→ BaseSharedHoBt::GetRowCount                     (schemamgr.inl:1246)
→ HoBtFactory::GetRowsetCountsForQp               (schemamgr.cpp:7039)
→ GetIndexSizeData → CIStatManFactory
→ CStatsTree::FInitStatMan                        (recursive, 14 levels)
→ CStatsTreeManager::UpdateAndPersistStatsTree
→ CStatsUtil::CreateQPStats
→ CStmtCreateStats::XretExecute                   ← AUTO_CREATE_STATISTICS
→ COptContext::PcxteOptimizeQuery                  ← query optimization
```

### Bug 4881252 — SQL Server 2025

| Field | Value |
|-------|-------|
| **Link** | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4881252 |
| **State** | New (unfixed) |
| **Area** | SQL Engine → Access Methods |
| **Version** | SQL 2025 (2025.170.924.10217) |
| **Watson Bucket** | [FailureHash: 893508c5-db5f-bb1b-6418-0ab0b031562f](https://portal.watson.azure.com/bucket?$filter=(FailureInfo_FailureHash%20eq%20893508c5-db5f-bb1b-6418-0ab0b031562f)) |

**Callstack:** Nearly identical to Bug 2292797 — same `GetRowCount` → `GetRowsetCountsForQp` → recursive `FInitStatMan` path during UPDATE STATISTICS. Confirms this bug persists into SQL 2025.

### Bug Summary

| Bug ID | SQL Version | State | Trigger | Root Cause |
|--------|-------------|-------|---------|------------|
| [2292797](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2292797) | SQL 2022 | **New** | Auto-create stats during query optimization | `GetRowCount` loop over cached HoBts, no yield |
| [4881252](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4881252) | SQL 2025 | **New** | UPDATE STATISTICS | Same root cause |
| Current case | SQL 2022 | — | Index stats DMV query | `GetNextAllHoBts` loop over cached HoBts, no yield |

All three share the same fundamental issue: **HoBt iteration loops in `hobtstats.cpp` / `schemamgr.inl` lack periodic yield checks when metadata is served from cache.**

---

## 4. Next Steps — Customer Environment Checks

### 4.1 Confirm HoBt Count

```sql
-- Total HoBt count across the database
SELECT 
    DB_NAME() AS database_name,
    COUNT(*) AS total_hobts,
    COUNT(DISTINCT object_id) AS distinct_objects,
    SUM(CASE WHEN index_id = 0 THEN 1 ELSE 0 END) AS heaps,
    SUM(CASE WHEN index_id = 1 THEN 1 ELSE 0 END) AS clustered_indexes,
    SUM(CASE WHEN index_id > 1 THEN 1 ELSE 0 END) AS nonclustered_indexes
FROM sys.partitions
WHERE index_id >= 0;

-- Top tables by partition count
SELECT TOP 20
    OBJECT_SCHEMA_NAME(object_id) + '.' + OBJECT_NAME(object_id) AS table_name,
    COUNT(*) AS partition_count,
    COUNT(DISTINCT index_id) AS index_count
FROM sys.partitions
WHERE index_id >= 0
GROUP BY object_id
ORDER BY COUNT(*) DESC;
```

If total HoBts > 10,000, the risk of non-yielding increases significantly with warm cache.

### 4.2 Confirm Metadata Cache State

```sql
-- Metadata memory cache stats
SELECT 
    type,
    pages_kb / 1024 AS size_mb,
    entries_count
FROM sys.dm_os_memory_cache_counters
WHERE type LIKE '%Object%' 
   OR type LIKE '%Schema%'
   OR type LIKE '%Metadata%'
ORDER BY pages_kb DESC;

-- Buffer pool usage for system catalog pages
SELECT 
    DB_NAME(database_id) AS db_name,
    COUNT(*) AS cached_pages,
    COUNT(*) * 8 / 1024 AS cached_mb
FROM sys.dm_os_buffer_descriptors
WHERE database_id = DB_ID()
  AND page_type = 'DATA_PAGE'
GROUP BY database_id;
```

### 4.3 Identify the Triggering Query

```sql
-- Check for recent non-yielding scheduler events
EXEC xp_readerrorlog 0, 1, N'non-yielding';

-- Check active queries accessing index DMVs
SELECT 
    r.session_id,
    r.status,
    r.command,
    r.wait_type,
    r.cpu_time,
    r.total_elapsed_time,
    SUBSTRING(t.text, 1, 200) AS query_text
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE t.text LIKE '%dm_db_index%'
   OR t.text LIKE '%index_physical_stats%'
   OR t.text LIKE '%index_operational_stats%';
```

### 4.4 Check for Monitoring Tools

Look for scheduled jobs or external monitoring tools that periodically scan index DMVs:

```sql
-- Check SQL Agent jobs that reference index DMVs
SELECT j.name, js.step_name, js.command
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps js ON j.job_id = js.job_id
WHERE js.command LIKE '%dm_db_index%'
   OR js.command LIKE '%index_physical_stats%'
   OR js.command LIKE '%index_operational_stats%'
   OR js.command LIKE '%index_usage_stats%';
```

Common culprits: SolarWinds, Redgate SQL Monitor, Idera, Ola Hallengren maintenance scripts, custom monitoring queries.

### 4.5 Analyze the Non-Yielding Dump

If a memory dump was generated during the non-yielding event:

1. Verify the callstack matches the pattern described in Section 2.4
2. Check `process_commands_internal` or `process_request` at the bottom of the stack
3. Look for `RowsetIndexStats::GetNextAllHoBts` or `BaseSharedHoBt::GetRowCount` in the faulting thread
4. Confirm the absence of `FixPage` / `BTreeMgr::Seek` in the stack (indicates cache hit path)

---

## 5. Workarounds

Since this is a known unfixed product bug (Bug 2292797 / 4881252), the following mitigations are recommended:

| # | Workaround | Details |
|---|-----------|---------|
| 1 | **Scope DMV queries** | Always use `WHERE object_id = ...` or `WHERE database_id = ...` filters when querying index DMVs. Avoid unfiltered scans such as `SELECT * FROM sys.dm_db_index_physical_stats(NULL, NULL, NULL, NULL, NULL)`. |
| 2 | **Reduce monitoring frequency** | If a monitoring tool runs index DMV queries every few minutes, increase the interval to reduce collision with warm cache. |
| 3 | **Consolidate partitions** | If there are many empty or unused partitions, consider merging them to reduce total HoBt count. |
| 4 | **Drop unused indexes** | Each unused index adds HoBts to the iteration. Removing them reduces the loop iteration count. |
| 5 | **Schedule during low cache period** | Run index DMV queries shortly after SQL Server restart (cold cache) when yields occur naturally through I/O. This is a last-resort option. |

---

## 6. Recommendation to PG

This case should be linked to **Bug 2292797** and **Bug 4881252** with the following additional evidence:

1. A new trigger path: `GetNextAllHoBts` → `CMEDProxyObject` cached metadata path (vs. the existing `GetRowCount` → `GetRowsetCountsForQp` path in the filed bugs)
2. Clear demonstration that cache hit vs. cache miss determines yield behavior
3. The `while (pSchema)` loop in `hobtstats.cpp:816-930` needs a periodic yield check

Suggested fix: Add a periodic `SOS_Task::Yield()` call inside the `GetNextAllHoBts()` loop, for example every 1000 iterations, similar to other long-running scan loops in the engine.

---

## 7. References

| Source | Link |
|--------|------|
| Bug 2292797 (SQL 2022) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2292797 |
| Bug 4881252 (SQL 2025) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4881252 |
| Legacy Bug 12721321 | https://sqlbuvsts01/Main/SQL%20Server/_workitems#_a=edit&id=12721321 |
| Source: hobtstats.cpp | `/Sql/Ntdbms/storeng/dfs/schemamanager/source/hobtstats.cpp` |
| Source: schemamgr.inl | `/Sql/Ntdbms/storeng/include/schemamgr.inl` |
| Source: hobtstats.inl | `/Sql/Ntdbms/storeng/include/hobtstats.inl` |
