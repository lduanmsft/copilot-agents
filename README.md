# Copilot Agents & MI KQL Investigation Framework

SQL Server / Managed Instance 调查工具集，基于 GitHub Copilot CLI 和 MCP 服务器构建。

## 主 Agent：lduan-agent

三种操作模式，启动时交互选择：

### Mode A：📚 多源文档搜索
跨 10 个知识源并行搜索，自动分发 sub-agent 并汇总结果。

| # | 数据源 | 工具 |
|---|--------|------|
| 1 | 🌐 公共文档 | `web_search` |
| 2 | 📘 Microsoft Learn | `microsoft-learn-*` |
| 3 | 🏢 EngHub (eng.ms) | `enghub-*` |
| 4 | 📋 CSS Wiki: SQLServerWindows | `csswiki-search_wiki` |
| 5 | 📋 CSS Wiki: AzureSQLMI | `csswiki-search_wiki` |
| 6 | 📋 CSS Wiki: AzureSQLDB | `csswiki-search_wiki` |
| 7 | 📖 msdata Wiki | `msdata-search_wiki` |
| 8 | 💻 msdata Code | `msdata-search_code` |
| 9 | 🐛 msdata Work Items | `msdata-search_workitem` |
| 10 | 🐙 GitHub | `github-mcp-server-*` |

搜索流程：选范围 → 并行 sub-agent → 三层内容读取（摘要→精读→深潜）→ 综合分析 → 可选生成报告

### Mode B：🔬 研究 SQL Server Error Code
深度分析 SQL 错误码：查找定义 → 源码追踪 → XEvent 检测方法 → 生成 HTML 报告

支持版本：SQL 2017 / 2019 / 2022 / 2025，自动映射到对应 repo 和 branch

### Mode C：🔍 分析 Callstack
分析 crash dump / non-yielding / assertion 的 callstack：
- 逐层源码追踪（sqlmin → sqllang → SqlDK）
- 跨层 bug 搜索（ADO work items）
- 检测 yield/lock/cache 问题
- 生成 HTML 报告

自动检测：粘贴包含 `sqlmin!`、`sqllang!`、`SqlDK!` 的文本自动进入 Mode C

### 智能路由建议

| 问题类型 | 推荐模式 |
|----------|---------|
| SQL crash / stack dump | Mode C (callstack) |
| Non-yielding scheduler | Mode C (callstack) |
| 错误码深度分析 | Mode B (error code) |
| Azure SQL MI (FOG/TDE/AKV) | Mode A → scope 5 + 3 |
| 一般 SQL 排错 | Mode A → scope 2 + 1 |

## 架构

