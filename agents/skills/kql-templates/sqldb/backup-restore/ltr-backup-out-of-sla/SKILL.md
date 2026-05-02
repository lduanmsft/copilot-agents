---
name: ltr-backup-out-of-sla
description: Debug Azure SQL Database Long-Term Retention (LTR) backup out of SLA alerts for Sterling databases. Analyzes LTR policies, validates incidents, identifies root causes including full backup failures, LTR copy timeouts, and elastic pool issues. Required inputs from calling agent - kusto-cluster-uri, kusto-database, and database configuration variables from get-db-info skill.
---

# Debug LTR Backup Out of SLA Alerts

Debug Long-Term Retention (LTR) backup out of SLA alerts for Azure SQL Database Sterling databases when backups do not happen by expected time.

## Background

LTR backups are based on full backups. The Backup/Restore service LTR threads copy qualified full backups (according to customer policies) to LTR containers. LTR backups are expected to happen and be kept according to customers' set policies.

**Important:** This guide is **only for Sterling databases**. For VLDB databases, refer to TSG HSLTR0002.

## Required Information

This skill requires the following inputs (should be obtained by the calling agent):

### From User or ICM:
- **Logical Server Name**
- **Logical Database Name** 
- **Logical Database ID** (GUID format)

### From execute-kusto-query skill:
- **kusto-cluster-uri**
- **kusto-database**
- **region**

### From get-db-info skill (optional, if available):
- **physical_database_id**
- **service_level_objective**
- All other database environment variables

**Note**: The calling agent should use the `execute-kusto-query` skill before invoking this skill.

## Critical Pre-Mitigation Steps

🚩 **BEFORE mitigating the incident:**
1. Make sure no LTR backup has been skipped or missed
2. Backfill any missing backups if required
3. Verify next_backup_time has been updated

🚩 **Only mitigate** if needed LTR backups have been backfilled/happened AND next_backup_time updated.

## Workflow

### 1. Check if ICM is Still Valid

Query CMS using HTTPQueryTool or Ltr V2 overview.xts view:

```sql
SELECT TOP 10 weekly_retention, monthly_retention, yearly_retention, week_of_year, 
       dropped_time, logical_database_created_time, last_backup_time, 
       next_backup_time, state 
FROM ltr_configurations 
WHERE logical_database_id = '{LogicalDatabaseId}'
```

**ICM is valid if ALL conditions are true:**

a) **dropped_time is null** (database not dropped)

b) **Retention policy exists**: At least one of weekly_retention, monthly_retention, yearly_retention, or week_of_year must be non-null and not equal to PT0S

c) **next_backup_time is before UTCNow** (backup is overdue)

d) **Based on policy, all LTR backups exist and no backup was skipped or missed**

**If incident does NOT meet all conditions:**
- Mitigate as noise
- Mark 'RCA needed' so expert can investigate

**If incident is valid:**
- Continue to identify root cause

### 2. Identify Root Cause from Known Issues

The following are known causes for LTR backup out of SLA:

a) **Expected full backup did not happen**
b) **LTR logic intentionally skipped last full backup**
c) **LTR copy timeout in TR**
d) **SubscriptionId disabled** (VLDB gap)
e) **LTR regression** (reach out to ltrcommitters@microsoft.com)

**Existing Umbrella Incidents:**
- Incident 619230339: GeoDr secondary stuck at TLB due to CMK key access
- Incident 626552360: LTR backup copy timeout in TR
- Incident 628197655: LTR backup not happen in VLDB due to subscription disabled

### 3. Diagnose: Expected Full Backup Did Not Happen

Execute Kusto Query:
```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Check full backup status for LTR analysis"
- parameters: {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "MonBackup | where TIMESTAMP >= ago(5d) | where logical_database_id contains '{LogicalDatabaseId}' | where backup_type == 'Full' or details contains '[LTRV2]' | project TIMESTAMP, event_type, backup_type, details, sql_error_message, logical_database_name, logical_server_name | order by TIMESTAMP desc"
}
```

**Common Issues:**

#### Issue: Databases in Basic SLO - Resource Limitations
**Cause**: Memory/connections exhaust in Basic tier
**Mitigation**: None available (limitation of Basic SLO)

#### Issue: Elastic Pool - Full Backup Scheduling Cannot Keep Up
Check if database's full backup has been delayed using Kusto query above.

**Mitigation** (EXECUTE WITH CAUTION):
1. Use Ltr V2 overview.xts view, tab "Sterling DBs", column "updateslo_script"
2. Move database out of pool temporarily (run updateslo_script once)
3. Wait for full backup to complete
4. Move database back to pool (run same updateslo_script again)

**⚠️ CRITICAL**: Mitigate **one database from one pool at a time**.

#### Issue: Restore HeaderOnly Timeout
**Error**: "The backup metadata is required to create the RecoveryPointMetadata. Check the exception thrown by Restore HeaderOnly."

**Mitigation**: Increase timeout using CAS command:
```
Set-ServerConfigurationParameters -ServerName {LogicalServerName} 
    -Parameters @('SQL.Config_BackupService_BackupMetadataRestoreHeaderOnlyTimeOutInSeconds') 
    -Values @('10800')
```

#### Issue: Storage Limit Reached
**Error**: "Failed to flush the commit table to disk in dbid 9 due to error 1132"

**Mitigation**: Enable trace flag 3013 on the instance:
```
Get-FabricNode -NodeName _DB_0 -NodeClusterName {ClusterName} | Invoke-DbccCommand -AppName {AppName} -Command TRACEON -TraceFlag 3013
```

#### Issue: FullBackupContainerName Metadata Missing
**Symptoms**: LTR backup fails because `FullBackupContainerName` entry missing in server-level backup storage container metadata.

