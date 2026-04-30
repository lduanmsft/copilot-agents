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
Step 2: Find KQL template
  → Local YAML → TSG / wiki / code → AI generate as fallback
  ↓
Step 3: Determine cluster endpoint
  → Use SQLClusterMappings.csv / Followers mapping
  ↓
Step 4: Present query for review ⚠️ never execute without confirmation
  → Show cluster + database + complete KQL with parameters filled in
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
    edition, service_level_objective, failover_group_id, logical_resource_pool_id
```

If `DatabaseName` is unknown but the user knows the server, list databases first:
```kql
MonAnalyticsDBSnapshot
| where logical_server_name =~ "{ServerName}"
| summarize arg_max(TIMESTAMP, *) by logical_database_name
| project logical_database_name, state, edition, service_level_objective, region_name
| order by logical_database_name asc
```

## Step 2: Find KQL Template

### 2a. Search local templates first
Use local YAML / extracted skills first because they are fastest and usually already parameterized.

```text
~/.copilot/agents/skills/kql-templates/sqldb/
├── availability/              (771 skills)
├── connectivity/              (306 skills)
├── data-integration/          (471 skills)
├── geodr/                     (109 skills)
├── native/                    (173 skills)
├── performance/               (914 skills)
├── query-store/               (29 skills)
├── resource-governance/       (95 skills)
├── telemetry/                 (317 skills)
└── css-wiki/                  (728 skills)
```

Recommended search order:
1. Local YAML / extracted skill by topic and keyword
2. Local TSG content or extracted CSS wiki material
3. CSS Wiki / msdata / EngHub
4. AI-generated KQL using table schema references

### 2b. DB document scope (Mode D equivalent)

| Source | Tool | Scope |
|--------|------|-------|
| CSS Wiki: AzureSQLDB | `csswiki-search_wiki` | `project=["AzureSQLDB"]` |
| msdata: TSG-SQL-DB-* repos | `msdata-search_wiki` / `msdata-search_code` | DB engineering TSGs and KQL source |
| EngHub | `enghub-search` | `"Azure SQL Database {topic}"` |

Typical msdata repo families to search:
- `TSG-SQL-DB-Availability`
- `TSG-SQL-DB-Connectivity`
- `TSG-SQL-DB-GeoDr`
- `TSG-SQL-DB-Performance`
- `TSG-SQL-DB-QueryStore`
- `TSG-SQL-DB-ResourceGovernance`
- `TSG-SQL-DB-BackupRestore`
- `TSG-SQL-DB-DataIntegration`

### 2c. Last resort: AI-generate KQL
If no suitable template exists, generate KQL using:
- `~/.copilot/agents/skills/kql-templates/sqldb/db-tables-reference.md`
- `~/.copilot/agents/skills/kql-templates/sqldb/db-tables-list.txt`
- `~/.copilot/agents/skills/kql-templates/sqldb/db-tables-relationship.html`

Always verify actual column names before execution.

## Step 3: Determine Cluster Endpoint
Use the same cluster mapping source as MI:

```text
~/.copilot/agents/skills/kql-templates/shared/SQLClusterMappings.Followers.csv
```

Guidance:
- Prefer **Follower** clusters first for read-only investigations.
- Use **Primary** clusters only if the follower has no data or you need the freshest telemetry.
- Use database **`sqlazure1`**.
- The cluster choice is driven by **Region**.

## Step 4: Present Query for User Review
**Do not execute immediately.** Show the user:
1. Cluster endpoint
2. Database name (`sqlazure1`)
3. Complete KQL with parameters filled in
4. A clear confirmation question

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
Cluster: {cluster_url}
Database: sqlazure1

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
