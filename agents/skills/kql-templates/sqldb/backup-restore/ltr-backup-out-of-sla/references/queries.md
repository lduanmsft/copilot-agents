!!!AI Generated. Manually verified!!!

# Kusto Queries for LTR Backup SLA Analysis

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Resource identifiers:**
- `{LogicalDatabaseId}`: Logical database ID (GUID format)
- `{LogicalDatabaseName}`: Logical database name (optional alternative filter)
- `{LogicalServerName}`: Logical server name
- `{LogicalServerId}`: Logical server ID (GUID format, for backfill scripts)

---

## LTR100 - Full Backup and LTR Copy Events

**Purpose:** Check full backup status and LTR copy events over the last 5 days to diagnose why LTR backup is out of SLA.

**What to look for:**
- `BACKUP_END` events for Full backups — confirm full backups are completing
- `BACKUP_LTR_COPY_START` / `BACKUP_LTR_COPY_END` events — track LTR copy progress
- If `BACKUP_LTR_COPY_START` exists without `BACKUP_LTR_COPY_END` for >3 days, the LTR thread may be hung
- Error messages in the `details` column

```kql
MonBackup
| where TIMESTAMP >= ago(5d)
| where logical_database_id contains '{LogicalDatabaseId}'
| where backup_type == 'Full' or details contains '[LTRV2]'
| project TIMESTAMP, event_type, backup_type, details, sql_error_message, logical_database_name, logical_server_name
| order by TIMESTAMP desc
```

---

## LTR200 - Full Backup Details for Backfill Analysis

**Purpose:** Fetch full backup details with LTR backfill script commands. Used to identify missed LTR backups and generate remediation commands.

**What to look for:**
- Gaps in weekly full backups (indicating missed LTR opportunities)
- The `backfill_ltr_backup_script` column for automated remediation
- Backup retention days to understand the policy window

```kql
let logicalDatabaseIdFilter = '{LogicalDatabaseId}';
let logicalDatabaseNameFilter = '{LogicalDatabaseName}';
MonBackup
| where (isnotempty(logicalDatabaseIdFilter) and logical_database_id in~ (logicalDatabaseIdFilter))
    or (isnotempty(logicalDatabaseNameFilter) and logical_database_name in~ (logicalDatabaseNameFilter))
| where backup_type =~ 'Full'
| where event =~ 'database_backup_metadata'
| where originalEventTimestamp between(ago(13d) .. ago(4d))
| extend logical_database_id = toupper(logical_database_id)
| join kind=leftouter (
    MonAnalyticsDBSnapshot
    | extend logical_database_id = toupper(logical_database_id)
    | summarize arg_max(end_utc_date, logical_server_id, backup_retention_days) by logical_database_id
    ) on $left.logical_database_id == $right.logical_database_id
| project-away end_utc_date, logical_database_id1
| parse backup_path with * 'Full/' full_backup_time '_S' num_stripes '_' * '.bak'
| extend subscription_id = SubscriptionId
| extend full_backup_time = todatetime(strcat(full_backup_time, "Z"))
| extend full_backup_time = format_datetime(full_backup_time, 'yyyy-MM-dd HH:mm:ss')
| extend backup_start_time = format_datetime(todatetime(backup_start_date), 'yyyy-MM-dd HH:mm:ss')
| extend backup_end_time = format_datetime(todatetime(backup_end_date), 'yyyy-MM-dd HH:mm:ss')
| extend get_policy_cas = strcat('Get-DatabaseLTRPolicy -LogicalServerName ', logical_server_name, ' -LogicalDatabaseName ', logical_database_name)
| extend get_ltr_backups_cas = strcat('(Get-LtrBackup -SubscriptionId ', subscription_id, ' -LogicalServerName ', logical_server_name, ' -LogicalDatabaseName ', logical_database_name, ') | Select-Object BackupTime, BackupExpirationTime, BackupState')
| extend backfill_ltr_backup_script = strcat('./Backfill-NonHSLtrBackup.ps1 -LogicalServerId ', logical_server_id, ' -LogicalDatabaseId ', logical_database_id, ' -FullBackupTime "', full_backup_time, '" -PolicyToApply')
| summarize make_set(backup_path), make_set(backfill_ltr_backup_script), take_any(backup_retention_days)
    by subscription_id, logical_server_name, logical_database_name, logical_database_id, get_policy_cas, get_ltr_backups_cas
| project-reorder logical_database_id, get_policy_cas, get_ltr_backups_cas, set_backfill_ltr_backup_script
| order by logical_database_id asc
```

---

## LTR Configuration (CMS Query)

**Purpose:** Verify LTR policy and next_backup_time via CMS.

**Method:** Execute via HTTPQueryTool or `Ltr V2 overview.xts` view:

```sql
SELECT TOP 10 weekly_retention, monthly_retention, yearly_retention, week_of_year, dropped_time, logical_database_created_time, last_backup_time, next_backup_time, state
FROM ltr_configurations
WHERE logical_database_id = '{LogicalDatabaseId}'
```

**What to look for:**
- `dropped_time` is NULL (ICM invalid if non-null)
- Policy values are NOT all null or `PT0S` (ICM invalid if all are `PT0S`)
- `next_backup_time` is before UTC now (ICM valid if overdue)
- `state` reflects active LTR configuration

---

## Notes

- Use the `get_policy_cas` and `get_ltr_backups_cas` commands from LTR200 output to validate LTR backups against policy
- For backfill: Use `Backfill-NonHSLtrBackup.ps1` with PolicyToApply = `w` (weekly), `m` (monthly), or `y` (yearly)
- Umbrella incidents for known issues: 619230339 (GeoDR/CMK), 626552360 (copy timeout), 628197655 (VLDB subscription)
- Escalation contact: ltrcommitters@microsoft.com (pixia / tisingh / penzh)
- Source TSG: LTR0011 (ADO Wiki: `/BackupRestore/LTR0011 LTR Backup Out of SLA Alert` in TSG-SQL-DB-DataIntegration)
