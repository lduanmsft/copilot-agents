# ColumnStore ObjectPool Spinlock 自死锁 — Non-Yielding Scheduler 分析

**ICM**: https://portal.microsofticm.com/imp/v5/incidents/details/528563800/summary
**日期**: 2026-04-28
**类型**: Spinlock 自死锁
**SQL 版本**: SQL Server 2022
**影响区域**: 列存储索引 / SQLOS 缓存

---

## 1. 问题摘要

一个使用列存储索引的 SELECT INTO 查询陷入非抢占调度器（NYS）状态，且**永远不会恢复**。多个调度器（13、14、15、17）同时报告 non-yielding。关键诊断指标是 **CPU = 0ms**（内核和用户均为 0），**系统空闲率 99%** — 证明线程并未运行，而是永久休眠。这是一个 **spinlock 自死锁**：线程持有 XList spinlock 后，通过缓存模拟层的另一条代码路径重新进入同一个 spinlock，造成永久挂起。

**错误日志证据：**
```
Process 0:0:0 (0x4240) Worker 0x000001A45CCE8160 appears to be non-yielding on Scheduler 13.
Approx Thread CPU Used: kernel 0 ms, user 0 ms.
Process Utilization 0%. System Idle 99%. Interval: 70206 ms.
```
- 325 个线程中有 17 个匹配 ColumnStoreObjectPool 过滤器
- 多个调度器同时卡住
- Case 标题：查询 "gets stuck in an NYS that never resolves"

---

## 2. 研究方法与工具

| 步骤 | 工具 | 参数 | 结果 |
|------|------|------|------|
| Bug 搜索 (XList race) | msdata-search_workitem | "XList race condition Invalidate spinlock self-deadlock" | 0 结果 |
| Bug 搜索 (ColumnStore) | msdata-search_workitem | "ColumnStoreObjectPool non-yielding spinlock deadlock" | 0 结果 |
| Bug 搜索 (TCacheStore) | msdata-search_workitem | "SpinlockBase::Sleep TCacheStore CacheProbabilisticAlgorithm self-deadlock" | 0 结果 |
| Bug 搜索 (Spinlock 27) | msdata-search_workitem | "Spinlock 27 XList ProbCostData non-yielding" | 16 结果 ★ |
| Bug 搜索 (PR 1298481) | msdata-search_workitem | "1298481 SOS Fix XList race condition" | 2 结果 ★ |
| Bug 详情 | msdata-wit_get_work_item | IDs: 2328489, 3507392, 4887916, 2627135, 2180018 | 获取完整详情 |
| 源码 | msdata-repo_get_file_content | columnstoreobjectref.cpp | 确认 Fix/Unfix 重入问题 |
| PR 详情 | msdata-repo_get_pull_request_by_id | PR 1298481 | 修复已确认，2024-03-19 合并 |
| PR 变更 | msdata-repo_get_pull_request_changes | PR 1298481 | 17 个文件变更 |
| CSS Wiki 搜索 | csswiki-search_wiki | "non-yielding scheduler columnstore cache spinlock" | 通用 NYS 文档（无特定 TSG） |

---

## 3. 完整 Callstack

### 3.1 初始 Callstack（inline 帧被折叠）

