# 毛球球 (MaoQiuQiu) 🧶

SQL Server 案例调查 Copilot Agent 系统，支持多源文档搜索、Error Code 深度研究、Callstack 分析、MI/SQL DB KQL 调查。

> 毛球球虽然软萌，但能滚到每个 Kusto 表的角落里帮你查问题。

## 快速安装

```powershell
# 1. Clone repo
git clone https://github.com/lduanmsft/copilot-agents.git

# 2. 进入安装包目录
cd copilot-agents/MaoQiuQiu

# 3. 运行安装脚本（自动复制到 ~/.copilot/agents/）
.\Install-MaoQiuQiu.ps1

# 4. 配置 MCP servers（见下方 MCP 工具依赖表）
# 5. 在 VS Code 中输入 @lduan-agent 开始使用
```

### 前置依赖
- VS Code Insiders + GitHub Copilot Chat
- Node.js（ADO MCP 需要 npx）
- Azure CLI（Kusto 查询认证：`az login`）
- Python 3.x（审计脚本，非必须）

## 架构概览

```
agents/
├── lduan-agent.agent.md          ← 主入口 Agent（5 种模式）
├── callstack-research.agent.md   ← Mode C: Callstack 分析
├── errorcode-research.agent.md   ← Mode B: Error Code 研究
├── search-*.agent.md (5个)       ← Mode A: 并行搜索 Sub-Agent
│
├── skills/                       ← 运行时技能文件
│   ├── mi-kql-investigation.md   ← MI KQL 调查工作流
│   ├── db-kql-investigation.md   ← DB KQL 调查工作流
│   ├── nys-analysis.md           ← Non-Yielding Scheduler 分析规则
│   ├── pr-tracking.md            ← PR/CU 可用性追踪
│   ├── report-rules.md           ← 报告生成规范（3 格式输出）
│   ├── kql-templates/            ← KQL 模板库（5204 skills）
│   │   ├── mi/                   ← MI: 1350 skills, 6 categories
│   │   ├── sqldb/                ← SQL DB: 3854 skills, 10 categories
│   │   └── shared/               ← 共享集群映射
│   └── ops/                      ← 运维文档（非运行时）
│       ├── mi-kql-extraction-pipeline.md
│       └── db-kql-extraction-pipeline.md
│
├── errorcode_research/           ← Error Code 研究报告输出
├── outcome/                      ← 案例分析报告输出
└── search-results/               ← 搜索结果缓存
```

## 5 种操作模式

| 模式 | 名称 | 功能 |
|------|------|------|
| **A** | 多源文档搜索 | 跨 8 个知识源并行搜索（Web、Learn、EngHub、CSS Wiki、msdata、GitHub） |
| **B** | Error Code 研究 | 深度分析 SQL Server 错误码（定义、源码、XEvent、Bug） |
| **C** | Callstack 分析 | 分析 non-yielding/crash/memory dump 的 callstack |
| **D** | MI Case Investigation | SQL MI 调查：文档搜索 + KQL 查询 + TSG 执行 |
| **E** | SQL DB Case Investigation | Azure SQL DB 调查：文档搜索 + KQL 查询 + TSG 执行 |

## KQL 模板库

### SQL Managed Instance (1350 skills)

| 分类 | Skills | 主要表 |
|------|--------|--------|
| availability | 328 | MonSQLSystemHealth, MonManagement, MonDmDbHadrReplicaStates |
| backup-restore | 434 | MonBackup, MonRestoreEvents, MonSQLXStore |
| general | 53 | MonManagedServers, MonAnalyticsDBSnapshot |
| networking | 108 | MonLogin, MonRedirector, MonFedAuthTicketService |
| performance | 344 | MonDmRealTimeResourceStats, MonWiQdsExecStats, MonSqlRgHistory |
| replication | 83 | MonCDCTraces, MonLogReaderTraces, MonTranReplTraces |

### Azure SQL Database (3854 skills)

