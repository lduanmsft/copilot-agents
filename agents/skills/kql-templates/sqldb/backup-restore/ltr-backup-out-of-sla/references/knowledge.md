!!!AI Generated. Manually verified!!!

# Terms and Concepts for LTR Backup Out of SLA

## General Concepts

1. **Long-Term Retention (LTR)**: Feature that copies qualified full backups to LTR containers according to customer-defined retention policies (weekly, monthly, yearly).

2. **Sterling Database**: Standard Azure SQL Database tier (non-Hyperscale). This skill applies only to Sterling databases. For VLDB databases, refer to TSG HSLTR0002.

3. **LTR Policy**: Customer-configured retention schedule with `weekly_retention`, `monthly_retention`, `yearly_retention`, and `week_of_year` parameters.

4. **next_backup_time**: Timestamp indicating when the next LTR backup is expected. If this is before UTCNow, the backup is overdue.

5. **dropped_time**: If non-null, the database has been dropped and the incident should be mitigated as noise.

## LTR Backup Flow

1. Full backup completes on the database
2. LTR threads evaluate whether the full backup qualifies for LTR per customer policy
3. Qualified full backups are copied to LTR containers
4. `next_backup_time` is updated after successful copy

## Known Failure Categories

- **Full backup did not happen**: No qualifying full backup available for LTR copy
  - Basic SLO: memory/connection exhaustion (no mitigation available)
  - Elastic pool: full backup scheduling bottleneck (move DB out of pool temporarily)
  - Restore HeaderOnly timeout (increase to 10800 seconds)
  - Storage limit (error 1132): enable TF 3013
  - FullBackupContainerName metadata missing: recreate metadata in storage container
  - "Could not allocate space for object": consult LTR committers
  - GeoDR seeding: request GeoDR on-call assistance
  - Authorization token / 403 Forbidden: see LTR0014
- **LTR copy started but never finished (Scenario B)**: LTR thread hung for >3 days — kill SqlSatelliteRunner to create new LTR thread
- **LTR logic intentionally skipped backup**: Policy evaluation determined backup was not needed
- **LTR copy timeout in TR**: Copy to LTR container timed out
- **SubscriptionId disabled (VLDB gap)**: Subscription-level issue
- **LTR regression**: Unexpected behavior requiring engineering investigation

## Backfill Procedure

When LTR backups are missing, the `Backfill-NonHSLtrBackup.ps1` script copies the qualifying full backup to LTR storage. Requires:
- Feature switch `DoNotUpdateSysDatabsesForRestoreVerification` enabled (both Worker.ISO and Worker.ISO.Premium)
- Parameters: `-LogicalServerId`, `-LogicalDatabaseId`, `-FullBackupTime` (exact UTC), `-PolicyToApply` (`w`/`m`/`y`)

## Related Documentation

- [LTR Policy Overview](https://learn.microsoft.com/en-us/azure/azure-sql/database/long-term-retention-overview)
