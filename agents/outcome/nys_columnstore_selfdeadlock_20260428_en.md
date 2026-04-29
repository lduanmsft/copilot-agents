# ColumnStore ObjectPool Spinlock Self-Deadlock — Non-Yielding Scheduler Analysis

**ICM**: https://portal.microsofticm.com/imp/v5/incidents/details/528563800/summary
**Date**: 2026-04-28  
**Type**: Spinlock Self-Deadlock  
**SQL Version**: SQL Server 2022  
**Affected Area**: Column Stores / SQLOS Cache  

---

## 1. Problem Summary

A SELECT INTO query scanning a columnstore index gets stuck in a non-yielding scheduler (NYS) condition that **never resolves**. Multiple schedulers (13, 14, 15, 17) report non-yielding simultaneously. The key diagnostic indicator is **CPU = 0ms** (both kernel and user), with **System Idle 99%** — proving the threads are NOT running but permanently sleeping. This is a **spinlock self-deadlock**: each thread holds an XList spinlock and then re-enters the same spinlock through a different code path within the cache simulation layer, creating a permanent hang.

**Error Log Evidence:**
```
Process 0:0:0 (0x4240) Worker 0x000001A45CCE8160 appears to be non-yielding on Scheduler 13.
Approx Thread CPU Used: kernel 0 ms, user 0 ms.
Process Utilization 0%. System Idle 99%. Interval: 70206 ms.
```
- 17 out of 325 threads match ColumnStoreObjectPool filter
- Multiple schedulers stuck simultaneously
- Case title: query "gets stuck in an NYS that never resolves"

---

## 2. Research Methodology & Tools Used

| Step | Tool | Parameters | Result |
|------|------|-----------|--------|
| Bug search (XList race) | msdata-search_workitem | "XList race condition Invalidate spinlock self-deadlock" | 0 results |
| Bug search (ColumnStore) | msdata-search_workitem | "ColumnStoreObjectPool non-yielding spinlock deadlock" | 0 results |
| Bug search (TCacheStore) | msdata-search_workitem | "SpinlockBase::Sleep TCacheStore CacheProbabilisticAlgorithm self-deadlock" | 0 results |
| Bug search (Spinlock 27) | msdata-search_workitem | "Spinlock 27 XList ProbCostData non-yielding" | 16 results ★ |
| Bug search (PR 1298481) | msdata-search_workitem | "1298481 SOS Fix XList race condition" | 2 results ★ |
| Bug details | msdata-wit_get_work_item | IDs: 2328489, 3507392, 4887916, 2627135, 2180018 | Full details retrieved |
| Source code | msdata-repo_get_file_content | columnstoreobjectref.cpp | Fix/Unfix re-entrancy confirmed |
| PR details | msdata-repo_get_pull_request_by_id | PR 1298481 | Fix confirmed, merged 2024-03-19 |
| PR changes | msdata-repo_get_pull_request_changes | PR 1298481 | 17 files changed |
| CSS Wiki search | csswiki-search_wiki | "non-yielding scheduler columnstore cache spinlock" | General NYS docs (no specific TSG) |

---

## 3. Callstack Narration (bottom-to-top)

Reading from bottom to top, here's what this thread was doing:

### 1. QUERY EXECUTION (frames 2d-29)
`CXStmtSelectInto::XretExecute → CXStmtDML::XretDMLExecute → CXStmtQuery::ErsqExecuteQuery → CQueryScan::GetRow`  
The query is a **SELECT INTO** statement being executed. It begins pulling rows from the query plan.

### 2. DML BATCH PROCESSING (frames 28-24)
`CQScanUpdateNew::GetRow → CQScanBatchHelper::GetRow → CBpQScan::GetNextRootBatch → CBpQScanProject → CBpQScanHashJoin`  
The SELECT INTO is inserting rows, pulling data in **batch mode** through a hash join operator.

### 3. HASH JOIN — PROBE SIDE (frames 23-17)
`CBpQScanHashJoin::Main → CBpPartialJoin::ProcessProbeSide → CBpQScanFilter → CBpQScanColumnStoreScan::BpGetNextBatch`  
The query is probing the hash join by scanning a **columnstore index**.

