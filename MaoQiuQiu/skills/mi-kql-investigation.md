# MI KQL Investigation Skill
# This skill defines how to find and execute KQL queries for SQL Managed Instance troubleshooting.

## Interactive KQL Investigation Flow

When the user asks to investigate an MI issue using Kusto/KQL, follow this **standard interaction flow**:

```
用户: "帮我查 {问题描述}"
  ↓
Step 1: 收集参数
  → ask_user: ServerName, Region, TimeRange
  → 如果用户不确定 region: 用 sqladhoc 自动查
  ↓
Step 2: 查找 KQL 模板
  → 搜本地 YAML → 搜本地 TSG repo → 搜 enghub/csswiki → AI 生成（兜底）
  ↓
Step 3: 展示查询，等用户确认 ⚠️ 关键步骤
  → 展示: 集群 URL + 完整 KQL（参数已填充）
  → 问: "要执行吗？还是需要调整？"
  → 用户可以: 确认执行 / 要求修改 / 自己复制去跑
  ↓
Step 4: 用户确认 → 执行
  → 执行 KQL，如有跨 region 需要自动跟进（不需再次确认）
  ↓
Step 5: 结构化分析
  → Conclusion + Rationale + Anomalies + Trends + Next Steps
```

**核心原则：**
- **永远先展示 KQL 再执行** — 让用户有机会 review 和修改
- **跨 region 跟进不需要再次确认** — 属于同一调查的延续
- **错误时自动修复并重新展示** — 不是静默重试

### Step 1: Gather Required Parameters
**Always ask the user for these before proceeding:**

1. **Server Name** — MI name (LogicalServerName), e.g. `dlinger`
2. **Region** — Azure region where the MI is located, e.g. `East Asia`
3. **Time Range** — How far back to look, e.g. `1h`, `24h`, `7d`, or specific datetime range

Use `ask_user` to collect these. Example:
```
"请提供以下信息：
 - MI server name
 - Region (如 eastasia, westeurope)
 - 时间范围 (如 最近1小时, 最近24小时, 或具体时间段)"
```

If the user doesn't know the region, use the global `sqladhoc` cluster to discover it:
```kql
// Auto-discover region (run on sqladhoc)
MonManagedServers
| where name =~ "{ServerName}"
| summarize arg_max(TIMESTAMP, *)
| project name, state, region = private_cluster_tenant_ring_name, edition, vcore_count
```
Then parse `private_cluster_tenant_ring_name` (e.g. `tr4923.eastasia1-a`) to determine the region.

### Step 2: Find KQL Template

**2a. Search Local YAML Templates (Fastest)**
```
~/.copilot/agents/skills/kql-templates/mi/
├── performance/performance.yaml      (CPU, memory, IO, blocking, deadlock, QDS, tempdb)
├── backup-restore/backup-restore.yaml (backup, restore, PITR, LTR, replication, CDC)
├── availability/availability.yaml    (failover, FOG, recovery, dump, errorlog, seeding, provisioning)
├── networking/networking.yaml        (connectivity, gateway, proxy, AAD, VNet, login)
└── general/general.yaml              (MI info, billing, governance, management operations)
```
Use `grep` to search by keyword across all YAML files:
```
grep -i "keyword" ~/.copilot/agents/skills/kql-templates/mi/**/*.yaml
```
If an exact or close match is found → extract the `ExecutedQuery` → proceed to Step 3.

**2b. Fallback — Search MI TSG Documentation**
If local templates don't have a good match, search MI documentation sources:

**MI Document Scope（合并 CSS Wiki scope 5 + msdata scope 7/8）：**

