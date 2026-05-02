!!!AI Generated. Manually verified!!!

# Debug Principles for LTR Backup Out of SLA

## ICM Validation Decision Tree

An LTR backup SLA incident is valid **only if ALL** conditions are true:

1. **dropped_time is null** — database has not been dropped
2. **Retention policy exists** — at least one of weekly/monthly/yearly retention is non-null and != PT0S
3. **next_backup_time is before UTCNow** — backup is overdue
4. **All expected LTR backups exist** — no backup was skipped or missed per policy

🚩 If any condition fails → Mitigate as noise, mark 'RCA needed' for expert review.

## Pre-Mitigation Safety Checks

**BEFORE mitigating the incident:**
1. Make sure no LTR backup has been skipped or missed
2. Backfill any missing backups if required
3. Verify `next_backup_time` has been updated

🚩 **Only mitigate** if needed LTR backups have been backfilled/happened AND `next_backup_time` updated.

## Elastic Pool Mitigation Caution

- ⚠️ Mitigate **one database from one pool at a time**
- Move database out of pool temporarily (run updateslo_script once)
- Wait for full backup to complete
- Move database back to pool (run same updateslo_script again)

## Escalation Contacts

- LTR committers: pixia / tisingh / penzh
- Regression issues: ltrcommitters@microsoft.com
