# DB KQL Investigation Skill

This skill defines how to find, review, execute, and analyze KQL for **Azure SQL Database** investigations.

## Standard Interaction Flow

When the user asks to investigate a SQL DB issue with Kusto/KQL, follow this standard flow:

```
User: "Help me investigate {problem}"
  ↓
Step 1: Gather parameters
  → ServerName, DatabaseName, Region, TimeRange
  → If region is unknown, discover it from telemetry
  ↓
Step 2: Issue classification
  → If user already specified (e.g. "failover", "high CPU") → route directly
  → Otherwise ask:
    A. Performance (CPU/memory/blocking/queries/QDS/compilation/disk)
    B. Availability (failover/quorum loss/error 40613/SLO change/seeding)
    C. Connectivity (login failure/AAD/gateway)
    D. GeoDR / FOG
    E. Backup & Restore
    F. General
  ↓
huoStep 3: Find KQL + search TSG (parallel)
  → Line 1: Local YAML → P1(livesite/sqldri) → P2(distilled) → get executable KQL
  → Line 2: msdata TSG repo (per topic) + CSS Wiki → get investigation guide / latest KQL
  → Merge: local KQL as primary, TSG supplements investigation context
  ↓
Step 4: Present query for review ⚠️ never execute without confirmation
  → Show complete KQL with parameters filled in
  ↓
Step 5: Execute after confirmation
  ↓
Step 6: Handle errors
  ↓
Step 7: Analyze results
  → Conclusion + Rationale + Anomalies + Trends + Next Steps
```

### Core rules
- **Always show the KQL before executing it.**
- **Never execute without explicit user confirmation.**
- **If the first query fails, fix or narrow it, then re-present the updated query.**
- **For the same investigation, follow-on queries are allowed after the user has approved the workflow direction.**

## Step 1: Gather Required Parameters
Always collect these parameters first:

1. **ServerName** — logical SQL server name, e.g. `myserver01`
2. **DatabaseName** — database name, e.g. `appdb-prod`
3. **Region** — Azure region, e.g. `eastus2`, `westeurope`
4. **TimeRange** — e.g. `1h`, `24h`, `7d`, or a specific datetime range

If the user does not know the region, discover it first using SQL DB metadata on the global / discovery path.

Example discovery query:
```kql
MonAnalyticsDBSnapshot
| where logical_server_name =~ "{ServerName}"
| where logical_database_name =~ "{DatabaseName}"
| summarize arg_max(TIMESTAMP, *)
| project logical_server_name, logical_database_name, region_name, state,
    edition, service_level_objective, zone_resilient,
    sql_instance_name, tenant_ring_name, fabric_partition_id,
    physical_database_id, sql_database_id, logical_database_id,
    failover_group_id, logical_resource_pool_id
```

**从结果中提取并保存（后续步骤会用到）：**
- `sql_instance_name` → **AppName**（用于 KQL filter，如 `AppName =~ '{AppName}'`）
- `tenant_ring_name` → **ClusterName**（用于 WinFabLogs 等表的 filter）
- `edition` + `service_level_objective` → 判断 Singleton/Elastic Pool/Hyperscale/Serverless，影响调查路径
- `zone_resilient` → 影响 failover 调查（GP ZR vs non-ZR）
- `fabric_partition_id` → 用于 availability 子目录的 WinFabLogs/MonFabricApi filter
- `physical_database_id` → 用于 MonFabricApi/MonSQLSystemHealth filter
- `sql_database_id` → 用于 MonSQLSystemHealth recovery message filter（`database ID {N}`）

If `DatabaseName` is unknown but the user knows the server, list databases first:
```kql
MonAnalyticsDBSnapshot
| where logical_server_name =~ "{ServerName}"
| summarize arg_max(TIMESTAMP, *) by logical_database_name
| project logical_database_name, state, edition, service_level_objective, region_name
| order by logical_database_name asc
```

## Step 2: Issue Classification

**如果用户已明确说了问题类型**（如 "failover", "high CPU", "login failure"）→ 直接路由到对应子目录。

**否则问用户选择：**
- **A. Performance** — CPU/memory/blocking/queries/QDS/compilation/disk
- **B. Availability** — failover/quorum loss/error 40613/SLO change/seeding/long reconfig
- **C. Connectivity** — login failure/AAD/gateway
- **D. GeoDR / FOG** — failover group/seeding/geo-replication
- **E. Backup & Restore** — backup/restore/PITR
- **F. General** — management operations/security/other

→ 选择后路由到对应子目录搜 KQL 模板（见 Step 3）

## Step 2a: Phase 0 Prerequisites (MANDATORY — 在 A/B/C 之前)

**⚠️ 不论后续选 A、B 还是 C，都必须先执行 Phase 0 三步获取 KQL 必备变量。**

> 原因: SQLDB 的 KQL 模板（尤其 Performance）严重依赖 `{AppNamesNodeNamesWithOriginalEventTimeRange}`、`{KustoClusterUri}`、`{SumCpuMillisecondOfAllApp}` 等变量。没有这些变量, KQL 无法填充也无法执行。
>
> 如果跳过 Phase 0 直接选 C, 后续 KQL 会因缺变量而失败。

### Phase 0.1: execute-kusto-query (识别 Kusto cluster)

- **Skill**: `Common/execute-kusto-query/SKILL.md` (在 SQLLivesiteAgents repo)
- **动作**: DNS 解析 `{LogicalServerName}.database.windows.net` → 找 region → 查 KustoConnectionConfiguration.xml → 得到 cluster URI 和 database
- **输出**: `{KustoClusterUri}`, `{KustoDatabase}`
- **永远不要猜或硬编码 cluster URI**

### Phase 0.2: get-db-info (获取数据库环境)

- **Skill**: `Common/get-db-info/SKILL.md` 或直接跑 db-kql-investigation.md Step 1 的 MonAnalyticsDBSnapshot 查询
- **输出**: `{AppName}` (= sql_instance_name), `{ClusterName}` (= tenant_ring_name), `{edition}`, `{service_level_objective}`, `{zone_resilient}`, `{fabric_partition_id}`, `{physical_database_id}`, `{sql_database_id}`, `{logical_resource_pool_id}`

### Phase 0.3: appnameandnodeinfo (Performance 必备 — 6 tasks)

- **Skill**: `performance/triage/appnameandnodeinfo-SKILL.md`
- **必须执行 6 个 task** (Performance 类别强制, Availability/Connectivity 可选):
  - Task 1: 复用 Phase 0.1 输出
  - Task 2: AppNames + NodeNames + 时间范围 filter strings (主输出)
  - Task 3: 7-day 历史 filter
  - Task 4: SumCpuMillisecondOfAllApp (CPU 容量)
  - Task 5: ActualSumCpuMillisecondOfAllApp (CPU 实际消耗)
  - Task 6: edition + isInElasticPool + service_level_objective
