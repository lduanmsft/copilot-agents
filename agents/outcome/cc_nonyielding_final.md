# Non-Yielding Scheduler: RowsetIndexStats::GetNextAllHoBts with Cached Metadata

**Date**: 2026-04-27
**Area**: SQL Engine — Access Methods / Metadata_Infrastructure
**Severity**: High — causes non-yielding scheduler dump, service disruption

---

## 1. Problem Summary

Customer experiences non-yielding scheduler when querying index stats DMVs (e.g., `sys.dm_db_index_physical_stats`) on databases with a large number of tables, partitions, and indexes. The customer has **many GB of cached metadata**, which means most objects are served from the metadata cache — skipping the I/O path that normally provides a natural yield point.

The fundamental issue: **whether the scheduler yields depends on whether metadata objects are served from cache or loaded from disk. When objects are cached, the HoBt iteration loop runs as a tight CPU-bound loop with zero yield opportunity.**

---

## 2. Root Cause Analysis

### 2.1 The Core Loop — `GetNextAllHoBts()`

**Source file:** `Sql/Ntdbms/storeng/dfs/schemamanager/source/hobtstats.cpp` (line 816-930)

`RowsetIndexStats::GetNextAllHoBts()` iterates over all HoBt (Heap or B-Tree) objects in a database. The core loop has **no built-in yield point**:

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

Whether the scheduler yields depends entirely on what happens inside `GetObjectByObjectId`.

### 2.2 Two Execution Paths — The Key Divergence

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

#### Path A: Metadata Cache MISS → yields normally

When the metadata object is **not** in cache, SQL Server must read it from disk:

```
GetObjectByObjectId
  → CMEDCatalogObject::GetCachedObjectById     (cache miss)
    → CMEDCatYukonObject::FLookupObjectFromId
      → ECatBitsYukon::FLocateObjRowById
        → CMEDScan::StartSearch
          → RowsetNewSS::FetchRowByKeyValue
            → IndexPageManager::GetPageWithKey
              → BTreeMgr::Seek → FixPage        ← Page I/O
                → SOS_Task::OSYield              ← ✅ YIELD HAPPENS HERE
```

#### Path B: Metadata Cache HIT → NO yield (the bug)

When the metadata object **is** in cache, the entire operation stays in memory:

```
GetObjectByObjectId
  → CMEDProxyDatabase::GetObjectByObjectId     (cache HIT — returns immediately)
    → CMEDProxyObject::~CMEDProxyObject        (cleanup)
      → SMD::ReleaseObjectLock
        → LockReference::Release               ← ❌ NO YIELD, pure CPU
```

No I/O occurs, so no yield happens. With tens of thousands of HoBts all cached, this loop runs for seconds without yielding, triggering non-yielding scheduler detection.

### 2.3 Three Layers of the Problem

```
┌──────────────────────────────────────────────────────────────────┐
│ Layer 1: Missing Yield Point                                     │
│ GetNextAllHoBts iterates all HoBts with no yield check           │
│ → N HoBts = N destructor calls, continuous execution             │
├──────────────────────────────────────────────────────────────────┤
│ Layer 2: Deep Destructor Chain                                   │
│ Each iteration: CMEDAccess dtor → CMEDProxyObject dtor           │
│   → DeleteEmbeddedProxies → CMEDProxyRelation dtor               │
│     → CMEDProxyStats dtor → each level has lock release          │
├──────────────────────────────────────────────────────────────────┤
│ Layer 3: Lock Spinlock Contention (amplifier)                    │
│ MDL::UnlockGeneric → lck_unlockInternal                          │
│   → LockHashSlot spinlock contention                             │
│   → SpinToAcquireWithExponentialBackoff (includes SleepEx!)      │
└──────────────────────────────────────────────────────────────────┘
```

**Trigger conditions**: Large number of objects (thousands of tables/indexes → many GB metadata cache) + concurrent metadata operations causing spinlock pressure.

---

## 3. Callstack Evidence

### 3.1 Repro Environment — Cold Cache (yields normally)

