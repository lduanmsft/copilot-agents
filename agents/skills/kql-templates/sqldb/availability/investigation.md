---
name: SQLDB Availability Investigation
description: Diagnoses Azure SQL Database high availability issues including failovers, quorum loss, replica problems, error 40613 states, SLO changes, seeding failures, and HADR sync commit waits. Adapted from SQLLivesiteAgents Availability.agent.md.
source: SQLLivesiteAgents/Availability
distilled: 2026-05-01
---

# SQLDB Availability Investigation

> 架构: Primary ↔ Secondary replicas on Service Fabric (WinFab)
>
> - **GP (General Purpose)**: 1 primary + 0 remote replicas (local SSD for tempdb)
> - **GP with ZR**: 1 primary + 2 zone-redundant replicas
> - **BC (Business Critical)**: 1 primary + 3 local replicas (AlwaysOn AG)

## Required Inputs

| Parameter | Source | Example |
|-----------|--------|---------|
| LogicalServerName | User/ICM | `my-server` |
| LogicalDatabaseName | User/ICM | `my-db` |
| StartTime | User/ICM | `2026-01-01 02:00:00` (UTC) |
| EndTime | User/ICM | `2026-01-01 03:00:00` (UTC) |

**Tips**:
- 时间窗口建议在客户报告的时间上下各扩展 1 小时
- 如果有 ICM: 优先用 `ObservedStartTime` → `ImpactStartTime` → `CreatedDate`; EndTime 用 `MitigateTime` → 当前时间 (cap at StartTime + 7h)

## Phase 0: Prerequisites

### Step 0.1: Kusto Cluster 解析

- **Skill**: `execute-kusto-query` (Common/execute-kusto-query/SKILL.md)
- DNS 解析 `{LogicalServerName}.database.windows.net` → 得到 region
- 查 `KustoConnectionConfiguration.xml` → Kusto cluster URI + database
- **永远不要猜测 Kusto cluster URI**

### Step 0.2: 获取数据库环境信息

- **Skill**: `get-db-info` (Common/get-db-info/SKILL.md)
- 查询获取: AppName, ClusterName, NodeName, physical_database_id, fabric_partition_id, SLO, deployment_type, zone_resilient
- 如果时间窗口内有 SLO 变更或 failover → 可能有多个配置，需为每个配置分别分析

## Phase 1: Triage — 确定问题类型

- **Skill**: `triage` (availability/triage/SKILL.md)

根据用户描述 / ICM 关键字选择调查路径:

| Keywords | Route | Note |
|----------|-------|------|
| failover, replica transition, role change, 40613 | `failover` | 最常见 |
| quorum, quorum loss, insufficient replicas | `quorum-loss` | |
| node down, node failure, bugcheck, deactivation | `node-health` | |
| 40613 state 126, database in transition | `error-40613-state-126` | |
| 40613 state 127, warmup, cannot open database | `error-40613-state-127` | |
| 40613 state 129 | `error-40613-state-129` | |
| HADR_SYNC_COMMIT, sync commit wait, log send queue | `high-sync-commit-wait` | **BC/Premium only** |
| seeding, seed failure, TRDB0058, VDI | `seeding-rca` | |
| update slo, slo change, scaling, tier change | `update-slo` | |
| login failure, login success rate, CRGW0001 | `login-failure-triage` | |
| long reconfig, stuck reconfiguration | `long-reconfig` | 通常由 failover 内部调用 |
| *(default)* | `failover` | |

**可多选**: 多个关键字同时匹配时选择多个 skill (如 quorum-loss + node-health)。

## Phase 2: Diagnostic Skills

### Route: failover

- **Skill**: `availability/failover/SKILL.md`
- **KQL**: `availability/failover/kql-livesite.yaml` (25 queries)

**Workflow**:
1. Validate inputs, calculate duration
2. Understand XEvents (hadr_fabric_api_replicator_begin/end_change_role)
3. Check SqlFailovers for completed failover events
4. Check LoginOutages for impact assessment
5. Check MonLogin for login failure timeline
6. Analyze MonSQLSystemHealth for SQL process lifecycle
7. Check WinFabLogs for reconfiguration events
8. Analyze role change XEvents timeline
9. Check image download / CodePackage activation delays
10. Check write status problems
11. Check error log gaps
12. Build per-node timeline

