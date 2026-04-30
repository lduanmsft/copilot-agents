# SQL DB KQL Template Extraction Pipeline

当需要从新的 SQL DB TSG repo 或 Dashboard 提取 KQL 模板时，按此流程执行。

## 前置条件
- TSG repo 已 clone 到 `~/repos/db-tsg/`
- Python 3.x + PyYAML 已安装
- azure-mcp kusto 可用
- msdata MCP 可用
- Dashboard JSON 文件已下载（如有）

## 与 MI Pipeline 的关键差异

| 维度 | MI | SQL DB |
|------|-----|--------|
| TSG repos | 6 个（mi-tsg/） | 10 个（db-tsg/） |
| 额外来源 | 无 | Dashboard JSON 文件 |
| YAML 格式 | 自定义 | DRI Copilot SqlSkills 格式 |
| AppTypeName | `Worker.CL`, `Worker.CL.WCOW.SQL22` | `Worker.ISO`, `Worker.ISO.Premium`, `Worker.DW` |
| 过滤维度 | instance 级（LogicalServerName = MI 名） | database 级（LogicalServerName + DatabaseName） |
| 表 | 136 MI 专有 | 105 共享 + 126 DB-only = 234 |
| Kusto DB | sqlazure1（共享） | sqlazure1（共享） |

---

## Step 1: Clone TSG Repos

```bash
cd ~/repos/db-tsg
```

### 10 个 DB TSG Repos

| Repo | 来源 | 内容 |
|------|------|------|
| AzureSQLDB | CSS Wiki | CSS 工程师共享 KQL/TSG |
| TSG-SQL-DB-Availability | msdata | 可用性 TSG |
| TSG-SQL-DB-Connectivity | msdata | 连接性 TSG（含 14 个可执行 TSG） |
| TSG-SQL-DB-DataIntegration | msdata | 数据集成 TSG（含 38 个可执行 TSG） |
| TSG-SQL-DB-GeoDr | msdata | Geo-DR TSG（含 fetch-tsg, execute-tsg skills） |
| TSG-SQL-DB-Native | msdata | Native/平台 TSG |
| TSG-SQL-DB-Performance | msdata | 性能 TSG |
| TSG-SQL-DB-QueryStore | msdata | Query Store TSG |
| TSG-SQL-DB-RG | msdata | Resource Governance TSG |
| TSG-SQL-DB-Telemetry | msdata | 遥测/监控 TSG |

```bash
# Clone all
for repo in AzureSQLDB TSG-SQL-DB-Availability TSG-SQL-DB-Connectivity TSG-SQL-DB-DataIntegration TSG-SQL-DB-GeoDr TSG-SQL-DB-Native TSG-SQL-DB-Performance TSG-SQL-DB-QueryStore TSG-SQL-DB-RG TSG-SQL-DB-Telemetry; do
    git clone "https://msdata.visualstudio.com/Database%20Systems/_git/$repo"
done
```

## Step 2: 提取 KQL → 生成 YAML 模板

### 2a. 从 TSG Markdown 提取

使用 `~/.copilot/scripts/extract_kql.py`，和 MI 相同的提取逻辑。

```bash
python extract_kql.py --repo ~/repos/db-tsg/{RepoName} --category {category-name}
```

### 2b. 从 Dashboard JSON 提取

Dashboard 文件是 Azure Data Explorer Dashboard 导出的 JSON，结构：
- `queries[]`: `{id, text, usedVariables[], dataSource}` — KQL 查询
- `tiles[]`: `{id, title, pageId, queryRef:{queryId}}` — 可视化瓦片（标题在这里）
- `pages[]`: `{id, title}` — 页面
- `parameters[]`: `{id, displayName, variableName}` — Dashboard 参数

```bash
python extract_dashboard_kql.py
```

Dashboard 特有：
- 用 `_variableName` 格式的参数（`_startTime`, `_logicalServerName`）
- 用 `cluster(clstr).database("sqlazure1").MonXxx` 模式（跨集群查询）
- 用 `_ExecuteForProdClusters` 宏（遍历所有 prod 集群）
- 标题从 `tiles` 的 `title` 字段获取（`pages` 通常为空）

### 输出 YAML 格式（SqlSkills 格式）

```yaml
SqlSkills:
- id: DB-{category}-{n}
  Topic: {source filename without .md}
  Source: {RepoName}/{relative_path}
  Prompts:
  - {自然语言描述 query 用途}
  - {表名 + 关键列名}
  - {调查场景}
  CustomizedParameters:
  - ServerName
  - DatabaseName
  KustoQueries:
  - TableName: {主表名}
    ExecutedQuery: '{参数化后的完整 KQL}'
    DisplayedQuery: '{显示用的 KQL（可选）}'
    EvaluationTrueMessage: '{查到数据时的提示（可选）}'
    EvaluationFalseMessage: '{没查到数据时的提示（可选）}'
```

### 保存位置
```
~/.copilot/agents/skills/kql-templates/sqldb/{category}/{category}.yaml
~/.copilot/agents/skills/kql-templates/sqldb/dashboard.yaml
```

### 参数化规则

和 MI 完全相同，参考 `mi-kql-extraction-pipeline.md` Step 2 的完整映射表。

额外注意 Dashboard 的 `_variableName` 格式保持原样（不转换为 `{param}`），因为 Dashboard 查询设计为在 Dashboard 内使用。

## Step 3: 列出所有使用的表

```powershell
# SqlSkills 格式
Select-String -Path $yamlFile -Pattern "TableName: (\w+)" |
  ForEach-Object { $_.Matches[0].Groups[1].Value } |
  Sort-Object -Unique

# Dashboard 格式
Select-String -Path dashboard.yaml -Pattern "\b(Mon[A-Z]\w+|Alr[A-Z]\w+)" |
  ForEach-Object { $_.Matches } | ForEach-Object { $_.Value } |
  Sort-Object -Unique
```

