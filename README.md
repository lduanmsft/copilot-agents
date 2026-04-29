# Copilot Agents & MI KQL Investigation Framework

SQL Managed Instance 调查工具集，基于 GitHub Copilot CLI 和 MCP 服务器构建。

## 架构

```
copilot-instructions.md          ← 全局指令（路由规则、行为规范）
mcp-config.json                  ← MCP 服务器配置

agents/                          ← 自定义 Agents
├── lduan-agent.agent.md         ← 主 Agent（错误码/callstack/MI 调查）
├── callstack-research.agent.md  ← Callstack 分析 Agent
├── errorcode-research.agent.md  ← SQL 错误码深度研究 Agent
├── search-csswiki.agent.md      ← CSS Wiki 搜索 Agent
├── search-enghub.agent.md       ← EngHub 搜索 Agent
├── search-github.agent.md       ← GitHub 搜索 Agent
├── search-msdata.agent.md       ← msdata ADO 搜索 Agent
└── search-web.agent.md          ← Web 搜索 Agent

agents/skills/                   ← Skills（可复用的调查流程）
├── mi-kql-investigation.md      ← MI KQL 标准交互流程 + 调查 SOP
├── nys-analysis.md              ← Non-Yielding Scheduler 分析
├── pr-tracking.md               ← PR/CU/Branch 追踪
└── report-rules.md              ← 报告生成规则

agents/skills/kql-templates/     ← KQL 模板库
├── SQLClusterMappings.csv       ← 55 region 主集群映射
├── SQLClusterMappings.Followers.csv  ← 55 region 只读集群映射
├── mi-tables-reference.md       ← 133 表完整 Schema（785 KB）
├── mi-tables-code-reference.md  ← 143 表代码级定义（154 KB）
├── mi-tables-relationship.html  ← 14 核心表关联图（可视化）
├── mi-tables-relationship.md    ← 关联关系 Markdown 版
├── mi-kql-audit-report.md       ← KQL 模板审计报告
├── mi/                          ← MI KQL 模板（1197 个）
│   ├── performance/             ← 266 个 (CPU/内存/IO/阻塞/QDS)
│   ├── backup-restore/          ← 486 个 (备份/恢复/PITR/LTR/复制)
│   ├── availability/            ← 273 个 (故障转移/FOG/恢复/Seeding)
│   ├── networking/              ← 131 个 (连接/网关/代理/AAD)
│   └── general/                 ← 41 个 (MI信息/计费/治理)
└── sqldb/                       ← SQL DB KQL 模板（31 个 YAML）

agents/outcome/                  ← Agent 分析产出（报告/文档）
agents/errorcode_research/       ← 错误码研究报告（HTML）
agents/search-results/           ← 搜索结果缓存
```

## MI KQL 标准交互流程

```
用户: "帮我查 {问题描述}"
  → Step 1: 收集参数（ServerName, Region, TimeRange）
  → Step 2: 搜本地 YAML 模板 → TSG repo → enghub/csswiki → AI 生成
  → Step 3: 展示 KQL 查询，等用户确认 ⚠️
  → Step 4: 用户确认后执行
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
| `azure-mcp` | stdio | Azure Kusto 查询 |
| `microsoft-learn` | http | Microsoft Learn 文档 |
| `dri-copilot` | http | SQL DRI Copilot（待服务端授权） |

## 数据来源

### KQL 模板来源
1. **asmi-troubleshooter-package** — CSS 工程师手写的 KQL 查询集（355 个）
2. **TSG-SQL-MI-BackupRestore** — 备份恢复 TSG（437 个）
3. **TSG-SQL-MI-Availability** — 可用性 TSG（220 个）
4. **TSG-SQL-MI-Networking** — 网络 TSG（110 个）
5. **TSG-SQL-MI-Performance** — 性能 TSG（75 个）

### 表定义来源
- **Kusto Schema**: `sqlazureeas2follower.eastasia.kusto.windows.net/sqlazure1`
- **源码**: `SqlTelemetry`, `DsMainDev`, `AzureSQLTools`, `SQLLivesiteAgents` 仓库
- **参考**: SQL DRI Copilot (`DRICopilot` 仓库) 的架构和 Prompt 设计

## 已验证的调查 SOP

### FOG Seeding 调查
```
MonGeoDRFailoverGroups（FOG 配置）
  → SQLClusterMappings.csv（Partner region 集群）
    → MonDbSeedTraces（Primary + Secondary 双端 seeding 进度）
      → 结构化分析
```

更多 SOP（Errorlog / Performance / Backup / Connectivity）待测试后补充。

## 依赖

- GitHub Copilot CLI v1.0.37+
- Node.js（ADO MCP 需要 npx）
- Azure CLI（Kusto 查询认证）
- Python 3.x + PyYAML（KQL 提取脚本）
