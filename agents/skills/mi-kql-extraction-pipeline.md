# MI KQL Template Extraction Pipeline

当需要从新的 TSG repo 提取 KQL 模板时，按此流程执行。

## 前置条件
- TSG repo 已 clone 到 `~/repos/mi-tsg/`
- Python 3.x + PyYAML 已安装
- azure-mcp kusto 可用
- msdata MCP 可用

---

## Step 1: Clone TSG Repo

```bash
cd ~/repos/mi-tsg
git clone https://msdata.visualstudio.com/Database%20Systems/_git/{RepoName}
```

确认文件数量：
```bash
Get-ChildItem {RepoName} -Recurse -Filter "*.md" | Measure-Object
```

## Step 2: 提取 KQL → 生成 YAML 模板

使用 `extract_kql_v2.py` 的提取逻辑。关键规则：

### 提取规则（从 asmi-troubleshooter-package 的 KQL 语法学习得来）
1. **合并 split code fence** — ` ```kusto ``` ` 只是格式标记，把内容拼回连续 KQL
2. **合并 let + 查询体** — `let ServerName = "xxx";` 和后面的 `MonBackup | where ...` 是一个完整查询
3. **去掉 prose** — 标题、链接、说明文字不是 KQL
4. **去掉 "Execute in [Web][Desktop]..."** 前缀
5. **有效 KQL 验证** — 必须包含 `Mon*/Alr*` 表引用 + `|` 管道操作符
6. **参数化** — 替换硬编码的 ServerName/DatabaseName 为 `{ServerName}/{DatabaseName}`
7. **去重** — 标准化空白后去掉重复查询

### 脚本模板
```python
# 参考 ~/repos/mi-tsg/extract_kql_v2.py
# 核心函数：
#   extract_kql_from_md(content) → List[str]  提取 KQL
#   extract_kql_from_ipynb(filepath) → List[str]  从 notebook 提取
#   is_valid_kql(query) → bool  验证有效性
#   parameterize(query) → str  参数化
#   extract_table_name(query) → str  提取主表名
```

### 输出 YAML 格式
```yaml
SqlSkills:
- id: MI-{category}-{n}
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
    ExecutedQuery: {参数化后的完整 KQL}
```

### 保存位置
```
~/.copilot/agents/skills/kql-templates/mi/{category}/{category}.yaml
```

## Step 3: 列出所有使用的表

从生成的 YAML 中提取所有唯一表名：
```powershell
Select-String -Path $yamlFile -Pattern "TableName: (\w+)" | 
  ForEach-Object { $_.Matches[0].Groups[1].Value } | 
  Sort-Object -Unique
```

## Step 4: 获取表 Schema

对每个表，从 Kusto 获取 schema：
```
azure-mcp-kusto kusto_table_schema
  cluster-uri: https://sqlazureeas2follower.eastasia.kusto.windows.net:443
  database: sqlazure1
  table: {TableName}
```

或批量获取（每批 5 个表）：
```kql
union 
  (Table1 | getschema | extend T='Table1'), 
  (Table2 | getschema | extend T='Table2'), 
  ...
| summarize Columns=make_list(ColumnName) by T
```

追加到 `~/.copilot/agents/skills/kql-templates/mi-tables-reference.md`

## Step 5: 研究表的代码定义

对每个表，在 msdata ADO 搜索源码定义：

```
msdata-search_code
  searchText: {TableName}
  project: "Database Systems"
  top: 3
```

关键文件通常在：
- `SqlTelemetry` 仓库 — MDS Runner 定义（`.cs` 文件）
- `BusinessAnalytics` 仓库 — Schema 定义（`.schema` 文件）
- `DsMainDev` 仓库 — Cosmos fetcher 脚本（`.script` 文件）
- `AzureSQLTools` 仓库 — 管理工具（`.cs` 文件）

找到定义文件后用 `msdata-repo_get_file_content` 读取，提取：
- 表的用途（哪个 Runner/组件生产数据）
- 数据来源（CMS snapshot / XEvent / Ring Buffer / MDS）
- 关键列的含义（从代码注释、变量名、查询使用方式推断）

### 输出格式
```markdown
## N. TableName — Short Description

### Definition
[表存什么数据，数据怎么来的]

### Code Source
- **Repository**: [repo name]
- **Key Files**: [file paths]
- **Data Origin**: [CMS / XEvent / MDS Runner / Ring Buffer]

### Key Columns
| Column | Type | Meaning | Code Source |
|--------|------|---------|-------------|
```

追加到 `~/.copilot/agents/skills/kql-templates/mi-tables-code-reference.md`

## Step 6: 画表关联关系图

基于表定义，分析 join 关系：
- **Instance 维度**: 哪些表通过 ServerName/LogicalServerName/server_name 关联
- **Database 维度**: 通过 database_name/logical_database_name/database_id
- **FOG 维度**: 通过 failover_group_id
- **Node 维度**: 通过 AppName/NodeName/ClusterName

生成 Mermaid ER 图，追加到：
- `~/.copilot/agents/skills/kql-templates/mi-tables-relationship.md`（Markdown）
- `~/.copilot/agents/skills/kql-templates/mi-tables-relationship.html`（可视化）

## Step 7: 审计提取的 KQL

验证每个 skill：
1. **TableName 正确性** — YAML 中的 TableName 是否匹配 ExecutedQuery 中实际的第一个表
2. **KQL 有效性** — 是否是完整可执行的查询（不是 prose/片段）
3. **参数化完整性** — 是否还有硬编码的 server/DB 名
4. **分类正确性** — 查询是否在正确的 category YAML 文件中

输出审计报告到 `~/.copilot/agents/skills/kql-templates/mi-kql-audit-v2.md`

## Step 8: 给每个 query 打 Prompt

基于表定义和 query 内容，给每个 skill 生成 2-3 个描述性 Prompt：

### Prompt 生成规则
1. **Prompt 1**: 自然语言描述 query 用途（如 "MI backup history and size by database"）
2. **Prompt 2**: 表名 + 关键列名（如 "MonBackup backup_type logical_database_name"）
3. **Prompt 3**: 调查场景（如 "Troubleshoot backup failures"）
4. 每个 prompt 不超过 60 字符
5. 至少一个 prompt 包含表名（方便 grep 搜索）
6. 包含 query 中实际使用的列名

原地更新 YAML 文件的 Prompts 字段。

---

## 完整流程示例（以 TransactionalReplication 为例）

```
1. git clone .../TSG-SQL-MI-TransactionalReplication     → 51 .md files
2. python extract → replication.yaml                      → N skills
3. 提取表名 → MonTranReplTraces, MonLogReaderTraces, ...
4. kusto_table_schema → 追加到 mi-tables-reference.md
5. msdata-search_code → 追加到 mi-tables-code-reference.md
6. 分析 join 关系 → 更新 relationship diagram
7. 审计 → 删除 broken, 修正 TableName
8. 打 Prompt → 更新 YAML Prompts 字段
```

## 相关文件
- 提取脚本: `~/repos/mi-tsg/extract_kql_v2.py`
- 清理脚本: `~/repos/mi-tsg/cleanup_broken.py`
- KQL 模板: `~/.copilot/agents/skills/kql-templates/mi/`
- 表参考: `~/.copilot/agents/skills/kql-templates/mi-tables-reference.md`
- 代码参考: `~/.copilot/agents/skills/kql-templates/mi-tables-code-reference.md`
- 关联图: `~/.copilot/agents/skills/kql-templates/mi-tables-relationship.html`
