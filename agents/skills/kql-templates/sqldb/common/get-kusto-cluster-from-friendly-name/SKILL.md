---
name: get-kusto-cluster-from-friendly-name
description: Identifies the correct Kusto cluster URI and database name for a given Azure region friendly name to be provided by user. This is a shared utility skill used by other skills to route telemetry queries to the appropriate regional Kusto cluster.
---

# Get Regional Kusto Cluster

This skill maps an Azure region name to its corresponding Kusto cluster URI and database name, enabling proper routing of telemetry queries to regional clusters.

## Required Information

### Input:
- **Region** (e.g., "west us 1", "eastus2", "japanwest1")

### Output:
- **kusto-cluster-uri** (e.g., `https://sqlazurewus1.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)

## Workflow

### Step 1: Normalize Region Name

Apply the following normalization rules to the region input:

**Region Number Default:**
- If user says "west us" without a number, treat it as "west us 1"
- Similarly: "east us" → "east us 1", "north europe" → "north europe 1", etc.

**Format Normalization:**
- Remove all spaces and convert to lowercase
- Examples:
  - "West US 1" → "westus1"
  - "East US 2" → "eastus2"
  - "Japan West 1" → "japanwest1"
  - "west us" → "westus1" (adds default "1")

### Step 2: Query for Regional Cluster

Execute the following query using the cluster URI `https://sqladhoc.kusto.windows.net` and the database name `sqlazure1`:

```kusto
KustoConnectionConfiguration
| where MdsNamespace in ('WASD2Prod','WASD2Mcpr','WASD2Bfpr','WASD2ffpr')
| extend RegionName = extract(@"^[^-]+-[^-]+-(.+)-[a-z]$", 1, tolower(ClusterName))
| where RegionName == '{region}'
| project DataSource, InitialCatalog
| take 1
```

**Parameters:**
- Replace `{region}` with the normalized region name from Step 1

### Step 3: Extract Results

From the query results:
- **kusto-cluster-uri**: Value from `DataSource` column
- **kusto-database**: Value from `InitialCatalog` column (typically `sqlazure1`)

### Step 4: Validate Results

**Expected**: 1 row returned

**If 0 rows returned**:
> 🚩 No Kusto cluster found for region '{region}'. 
> 
> Possible causes:
> - Region name is incorrect or misspelled
> - Region is not yet configured in KustoConnectionConfiguration
> - Region normalization may need adjustment

**STOP execution** and notify user.

## Usage Examples

### Example 1: West US 1
**Input:** "west us 1"
- Normalized: "westus1"
- **Output:** 
  - kusto-cluster-uri: `https://sqlazurewus1.kusto.windows.net:443`
  - kusto-database: `sqlazure1`

### Example 2: East US (defaults to East US 1)
**Input:** "east us"
- Normalized: "eastus1" (added default "1")
- **Output:**
  - kusto-cluster-uri: `https://sqlazureeus12.kusto.windows.net:443`
  - kusto-database: `sqlazure1`

### Example 3: Japan West 1
**Input:** "Japan West 1"
- Normalized: "japanwest1"
- **Output:**
  - kusto-cluster-uri: `https://sqlazurejpw1.kusto.windows.net:443`
  - kusto-database: `sqlazure1`

## Integration with Other Skills

Other skills should use this skill when they need to:
1. Route queries to a regional Kusto cluster instead of a central cluster
2. Query telemetry data specific to a region
3. Perform region-specific operations that require regional cluster access

**Usage Pattern:**

### Step 1: Get Regional Kusto Cluster
Execute Common skill: `.github/skills/Common/get-kusto-cluster-from-friendly-name/SKILL.md`
- Input: Region from user or inferred from context
- Output: kusto-cluster-uri, kusto-database

### Step 2: Execute Query on Regional Cluster
Use the kusto-cluster-uri and kusto-database from Step 1 to execute queries.

## Notes

- This skill queries the `KustoConnectionConfiguration` table which contains the mapping of regions to Kusto clusters
- The mapping is maintained in Azure SQL Database infrastructure
- Different environments (Prod, MCPR, BFPR, FFPR) may have different cluster mappings
- Always use the regional cluster for optimal query performance and data locality
