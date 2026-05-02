---
name: restore-failure
description: Debug Azure SQL Database restore failures and stuck restore operations. Investigates restore validation errors, state machine issues, backup unavailability, and stuck restore scenarios. Required inputs from calling agent - kusto-cluster-uri, kusto-database, and database configuration variables from get-db-info skill.
---

# Debug Azure SQL Database Restore Failures and Stuck Restore Operations

Debug and investigate Azure SQL Database restore operations that fail or become stuck during execution.

## Required Information

This skill requires the following inputs (should be obtained by the calling agent):

### From User or ICM:
- **Logical Server Name** (e.g., `my-server`)
- **Source Database Name** (database to restore from)
- **Target Database Name** (optional, database name for restore target)
- **Point In Time** (optional, UTC format: `2024-01-15 14:30:00`)
- **Restore Request ID** (optional, from CMS/Sterling)

### From execute-kusto-query skill:
- **kusto-cluster-uri**
- **kusto-database**
- **region**

### From get-db-info skill (optional, if available):
- **physical_database_id**
- All other database environment variables

**Note**: The calling agent should use the `execute-kusto-query` skill before invoking this skill.

## Overview

This skill diagnoses why Azure SQL Database restore operations fail or become stuck. Common issues include:
- Restore validation failures (invalid point in time, server not found, database exists)
- Restore state machine not created or stuck in Ready state
- Backup files unavailable or corrupted
- Server disabled or dropped
- SQL process crashes during restore
- Blob lease issues during remote database restore

**Critical**: Always verify server has not been disabled or dropped before investigating restore failures.

## Workflow

### 1. Check Restore Request Using SterlingRestoreRequests.xts

Open the `SterlingRestoreRequests.xts` view in the appropriate region and enter the server name to find all restore requests. This is the primary triage tool for restore failures.

Alternatively, execute query **RFQ100** from [references/queries.md](references/queries.md) to find the restore request:

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Find restore request details"
- parameters: {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "MonRestoreRequests | where target_logical_server_name =~ '{LogicalServerName}' | where target_logical_database_name =~ '{TargetDatabaseName}' | project TIMESTAMP, restore_request_id, state, operation_details, restore_type, target_logical_server_name, target_logical_database_name | order by TIMESTAMP desc | take 10"
}
```

**Analysis:**
- **If no results**: Restore request was never created — check management validation (RFQ300)
- **If `state` == "Restoring"**: Restore in progress — check events (RFQ200)
- **If `state` == "Failed"**: Check `operation_details` for error message
- **If `state` == "Completed"**: Restore succeeded, verify DB is online
- **If `state` == "Cancelled"**: Target DB was dropped, cancelling the restore

### 2. Check Management Validation (If No Restore Request Found)

If RFQ100 returned no results, check if the restore request failed validation:

Execute query **RFQ300** from [references/queries.md](references/queries.md):

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Check management workflow for restore validation failures"
- parameters: {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "MonManagementOperations | where request_id contains '{RestoreRequestId}' | where event in ('management_operation_success', 'management_operation_failure', 'management_operation_canceled', 'management_workflow_restore_request_begin', 'management_workflow_restore_request_failure') | project originalEventTimestamp, event, operation_type, request_id, message | order by originalEventTimestamp desc"
}
```

**If `management_workflow_restore_request_failure` found:**
> 🚩 **Restore Validation Failed**: Check the message column for the specific validation error.
>
> **Common validation failures** (from TSG BRDB0005 Step 3):
> - Invalid point in time (outside retention window)
> - Cannot find specified logical server
> - Database already exists with same name

### 3. Monitor Restore Progress (If State is Restoring)

Execute query **RFQ200** from [references/queries.md](references/queries.md) to check restore events:

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Monitor restore event progress"
- parameters: {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "MonRestoreEvents | where restore_request_id =~ '{RestoreRequestId}' | order by originalEventTimestamp desc | project originalEventTimestamp, event, restore_database_progress, message, exception_type | take 20"
}
```

**Analysis:**
- Repeating same events = stuck restore
- `exception_type` not empty = errors occurring
- "Non retriable error" with SSL/TLS = silent failure (see BRDB0005.6)
- Error 21105 with REPLICATION = Cloud Lifter regression

### 4. Diagnose Common Failure Scenarios

#### Scenario 1: Restore Request Not Created

If no restore request found in MonRestoreRequests (RFQ100) and management validation failed (RFQ300):
> 🚩 **Restore Validation Failed**
> 
> **Check the management operation error message for specific cause:**
> - Invalid point in time — verify time is within backup retention window
> - Source database not found — verify database exists using SterlingRestoreRequests.xts
> - Target database already exists — drop or rename target, retry

#### Scenario 2: Restore Stuck (Blank or Repeating Events)

If MonRestoreEvents (RFQ200) shows no events or repeating identical events:

Check for SQL process crashes using query **RFQ400**:

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Check for SQL process crashes during restore"
- parameters: {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "WinFabLogs | where ClusterName == '{ClusterName}' | where NodeName == '{NodeName}' | where Text contains 'sqlservr.exe' or Text contains 'sqlsatelliterunner' | project PreciseTimeStamp, NodeName, Text | order by PreciseTimeStamp desc | take 100"
}
```

