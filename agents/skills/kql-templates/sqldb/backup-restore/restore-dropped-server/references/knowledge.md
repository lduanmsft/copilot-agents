!!!AI Generated. Manually verified!!!

# Terms and Concepts for Dropped Server Restore

## General Concepts

1. **DeferredDropped State**: Server state after deletion where the server metadata still exists but is pending cleanup. Databases are in Tombstoned state. Recoverable within 7 days.

2. **Tombstoned State**: Database state within a DeferredDropped server. Indicates database was dropped as part of server deletion and may be recoverable.

3. **PITR (Point-In-Time Restore)**: Restores a database to a specific point in time using available backup chain (full + differential + log backups).

4. **DNS Availability**: Whether the server's DNS name (`{server}.database.windows.net`) is available for reclaim. Critical for DeferredDropped recovery.

5. **CRI (Customer Reported Incident)**: Support incident filed by the customer. Required within 7 days of drop for server recovery.

## Recovery Methods

### Method A: DeferredDropped Recovery (Preferred)
- Requires DNS name available, server in DeferredDropped state, databases in Tombstoned state
- Uses `Recover-LogicalServer` CAS command
- Recovers the server with **master only** — customer must then self-service restore individual databases

### Method B: PITR to New Server
- Fallback when DNS is unavailable or server not in DeferredDropped state
- Requires customer to create empty databases with identical names
- Uses `Restore-DatabaseFromDroppedServer.ps1` script from DS Console (`Scripts\BackupRestore`)
- Use RSV200 query to verify backup existence via `List-XStoreBlobs`, RSV300 to generate restore scripts

## Critical Constraints

- **7-day hard limit**: After 7 days, backups are deleted per compliance requirements
- **DevOps only**: This procedure is restricted to DevOps engineers
- **TDE/CMK scenarios**: Require additional key vault permission setup

## Related Documentation

### Internal Documentation (eng.ms / ADO Wiki)
- [BRDB0019 - Dropped Server Restore (DevOps Only)](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-backup-restore/sql-backup-restore/brdb0019-dropped-server-restore-_devops-only_)
  - ADO Wiki: `TSG-SQL-DB-DataIntegration` > `/BackupRestore/BRDB0019 Dropped Server Restore` (project: Database Systems)