```
copilot-instructions.md          ← 全局指令（路由规则、行为规范）
mcp-config.json                  ← MCP 服务器配置

agents/                          ← 自定义 Agents
├── lduan-agent.agent.md         ← 主 Agent（Mode A/B/C）
├── callstack-research.agent.md  ← Callstack 分析 Agent（Mode C 的执行引擎）
├── errorcode-research.agent.md  ← 错误码研究 Agent（Mode B 的执行引擎）
├── search-csswiki.agent.md      ← CSS Wiki 搜索 Agent（含读写规则）
├── search-enghub.agent.md       ← EngHub 搜索 Agent
├── search-github.agent.md       ← GitHub 搜索 Agent
├── search-msdata.agent.md       ← msdata ADO 搜索 Agent
└── search-web.agent.md          ← Web 搜索 Agent

agents/skills/                   ← Skills（可复用的调查流程）
├── mi-kql-investigation.md      ← MI KQL 标准交互流程 + 调查 SOP
├── mi-kql-extraction-pipeline.md ← KQL 模板提取流程（8 步 pipeline）
├── nys-analysis.md              ← Non-Yielding Scheduler 分析 Skill
├── pr-tracking.md               ← PR/CU/Branch 追踪 Skill
└── report-rules.md              ← 报告生成规则（3 种格式）

agents/skills/kql-templates/     ← KQL 模板库
├── SQLClusterMappings.csv       ← 55 region 主集群映射
├── SQLClusterMappings.Followers.csv  ← 55 region 只读集群映射
├── mi-tables-reference.md       ← 133+ 表完整 Schema
├── mi-tables-code-reference.md  ← 143+ 表代码级定义
├── mi-tables-relationship.html  ← 核心表关联图（可视化）
├── mi/                          ← MI KQL 模板（1224 个）
│   ├── performance/             ← 266 个 (CPU/内存/IO/阻塞/QDS)
│   ├── backup-restore/          ← 486 个 (备份/恢复/PITR/LTR)
│   ├── availability/            ← 273 个 (故障转移/FOG/恢复/Seeding)
│   ├── networking/              ← 131 个 (连接/网关/代理/AAD)
│   ├── replication/             ← 27 个 (事务复制/CDC/CT)
│   └── general/                 ← 41 个 (MI信息/计费/治理)
└── sqldb/                       ← SQL DB KQL 模板（31 个 YAML）

scripts/                         ← 工具脚本
├── extract_kql.py               ← KQL 提取脚本（从 TSG repo → YAML）
└── cleanup_broken.py            ← 清理 broken KQL entries

agents/outcome/                  ← Agent 分析产出（报告/HTML）
agents/errorcode_research/       ← 错误码研究报告
```

## MI KQL 标准交互流程

```
用户: "帮我查 {问题描述}"
  → Step 1: 收集参数（ServerName, Region, TimeRange）
  → Step 2: 搜本地 YAML 模板 → TSG repo → enghub/csswiki → AI 生成
  → Step 3: 展示 KQL 查询，等用户确认 ⚠️
  → Step 4: 用户确认后执行（跨 region 自动跟进）
  → Step 5: 结构化分析（Conclusion + Anomalies + Next Steps）
```

详见 [mi-kql-investigation.md](agents/skills/mi-kql-investigation.md)

## MCP 服务器

| Server | 类型 | 用途 |
|--------|------|------|
| `csswiki` | local (ADO) | Supportability Wiki 搜索 |
| `msdata` | local (ADO) | msdata ADO（代码/Wiki/工作项） |
| `mssql` | local | 本地 SQL Server 查询 |
| `enghub` | stdio | EngHub 文档搜索 |
| `azure-mcp` | stdio | Azure Kusto 查询执行 |
| `microsoft-learn` | http | Microsoft Learn 文档 |
| `dri-copilot` | http | SQL DRI Copilot（待服务端授权） |

## 数据来源

### KQL 模板
| 来源 | 数量 |
|------|------|
| asmi-troubleshooter-package | 355 |
| TSG-SQL-MI-BackupRestore | 437 |
| TSG-SQL-MI-Availability | 220 |
| TSG-SQL-MI-Networking | 110 |
| TSG-SQL-MI-Performance | 75 |
| **合计** | **1197** |

### 表定义
- **Schema 来源**: `sqlazureeas2follower.eastasia.kusto.windows.net/sqlazure1`
- **代码来源**: `SqlTelemetry`, `DsMainDev`, `AzureSQLTools`, `SQLLivesiteAgents` 仓库
- **架构参考**: SQL DRI Copilot (`DRICopilot` 仓库)

## 已验证的调查 SOP

| 场景 | 状态 | 文件 |
|------|------|------|
| FOG Seeding 调查 | ✅ 已验证 | mi-kql-investigation.md |
| Errorlog 调查 | 📝 待补充 | — |
| Performance 调查 | 📝 待补充 | — |
| Backup 调查 | 📝 待补充 | — |
| Connectivity 调查 | 📝 待补充 | — |

## 依赖

- GitHub Copilot CLI v1.0.37+
- Node.js（ADO MCP 需要 npx）
- Azure CLI（Kusto 查询认证）
- Python 3.x + PyYAML（KQL 提取脚本）
