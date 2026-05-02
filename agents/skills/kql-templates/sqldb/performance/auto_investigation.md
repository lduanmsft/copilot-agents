---
name: SQLDB Performance Investigation
description: Diagnoses Azure SQL Database performance issues including high CPU, memory pressure, QDS readonly, query plan regressions, query performance, compilation issues, disk space problems, worker thread exhaustion, scheduler hangs, and LSASS telemetry holes. Adapted from SQLLivesiteAgents Performance.agent.md + Performance/triage/SKILL.md.
source: SQLLivesiteAgents/Performance
distilled: 2026-05-01
---

# SQLDB Performance Investigation

> 架构: Azure SQL DB performance issues are typically resource-related (CPU/memory/disk/IO) or query-related (regression/compilation/blocking).
>
> - **Singleton**: 单数据库 - 直接节点上分析
> - **Elastic Pool (EP)**: 弹性池 - 多 DB 共享资源, 需用 EP-specific KQL
> - **GP / BC / Hyperscale**: 不同 SLO 下表行为不同 (e.g., HSC wait 仅 BC, RBPEX 仅 Hyperscale)

## Required Inputs

| Parameter | Source | Example |
|-----------|--------|---------|
| LogicalServerName | User/ICM | `my-server` |
| LogicalDatabaseName | User/ICM | `my-db` |
| StartTime | User/ICM | `2026-01-01 02:00:00` (UTC) |
| EndTime | User/ICM | `2026-01-01 03:00:00` (UTC) |

**Tips**:
- 时间窗口建议在客户报告的时间上下各扩展 1 小时: `StartTime = 报告时间 - 1h`, `EndTime = 报告时间 + 1h`
- 如果有 ICM (**只提取 4 个参数, 不读 title/description/AI summary 做 triage**):
  - **ServerName**: `ServerName` → `LogicalServerName` → parse from title
  - **DatabaseName**: `DatabaseName` → `LogicalDatabaseName` → parse from title
  - **StartTime**: `ObservedStartTime` → `ImpactStartTime` → `CreatedDate`, 然后 -1h
  - **EndTime**: `MitigateTime` → 当前 UTC (cap at StartTime + 7h), 然后 +1h
- **MI 案例**: 如果是 Managed Instance, 请参考 `mi/performance/` (架构差异: Worker.CL, BPE, etc.)

## Phase 0: Prerequisites

> **⚠️ 在主流程 `db-kql-investigation.md` Step 2a 已强制执行 Phase 0。**
> 如果通过其它路径直接进入此 auto_investigation, 必须先跑这 3 步。
> 已经跑过的, **复用变量**, 不要重复执行。

### Step 0.1: Kusto Cluster 解析

- **Skill**: `execute-kusto-query` (Common/execute-kusto-query/SKILL.md)
- DNS 解析 `{LogicalServerName}.database.windows.net` → 得到 region
- 查 `KustoConnectionConfiguration.xml` → Kusto cluster URI + database
- **永远不要猜测 Kusto cluster URI**

### Step 0.2: 获取数据库环境信息

- **Skill**: `get-db-info` (Common/get-db-info/SKILL.md)
- 查询获取: AppName, ClusterName, NodeName, physical_database_id, fabric_partition_id, SLO, deployment_type, edition, isInElasticPool

### Step 0.3: 获取 AppName/Node Filter 变量 (MANDATORY)

- **Skill**: `appnameandnodeinfo` (performance/triage/appnameandnodeinfo-SKILL.md)
- 输出变量 (传给所有后续诊断 skill, **避免重复执行**):

| Variable | 用途 |
|----------|------|
| `{AppNamesNodeNamesWithOriginalEventTimeRange}` | 大多数 telemetry KQL 的 filter |
| `{AppNamesNodeNamesWithPreciseTimeRange}` | 用 PreciseTimeStamp 的 KQL |
| `{AppNamesOnly}` | 仅 AppName 列表 |
| `{NodeNamesWithOriginalEventTimeRange}` | 节点级查询 |
| `{SumCpuMillisecondOfAllApp}` | CPU skill: 总容量 |
| `{ActualSumCpuMillisecondOfAllApp}` | CPU skill: 实际消耗 |
| `{isInElasticPool}` | CPU/QDS skill: EP vs Singleton 路由 |
| `{edition}` | 服务层判断 |
| `{service_level_objective}` | 资源限制判断 |

