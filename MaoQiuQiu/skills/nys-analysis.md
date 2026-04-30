# Non-Yielding Scheduler (NYS) Analysis Skill

This skill is referenced by `callstack-research.agent.md` when the callstack type is detected as non-yielding.
It is NOT a standalone agent — it provides analysis rules and procedures for the callstack-research agent to follow.

---

## NYS Classification — FIRST STEP (before code analysis)

Check error log metrics from the non-yielding event:

```
"Approx Thread CPU Used: kernel X ms, user Y ms"
"Process Utilization Z%. System Idle W%"
```

### Decision Tree

```
CPU > 0 ms?
  YES → CPU-BOUND NON-YIELDING
        Thread is running but not yielding to the scheduler.
        Root cause: tight loop without yield point.
        Focus: Find the loop, check yield points, cache-hit vs miss paths.

  NO (0 ms kernel, 0 ms user) → Thread is NOT running
        ↓
        Callstack in SpinlockBase::Sleep / Backoff?
          YES → ⚠️ SPINLOCK SELF-DEADLOCK (highest priority)
                Thread holds a spinlock and tries to re-acquire the SAME one.
                This NEVER resolves — it's a permanent hang.
                
                Confirm with:
                - "never resolves" in case description
                - System Idle ~99% (no CPU work being done)
                - Multiple threads stuck on same spinlock type
                - Spinlock owner (dx spinlock address → m_threadId) = stuck thread itself

          NO  → EXTERNAL WAIT
                Thread blocked on I/O, network, or external dependency.
                Check wait type and external resources.
```

---

## CPU-Bound Non-Yielding Analysis

### Source Code Analysis
1. **Find the loop**: Identify `while`/`for`/`do-while` containing the faulting function
2. **Check for yield points**: Search for `SOS_Task::Yield`, `SOS_Task::OSYield`, `YieldAndCheckForAbort` inside the loop
3. **Trace conditional paths**: If yield only happens in one code path (e.g., cache miss → I/O → yield), document both paths
4. **Check lock safety**: Note any latches/locks held inside the loop — yield must NOT happen while holding them
5. **Count iteration scale**: How many iterations can this loop run? (e.g., one per HoBt = potentially tens of thousands)

### Fix Checklist (for proposing a code fix)
- [ ] Yield interval: use power-of-2 (compiler optimizes `% 64` to `& 0x3F`)
- [ ] Use `YieldAndCheckForAbort` vs plain `Yield` (supports KILL/cancel)
- [ ] Verify yield does NOT happen while holding latches/locks
- [ ] Check other engine scan patterns for consistent interval choice
- [ ] Identify ALL entry points that need the same fix
- [ ] Analyze both cache-hit and cache-miss performance impact

### Customer Checks
```sql
-- Check for non-yielding events in error log
EXEC xp_readerrorlog 0, 1, N'non-yielding';

-- Check metadata cache size (for metadata loop non-yielding)
SELECT type, pages_kb / 1024 AS size_mb, entries_count
FROM sys.dm_os_memory_cache_counters
WHERE type LIKE '%Object%' OR type LIKE '%Schema%' OR type LIKE '%Metadata%'
ORDER BY pages_kb DESC;

-- Check HoBt count (for index stats DMV non-yielding)
SELECT DB_NAME() AS db, COUNT(*) AS total_hobts
FROM sys.partitions WHERE index_id >= 0;

-- Check for monitoring tools scanning index DMVs
SELECT j.name, js.step_name, js.command
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps js ON j.job_id = js.job_id
WHERE js.command LIKE '%dm_db_index%'
   OR js.command LIKE '%index_physical_stats%'
   OR js.command LIKE '%index_operational_stats%';
```

---

## Spinlock Self-Deadlock Analysis

### Identification
1. **CPU = 0ms** (kernel AND user) — thread is sleeping, not spinning
2. **System Idle ~99%** — no CPU contention
3. **Callstack shows** `SpinlockBase::Sleep` / `SpinlockBase::Backoff` / `SpinToAcquireOptimistic`
4. **Never resolves** — contention resolves eventually, self-deadlock doesn't
5. **Spinlock owner = stuck thread itself** — confirm with:
   ```
   dx (*((sqlmin!SpinlockBase::Lock *)<spinlock_address>))
       m_threadId : 0xNNNN    ← if this matches the stuck thread → self-deadlock
   ```