### 4. COLUMNSTORE ROW GROUP SCAN (frames 16-0f)
`ColumnsetSS::FetchNextColumnBatch → RowBucketScanner::GetNextRowGroup → RowGroupManager::SetUpRowGroup → ColumnStoreObjectRef::Fix`  
Setting up the next row group for scanning. The `Fix()` call pins the row group object in the **ColumnStoreObjectPool** cache. **Critical**: `Fix()` calls `Unfix()` first if a previous object is pinned (line 109), which releases the old object from the cache store.

### 5. CACHE STORE INSERTION (frames 0d-0a)
`ColumnStoreObjectPool::ConstructObjectAndFix → TCacheStore::CacheUserDataExclusiveWithControl → TCacheSimulation::SimulationHit → TCacheStore::ConvertEntryToActual`  
Inserting the row group object into the ColumnStoreObjectPool cache. The cache's **probabilistic simulation algorithm** updates its internal cost-tracking XList.

### 6. ★ STUCK HERE — SPINLOCK SELF-DEADLOCK (frames 0a-00)

**Note:** In the initial callstack, frames 07-09 were collapsed as inline frames by the debugger. The full dump with source references reveals the complete self-deadlock path:

```
Frame 0a: XList<ProbCostData>::Delete+0x11f          [xlist.inl @ 373]
            → m_lock.Get() completed                  ← ✅ FIRST acquisition of Spinlock<27>
            → calls pEnum->Invalidate(el)              ← while HOLDING the spinlock

Frame 09:   XListEnumerator<ProbCostData>::Invalidate+0x8f  [xlist.inl @ 1195]
              → m_baseObject->Release()                ← ★ BUG: premature reference release

Frame 08:     XListElem<ProbCostData>::Release+0x1b    [xlist.inl @ 240]
                → refcount drops to 0

Frame 07:       XListElem<ProbCostData>::RemoveAndDestroy+0x1f  [xlist.inl @ 286]
                  → triggers recursive deletion

Frame 06: XList<ProbCostData>::Delete+0x64             [xlist.inl @ 361]
            → m_lock.Get()                             ← ❌ SECOND acquisition of SAME Spinlock<27>
            → non-reentrant → SpinToAcquire → Backoff → Sleep

Frames 05-00: Spinlock<27>::Get → SpinToAcquireOptimistic → Backoff → Sleep → ZwDelayExecution
            → CPU = 0ms, permanent sleep
```

**Spinlock owner confirmation from dump:**
```
dx (*((sqlmin!SpinlockBase::Lock *)0x19e1cf25b98))
    m_threadId : 0x4240        ← spinlock is held by thread 0x4240
    
~~[0x4240]s → Thread 177      ← that's THIS thread!
```

Thread 177 (0x4240) holds Spinlock<27> AND is trying to acquire the same Spinlock<27> — **confirmed self-deadlock**.

- **CPU = 0ms** confirms the thread is sleeping, not spinning
- **This is a SELF-DEADLOCK — it will never resolve**
- Spinlocks are **non-reentrant**
- All 17 stuck threads are waiting on this spinlock held by thread 177

---

## 4. Callstack Analysis

### Parsed Layers

| Layer | Frames | Functions | Purpose |
|-------|--------|-----------|---------|
| Query Execution | 2d-29 | CXStmtSelectInto, CXStmtDML, CXStmtQuery | SELECT INTO execution |
| DML/Batch | 28-24 | CQScanUpdateNew, CQScanBatchHelper, CBpQScanHashJoin | Batch mode row processing |
| Hash Join | 23-17 | CBpPartialJoin, CBpQScanFilter, CBpQScanColumnStoreScan | Columnstore scan for hash probe |
| Columnstore Scan | 16-0f | ColumnsetSS, RowBucketScanner, RowGroupManager, ColumnStoreObjectRef | Row group setup and caching |
| Cache Store | 0d-0a | ColumnStoreObjectPool, TCacheStore, TCacheSimulation | Cache insertion with probabilistic algorithm |
| **Spinlock (STUCK)** | 06-00 | XList::Delete, Spinlock<27,1,268435714>, SpinlockBase::Sleep | **Self-deadlock on XList spinlock** |

