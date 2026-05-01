If kusto cluster information is known execute kusto query.
Execute Kusto Queries via Azure MCP
**Execute queries**
```
Tool: mcp_azure-mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "<brief description of what you're querying>"
- parameters: "<JSON string with cluster-uri, database, and query>"
```

**Example:**
```
Tool: mcp_azure-mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Test query to validate Kusto access"
- parameters: {"cluster-uri": "https://sqlazureeus12.kustomfa.windows.net:443", "database": "sqlazure1", "query": "MonDmRealTimeResourceStats | take 1 | project TIMESTAMP"}
```

**Critical Notes:**
- The `parameters` field must be a JSON string (not a JSON object)
- Always include `cluster-uri`, `database`, and `query` in the parameters
- Use the exact cluster URI including port (e.g., :443)
- Do NOT assume the mcp_azure-mcp_kusto  is disabled.  Try executing the query first to validate access.
- If mcp_azure-mcp_kusto is disabled, activate it and try again