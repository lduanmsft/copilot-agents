---
name: failover
description: Debug Azure SQL Database high availability (HA) failover issues including long failovers, failed failovers, and availability problems. Use when investigating SQL Database availability issues, failover delays, replica transitions, or database connectivity problems. Accepts either ICM ID or direct parameters (logical server name, database name, time window). Executes Kusto queries via Azure MCP to analyze telemetry data including failover events, replica changes, SQL process lifecycle, and extended events.
---

# Debug Azure SQL Database High Availability Failover Issues

Debug HA issues such as long failovers or failed failovers for Azure SQL Database.

## Required Information

This skill requires the following inputs (should be obtained by the calling agent):

### From User or ICM:
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill (one or more configurations):
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **logical_database_id**
- **physical_database_id**
- **fabric_partition_id**
- **service_level_objective**
- **zone_resilient**
- **deployment_type** (e.g., "GP without ZR", "GP with ZR", "BC")
- **config_start_time** (when this configuration was active from)
- **config_end_time** (when this configuration was active until)
- All other database environment variables

**Note**: The calling agent should use the `execute-kusto-query` skill and the `get-db-info` skill before invoking this skill. If multiple database configurations exist (e.g., tier change during incident), the agent should invoke this skill separately for each configuration with its respective time window.

## Workflow

### 1. Validate Inputs

Ensure all required parameters are provided:
- From user/ICM: LogicalServerName, LogicalDatabaseName, StartTime, EndTime
- From execute-kusto-query: kusto-cluster-uri, kusto-database, region
- From get-db-info: AppName, ClusterName, physical_database_id, fabric_partition_id, deployment_type, config_start_time, config_end_time, and all other database variables

**Note**: If analyzing a specific database configuration (when multiple exist), use config_start_time and config_end_time to scope the analysis to that configuration's active period.

Calculate `Duration` between StartTime and EndTime (e.g., `1h`, `101m`).

### 2. Understand XEvents

Use `mcp_bluebird-mcp-_engineering_copilot` to learn about XEvents:
- `hadr_fabric_api_replicator_begin_change_role`
- `hadr_fabric_api_replicator_end_change_role`

Focus on fields they expose. Store this knowledge for later analysis.

**Note**: This tool connects to the DsMainDev repository (SQL Server product code) which contains XEvent definitions.

### 3. Output SqlFailovers and LoginOutages

Execute queries HA140 and HA200 from [references/queries.md](references/queries.md).

Output results in tabular format.

### 3a. Check Management Operation Timing (MANDATORY for CustomerInitiated outages)

**⚠️ CRITICAL**: If LoginOutages (HA200) shows `OutageType = "CustomerInitiated"` with operations like `UpdateLogicalElasticPool`, `FailoverApi`, `ResumeContinuousCopy`, or similar management operations:

1. **MUST** execute query HA210 from [references/queries.md](references/queries.md) to get **actual** operation start/end times
2. **DO NOT** use timestamps from `OutageReasonLevel3` JSON field — those are **snapshot times**, not actual completion times
3. **Copy the HA210 query results directly into the report table** using the format in [references/output.md](references/output.md) — the query already produces one aggregated row per operation with the final columns

**Why this matters**: LoginOutages metadata may contain outdated/incorrect timestamps. The authoritative source for management operation timing is `MonManagementOperations`.

### 4. Identify Old and New Primary Replicas

**Choose appropriate query based on deployment:**
- **GP without ZR**: Use HA106 (DeleteReplica) + HA107 (AddPrimary)
- **GP with ZR or BC**: Use HA108 (ReconfigurationStartedOperational)

Execute queries from [references/queries.md](references/queries.md).

Output old/new primary replicas with timestamps.

### 5. Create Failover Time Windows

For each failover identified:

**Create table:**
| Failover#  | Old Primary | New Primary | Window StartTime    | Window EndTime      | Duration |
|------------|-------------|-------------|---------------------|---------------------|----------|
| 1          | _DB_3       | _DB_55      | 2025-12-09 07:12:04 | 2025-12-09 09:01:10 | 109m     |
| 2          | _DB_55      | _DB_57      | 2025-12-09 09:01:10 | 2025-12-09 14:00:00 | 299m     |

