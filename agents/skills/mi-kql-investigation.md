# MI KQL Investigation Skill
# This skill defines how to find and execute KQL queries for SQL Managed Instance troubleshooting.

## Interactive KQL Investigation Flow

When the user asks to investigate an MI issue using Kusto/KQL, follow this **standard interaction flow**:

```
用户: "帮我查 {问题描述}"
  ↓
Step 1: 收集参数
  → ask_user: ServerName, Region, DatabaseName(可选), AppName(可选), TimeRange
  ↓
Step 1.5: 解析元数据
  → Region → 查 CSV 得到 Follower 集群 URL
  → 用 ServerName 在集群上查 MonManagedServers 获取:
    AppName(如果用户没提供), Edition, VCores, State, NodeName
  ↓
Step 2: 问题分类
  → 如果用户已明确说了问题类型（如 "high CPU"）→ 直接路由
  → 否则 ask_user 选择:
    A. Performance (CPU/内存/IO/blocking/查询/QDS/磁盘空间/编译)
    B. Availability (failover/FOG/seeding/dump/recovery)
    C. Backup & Restore (备份/还原/PITR/LTR)
    D. Networking (连接/gateway/AAD/proxy/login)
    E. Replication (事务复制/CDC/CT)
    F. General (管理操作/安全/billing/其他)
  → Performance 不追问子类别，由 KQL 模板搜索自动匹配
  ↓
Step 3: 查找 KQL + 搜索 TSG（并行）
  → 线路 1: 搜本地 YAML → P1(livesite/asmi) → P2(tsg) → 得到可执行 KQL
  → 线路 2: 搜 msdata TSG repo + CSS Wiki → 得到调查指南/最新 KQL/上下文
  → 合并: 本地 KQL 为主，TSG 补充调查思路和最新更新
  ↓
Step 4: 确定集群 URL
  → Region → 查 CSV 得到 Follower 集群 URL
  ↓
Step 5: 展示查询，等用户确认 ⚠️ 关键步骤
  → 展示: 集群 URL + 完整 KQL（参数已填充）
  → 问: "要执行吗？还是需要调整？"
  → 用户可以: 确认执行 / 要求修改 / 自己复制去跑
  ↓
Step 6: 用户确认 → 执行
  → 执行 KQL，如有跨 region 需要自动跟进（不需再次确认）
  ↓
Step 7: 错误处理
  → 列名错误: 查 schema 修正 / 无数据: 换集群或扩大时间范围
  ↓
Step 8: 结构化分析
  → Conclusion + Rationale + Anomalies + Trends + Next Steps
```

**核心原则：**
- **所有 KQL 都要先展示再执行** — 包括 triage 快速扫描、深入调查、跨 region 跟进，全部先展示让用户确认
- **错误时自动修复并重新展示** — 不是静默重试

### Step 1: Gather Required Parameters
**Always ask the user for these before proceeding:**

1. **Server Name** — MI name (LogicalServerName), e.g. `dlinger`
2. **Region** — Azure region, e.g. `eastasia`, `westeurope`
3. **Database Name** (optional) — specific database if relevant, e.g. `mydb`
4. **AppName** (optional) — MI 的 AppName hash，如果用户知道的话，e.g. `a703f2b710af`
5. **Time Range** — How far back to look, e.g. `1h`, `24h`, `7d`, or specific datetime range

Use `ask_user` to collect these. Example:
```
"请提供以下信息：
 - MI server name
 - Region (如 eastasia, westeurope)
 - 数据库名 (如果是特定数据库的问题)
 - AppName (如果知道的话，不知道我会自动查)
 - 时间范围 (如 最近1小时, 最近24小时, 或具体时间段)"
```

### Step 1.5: Auto-Resolve MI Metadata

**1.5a. 用 Region 查集群 URL：**

CSV 格式为 `[SQL] {Region}`，例如 `[SQL] East Asia`。

```bash
# 用户输入 "East Asia" → 搜 "[SQL] East Asia"
grep -i "East Asia" ~/.copilot/agents/skills/kql-templates/shared/SQLClusterMappings.Followers.csv
```
→ 得到 Follower 集群 URL，例如:
`https://sqlazureeas2follower.eastasia.kusto.windows.net:443/sqlazure1`