```
00 ntdll!ZwDelayExecution+0x14
01 KERNELBASE!SleepEx+0xa1
02 sqldk!SpinlockBase::Sleep+0x408
03 sqldk!SpinlockBase::Backoff+0x272
04 sqlmin!Spinlock<27,1,268435714>::SpinToAcquireOptimistic+0x136
05 sqlmin!Spinlock<27,1,268435714>::Get+0x3e                          (Inline)
06 sqlmin!XList<ProbCostData>::Delete+0x64
07 sqlmin!XTList<ProbCostData>::RemoveElem+0x13                       (Inline)
08 sqlmin!TPartitionedDescriptorList<...>::RemoveElem+0x17             (Inline)
09 sqlmin!TCacheSimulation<...>::SimulationHit+0x7c                    (Inline)
0a sqlmin!TCacheStore<...>::ConvertEntryToActual+0xc0
0b sqlmin!TCacheStore<...>::CacheUserDataWithControlHelper+0x282
0c sqlmin!TCacheStore<...>::CacheUserDataExclusiveWithControl+0xf3
0d sqlmin!ColumnStoreObjectPool::ConstructObjectAndFix+0x6d9
0e sqlmin!ColumnStoreObjectPool::RetrieveObjectAndFix+0x8e            (Inline)
0f sqlmin!ColumnStoreObjectRef::Fix+0xbc
10 sqlmin!RowGroupManager::SetUpRowGroup+0x4de
11 sqlmin!RowGroupManager::GetNextRowGroup+0xa7b
12 sqlmin!RowBucketScanner::GetNextRowGroup+0x54                      (Inline)
13 sqlmin!RowBucketScanner::GetNextRowBucketAndFinalizeCurrent+0x169
14 sqlmin!ColumnDataSetSession::FetchNextColumnBatch+0x4ca
15 sqlmin!NormalColumnDataSet::FetchNextColumnBatch+0x46
16 sqlmin!ColumnsetSS::FetchNextColumnBatch+0x35
17 sqlmin!CBpQScanColumnStoreScan::BpGetNextBatch+0xe3
18-24 ... CBpQScan → CBpQScanHashJoin → CBpPartialJoin ...
25 sqlmin!CQScanBatchHelper::GetRow+0x94
26 sqlmin!CQScanUpdateNew::GetRow+0xf6
27 sqlmin!CQScanLightProfileNew::GetRow+0x19
28 sqlmin!CQueryScan::GetRow+0x80
29 sqllang!CXStmtQuery::ErsqExecuteQuery+0x3de
2a sqllang!CXStmtDML::XretDMLExecute+0x48c
2b sqllang!CXStmtSelectInto::XretSelectIntoExecute+0x81c
2c sqllang!CXStmtSelectInto::XretDoExecute+0xf4
2d sqllang!CXStmtSelectInto::XretExecute+0x133
```

### 3.2 完整 Dump Callstack（展开 inline 帧，含源文件引用）

Spinlock owner 确认为 Thread 177 (0x4240) — 与卡住线程相同（self-deadlock）。