### Source Code Re-Entrancy Analysis (CRITICAL)
When a callstack shows `SpinlockBase::Sleep` with CPU=0:

1. **Find the function that acquires the spinlock** (`m_lock.Get()` or `Spinlock::Get`)
2. **List ALL functions called while the spinlock is held** (between `Get()` and `Release()`)
3. **For each function called under spinlock, trace if it can call `Release()` on any ref-counted object:**
   - `XListElem::Release()` → if refcount drops to 0 → `RemoveAndDestroy()` → could call back `XList::Delete()` → `m_lock.Get()` (recursive!)
   - This is the most common self-deadlock pattern in XList, TCacheStore, and similar ref-counted data structures
4. **Search for deadlock-related comments in the source code**: 
   - grep for `deadlock`, `recursive`, `reentrant`, `re-entrant` in the source file
   - Code authors often document known risks. Example from `xlist.inl`:
     ```
     // - Therefore, a recursive Delete() will not be called
     //   (Which could result in a deadlock).
     ```
   - If such a comment exists, the author knew the risk but believed the assertion would prevent it
5. **Verify assertions**: If the code has `Assert(refcount > 1)` or similar guards against recursive calls, check if the assumption can be violated under race conditions
6. **Inline frame warning**: Initial callstacks may hide key frames (`Release`, `Invalidate`, `RemoveAndDestroy`). If only one lock acquisition is visible but self-deadlock is suspected, ask for full dump with:
   ```
   ~~[threadId]s
   kp    (or kn for frame numbers)
   ```

### Self-Deadlock Pattern Template

```
Thread A:
  Function_X()                        ← outer function
    → spinlock.Get()                  ← ✅ FIRST acquisition
    → for each item:
        → Callback()                  ← called while spinlock held
          → ref_counted_obj->Release()  ← if refcount drops to 0:
            → obj->Destroy()
              → Function_X()          ← RECURSIVE call
                → spinlock.Get()      ← ❌ SECOND acquisition, SAME spinlock
                → non-reentrant → DEADLOCK
```

### PR/Fix Correlation
1. **Identify the spinlock**: Extract type ID and instance ID from `Spinlock<type,x,id>`
2. **Search for the exact fix**: 
   - The spinlock-holding function name (e.g., `"XList race condition"`)
   - The data structure class name (e.g., `"ColumnStoreObjectPool deadlock"`)
   - The spinlock type number
3. **If a PR/fix is found**: the answer is **"apply the CU containing the fix"**, NOT a workaround
4. **Explain what the fix does**:
   - Common fix pattern: **Deferred Release** — collect objects to release, defer `Release()` calls to AFTER spinlock is released
   - Other patterns: changed lock ordering, made spinlock reentrant, removed double acquisition, added try-lock

### Customer Checks
```sql
-- Check SQL Server version (does it contain the fix?)
SELECT @@VERSION;

-- Check spinlock stats
SELECT name, collisions, spins, spins_per_collision, sleep_time, backoffs
FROM sys.dm_os_spinlock_stats
WHERE name LIKE '%CACHESTORE%' OR collisions > 1000
ORDER BY collisions DESC;

-- Check relevant cache store
SELECT * FROM sys.dm_os_memory_cache_counters 
WHERE name LIKE '%ColumnStore%' OR name LIKE '%Object%'
ORDER BY pages_kb DESC;
```

---

## Common Non-Yielding Patterns Reference

| Pattern | CPU | Spinlock in stack | Resolution |
|---------|-----|-------------------|------------|
| **Missing yield in loop** | > 0 | No | Add periodic `YieldAndCheckForAbort()` in loop |
| **Cache-hit bypasses yield** | > 0 | No | Add yield in the cached code path |
| **Spinlock self-deadlock** | = 0 | Yes (`Sleep/Backoff`) | Apply CU with fix (deferred release pattern) |
| **Spinlock contention** | > 0 | Yes (`SpinToAcquire`) | Partition the spinlock, reduce concurrency |
| **Destructor chain no yield** | > 0 | Maybe (`LockReference`) | Add yield check in destructor loop |