**1.5b. 在 regional 集群上查 MI 元数据（补全 AppName 等）：**

```kql
// Run on regional Follower cluster, database sqlazure1
MonManagedServers
| where name =~ "{ServerName}"
| summarize arg_max(TIMESTAMP, *) by name
| project 
    ServerName = name,
    AppName,                                    // ← 用于某些表的 filter fallback
    Region = private_cluster_tenant_ring_name,  // ← 验证 region 是否一致
    Edition = edition,                          // ← GeneralPurpose / BusinessCritical
    VCores = vcore_count,
    State = state,
    NodeName
```

**从结果中提取：**
- `AppName` — 如果用户没提供，保存用于后续 KQL filter fallback
- `Edition` — 判断 GP/BC，影响某些调查路径（如 GP 有 XStore IO 问题，BC 有 local SSD）
- `State` — 判断 MI 是否 Ready，Stopped 状态下查不到实时数据

**如果查不到数据：**
- 检查 ServerName 拼写
- 确认 Region 是否正确
- MI 可能刚创建或已删除

### Step 3: Find KQL + Search TSG（并行两条线）

**并行执行两条线路：**

#### 线路 1: 搜本地 YAML Templates（得到可执行 KQL）

按 Step 2 的分类定位目录，在对应目录下搜 KQL 模板：

```
~/.copilot/agents/skills/kql-templates/mi/
├── performance/                          ← A. Performance
│   ├── cpu/                              (kql-livesite.yaml, kql-asmi.yaml, kql-tsg.yaml, investigation.yaml)
│   ├── blocking/                         (同上)
│   ├── memory/                           ...
│   ├── queries/                          ...
│   ├── query-store/                      ...
│   ├── compilation/                      ...
│   ├── out-of-disk/                      ...
│   ├── io-storage/                       ...
│   ├── miscellaneous/                    ...
│   ├── node-health/                      ...
│   ├── corruption/                       ...
│   ├── fulltext/                         ...
│   └── sqlos/                            ...
├── availability/availability.yaml        ← B. Availability
├── backup-restore/backup-restore.yaml    ← C. Backup & Restore
├── networking/networking.yaml            ← D. Networking
├── replication/replication.yaml          ← E. Replication
└── general/general.yaml                  ← F. General
```

**搜索优先级：**
- **P1**: `kql-livesite.yaml` + `kql-asmi.yaml` — 工程团队模板 + MI 原生手工 KQL
- **P2**: `kql-tsg.yaml` — TSG 文档批量抽取的 KQL

```bash
# Performance: 在对应子目录搜
grep -i "keyword" ~/.copilot/agents/skills/kql-templates/mi/performance/**/*.yaml

# 非 Performance: 在对应分类文件搜
grep -i "keyword" ~/.copilot/agents/skills/kql-templates/mi/{category}/{category}.yaml
```

If match found → extract `ExecutedQuery` → fill parameters → proceed to Step 5.

#### 线路 2: 搜 msdata TSG Repos + CSS Wiki（得到调查指南和最新 KQL）

**与线路 1 并行执行。**目的：
- 获取最新调查指南（TSG 可能已更新，本地 YAML 是静态快照）
- 获取调查上下文、阈值判断标准、下一步建议
- 如果本地没有匹配的 KQL，从 TSG 中提取

按问题分类**只搜对应的** msdata TSG repo（不要全搜）：