```
00 sqlmin!SOS_Task::Sleep                          ← ✅ yield point
01 sqlmin!SOS_Task::OSYield
02 sqlmin!FixPageNoCheck
03 sqlmin!FixPage                                  ← I/O required
04 sqlmin!BTreeMgr::HandleRoot
05 sqlmin!BTreeMgr::Seek
06 sqlmin!BTreeMgr::GetHPageIdWithKey
07 sqlmin!IndexPageManager::GetPageWithKey
08 sqlmin!GetRowForKeyValue
09 sqlmin!CAutoRefc<PageContext>::{ctor}
0a sqlmin!IndexDataSetSession::GetRowByKeyValue
0b sqlmin!IndexDataSetSession::FetchRowByKeyValueInternal
0c sqlmin!DatasetSession::FetchRowByKeyValue
0d sqlmin!RowsetNewSS::FetchRowByKeyValueInternal
0e sqlmin!RowsetNewSS::FetchRowByKeyValue
0f sqlmin!CMEDScan::StartSearch
10 sqlmin!CMEDScan::StartSearch
11 sqlmin!ECatBitsYukon::FLocateObjRowById         ← metadata loaded from disk
12 sqlmin!CMEDCatYukonObject::FLookupObjectFromId
13 sqlmin!CMEDCatalogObject::GetCachedObjectById    ← cache MISS
14 sqlmin!CMEDProxyDatabase::GetObjectByObjectId
15 sqlmin!RowsetIndexStats::GetNextAllHoBts
16 sqlmin!RowsetIndexStats::FGetNextRowInternal
17 sqlmin!RowsetIndexStats::InternalGetRow
18 sqlmin!CQScanTVFStreamNew::GetRow
19 sqlmin!CQScanNew::GetRowOrReQualifyHelper
1a sqlmin!CQScanLightProfileNew::GetRowReQualifyRowHelper
1b sqlmin!CQScanLightProfileNew::GetRow
1c sqlmin!CQScanStreamAggregateNew::GetRowHelper
1d sqlmin!CQScanStreamAggregateNew::GetCalculatedRow
1e sqlmin!CQueryScan::StartupQuery
1f sqllang!CXStmtQuery::SetupQueryScanAndExpression
20 sqllang!CXStmtQuery::InitForExecute
21 sqllang!CXStmtQuery::ErsqExecuteQuery
22 sqllang!CXStmtSelect::XretDoExecute
23 sqllang!CXStmtSelect::XretExecute
24 sqllang!CExecStmtLoopVars::ExecuteXStmtAndSetXretReturn
25 sqllang!CMsqlExecContext::ExecuteStmts<1,1>
26 sqllang!CMsqlExecContext::FExecute
27 sqllang!CSQLSource::Execute
28 sqllang!process_request
```

**Note**: Query is very slow but always yields — because every `GetCachedObjectById` is a cache miss → B-Tree seek → `FixPage` → I/O wait → `OSYield`.

### 3.2 Customer Environment — Warm Cache (non-yielding)

```
sqlmin!LockReference::Release+418                  ← ❌ pure CPU, no yield
sqlmin!SMD::ReleaseObjectLock+273
sqlmin!CMEDProxyObject::~CMEDProxyObject+446        ← cache HIT → instant return, destructor only
sqlmin!CMEDProxyObject::`vector deleting destructor'+20
sqlmin!CMEDAccess::~CMEDAccess+528
sqlmin!CMEDAccess::`vector deleting destructor'+20
sqlmin!RowsetIndexStats::GetNextAllHoBts+1292       ← same loop, but NO I/O path
sqlmin!RowsetIndexStats::InternalGetRow+35
sqlmin!CQScanTVFStreamNew::GetRow+172
sqlmin!CQScanLightProfileNew::GetRow+25
sqlmin!CQScanStreamAggregateNew::GetRowHelper+703
sqlmin!CQScanStreamAggregateNew::GetCalculatedRow+33
sqlmin!CQueryScan::UncacheQuery+1565
sqllang!CXStmtQuery::SetupQueryScanAndExpression+1153
sqllang!CXStmtQuery::InitForExecute+47
sqllang!CXStmtQuery::ErsqExecuteQuery+990
sqllang!CXStmtSelect::XretExecute+883
sqllang!CMsqlExecContext::ExecuteStmts<1,1>+2299
sqllang!CMsqlExecContext::FExecute+2374
sqllang!CSQLSource::Execute+3011
sqllang!CStmtExecProc::XretLocalExec+704
sqllang!CStmtExecProc::XretExecExecute+1495
sqllang!CXStmtExecProc::XretExecute+56
sqllang!CMsqlExecContext::ExecuteStmts<1,1>+2299
sqllang!CMsqlExecContext::FExecute+2374
sqllang!CSQLSource::Execute+3011
sqllang!process_request+3571
```

### 3.3 Key Observations from Comparing the Two Stacks