## Phase 1: Triage — 选择诊断 Skills

- **Skill**: `triage` (performance/triage/SKILL.md)

> **⚠️ 与 Availability 不同**: Performance triage 可同时返回 **多个** skill (e.g., 同时跑 CPU + memory)。
> **⛔ 不读 ICM keywords**: 仅基于用户输入的关键词选 skill, ICM title/description/AI summary 一律不用 (确保结果一致)。

### 关键词路由表

| Keywords (用户输入) | Routes | Note |
|---------------------|--------|------|
| "high CPU", "CPU usage", "CPU spike", "CPU 100%" | `cpu` | 最常见 |
| "memory", "OOM", "memory pressure", "overbooking", "DRG", "MRG", "buffer pool", "MEMORYCLERK" | `memory` | |
| "QDS", "Query Store", "readonly", "Error 65536/131072/262144" | `query-store` | |
| "plan regression", "APRC", "FORCE_LAST_GOOD_PLAN", "forced plan regression" | `aprc` | 通常单查询 |
| "slow query", "query performance", "query timeout", "failed query", "wait queries", "long-running" | `queries` | |
| "compilation", "compile error", "failed compilation", "compilation CPU" | `compilation` | |
| "disk space", "disk full", "tempdb full", "log full", "data full", "quota", "out of space", "XStore" | `out-of-disk` | |
| "worker thread", "thread exhaustion", "session surge", "corruption", "AKV", "Azure Key Vault", "restart", "failover", "kill command", "profiler trace" | `miscellaneous` | |
| "non-yielding", "scheduler", "dump", "hang", "unresponsive", "scheduler hang" | `sqlos` | |
| "blocking", "deadlock", "lead blocker" | `blocking` | |
| "LSASS", "telemetry hole", "telemetry gap", "sluggish VM", "frozen VM", "watchdog", "MonLogin", "residual LSASS", "LSASS cascade", "connection pool exhaustion", "PREEMPTIVE_OS_AUTHENTICATIONOPS" | `lsass` | LSASS deep-dive |
| *(default — 无明确关键词)* | `cpu` + `memory` + `out-of-disk` + `query-store` + `miscellaneous` | 5 维度全面扫描 |

### Triage 输出 (MANDATORY, 仅显示一次, 在最终 report 顶部)

```
## ✅ Triage Complete

| Field | Value |
|-------|-------|
| **Selected Skills** | {selected_skills} |
| **Reason** | {triage_reason} |
| **Evidence** | {triage_evidence} |
| **Confidence** | High (用户明确给关键词) / Standard (默认 5 skills) |
```

## Phase 2: Diagnostic Skills

> **执行顺序** (多 skill 时按此顺序): cpu → memory → out-of-disk → query-store → aprc → queries → compilation → miscellaneous → sqlos → blocking → lsass
>
> **变量传递**: Phase 0 Step 0.3 获得的所有变量必须传给每个 skill, **不要重复执行 appnameandnodeinfo**。

### Route: cpu

- **Skill**: `performance/cpu/SKILL.md`
- **KQL**: `performance/cpu/kql-livesite.yaml` (8 queries) + `kql-distilled.yaml` (2) + `kql-sqldri-CPU.yaml` (6) + `kql-sqldri-CPU_UserPoolCPUDiscrepancy.yaml` (2)
- **References**: `cpu/references/` — kernel-mode, node-level, system-pool, top-system-pool, user-pool (EP/Singleton), user-pool discrepancy
- **路由变体**: 根据 `{isInElasticPool}` 选 EP 或 Singleton 入口

### Route: memory

