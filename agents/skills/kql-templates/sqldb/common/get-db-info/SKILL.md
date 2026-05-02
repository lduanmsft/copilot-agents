---
name: get-db-info
description: Retrieves Azure SQL Database environment information including Fabric partition ID, physical database ID, logical database ID, service tier, and cluster details. This is a shared utility skill used by other HA troubleshooting skills to obtain database configuration and deployment information.
---

# Database Information Lookup

This skill retrieves essential database environment information from Azure SQL Database telemetry. It queries the `MonAnalyticsDBSnapshot` table to obtain database identifiers, deployment configuration, and Service Fabric details.

## ⚠️ CRITICAL: Mandatory Output Section

The **Database Environment** section is **MANDATORY** in every investigation report. It must:
1. Appear immediately after the Incident Summary section
2. Include ALL 14 fields for each configuration (never omit any field)
3. Use side-by-side format when there are 2-3 configurations
4. Use vertical format when there are 4+ configurations

## Required Information

### From User or ICM:
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`) - for query execution only, NOT for output
- **kusto-database** (e.g., `sqlazure1`) - for query execution only, NOT for output

## Workflow

### 1. Execute Database Environment Query

Execute query from [references/queries.md](references/queries.md) section DBINFO100.

**Query Purpose**: Retrieves database configuration from MonAnalyticsDBSnapshot including:
- SQL instance name (AppName)
- Logical database ID
- Physical database ID
- Fabric application URI
- Fabric partition ID
- Service level objective (service tier)
- Zone resilient flag
- Tenant ring name (ClusterName)

### 2. Validate Results

**Expected**: 1 or more rows returned

**If 0 rows returned**:
> 🚩 No database environment found for LogicalServerName='{LogicalServerName}', LogicalDatabaseName='{LogicalDatabaseName}' in time window {StartTime} to {EndTime}.
> 
> Possible causes:
> - Incorrect server or database name
> - Database did not exist during this time window
> - Telemetry data not available

**STOP execution**.

**If 1 row returned**:
- Normal case - database configuration is stable throughout the time window
- Proceed to extract variables and display using single configuration format

**If 2+ rows returned**:
> ⚠️ Multiple database environment records found ({count} rows). Database was reconfigured during the time window.

- **CRITICAL**: Check if `min_PreciseTimeStamp` values are **identical or very close** across configurations
- If timestamps are ambiguous (same or within minutes), see **Step 2a: Resolve Ambiguous Configuration Order**
- Use **side-by-side format** for 2-3 configs, **vertical format** for 4+ configs
- **Always order configurations chronologically** - Config 1 = oldest (first observed), Config N = newest

### 2a. Resolve Ambiguous Configuration Order (When Timestamps Overlap)

**⚠️ CRITICAL**: When multiple configurations have identical or very close `min_PreciseTimeStamp` values, you **CANNOT** determine which is "old" vs "new" from `min_PreciseTimeStamp` alone.

**Detection**: Timestamps are ambiguous when:
- `min_PreciseTimeStamp` values are identical across configs, OR
- `min_PreciseTimeStamp` values are within 30 minutes of each other

**Resolution**: Use `max_PreciseTimeStamp` as a tiebreaker — the config with the **larger** (later) `max_PreciseTimeStamp` is the **newer** configuration.

**Why this works**: 
- The old configuration stops receiving telemetry after the reconfiguration, so its `max_PreciseTimeStamp` is earlier
- The new configuration continues receiving telemetry, so its `max_PreciseTimeStamp` is later
- In rare cases where both configs are decommissioned simultaneously (e.g., two rapid reconfigurations), `max_PreciseTimeStamp` may also be identical — we will accommodate this edge case when we see enough real incidents to justify it

**Example**:
```
DBINFO query results:
  Config A: min_PreciseTimeStamp = 11:54, max_PreciseTimeStamp = 12:08  ← OLD (earlier max)
  Config B: min_PreciseTimeStamp = 11:54, max_PreciseTimeStamp = 16:24  ← NEW (later max)