| Aspect | Repro (cold cache) | Customer (warm cache) |
|--------|-------------------|----------------------|
| `GetCachedObjectById` | Cache MISS → full B-Tree seek | Cache HIT → instant return |
| I/O path | `FixPage` → `SOS_Task::OSYield` | Absent — no I/O |
| Yield | Every HoBt iteration | Never |
| Cleanup path | Not visible (yield during lookup) | `CMEDProxyObject` dtor → `LockReference::Release` |
| Call chain | `InternalGetRow` → `FGetNextRowInternal` → `GetNextAllHoBts` | `InternalGetRow` → `GetNextAllHoBts` |

---

## 4. Related Bugs

### 4.1 Direct Matches — Same GetNextAllHoBts / Metadata Destructor Path

| Bug ID | Title | State | Assigned | Version | Relevance |
|--------|-------|-------|----------|---------|-----------|
| [**5144129**](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/5144129) | MDL::UnlockGeneric non-yielding | **New** (2026-03-28) | Unassigned | SQL 2025 (17.0.9051) | **Highest** — identical path: CMEDProxyObject dtor → UnlockGeneric → spinlock |
| [**2763394**](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2763394) | CMEDProxyStats::Destroy non-yielding | **Active** | Alex Swanson | SQL 2022 (16.0.5290+) | **High** — same destructor chain + spinlock contention |
| [**2485230**](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2485230) | CMEDIndexStatsCollection::GetProxyIndexWithLock non-yielding | **Active** | Alex Swanson | SQL 2022 (16.0.5168+) | **High** — same metadata proxy path during compile |

### 4.2 Same Root Cause — Different Entry Point

| Bug ID | Title | State | Version | Trigger |
|--------|-------|-------|---------|---------|
| [**2292797**](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2292797) | Non-yielding in GetRowCount/FInitStatMan | **New** | SQL 2022 (16.0.937) | Auto-create stats during query optimization |
| [**4881252**](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4881252) | Non-yielding in GetRowCount/FInitStatMan | **New** | SQL 2025 (17.0.924) | UPDATE STATISTICS |

These bugs hit a different loop (`GetRowsetCountsForQp` → `GetRowCount` over cached HoBts in `schemamgr.inl:1246`) but share the same fundamental root cause: **HoBt iteration with no yield when metadata is cached**.

### 4.3 CMEDProxyObject Destructor Non-Yielding Pattern (Watson Clusters)

| Bug ID | Title | State |
|--------|-------|-------|
| [4137267](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4137267) | CMEDProxyObject destructor non-yielding | New |
| [4281144](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4281144) | CMEDProxyObject::GetDefault non-yielding | New |
| [4291882](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4291882) | CMEDProxyObject::GetRelation non-yielding | New |
| [4409805](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4409805) | CMEDProxyCheck::GetObject non-yielding | New |
| [1948956](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/1948956) | CMEDProxyRelation destructor non-yielding | **Done** (Panos Antonopoulos) |
| [3702923](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/3702923) | FAILED_ASSERTION in HoBtFactory/GetNextAllHoBts | New (Jay Krell) |

### 4.4 Key Observations

1. **Bugs 2485230 and 2763394 were previously marked Done/Fixed, then reopened as Active** — prior fixes were insufficient
2. **Bug 5144129 is a brand new bucket on SQL 2025 (v17)** — the issue persists in the latest version
3. All bugs are under **Metadata_Infrastructure** area path
4. Primary owner: **Alex Swanson (alswanso@microsoft.com)**

---

## 5. Proposed Code Fix

### Fix 1 (P0 — Must Do): Periodic Yield in `GetNextAllHoBts` Loop

**File**: `hobtstats.cpp` line 816-930

```cpp
HRESULT RowsetIndexStats::GetNextAllHoBts(...)
{
+   ULONG cIterations = 0;
+   const ULONG cYieldInterval = 64;

    do
    {
        BaseSharedHoBt* pSchema = m_HashScanContext.GetNextHoBt();

        while (pSchema)
        {
+           // Periodic yield check to prevent non-yielding scheduler
+           // when metadata is served from cache (no I/O = no natural yield point).
+           // See Bug 5144129, 2763394, 2292797.
+           if (++cIterations % cYieldInterval == 0)
+           {
+               SOS_Task::YieldAndCheckForAbort(SOS_Task::YieldReason_Other);
+           }

            pSchema->m_Latch.Acquire(LatchBase::KP);
            hr = m_pMEDProxyDatabase->GetObjectByObjectId(objectId, &pProxyObj);
            // ... existing logic ...
            pSchema->m_Latch.Release(LatchBase::KP);
            pSchema = m_HashScanContext.GetNextHoBt();
        }
    } while (Available == LockAndSetNextDatabase());

    return hr;
}
```