- **Skill**: `performance/memory/SKILL.md`
- **KQL**: `kql-livesite.yaml` (5) + `kql-distilled.yaml` (6) + `kql-sqldri-Memory.yaml` (10) + `kql-sqldri-OverCommit.yaml` (6) + `kql-sqldri-Overbooking_memory.yaml` (6)
- **References**: bufferpool-decrease, oom-summary, overbooking
- **典型问题**: OOM, MRG/DRG overbooking, buffer pool drop ≥20%

### Route: out-of-disk

- **Skill**: `performance/out-of-disk/SKILL.md`
- **KQL**: `kql-livesite.yaml` (8) + `kql-distilled.yaml` (1) + `kql-sqldri-OOD.yaml` (5) + `kql-sqldri-Disk.yaml` / `Filefulll.yaml` / `Storage_XStore.yaml` (各 1)
- **References**: data-or-log-reached-max-size, directory-quota-hit-limit, drive-out-of-space, has-out-of-space-issue, out-of-space-nodes, tempdb-full-analysis, xstore-error-analysis
- **5 类**: Drive 满, Quota 超限, 文件达 max size, Tempdb 满, XStore 错误

### Route: query-store

- **Skill**: `performance/query-store/SKILL.md`
- **KQL**: `kql-livesite.yaml` (13) + `kql-distilled.yaml` (4) + `kql-sqldri-QDS.yaml` (3) + `kql-sqldri-QDS_ReadonlyAnalysis_*.yaml` (EP:1, Shared:8, Singleton:2) + `kql-sqldri-APRC.yaml` (4)
- **References**: 13 个文件 (settings, memory, sizebased cleanup, readonly Error 65536/131072/262144, capturemode, RCA)
- **关键 Errors**: 65536 (statement hash map limit), 131072 (buffered items limit), 262144 (instance resource limit)
- **路由变体**: EP / Singleton 不同 readonly 检查路径

### Route: aprc

- **Skill**: `performance/aprc/SKILL.md`
- **KQL**: 共用 `query-store/kql-sqldri-APRC.yaml` (4)
- **References**: force-last-good-plan-state-check, forced-plan-regression-detection-of-specific-query, plan-regression-detection-of-specific-query
- **场景**: 通常针对 specific query hash 调查 (FORCE_LAST_GOOD_PLAN 状态 + plan regression)

### Route: queries

- **Skill**: `performance/queries/SKILL.md`
- **KQL**: `kql-livesite.yaml` (22 — 最多!) + `kql-distilled.yaml` (1) + `kql-sqldri-MonDmCloudDatabaseWaitStats_ActionPlan.yaml` (1) + `kql-sqldri-Query_WaitType_ActionPlans.yaml` (5)
- **References**: 22 个文件覆盖 — top CPU/memory/wait/reads/writes/log/tempdb queries, failed queries, long-running, antipattern, query-specific (CPU/memory/execution/wait/plan)
- **入口**: `top-cpu-queries.md` (默认) 或 specific-query-* (有 query hash)

### Route: compilation

- **Skill**: `performance/compilation/SKILL.md`
- **KQL**: `kql-livesite.yaml` (7) + `kql-distilled.yaml` (9) + `kql-sqldri-CPU_Compilation.yaml` (9)
- **References**: cpu-usage-of-failed-compilation, cpu-usage-of-successful-compilation, failed-compilation-summary, query-compile-gateway, top-failed-compilation-ranked-by-cpu-usage, top-successful-compilation-ranked-by-cpu-usage

### Route: miscellaneous

- **Skill**: `performance/miscellaneous/SKILL.md`
- **KQL**: `kql-livesite.yaml` (11) + `kql-distilled.yaml` (1) + `kql-sqldri-Misc.yaml` (4) + `kql-sqldri-worker.yaml` (4) + `kql-sqldri-Dump.yaml` (1) + `kql-sqldri-Misc_DatabaseCorruption.yaml` (1)
- **References**: AKV error, profiler trace, database corruption, kill command, process-id-display, sql-restart-and-failover, worker session similarity, worker thread exhaustion, xevent session detection
- **覆盖**: Worker 耗尽 + corruption + AKV + restart/failover + kill + profiler trace