```
00 ntdll!ZwDelayExecution+0x14                                         [minkernel\ntdll\daytona\objfre\amd64\usrstubs.asm @ 595]
01 KERNELBASE!SleepEx+0xa1                                             [minkernel\kernelbase\thread.c @ 2230]
02 sqldk!SpinlockBase::Sleep+0x408                                     [sql\dktemp\sos\src\spinlock.cpp @ 240]
03 sqldk!SpinlockBase::Backoff+0x272                                   [sql\dktemp\sos\src\spinlock.cpp @ 75]
04 sqlmin!Spinlock<27,1,268435714>::SpinToAcquireOptimistic+0x136       [sql\dktemp\sos\include\spinlock.inl @ 796]
05 sqlmin!Spinlock<27,1,268435714>::Get+0x3e                    (Inline)[sql\dktemp\sos\include\spinlock.inl @ 592]
06 sqlmin!XList<ProbCostData>::Delete+0x64                              [sql\dktemp\base\include\xlist.inl @ 361]     ← ❌ 第二次获取 spinlock
07 sqlmin!XListElem<ProbCostData>::RemoveAndDestroy+0x1f                [sql\dktemp\base\include\xlist.inl @ 286]     ← refcount=0 触发删除
08 sqlmin!XListElem<ProbCostData>::Release+0x1b                 (Inline)[sql\dktemp\base\include\xlist.inl @ 240]     ← Release() 降到 0
09 sqlmin!XListEnumerator<ProbCostData>::Invalidate+0x8f        (Inline)[sql\dktemp\base\include\xlist.inl @ 1195]    ← ★ BUG: 过早释放
0a sqlmin!XList<ProbCostData>::Delete+0x11f                             [sql\dktemp\base\include\xlist.inl @ 373]     ← ✅ 第一次获取 spinlock
0b sqlmin!XTList<ProbCostData>::RemoveElem+0x13                 (Inline)[sql\dktemp\sos\include\soscache.h @ 2206]
0c sqlmin!TPartitionedDescriptorList<...>::RemoveElem+0x17      (Inline)[sql\dktemp\sos\include\soscache.inl @ 3040]
0d sqlmin!TCacheSimulation<...>::SimulationHit+0x7c             (Inline)[sql\dktemp\sos\include\soscache.inl @ 11625]
0e sqlmin!TCacheStore<...>::ConvertEntryToActual+0xc0                   [sql\dktemp\sos\include\soscache.inl @ 8516]
0f sqlmin!TCacheStore<...>::CacheUserDataWithControlHelper+0x282        [sql\dktemp\sos\include\soscache.inl @ 6358]
10 sqlmin!TCacheStore<...>::CacheUserDataExclusiveWithControl+0xf3      [sql\dktemp\sos\include\soscache.inl @ 6459]
11 sqlmin!ColumnStoreObjectPool::ConstructObjectAndFix+0x6d9            [sql\ntdbms\storeng\dfs\manager\columnstoreobjectpool.cpp @ 834]
12 sqlmin!ColumnStoreObjectPool::RetrieveObjectAndFix+0x8e      (Inline)[sql\ntdbms\storeng\dfs\manager\columnstoreobjectpool.cpp @ 1173]
13 sqlmin!ColumnStoreObjectRef::Fix+0xbc                                [sql\ntdbms\storeng\dfs\manager\columnstoreobjectref.cpp @ 126]
14 sqlmin!RowGroupManager::SetUpRowGroup+0x4de                          [sql\ntdbms\storeng\dfs\access\datasetrowgroupmgr.cpp @ 2235]
15 sqlmin!RowGroupManager::GetNextRowGroup+0xa7b                        [sql\ntdbms\storeng\dfs\access\datasetrowgroupmgr.cpp @ 1264]
16 sqlmin!RowBucketScanner::GetNextRowGroup+0x54                (Inline)[sql\ntdbms\storeng\dfs\access\rowbucketscanner.cpp @ 705]
17 sqlmin!RowBucketScanner::GetNextRowBucketAndFinalizeCurrent+0x169    [sql\ntdbms\storeng\dfs\access\rowbucketscanner.cpp @ 265]
18 sqlmin!ColumnDataSetSession::FetchNextColumnBatch+0x4ca              [sql\ntdbms\storeng\dfs\access\columndataset.cpp @ 1928]
19 sqlmin!NormalColumnDataSet::FetchNextColumnBatch+0x46                [sql\ntdbms\storeng\dfs\access\columndataset.cpp @ 3404]
1a sqlmin!ColumnsetSS::FetchNextColumnBatch+0x35                       [sql\ntdbms\storeng\drs\oledb\columnset.cpp @ 543]
1b sqlmin!CBpQScanColumnStoreScan::BpGetNextBatch+0xe3                 [sql\ntdbms\query\qebp\bpcolscan.cpp @ 1074]
...
29 sqllang!CXStmtQuery::ErsqExecuteQuery+0x3de
2a sqllang!CXStmtDML::XretDMLExecute+0x48c
2b sqllang!CXStmtSelectInto::XretSelectIntoExecute+0x81c
2d sqllang!CXStmtSelectInto::XretExecute+0x133
```

---

## 4. Callstack 叙述（从底到顶）

从底到顶，这个线程在做什么：

### 1. 查询执行（帧 2d-29）
`CXStmtSelectInto::XretExecute → CXStmtDML::XretDMLExecute → CXStmtQuery::ErsqExecuteQuery → CQueryScan::GetRow`
正在执行一个 **SELECT INTO** 语句，开始从查询计划中拉取行。

### 2. DML 批处理（帧 28-24）
`CQScanUpdateNew::GetRow → CQScanBatchHelper::GetRow → CBpQScan::GetNextRootBatch → CBpQScanProject → CBpQScanHashJoin`
SELECT INTO 正在插入行，通过哈希连接运算符以**批处理模式**拉取数据。

### 3. 哈希连接 — 探测侧（帧 23-17）
`CBpQScanHashJoin::Main → CBpPartialJoin::ProcessProbeSide → CBpQScanFilter → CBpQScanColumnStoreScan::BpGetNextBatch`
查询正在通过扫描**列存储索引**来探测哈希连接。