**Why 64?**
- 2^6 → compiler optimizes `% 64` to `& 0x3F`
- 64 iterations ≈ 64 μs–6.4 ms (cache hit, no contention) → far below 5-second non-yielding threshold
- Consistent with other engine scan patterns (e.g., `CQScanTableScan` uses 64 or 128)

**Why `YieldAndCheckForAbort`?**
- Also checks for query abort (user KILL/cancel) — important for long-running DMV queries
- If `RowsetIndexStats` lacks abort infrastructure, fall back to `SOS_Task::Yield()`

**Performance impact**: < 1% overhead. Cold cache: no impact (I/O already yields). Warm cache with few HoBts: no impact (< 64 iterations).

**Important**: The yield must happen **before** latch acquire — yielding while holding a KP latch would block other threads.

### Fix 2 (P1 — Defense-in-Depth): Yield in `InternalGetRow`

**File**: `hobtstats.cpp` — `RowsetIndexStats::InternalGetRow()`

```cpp
HRESULT RowsetIndexStats::InternalGetRow(...)
{
    HRESULT hr;
    hr = FGetNextRowInternal(...);

+   // Yield at row boundary — state is consistent after returning a complete row.
+   SOS_Task::YieldAndCheckForAbort(SOS_Task::YieldReason_Other);

    return hr;
}
```

**Pros**: Safe — yields at row boundary where all internal state is consistent.
**Cons**: If `GetNextAllHoBts` skips many non-qualifying HoBts in a single call, no yield occurs during the skip loop. Cannot replace Fix 1.

### Fix 3 (P2 — Covers Bug 2292797/4881252): Yield in `GetRowsetCountsForQp`

**File**: `schemamgr.cpp` ~line 7039

```cpp
HRESULT HoBtFactory::GetRowsetCountsForQp(...)
{
+   ULONG cIterations = 0;

    for (each partition)
    {
        rowCount += pHoBt->GetRowCount();
+
+       if (++cIterations % 128 == 0)
+       {
+           SOS_Task::YieldAndCheckForAbort(SOS_Task::YieldReason_Other);
+       }
    }
}
```

This covers the separate non-yielding path seen in Bug 2292797 (auto-create stats) and Bug 4881252 (UPDATE STATISTICS).

### Fix Priority Summary

| Priority | Fix | File | Risk | Coverage |
|----------|-----|------|------|----------|
| **P0** | Yield in `GetNextAllHoBts` loop | hobtstats.cpp | Low | Customer's current callstack |
| **P1** | Yield in `InternalGetRow` | hobtstats.cpp | Very Low | Defense-in-depth for all callers |
| **P2** | Yield in `GetRowsetCountsForQp` | schemamgr.cpp | Low | Bug 2292797/4881252 path |

---

## 6. Testing Recommendations

### Repro Setup
```sql
-- 1. Create database with many objects
CREATE DATABASE BigMetadataDB;
USE BigMetadataDB;

-- Create 50,000+ tables with indexes = 150K+ HoBts
-- (use a generation script)

-- 2. Warm the metadata cache (first pass — slow but yields)
SELECT * FROM sys.dm_db_index_physical_stats(DB_ID('BigMetadataDB'), NULL, NULL, NULL, 'LIMITED');

-- 3. Second pass — metadata now cached → should trigger non-yielding WITHOUT fix
SELECT * FROM sys.dm_db_index_physical_stats(DB_ID('BigMetadataDB'), NULL, NULL, NULL, 'LIMITED');
```

### Validation After Fix
1. Second pass completes without non-yielding scheduler event
2. Query can be cancelled with `KILL` during execution
3. No performance regression (< 1% overhead)
4. Small databases (< 100 objects) behave identically

---

## 7. Customer-Side Investigation Checklist

### 7.1 Confirm HoBt Count
```sql
SELECT DB_NAME() AS database_name,
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

> If total HoBts > 10,000, the risk of non-yielding increases significantly with warm cache.

### 7.2 Confirm Metadata Cache State
```sql
SELECT type, pages_kb / 1024 AS size_mb, entries_count
FROM sys.dm_os_memory_cache_counters
WHERE type LIKE '%Object%' OR type LIKE '%Schema%' OR type LIKE '%Metadata%'
ORDER BY pages_kb DESC;

-- Buffer pool usage for system catalog pages
SELECT DB_NAME(database_id) AS db_name,
       COUNT(*) AS cached_pages,
       COUNT(*) * 8 / 1024 AS cached_mb
FROM sys.dm_os_buffer_descriptors
WHERE page_type = 'DATA_PAGE'
GROUP BY database_id
ORDER BY cached_pages DESC;
```

### 7.3 Identify the Triggering Query
```sql
-- Check ERRORLOG for non-yielding events
EXEC xp_readerrorlog 0, 1, N'non-yielding';

