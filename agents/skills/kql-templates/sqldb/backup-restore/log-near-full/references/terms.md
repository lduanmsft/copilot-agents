# Terminology for Log Full/Near Full Analysis

## Database Identifiers

**Physical Database ID (physical_database_id)**
- GUID format identifier for the actual database instance
- Example: `06b4a46b-4576-4bb7-b3a1-19ed916a65c4`
- Used in all Kusto queries and backend SQL queries

**Logical Database Name / Logical Server Name**
- User-visible names in Azure Portal

**AppName (Application Name)**
- Internal Service Fabric application name

## Log Space Metrics

**LogSpaceUsedGB** - Current log space in use (GB)
**MaxLogSizeGB** - Maximum allowed log size (GB)
**LogUsedPercentage** - (LogSpaceUsedGB / MaxLogSizeGB) * 100

**Log Reuse Wait Description (log_reuse_wait_desc)**
- **NOTHING**: Normal state, log can be truncated
- **CHECKPOINT**: Waiting for checkpoint
- **LOG_BACKUP**: Waiting for log backup
- **ACTIVE_BACKUP_OR_RESTORE**: Active backup/restore operation
- **ACTIVE_TRANSACTION**: Long-running transaction
- **AVAILABILITY_REPLICA**: Waiting for HA secondary replicas
- **REPLICATION**: Waiting for CDC/Synapse Link/Fabric Mirroring
- **XTP_CHECKPOINT**: Waiting for in-memory OLTP checkpoint
- **OLDEST_PAGE**: Waiting for dirty pages to be written

## Log Sequence Number (LSN)

**LSN** - Log Sequence Number, unique identifier for log records
**Last Scan LSN** - For CDC, last LSN scanned by capture job
**Forwarder LSN** - For GeoDR, last LSN forwarded to secondary

## Replication Features

**CDC (Change Data Capture)** - Tracks row-level changes, uses log reader
**Synapse Link** - Near real-time data integration with Azure Synapse
**Fabric Mirroring** - Integration with Microsoft Fabric

## High Availability

**Primary Replica** - Read-write replica
**Secondary Replica** - Read-only replica that receives log records
**Forwarder** - Special replica for GeoDR
**Redo Queue** - Queue of log records waiting to be applied on secondary

## Directory Quota

**DirectoryQuotaNearFull** - Node directory has insufficient space
**Stale Directory** - Directory consuming space but no longer in use
**Orphaned RBPEX Pages** - In-memory OLTP pages not cleaned up properly

## Related Documentation

### Internal Documentation (eng.ms / ADO Wiki)
- [BRDB0156 - Log Near Full](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-backup-restore/sql-backup-restore/brdb0156-log-near-full)
  - ADO Wiki: `TSG-SQL-DB-DataIntegration` > `/BackupRestore/BRDB0156 Log near full` (project: Database Systems)