### Route: sqlos

- **Skill**: `performance/sqlos/` (无 SKILL.md, 直接读 references)
- **KQL**: `kql-livesite.yaml` (2) + `kql-distilled.yaml` (1) + `kql-sqldri-SqlOS.yaml` (1)
- **References**: non-yielding.md
- **场景**: Non-yielding scheduler, dump 分析

### Route: blocking

- **Skill**: `performance/blocking/SKILL.md`
- **KQL**: `kql-livesite.yaml` (9) + `kql-distilled.yaml` (4) + `kql-sqldri-Blocking.yaml` (4)
- **References**: blocking-detection, deadlock-detection, lead-blocker-sessions, long-running-transactions, top-deadlock-queries

### Route: lsass

- **Skill**: `performance/lsass/SKILL.md`
- **References**: knowledge.md, principles.md, queries.md
- **Two-Problem 分类**:
  - **Problem 1 (Residual)**: 无外部触发, LSASS CPU 自发飙升
  - **Problem 2 (Direct)**: MonLogin / XStore spike ≥ 3× baseline 触发
- **关键检查**: per-core pegged cores, MonLogin 时序关联, XStore IO stats, watchdog (sluggish/frozen VM), virtual file IO stalls (MonSqlRgHistory), guest OS version change (MonRgLoad)

## Phase 3: ICM Correlation (Optional)

> 运行时询问: "是否需要搜索相关 ICM incidents？"
> 需要 ICM MCP 工具 (后续会添加)

### Step 3.1: Similar Incidents
- 基于 ML 相似度搜索 ICM 中的类似 incident, 提供历史上下文和已知解决方案

### Step 3.2: Correlated Incidents
- 搜索 ICM DataWarehouse 中提到相同 server/database/AppName 的 incident, 判断是否有并发关联事件

## Phase 4: RCA 输出

### 根因分类

| Category | Indicators | Customer Message |
|----------|-----------|-----------------|
| **CPU Resource Exhaustion** | User pool CPU >90%, 多 worker 同时 high CPU | 数据库 CPU 达上限, 建议升级 SLO 或优化查询 |
| **CPU - Specific Query** | 单查询占 CPU 大头, top-cpu-queries 命中 | 优化具体查询 (索引/重写/统计信息) |
| **Memory Overbooking** | OverCommit / DRG-MRG events, buffer pool drop ≥20% | 实例内存超分, 平台已介入 / 客户考虑减少并发 |
| **OOM** | Discrete OOM events in SystemHealth | 工作集超限, 检查 large queries / 增加 memory |
| **QDS Readonly - Memory Limit** | Error 65536 / 131072 | 增加 SLO (more memory budget) 或清理 QDS |
| **QDS Readonly - Disk Limit** | Error 262144, QDS size > limit | 启用 size-based cleanup 或增加 SLO |
| **Plan Regression** | APRC FORCE_LAST_GOOD_PLAN 命中, 查询执行时间 step-up | 强制好计划 / 重新编译 / 更新统计信息 |
| **Slow / Failed Queries** | Top wait queries, failed query patterns | 优化具体查询 |
| **Compilation Storm** | High failed/successful compilation CPU | 启用 plan cache / 减少 ad-hoc query |
| **Out of Disk** | Drive/quota/tempdb/file 任一满 | 增加 SLO 或清理空间 |
| **XStore Error** | XStore IO error 频繁 | 平台 storage 层问题, escalate |
| **Worker Thread Exhaustion** | Worker pool 满, blocking chain 深 | 减少并发 / 增加 SLO |
| **Database Corruption** | Corruption detected in errorlog | DBCC CHECKDB + restore from backup |
| **AKV Error** | TDE/AKV unavailability | 检查 Key Vault 权限和网络 |
| **Non-yielding Scheduler** | SOS_SCHEDULER_YIELD + non-yielding XEvent | SQL 内部 hang, escalate + 收集 dump |
| **LSASS Telemetry Hole - Residual** | LSASS CPU 自发飙升, 无 MonLogin trigger | 平台 LSASS issue, escalate |
| **LSASS Telemetry Hole - Direct** | MonLogin spike ≥ 3× baseline → LSASS 跟进 | 客户登录风暴 / 连接池问题 |