### 4. 列存储行组扫描（帧 16-0f）
`ColumnsetSS::FetchNextColumnBatch → RowBucketScanner::GetNextRowGroup → RowGroupManager::SetUpRowGroup → ColumnStoreObjectRef::Fix`
正在设置下一个行组用于扫描。`Fix()` 调用将行组对象固定在 **ColumnStoreObjectPool** 缓存中。**关键**：如果之前有固定的对象，`Fix()` 会先调用 `Unfix()` 释放旧对象（第 109 行），旧对象会从缓存存储中释放。

### 5. 缓存存储插入（帧 0d-0a）
`ColumnStoreObjectPool::ConstructObjectAndFix → TCacheStore::CacheUserDataExclusiveWithControl → TCacheSimulation::SimulationHit → TCacheStore::ConvertEntryToActual`
将行组对象插入 ColumnStoreObjectPool 缓存。缓存的**概率模拟算法**正在更新其内部成本跟踪 XList。

### 6. ★ 卡在这里 — SPINLOCK 自死锁（帧 0a-00）

**注意：** 初始 callstack 中帧 07-09 被调试器折叠为 inline 帧。展开后可以看到完整的自死锁路径：

```
帧 0a: XList<ProbCostData>::Delete+0x11f          [xlist.inl @ 373]
         → m_lock.Get() 已完成                     ← ✅ 第一次获取 Spinlock<27>
         → 调用 pEnum->Invalidate(el)               ← 在持有 spinlock 的情况下

帧 09:   XListEnumerator<ProbCostData>::Invalidate+0x8f  [xlist.inl @ 1195]
           → m_baseObject->Release()                ← ★ BUG：过早释放引用

帧 08:     XListElem<ProbCostData>::Release+0x1b    [xlist.inl @ 240]
             → refcount 降为 0

帧 07:       XListElem<ProbCostData>::RemoveAndDestroy+0x1f  [xlist.inl @ 286]
               → 触发递归删除

帧 06: XList<ProbCostData>::Delete+0x64             [xlist.inl @ 361]
         → m_lock.Get()                             ← ❌ 第二次获取同一个 Spinlock<27>
         → 不可重入 → SpinToAcquire → Backoff → Sleep

帧 05-00: Spinlock<27>::Get → SpinToAcquireOptimistic → Backoff → Sleep → ZwDelayExecution
         → CPU = 0ms，永久休眠
```

**Spinlock owner 确认：**
```
dx (*((sqlmin!SpinlockBase::Lock *)0x19e1cf25b98))
    m_threadId : 0x4240        ← spinlock 被线程 0x4240 持有
    
~~[0x4240]s → Thread 177      ← 就是这个线程自己！
```

线程 177 (0x4240) 持有 Spinlock<27>，同时又在尝试获取同一个 Spinlock<27> — **确认是 self-deadlock**。

- **CPU = 0ms** 确认线程正在休眠，而不是自旋
- **这是自死锁 — 永远不会解决**
- Spinlock 是**不可重入的**
- 所有 17 个卡住的线程都在等待这个被线程 177 持有的 spinlock

---

## 5. Callstack 分析

### 分层解析

| 层级 | 帧 | 函数 | 用途 |
|------|-----|------|------|
| 查询执行 | 2d-29 | CXStmtSelectInto, CXStmtDML, CXStmtQuery | SELECT INTO 执行 |
| DML/批处理 | 28-24 | CQScanUpdateNew, CQScanBatchHelper, CBpQScanHashJoin | 批处理模式行处理 |
| 哈希连接 | 23-17 | CBpPartialJoin, CBpQScanFilter, CBpQScanColumnStoreScan | 列存储扫描用于哈希探测 |
| 列存储扫描 | 16-0f | ColumnsetSS, RowBucketScanner, RowGroupManager, ColumnStoreObjectRef | 行组设置和缓存 |
| 缓存存储 | 0d-0a | ColumnStoreObjectPool, TCacheStore, TCacheSimulation | 概率算法缓存插入 |
| **Spinlock（卡住）** | 06-00 | XList::Delete, Spinlock<27,1,268435714>, SpinlockBase::Sleep | **XList spinlock 自死锁** |

### Spinlock 详情
- **Spinlock 类型**: 27
- **实例 ID**: 268435714
- **行为**: 不可重入 — 同一线程不能获取两次
- **源文件**: `sql\dktemp\base\include\xlist.inl`