注意区分：
- 105 个共享表（MI 和 DB 都有）→ schema 已在 `mi-tables-reference.md`
- DB-only 表 → 需要新拉 schema，写入 `db-tables-reference.md`

## Step 4: 获取表 Schema

```
azure-mcp-kusto kusto_table_schema
  cluster-uri: https://sqlazureeas2follower.eastasia.kusto.windows.net:443
  database: sqlazure1
  table: {TableName}
```

每批 5 个表并行查询。结果追加到：
```
~/.copilot/agents/skills/kql-templates/sqldb/db-tables-reference.md
```

对于找不到的表（返回空 schema），可能是：
- 函数/视图（用 `.show functions | where Name == 'xxx'` 查）
- Dashboard 里的计算列/别名（如 `MonLoginTime`, `MonRedirectorTime`）
- 已废弃的表
- 记录在 "Tables Not Found" section

## Step 5: 研究表的代码定义

```
msdata-search_code
  searchText: {TableName}
  project: "Database Systems"
  top: 3
```

DB 特有的代码位置：
- `SqlTelemetry` → MDS Runner（`.cs`）
- `TSG-SQL-DB-Telemetry` → MDS Agent Config（`MonitoringSqlMDSAgentConfig_template`）
- `SqlLivesiteCopilot` / `SQLLivesiteAgents` → DRI Copilot skills（参考用）
- `MDM_SQL_AzureDBProduction` → 其他 Dashboard（参考用）

结果追加到：
```
~/.copilot/agents/skills/kql-templates/sqldb/db-tables-code-reference.md
```

## Step 6: 画表关联关系图

DB 维度和 MI 不同：
- **Server 维度**: LogicalServerName / logical_server_name
- **Database 维度**: logical_database_name / DatabaseName / database_id / logical_database_guid
- **Elastic Pool 维度**: elastic_pool_name / vldb_pool_id
- **Gateway 维度**: ClusterName (Gateway cluster, 不是 backend)
- **Node 维度**: AppName / NodeName（backend worker）
- **Subscription 维度**: SubscriptionId / subscription_id

生成到：
```
~/.copilot/agents/skills/kql-templates/sqldb/db-tables-relationship.html
```

## Step 7: KQL Lint（阻塞步骤）

**和 MI 完全相同的 12 类检查（A1-A12）**，参考 `mi-kql-extraction-pipeline.md` Step 7。

SQLDB 额外注意：
- DRI Copilot 原始 SqlSkills YAML 质量较高（~90% 可用），但仍需检查 A5（尾逗号）和 A7（bold `**`）
- Dashboard 提取的查询通常没有裸变量问题（用 `_variableName` 格式）
- Dashboard 查询通常更长（跨集群 + union），语法问题较少

### 审计脚本
```bash
python ~/.copilot/scripts/audit_sqldb_kql.py
```

### 已知 SQLDB 审计结果（2026-04-30）
- 4,293 skills, 0 duplicates
- A1-A7: 全部修复到 0
- H1 硬编码 GUID: 242（不修，TSG 示例值）
- 质量: ~95% 直接可用

## Step 8: 给每个 query 打 Prompt

和 MI 相同规则，参考 `mi-kql-extraction-pipeline.md` Step 8。

SQLDB 的 DRI Copilot 格式已经自带 Prompts，通常不需要重新生成。
Dashboard 提取的查询需要生成 Prompt（从 tile title + query content 推断）。

---

## 完整流程示例（以 Connectivity 为例）

```
1. git clone .../TSG-SQL-DB-Connectivity          → 200+ .md files
2. python extract_kql.py --repo ... --category connectivity  → connectivity.yaml (306 skills)
3. 提取表名 → MonLogin, MonRedirector, MonLoginDispatcherPool, ...
4. kusto_table_schema → 追加到 db-tables-reference.md
5. msdata-search_code → 追加到 db-tables-code-reference.md
6. 分析 join 关系 → 更新 db-tables-relationship.html
7. 审计 → 修复语法，删除 broken
8. 打 Prompt → 更新 YAML Prompts 字段
```

## Dashboard 提取流程示例

```
1. 下载 Dashboard JSON 到 ~/Downloads/
2. python extract_dashboard_kql.py              → dashboard.yaml (394 skills)
3. 跨格式去重（vs 已有 TSG yaml）             → 330 net new
4. 提取新表名（25 个新表）
5. kusto_table_schema → 20 个有物理表，5 个不存在
6. msdata-search_code → 追加 code definitions
7. 审计 → 修复
```

## 当前统计

| 来源 | Skills | 文件 |
|------|--------|------|
| TSG 10 repos | 3,899 | 10 个子目录 yaml |
| Dashboard x2 | 394 | dashboard.yaml |
| **Total** | **4,293** | 11 个 yaml 文件 |
| 表 schema | 234 | db-tables-reference.md (1.3MB) |
| 代码定义 | 54 | db-tables-code-reference.md (49KB) |
| 集群映射 | 55 regions | SQLClusterMappings.csv (共享) |

## 相关文件
- 提取脚本: `~/.copilot/scripts/extract_kql.py`
- Dashboard 提取: `~/.copilot/scripts/extract_dashboard_kql.py`
- KQL 模板: `~/.copilot/agents/skills/kql-templates/sqldb/`
- 表 Schema: `sqldb/db-tables-reference.md`
- 代码参考: `sqldb/db-tables-code-reference.md`
- 关联图: `sqldb/db-tables-relationship.html`
- 审计参考: `mi-kql-extraction-pipeline.md` Step 7（错误模式清单共用）
- 调查流程: `~/.copilot/agents/skills/db-kql-investigation.md`
