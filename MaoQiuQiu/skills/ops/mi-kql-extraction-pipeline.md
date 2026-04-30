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
6. **参数化** — 替换硬编码值为 `{param}` 格式（见下方完整映射表）
7. **去重** — 精确归一化匹配（collapse whitespace → lowercase → 比较全文）
8. **独立性检查** — 每个 ExecutedQuery 必须可独立执行，所有 `let` 变量必须在同一 entry 内定义

### 参数化完整规则

#### 硬编码值替换
| TSG 中的写法 | 替换为 |
|-------------|--------|
| `<server_name>`, `<MI_name>`, `<MI name>`, `<sql_instance_name>` | `"{ServerName}"` |
| `<Databasename>`, `<DATABASE_ID>`, `<db guid>`, `<database_name>` | `"{DatabaseName}"` |
| `<ApplicationName>` | `"{AppName}"` |
| `<cluster_name>`, `<tenant-ring>`, `<tenant_ring>` | `"{ClusterName}"` |
| `<icm_start_time>`, `<startTime>`, `<start_time>` | `ago({TimeRange})` |
| `<endTime>`, `<end_time>` | `now()` |

#### 裸变量引用 → 必须有 let 声明
TSG markdown 中经常有 `let serverName = "my-server";` 后面跟查询体，提取时必须确保 let 和查询体在同一个 ExecutedQuery 内。如果 let 丢失了，必须补回：

| 裸变量名 | 补回的 let 语句 | 对应参数 |
|----------|---------------|---------|
| `serverName` | `let serverName = "{ServerName}";` | ServerName |
| `srv` | `let srv = "{ServerName}";` | ServerName |
| `server` | `let server = "{ServerName}";` | ServerName |
| `MIName` | `let MIName = "{ServerName}";` | ServerName |
| `instanceName` | `let instanceName = "{ServerName}";` | ServerName |
| `managedInstanceName` | `let managedInstanceName = "{ServerName}";` | ServerName |
| `miName` | `let miName = "{ServerName}";` | ServerName |
| `databaseName` | `let databaseName = "{DatabaseName}";` | DatabaseName |
| `dbName` | `let dbName = "{DatabaseName}";` | DatabaseName |
| `db` | `let db = "{DatabaseName}";` | DatabaseName |
| `appName` | `let appName = "{AppName}";` | AppName |
| `subscriptionId` | `let subscriptionId = "{SubscriptionId}";` | SubscriptionId |
| `tenantRing` | `let tenantRing = "{ClusterName}";` | ClusterName |
| `clusterName` | `let clusterName = "{ClusterName}";` | ClusterName |
| `ringName` | `let ringName = "{ClusterName}";` | ClusterName |
| `startTime` | `let startTime = ago({TimeRange});` | TimeRange |
| `endTime` | `let endTime = now();` | TimeRange |
| `dt` | `let dt = ago({TimeRange});` | TimeRange |
| `req_id` | `let req_id = "{RequestId}";` | RequestId |
| `serverId` | `let serverId = "{ManagedServerId}";` | ManagedServerId |

**判断方法**：如果变量在 `==`, `=~`, `!=`, `contains`, `has`, `between()` 等 operator 后面出现，且同一 ExecutedQuery 内没有对应的 `let var =` 声明，则必须补回 let。

#### 参数引号规则
- `== {ServerName}` ❌ → `== "{ServerName}"` ✅
- KQL 比较操作符后的字符串参数必须加引号
- `ago({TimeRange})` 不加引号（timespan 类型）

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

追加到 `~/.copilot/agents/skills/kql-templates/mi/mi-tables-reference.md`

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

追加到 `~/.copilot/agents/skills/kql-templates/mi/mi-tables-code-reference.md`

## Step 6: 画表关联关系图

基于表定义，分析 join 关系：
- **Instance 维度**: 哪些表通过 ServerName/LogicalServerName/server_name 关联
- **Database 维度**: 通过 database_name/logical_database_name/database_id
- **FOG 维度**: 通过 failover_group_id
- **Node 维度**: 通过 AppName/NodeName/ClusterName