- **输出变量** (10+ 个, 后续所有 Performance KQL 必备):
  - `{AppNamesOnly}`
  - `{AppNamesNodeNamesWithOriginalEventTimeRange}` ← 最关键
  - `{AppNamesNodeNamesWithPreciseTimeRange}`
  - `{ApplicationNamesNodeNamesWithOriginalEventTimeRange}`
  - `{NodeNamesWithOriginalEventTimeRange}`
  - `{NodeNamesWithPreciseTimeRange}`
  - `{AppNamesNodeNamesWith7DayOriginalEventTimeRange}`
  - `{SumCpuMillisecondOfAllApp}`
  - `{ActualSumCpuMillisecondOfAllApp}`
  - `{isInElasticPool}`
  - `{edition}`
  - `{service_level_objective}`
- **🚩 Managed Instance 检查**: Task 2 如果 `IsManagedInstance == true` → 立即终止, 提示用户使用 MI 流程

### 类别 → Phase 0 强制范围

| 选择的类别 (Step 2) | Phase 0.1 | Phase 0.2 | Phase 0.3 |
|--------------------|-----------|-----------|-----------|
| **A. Performance** | ✅ 必须 | ✅ 必须 | ✅ 必须 (KQL 全部依赖) |
| **B. Availability** | ✅ 必须 | ✅ 必须 | ⚠️ 推荐 (部分 KQL 依赖, e.g. node-health) |
| **C. Connectivity** | ✅ 必须 | ✅ 必须 | ⚠️ 部分场景需要 (gateway-node-low-login, xdbhost-*) |
| **D. GeoDR** | ✅ 必须 | ✅ 必须 | ❌ 不需要 |
| **E. Backup & Restore** | ✅ 必须 | ✅ 必须 | ❌ 不需要 |
| **F. General** | ✅ 必须 | ⚠️ 视情况 | ❌ 不需要 |

### Phase 0 完成后, 才进入 Step 2b

## Step 2b: 是否执行自动调查流程 (Optional)

> **前置**: Step 2a Phase 0 已完成, 变量已就绪。

**在选择问题类型后，如果该类别有 `auto_investigation.md`，询问用户：**

```
检测到 {category} 类别有自动调查模板。

请选择:
A. 🤖 自动调查 — 自动 triage + 执行诊断流程 + RCA 输出
B. 📂 手动选择子类别 — 直接选择要调查的子问题 (跳过 triage, 直接执行选定的 SKILL.md)
C. ⏭️ 跳过 — 继续手动搜 KQL + TSG (Step 3) — Phase 0 变量已可用, 可直接填充 KQL
```

**子类别列表 (选 B 时展示，含执行的 SKILL 路径):**

**Availability** 子类别:

| # | 子类别 | 执行的 Skill | KQL 数 |
|---|--------|-------------|--------|
| 1 | failover | `availability/failover/SKILL.md` | 25 |
| 2 | quorum-loss | `availability/quorum-loss/SKILL.md` | 20 |
| 3 | node-health | `availability/node-health/SKILL.md` | 8 |
| 4 | error-40613 | `availability/error-40613/SKILL.md` (含 state-126/127/129) | 20 |
| 5 | high-sync-commit-wait | `availability/high-sync-commit-wait/SKILL.md` (BC/Premium only) | 11 |
| 6 | seeding-rca | `availability/seeding-rca/SKILL.md` | 11 |
| 7 | long-reconfig | `availability/long-reconfig/SKILL.md` | 21 |
| 8 | update-slo | `availability/update-slo/SKILL.md` | 10 |
| 9 | login-failure | `availability/login-failure/SKILL.md` | 6 |

**Connectivity** 子类别:

| # | 子类别 | 执行的 Skill | KQL 数 |
|---|--------|-------------|--------|
| 1 | login-failure | `auto_investigation.md` Phase 2 (Steps 2-12) | 118 |
| 2 | session-disconnect | `auto_investigation.md` Branch B (Step 30) | 2 |
| 3 | xdbhost-restart | `auto_investigation.md` Branch A (Step 20) | 7 |
| 4 | gateway-node-low-login | `auto_investigation.md` Branch C (Step 40) | 18 |
| 5 | control-ring-unhealthy | `auto_investigation.md` Branch D (Step 50) | 10 |
| 6 | xdbhost-tcp-rejections | `auto_investigation.md` Branch E (Step 60) | 8 |
| 7 | brain-login-alert | `auto_investigation.md` Branch F (Step 70) | 2 |

**Performance** 子类别:

| # | 子类别 | 执行的 Skill | KQL 数 (livesite) |
|---|--------|-------------|------------------|
| 1 | cpu | `performance/cpu/SKILL.md` | 8 |
| 2 | memory | `performance/memory/SKILL.md` | 5 |
| 3 | out-of-disk | `performance/out-of-disk/SKILL.md` | 8 |
| 4 | query-store | `performance/query-store/SKILL.md` | 13 |
| 5 | aprc | `performance/aprc/SKILL.md` (共用 query-store APRC KQL) | 4 |
| 6 | queries | `performance/queries/SKILL.md` | 22 |
| 7 | compilation | `performance/compilation/SKILL.md` | 7 |
| 8 | miscellaneous | `performance/miscellaneous/SKILL.md` | 11 |
| 9 | sqlos | `performance/sqlos/references/non-yielding.md` (无 SKILL.md) | 2 |
| 10 | blocking | `performance/blocking/SKILL.md` | 9 |
| 11 | lsass | `performance/lsass/SKILL.md` (流程在 references) | 0 |
| **default** | **5 skills 并行**: cpu + memory + out-of-disk + query-store + miscellaneous | 各对应 SKILL.md | 45 (合计) |

> **注意**: 
> - Availability 每个子类别有独立的 SKILL.md；Connectivity 的调查流程内联在 auto_investigation.md 的各 Branch 中。
> - Performance 与 Availability 类似 (子类别独立 SKILL.md), 但 triage 可同时返回**多个** skill (e.g., cpu + memory)。
> - Performance 必须在 Phase 0 执行 `appnameandnodeinfo` skill 获取 `{AppNamesNodeNamesWithOriginalEventTimeRange}` 等变量, 传给所有诊断 skill。

**用户选定后，告知用户**: "将执行 `{skill路径}`，包含 N 步 workflow / N 条 KQL。"