---

## 6. 源码分析

### 6.1 ColumnStoreObjectRef::Fix — 重入触发点

来自 `columnstoreobjectref.cpp`（第 ~109 行）：

```cpp
ColumnStoreObject*
ColumnStoreObjectRef::Fix(...)
{
    if (m_pObject != NULL)
    {
        DBG_ASSERT(m_isCached);
        Unfix();  // ← 释放旧对象，进入缓存模拟
    }

    m_pObject = CSPool->RetrieveObjectAndFix(...);  // ← 检索/构造新对象
    m_isCached = true;
    return m_pObject;
}
```

关键路径：`Fix()` → `Unfix()` → `UnfixObject()` → `ReleaseUserData()` → 缓存模拟 → **获取 XList spinlock**。然后 `Fix()` 继续执行 `RetrieveObjectAndFix()` → `ConstructObjectAndFix()` → 缓存模拟 → **尝试获取同一个 XList spinlock** → **死锁**。

### 6.2 XList::Delete() — 第一次获取 spinlock（callstack 帧 06）

来自 `xlist.inl`（第 358-398 行，修复前）：

```cpp
void XList<TElem>::Delete(__in TElem* const el)
{
    m_lock.Get();          // ← ★ 第一次获取 Spinlock<27,1,268435714>

    AddRecord(XLO_Delete, el);

    // 遍历所有 enumerator，通知它们这个元素要被删除
    TEnumerators::EnumeratorType iter(&m_enumerators);
    for (EnumeratorType* pEnum = iter.GetNext(nullptr);
         pEnum != nullptr;
         pEnum = iter.GetNext(pEnum))
    {
        pEnum->Invalidate(el);   // ← ★ 问题在这里！在持有 spinlock 的情况下调用
    }

    TElements::Delete(el);       // 从链表中移除
    m_lock.Release();            // 释放 spinlock
    el->SetList(nullptr);
}
```

### 6.3 XListEnumerator::Invalidate() — 触发重入的地方

来自 `xlist.inl`（第 1164-1198 行，修复前）：

```cpp
void XListEnumerator<TElem>::Invalidate(_In_ TElem* const el)
{
    // 注意：此时 m_lock 已经被 Delete() 持有！
    AssertHdr(m_pList->GetLock()->IsLockHeld());

    if (el == m_baseObject)
    {
        // 被删除的元素是当前的 base → 需要更新 base
        m_baseObject = m_pList->GetPrevElem(el);  // 获取前一个元素（会 AddRef）

        if (m_baseObject != nullptr)
        {
            // ★★★ 这里是 BUG ★★★
            // 代码注释说 "This cannot be the last reference"
            // 并断言 refcount > 1
            // 但在竞态条件下，这个断言不成立！
            AssertHdr(m_baseObject->GetRefCount() > 1);

            m_baseObject->Release();   // ← 如果这是最后一个引用：
            //   → Release() 导致 refcount 降为 0
            //   → 触发 RemoveAndDestroy()
            //   → RemoveAndDestroy() 调用 XList::Delete()
            //   → Delete() 尝试 m_lock.Get()
            //   → 同一个 spinlock，同一个线程，不可重入
            //   → ★ SELF-DEADLOCK！永远不会返回
        }
    }
}
```

### 6.4 完整的自死锁调用链

```
Thread A:
  XList::Delete(element_X)
    → m_lock.Get()                         ← 获取 Spinlock<27> ✅
    → for each enumerator:
        → Invalidate(element_X)
          → m_baseObject = GetPrevElem()   ← AddRef on prev element
          → m_baseObject->Release()        ← 如果 refcount 降为 0:
            → RemoveAndDestroy()
              → XList::Delete(m_baseObject)
                → m_lock.Get()             ← 再次获取同一个 Spinlock<27> ❌
                                              spinlock 不可重入
                                              → SpinToAcquire
                                              → Backoff
                                              → Sleep（CPU = 0ms）
                                              → ★ 永久死锁
```

---

## 7. PR 1298481 修复分析

### 修复方式：Deferred Release（延迟释放）

PR 1298481 由 Keiichiro Koga 提交，2024-03-19 合并。核心修改在 `xlist.inl` 中。

**修复前（有 bug 的代码）：**