| # | 来源 | 工具 | 搜索范围 |
|---|------|------|----------|
| **CSS Wiki（Supportability org）** |
| 1 | CSS Wiki: AzureSQLMI | `csswiki-search_wiki` project=["AzureSQLMI"] | 支持团队的 MI TSG 和 case 经验 |
| **msdata Wiki（Database Systems org）** |
| 2 | msdata Wiki: TSG-SQL-MI-BackupRestore | `msdata-search_wiki` wiki=["TSG-SQL-MI-BackupRestore"] | 工程团队的备份恢复 TSG |
| 3 | msdata Wiki: TSG-SQL-MI-Availability | `msdata-search_wiki` wiki=["TSG-SQL-MI-Availability"] | 工程团队的可用性 TSG |
| 4 | msdata Wiki: TSG-SQL-MI-Networking | `msdata-search_wiki` wiki=["TSG-SQL-MI-Networking"] | 工程团队的网络 TSG |
| 5 | msdata Wiki: TSG-SQL-MI-Performance | `msdata-search_wiki` wiki=["TSG-SQL-MI-Performance"] | 工程团队的性能 TSG |
| 6 | msdata Wiki: TSG-SQL-MI-TransactionalReplication | `msdata-search_wiki` wiki=["TSG-SQL-MI-TransactionalReplication"] | 工程团队的事务复制 TSG |
| 7 | msdata Wiki: Database Systems.wiki | `msdata-search_wiki` | MI Provisioning TSG 等 |
| **msdata Code（Database Systems org）** |
| 8 | msdata Code: TSG-SQL-MI-* repos | `msdata-search_code` repository=["TSG-SQL-MI-BackupRestore","TSG-SQL-MI-Availability","TSG-SQL-MI-Networking","TSG-SQL-MI-Performance","TSG-SQL-MI-TransactionalReplication"] | TSG 源码中的 KQL |
| 9 | msdata Code: TSG-SQL-DB-GeoDr | `msdata-search_code` repository=["TSG-SQL-DB-GeoDr"] | MI Failover Group TSG |
| **EngHub** |
| 10 | EngHub MI docs | `enghub-search` query="SQL Managed Instance {topic}" | EngHub 上的 MI 文档 |

**msdata MI TSG Repos 完整列表：**
```
msdata.visualstudio.com/Database Systems/_git/
├── TSG-SQL-MI-Availability             (MI 可用性)
├── TSG-SQL-MI-BackupRestore            (MI 备份恢复)
├── TSG-SQL-MI-Networking               (MI 网络)
├── TSG-SQL-MI-Performance              (MI 性能)
├── TSG-SQL-MI-TransactionalReplication (MI 事务复制)
├── TSG-SQL-MIRS                        (MI RS)
├── TSG-SQL-DB-GeoDr                    (GeoDR/FOG，含 MI 部分)
└── TSG-SQL-DB-DataIntegration          (数据集成，含 Hyperscale MI)
```

**2c. Last Resort — AI Generate with Schema Reference**
If no template found, generate KQL using:
- Table schema from `~/.copilot/agents/skills/kql-templates/mi/mi-tables-reference.md` (148 tables, all columns)
- Table code definitions from `~/.copilot/agents/skills/kql-templates/mi/mi-tables-code-reference.md`
- Always verify column names against schema before generating

### Step 3: Determine Cluster Endpoint
Look up the region in the cluster mapping CSV:
```
grep "{region}" ~/.copilot/agents/skills/kql-templates/shared/SQLClusterMappings.Followers.csv
```
- Prefer **Follower** clusters (read-only, lower load) for ad-hoc queries
- Use **Primary** clusters only if Follower returns no data or for real-time needs
- All clusters use database `sqlazure1` (shared by SQL DB and MI)

### Step 4: Present Query for User Review
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
- **确认执行** → proceed to Step 5
- **要求修改** → adjust query and re-present
- **自己去跑** → user copies the query to Kusto Web Explorer

### Step 5: Execute Query
Execute using `azure-mcp kusto_query` with the cluster-uri and database from Step 3.

**Query safety checks before execution:**
- Ensure `| take N` or time filter exists (prevent full table scan)
- Ensure time range is not too wide (>30d may timeout)
- Verify cluster URI includes `:443/sqlazure1`

### Step 6: Handle Errors
- **Column not found (SEM0100)**: Query table schema with `getschema`, fix column names, re-present fixed query to user
- **No data returned**: Suggest trying primary cluster, wider time range, or different table
- **403/Auth error**: Verify cluster URI format
- **Timeout**: Narrow time range or add more filters

### Step 7: Analyze Results
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

**TODO**: Record after testing

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
