---
name: gateway-health-and-rollout
description: 'Check Gateway health — login success rates, resource usage (CPU, memory, cache), redirector/fabric resolution health, and node-level anomalies. Automatically detects version transitions and compares metrics side-by-side when a rollout occurred. Use when asked to check gateway health, gateway login stats, gateway resource usage, gateway rollout validation, gateway version comparison, gateway redirector health, alias cache issues, fabric resolution failures, gateway performance after a deployment, or gateway health summary for a region/ring/server.'
---
# Gateway Health and Rollout

## Usage Scenarios

| Scenario | Example Prompt | What You Get |
|----------|---------------|-------------|
| **Health summary** | "Check gateway health for eastus1" | Login success rate, resource usage, redirector health, node anomalies for all clusters in the region |
| **Rollout validation** | "Validate the gateway rollout in swedencentral" | Side-by-side comparison of old vs new version across all metrics |
| **Ring-level check** | "Check health for cr22.useuapeast2-a" | Targeted health report for a single connectivity ring |
| **Server investigation** | "Check gateway health for myserver.database.windows.net" | Resolves the server's region/ring, then runs health check |
| **Custom time window** | "Gateway health for eastus2euap, past 14 days" | Same analysis with extended lookback |
| **Node-level drill-down** | "Any anomalous gateway nodes in westus2?" | Flags nodes with metrics >2σ from cluster baseline |

> The skill auto-detects version transitions. If a rollout happened in the time window, you get version comparison automatically — no need to specify.

## Overview

This skill checks Gateway health by querying Kusto telemetry tables for login success rates, resource usage, and redirector/fabric resolution health. Works for general health summaries of any region, ring, or server. When a code package version change is detected in the time window, it automatically runs side-by-side comparisons for both versions.

## When to Use

Use this skill when:
- Checking Gateway login success rate for a cluster
- Investigating Gateway resource usage (CPU, memory, thread count, cache entries)
- Validating a Gateway rollout by comparing metrics before and after the version change
- A code package version changed and you want to compare login and resource metrics for both versions
- Performing on-call health checks for Gateway nodes
- Asked about Gateway performance in the last 2 days
- Investigating alias cache refresh failures or ODBC connectivity issues
- Checking fabric resolution (SF partition lookup) health
- Diagnosing URI cache churn or lookup retry storms
- Investigating management service HTTP call latency from Gateway

## Prerequisites

### Required Information from Previous Steps

Before executing any Kusto queries in this skill, you **MUST** use the `execute-kusto-query` skill (`.github/skills/Common/execute-kusto-query/SKILL.md`) to determine the correct Kusto cluster and database for the target region.

- **kusto-cluster-uri**: Resolved via `execute-kusto-query` skill based on the cluster's region
- **kusto-database**: Resolved via `execute-kusto-query` skill (typically `sqlazure1`)

> **CRITICAL**: Do NOT hardcode or assume a Kusto cluster URI. Different regions route to different Kusto clusters (e.g., eastus1 → `sqlazureeus12`, swedencentral → `sqlazuresec`). Always resolve via `execute-kusto-query`.

### Required MCP Servers

- **Kusto MCP server**: For executing KQL queries (configured via `execute-kusto-query` skill)
- **ADO MCP server** (optional, for Step 7 config diff): Requires `@azure-devops/mcp` configured for `msdata`
- **bluebird-mcp** (optional, for Step 7 config diff): For fetching file content from DsMainDev repo

**Authentication**: Uses Azure CLI credentials. Run `az login` if not already authenticated.

---

## Workflow

### Step 1: Gather Input Parameters

The user must provide **at least one** of the following identifiers. Accept whichever is given:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| ClusterName | One of these three | — | Gateway cluster name (e.g., `cr15.eastus1-a.control.database.windows.net`) |
| Region | One of these three | — | Azure region keyword (e.g., `eastus1`, `swedencentral1`) |
| LogicalServerName | One of these three | — | SQL logical server name or FQDN (e.g., `myserver` or `myserver.database.windows.net`) |
| StartTime | No | `ago(2d)` | Start of analysis window. Accepts KQL `ago()` or `datetime()` |
| EndTime | No | `now()` | End of analysis window. Accepts KQL `ago()` or `datetime()` |
| TimeRange | No | `2d` | Alternative to StartTime/EndTime — lookback duration from now |
| AppTypeName | No | `Gateway` | Filter by SF app type (default: filters for Gateway app types) |