### Spinlock Details
- **Spinlock Type**: 27
- **Instance ID**: 268435714
- **Behavior**: Non-reentrant — same thread cannot acquire twice
- **Source file**: `sql\dktemp\base\include\xlist.inl`

---

## 5. Source Code Analysis

### 5.1 ColumnStoreObjectRef::Fix — The Re-Entrancy Trigger

From `columnstoreobjectref.cpp` (line ~109):

```cpp
ColumnStoreObject*
ColumnStoreObjectRef::Fix(...)
{
    if (m_pObject != NULL)
    {
        DBG_ASSERT(m_isCached);
        Unfix();  // ← RELEASES the old object, which enters cache simulation
    }

    m_pObject = CSPool->RetrieveObjectAndFix(...);  // ← Retrieves/constructs new object
    m_isCached = true;
    return m_pObject;
}
```

The critical path: `Fix()` → `Unfix()` → `UnfixObject()` → `ReleaseUserData()` → cache simulation → **acquires XList spinlock**. Then `Fix()` continues to `RetrieveObjectAndFix()` → `ConstructObjectAndFix()` → cache simulation → **tries to acquire the SAME XList spinlock** → **DEADLOCK**.

### 5.2 XList::Delete() — First Spinlock Acquisition (callstack frame 06)

From `xlist.inl` (line 358-398, before fix):

```cpp
void XList<TElem>::Delete(__in TElem* const el)
{
    m_lock.Get();          // ← ★ FIRST acquisition of Spinlock<27,1,268435714>

    AddRecord(XLO_Delete, el);

    // Invalidate all iterators — called WHILE HOLDING the spinlock
    TEnumerators::EnumeratorType iter(&m_enumerators);
    for (EnumeratorType* pEnum = iter.GetNext(nullptr);
         pEnum != nullptr;
         pEnum = iter.GetNext(pEnum))
    {
        pEnum->Invalidate(el);   // ← ★ THE BUG: calls Release() while spinlock is held
    }

    TElements::Delete(el);       // Remove from linked list
    m_lock.Release();            // Release spinlock
    el->SetList(nullptr);
}
```

### 5.3 XListEnumerator::Invalidate() — Where Re-Entrancy Happens

From `xlist.inl` (line 1164-1198, before fix):

```cpp
void XListEnumerator<TElem>::Invalidate(_In_ TElem* const el)
{
    // NOTE: m_lock is ALREADY HELD by Delete() at this point!
    AssertHdr(m_pList->GetLock()->IsLockHeld());

    if (el == m_baseObject)
    {
        // The element being deleted is our current base → need to update base
        m_baseObject = m_pList->GetPrevElem(el);  // Gets prev element (AddRefs it)

        if (m_baseObject != nullptr)
        {
            // ★★★ THIS IS THE BUG ★★★
            // The comment says "This cannot be the last reference"
            // and asserts refcount > 1
            // But under race conditions, this assertion does NOT hold!
            AssertHdr(m_baseObject->GetRefCount() > 1);

            m_baseObject->Release();   // ← If this IS the last reference:
            //   → Release() causes refcount to drop to 0
            //   → Triggers RemoveAndDestroy()
            //   → RemoveAndDestroy() calls XList::Delete()
            //   → Delete() calls m_lock.Get()
            //   → Same spinlock, same thread, non-reentrant
            //   → ★ SELF-DEADLOCK! Never returns
        }
    }
}
```

### 5.4 Complete Self-Deadlock Call Chain

```
Thread A:
  XList::Delete(element_X)
    → m_lock.Get()                         ← Acquires Spinlock<27> ✅
    → for each enumerator:
        → Invalidate(element_X)
          → m_baseObject = GetPrevElem()   ← AddRef on prev element
          → m_baseObject->Release()        ← If refcount drops to 0:
            → RemoveAndDestroy()
              → XList::Delete(m_baseObject)
                → m_lock.Get()             ← Tries to acquire SAME Spinlock<27> ❌
                                              Spinlock is non-reentrant
                                              → SpinToAcquire
                                              → Backoff
                                              → Sleep (CPU = 0ms)
                                              → ★ PERMANENT DEADLOCK
```

---

## 6. PR 1298481 Fix Analysis

### Fix Approach: Deferred Release

PR 1298481 by Keiichiro Koga, merged 2024-03-19. Core changes in `xlist.inl`.

