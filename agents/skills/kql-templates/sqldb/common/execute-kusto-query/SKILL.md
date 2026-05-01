---
name: execute-kusto-query
description: **MANDATORY** Execute this skill when user asks to run Kusto queries, execute KQL, analyze SQL telemetry, or query monitoring tables (MonAnalyticsDBSnapshot, MonDmRealTimeResourceStats, etc.). This skill automatically finds the correct Kusto cluster based on logical server region. DO NOT execute Kusto queries directly - always use this skill workflow.
---

# Workflow 

**ABSOLUTE MANDATORY RULES:**
- You MUST use this skill whenever executing Kusto/KQL queries for SQL Database telemetry
- You must review these instructions in full before executing any steps to understand the full instructions guidelines
- You must follow these instructions exactly as specified without deviation
- DO NOT use mcp_azure_mcp_kusto directly without following this workflow
- DO NOT use default clusters like sqladhoc without determining the correct cluster for the logical server

**When to use these instructions:**
1. User asks to execute/run a Kusto query or KQL query
2. User mentions querying telemetry tables (MonAnalyticsDBSnapshot, MonDmRealTimeResourceStats, MonDmDbHadrReplicaStates, etc.)
3. User asks about which region a logical server is in
4. User asks to analyze SQL Database telemetry or monitoring data

## How to Execute Kusto Queries - Follow These Steps in Order

### Step 1: Parse and replace parameters in Kusto queries
Parse parameters using [references/parseParameters.md](references/parseParameters.md)
- Replace {ParameterName} placeholders with actual values
- If values are missing, prompt the user

### Step 2: Obtain Kusto cluster information for the logical server
**CRITICAL:** Always identify the correct cluster - do NOT use default clusters
Identify telemetry-region and kusto-cluster-uri and Kusto-database using [references/getKustoClusterDetails.md](references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

### Step 3: Execute the Kusto query on the correct cluster
Execute Kusto query using [references/executeQuery](references/executeQuery.md)
- Use the cluster-uri and database identified in Step 2
- Execute the query via mcp_azure_mcp_kusto tool