**当前有 auto_investigation.md 的类别：**
- `availability/auto_investigation.md` — 11 routes (路由到独立 SKILL.md)
- `connectivity/auto_investigation.md` — 7 routes (流程内联在各 Branch)
- `performance/auto_investigation.md` — 11 routes (路由到独立 SKILL.md, 可多选并行执行)

**选择 A → 执行 auto_investigation.md 的完整流程 (Phase 0 → Phase 1 Triage → 自动选 Route → 执行对应 SKILL.md/Branch → RCA)**
**选择 B → 展示子类别列表，用户选定后告知将执行哪个 SKILL.md/Branch，跳过 Phase 1 Triage 直接执行 (仍需 Phase 0 Prerequisites)**
**选择 A/B 完成后询问: "自动调查已完成，是否还需要继续搜索 KQL/TSG 补充调查？(Step 3-7)"**
**选择 C → 继续 Step 3 手动调查流程（triage 路由 → 搜目录下 YAML KQL 库 + TSG）。**

## Step 3: Find KQL + Search TSG

### Step 3.0: Triage 路由 — 确定搜索的子目录

**根据用户描述的问题，使用关键词 triage 定位到具体子目录，再搜该目录下的 YAML KQL 库。**

```
用户描述问题 (e.g. "database had an outage", "high CPU", "login failure")
  ↓
Triage 路由（关键词匹配）
  ├── 匹配到关键词 → 定位到具体子目录 (e.g. availability/failover/)
  │   → 搜该子目录下的 kql-livesite.yaml / kql-sqldri-*.yaml
  │
  ├── 无明确关键词但有 ICM → 从 ICM title/description 提取关键词 → 同上
  │
  └── 完全不确定方向 → 使用默认路由:
      - Availability → availability/failover/ (最常见)
      - Performance → 跑 5 维度入口 skill: CPU + memory + out-of-disk + QDS + miscellaneous
      - Connectivity → connectivity/connectivity-scenarios/login-failure/
```

**各类别 triage 路由表：**

**Availability** (关键词 → 子目录，来自 `availability/triage/SKILL.md`):

| 关键词 | 路由到 | yaml 文件 |
|--------|--------|-----------|
| "failover", "role change", "replica transition" | `availability/failover/` | kql-livesite.yaml (25 skills) |
| "quorum", "quorum loss", "insufficient replicas" | `availability/quorum-loss/` | kql-livesite.yaml (20 skills) |
| "40613 state 126", "database in transition" | `availability/error-40613/` | kql-livesite.yaml (20 skills) |
| "40613 state 127", "warmup" | `availability/error-40613/` | kql-livesite.yaml (20 skills) |
| "node down", "bugcheck", "node health" | `availability/node-health/` | kql-livesite.yaml (8 skills) |
| "update slo", "tier change", "scaling" | `availability/update-slo/` | kql-livesite.yaml (10 skills) |
| "seeding", "seed failure", "TRDB0058" | `availability/seeding-rca/` | kql-livesite.yaml (11 skills) |
| "HADR_SYNC_COMMIT", "sync commit wait" | `availability/high-sync-commit-wait/` | kql-livesite.yaml (11 skills, BC only) |
| "long reconfig", "stuck reconfiguration" | `availability/long-reconfig/` | kql-livesite.yaml (21 skills) |
| "login failure" (非 connectivity 类) | `availability/login-failure/` | kql-livesite.yaml (6 skills) |
| (无匹配 — 默认) | `availability/failover/` | kql-livesite.yaml |

**Performance** (关键词 → 子目录，来自 `performance/triage/SKILL.md`):

| 关键词 | 路由到 | 入口 skill |
|--------|--------|-----------|
| "high CPU", "CPU spike" | `performance/cpu/` | LS-CPU-01 |
| "blocking", "deadlock" | `performance/blocking/` | LS-BLOCKING-01 |
| "memory", "OOM", "buffer pool" | `performance/memory/` | LS-MEMORY-01 |
| "slow query", "query performance" | `performance/queries/` | LS-QUERIES-01 |
| "QDS", "Query Store", "readonly" | `performance/query-store/` | LS-QDS-01 |
| "compilation", "compile error" | `performance/compilation/` | LS-COMPILE-01 |
| "disk space", "tempdb full", "quota" | `performance/out-of-disk/` | LS-OOD-01 |
| "worker thread", "corruption", "AKV" | `performance/miscellaneous/` | LS-MISC-01 |
| "non-yielding", "scheduler", "dump" | `performance/sqlos/` | LS-SQLOS-01 |
| (无匹配 — 默认) | 跑 5 维度扫描: CPU + memory + out-of-disk + QDS + miscellaneous | 各 *-01 skill |

**Connectivity** (关键词 → 子目录，来自 `connectivity/connectivity-triage/SKILL.md`):

| 关键词 | 路由到 | yaml 位置 |
|--------|--------|-----------|
| "login failure", "connectivity" | `connectivity/connectivity-scenarios/` | login-failure/ |
| "session disconnect", "timeout" | `connectivity/connectivity-scenarios/` | session-disconnect/ |
| "xdbhost restart", "HasXdbHostRestarts" | `connectivity/connectivity-scenarios/` | xdbhost-restart/ |
| "gateway node low login" | `connectivity/connectivity-scenarios/` | gateway-node-low-login-success-rate/ |
| "nodes unhealthy", "control ring" | `connectivity/connectivity-scenarios/` | control-ring-nodes-unhealthy/ |
| "TCP rejections" | `connectivity/connectivity-scenarios/` | xdbhost-high-tcp-rejections/ |
| "BRAIN", "login success rate SLI" | `connectivity/connectivity-scenarios/` | brain-low-login-success-rate/ |
| (无匹配 — 默认) | `connectivity/connectivity-scenarios/` | login-failure/ |

### Step 3.1: 搜定位到的子目录下的 YAML KQL 库 + 并行搜 TSG

**Triage 确定子目录后，并行执行两条线路：**

#### 线路 1: 搜本地 YAML Templates（得到可执行 KQL）

在 triage 定位到的子目录下搜 KQL 模板：

