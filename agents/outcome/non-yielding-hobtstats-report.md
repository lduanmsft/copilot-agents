# Non-Yielding Scheduler Analysis: RowsetIndexStats::GetNextAllHoBts
# 非抢占调度器分析：RowsetIndexStats::GetNextAllHoBts

---

## 1. Problem Summary / 问题摘要

**EN:** A non-yielding scheduler condition occurs when querying index stats DMVs (e.g., `sys.dm_db_index_physical_stats`, `sys.dm_db_index_operational_stats`) on databases with a large number of tables, partitions, and indexes. The issue is triggered specifically when the metadata cache has a high hit rate — meaning most objects are already cached in memory.

**CN:** 在查询 index stats DMV（如 `sys.dm_db_index_physical_stats`、`sys.dm_db_index_operational_stats`）时，如果数据库有大量的表、分区和索引，且 metadata cache 命中率很高（大部分对象已缓存在内存中），会触发非抢占调度器（non-yielding scheduler）问题。

---

## 1.5 Research Methodology & Tools Used / 研究方法与工具

本分析使用以下 MCP 工具对 `msdata` (Azure DevOps) 和内部源码仓库进行查询：

| Step / 步骤 | Tool / 工具 | Purpose / 用途 | Key Query / 关键查询 |
|---|---|---|---|
| 源码搜索 | `msdata-search_code` | 查找包含 `GetNextAllHoBts` 的源文件 | `searchText: "GetNextAllHoBts"`, project: Database Systems, repo: DsMainDev, path: /Sql/Ntdbms |
| 源码读取 | `msdata-repo_get_file_content` | 读取 `hobtstats.cpp` 完整源码分析循环逻辑 | path: `/Sql/Ntdbms/storeng/dfs/schemamanager/source/hobtstats.cpp`, branch: `rel/box/sql2022/sql2022_rtm_qfe-cu` |
| Bug 搜索 | `msdata-search_workitem` | 查找已有的 Watson bug | ❌ `"GetNextAllHoBts non-yielding scheduler"` → 0 results |
| | | | ❌ `"RowsetIndexStats non-yielding yield metadata cache"` → 0 results |
| | | | ❌ `"sys.dm_db_index_physical_stats non-yielding scheduler many partitions"` → 0 results |
| | | | ❌ `"CQScanTVFStreamNew non-yielding index stats metadata"` → 0 results |
| | | | ✅ `"hobtstats non-yielding"` → **8 results** (源码文件名命中 Watson callstack 文本) |
| Bug 详情 | `msdata-wit_get_work_item` | 获取 2 个最相关 bug 的完整信息 | id: `2292797`, `4881252` (expand: all) |

> **经验教训 / Lesson learned:** Watson 自动 filed 的 bug 内容主要是 callstack 文本。搜索时用**源码文件名**（如 `hobtstats`）比用功能性描述（如 `non-yielding index stats`）更有效。

---

## 2. Root Cause Analysis / 根因分析

### 2.1 The Core Loop — `GetNextAllHoBts()` / 核心循环

> 🔧 **Tool:** `msdata-search_code` searchText: `"GetNextAllHoBts"` → found `hobtstats.cpp`
> 🔧 **Tool:** `msdata-repo_get_file_content` path: `/Sql/Ntdbms/storeng/dfs/schemamanager/source/hobtstats.cpp` branch: `rel/box/sql2022/sql2022_rtm_qfe-cu`

**Source file:** `/Sql/Ntdbms/storeng/dfs/schemamanager/source/hobtstats.cpp` (line 793-934)

The function `RowsetIndexStats::GetNextAllHoBts()` iterates over **all HoBt (Heap or B-Tree) objects** in a database. The core loop has **no built-in yield point**:

该函数遍历数据库中**所有的 HoBt（堆或 B 树）对象**。核心循环**没有内置 yield 点**：

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

**Key observation / 关键发现:** There is no `SOS_Task::Yield()` or equivalent yield check anywhere in this `while` loop. Whether the scheduler yields or not depends entirely on what happens inside `GetObjectByObjectId`.

此 `while` 循环中没有任何 `SOS_Task::Yield()` 或等效的 yield 检查。调度器是否 yield 完全取决于 `GetObjectByObjectId` 内部的执行路径。