**References**: knowledge.md (XEvent definitions), principles.md (debug approach), output.md (report template)

### Route: quorum-loss

- **Skill**: `availability/quorum-loss/SKILL.md`
- **KQL**: `availability/quorum-loss/kql-livesite.yaml` (20 queries)

**Workflow**:
1. Check Service Fabric partition health
2. Identify quorum loss window
3. Analyze replica state changes
4. Check node failures during quorum loss
5. Investigate blocked replica rebuilds
6. Assess reconfiguration blocked scenarios

**Cross-ref**: → `node-health` (if node failure caused quorum loss)

### Route: node-health

- **Skill**: `availability/node-health/SKILL.md`
- **KQL**: `availability/node-health/kql-livesite.yaml` (8 queries)

**8 mandatory queries**:
1. NH100: Locate database node(s)
2. NH200: SF node state changes
3. NH210: Node health issues
4. NH300: MonSQLInfraHealthEvents (extended: -12h to +24h)
5. NH400: Bugcheck events
6. NH500: Node up/down in WinFabLogs
7. NH600: Node repair tasks
8. NH700: RestartCodePackage actions

### Route: error-40613-state-126

- **Skill**: `availability/error-40613/error-40613-state-126-SKILL.md`
- **KQL**: `availability/error-40613/kql-livesite.yaml` (STATE126-*)

**Decision tree**:
- Duration < 30s → Expected transient (normal failover)
- Duration 30s-2min → Investigate role change delays
- Duration > 2min → 🚩 Stuck transition → escalate to failover skill

**Cross-ref**: → `failover` (if stuck), → `error-40613-state-127` (if recovery stuck after transition)

### Route: error-40613-state-127

- **Skill**: `availability/error-40613/error-40613-state-127-SKILL.md`
- **KQL**: `availability/error-40613/kql-livesite.yaml` (STATE127-*)

**Focus**: Database warmup/recovery after failover. Check MonSQLSystemHealth for recovery progress messages.

### Route: error-40613-state-129

- **Skill**: `availability/error-40613/error-40613-state-129-SKILL.md`
- **KQL**: `availability/error-40613/kql-livesite.yaml` (STATE129-*)

**Focus**: HADR subsystem unavailable.

### Route: high-sync-commit-wait

- **Skill**: `availability/high-sync-commit-wait/SKILL.md`
- **KQL**: `availability/high-sync-commit-wait/kql-livesite.yaml` (11 queries)
- **Condition**: BC/Premium only — skip for GP/Hyperscale

**Workflow** (10 steps):
1. SLO pre-check (skip if not BC/Premium)
2. HSC050: HADR_SYNC_COMMIT wait baseline
3. HSC100-180: Commit manager analysis, log send queue, redo queue, XEvent correlation

### Route: seeding-rca

- **Skill**: `availability/seeding-rca/SKILL.md`
- **KQL**: `availability/seeding-rca/kql-livesite.yaml` (11 queries)

**Focus**: Geo-replication seeding failures (VDI, AKV/TDE, certificate issues).

### Route: long-reconfig

- **Skill**: `availability/long-reconfig/SKILL.md`
- **KQL**: `availability/long-reconfig/kql-livesite.yaml` (21 queries)

**Focus**: Stuck or prolonged Service Fabric reconfigurations (>2 min). Usually called from within failover investigation.

### Route: update-slo

- **Skill**: `availability/update-slo/SKILL.md`
- **KQL**: `availability/update-slo/kql-livesite.yaml` (10 queries)

**Focus**: SLO change FSM (Finite State Machine) stuck or failed. Check MonManagement for UpdateSloTarget workflow stages.

### Route: login-failure-triage

- **Skill**: `availability/login-failure/SKILL.md`
- **KQL**: `availability/login-failure/kql-livesite.yaml` (6 queries)