**Store variables per failover:**
- `FailoverNumber`
- `OldPrimaryNode`
- `NewPrimaryNode`
- `WindowStartTime`
- `WindowEndTime`
- `WindowDuration`

**Also generate Failover Sequence table** as specified in [references/output.md](references/output.md) - this provides a chronological view of all DeleteReplica and AddPrimary events before the detailed per-node analysis.

### 6. Generate Detailed Per-Node Timeline Analysis (MANDATORY OUTPUT)

For each failover window, follow [references/principles.md](references/principles.md).

**CRITICAL OUTPUT REQUIREMENT**: You MUST generate the complete "Detailed Per-Node Timeline Analysis" section as specified in [references/output.md](references/output.md).

**This section must include:**
- One complete timeline subsection for EACH node involved in the failover sequence
- Chronological event tables with timestamps and time gaps
- Warnings section for each node (missing events, delays)
- Analysis of each node's behavior

**Important**:
- Print one timeline per node involved in the failover sequence
- Use the same format for all nodes (whether old primary, new primary, failed attempt, or successful)
- Events are printed in chronological order as they occurred
- Warnings for missing events and large gaps are shown after the timeline
- Follow the exact format from output.md examples

**MANDATORY: For EACH node, you MUST execute ALL the following queries (use node-specific time windows) - NO EXCEPTIONS**

Even if you think a query won't return results (e.g., AddPrimary for old primary, or DeleteReplica for new primary), you MUST still execute it. The query results determine what gets printed, not assumptions.

Read queries from [references/queries.md](references/queries.md), **Adjust Duration** parameter to each node's active time window.

**Time windows per node:**
- Old primary: From 1 hour before DeleteReplica to DeleteReplica time
- Each new primary: From AddPrimary time to either next AddPrimary OR +2 hours

**All possible events to query** (print in chronological order as they occurred):
1. HA1020 (DeactivateNode)
2. HA106 (DeleteReplica)
3. HA107 (AddPrimary)
4. HA1000 (Image Downloaded)
5. HA1005 (XDB Launch Setup)
6. HA1010 (CodePackage Activated Successfully)
7. HA2000 (SQL Process Started)
8. HA2010 (Tempdb Recovery in X second(s))
9. HA2020 (SQL Server Ready for client connections)
10. HA2030 (Server [CFabricReplicaManager::Start] Registered service type)
11. HA2040 (hadr_fabric_api_factory_create_replica)
12. HA5005 (Role Change to PRIMARY - hadr_fabric_api_replicator_begin_change_role)
13. HA4020 (Recovery completed for database {physical_database_id} (database ID {db_id}) in X second(s))
14. HA400 (hadr_fabric_api_partition_write_status: GRANTED)

> **Quorum Loss Check**:
> - **Condition**: HA400 results contain `current_write_status_desc = 'NO_WRITE_QUORUM'`
> - **Action**: Invoke the [quorum-loss skill](../quorum-loss/SKILL.md) with the following parameters:
>   - **kusto-cluster-uri**: (from execute-kusto-query)
>   - **kusto-database**: (from execute-kusto-query)
>   - **region**: (from execute-kusto-query)
>   - **LogicalServerName**: (from user/ICM)
>   - **LogicalDatabaseName**: (from user/ICM)
>   - **AppName**: (from get-db-info)
>   - **ClusterName**: (from get-db-info)
>   - **physical_database_id**: (from get-db-info)
>   - **fabric_partition_id**: (from get-db-info)
>   - **StartTime**: Time of first NO_WRITE_QUORUM event
>   - **EndTime**: Time of last NO_WRITE_QUORUM event (or original EndTime)
> - **Purpose**: Investigate quorum loss before continuing with failover analysis

**Query Execution Rules:**
- Execute ALL the queries above for EVERY node - no skipping, no assumptions
- If a query returns no results, that's fine - just don't print that event in the timeline
- If a query returns results, ALL results must be printed in chronological order
- Do NOT decide which queries to skip based on node role (old vs new primary)

**Output Format:**

**CRITICAL**: You must follow [references/output.md](references/output.md) to generate "Detailed Per-Node Timeline Analysis"

**Rules for warnings:**

**CRITICAL**: Node role determines which warnings apply. These are **MUTUALLY EXCLUSIVE** categories:

- **For NEW primary replicas** (nodes with AddPrimary event) - warn ONLY if these are missing:
  - AddPrimary
  - hadr_fabric_api_factory_create_replica
  - hadr_fabric_api_replicator_begin_change_role with new_role_desc: PRIMARY
  - Recovery completed for UserDB (physical_database_id)
  - hadr_fabric_api_partition_write_status: GRANTED
  - **If all critical events are present, do NOT flag missing critical events**
  
- **For OLD primary replicas** (nodes with DeleteReplica event) - warn ONLY if DeleteReplica is missing:
  - DeleteReplica
  - **If DeleteReplica is present, do NOT flag any missing critical events**
  - **No other events are considered critical for old primary replicas**

**DO NOT apply new primary warnings to old primary nodes, or vice versa.**
**DO NOT flag missing critical events if the critical events for that node role are present.**

- **Large time gaps** (applies to ALL nodes) - flag if gap exceeds:
  - >2 minutes between most consecutive events
  - >5 minutes for Image Download → CodePackage Activation
  - >10 minutes for SQL Ready → Write Status GRANTED
  - >30 seconds for Tempdb Recovery
- **Special conditions** - include narrative descriptions for:
  - Error 18401 (script upgrade mode) with time range
  - Extended periods in any state
  - Process restarts or crashes

**CRITICAL - Timestamp and Output Rules:**
- **NEVER estimate or create timestamps** - only use actual timestamps from query results
- **Print events in chronological order** as they occurred (not in expected sequence order)
- **Print only events that occurred** - do NOT print events that didn't occur in the main timeline
- **Group warnings after events** - list missing critical events and large gaps in warning section
- **Determine node role from events** - if DeleteReplica present = old primary; if AddPrimary present = new primary
- Format timestamps as: `YYYY-MM-DD HH:MM:SS` or `YYYY-MM-DD HH:MM:SS.ff` for sub-second precision
- Calculate time gaps between consecutive events to identify delays
- Time gap format: Use shorthand notation (e.g., 5s, 1m 30s, 2h 15m, 3h 42m 15s) - NOT "5 seconds", "1 minute 30 seconds", etc.


**Output requirements:**
- Print timeline for EVERY node involved in the failover sequence
- For each node, print ONLY events that actually occurred (with timestamps from query results)
- DO NOT print events that didn't occur in the main timeline
- In warnings section, list:
  - 🚩 Missing critical events
  - ⚠️ Large time gaps with duration and affected events
  - Narrative descriptions for special conditions (Error 18401, etc.)
- Use actual timestamps from queries in format: `YYYY-MM-DD HH:MM:SS` or with milliseconds/microseconds
- Calculate time gap between consecutive events to detect delays

**Verification Checklist (before outputting timeline for a node):**
- [ ] Executed **All possible events to query** for this node?
- [ ] Collected all results from all queries?
- [ ] Sorted all events by timestamp chronologically?
- [ ] Printed all events that occurred (not just a subset)? with milliseconds/microseconds


### 7. Major Issue Evidence Queries

Include ONLY queries for events marked with 🚩:

````
**[QueryID] - Brief description**
```kql
(The ACTUAL executed query with ALL parameters replaced)
```
**Result Summary**: Explanation of what result shows
````

**DO NOT**:
- Include queries for ✅ events
- Reference queries without showing actual KQL
- Use templates or placeholders

**Analysis Requirements:**
- Base conclusions on facts and principles only
- Do NOT speculate or guess
- Clearly separate analysis per failover
- Do NOT mix failover analyses

## Key Terms

See [references/knowledge.md](references/knowledge.md) for:
- General concepts (Application Instance, Service Tiers, Availability Zones)
- Deployment models (Single database, Elastic pool)
- Telemetry concepts (Logical Server/Database, AppTypeName, fabric_application_uri, zone_resilient)

## Query Execution Format

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "<description>"
- parameters: {"cluster-uri": "<uri>", "database": "<db>", "query": "<kql>"}
```

**Parameters must be JSON object, not string.**

## Related Skills

- **[Quorum Loss](../quorum-loss/SKILL.md)**: Quorum loss investigation when NO_WRITE_QUORUM is detected in HA400 results