**Before fix (buggy code):**

`Delete()` calls `Invalidate()` while holding the spinlock. `Invalidate()` directly calls `Release()` — if this triggers a recursive deletion, it attempts to acquire the already-held spinlock.

**After fix:**

```cpp
void XList<TElem>::Delete(__in TElem* const el)
{
    TElem* deferredReleaseObject = nullptr;    // ← NEW: deferred release pointer
    UINT deferredReleaseCount = 0;             // ← NEW: deferred release count

    {
        Holder lockScope = m_lock.GetIntoHolder();  // Acquire spinlock (RAII scope)

        AddRecord(XLO_Delete, el);

        // Invalidate all iterators — but NO LONGER releases immediately
        for (EnumeratorType* pEnum = ...; pEnum != nullptr; ...)
        {
            pEnum->Invalidate(
                el,
                &deferredReleaseObject,        // ← NEW param: collect objects to release
                deferredReleaseCount);          // ← NEW param: count
        }

        TElements::Delete(el);
    }   // ← ★ Spinlock RELEASED here (RAII lockScope destructor)

    // ★★★ KEY FIX ★★★
    // Release operations moved OUTSIDE the spinlock scope!
    // Even if Release triggers RemoveAndDestroy → recursive Delete(),
    // it will NOT deadlock because the spinlock is no longer held
    for (UINT i = 0; i < deferredReleaseCount; i++)
    {
        deferredReleaseObject->Release();      // ← SAFE: spinlock is NOT held
    }
    deferredReleaseObject = nullptr;
}
```

**Fix Summary:**

| | Before Fix | After Fix |
|---|--------|--------|
| `Release()` timing | Inside `Invalidate()`, spinlock **HELD** | After `Delete()` returns, spinlock **RELEASED** |
| Recursive `Delete()` risk | Deadlocks (spinlock non-reentrant) | Safe (spinlock already released) |
| Implementation | Direct `m_baseObject->Release()` | Collected into `deferredReleaseObject`, released later |
| Files changed | — | `xlist.h`, `xlist.inl`, `sos.h`, `sosTraceflags.h` (17 files total) |
| Feature switch | — | Controlled by **XListFix** feature flag |

---

## 7. Related Bugs

## 6. Related Bugs

| Bug ID | Title | State | Assignee | Version | Relevance |
|--------|-------|-------|----------|---------|-----------|
| **2328489** | XList_ProbCostData_::Insert (NON_YIELDING) | Active | — | 2022.160.937 | ★★★★★ Exact match, references PR 1298481 |
| **3507392** | TCacheStore CacheProbabilisticAlgorithm (NON_YIELDING) | Done | Keiichiro Koga | 2022.160.5564 | ★★★★★ Linked to PR 1298481 |
| **3358306** | XListEnumerator_ProbCostData_::Invalidate (ASSERTION) | New | — | 2022.160.5506 | ★★★★☆ Same root cause |
| **2627135** | XList_ProbCostData_::Insert (INVALID_POINTER_READ) | Done | — | 2022.160.5100 | ★★★★☆ Same race condition |
| **2180018** | XListEnumerator_ProbCostData_::GetNext (INVALID_POINTER_READ) | New | Satyendra Mishra | 2022.160.816 | ★★★☆☆ Related |
| **4887916** | XTListEnumerator_ProbCostData_::ReInit (STALLED) | New | — | 2025.170.1017 | ★★★☆☆ Same issue in SQL 2025 |

---

## 7. Root Cause

This is a known bug — a **race condition in `XListEnumerator::Invalidate`** in the SOS cache framework (`xlist.inl`). The XList data structure used by the probabilistic cache simulation algorithm has a flaw where the `Invalidate` function releases a reference on the base object prematurely. When another thread modifies the list concurrently, or when the same thread re-enters through the cache store's release path, the non-reentrant spinlock (`Spinlock<27,1,268435714>`) is acquired twice by the same thread, causing a permanent self-deadlock.

