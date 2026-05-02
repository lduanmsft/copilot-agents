!!!AI Generated. Manually verified!!!

# Terms and Concepts for Restore Failure Analysis

## General Concepts

1. **PITR (Point-In-Time Restore)**: Restores a database to a specific point in time using the backup chain.

2. **Restore State Machine**: Internal workflow system that manages restore request lifecycle from creation through completion or failure.

3. **Restore States**: Lifecycle states of a restore operation:
   - **Ready**: Request created, waiting to start
   - **Restoring**: Restore in progress
   - **Completed**: Restore succeeded
   - **Failed**: Restore failed with error
   - **Cancelled**: Restore cancelled by user/system (e.g., target DB dropped)

## Exit Codes (from WinFabLogs)

Exit codes are found in WinFabLogs when sqlservr.exe crashes during restore:

| Exit Code | Meaning |
|-----------|---------|
| 1460 | Named pipe timeout (subcore SLOs) — mitigate with `Fix-StuckRestore.ps1` |
| 7148 | WinFab terminated SQL process |
| 304 | SQL fast exit — check sqlsatelliterunner |

## Common Validation Failures

These appear in `MonManagementOperations` message column when `management_workflow_restore_request_failure` event is found:

- Invalid point in time (outside retention window)
- Cannot find specified logical server
- Database already exists with same name

## Error Patterns in MonRestoreEvents

- "Non retriable error" with SSL/TLS = silent failure (BRDB0005.6)
- Error 21105 with REPLICATION = Cloud Lifter regression
- "Operation (Acquire) failed on file" = blob lease conflict after failover (TRDB0040)
- "Unknown error. ExecuteNonQuery requires an open and available Connection" = SQL engine dump during restore (query Watson with appName)
- "Could not perform the operation because server would exceed the allowed Database Throughput Unit quota" = insufficient DTU quota (escalate to Provisioning team)

## Related Sub-TSGs

- **BRDB0005.1**: Hyperscale restore stuck/failure
- **BRDB0005.6**: Restore fails silently (SSL/TLS timeout)
- **BRDB0005.7**: V-instance Troubleshooting (appname starts with "v-")
- **BRDB0005.9**: Stuck restore to Pool with insufficient PFS space
- **BRDB0004**: Manual restore/geo-restore for customer

## Related Skills

- **restore-dropped-server**: For server recovery after accidental deletion (DevOps only)

## Related Documentation

### Internal Documentation (eng.ms / ADO Wiki)
- [BRDB0005 - Restore Stuck/Failure Investigation](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-backup-restore/sql-backup-restore/brdb0005-restore-stuck_failure-investigation)
  - ADO Wiki: `TSG-SQL-DB-DataIntegration` > `/BackupRestore/BRDB0005 Restore Stuck_Failure Investigation` (project: Database Systems)