### Escalation 判断

| Condition | Action |
|-----------|--------|
| CPU/memory/disk 已自愈 | 提供 RCA, 不 escalate |
| QDS readonly 反复发生 | Escalate 到 QDS 团队 |
| Plan regression 影响范围大 (>10 queries) | Escalate 到 QO 团队 |
| Database corruption | Escalate 到 Storage Engine 团队 + 启动 restore |
| Non-yielding scheduler | Escalate 到 SQLOS 团队 + 收集 dump |
| LSASS Residual | Escalate 到 Identity / Platform 团队 |
| Worker thread exhaustion 反复 | 建议升级 SLO 或调整应用 |

## Route → Steps Mapping

| Route | Steps | KQL 数 (livesite) | 说明 |
|-------|-------|-------------------|------|
| cpu | 0.1, 0.2, 0.3, 1, cpu skill | 8 | 最常见 |
| memory | 0.1, 0.2, 0.3, 1, memory skill | 5 | OOM/overbooking/buffer pool |
| out-of-disk | 0.1, 0.2, 0.3, 1, out-of-disk skill | 8 | 5 类磁盘问题 |
| query-store | 0.1, 0.2, 0.3, 1, query-store skill | 13 | QDS readonly RCA |
| aprc | 0.1, 0.2, 0.3, 1, aprc skill | 4 (共用 QDS) | 单查询 plan regression |
| queries | 0.1, 0.2, 0.3, 1, queries skill | 22 | Top queries + specific query |
| compilation | 0.1, 0.2, 0.3, 1, compilation skill | 7 | 编译问题 |
| miscellaneous | 0.1, 0.2, 0.3, 1, misc skill | 11 | Worker/corruption/AKV/etc |
| sqlos | 0.1, 0.2, 0.3, 1, sqlos refs | 2 | Non-yielding scheduler |
| blocking | 0.1, 0.2, 0.3, 1, blocking skill | 9 | Blocking/deadlock |
| lsass | 0.1, 0.2, 0.3, 1, lsass refs | 0 (流程在 references) | LSASS Two-Problem 分析 |
| **default (no keywords)** | 0.1, 0.2, 0.3, 1, **5 skills 并行**: cpu + memory + out-of-disk + query-store + miscellaneous | 8+5+8+13+11=45 | 综合扫描 |

## Skill 交叉引用

| Skill | 内部调用 | 被调用方 |
|---|---|---|
| cpu | compilation (if compile CPU high), queries (if specific query) | triage |
| memory | (独立, 但可能触发 QDS readonly Error 65536/131072) | triage |
| out-of-disk | (独立, 但可能触发 QDS readonly Error 262144) | triage |
| query-store | aprc (if plan regression detected), memory (if Error 65536/131072), out-of-disk (if Error 262144) | triage |
| aprc | queries (specific query 详细分析) | triage, query-store |
| queries | aprc (if plan regression), compilation (if compile CPU high) | triage, cpu, aprc |
| compilation | queries (top failed compile query) | triage, cpu |
| miscellaneous | sqlos (if non-yielding), failover skill (if SQL restart) | triage |
| sqlos | (独立, 但可能 dump → 详细 dump 分析) | triage, miscellaneous |
| blocking | queries (top blocking query) | triage |
| lsass | (独立, 但和 Connectivity 的 login-failure 互补) | triage |

## 参考来源

- **Performance.agent.md** (`SQLLivesiteAgents/.github/agents/Performance.agent.md`) — 14 skills 总览 + skill selection logic
- **triage SKILL.md** (`Performance/triage/SKILL.md`) — Workflow + 关键词决策矩阵 + 执行顺序
- **appnameandnodeinfo SKILL.md** (`Common/appnameandnodeinfo/SKILL.md`) — Phase 0 Step 0.3 必备变量