```text
~/.copilot/agents/skills/kql-templates/sqldb/
├── performance/                          ← Performance (9 子目录, 200+ skills)
│   ├── cpu/                              (kql-livesite, kql-sqldri, kql-distilled, kql-tsg, investigation)
│   ├── blocking/                         (同上)
│   ├── memory/                           ...
│   ├── queries/                          ...
│   ├── query-store/                      ...
│   ├── compilation/                      ...
│   ├── out-of-disk/                      ...
│   ├── miscellaneous/                    ...
│   └── sqlos/                            ...
├── availability/                         ← Availability (10 子目录, 132 livesite skills)
│   ├── auto_investigation.md             ← 🤖 自动调查入口 (11 routes)
│   ├── triage/                           (SKILL.md — 路由层)
│   ├── failover/                         (SKILL.md + kql-livesite.yaml + references/)
│   ├── quorum-loss/                      (SKILL.md + kql-livesite.yaml + references/)
│   ├── error-40613/                      (3 SKILL.md + kql-livesite.yaml + references/)
│   ├── long-reconfig/                    (SKILL.md + kql-livesite.yaml + references/)
│   ├── high-sync-commit-wait/            (SKILL.md + kql-livesite.yaml + references/, BC/Premium only)
│   ├── seeding-rca/                      (SKILL.md + kql-livesite.yaml + references/)
│   ├── update-slo/                       (SKILL.md + kql-livesite.yaml + references/)
│   ├── node-health/                      (SKILL.md + kql-livesite.yaml + references/)
│   └── login-failure/                    (SKILL.md + kql-livesite.yaml + references/)
├── connectivity/                         ← Connectivity (118 livesite skills)
│   ├── auto_investigation.md             ← 🤖 自动调查入口 (7 routes)
│   ├── connectivity-base/                (kql-livesite.yaml — 8 skills + ring-health 12 skills)
│   ├── connectivity-errors/              (12 error dirs, 33 KQL + 5 knowledge)
│   ├── connectivity-scenarios/           (6 scenarios, 49 KQL)
│   └── connectivity-utilities/           (5 utilities, 16 KQL)
├── config/                               ← Dashboard config
└── (root-level legacy yaml files)
```

**搜索优先级：**
- **P1**: `kql-livesite.yaml` — SQLLivesiteAgents 工程团队模板
- **P1**: `kql-sqldri-*.yaml` — SQLDRI Copilot Perf Workflow 模板
- **P2**: `kql-distilled.yaml` — 手工蒸馏的 KQL

Recommended search order:
1. Local YAML / extracted skill by topic and keyword
2. Local TSG content or extracted CSS wiki material
3. CSS Wiki / msdata / EngHub
4. AI-generated KQL using table schema references

### Step 3.2: Search msdata TSG Repos + CSS Wiki（并行线路 2）

**与线路 1（本地 YAML）并行执行。** 完整搜索方法（工具选型/参数/陷阱）见 [search-tsg](search-tsg.md)。

**按 Step 2 分类只搜对应的 repo**：