`Delete()` 在持有 spinlock 时调用 `Invalidate()`，`Invalidate()` 又直接调用 `Release()` — 如果触发递归删除，会在持有 spinlock 的情况下再次尝试获取它。

**修复后：**

```cpp
void XList<TElem>::Delete(__in TElem* const el)
{
    TElem* deferredReleaseObject = nullptr;    // ← 新增：延迟释放指针
    UINT deferredReleaseCount = 0;             // ← 新增：延迟释放计数

    {
        Holder lockScope = m_lock.GetIntoHolder();  // 获取 spinlock（RAII 作用域）

        AddRecord(XLO_Delete, el);

        // Invalidate all iterators — 但不再立即 Release
        for (EnumeratorType* pEnum = ...; pEnum != nullptr; ...)
        {
            pEnum->Invalidate(
                el,
                &deferredReleaseObject,        // ← 新参数：收集需要 Release 的对象
                deferredReleaseCount);          // ← 新参数：计数
        }

        TElements::Delete(el);
    }   // ← ★ spinlock 在这里释放（RAII lockScope 析构）

    // ★★★ 关键修复 ★★★
    // Release 操作移到 spinlock 作用域之外执行！
    // 即使 Release 触发 RemoveAndDestroy → 递归 Delete()，
    // 也不会死锁，因为 spinlock 已经释放了
    for (UINT i = 0; i < deferredReleaseCount; i++)
    {
        deferredReleaseObject->Release();      // ← 安全：spinlock 未被持有
    }
    deferredReleaseObject = nullptr;
}
```

**修复核心思想：**

| | 修复前 | 修复后 |
|---|--------|--------|
| `Release()` 调用时机 | 在 `Invalidate()` 内部，spinlock **持有中** | 在 `Delete()` 返回前，spinlock **已释放** |
| 递归 `Delete()` 风险 | 会死锁（spinlock 不可重入） | 安全（spinlock 已释放） |
| 实现方式 | 直接调用 `m_baseObject->Release()` | 收集到 `deferredReleaseObject`，延迟释放 |

---

## 8. 相关 Bug

| Bug ID | 标题 | 状态 | 负责人 | 版本 | 相关度 |
|--------|------|------|--------|------|--------|
| **2328489** | XList_ProbCostData_::Insert (NON_YIELDING) | Active | — | 2022.160.937 | ★★★★★ 精确匹配，引用 PR 1298481 |
| **3507392** | TCacheStore CacheProbabilisticAlgorithm (NON_YIELDING) | Done | Keiichiro Koga | 2022.160.5564 | ★★★★★ 关联 PR 1298481 |
| **3358306** | XListEnumerator_ProbCostData_::Invalidate (ASSERTION) | New | — | 2022.160.5506 | ★★★★☆ 相同根因 |
| **2627135** | XList_ProbCostData_::Insert (INVALID_POINTER_READ) | Done | — | 2022.160.5100 | ★★★★☆ 相同竞态条件 |
| **2180018** | XListEnumerator_ProbCostData_::GetNext (INVALID_POINTER_READ) | New | Satyendra Mishra | 2022.160.816 | ★★★☆☆ 相关 |
| **4887916** | XTListEnumerator_ProbCostData_::ReInit (STALLED) | New | — | 2025.170.1017 | ★★★☆☆ SQL 2025 中同样的问题 |

---

## 9. 根因

这是一个已知 bug — SOS 缓存框架（`xlist.inl`）中 **`XListEnumerator::Invalidate` 的竞态条件**。概率缓存模拟算法使用的 XList 数据结构存在缺陷：`Invalidate` 函数过早释放了对基础对象的引用。当另一个线程并发修改列表，或当同一线程通过缓存存储的释放路径重入时，不可重入的 spinlock（`Spinlock<27,1,268435714>`）被同一线程获取两次，造成永久自死锁。

**自死锁流程：**
```
线程 A 调用 ColumnStoreObjectRef::Fix()
  → Fix() 调用 Unfix() 释放之前固定的对象
    → Unfix() → CSPool->UnfixObject()
      → TCacheStore::ReleaseUserData()
        → ActualEntryToSimulatedOrHistoryEntry()
          → TCacheSimulation::SimulationInsertion()
            → XList<ProbCostData>::Insert()
              → 获取 Spinlock<27,1,268435714> ← 第一次获取
              → 在列表操作中，调用 XList::Delete
                → Delete() 尝试再次获取 Spinlock<27,1,268435714>
                → ★ 死锁：线程永远等待自己
```