**Exit codes from WinFabLogs (from TSG BRDB0005):**
- **Exit code 1460**: Named pipe timeout on subcore SLOs — mitigate with `Fix-StuckRestore.ps1`
- **Exit code 7148**: WinFab terminated process
- **Exit code 304**: SQL fast exit — check sqlsatelliterunner

#### Scenario 3: Restore Failed with Error

If RFQ100 shows `state` == "Failed":
> 🚩 **Restore Failed**
> - **Error Details**: Check `operation_details` column from RFQ100
>
> Route by error pattern in `operation_details`:
> - Server not found → Verify server exists, use restore-dropped-server if needed
> - Database already exists → Drop/rename target, retry
> - Invalid point in time → Verify time is within retention window, retry
> - SSL/TLS handshake error (error 258) → Silent failure, see BRDB0005.6
> - Error 21105 with replication → Cloud Lifter regression, use `Set-ServerConfigurationParameters` to enable FS: `SQL.Config_FeatureSwitches_Replication` = `on`
> - "Operation (Acquire) failed on file" → Blob lease conflict after failover during remote DB restore, follow TSG TRDB0040: Break Blob Lease
> - "Unknown error. ExecuteNonQuery requires an open and available Connection" → SQL engine dump during restore, query Azure Watson site with appName
> - Server DTU quota exceeded → Escalate to Provisioning, Elastic Pools and Elastic Jobs queue
> - PremiumRS without explicit target SLO → Restore hangs, follow BRDB0005.9 / BRDB0004 for manual restore with explicit SLO
> - Insufficient PFS-backed pool space → See BRDB0005.9: Stuck restore to Pool with insufficient space

#### Scenario 4: Long-Running Restore

If state is "Restoring" and RFQ200 shows advancing progress:
> ⚠️ **Long-Running Restore** — this may be normal for large databases.
>
> **Recommended Actions**:
> 1. Check `restore_database_progress` in RFQ200 to confirm progress is advancing
> 2. Check every 30 minutes for progress updates
> 3. If no progress for 2+ hours, escalate to backup/restore team

#### Scenario 5: V-Instance Stuck Restore

If appname starts with "v-" (restore verification instance):
> ⚠️ **V-Instance Stuck Restore** — follow BRDB0005.7: V-instance Troubleshooting

### 4b. Cancel Restore (If Needed)

**Customer self-service**: Ask customer to connect via SSMS and execute:
```sql
DROP DATABASE [target_dbname_as_per_restore_request]
```

**DevOps cancel**:
```
Cancel-RestoreRequest -OperationId {request_id}
```

**Note**: Get `request_id` from SterlingRestoreRequests XTS view or CMS query:
```sql
SELECT request_id, state, create_time FROM restore_requests
WHERE target_server_name = '{ServerName}' AND target_database_name = '{DatabaseName}'
ORDER BY create_time DESC
```

### 5. Post-Mitigation Verification

After applying any mitigation, verify restore state:

**Step 5a**: Check restore request state using query **RFQ500** from [references/queries.md](references/queries.md).

**Step 5b**: Verify restore progress in MonRestoreEvents:
```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Verify restore events after mitigation"
- parameters: {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "MonRestoreEvents | where restore_request_id =~ '{RestoreRequestId}' | order by originalEventTimestamp desc | project originalEventTimestamp, event, restore_database_progress, message, exception_type | take 20"
}
```

**Step 5c**: Confirm management operation completed:
```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Confirm management operation completed"
- parameters: {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "MonManagementOperations | where request_id contains '{RequestId}' | where event in ('management_operation_success', 'management_operation_failure', 'management_operation_canceled') | project originalEventTimestamp, event, operation_type, request_id | order by originalEventTimestamp desc"
}
```

**Success Criteria:**
- `state` changed to "Completed" in RFQ500
- `management_operation_success` event in MonManagementOperations
- Target database is accessible

## Summary Output Format

After completing analysis, provide summary:

> ## 🔍 **Restore Failure Analysis Summary**
> 
> **Restore Information:**
> - Logical Server: {LogicalServerName}
> - Source Database: {SourceDatabaseName}
> - Target Database: {TargetDatabaseName}
> - Point In Time: {PointInTime}
> - Restore Request ID: {RestoreRequestId}
> 
> **Restore State:**
> - State: {restore_state}
> - Error Code: {error_code}
> - Error Message: {error_message}
> 
> **Root Cause:**
> - {Identified issue}
> 
> **Recommended Actions:**
> {Numbered list of mitigation steps}
> 
> **Escalation:** {If needed, which team and why}

## Related References

- [references/queries.md](references/queries.md) — Kusto query definitions (RFQ100–RFQ500)
- [references/knowledge.md](references/knowledge.md) — Restore concepts, error codes, and expected durations
- [references/principles.md](references/principles.md) — Restore failure decision tree
- [references/report.md](references/report.md) — Output format templates
- [references/prep/sources.md](references/prep/sources.md) — TSG source URLs

## Related Skills

- **restore-dropped-server**: For server recovery after accidental deletion (DevOps only)