> **Input resolution priority**: If multiple identifiers are provided, prefer ClusterName > Region > LogicalServerName.
> **Time window**: If StartTime/EndTime are provided, use them. If only TimeRange is provided, use `ago(TimeRange)`. Default: `ago(2d)`.

---

### Step 2: Resolve Region and Kusto Cluster via execute-kusto-query

**MANDATORY**: Before running any Kusto queries, resolve the **region** and the correct **Kusto cluster URI** using the `execute-kusto-query` skill (`.github/skills/Common/execute-kusto-query/SKILL.md`).

Follow the appropriate path based on what the user provided in Step 1:

#### Path A: ClusterName provided
1. Extract the region from the cluster name: e.g., `cr15.eastus1-a.control.database.windows.net` → region = `eastus1`
2. Use the `execute-kusto-query` skill to resolve `kusto-cluster-uri` and `kusto-database` for that region
3. The provided ClusterName becomes the `<CLUSTER_NAME>` filter in all queries

#### Path B: Region provided (no ClusterName)
1. Use the `execute-kusto-query` skill to resolve `kusto-cluster-uri` and `kusto-database` for the given region
2. Discover Gateway clusters in that region by running:
   ```kql
   MonLogin
   | where TIMESTAMP > ago(<TimeRange>)
   | where AppTypeName has "Gateway"
   | where event == "process_login_finish"
   | where ClusterName has "control"
   | summarize LoginCount = count() by ClusterName
   | order by LoginCount desc
   | take 20
   ```
3. Present the discovered clusters to the user and ask which one(s) to analyze, or analyze all

#### Path C: LogicalServerName provided (no ClusterName or Region)
1. Resolve the logical server to a region using the `execute-kusto-query` skill's DNS lookup workflow:
   - If `LogicalServerName` is not already a FQDN, expand to FQDN: `{LogicalServerName}.database.windows.net`
   - Run DNS resolution to extract the region keyword
2. Use the `execute-kusto-query` skill to resolve `kusto-cluster-uri` and `kusto-database` for that region
3. Discover which Gateway cluster(s) serve this logical server:
   ```kql
   MonLogin
   | where TIMESTAMP > ago(<TimeRange>)
   | where AppTypeName has "Gateway"
   | where event == "process_login_finish"
   | where logical_server_name =~ "<LOGICAL_SERVER_NAME>"
   | summarize LoginCount = count() by ClusterName
   | order by LoginCount desc
   | take 5
   ```
4. Use the top cluster as `<CLUSTER_NAME>` for subsequent queries

**Output of this step** (required for all subsequent steps):
- `kusto-cluster-uri` — the Kusto cluster URI for query execution
- `kusto-database` — the Kusto database name
- `<CLUSTER_NAME>` — the Gateway cluster name to filter on
- `<TIME_FILTER>` — the **full time predicate** including the column name, used in `| where <TIME_FILTER>`. Construct as:
  - **ago style**: `TIMESTAMP > ago(2d)` or `TIMESTAMP > ago(14d)`
  - **between style**: `TIMESTAMP between(datetime(2026-03-01) .. datetime(2026-03-11))`
  - For Query 19 (MonRolloutProgress): use `originalEventTimestamp` instead of `TIMESTAMP`
  - For Query 20 (MonWatsonAnalysis): use `DumpCrashTime` instead of `TIMESTAMP`

> **CRITICAL**: Do NOT skip this step. Do NOT use default/hardcoded cluster URIs.

---

### Step 3: Detect Code Package Versions

Run **Query 1** from [references/queries.md](references/queries.md) to identify distinct code package versions in the time window. Replace `<TIME_FILTER>` and `<CLUSTER_NAME>` with values from Step 2.

**Decision point:**
- **Single version** → Proceed with Steps 4-5 using full time range
- **Multiple versions** → Note the version transition time and run Steps 4-5 for **each version separately**, then present comparison in Step 6

---