---

## 10. 解决方案

### PR 1298481 修复可用性

修复在 **PR 1298481："SOS: Fix XList race condition in Invalidate"** 中，由 Keiichiro Koga 提交，2024-03-19 合并。PR 引入了 Trace Flag **16405** (`SOS_TRCFLG_RETAIL_XLIST_FIX`) 作为功能开关。

**修复在各分支的可用性：**

| Branch | 修复代码 | TF 16405 | 状态 |
|--------|---------|----------|------|
| master | ✅ 存在 | Reserved（默认启用） | ✅ 已修复 |
| rel/box/sql2025/sql2025_rtm_qfe-cu | ✅ 存在 | Reserved（默认启用） | ✅ 已修复 |
| rel/box/sql2022/sql2022_rtm_qfe-cu | ❌ 不存在 | 不存在 | ❌ 未 backport |

**验证方法：** 在各分支中搜索修复代码的关键标识符 `deferredReleaseObject`（xlist.inl 中的延迟释放变量）：
- master: ✅ 找到
- SQL 2025 release branch: ✅ 找到
- SQL 2022 release branch: ❌ 未找到

**修复内容：**
1. 移除了 `XListEnumerator::Invalidate` 中的过早引用释放
2. 保留 `GetPrevElem` 中添加的引用，直到迭代推进或完成
3. 在 `XList::Delete` 中引入了**延迟释放** — 之前的基础对象引用在 spinlock 作用域**之外**释放
4. 由 **XListFix** 功能开关控制（TF 16405），在最新分支中已标记为 Reserved（默认启用）

**修复涉及的文件：**
- `Sql/DkTemp/base/include/xlist.h` / `xlist.inl` — 核心修复
- `Sql/DkTemp/sos/include/sos.h` — 功能开关
- `Sql/DkTemp/sos/include/sosTraceflags.h` — 跟踪标志 16405
- 功能开关 XML 和测试

### 对客户的建议

由于修复**尚未 backport 到 SQL Server 2022**，建议：

1. **首选：通过 support case 请求 On-Demand hotfix (OD fix)** — 引用 PR 1298481、Bug 3003613、TF 16405
2. **替代方案：升级到 SQL Server 2025**（修复已包含，TF 16405 默认启用）
3. **临时 workaround：降低 MAXDOP** — 减少并发 columnstore 扫描线程数，降低触发 XList spinlock self-deadlock 的概率

---

## 11. 客户环境检查

由于根因已通过 dump 分析确认为 **code bug（XList spinlock self-deadlock）**，不是 workload 或配置问题，因此不需要收集列存储索引数量、spinlock 统计等信息。唯一需要确认的是客户版本是否包含修复：

| 检查项 | 查询 | 看什么 | 说明什么 |
|--------|------|--------|---------|
| 版本确认 | `SELECT @@VERSION` | Build number | 确认是否需要 OD hotfix。修复尚未 backport 到 SQL 2022 任何 CU，所以当前所有 SQL 2022 版本都受影响。 |

---

## 12. 升级路径

- **Area Path**: Database Systems\SQL Server\SQL Engine\SQLOS
- **负责人**: Keiichiro Koga (keiikoga@microsoft.com) — PR 作者
- **DRI**: Satyendra Mishra (satyem@microsoft.com) — SoS DRI
- **PR**: [PR 1298481](https://msdata.visualstudio.com/Database%20Systems/_git/DsMainDev/pullrequest/1298481)

---

## 13. 参考资料

- **PR 1298481**: SOS: Fix XList race condition in Invalidate
- **Bug 2328489**: [链接](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2328489)
- **Bug 3507392**: [链接](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/3507392)
- **Bug 3358306**: [链接](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/3358306)
- **Bug 2627135**: [链接](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2627135)
- **源码**: `sql\dktemp\base\include\xlist.inl`, `sql\Ntdbms\storeng\dfs\manager\columnstoreobjectref.cpp`
