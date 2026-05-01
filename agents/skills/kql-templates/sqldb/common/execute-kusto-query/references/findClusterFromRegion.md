# Get Kusto cluster URI for a region

## Primary Method: Kusto Query

Query to get cluster URI based on region name.

**Execute using mcp_azure-mcp_kusto tool:**

```
{
  "tool": "mcp_azure-mcp_kusto",
  "parameters": {
    "command": "kusto_query",
    "intent": "Find Kusto cluster URI and database for region {region}",
    "parameters": {
      "cluster-uri": "https://sqladhoc.kusto.windows.net:443",
      "database": "sqlazure1",
      "query": "KustoConnectionConfiguration | where MdsNamespace in ('WASD2Prod','WASD2Mcpr','WASD2Bfpr','WASD2ffpr') | extend RegionName = extract(@\"^[^-]+-[^-]+-(.+)-[a-z]$\", 1, tolower(ClusterName)) | where RegionName == '{region}' | project DataSource, InitialCatalog | take 1"
    }
  }
}
```

**Before executing:**
1. Replace `{region}` placeholder with the actual region keyword (e.g., "eastus1", "westus2")
2. The parameters field must be a JSON object with cluster-uri, database, and query

**Example for region "eastus1":**
```
mcp_azure-mcp_kusto(
  command: "kusto_query",
  intent: "Find Kusto cluster URI and database for region eastus1",
  parameters: {
    "cluster-uri": "https://sqladhoc.kusto.windows.net:443",
    "database": "sqlazure1",
    "query": "KustoConnectionConfiguration | where MdsNamespace in ('WASD2Prod','WASD2Mcpr','WASD2Bfpr','WASD2ffpr') | extend RegionName = extract(@\"^[^-]+-[^-]+-(.+)-[a-z]$\", 1, tolower(ClusterName)) | where RegionName == 'eastus1' | project DataSource, InitialCatalog | take 1"
  }
)
```

**Output:** 
- `kusto-cluster-uri` from DataSource column (e.g., "https://sqlazureeus12.kusto.windows.net:443")
- `database` from InitialCatalog column (always "sqlazure1")

---

## Fallback Method: XML Configuration File

**Use this fallback when:**
- The Kusto query above fails or returns no results
- The sqladhoc cluster is unavailable
- Kusto access is not yet established

### Steps:

1. **Read the XML file**: `KustoConnectionConfiguration.xml` (in the `assets/` folder)

2. **Find matching Connection element** where ClusterName contains the region pattern:
   - For region `eastus1`, find ClusterName like `wasd-prod-eastus1-a` or similar
   - For region `japanwest1`, find ClusterName like `wasd-prod-japanwest1-a` or similar
   
3. **Extract values from the matching Connection element**:
   ```xml
   <Connection>
       <ClusterName>Wasd-prod-eastus1-a</ClusterName>
       <ClusterShortName>ProdEus1a</ClusterShortName>
       <DataSource>https://sqlazureeus12.kusto.windows.net:443</DataSource>
       <InitialCatalog>sqlazure1</InitialCatalog>
       <MdsNamespace>WASD2Prod</MdsNamespace>
   </Connection>
   ```
   
   - `kusto-cluster-uri` = Value from `<DataSource>` element
   - `kusto-database` = Value from `<InitialCatalog>` element

**If no matching region found in XML:**
> 🚩 CRITICAL: Region {region} not found in KustoConnectionConfiguration.xml. Cannot determine Kusto cluster-uri.

**STOP execution** if region mapping is not found in both primary and fallback methods.