# Sources: Hyperscale (VLDB) Restore Investigation

## Primary TSG

- **BRDB0005.1** — Hyperscale restore stuck/failure
  - Primary knowledge source for Kusto queries and diagnostic patterns
  - Covers failed RCA, stuck detection, and slow restore analysis for VLDB restores

## XTS View

- **`sterling/vldbrestorerequests.xts`** — 21 activities covering the full HS restore investigation space
  - Used during the research/design phase to discover and extract queries
  - All 24 queries (QHR00A–QHR190) were extracted as standalone KQL from this view
  - XTS is **not a runtime dependency** — all queries execute via `mcp_sqlops_query_kusto`

## Kusto Tables (from TSG BRDB0005.1)

| Table | Purpose |
|-------|---------|
| `MonManagementOperations` | Management operation lifecycle |
| `MonManagement` | State machine transitions (FSM events) |
| `MonManagementFSMInternal` | FSM internal queue events |
| `MonBlobClient` | Azure Storage blob copy operations |
| `MonFabricClient` | Service Fabric client operations |
| `WinFabLogs` | Service Fabric placement traces |
| `MonAnalyticsDBSnapshot` | Database snapshot metadata |
| `MonSocrates` | Socrates component traces |
| `MonSQLSystemHealth` | SQL system health events |
| `MonRecoveryTrace` | Database recovery traces |
| `MonXlogSrv` | XLog server traces |
| `MonSQLXStore` | XStore file operations |