```

**After resolution**:
- Label configurations as "Config 1 (Old)" → "Config N (New)"
- The config with the **earlier** `max_PreciseTimeStamp` is the OLD configuration
- The config with the **later** `max_PreciseTimeStamp` is the NEW configuration

### 3. Extract Variables

For each result row, extract and store:

- **AppName** = `sql_instance_name`
- **ClusterName** = `tenant_ring_name`
- **logical_database_id** = `logical_database_id`
- **physical_database_id** = `physical_database_id`
- **fabric_partition_id** = `fabric_partition_id`
- **fabric_application_uri** = `fabric_application_uri`
- **service_level_objective** = `service_level_objective` (e.g., GP_Gen5_2, BC_Gen5_4)
- **zone_resilient** = `zone_resilient` (0 or 1)
- **logical_resource_pool_id** = `logical_resource_pool_id`
- **sql_database_id** = `sql_database_id`
- **database_usage_status** = `database_usage_status` (e.g., Active, Inactive, UpdateSloTarget)
- **physical_database_states** = `set_physical_database_state` (set of states observed, e.g., ["Ready"], ["Ready", "Deactivated"])
- **config_start_time** = `min_PreciseTimeStamp` (when this configuration was first observed)
- **config_end_time** = `max_PreciseTimeStamp` (when this configuration was last observed)

**If multiple rows**: Store as an array/list of configurations, each with its own time range.

> 💡 **Tip**: If one configuration has `database_usage_status = "UpdateSloTarget"`, the other configuration with `database_usage_status = "Active"` is the UpdateSlo **source**. This indicates an SLO change operation is in progress.

### 4. Determine Deployment Type

Based on the retrieved information:

**Zone Resilient Flag**:
- `zone_resilient = 1` → Database is deployed across availability zones
- `zone_resilient = 0` → Database is in a single availability zone

**Service Tier** (from `service_level_objective`):
- Starts with `GP_` → General Purpose tier
- Starts with `BC_` or contains `BC` → Business Critical tier
- Starts with `HS_` → Hyperscale tier

**Deployment Pattern** (for query selection in diagnostic skills):
- **GP without ZR**: `zone_resilient = 0` AND service tier = `GP_*`
- **GP with ZR**: `zone_resilient = 1` AND service tier = `GP_*`
- **BC**: Service tier contains `BC_*` (typically zone resilient)

## Output Format

**⚠️ CRITICAL**: The Database Environment section is **MANDATORY** in every report.

See [references/output.md](references/output.md) for:
- Mandatory output templates (single, side-by-side, vertical formats)
- Complete field checklist with descriptions and examples
- **Pre-output validation checklist** (MUST complete before outputting)

### 🔴🔴🔴 ENFORCEMENT: Copy-Paste the Template 🔴🔴🔴

**DO NOT** write the Database Environment table from memory. Instead:

1. **Open** [references/output.md](references/output.md)
2. **Copy** the appropriate template (single/side-by-side/vertical)
3. **Paste** the template into your output
4. **Replace** placeholder values `{...}` with actual query results
5. **Verify** - Count the rows in your table. **Must be exactly 14**.

This ensures all field names are spelled correctly and no fields are omitted.

### Output Rules:

1. **Section is MANDATORY** - Must always appear in the report after Incident Summary
2. **ALL 14 fields must be present** - Never omit any field - **COUNT THEM!**

### 🔴 MANDATORY 14-Field Checklist (COUNT BEFORE OUTPUT!)

**STOP!** Before generating the Database Environment section, verify your output includes ALL of these fields:

| # | Field Name | From Query Column |
|---|------------|-------------------|
| 1 | AppName | sql_instance_name |
| 2 | logical_database_id | logical_database_id |
| 3 | logical_resource_pool_id | logical_resource_pool_id |
| 4 | fabric_application_uri | fabric_application_uri |
| 5 | fabric_partition_id | fabric_partition_id |
| 6 | physical_database_id | physical_database_id |
| 7 | sql_database_id | sql_database_id |
| 8 | service_level_objective | service_level_objective |
| 9 | zone_resilient | zone_resilient |
| 10 | tenant_ring_name | tenant_ring_name |
| 11 | database_usage_status | database_usage_status |
| 12 | physical_database_states | set_physical_database_state |
| 13 | min_PreciseTimeStamp | min(PreciseTimeStamp) |
| 14 | max_PreciseTimeStamp | max(PreciseTimeStamp) |

3. **Use EXACT field names from template** - Do NOT rename or abbreviate fields
4. **Use `""` for null/empty values** - Do not omit the row
5. **Side-by-side format for 2-3 configs** - Better visual comparison
6. **Vertical format for 4+ configs** - Separate tables for each
7. **NO "Common Properties" subsection** - Show all fields for each configuration
8. **EXCLUDE Kusto connection info** - Do NOT display Kusto Cluster URI or Kusto Database

### 🔴 MANDATORY: Before Outputting

**STOP** and refer to [references/output.md](references/output.md) **Validation Checklist** section:
- Verify all **14 field names** match EXACTLY (including parentheses for aliases)
- Review the **Common Mistakes to Avoid** table
- Count your fields - must be exactly 14 rows

### Format Selection:

| Configuration Count | Format to Use |
|---------------------|---------------|
| 1 | Single table |
| 2 | Side-by-side (2 columns) |
| 3 | Side-by-side (3 columns) |
| 4+ | Vertical (separate tables) |

## Error Handling

- If query execution fails: Report Kusto error and stop
- If 0 rows: Stop with error message (possible incorrect parameters)
- If required fields are null: Display as empty string `""`, do not omit

## Usage Notes

This skill should be called by the agent after the `execute-kusto-query` skill and before invoking diagnostic skills like the `failover` skill or the `quorum-loss` skill. The output variables are used by diagnostic skills for:
- Filtering telemetry queries
- Selecting appropriate query patterns
- Understanding database configuration context