生成 Mermaid ER 图，追加到：
- `~/.copilot/agents/skills/kql-templates/mi/mi-tables-relationship.md`（Markdown）
- `~/.copilot/agents/skills/kql-templates/mi/mi-tables-relationship.html`（可视化）

## Step 7: KQL Lint（阻塞步骤）

**这是阻塞步骤** — 不通过不能进入 Step 8。

### 7a. 语法检查（已知错误模式清单）

以下每一项都会导致 KQL 执行失败，必须在提取后立即检查和修复：

| # | 错误模式 | 示例 | 修复 | 影响 |
|---|---------|------|------|------|
| A1 | Operator 前后缺空格 | `whereAppName==`, `whereTIMESTAMP>=`, `byquery_id` | 加空格 | KQL PARSE ERROR |
| A2 | TableName: Unknown | 查询片段没有有效表引用 | 移除该 entry | 不可执行 |
| A3 | 参数占位符缺引号 | `== {ServerName}` | `== "{ServerName}"` | KQL PARSE ERROR |
| A4 | 查询截断/不完整 | `where name in (` 未闭合 | 移除该 entry | 不可执行 |
| A5 | project 末尾逗号 | `project col1, col2,` | 删除末尾逗号 | KQL PARSE ERROR: SYN0002 |
| A6 | 反引号包裹表名 | `` `MonBackup` `` | 去掉反引号 | KQL 不认反引号 |
| A7 | HTML/Markdown 残留 | `ADSNbsp`, `**bold**`, `\|---\|` | 移除 | 语法错误或脏数据 |
| A8 | 硬编码 GUID | `subscription_id == "abc-123-..."` | 替换为 `"{SubscriptionId}"` | 可执行但不可复用 |
| A9 | 裸变量引用无 let | `where LogicalServerName =~ serverName` | 补回 `let serverName = "{ServerName}";` | SEM0100: column not found |
| A10 | 角括号占位符 | `<server_name>`, `<MI_name>` | 替换为 `"{ServerName}"` | 静默返回 0 行（最危险） |
| A11 | 全注释查询 | 所有行以 `//` 开头 | 移除该 entry | 不可执行 |
| A12 | 跨 entry 依赖 | 引用其他 entry 的 `AllDatabases` 等中间结果 | 合并或内联 | 不可独立执行 |

### A10 特别说明（静默失败）
角括号占位符是最危险的错误：
```kql
// Agent 参数替换只认 {ServerName}，不认 <server_name>
// 查询带着字面量 "<server_name>" 发到 Kusto
// Kusto 不报错，但 where 条件过滤掉所有行
// 返回 0 行 — 工程师以为没有数据，实际上是参数没替换
```

### 7b. 完整性检查
1. **TableName 正确性** — YAML 中的 TableName 必须匹配 ExecutedQuery 中实际的第一个表
2. **可独立执行** — 查询不能引用其他 entry 定义的变量（`let` 必须在同一 entry 内）
3. **非注释** — 不能全是 `//` 注释行
4. **有效表引用** — 必须引用至少一个 Mon*/Alr* 表

### 7c. 去重（精确匹配）
1. 归一化：collapse whitespace → lowercase → 精确比较全文
2. 保留第一次出现，移除后续重复
3. **不要用首行匹配或 signature hash 做去重** — 会误删查同表但不同 filter 的查询
4. 教训：首行匹配曾误报 48.9% 重复率，实际精确重复只有 8.6%

### 7d. 抽样执行验证
- 随机抽取 10% 的查询在 Kusto follower 上执行
- 只验证语法正确性（加 `| take 0` 避免拉数据）
- 失败的查询标记为需要修复

### 7e. 修复脚本
所有修复脚本保存在 `~/.copilot/scripts/`：
- `fix_mi_kql.py` — Round 1: A1-A8 批量修复
- `fix_mi_remaining.py` — A5 尾逗号 + A10 角括号 + A9 裸变量
- `fix_all_undef_vars.py` — A9 全量裸变量修复（180 instances → 0）
- `fix_trailing_commas.py` — A5 精确修复（处理 YAML 引号边界）
- `dedup_mi_kql.py` — 精确去重
- `scan_undef_comprehensive.py` — 验证扫描（目标: 0 remaining）
- `audit_sqldb_kql.py` — SQLDB 全量审计