| Step 2 分类 | 目标 msdata Repo |
|-------------|-----------------|
| **A. Performance** | [TSG-SQL-DB-Performance](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-Performance) |
| **B. Availability** | [TSG-SQL-DB-Availability](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-Availability) |
| **C. Connectivity** | [TSG-SQL-DB-Connectivity](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-Connectivity) |
| **D. GeoDR / FOG** | [TSG-SQL-DB-GeoDr](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-GeoDr) |
| **E. Backup & Restore** | [TSG-SQL-DB-BackupRestore](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-BackupRestore) |
| **F. General** | [Database Systems Wiki](https://msdata.visualstudio.com/Database%20Systems/_wiki) |
| Query Store | [TSG-SQL-DB-QueryStore](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-QueryStore) |
| Resource Governance | [TSG-SQL-DB-RG](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-RG) |
| Data Integration | [TSG-SQL-DB-DataIntegration](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-DataIntegration) |

**主用工具**: `mcp_msdata_search_code` 一次传入 `repository` 数组并行搜多个 repo。
**结果后处理**: 过滤 `_site/` 和 `.attachments/` 噪音, 只保留 `.md`/`.ipynb`/`.yml`。

**调用模板**（跨 10 个 SQL DB TSG repo 一次搜索）：
```jsonc
{
  "tool": "mcp_msdata_search_code",
  "project": ["Database Systems"],
  "repository": [
    "TSG-SQL-DB-Airgap","TSG-SQL-DB-Availability","TSG-SQL-DB-Connectivity",
    "TSG-SQL-DB-DataIntegration","TSG-SQL-DB-GeoDr","TSG-SQL-DB-Native",
    "TSG-SQL-DB-Performance","TSG-SQL-DB-QueryStore","TSG-SQL-DB-RG",
    "TSG-SQL-DB-Telemetry"
  ],
  "searchText": "<token>", "top": 50
}
```

**同时搜 CSS Wiki**（所有分类都搜）：
- `mcp_csswiki_search_wiki` project=["AzureSQLDB"] — CSS 团队 SQLDB TSG 和 case 经验

**取单页全文** → `mcp_enghub_fetch <url>`（`mcp_msdata_repo_get_file_content` 已被禁用）。

### Step 3.3: 兜底 — AI Generate with Schema Reference
If no suitable template exists, generate KQL using:
- `~/.copilot/agents/skills/kql-templates/sqldb/db-tables-reference.md`
- `~/.copilot/agents/skills/kql-templates/sqldb/db-tables-list.txt`
- `~/.copilot/agents/skills/kql-templates/sqldb/db-tables-relationship.html`

Always verify actual column names before execution.

## Step 4: Present Query for User Review
**Do not execute immediately.** Show the user:
1. Complete KQL with parameters filled in
2. A clear confirmation question

**Note:** SQLDB 不需要手动确定集群 URL — `execute-kusto-query` skill 会根据 ServerName 自动 DNS 解析 region 并定位正确的 Kusto 集群。

### Parameter substitution (runtime)
When filling parameters into YAML templates, replace **all** of these placeholders with the user-provided value:

| User input | Placeholders to replace |
|------------|------------------------|
| ServerName | `{ServerName}`, `{LogicalServerName}` |
| DatabaseName | `{DatabaseName}` |
| TimeRange | `{TimeRange}` |
| AppName | `{AppName}` |
| ClusterName | `{ClusterName}` |

Note: Different Kusto tables use different **column names** for the same concept (e.g., `logical_server_name`, `LogicalServerName`, `server_name`). The column names in the KQL are correct as-is — only the `{placeholder}` values should be replaced.

Example format:

````text
Query:
```kql
{complete KQL with ServerName / DatabaseName / TimeRange filled in}
```

Execute this query, or do you want to adjust it first?
````

## Step 5: Execute
Only after user confirmation:
- Execute the reviewed KQL
- Keep time filters and row limits in place
- If multiple queries are needed, run the approved chain in logical order

Safety checks before execution:
- Ensure a bounded time filter exists
- Ensure the query is scoped to server and/or database when possible
- Add `take`, `top`, or `summarize` where appropriate
- Avoid full-table scans over long time ranges

## Step 6: Handle Errors
Common handling patterns:
- **Column not found / SEM0100** → check schema, fix the column, re-present query
- **No data** → widen time range, switch cluster, or relax one filter at a time
- **Timeout** → narrow time range, reduce projected columns, summarize earlier
- **Auth / endpoint issue** → verify cluster URL and target database
- **Case mismatch** → normalize server/database filters using `=~`

## Step 7: Analyze Results

### Step 7.0: Apply `QuestionToAI` Rules (if KQL came from a YAML skill)

**⚠️ MANDATORY when the executed KQL came from a `kql-distilled.yaml` / `kql-livesite.yaml` / `kql-sqldri-*.yaml` skill that has a `QuestionToAI:` field.**

The `QuestionToAI:` field is structured AI post-processing logic. After the KQL returns:

1. **Read the skill's `QuestionToAI` field** from the YAML where the KQL was sourced
2. **Bind result columns to placeholders** (`{{column_name}}` → actual value from row 0 or row "top1")
3. **Apply each rule sequentially** in the `### Rules` block
4. **Compute output variables** (e.g. `{{IssueDetected}}`, `{{ResultMessage}}`, `{{HasPlanRegression}}`)
5. **Display the variable bindings AND the rules outcome** in the analysis section, so the user sees exactly what was inferred

**Common output variables** (convention from sqldri-copilot):

| Variable | Type | Meaning |
|----------|------|---------|
| `{{IssueDetected}}` | bool string | `'true'` if skill found a problem, `'false'` otherwise — drives next-step routing |
| `{{ResultMessage}}` | string | Human-readable one-line summary of the result |
| `{{<custom>Message}}` | string | Skill-specific message (e.g. `{{cpuMessage}}`, `{{longRunningMessage}}`) |
| `{{Has<Indicator>}}` | bool string | Skill-specific flag (e.g. `{{HasPlanRegression}}`, `{{HasHighWait}}`) — drives recommended follow-up skills |

**Skip rule application if**:
- The KQL was hand-written or modified beyond placeholder substitution
- The skill has no `QuestionToAI` field
- The query result is empty (use the skill's `MessageForEmptyKustoResult` instead)

**Example** (DIST-QUERIES-TopDuration):

```
Result row[0]: query_hash=0xC610B2E4522D75C1, TotalElapsed_ms=215.2, WaitPercent=62.7, dcount_plan=1
            ↓ Apply QuestionToAI rules
Rule 2: dcount_plan=1, not > 1     → {{HasPlanRegression}} = 'false'
Rule 3: WaitPercent=62.7 >= 30      → {{HasHighWait}}       = 'true'
                                        → recommend LS-QUERIES-13 (Top Wait Types)
Rule 5: TotalElapsed_ms=215.2 < 1000 → {{IssueDetected}}    = 'false'
```

### Step 7.1: Structured Summary

Use a structured summary:
- **Conclusion** — healthy vs unhealthy, issue type, confidence
- **Rationale** — what evidence supports the conclusion
- **Anomalies** — timestamps, spikes, errors, wait types, failed operations
- **Trends** — sustained, intermittent, cyclical, or step-change behavior
- **Next Steps** — additional tables / queries to run next

## DB-Specific Differences from MI

### Identity and scoping
- SQL DB investigations usually require **both** `LogicalServerName` **and** `DatabaseName`.
- MI investigations are often server-level first; SQL DB is much more **database-granular**.
- Database joins commonly use `database_name`, `logical_database_name`, `database_id`, or `logical_database_id`.

### Service model differences
- SQL DB includes:
  - **Elastic pools**
  - **DTU-based SKUs**
  - **Serverless**
  - **Hyperscale**
- Performance interpretation must account for whether the workload is single DB, pooled DB, serverless, or Hyperscale.

### App type differences
- SQL DB worker patterns commonly use:
  - `AppTypeName == "Worker.ISO"`
  - `AppTypeName == "Worker.ISO.Premium"`
  - `AppTypeName == "Worker.DW"`
- MI guidance that relies on `Worker.CL` does **not** directly apply to SQL DB.

### Telemetry granularity
- SQL DB has richer **per-database** monitoring for:
  - real-time resource stats
  - wait stats
  - Query Store execution data
  - login / redirector activity
  - elastic pool and Hyperscale signals

## Key DB Tables Reference (Top 15)

| Table | Purpose |
|-------|---------|
| `MonAnalyticsDBSnapshot` | Latest DB properties, tier, state, region, pool, serverless/Hyperscale context |
| `MonDmRealTimeResourceStats` | Per-database CPU, data IO, log write, memory style resource pressure |
| `MonDmCloudDatabaseWaitStats` | Per-database wait profile and dominant bottlenecks |
| `MonLogin` | Login attempts, failures, latency, client address / driver context |
| `MonBackup` | Backup history, metadata, start/end, failures |
| `AlrSQLErrorsReported` | SQL errors, severity, error numbers, fabric / app context |
| `MonSQLSystemHealth` | System health and errorlog-style diagnostic events |
| `MonManagement` | Management-plane and control-plane operations impacting the DB |
| `MonWiQdsExecStats` | Query Store execution stats for hot queries / plans |
| `MonGeoDRFailoverGroups` | GeoDR / Failover Group configuration, role, partner mapping |
| `MonDbSeedTraces` | Seeding, catch-up, replica sync progress |
| `MonElasticPoolStats` | Elastic pool context and pool-level pressure for DBs in pools |
| `MonSocrates` | Hyperscale-specific service / storage / replica signals |
| `MonRedirector` | Gateway / routing / redirect behavior |
| `MonRolloutProgress` | Deployment / rollout correlation during incidents |

## DB-Specific Filter Patterns

### Worker / app filters
```kql
| where AppTypeName == "Worker.ISO"
| where AppTypeName == "Worker.ISO.Premium"
| where AppTypeName == "Worker.DW"
```

### Server filter
```kql
| where LogicalServerName =~ "{ServerName}"
```
or
```kql
| where logical_server_name =~ "{ServerName}"
```
or
```kql
| where server_name =~ "{ServerName}"
```

### Database filter
```kql
| where DatabaseName =~ "{DatabaseName}"
```
or
```kql
| where database_name =~ "{DatabaseName}"
```
or
```kql
| where logical_database_name =~ "{DatabaseName}"
```

### Combined DB investigation filter
```kql
| where logical_server_name =~ "{ServerName}" or LogicalServerName =~ "{ServerName}" or server_name =~ "{ServerName}"
| where database_name =~ "{DatabaseName}" or DatabaseName =~ "{DatabaseName}" or logical_database_name =~ "{DatabaseName}"
```

### GeoDR / FOG filter
```kql
| where failover_group_id == "{FailoverGroupId}"
```

### Database ID filter
```kql
| where database_id == {DatabaseId}
```

## Suggested Investigation Starting Points

### Performance
1. `MonAnalyticsDBSnapshot`
2. `MonDmRealTimeResourceStats`
3. `MonDmCloudDatabaseWaitStats`
4. `MonWiQdsExecStats`
5. `MonElasticPoolStats` or `MonSocrates`

### Availability / outage
1. `MonAnalyticsDBSnapshot`
2. `AlrSQLErrorsReported`
3. `MonSQLSystemHealth`
4. `MonManagement`
5. `MonRolloutProgress`

### Connectivity
1. `MonLogin`
2. `MonRedirector`
3. `AlrSQLErrorsReported`
4. `MonSQLSystemHealth`

### Backup
1. `MonAnalyticsDBSnapshot`
2. `MonBackup`
3. `MonManagement`
4. `AlrSQLErrorsReported`

### GeoDR / FOG
1. `MonGeoDRFailoverGroups`
2. `MonDbSeedTraces`
3. `MonAnalyticsDBSnapshot`
4. `MonRedirector`

---

## Investigation SOPs

### AAD Login Failure Investigation

**Tested and verified on 2026-04-30 with tsazessdbxtpttu04/I17BAADATSSDB01 (East Asia)**
**源码确认: WebQueryEndpoint/XEvents/WebQueryProcessLoginFinishXEvent.cs (Gateway 层 XEvent)**
**TSG 参考: TSG-SQL-Security/TSG/AAD/AAD0005-No-token-from-client.md (ENTRA0010)**

#### TDS AAD Authentication Flow

**MonLogin 的 `process_login_finish` XEvent 由 Gateway (WebQueryEndpoint) 记录，不是 Backend Worker。**
**所有 fedauth_* 时间列都是 Gateway 层的测量。**

```
客户端 (app)                   SQL Gateway (WebQueryEndpoint)           AAD
  |                                 |                                    |
  |--- TCP handshake -------------->|                                    |
  |--- TDS prelogin (加密协商) ---->|                                    |
  |--- TLS handshake -------------->|                                    |
  |--- Login7 packet -------------->|                                    |
  |                                 |                                    |
  |<-- FEDAUTHINFO (tenant info) ---|  Gateway 告诉客户端:               |
  |                                 |  "去 AAD 获取 token,               |
  |                                 |   这是 tenant ID 和 SPN"           |
  |                                 |                                    |
  |  ┌─── fedauth_token_wait_time_ms 开始计时 ───────────────┐          |
  |  │                              |                        │          |
  |  │  客户端向 AAD 获取 token:     |                        │          |
  |  │  |- 连接 AAD endpoint        |                        │          |
  |  │  |- 发送凭据                  |                        │          |
  |  │  |- 等 AAD 返回 JWT           |                        │          |
  |--- 向 AAD 认证 (用户名+密码等) -------------------------------------------->|
  |<-- JWT access token --------------------------------------------------------|
  |  │                              |                        │          |
  |  │  客户端把 token 发给 Gateway: |                        │          |
  |--- FEDAUTH token message ------>|                        │          |
  |  │                              |                        │          |
  |  └─── fedauth_token_wait_time_ms 结束 ───────────────────┘          |
  |                                 |                                    |
  |                                 |  ┌── fedauth_token_process_time ──┐|
  |                                 |  │  验证 JWT:                     │|
  |                                 |  │  - 签名验证 (signature_validation) │
  |                                 |  │  - JWT 解析 (jwt_token_parsing)│|
  |                                 |  │  - 上下文构建 (context_build)  │|
  |                                 |  │  - 组展开 (group_expansion)    │|
  |                                 |  └────────────────────────────────┘|
  |                                 |                                    |
  |                                 |-- 转发到 Backend Worker            |
  |<-- Login 成功或失败 ------------|                                    |
```

**关键事实（来自 TSG ENTRA0010 和源码确认）：**
1. `fedauth_token_wait_time_ms` = **Gateway 等客户端发送 token 的时间**（从发出 FEDAUTHINFO 到收到 FEDAUTH token）
2. Gateway 给客户端 **20 秒**超时。超过 20 秒 → 连接被 Gateway 终止
3. 这段等待时间包含：客户端连接 AAD + AAD 验证 + AAD 返回 token + 客户端发回 token 的网络时间
4. **SQL 端（Gateway）无法区分**是 AAD 慢还是客户端慢 → 需要客户端日志确认
5. `DISPATCHER_QUEUE_SEMAPHORE` in message = Gateway worker 线程在等 token 期间的等待类型（表现，不是根因）

**Known Issue（来自 TSG ENTRA0010）：**
> 现代 SQL 驱动的 "Default" authentication 模式会依次尝试多种身份来源（managed identity → VS → VS Code）。在没有 managed identity 的机器上，获取 token 需要 **10-15 秒**，导致连接看起来非常慢。

#### Interaction Flow

```
用户: "login failed for {ServerName}/{DatabaseName}"
  ↓
Step 1: 问 region + 确认时间点
  ↓
Step 2: 展示查询（3 个），等确认
  → 查询 1: MonLogin failed login 详情（含 fedauth 时间分解）
  → 查询 2: 成功 vs 失败对比
  → 查询 3: Reconfiguration 检查
  ↓
Step 3: 用户确认 → 执行
  ↓
Step 4: 分析
  → 先看 error + state → 确定失败类型
  → 再看 fedauth_* 列 → 确定是哪个阶段慢
  → 结合 message (waitstats XML) → 补充 SQL 内部等待信息
  → ⚠️ 不猜测！先查文档确认每个列和值的含义
```

#### KQL 查询

**查询 1: Failed login 详情（含完整 fedauth 时间分解）**
```kql
MonLogin
| where logical_server_name =~ "{ServerName}"
| where database_name =~ "{DatabaseName}"
| where PreciseTimeStamp between (datetime("{StartTime}") .. datetime("{EndTime}"))
| where event == "process_login_finish"
| where is_success == 0
| extend AADUser = iif(fedauth_adal_workflow > 0 or fedauth_library_type > 0, "AAD", "SQL")
| extend fedauth_type_desc = case(
    fedauth_library_type == 0, "SQL Auth",
    fedauth_library_type == 2, "Token Based",
    fedauth_library_type == 3 and fedauth_adal_workflow == 1, "AAD Password",
    fedauth_library_type == 3 and fedauth_adal_workflow == 2, "AAD Integrated",
    fedauth_library_type == 3 and fedauth_adal_workflow == 3, "AAD Universal (MFA)",
    strcat("Type:", tostring(fedauth_library_type), " WF:", tostring(fedauth_adal_workflow)))
| project PreciseTimeStamp, error, state, state_desc,
    fedauth_type_desc,
    total_time_ms,
    netread_time_ms,
    fedauth_token_wait_time_ms,
    fedauth_token_process_time_ms,
    fedauth_jwt_token_parsing_time_ms,
    fedauth_signature_validation_time_ms,
    fedauth_context_build_time_ms,
    fedauth_group_expansion_time_ms,
    ssl_time_ms, login_time_ms,
    peer_address, application_name, driver_name,
    message
| order by PreciseTimeStamp desc
| take 50
```

**查询 2: 成功 vs 失败对比（同时段）**
```kql
MonLogin
| where logical_server_name =~ "{ServerName}"
| where database_name =~ "{DatabaseName}"
| where PreciseTimeStamp between (datetime("{StartTime}") .. datetime("{EndTime}"))
| where event == "process_login_finish"
| summarize
    SuccessCount = countif(is_success == true),
    FailCount = countif(is_success == false)
    by bin(PreciseTimeStamp, 1m)
| order by PreciseTimeStamp asc
```

**查询 3: Reconfiguration / Failover 检查**
```kql
MonManagement
| where TIMESTAMP between (datetime("{StartTime}") .. datetime("{EndTime}"))
| where LogicalServerName =~ "{ServerName}"
| where operation_name has_any ("Failover", "Reconfigure", "UpdateDatabase")
| project TIMESTAMP, operation_name, event
| order by TIMESTAMP desc
| take 20
```

#### 分析指南

**Step 1: 看 error + state 确定失败类型**
| Error | 含义 |
|-------|------|
| 18456 | Authentication failure（看 state 确定具体原因） |
| 33155 | Login timeout |
| 40613 | Database not available |
| 40532 | Cannot open database |

**Step 2: 如果是 timeout (33155)，看 fedauth 时间分解**
| 判断 | 原因 | 下一步 |
|------|------|--------|
| `fedauth_token_wait_time_ms` ≈ `total_time_ms` | 客户端获取 AAD token 慢（SQL 在等 token） | 需要客户端日志（ODBC trace / app log） |
| `fedauth_token_process_time_ms` 很大 | SQL 验证 token 慢 | 检查 SQL 负载 |
| `fedauth_fetch_signingkey_refresh_time_ms` 很大 | SQL 刷新 AAD 公钥慢 | 检查 SQL 到 AAD 的网络 |
| `ssl_time_ms` 很大 | TLS 握手慢 | 检查网络/证书 |
| `login_time_ms` 很大 | SQL login 处理慢 | 检查 SQL CPU/blocking |
| `enqueue_time_ms` 很大 | Gateway 排队等待 | 检查 Gateway 负载 |

**Step 3: message 列的 waitstats XML 是补充信息**
- `DISPATCHER_QUEUE_SEMAPHORE` → SQL worker 线程等待（通常是在等外部响应期间的表现，不是根因）
- 先看 fedauth_* 列确定根因，再用 message 补充

**⚠️ 关键：fedauth_token_wait_time_ms 不是 "SQL 去 AAD 拿 token"。在 AAD Password 模式下，是客户端先从 AAD 拿 token，然后发给 SQL。SQL 只是在等客户端把 token 发过来。**

---

### Availability Investigation

**当问题分类为 Availability 时的完整流程（failover/outage/quorum loss/error 40613/SLO change 等）：**

**模板目录**: `~/.copilot/agents/skills/kql-templates/sqldb/availability/`
**来源**: SQLLivesiteAgents 工程团队 P1 模板 (132 skills, 26 Kusto 表)

```
Availability 问题
  ↓
Step 3a: Triage — 并行跑 4 个快速扫描
  → 查询 1: SqlFailovers (有无 failover?)
  → 查询 2: LoginOutages (有无 outage?)
  → 查询 3: MonLogin error 40613 (state 126/127/129?)
  → 查询 4: MonSQLSystemHealth 高严重度错误
  → 展示结果 + 自动路由到子场景
  ↓
Step 3a-result: 展示 triage 总览 + 选择深入方向
  | 维度 | 状态 | 关键指标 |
  |------|------|----------|
  | Failover | 🔴 | 2 failovers detected |
  | LoginOutages | 🔴 | 45s outage |
  | Error 40613 | 🟡 | state 127, 30s |
  | SQL Errors | 🟢 | no sev>=17 |
  → 自动推荐深入方向（基于 triage 结果）
  → 用户也可手动选择:
    1. failover/          — Failover 调试 (25 skills)
    2. quorum-loss/       — 仲裁丢失 (20 skills)
    3. error-40613/       — Error 40613 state 126/127/129 (20 skills)
    4. long-reconfig/     — 长重配置 (21 skills)
    5. high-sync-commit-wait/ — HADR 同步提交延迟 (11 skills, BC/Premium only)
    6. seeding-rca/       — Geo-Replication seeding 失败 (11 skills)
    7. update-slo/        — SLO 变更调试 (10 skills)
    8. node-health/       — 节点基础设施 (8 skills)
    9. login-failure/     — 登录失败分类 (6 skills)
  ↓
Step 3b: 深入调查
  → 加载用户选择的子目录的 kql-livesite.yaml
  → 填充参数 → 展示 KQL
  ↓
同时 线路 2 搜 TSG-SQL-DB-Availability repo（并行）
```

#### Triage 快速扫描查询

**查询 1: SqlFailovers — 有无 failover?**
```kql
SqlFailovers
| where FailoverStartTime between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{ServerName}' and logical_database_name =~ '{DatabaseName}'
| project FailoverStartTime, FailoverEndTime, ReconfigurationType, CRMAction, OldPrimary, NewPrimary
| order by FailoverStartTime asc
```
→ 有结果 → 路由 `failover/` (🔴) 或 `quorum-loss/`

**查询 2: LoginOutages — 有无 outage?**
```kql
LoginOutages
| where outageStartTime between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{ServerName}' and database_name =~ '{DatabaseName}'
| project outageStartTime, outageEndTime, durationSeconds, OutageType, OutageReasonLevel1, OutageReasonLevel2, OwningTeam
| order by outageStartTime asc
```
→ `OutageType == "CustomerInitiated"` → 路由 `update-slo/`
→ `OutageReasonLevel1` contains "Failover" → 路由 `failover/`

**查询 3: MonLogin error 40613 — 有无 40613 错误?**
```kql
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where logical_server_name =~ '{ServerName}' and database_name =~ '{DatabaseName}'
| where error == 40613
| summarize count() by state
| order by count_ desc
```
→ state 126 → 路由 `error-40613/` (STATE126 分支)
→ state 127 → 路由 `error-40613/` (STATE127 分支)
→ state 129 → 路由 `error-40613/` (STATE129 分支)

**查询 4: MonSQLSystemHealth — 高严重度错误?**
```kql
MonSQLSystemHealth
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where AppName =~ '{AppName}'
| where error_id in (17883, 17884, 17888, 701, 802, 833, 837)
| summarize count() by error_id, NodeName
| order by count_ desc
```
→ 有结果 → 路由 `node-health/` 或 `long-reconfig/`

#### 自动路由逻辑

| Triage 结果 | 自动路由到 | 原因 |
|-------------|-----------|------|
| Failover found + duration > 60s | `failover/` | 长 failover 需要完整时间线分析 |
| Failover found + duration < 30s | `error-40613/` | 短 failover，关注 recovery/warmup |
| QuorumLoss in LoginOutages | `quorum-loss/` | 仲裁丢失 |
| OutageType = CustomerInitiated | `update-slo/` | SLO 变更引起的 outage |
| Error 40613 state 126 > 120s | `error-40613/` | 卡角色转换 |
| Error 40613 state 127 > 300s | `error-40613/` | 卡预热 |
| Error 40613 state 129 > 300s | `error-40613/` | HADR 不可用 |
| Non-yielding / OOM / I/O stalls | `long-reconfig/` | 性能压力导致的可用性问题 |
| Login failures without failover | `login-failure/` | 非 failover 原因的登录失败 |
| No clear signal | `node-health/` | 基础设施层排查 |

#### 深入调查时的 KQL 文件

每个子目录下只有一个文件 `kql-livesite.yaml`，所有 KQL 来自 SQLLivesiteAgents P1 模板：

| 子目录 | Skills | 核心表 |
|--------|--------|--------|
| `failover/` | 25 | WinFabLogs, MonFabricApi, MonSQLSystemHealth, SqlFailovers, MonNodeTraceETW |
| `quorum-loss/` | 20 | WinFabLogs, MonFabricDebug, MonRecoveryTrace, MonDmDbHadrReplicaStates |
| `error-40613/` | 20 | MonLogin, MonFabricApi, MonSQLSystemHealth, SqlFailovers, LoginOutages |
| `long-reconfig/` | 21 | MonFabricApi, MonFabricDebug, MonSQLSystemHealth, MonDmDbHadrReplicaStates |
| `high-sync-commit-wait/` | 11 | MonDmDbHadrReplicaStates, MonDmOsWaitStats, MonFabricApi |
| `seeding-rca/` | 11 | MonDbSeedTraces, MonFabricDebug, MonRgLoad, MonAnalyticsDBSnapshot |
| `update-slo/` | 10 | MonManagement, MonManagementOperations, MonAnalyticsDBSnapshot |
| `node-health/` | 8 | MonClusterLoad, WinFabLogs, MonSQLInfraHealthEvents |
| `login-failure/` | 6 | MonLogin, MonDmDbHadrReplicaStates, SqlFailovers |

### Performance Investigation

**当 Step 2 分类为 A. Performance 时的完整流程：**

**来源**: SQLLivesiteAgents / Performance / triage / SKILL.md

```
Performance 问题
  ↓
Step 3a: Triage — 关键词路由或默认全扫
  → 有用户关键词 ("high CPU", "memory", "blocking"...) → 直接路由到对应子目录
  → 无关键词 → 默认跑 5 个: CPU, memory, out-of-disk, query-store, miscellaneous
  ↓
Step 3b: 按选定子目录，加载对应的 kql-livesite.yaml 第一个 skill
  → 每个子目录的 *-01 skill 就是该维度的入口查询：
    LS-CPU-01    → cpu/kql-livesite.yaml         (User Pool CPU Summary)
    LS-BLOCKING-01 → blocking/kql-livesite.yaml   (Peak Blocking Detection)
    LS-MEMORY-01  → memory/kql-livesite.yaml      (Memory Overbooking — MRG Detection)
    LS-QUERIES-01 → queries/kql-livesite.yaml     (Query Execution CPU Analysis)
    LS-QDS-01    → query-store/kql-livesite.yaml  (QDS Readonly Detection)
    LS-COMPILE-01 → compilation/kql-livesite.yaml (Failed Compilation CPU %)
    LS-OOD-01    → out-of-disk/kql-livesite.yaml  (Drive Out of Space)
    LS-MISC-01   → miscellaneous/kql-livesite.yaml (Worker Thread Exhaustion)
    LS-SQLOS-01  → sqlos/kql-livesite.yaml        (Non-Yielding Detection)
  → 填充参数 → 展示 KQL
  ↓
Step 3c: 根据入口查询结果，按 investigation.yaml 的分支逻辑深入
  → 例: LS-CPU-01 发现 max_cpu > 80% → 跑 LS-CPU-01b (hourly pattern)
    → 再跑 LS-CPU-03 (discrepancy) → LS-CPU-04 (top queries)
  ↓
同时 线路 2 搜 TSG-SQL-DB-Performance repo（并行）
```

**关键词 → 子目录路由表** (来自 SQLLivesiteAgents triage SKILL.md):

| 用户关键词 | 路由到子目录 | 入口 KQL |
|-----------|------------|---------|
| "high CPU", "CPU spike", "CPU usage" | `cpu/` | LS-CPU-01 |
| "memory", "OOM", "overbooking", "buffer pool" | `memory/` | LS-MEMORY-01 |
| "blocking", "deadlock" | `blocking/` | LS-BLOCKING-01 |
| "slow query", "query performance", "failed queries" | `queries/` | LS-QUERIES-01 |
| "QDS", "Query Store", "readonly" | `query-store/` | LS-QDS-01 |
| "compilation", "compile error" | `compilation/` | LS-COMPILE-01 |
| "disk space", "disk full", "tempdb full", "quota" | `out-of-disk/` | LS-OOD-01 |
| "worker thread", "corruption", "AKV" | `miscellaneous/` | LS-MISC-01 |
| "non-yielding", "scheduler", "dump" | `sqlos/` | LS-SQLOS-01 |
| (无关键词 — 默认) | CPU + memory + out-of-disk + query-store + miscellaneous | 5 个入口并行 |

**执行顺序** (多 skill 时): CPU → memory → out-of-disk → QDS → Queries → Compilation → miscellaneous → SQLOS

**深入调查时的 KQL 文件优先级**:
- **P1**: `kql-livesite.yaml` — SQLLivesiteAgents 工程团队模板
- **P1**: `kql-sqldri-*.yaml` — SQLDRI Copilot Perf Workflow 模板
- **P2**: `kql-distilled.yaml` — 手工蒸馏的 KQL

### Backup Investigation

**TODO**: Record after testing

### Connectivity Investigation

**TODO**: Record after testing