**Focus**: Login failure as symptom of availability issue (different from Connectivity's login-failure which focuses on Gateway/network layer).

## Phase 3: ICM Correlation (Optional)

> 运行时询问: "是否需要搜索相关 ICM incidents？"
> 需要 ICM MCP 工具 (后续会添加)

### Step 3.1: Similar Incidents

- **Skill**: `similar-incidents` (Common/similar-incidents/SKILL.md)
- 基于 ML 相似度搜索 ICM 中的类似 incident
- 提供历史上下文和已知解决方案

### Step 3.2: Correlated Incidents

- **Skill**: `correlated-incidents` (Common/correlated-incidents/SKILL.md)
- 搜索 ICM DataWarehouse 中提到相同 server/database/AppName 的 incident
- 判断是否有并发的关联事件

## Phase 4: RCA 输出

### 根因分类

| Category | Indicators | Customer Message |
|----------|-----------|-----------------|
| **Planned Failover** | SqlFailovers 有记录, ReconfigurationType=Planned | 平台计划性维护导致短暂中断, 建议实现重试逻辑 |
| **Unplanned Failover** | SqlFailovers ReconfigurationType=Unplanned, node failure | 节点异常触发自动故障转移 |
| **Quorum Loss** | SF partition quorum loss, multiple replica failures | 多副本同时失败导致不可用 |
| **Node Health Issue** | Bugcheck, deactivation, repair task | 底层基础设施问题 |
| **SLO Change Stuck** | UpdateSloTarget FSM stuck | SLO 变更流程卡住 |
| **Seeding Failure** | VDI error, AKV/TDE issue | Geo-replication 种子失败 |
| **Long Reconfiguration** | Reconfig duration > 2min | Service Fabric 重配置延迟 |
| **HADR Sync Commit** | High HADR_SYNC_COMMIT wait (BC only) | 同步提交等待导致性能降级或不可用 |
| **Login Failure (Availability)** | 40613 state 126/127/129 | 数据库在转换/恢复/不可用状态 |

### Escalation 判断

| Condition | Action |
|-----------|--------|
| Failover 已自愈, duration < 30s | 提供 RCA, 不 escalate |
| Failover duration > 2min 或未自愈 | Escalate 到 Availability 工程团队 |
| Quorum loss | Escalate + 检查 node health |
| SLO change stuck > 1h | Escalate 到 Management Service 团队 |
| Seeding 反复失败 | Escalate 到 GeoDR 团队 |
| Node bugcheck/repair | Escalate 到 Infrastructure 团队 |

## Route → Steps Mapping

| Route | Steps | Description |
|-------|-------|-------------|
| failover | 0.1, 0.2, 1, failover skill (12 steps) | 完整 failover 调查 |
| quorum-loss | 0.1, 0.2, 1, quorum-loss skill + node-health | Quorum loss + 节点检查 |
| node-health | 0.1, 0.2, 1, node-health skill (8 queries) | 节点基础设施检查 |
| error-40613-state-126 | 0.1, 0.2, 1, state-126 skill (5 steps) | DB transition 诊断 |
| error-40613-state-127 | 0.1, 0.2, 1, state-127 skill | DB warmup 诊断 |
| error-40613-state-129 | 0.1, 0.2, 1, state-129 skill | HADR subsystem 诊断 |
| high-sync-commit-wait | 0.1, 0.2, 1, HSC skill (10 steps) | BC/Premium only |
| seeding-rca | 0.1, 0.2, 1, seeding skill | Geo-replication 种子 RCA |
| long-reconfig | 0.1, 0.2, 1, long-reconfig skill | 长重配置分析 |
| update-slo | 0.1, 0.2, 1, update-slo skill | SLO 变更 FSM 分析 |
| login-failure-triage | 0.1, 0.2, 1, login-failure skill | 登录失败 (可用性层面) |

## Skill 交叉引用

| Skill | 内部调用 | 被调用方 |
|---|---|---|
| failover | node-health, long-reconfig | triage, Connectivity Step 12 |
| quorum-loss | node-health | triage |
| node-health | *(独立)* | failover, quorum-loss, Connectivity Step 9 |
| error-40613-state-126 | failover (>2min), state-127 (recovery stuck) | triage |
| error-40613-state-127 | *(独立)* | state-126 |
| long-reconfig | failover | failover (内部子流程) |
| login-failure-triage | *(独立)* | triage |