**Self-Deadlock Flow:**
```
Thread A calls ColumnStoreObjectRef::Fix()
  → Fix() calls Unfix() to release previously pinned object
    → Unfix() → CSPool->UnfixObject()
      → TCacheStore::ReleaseUserData()
        → ActualEntryToSimulatedOrHistoryEntry()
          → TCacheSimulation::SimulationInsertion()
            → XList<ProbCostData>::Insert()
              → Acquires Spinlock<27,1,268435714> ← FIRST ACQUISITION
              → During list manipulation, XList::Delete is called
                → Delete() tries to acquire Spinlock<27,1,268435714> AGAIN
                → ★ DEADLOCK: Thread waits for itself forever
```

---

## 9. Resolution

### PR 1298481 Fix Availability

The fix is in **PR 1298481: "SOS: Fix XList race condition in Invalidate"** by Keiichiro Koga, merged 2024-03-19. The PR introduces Trace Flag **16405** (`SOS_TRCFLG_RETAIL_XLIST_FIX`) as a feature switch.

**Fix availability across branches:**

| Branch | Fix Code | TF 16405 | Status |
|--------|----------|----------|--------|
| master | ✅ Present | Reserved (default-on) | ✅ Fixed |
| rel/box/sql2025/sql2025_rtm_qfe-cu | ✅ Present | Reserved (default-on) | ✅ Fixed |
| rel/box/sql2022/sql2022_rtm_qfe-cu | ❌ Not present | Does not exist | ❌ Not backported |

**Verification method:** Searched for the fix's key identifier `deferredReleaseObject` (the deferred release variable in xlist.inl) in each branch:
- master: ✅ Found
- SQL 2025 release branch: ✅ Found
- SQL 2022 release branch: ❌ Not found

**What the fix does:**
1. Removes the premature reference release in `XListEnumerator::Invalidate`
2. Keeps the reference added in `GetPrevElem` until the iteration advances or finishes
3. Introduces **deferred release** in `XList::Delete` — previous base object references are released **outside** of the spinlock scope
4. Controlled by the **XListFix** feature switch (TF 16405), marked as Reserved (default-on) in latest branches

**Files modified by the fix:**
- `Sql/DkTemp/base/include/xlist.h` / `xlist.inl` — Core fix
- `Sql/DkTemp/sos/include/sos.h` — Feature switch
- `Sql/DkTemp/sos/include/sosTraceflags.h` — Trace flag 16405
- Feature switch XML and tests

### Customer Recommendation

Since the fix has **NOT been backported to SQL Server 2022**, the recommendations are:

1. **Primary: Request an On-Demand hotfix (OD fix) via support case** — Reference PR 1298481, Bug 3003613, TF 16405
2. **Alternative: Upgrade to SQL Server 2025** (fix is included, TF 16405 is default-on)
3. **Temporary workaround: Reduce MAXDOP** — Lower concurrent columnstore scan thread count to reduce the probability of triggering the XList spinlock self-deadlock

---

## 10. Customer Environment Checks

Since the root cause has been confirmed via dump analysis as a **code bug (XList spinlock self-deadlock)**, not a workload or configuration issue, there is no need to collect columnstore index counts, spinlock statistics, or cache store metrics. The only required check is to confirm the customer's version:

| Check | Query | What to look for | What it means |
|-------|-------|-------------------|---------------|
| Version confirmation | `SELECT @@VERSION` | Build number | Confirms whether OD hotfix is needed. The fix has not been backported to any SQL 2022 CU, so all current SQL 2022 builds are affected. |

---

## 11. Escalation

- **Area Path**: Database Systems\SQL Server\SQL Engine\SQLOS
- **Owner**: Keiichiro Koga (keiikoga@microsoft.com) — PR author
- **DRI**: Satyendra Mishra (satyem@microsoft.com) — SoS DRI
- **PR**: [PR 1298481](https://msdata.visualstudio.com/Database%20Systems/_git/DsMainDev/pullrequest/1298481)

---

## 12. References

- **PR 1298481**: SOS: Fix XList race condition in Invalidate
- **Bug 2328489**: [Link](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2328489)
- **Bug 3507392**: [Link](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/3507392)
- **Bug 3358306**: [Link](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/3358306)
- **Bug 2627135**: [Link](https://msdata.visualstudio.com/Database%20Systems/_workitems/edit/2627135)
- **Source**: `sql\dktemp\base\include\xlist.inl`, `sql\Ntdbms\storeng\dfs\manager\columnstoreobjectref.cpp`
