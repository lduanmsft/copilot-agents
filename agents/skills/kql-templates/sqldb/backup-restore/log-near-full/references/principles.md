!!!AI Generated. Manually verified!!!

# Debug Principles for Log Full/Near Full Analysis

## Log Truncation Holdup Decision Tree

1. **Identify the holdup reason** from MonFabricThrottle or `sys.databases.log_reuse_wait_desc`
2. **Route to appropriate mitigation** based on holdup reason:

| Holdup Reason | Investigation Path |
|---------------|-------------------|
| ACTIVE_BACKUP_OR_RESTORE | Check active backups (LOG300), Hyperscale reverse migration (Soc074) |
| LOG_BACKUP | Check backup history (LOG300), log backup failures |
| REPLICATION | Identify feature via LOG400 (CDC/Synapse Link/Fabric Mirroring), route to appropriate TSG |
| AVAILABILITY_REPLICA | Check replica health (LOG500), redo queue, GeoDR (LOG520) |
| ACTIVE_TRANSACTION | Identify long-running transactions, check CDC/Synapse Link involvement |
| CHECKPOINT / OLDEST_PAGE | Execute manual checkpoint via JIT |
| XTP_CHECKPOINT | Check in-memory OLTP checkpoint (HK0020), orphaned RBPEX |

## Severity Assessment

Severity is determined by the ICM incident (typically Sev 2 or Sev 3 when log space exceeds thresholds). The holdup reason determines the investigation path, not the priority — all holdup reasons require action when log is near full.

## DirectoryQuotaNearFull

- **If DirectoryQuotaNearFull detected**: Stop further log analysis. Transfer to **Azure SQL DB/SQL DB Perf : InterProcessRG/ResourceLimits** queue or refer to TSG PERFTS016.
- DirectoryQuota issues take precedence over log holdup analysis.

## Special Cases

1. **Hyperscale Reverse Migration + LOG_BACKUP**: Transfer to Hyperscale Migration queue. Migration may need to be canceled to release log.
2. **CDC + AVAILABILITY_REPLICA**: Follow CDC mitigation path (TSG CDC0001, "Case 4: Kill active Txn") first.
3. **CHECKPOINT/OLDEST_PAGE**: Only one manual checkpoint should be needed. If issue persists, investigate deeper.
4. **XTP_CHECKPOINT + Orphaned RBPEX**: Link repair item https://msdata.visualstudio.com/_workitems/edit/1851900