### 2.2 Two Execution Paths / 两条执行路径

#### Path A: Metadata Cache MISS (yields normally) / 缓存未命中（正常 yield）

When the metadata object is **not** in cache, SQL Server must read it from disk:

当 metadata 对象**不在**缓存中时，SQL Server 必须从磁盘读取：

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

**The I/O wait in `FixPage` triggers a scheduler yield.** This is why the repro with cold cache works fine — every HoBt iteration includes an I/O wait that allows other tasks to run.

**`FixPage` 中的 I/O 等待触发了调度器 yield。** 这就是为什么冷缓存下的复现测试正常工作 — 每次 HoBt 迭代都包含一个 I/O 等待，允许其他任务运行。

#### Path B: Metadata Cache HIT (NO yield — the bug) / 缓存命中（无 yield — bug）

When the metadata object **is** in cache, the entire operation stays in memory:

当 metadata 对象**在**缓存中时，整个操作都在内存中完成：

```
GetObjectByObjectId
→ CMEDProxyDatabase::GetObjectByObjectId     (cache HIT — returns immediately)
→ CMEDProxyObject::~CMEDProxyObject          (cleanup)
→ SMD::ReleaseObjectLock
→ LockReference::Release                     ← ❌ NO YIELD, pure CPU
```

**No I/O occurs, so no yield happens.** The `while (pSchema)` loop runs as a tight CPU-bound loop. With tens of thousands of HoBts all cached, this loop can run for seconds or even minutes without yielding, triggering the non-yielding scheduler detection (default threshold: 60 seconds).

**没有 I/O 发生，因此没有 yield。** `while (pSchema)` 循环变成紧密的 CPU 密集型循环。当数万个 HoBt 全部缓存时，此循环可以运行数秒甚至数分钟而不 yield，触发非抢占调度器检测（默认阈值：60 秒）。

### 2.3 Visual Comparison / 可视化对比

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

---

## 3. Related Bugs / 相关 Bug

> 🔧 **Tool:** `msdata-search_workitem` — 搜索关键词 `"hobtstats non-yielding"` 命中 8 个结果（前 4 次搜索均为 0 结果）
> 🔧 **Tool:** `msdata-wit_get_work_item` — 获取 Bug 2292797 和 4881252 的完整详情 (expand: all)