**Mitigation**:
1. Get server-level backup storage container from CMS:
   ```sql
   SELECT asa.storage_account_subscription_id, ls.backup_storage_account_name, ls.backup_storage_container_name
   FROM logical_servers ls
   JOIN azure_storage_accounts asa ON ls.backup_storage_account_name = asa.storage_account_name
   WHERE ls.logical_server_id = '{LogicalServerId}'
   ```
2. Request JIT access to the storage account subscription_id from SAW
3. Navigate to full backup path: `container/backup/{LogicalDatabaseId}/Full`
4. Locate and recreate the missing `FullBackupContainerName` metadata (**case-sensitive**)
- Technical RCA: ICM #353674706

#### Issue: "Could not allocate space for object" / "Failed to flush the commit table to disk"
**Mitigation**: Consult LTR committers (ICM #351989110)

#### Issue: GeoDR Seeding Caused Full Backup Failure
**Error**: "Backup, file manipulation operations (such as ALTER DATABASE ADD FILE) and encryption changes on a database must be serialized."
**Mitigation**: Request assistance from GeoDR on-call.

#### Issue: "Authorization token not loaded for accessing container" or "403 Forbidden"
**Mitigation**: Refer to TSG LTR0014: SQLDB LTR copy failure alert.

### 3b. Diagnose: LTR Copy Started But Never Finished (Scenario B)

If MonBackup shows `BACKUP_LTR_COPY_START` but NOT `BACKUP_LTR_COPY_END` for >3 days, the LTR thread is likely hung.

**Mitigation**:
1. Increase database internal backup retention to 30 days (for backfill safety)
2. Kill the SqlSatelliteRunner instance to create a new LTR thread
3. A new LTR backup copy will start soon
4. Wait until new LTR copy completes and `next_backup_time` changes before mitigating
5. If thread was hung for a week+, new thread may skip previous week's backup — follow backfill section

### 4. Check for Skipped/Missed Backups and Backfill

**Use Ltr V2 overview.xts view**:
1. Input logical_database_id in filter
2. Review "LTR backups" tab to verify all expected backups exist per policy

**If backups are missing, determine backfill need:**

1. Full backup taken <6 days after previous → not considered for LTR (mitigate as noise + "RCA needed")
2. Full backup taken while database was GeoDR secondary → not considered for LTR (mitigate as noise + "RCA needed")
3. Otherwise → backfill required

**Backfill Procedure:**

1. Enable prerequisite feature switch (wait for apps to reach Ready):
   ```
   Set-ServerConfigurationParameters -ServerName {LogicalServerName} -Parameters @('Worker.ISO\SQL.Config_FeatureSwitches_DoNotUpdateSysDatabsesForRestoreVerification', 'Worker.ISO.Premium\SQL.Config_FeatureSwitches_DoNotUpdateSysDatabsesForRestoreVerification') -Values @('on','on') -ClientTimeoutInSecs 10
   ```
2. Generate backfill commands using query **LTR200** from [references/queries.md](references/queries.md)
3. Run the backfill script:
   ```
   .\Backfill-NonHSLtrBackup.ps1 -LogicalServerId {LogicalServerId} -LogicalDatabaseId {LogicalDatabaseId} -FullBackupTime '{FullBackupTime}' -PolicyToApply {PolicyToApply}
   ```
   - `PolicyToApply` values: `w` (weekly), `m` (monthly), `y` (yearly)
   - `FullBackupTime` must match exact format from Kusto output (in quotes)
4. After execution, verify backup exists and monitor restore verification until completion

**If backfills needed:**
- Do NOT mitigate incident until backfills complete
- Contact LTR committers for complex scenarios: pixia / tisingh / penzh (ltrcommitters@microsoft.com)

### 5. Verify LTR Copy Timeout (TR Issue)

Execute Kusto query to check for LTR copy timeout events:
```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Check for LTR copy timeout events"
- parameters: {
    "cluster-uri": "{kusto-cluster-uri}",
    "database": "{kusto-database}",
    "query": "MonBackup | where TIMESTAMP >= ago(5d) | where logical_database_id contains '{LogicalDatabaseId}' | where details contains 'LTR' and details contains 'timeout' | project TIMESTAMP, event_type, details, sql_error_message"
}
```

**If timeout detected:**
> 🚩 **LTR Copy Timeout Detected**
> - Link to umbrella incident 626552360
> - Escalate to backup/restore team if not resolved

## Summary Output Format

After completing analysis, provide summary:

> ## 🔍 **LTR Backup SLA Analysis Summary**
> 
> **Database Information:**
> - Logical Server: {LogicalServerName}
> - Logical Database: {LogicalDatabaseName}
> - Logical Database ID: {LogicalDatabaseId}
> 
> **LTR Policy:**
> - Weekly Retention: {weekly_retention}
> - Monthly Retention: {monthly_retention}
> - Yearly Retention: {yearly_retention}
> - Next Backup Time: {next_backup_time}
> 
> **Root Cause:**
> - {Identified issue category}
> - {Specific diagnostic findings}
> 
> **Recommended Actions:**
> {Numbered list of mitigation steps}
> 
> **Backfill Status:**
> - Required: {Yes/No}
> - Completed: {Yes/No/Pending}

## Related References

- [references/queries.md](references/queries.md) — Kusto query definitions (LTR100–LTR200)
- [references/knowledge.md](references/knowledge.md) — LTR terminology and concepts
- [references/principles.md](references/principles.md) — ICM validation and pre-mitigation checks
- [references/report.md](references/report.md) — Output format templates
- [references/prep/sources.md](references/prep/sources.md) — TSG source URLs

Contact LTR committers for complex scenarios: pixia / tisingh / penzh

LTR Policy Documentation: https://learn.microsoft.com/en-us/azure/azure-sql/database/long-term-retention-overview