输出审计报告到 `~/.copilot/agents/skills/kql-templates/CC_audit_mi/`

## Step 8: 给每个 query 打 Prompt

基于表定义和 query 内容，给每个 skill 生成 2-3 个描述性 Prompt：

### Prompt 生成规则
1. **Prompt 1**: 自然语言描述 query 用途（如 "MI backup history and size by database"）
2. **Prompt 2**: 表名 + 关键列名（如 "MonBackup backup_type logical_database_name"）
3. **Prompt 3**: 调查场景（如 "Troubleshoot backup failures"）
4. 每个 prompt 不超过 60 字符
5. 至少一个 prompt 包含表名（方便 grep 搜索）
6. 包含 query 中实际使用的列名
7. **禁止从文件名生成 prompt** — 必须从查询内容推断

原地更新 YAML 文件的 Prompts 字段。

### 教训（2026-04-30 审计总结）

**错误根因**：
1. `is_valid_kql()` 太宽松 — 只检查"有 Mon 表 + 有管道符"，没检查语法完整性
2. Markdown → KQL 边界判断太粗 — 把多个独立查询片段合并成一个 entry
3. 参数化只做替换没做验证 — `{ServerName}` 替换后没检查引号
4. 去重用 signature hash — 误删了查同表但不同 filter 的查询
5. Prompt 从文件名生成 — "MI restore request status" 被复制到 56 个无关条目
6. 没有执行验证步骤 — 提取完从不在 Kusto 上跑一遍
7. 角括号占位符没处理 — `<server_name>` 不是 `{ServerName}`，agent 不认，静默返回 0 行
8. 裸变量引用没检测 — 180 个 entry 引用了没有 let 声明的变量，运行时 SEM0100 错误

**数量级**（MI 首次提取 → 审计修复）：
- 原始: 1,537 skills
- 移除 broken (A2/A4/A11): -63
- 移除重复 (7c): -123
- 语法修复 (A1/A3/A5/A6/A7): 351 fixes
- 角括号修复 (A10): 64 fixes
- 裸变量修复 (A9): 180 → 0 (补回 let 语句)
- Prompt 修正 (B1): 56 entries
- 代码参考修正: 12 fixes (3 表名拼写 + 6 列类型 + 3 虚构列)
- 最终: 1,351 skills, 0 syntax errors, 0 undefined vars

**参考报告**：
- `CC_audit_mi/kql-syntax-prompt-audit.md` — 原始审计
- `CC_audit_mi/remaining-fixes-required.md` — 为什么"low priority"是错的
- `CC_audit_mi/undefined-var-fix-guide.md` — 180 个裸变量逐条修复指南
- `CC_audit_mi/post-fix-audit-report.md` — 修复后审计报告
- `CC_audit_mi/validation-report.md` — 表存在性和列类型验证

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
- 提取脚本: `~/.copilot/scripts/extract_kql.py`
- Dashboard 提取: `~/.copilot/scripts/extract_dashboard_kql.py`
- 修复脚本: `~/.copilot/scripts/fix_mi_kql.py`, `fix_all_undef_vars.py`, `fix_trailing_commas.py`
- 审计脚本: `~/.copilot/scripts/audit_sqldb_kql.py`, `scan_undef_comprehensive.py`
- 去重脚本: `~/.copilot/scripts/dedup_mi_kql.py`
- KQL 模板: `~/.copilot/agents/skills/kql-templates/mi/` (MI), `sqldb/` (DB)
- 表 Schema: `mi-tables-reference.md` (MI), `db-tables-reference.md` (DB)
- 代码参考: `mi-tables-code-reference.md` (MI), `db-tables-code-reference.md` (DB)
- 关联图: `mi-tables-relationship.html` (MI), `db-tables-relationship.html` (DB)
- 审计报告: `CC_audit_mi/` (5 份报告)
- SQLDB 审计: `sqldb/sqldb-kql-audit-report.md`