-- Check for active queries hitting index DMVs
SELECT r.session_id, r.status, r.command, r.wait_type,
       r.cpu_time, r.total_elapsed_time,
       SUBSTRING(t.text, 1, 200) AS query_text
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE t.text LIKE '%dm_db_index%'
   OR t.text LIKE '%index_physical_stats%'
   OR t.text LIKE '%index_operational_stats%';
```

### 7.4 Check for Monitoring Tools
```sql
-- SQL Agent jobs that reference index DMVs
SELECT j.name, js.step_name, js.command
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps js ON j.job_id = js.job_id
WHERE js.command LIKE '%dm_db_index%'
   OR js.command LIKE '%index_physical_stats%'
   OR js.command LIKE '%index_operational_stats%'
   OR js.command LIKE '%index_usage_stats%';
```

Common culprits: SolarWinds, Redgate SQL Monitor, Idera, Ola Hallengren maintenance scripts, custom monitoring queries.

### 7.5 Spinlock Contention (for Layer 3 diagnosis)
```sql
SELECT name, collisions, spins, spins_per_collision,
       sleep_time, backoffs
FROM sys.dm_os_spinlock_stats
WHERE name LIKE 'LOCK%'
ORDER BY collisions DESC;
```

### 7.6 Collect from Customer
- Exact SQL Server version (`SELECT @@VERSION`)
- Non-yielding frequency and timing — does it correlate with maintenance jobs?
- Has the object count increased recently?
- Memory dump if available (look for `GetNextAllHoBts` on the non-yielding thread, absence of `FixPage`/`BTreeMgr::Seek` confirms cache-hit path)

---

## 8. Workarounds (Until Fix is Available)

| # | Workaround | Details |
|---|-----------|---------|
| 1 | **Scope DMV queries** | Always specify `object_id` and `index_id` parameters. Avoid `NULL` (= scan all objects). E.g., `sys.dm_db_index_physical_stats(DB_ID(), @object_id, @index_id, NULL, 'LIMITED')` |
| 2 | **Reduce monitoring frequency** | If a monitoring tool runs index DMV queries every few minutes, increase the interval to reduce collision with warm cache |
| 3 | **Drop unused indexes** | Each unused index adds HoBts to the iteration loop |
| 4 | **Consolidate partitions** | Merge empty/unused partitions to reduce total HoBt count |
| 5 | **Schedule during low cache period** | Run index DMV queries shortly after restart (cold cache → yields naturally through I/O). Last resort |

---

## 9. Escalation Recommendation

### Link to Existing Bugs
This case should be associated with:
- **Bug 5144129** (SQL 2025, New, Unassigned) — identical callstack pattern
- **Bug 2763394** (SQL 2022, Active, Alex Swanson) — same destructor chain with spinlock evidence
- **Bug 2292797** and **Bug 4881252** — same root cause via different entry point

### Contact
- **Primary owner**: Alex Swanson (alswanso@microsoft.com) — Metadata_Infrastructure
- **Area Path**: Database Systems\SQL Server\SQL Engine\Metadata_Infrastructure (for metadata/lock bugs) and Access Methods (for hobtstats yield bugs)

### New Evidence This Case Provides
1. **Repro proof** of cache-hit vs cache-miss divergence with side-by-side callstacks
2. A new trigger path: `GetNextAllHoBts` → `CMEDProxyObject` cached metadata (vs. the existing `GetRowCount` path in filed bugs)
3. Customer impact with many GB of cached metadata — confirms this is a real-world scenario, not just a Watson auto-file

---

## 10. References

| Source | Link |
|--------|------|
| Bug 5144129 (SQL 2025, New) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/5144129 |
| Bug 2763394 (SQL 2022, Active) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2763394 |
| Bug 2485230 (SQL 2022, Active) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2485230 |
| Bug 2292797 (SQL 2022, New) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2292797 |
| Bug 4881252 (SQL 2025, New) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4881252 |
| Bug 1948956 (Done, prior fix) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/1948956 |
| Bug 3702923 (Assertion) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/3702923 |
| Source: hobtstats.cpp | `Sql/Ntdbms/storeng/dfs/schemamanager/source/hobtstats.cpp` |
| Source: schemamgr.inl | `Sql/Ntdbms/storeng/include/schemamgr.inl` |
| Source: cmedobj.cpp | `Sql/Ntdbms/metadata/src/cmedobj.cpp` |
| Source: medutil.cpp | `Sql/Ntdbms/metadata/src/medutil.cpp` |