### Bug 2292797 — SQL Server 2022
- **Link:** https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2292797
- **State:** New (unfixed / 未修复)
- **Version:** SQL 2022 (16.0.937.2220)
- **Watson Bucket:** [2056126](https://azurewatson.microsoft.com/bucket/2056126)
- **Related Legacy Bug:** 12721321 (old TFS / 旧 TFS)
- **Area Path:** SQL Engine → Access Methods

**Callstack:**
```
PartitionedCounter::GetCounterAndCorrectNegative  (hobtstats.inl:400)
→ BaseSharedHoBt::GetRowCount                     (schemamgr.inl:1246)
→ HoBtFactory::GetRowsetCountsForQp               (schemamgr.cpp:7039)
→ GetIndexSizeData → CIStatManFactory
→ CStatsTree::FInitStatMan                        (recursive, 14 levels deep)
→ CStatsTreeManager::UpdateAndPersistStatsTree
→ CStatsUtil::CreateQPStats → CStmtCreateStats    ← AUTO_CREATE_STATISTICS
→ COptContext::PcxteOptimizeQuery                  ← during query optimization
```

**Trigger scenario / 触发场景:** Query optimizer triggers auto-create statistics on a table with many partitions. The recursive `FInitStatMan` calls `GetRowCount` for each partition's HoBt. With cached metadata, the entire recursion runs without yielding.

查询优化器在具有大量分区的表上触发自动创建统计信息。递归的 `FInitStatMan` 对每个分区的 HoBt 调用 `GetRowCount`。在缓存命中的情况下，整个递归过程不会 yield。

### Bug 4881252 — SQL Server 2025
- **Link:** https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4881252
- **State:** New (unfixed / 未修复)
- **Version:** SQL 2025 (2025.170.924.10217)
- **Watson Bucket:** [FailureHash: 893508c5-db5f-bb1b-6418-0ab0b031562f](https://portal.watson.azure.com/bucket?$filter=(FailureInfo_FailureHash%20eq%20893508c5-db5f-bb1b-6418-0ab0b031562f))
- **Area Path:** SQL Engine → Access Methods

**Callstack:** Nearly identical to Bug 2292797 — same `GetRowCount` → `GetRowsetCountsForQp` → recursive `FInitStatMan` path, confirming this bug persists across versions.

Callstack 与 Bug 2292797 几乎相同，确认此 bug 跨版本持续存在。

### Summary Table / Bug 汇总

| Bug ID | SQL Version | State | Trigger | Root Cause |
|--------|-------------|-------|---------|------------|
| [2292797](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2292797) | SQL 2022 | **New** | Auto-create stats during query optimization | `GetRowCount` loop over cached HoBts, no yield |
| [4881252](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4881252) | SQL 2025 | **New** | UPDATE STATISTICS | Same root cause |
| Current case | SQL 2022 | — | Index stats DMV query | `GetNextAllHoBts` loop over cached HoBts, no yield |

All three share the same fundamental issue: **HoBt iteration loops in `hobtstats.cpp` / `schemamgr.inl` lack periodic yield checks when metadata is served from cache.**

三者共享同一根本问题：**`hobtstats.cpp` / `schemamgr.inl` 中的 HoBt 遍历循环在 metadata 从缓存返回时缺少周期性 yield 检查。**

---

## 4. Customer Environment Checks / 客户环境检查项

> 🔧 **Source / 来源:** SQL 查询基于源码分析推导 — 针对根因中识别的特定对象和路径

### 4.1 Confirm HoBt Count / 确认 HoBt 数量

```sql
-- Total HoBt count across the database
-- 统计数据库中的 HoBt 总数
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
-- 按分区数排序的表
SELECT TOP 20
    OBJECT_SCHEMA_NAME(object_id) + '.' + OBJECT_NAME(object_id) AS table_name,
    COUNT(*) AS partition_count,
    COUNT(DISTINCT index_id) AS index_count
FROM sys.partitions
WHERE index_id >= 0
GROUP BY object_id
ORDER BY COUNT(*) DESC;
```

**Threshold / 阈值:** If total HoBts > 10,000, the risk of non-yielding increases significantly with warm cache.

如果 HoBt 总数 > 10,000，在缓存预热的情况下 non-yielding 风险显著增加。

### 4.2 Confirm Metadata Cache State / 确认 Metadata 缓存状态

```sql
-- Metadata memory cache stats
-- Metadata 内存缓存统计
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
-- 系统目录页面的缓冲池使用
SELECT 
    DB_NAME(database_id) AS db_name,
    COUNT(*) AS cached_pages,
    COUNT(*) * 8 / 1024 AS cached_mb
FROM sys.dm_os_buffer_descriptors
WHERE database_id = DB_ID()
  AND page_type = 'DATA_PAGE'
GROUP BY database_id;
```

### 4.3 Identify the Triggering Query / 识别触发查询

```sql
-- Check for recent non-yielding scheduler events
-- 检查最近的 non-yielding scheduler 事件
EXEC xp_readerrorlog 0, 1, N'non-yielding';

-- Check active queries accessing index DMVs
-- 检查正在访问 index DMV 的活动查询
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

### 4.4 Check for Monitoring Tools / 检查监控工具

Look for scheduled jobs or external monitoring tools that periodically scan index DMVs:

检查是否有定时任务或外部监控工具定期扫描 index DMV：

```sql
-- Check SQL Agent jobs that reference index DMVs
-- 检查引用 index DMV 的 SQL Agent 作业
SELECT j.name, js.step_name, js.command
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps js ON j.job_id = js.job_id
WHERE js.command LIKE '%dm_db_index%'
   OR js.command LIKE '%index_physical_stats%'
   OR js.command LIKE '%index_operational_stats%'
   OR js.command LIKE '%index_usage_stats%';
```

Common culprits / 常见工具: SolarWinds, Redgate SQL Monitor, Idera, Ola Hallengren maintenance scripts, custom monitoring queries.

### 4.5 Check the Non-Yielding Dump / 检查 Non-Yielding Dump

If a memory dump was generated during the non-yielding event:

如果在 non-yielding 事件期间生成了内存转储：

1. Verify the callstack matches the pattern described above
   验证 callstack 是否匹配上述模式
2. Check the `process_commands_internal` or `process_request` at the bottom of the stack
   检查堆栈底部的 `process_commands_internal` 或 `process_request`
3. Look for `RowsetIndexStats::GetNextAllHoBts` or `BaseSharedHoBt::GetRowCount` in the faulting thread
   在故障线程中查找 `RowsetIndexStats::GetNextAllHoBts` 或 `BaseSharedHoBt::GetRowCount`

---

## 5. Workarounds / 临时解决方案

> 🔧 **Source / 来源:** 基于源码分析（Section 2）和 Bug 模式（Section 3）推导 — 减少 HoBt 数量或降低 cache 命中率可打破 non-yielding 循环

Since this is a known unfixed product bug, recommend the following mitigations:

由于这是一个已知的未修复产品 bug，建议以下缓解措施：

| # | Workaround | Details |
|---|-----------|---------|
| 1 | **Scope DMV queries / 限定 DMV 查询范围** | Always use `WHERE object_id = ...` or `WHERE database_id = ...` filters when querying index DMVs. Avoid full scans like `SELECT * FROM sys.dm_db_index_physical_stats(NULL, NULL, NULL, NULL, NULL)`. 查询 index DMV 时始终使用过滤条件，避免全扫描。 |
| 2 | **Reduce monitoring frequency / 降低监控频率** | If a monitoring tool runs index DMV queries every few minutes, increase the interval to reduce collision with warm cache. 如果监控工具每几分钟运行一次 index DMV 查询，增加间隔。 |
| 3 | **Consolidate partitions / 合并分区** | If there are many empty or unused partitions, consider merging them to reduce total HoBt count. 如果有大量空或未使用的分区，考虑合并以减少 HoBt 总数。 |
| 4 | **Drop unused indexes / 删除未使用的索引** | Each unused index adds HoBts. Removing them reduces the loop iteration count. 每个未使用的索引都会增加 HoBt 数量，删除它们可减少循环次数。 |
| 5 | **Schedule during low cache period / 在低缓存期调度** | Run index DMV queries shortly after SQL Server restart (cold cache) when yields occur naturally through I/O. 在 SQL Server 重启后不久（冷缓存）运行 index DMV 查询，此时 I/O 会自然产生 yield。 |

---

## 6. Recommendation to PG / 向 PG 的建议

> 🔧 **Source / 来源:** 修复建议基于 `msdata-repo_get_file_content` 对 `hobtstats.cpp` 循环结构（line 816–930）的分析

The fix should add a **periodic yield check** inside the `GetNextAllHoBts()` loop in `hobtstats.cpp`, similar to other long-running scan loops in the engine. For example:

修复方案应在 `hobtstats.cpp` 的 `GetNextAllHoBts()` 循环中添加**周期性 yield 检查**，类似引擎中其他长时间运行的扫描循环。例如：

```cpp
// Proposed fix (conceptual)
ULONG iterationCount = 0;
while (pSchema)
{
    // ... existing logic ...

    pSchema->m_Latch.Release(LatchBase::KP);
    pSchema = m_HashScanContext.GetNextHoBt();

    // Add periodic yield check every N iterations
    if (++iterationCount % 1000 == 0)
    {
        SOS_Task::Yield();  // Allow scheduler to run other tasks
    }
}
```

This case should be linked to **Bug 2292797** and **Bug 4881252** with the additional evidence of the `GetNextAllHoBts` → `CMEDProxyObject` cached path analysis.

此 case 应关联到 **Bug 2292797** 和 **Bug 4881252**，并补充 `GetNextAllHoBts` → `CMEDProxyObject` 缓存路径分析的额外证据。

---

## 7. References / 参考资料

| Source | Link |
|--------|------|
| Bug 2292797 (SQL 2022) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2292797 |
| Bug 4881252 (SQL 2025) | https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/4881252 |
| Legacy Bug 12721321 | https://sqlbuvsts01/Main/SQL%20Server/_workitems#_a=edit&id=12721321 |
| Source: hobtstats.cpp | `/Sql/Ntdbms/storeng/dfs/schemamanager/source/hobtstats.cpp` |
| Source: schemamgr.inl | `/Sql/Ntdbms/storeng/include/schemamgr.inl` |
| Source: hobtstats.inl | `/Sql/Ntdbms/storeng/include/hobtstats.inl` |
