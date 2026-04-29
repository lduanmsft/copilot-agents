# Proposed Addition to Backup-Scenarios.md

> **Insert after Issue 2 (Slow backup performance after enabling TDE)**

---

**Issue 3:**

Slow backup/restore performance when TDE is enabled with EKM (Azure Key Vault)

**Symptoms:**

- Backup or restore of a TDE-enabled database is significantly slower than expected.
- The `backup_restore_progress_trace` XEvent or TF 3004/3605 output shows long pauses between phases.
- The SQL Server error log shows repeated `Refresh DEK for DBID` entries during backup/restore.
- The issue is more pronounced when using EKM with a remote key store such as Azure Key Vault (AKV).

**Cause:**

When TDE is configured with an EKM provider (e.g., Azure Key Vault), SQL Server must contact the EKM provider to decrypt the Database Encryption Key (DEK) during backup and restore operations. In certain code paths, the DEK is not cached, resulting in frequent network round-trips to the remote EKM provider:

| Operation | DEK Caching Behavior | EKM Call Frequency |
|-----------|---------------------|-------------------|
| **Log Flush** | Caches 8 most recently used VLFs; accessing a new VLF triggers an EKM call | Per new VLF |
| **Backup** | SQL 2016 RTM/SP1: No cached DEK is used | Per VLF (or more frequently) |
| **Restore** | No cached DEK is used at all | Per **4MB log block** (very frequent) |

For restore operations, the impact is especially severe — SQL Server contacts the EKM provider for every 4MB of log block, not just every VLF. This generates a large volume of network requests to AKV, causing significant latency accumulation.

This issue also affects DB Mirroring, causing very slow redo rates on the mirror server when TDE with EKM is enabled.

**Diagnosis:**

1. Enable the `backup_restore_progress_trace` XEvent (SQL 2016+) or trace flags 3004 and 3605 to identify which backup/restore phase is slow.
2. Check the SQL Server error log for repeated `Refresh DEK for DBID` entries — each entry may represent a round-trip to AKV.
3. Monitor AKV request logs for throttling responses (HTTP 429) during the backup/restore window.
4. Measure network latency between the SQL Server instance and the AKV endpoint.

**Known Fixes:**

| Fix | Version | Description |
|-----|---------|-------------|
| Defect 11514403 | SQL Server 2016 SP2 | Fixed the restore code path to use cached DEK |
| Bug 11565899 | SQL Server 2016 SP1 CU8 | Additional DEK caching improvements |
| OD Hotfix (MSIT) | SQL Server 2016+ | Fallback to cached DEK when the EKM request fails (improves availability during intermittent network issues) |

**Workaround:**

- Update to a SQL Server version that includes the DEK caching fixes (SQL Server 2016 SP2 or later).
- Ensure low-latency network connectivity between the SQL Server instance and the AKV endpoint.
- Monitor and mitigate AKV throttling (consider increasing AKV throughput limits if needed).
- For restore scenarios with large transaction logs, consider using larger VLF sizes to reduce the total number of DEK refresh calls.

**References:**

- [Performance issues with EKM TDE transaction log (CSS Wiki - Backup & Restore)](https://dev.azure.com/Supportability/SQLServerWindows/_wiki/wikis/SQLServerWindows?pagePath=/SQL-Server-On-Premise/Troubleshooting-Guides/Backup-&-Restore/Miscellaneous/Performance-issues-with-EKM-TDE-transaction-log)
- [Performance issues with EKM TDE transaction log (CSS Wiki - Security Workflow)](https://dev.azure.com/Supportability/SQLServerWindows/_wiki/wikis/SQLServerWindows?pagePath=/SQL-Server-On-Premise/Troubleshooting-Guides/Security-Workflow/SQL-Security-Workflow/Workflow/Performance-issues-with-EKM-TDE-transaction-log)
- RFC Work Item 8960487 — PG response detailing when SQL Server contacts the EKM provider
