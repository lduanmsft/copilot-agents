---
name: SQLDB Connectivity Investigation (CSS)
description: CSS case investigation skill for Azure SQL DB connectivity issues. Adapted from SQLLivesiteAgents Connectivity.agent.md — removed mitigation ops, added RCA output templates.
source: SQLLivesiteAgents/Connectivity (CSS adaptation)
distilled: 2026-05-01
---

# SQLDB Connectivity Investigation (CSS 版)

> 与工程 DRI 版 (investigation.md) 的区别:
> 1. 去掉 mitigation 操作 (kill GW, restart XdbHost, CAB 等)
> 2. 输出为 RCA 摘要 + escalation 移交包
> 3. 只保留 login-failure + session-disconnect 两条路径 (ICM alert 路径不需要)
> 4. 不保存 report 到 ADO repo

## 1. 输入参数

| Parameter | Required | Example |
|-----------|----------|---------|
| LogicalServerName | Yes | `my-server` (不含 .database.windows.net) |
| LogicalDatabaseName | Yes | `my-db` |
| StartTime | Yes | `2026-01-01 02:00:00` (UTC) |
| EndTime | Yes | `2026-01-01 03:00:00` (UTC) |
| ErrorCode | Optional | `40613` (加速 triage) |
| ErrorState | Optional | `22` |

**Tips**:
- 时间窗口建议在客户报告的时间上下各扩展 1 小时
- 如果客户只说 "intermittent", 取最近一次复现的 24h 窗口

## 2. Phase 0: Kusto 集群解析 + 数据库环境

### Step 0.1: DNS → Region → Kusto Cluster

`nslookup {LogicalServerName}.database.windows.net` → 得到 region → 查 `KustoConnectionConfiguration.xml` 得到 Kusto cluster URI + database.

**永远不要猜测 Kusto cluster URI.** 不同 region 对应不同集群.

### Step 0.2: 获取数据库环境信息

查询获取: AppName, ClusterName(TR), NodeName(DB node), deployment_type, physical_database_id, fabric_partition_id.

如果时间窗口内数据库有过 SLO 变更或 failover, 可能有多个配置, 需要为每个配置分别分析.

## 3. Phase 1: Triage

根据客户描述 + error code 确定调查路径:

| Keywords | Route |
|----------|-------|
| login failure, cannot connect, authentication, 18456, 40613 | **login-failure** |
| session disconnect, connection dropped, timeout, 17900 | **session-disconnect** |
| intermittent, connectivity issue | **login-failure** (default) |

## 4. Phase 2: Login Failure Investigation

### Step 2.1: Check Outage Records

- **KQL**: `connectivity-base/` → `LS-CONN-BASE-01` (LoginOutages)
- 有 outage record → 问题已被平台识别, 提取 OutageReasonLevel1/2/3
- 没有 → 继续调查

### Step 2.2: Determine Login Target

- **KQL**: `connectivity-base/` → `LS-CONN-BASE-04` (MonLogin)
- 确定 TargetTRRing + TargetDBNode
- 多个不同 TargetTRRing → 发生了 failover 或 SLO 变更

### Step 2.3: Determine Connectivity Ring

- **KQL**: `connectivity-base/` → `LS-CONN-BASE-03` (MonLogin)
- 通常 2 个 CR; >2 可能是 slice migration
- 比较 TotalLogins vs LoginWithError, 差异 >2 倍 → 异常

### Step 2.4: Connection Type Analysis

- **KQL**: `connectivity-base/` → `LS-CONN-BASE-07` (MonLogin)
- `proxy_override` → Connection Policy; `result` → 实际连接类型
- `is_vnet_private_access_address=true` → Private Endpoint
- Policy=Redirect 但实际 Proxy → 驱动不支持 或 NVA/Zscaler

### Step 2.5: Determine Prevailing Error

- **KQL**: `connectivity-base/` → `LS-CONN-BASE-05` (MonLogin)
- 区分 `is_user_error=true` (客户侧) vs `false` (平台侧)
- `avg_total_time_ms > 4000ms` → 某环节有 delay
- **Error 33155**: MUST 查 `fedauth_token_wait_time_ms` — 如果 ≈ total_time_ms → 客户端 token 获取慢

**分支**:
- 全是 user error (EXCEPT 33155) → Phase 5: 客户侧问题
- Error 33155/1 → Step 2.7 (需要 fedauth timing)
- Error 40613/22 → Step 2.6 + Step 2.8
- Error 17900/25 → Phase 3 Session Disconnect
- System error → Step 2.6

### Step 2.6: Narrow Down by Node

- **KQL**: `connectivity-base/` → `LS-CONN-BASE-06` (MonLogin)
- 错误集中单个 node → node-specific; 分散多个 → infrastructure-level

### Step 2.7: Error-Specific Analysis

根据 top error/state, 查 `connectivity-errors/error-{code}-state-{state}/`:

| Error | State | 含义 | Action |
|-------|-------|------|--------|
| 40613 | 10 | CantFindRequestedInstance | 5 KQL (verify node, GW switch, SF notification) |
| 40613 | 22 | DueToProxyConnextThrottle | 检查 SNAT + 网络分析 |
| 40613 | 84 | Proxy connect timeout | 6 KQL chain + 网络分析 |
| 40613 | 81 | IPv6 prefix mismatch | 3 KQL |
| 40613 | 12/13/44/126 | XdbHost restart cascade | → Step 2.10 |
| 18456 | multi | Login failed for user | 6 KQL (state-specific) |
| 18456 | 113 | DosGuard | 6 KQL |
| 33155 | 1 | **AAD Login Timeout** | 查 fedauth_* 列, TSG: ENTRA0010 |
| 26078 | 15 | XdbHost queue timeout | → xdbhost-metric-check |
| 40532 | 150 | VNET firewall rejected | 3 KQL |
| 47073 | 172 | DPNA | 3 KQL |
| 17900 | 25 | TDS protocol error | 1 KQL (connection trace) |

### Step 2.8: CR Health Check (简化版)

- **KQL**: `connectivity-base/connectivity-ring-health/` → GW1100, GW1110, GW1112, GW1122
- SNAT events → 网络层问题
- GW restart → 与客户报告的时间对比
- Deployment → 版本更新导致 transient failure

### Step 2.9: Failover / Availability Cross-Check

- 查 `sqldb/availability/` 下的 failover KQL
- 有 failover → 登录失败是 secondary symptom, RCA 应指向 failover

### Step 2.10: XdbHost Restart Analysis (条件执行)

**条件**: 发现 40613 state 10/12/13/44/126 error cascade

- **KQL**: `connectivity-scenarios/xdbhost-restart/` → XR100-XR700
- XR100: 确认 process_id 变化
- XR200: 分类触发原因
- XR300: 自动化 KillProcess 检查
- XR400/410: user errors vs restart errors 时间线
- XR600: 登录量 (>2500/min = 异常高)
- XR700: 自愈验证

**Key**: restart 前 user errors >> system errors → 客户认证错误洪水触发了自动化

### Step 2.11: App Health

- **KQL**: `connectivity-utilities/app-health/` → AH305(先), AH305-pre, AH100, AH200
- AH305: 8 类系统健康模式 (I/O_slow, Memory_pressure, Deadlock, StackDump...)
- AH305-pre: 与事件前 2h 对比 → chronic vs acute

## 5. Phase 3: Session Disconnect Investigation

### Step 3.1: Disconnect Events Summary

- **KQL**: `connectivity-scenarios/session-disconnect/` → `LS-SD-01`
- Top error/state 组合; 17900/25 最多 → TDS protocol error

### Step 3.2: Connection Trace

- **KQL**: `connectivity-scenarios/session-disconnect/` → `LS-SD-02`
- 追踪 top 3 connection_peer_id end-to-end
- 看 kill_reason, extra_info (Error_SniRead), is_mars

### Step 3.3: 建议客户操作 (MUST output)

- 建议抓取 client-side networking trace + 联系 Azure Networking CSS
- 确认 end-to-end 网络路径 (NVA, Zscaler, SSL inspection)
- Error 17900/25 → TSG: https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/connection/tds-protocol-error

## 6. Phase 5: RCA 输出

### 根因分类

| Category | Indicators | Customer Message |
|----------|-----------|-----------------|
| **Platform — Failover/Reconfig** | LoginOutages 有记录, failover events, 40613 state 10/12/13/44/126 | 平台重配置导致短暂中断, 建议实现重试逻辑 |
| **Platform — Gateway/Network** | SNAT, 40613/22, 40613/84, GW restart, deployment | Gateway 层问题, 已自愈或需 escalate |
| **Platform — DB Node** | sqlservr crash (AH100), I/O slow (AH305), memory pressure | 节点异常导致连接问题 |
| **Customer — Authentication** | is_user_error=true, 18456 states | 客户端认证问题, 检查用户名/密码/AAD/防火墙 |
| **Customer — Connection Config** | Proxy/Redirect mismatch, outdated driver, PE misconfiguration | 连接配置问题 |
| **Undetermined — Network Path** | Session disconnect, 17900/25, 无平台异常 | 建议 client trace + Azure Networking 协助 |

### Escalation 判断

| Condition | Action |
|-----------|--------|
| Platform issue, 未自愈 | Escalate 到对应工程团队 + 附调查数据 |
| Platform issue, 已自愈 | 提供 RCA, 不 escalate |
| Customer issue | 提供建议, 不 escalate |
| Network path issue | 建议联系 Azure Networking CSS + 提供 EagleEye 链接 |

## KQL 引用汇总

| Directory | Count | Used In |
|-----------|-------|---------|
| `connectivity-base/` | 8 KQL | Steps 2.1-2.6 |
| `connectivity-base/connectivity-ring-health/` | 12 KQL | Step 2.8 (4 常用) |
| `connectivity-errors/` (12 error dirs) | 33 KQL | Step 2.7 |
| `connectivity-scenarios/xdbhost-restart/` | 7 KQL | Step 2.10 |
| `connectivity-scenarios/session-disconnect/` | 2 KQL | Phase 3 |
| `connectivity-utilities/app-health/` | 6 KQL | Step 2.11 |
| `connectivity-utilities/xdbhost-metric-check/` | 6 KQL | Error 26078/40613-13/15 |
| `connectivity-utilities/` (others) | 4 KQL | On-demand |
| **Total CSS-used** | **~78** | |