### Step 4: Check Login Success Rate

Run **Query 2** (time-series) or **Query 3** (aggregated per version) from [references/queries.md](references/queries.md). If comparing versions, run once per version.

> **LoginSuccessRate** = (Total - SystemErrors) / Total. Only system failures (is_success=false AND is_user_error=false) count as failures. User errors are reported separately.

Also run **Query 4** (top errors) to identify the dominant user errors contributing to high failure counts.

---

### Step 5: Check Resource Usage

Run **Query 5** (time-series) or **Query 6** (aggregated per version) from [references/queries.md](references/queries.md) for memory, threads, and cache metrics.

Also run **Query 7** for process-level CPU and memory counters from MDS.

See [references/knowledge.md](references/knowledge.md) for column definitions (MonGatewayResourceStats, MonMdsPerfCounters).

---

### Step 5.5: Check Redirector Health (MonRedirector)

Run the following queries from [references/queries.md](references/queries.md) to assess redirector health. See [references/knowledge.md](references/knowledge.md) for MonRedirector event types and column definitions.

| Sub-step | Query | What it checks |
|----------|-------|----------------|
| 5.5a | Query 9 | Fabric resolution failures (`fabric_end_resolve` with result != 0) |
| 5.5b | Query 10 | Fabric resolution latency (P50/P95/P99 for successful calls) |
| 5.5c | Query 11 | Alias cache ODBC failures (`sql_alias_odbc_failure`) |
| 5.5d | Query 12 | Alias cache refresh activity |
| 5.5e | Query 13 | Lookup retries (resolution instability) |
| 5.5f | Query 14 | URI cache churn (insert/delete rates) |
| 5.5g | Query 16 | Management service HTTP call stats |
| 5.5h | Query 15 | SOS wait statistics (top contention points) |
| Summary | Query 18 | Aggregated redirector health per version |

---

### Step 6: Compare Versions (if applicable)

When multiple code package versions were detected in Step 3, present a side-by-side comparison table:

#### Output Format

Use the report template and assessment criteria from [references/knowledge.md](references/knowledge.md) (see "Report Template" and "Assessment Criteria" sections).

---

### Step 7: Config and Feature Switch Diff (if version change detected)

When a code package version change is detected in Step 3, diff the ServiceSettings config files between the old and new GW release branches to identify feature switch and config changes.

**Prerequisites:** Requires `bluebird-mcp` and `ado` MCP servers to be configured.

#### 7a: Identify the Release Branches

The two code package versions detected in Step 3 contain commit hashes (e.g., `17.0.9051.10211-RelDB-a78871a0`). Use these to find the corresponding release branches.

> **IMPORTANT**: GW release branches do NOT always have `_GW` in the name. Some trains use a `_GW` suffix (e.g., `rel/db/T83_20251002_7c45cd8e_GW`), but others use the base branch directly (e.g., `rel/db/T85_20260202_cb4e5e9d`). Always search broadly.

1. Get the DsMainDev repo ID:
```
Tool: mcp_ado_repo_get_repo_by_name_or_id
Parameters:
- project: "Database Systems"
- repositoryNameOrId: "DsMainDev"
```

2. List recent release branches across multiple trains:
```
Tool: mcp_ado_repo_list_branches_by_repo
Parameters:
- repositoryId: <repo_id from step 1>
- filterContains: "rel/db/T"
- top: 30
```

3. Identify the two branches corresponding to the old and new code package versions:
   - Try matching the **commit hash suffix** from the version string (e.g., `a78871a0`) against branch names
   - If no match, identify by **train number and date** — branch name format is:
     - `rel/db/T<train>_<YYYYMMDD>_<hash>` (base release — may or may not have `_GW` suffix)
     - `rel/db/T<train>_Update1` (update release — may or may not have `_GW` suffix)
     - `rel/db/T<train>_<YYYYMMDD>_<hash>_GW` (GW-specific fork, used on some trains)
   - For EUAP/canary regions, expect the **latest train** branches
   - When in doubt, fetch from both the `_GW` variant and the base branch — they may be identical

#### 7b: Fetch and Diff ServiceSettings Files

For each of the following config files, fetch the content from both branches using `bluebird-mcp` and compare:

| Train | Config File Path |
|-------|-----------------|
| **GW** (Gateway) | `Sql/xdb/manifest/svc/gateway/ServiceSettings_Gateway_Common.xml` |
| **DB** (SQL Server) | `Sql/xdb/manifest/svc/sql/manifest/ServiceSettings_SQLServer_Common.xml` |
| **MS** (Management Service) | `Sql/xdb/manifest/svc/mgmt/fsm/common/ServiceSettings_ManagementService_FiniteStateMachine.xml` |
| **MS** (Management Service) | `Sql/xdb/manifest/svc/mgmt/fsm/fabric/ServiceSettings_FiniteStateMachine_Fabric.xml` |
| **MS** (Management Service) | `Sql/xdb/manifest/svc/mgmt/clients/ServiceSettings_ManagementService_Clients.xml` |
| **MS** (Management Service) | `Sql/xdb/manifest/svc/mgmt/ServiceSettings_ManagementService_Workflows.xml` |

**For each file**, fetch both versions:

Tool: mcp_bluebird-mcp-_get_file_content
Parameters:
- repository: "DsMainDev"
- path: "<file_path>"
- branch: "<old_branch_name>"

Tool: mcp_bluebird-mcp-_get_file_content
Parameters:
- repository: "DsMainDev"
- path: "<file_path>"
- branch: "<new_branch_name>"

Save both files locally and run:
powershell
git diff --no-index <old_file> <new_file>

#### 7c: Parse and Report Feature Switch Changes

The ServiceSettings XML has a `<FeatureSwitches>` section containing `<FeatureSwitch>` elements with `name`, `Value`, and `ownerDl` attributes.

Compare the `<FeatureSwitches>` sections and report:

1. **Removals** — feature switches in old but not in new
2. **Value changes** — feature switches where `Value` changed (e.g., `off` → `on`)
3. **Additions** — feature switches in new but not in old

#### Output Format

### Config / Feature Switch Diff
**Old Branch**: <old_branch>
**New Branch**: <new_branch>

#### Gateway Config (ServiceSettings_Gateway_Common.xml)
| Change | Feature Switch | Old Value | New Value | Owner DL |
|--------|---------------|-----------|-----------|----------|
| Changed | SomeFeature | off | on | someteam@service.microsoft.com |
| Added | NewFeature | — | on | otherteam@service.microsoft.com |
| Removed | OldFeature | off | — | someteam@service.microsoft.com |

#### DB Config (ServiceSettings_SQLServer_Common.xml)
(same table format)

#### Management Service Config
(same table format, merged across all 4 MS files)
```

If a file is **identical** between branches, report:
> ✅ No config changes in `<filename>` between branches.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data in MonLogin | Verify ClusterName spelling, check if Gateway app type name is correct for the cluster |
| No data in MonGatewayResourceStats | This table may have shorter retention; try a smaller time window |
| No code_package_version column | The column is an XEvent action — ensure `code_package_version` action is in the session |
| Kusto MCP not responding | Run `az login` to refresh credentials, verify MCP server config |
| Too many results | Increase the `bin()` interval from 15m to 1h |
| No data in MonRedirector | Verify the `xdbgateway` XEvent session is running; check `MonitoringGatewayMDSAgentConfig_template.xml` |
| fabric_end_resolve shows all failures | Check if SF cluster is healthy, partitions may be down or moving |
| High ODBC failures | Alias database may be unreachable — check network and alias DB health |
| Unexpected SOS wait types | Compare with baseline; new wait types after version change may indicate regressions |
  | bluebird-mcp not available | Config diff step requires bluebird-mcp; skip Step 7 and note in report |
| GW branch not found | Not all trains have `_GW` suffixed branches; try the base branch `rel/db/T<N>_<date>_<hash>` without suffix |
| File not found on branch | The file path may have changed between releases; search with `mcp_bluebird-mcp-_search_file_paths` |
| `_get_file_content` returns error | Verify branch name is exact (e.g., `rel/db/T83_Update1_GW` not `refs/heads/...`) |

## References

See [references/knowledge.md](references/knowledge.md) for source code references, XEvent session paths, and ServiceSettings file locations.