| 分类 | Skills | 主要表 |
|------|--------|--------|
| availability | 768 | MonSQLSystemHealth, MonSocrates, MonManagement |
| connectivity | 303 | MonLogin, MonRedirector, MonWebQueryEndpoint |
| css-wiki | 715 | MonLogin, MonDmRealTimeResourceStats, MonBlockedProcessReportFiltered |
| data-integration | 471 | MonBackup, MonRestoreEvents, MonDataSync |
| geodr | 108 | MonGeoDRFailoverGroups, MonDmDbHadrReplicaStates |
| native | 167 | ASTrace, MonLogin, MonAnalyticsDBSnapshot |
| performance | 898 | MonWiQdsExecStats, MonSqlRgHistory, MonRgLoad |
| query-store | 29 | MonQueryStoreInfo, MonWiQdsExecStats |
| resource-governance | 93 | MonRgLoad, MonRgManager, MonClusterLoad |
| telemetry | 302 | MonRgLoad, MonRgManager, MonSynapseLinkTraces |

### 参考文档

| 文件 | 位置 | 内容 |
|------|------|------|
| `mi-tables-reference.md` | `kql-templates/mi/` | MI 表 Schema（135 表，802KB） |
| `mi-tables-code-reference.md` | `kql-templates/mi/` | MI 表代码定义（141 表，160KB） |
| `mi-tables-relationship.html` | `kql-templates/mi/` | MI 表关系图（25 核心表） |
| `db-tables-reference.md` | `kql-templates/sqldb/` | DB 表 Schema（231 表，1.3MB） |
| `db-tables-code-reference.md` | `kql-templates/sqldb/` | DB 表代码定义（160 表，172KB） |
| `db-tables-relationship.html` | `kql-templates/sqldb/` | DB 表关系图（30 核心表） |
| `SQLClusterMappings.Followers.csv` | `kql-templates/shared/` | Region → Kusto 集群映射 |

## MCP 工具依赖

| MCP Server | 用途 |
|------------|------|
| `csswiki` | CSS Wiki 搜索（SQLServerWindows, AzureSQLMI, AzureSQLDB） |
| `msdata` | msdata ADO Wiki/Code/WorkItems 搜索 |
| `enghub` | EngineeringHub (eng.ms) 文档搜索 |
| `microsoft-learn` | Microsoft Learn 文档搜索 |
| `github-mcp-server` | GitHub 代码/Issue 搜索 |
| `azure-mcp` | Azure Kusto 查询执行 |

## KQL 调查工作流

### 标准流程（MI/DB 共用）

```
Step 1: 收集参数（ServerName, Region, TimeRange, [DatabaseName]）
Step 2: 搜索 KQL 模板（本地 YAML → TSG → AI 生成）
Step 3: 确定集群端点（SQLClusterMappings → Follower 优先）
Step 4: 展示查询等用户确认（⚠️ 永不自动执行）
Step 5: 执行并分析结果
Step 6: 结构化输出（Conclusion + Rationale + Anomalies + Next Steps）
```

### MI vs DB 关键差异

| 维度 | MI | SQL DB |
|------|-----|--------|
| 粒度 | Instance 级 | **Database 级** |
| Worker 类型 | `Worker.CL` | `Worker.ISO` / `Worker.ISO.Premium` |
| 参数 | ServerName + Region | ServerName + **DatabaseName** + Region |
| 特有场景 | FOG seeding, MI Link | Elastic Pool, Hyperscale, Serverless |

### 运行时参数替换

| 用户输入 | 替换占位符 |
|----------|-----------|
| ServerName | `{ServerName}`, `{LogicalServerName}` |
| DatabaseName | `{DatabaseName}` |
| TimeRange | `{TimeRange}` |
| AppName | `{AppName}` |
| ClusterName | `{ClusterName}` |

## 报告输出

所有报告输出到 `outcome/`，每个报告生成 3 个文件：
- `{name}.md` — 中文 Markdown
- `{name}_en.md` — 英文 Markdown
- `{name}.html` — 暗色主题 HTML（自动用浏览器打开）

## 维护

### 添加新 KQL 模板
参考 `skills/ops/mi-kql-extraction-pipeline.md` 或 `skills/ops/db-kql-extraction-pipeline.md`。

### 审计模板质量
审计脚本在 `~/.copilot/scripts/`：
- `audit_sqldb_kql_v2.py` — DB 模板全面审计
- `audit_mi_kql.py` — MI 模板审计
- `audit_prompt_tags.py` — Prompt 标签校验
- `audit_prompt_semantic.py` — Prompt 语义校验

### 上次审计 (2026-04-30)
- MI: 1350 skills, 0 CRITICAL issues
- DB: 3854 skills, 0 CRITICAL issues
- 合计 5204 个可用 KQL 模板