| Step 2 分类 | 只搜这个 msdata TSG Repo | 搜索工具 |
|-------------|-------------------------|----------|
| **A. Performance** | [TSG-SQL-MI-Performance](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-MI-Performance) | `msdata-search_code` / `msdata-search_wiki` |
| **B. Availability** | [TSG-SQL-MI-Availability](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-MI-Availability) | `msdata-search_code` / `msdata-search_wiki` |
| **C. Backup & Restore** | [TSG-SQL-MI-BackupRestore](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-MI-BackupRestore) | `msdata-search_code` / `msdata-search_wiki` |
| **D. Networking** | [TSG-SQL-MI-Networking](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-MI-Networking) | `msdata-search_code` / `msdata-search_wiki` |
| **E. Replication** | [TSG-SQL-MI-TransactionalReplication](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-MI-TransactionalReplication) | `msdata-search_code` / `msdata-search_wiki` |
| **F. General** | [Database Systems Wiki](https://msdata.visualstudio.com/Database%20Systems/_wiki) | `msdata-search_wiki` |
| FOG/GeoDR | [TSG-SQL-DB-GeoDr](https://msdata.visualstudio.com/Database%20Systems/_git/TSG-SQL-DB-GeoDr) | `msdata-search_code` |

**同时搜 CSS Wiki**（所有分类都搜，不受 Step 2 限制）：
- `csswiki-search_wiki` project=["AzureSQLMI"] — CSS 支持团队的 MI TSG 和 case 经验

**合并两条线路的结果：**
- 本地 KQL 为主 → 填充参数后直接用
- TSG 补充：调查思路、结果解读、阈值判断、下一步建议
- 如果 TSG 里有更新的 KQL → 优先用 TSG 版本
- 如果本地没有匹配 → 用 TSG 里的 KQL

#### 兜底: AI Generate with Schema Reference
If no template found, generate KQL using:
- Table schema from `~/.copilot/agents/skills/kql-templates/mi/mi-tables-reference.md` (148 tables, all columns)
- Table code definitions from `~/.copilot/agents/skills/kql-templates/mi/mi-tables-code-reference.md`
- Always verify column names against schema before generating

### Step 4: Determine Cluster Endpoint
集群 URL 已在 Step 1.5a 通过 Region 查 CSV 获得。

- Prefer **Follower** clusters (read-only, lower load) for ad-hoc queries
- Use **Primary** clusters only if Follower returns no data or for real-time needs
- All clusters use database `sqlazure1` (shared by SQL DB and MI)

### Step 5: Present Query for User Review
**DO NOT execute immediately.** Show the user:

1. **Cluster endpoint** being used
2. **Complete KQL query** with all parameters filled in
3. Ask: **"要执行这个查询吗？"**

Format:
```
集群: {cluster_url}
数据库: sqlazure1

查询:
｀｀｀kql
{complete KQL with parameters filled}
｀｀｀

要执行吗？还是需要调整？
```

The user may:
- **确认执行** → proceed to Step 6
- **要求修改** → adjust query and re-present
- **自己去跑** → user copies the query to Kusto Web Explorer

### Step 6: Execute Query
Execute using `azure-mcp kusto_query` with the cluster-uri and database from Step 3.

**Query safety checks before execution:**
- Ensure `| take N` or time filter exists (prevent full table scan)
- Ensure time range is not too wide (>30d may timeout)
- Verify cluster URI includes `:443/sqlazure1`

### Step 7: Handle Errors
- **Column not found (SEM0100)**: Query table schema with `getschema`, fix column names, re-present fixed query to user
- **No data returned**: Suggest trying primary cluster, wider time range, or different table
- **403/Auth error**: Verify cluster URI format
- **Timeout**: Narrow time range or add more filters

### Step 8: Analyze Results
Apply the DRI Copilot summarizer pattern:
- **Conclusion**: Healthy or issue detected
- **Rationale**: Why you reached that conclusion
- **Anomalies** (if detected): Timestamp, value, baseline, severity
- **Trends** (if detected): Increasing, decreasing, or cyclical patterns
- **Next Steps**: Suggest follow-up queries if needed

---

## Common Investigation Workflows

### FOG (Failover Group) Seeding Investigation

**Tested and verified on 2026-04-29 with dlinger (East Asia) → lduan-mi-sea (Southeast Asia)**

#### Interaction Flow

```
用户: "帮我检查 {ServerName} 最近 {TimeRange} 的 seeding"
  ↓
Step 1: 问 region
  → ask_user: "{ServerName} 在哪个 region？" (提供选项 + "我不确定，帮我查")
  → 如果用户不确定: 用 sqladhoc 集群自动查
  ↓
Step 2: 查 CSV 找集群 + 搜 YAML 找模板
  → grep SQLClusterMappings.Followers.csv 找集群 URL
  → grep availability.yaml 找 seeding 相关模板
  ↓
Step 3: 展示查询，等用户确认
  → 展示 2 个查询:
    查询 1: MonGeoDRFailoverGroups（FOG 配置）
    查询 2: MonDbSeedTraces（seeding 进度）
  → 问: "要执行吗？还是需要调整？"
  ↓
Step 4: 用户确认 → 执行
  → 并行执行 2 个查询
  → 从 FOG 配置结果中提取 PartnerRegion 和 PartnerServerName
  ↓
Step 5: 自动跨 region 查 Secondary
  → 用 PartnerRegion 查 CSV 找 Secondary 集群 URL
  → 在 Secondary 集群执行 MonDbSeedTraces 查询
  （不需要再次问用户确认，因为这是同一调查的延续）
  ↓
Step 6: 汇总分析
  → FOG 配置表（FOG Name, Policy, Role, Partner）
  → Seeding 活动表（时间, 数据库, 进度%, 速度, 状态, 端）
  → Conclusion: 是否有异常
  → Anomalies: 失败/慢速/卡住的 seeding
  → Next Steps: 如果有问题建议查什么
```

**Step 1: Gather parameters**
Ask user for: ServerName, Region, Time Range (e.g. 14d)

**Step 2: Check FOG Configuration (on Primary region)**
```kql
MonGeoDRFailoverGroups
| where logical_server_name =~ "{ServerName}"
| summarize arg_max(PreciseTimeStamp, *)
| project GroupId = failover_group_id, GroupName = failover_group_name,
    Policy = failover_policy, Server = logical_server_name,
    Role = role, PartnerRegion = partner_region,
    PartnerServer = partner_server_name
```
→ Get: partner_server_name, partner_region
→ If no results: MI has no FOG configured, investigation ends here

**Step 3: Query Seeding on Primary (Source) side**
```kql
MonDbSeedTraces
| where TIMESTAMP >= ago({TimeRange})
| where AppTypeName startswith "Worker.CL"
| where LogicalServerName =~ "{ServerName}"
| where event == 'hadr_physical_seeding_progress'
| extend transfer_rate_mb_per_second = round(transfer_rate_bytes_per_second / 1024.0 / 1024.0, 2)
| extend progress_pct = round(todouble(transferred_size_bytes) * 100.0 / todouble(database_size_bytes), 2)
| project originalEventTimestamp, database_name, progress_pct,
    transfer_rate_mb_per_second, internal_state_desc, role_desc
| order by originalEventTimestamp desc
| take 50
```

**Step 4: Switch to Partner Region Cluster**
Look up partner_region in `SQLClusterMappings.Followers.csv`
```
grep "{partner_region}" ~/.copilot/agents/skills/kql-templates/shared/SQLClusterMappings.Followers.csv
```

**Step 5: Query Seeding on Secondary (Destination) side**
Run the same MonDbSeedTraces query on the partner region cluster, replacing ServerName with PartnerServerName:
```kql
MonDbSeedTraces
| where TIMESTAMP >= ago({TimeRange})
| where AppTypeName startswith "Worker.CL"
| where LogicalServerName =~ "{PartnerServerName}"
| where event == 'hadr_physical_seeding_progress'
| extend transfer_rate_mb_per_second = round(transfer_rate_bytes_per_second / 1024.0 / 1024.0, 2)
| extend progress_pct = round(todouble(transferred_size_bytes) * 100.0 / todouble(database_size_bytes), 2)
| project originalEventTimestamp, database_name, progress_pct,
    transfer_rate_mb_per_second, internal_state_desc, role_desc
| order by originalEventTimestamp desc
| take 50
```

**Step 6: Analyze Results**
Cross-reference Source and Destination data:
- Match by timestamp — Source and Destination events should be within seconds of each other
- Check `internal_state_desc`:
  - `Success` → seeding completed normally
  - `Failure` → check `failure_message` and `failure_code`
  - `WaitingForRestoreToStart` / `WaitingForBackupToStartSending` → normal intermediate states
- Check transfer rate — typical MI seeding: 0.1-50 MB/s depending on network and DB size
- If progress_pct > 100% → normal for incremental seeding (transferred_size includes multiple rounds)
- If no seeding data at all → MI may be Stopped, or FOG was just created without initial sync yet

**Example output interpretation:**
```
4/17 05:53 | test02 | 2.75% | 0.22 MB/s (S) / 0.08 MB/s (D) | Success
→ Small database, seeding completed quickly. Speed difference between Source/Destination is normal (Source measures send rate, Destination measures receive+restore rate).
```
---

### Errorlog Investigation

**TODO**: Record after testing

### Performance Investigation

**当 Step 2 分类为 A. Performance 时的完整流程：**

```
Performance 问题
  ↓
Step 3a: 并行执行 triage 快速扫描（8 个维度）
  → 读 performance/triage.yaml → 并行跑 8 个轻量 KQL
  → 结果: 每个维度标记 🔴/🟡/🟢
  ↓
Step 3a-result: 展示总览表 + 选择深入方向
  | 维度 | 状态 | 关键指标 |
  |------|------|----------|
  | CPU  | 🔴   | max=92%  |
  | Blocking | 🟢 | 0 events |
  | ... | ... | ... |
  → 问用户:
    A. 深入调查 triage 异常项（自动列出 🔴🟡 的维度）
    B. 选择其他方向: CPU/Blocking/Memory/Queries/QDS/Compilation/IO/Disk/Misc/SQLOS
  ↓
Step 3b: 深入调查
  → 加载用户选择的子目录的 kql-livesite.yaml + kql-asmi.yaml
  → 填充参数 → 展示 KQL
  ↓
同时 线路 2 搜 TSG-SQL-MI-Performance repo（并行）
```

**triage.yaml 位置**: `~/.copilot/agents/skills/kql-templates/mi/performance/triage.yaml`

**8 个快速扫描维度**:

| # | 维度 | 表 | 阈值 | 深入目录 |
|---|------|-----|------|---------|
| 1 | CPU | MonDmRealTimeResourceStats | max > 80% | cpu/ |
| 2 | Blocking | MonBlockedProcessReportFiltered + MonDeadlockReportsFiltered | count > 0 | blocking/ |
| 3 | Memory | MonSQLSystemHealth | OOM events > 0 | memory/ |
| 4 | Wait Stats | MonDmCloudDatabaseWaitStats | informational | queries/ |
| 5 | Disk | MonManagedInstanceResourceStats | usage > 90% | out-of-disk/ |
| 6 | Query Store | MonQueryStoreInfo | readonly | query-store/ |
| 7 | Errors | AlrSQLErrorsReported | severity >= 17 | miscellaneous/ |
| 8 | Failover | MonManagementOperations | any event | miscellaneous/ |

**深入调查时的 KQL 文件优先级**:
- **P1**: `kql-livesite.yaml` + `kql-asmi.yaml` (工程团队 + MI 原生)
- **P2**: `kql-tsg.yaml` (TSG 批量抽取)
- 每个子目录的 `investigation.yaml` 定义了步骤、阈值和分支逻辑

### Backup Investigation

**TODO**: Record after testing

### Connectivity Investigation

**TODO**: Record after testing

---

## Key MI Tables Reference

| Table | Purpose |
|-------|---------|
| MonManagedServers | MI instance metadata (state, SLO, config) |
| MonManagedInstanceResourceStats | Instance-level resource usage (CPU, memory, storage) |
| MonGeoDRFailoverGroups | FOG configuration and role |
| MonMIGeoDRFailoverGroupsConnectivity | FOG connectivity health |
| MonDbSeedTraces | Seeding progress and state transitions |
| MonAnalyticsDBSnapshot | Database state and properties |
| MonBackup | Backup history and metadata |
| MonDmRealTimeResourceStats | Real-time resource stats (CPU, IO, log write) |
| AlrSQLErrorsReported | SQL errorlog (error_number, severity, state) |
| MonSQLSystemHealth | System health XEvents (non-yielding, OOM, etc.) |
| MonLogin | Login activity and failures |
| MonManagement | Management operations (provisioning, failover, etc.) |
| MonWiQdsExecStats | Query Store execution stats |
| MonDmCloudDatabaseWaitStats | Wait statistics by database |

## MI-Specific Filter Patterns

- MI AppTypeName: `Worker.CL` or `Worker.CL.WCOW.SQL22`
- Filter by server: `LogicalServerName =~ "{ServerName}"` or `logical_server_name =~ "{ServerName}"`
- Filter by database: `logical_database_name =~ "{DatabaseName}"` or `database_name =~ "{DatabaseName}"`
- **AppName fallback**: 某些 MI 表的 LogicalServerName 可能为空，使用双 filter:
  `(LogicalServerName =~ '{ServerName}' or AppName =~ '{AppName}')`
- AppName 在 Step 1.5 自动获取，不需要用户手动提供
