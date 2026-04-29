# MI KQL Template Audit Report

## Summary
- Total skills audited: 1765
- Skills with >=1 issue: 756
- Error instances logged: 796
- Error rate: 42.8%

> Notes: I scanned all 5 files for `TableName`/query alignment and sampled suspicious entries across every file. The dominant failure mode is notebook/doc export artifacts: many skills are prose blocks, isolated `let` statements, or mid-pipeline fragments rather than runnable KQL.

## Error Type 1: Wrong TableName
| Skill ID | File | TableName in YAML | Actual Table in Query | Fix |
|----------|------|-------------------|----------------------|-----|
| MI-availability-9 | availability.yaml | `MonRecoveryTraceMonRecoveryTrace` | `MonRecoveryTrace` | Normalize `TableName` to the real source table. |
| MI-performance-119 | performance.yaml | `MonQueryProcessingMonQueryProcessing` | `MonQueryProcessing` | Remove duplicated table token introduced by export. |
| MI-performance-120 | performance.yaml | `MonSqlSampledBufferPoolDescriptorsCheck` | `MonSqlSampledBufferPoolDescriptors` | Keep the note (`Check buffer pool page types`) out of `TableName`. |
| MI-performance-121 | performance.yaml | `MonDmOsWaitstatsMonSqlRgHistory` | `MonSqlRgHistory` | Split the prose from the query and set `TableName` to the real table. |

## Error Type 2: Broken/Invalid KQL

Detected at scale: **646** skills. Representative examples below.

| Skill ID | File | Issue Description |
|----------|------|-------------------|
| MI-general-1 | general.yaml | `ExecutedQuery` is a Chinese prose overview, not KQL. |
| MI-general-46 | general.yaml | Chapter summary text stored as `ExecutedQuery`. |
| MI-performance-3 | performance.yaml | Work-item guidance text pasted into `ExecutedQuery`; no runnable KQL. |
| MI-performance-7 | performance.yaml | Starts with a pipe and ends at `let leadblockers=`; truncated mid-query. |
| MI-performance-101 | performance.yaml | Valid KQL is concatenated with long prose/doc text and additional table names. |
| MI-availability-1 | availability.yaml | Contains only `let ServerName = "marketman-prod-main-db";` with no query body. |
| MI-availability-2 | availability.yaml | Contains only `let DatabaseName = "MarketManProd";` with no query body. |
| MI-availability-46 | availability.yaml | Provisioning chapter description pasted into `ExecutedQuery`. |
| MI-backup-restore-6 | backup-restore.yaml | Only variable declarations (`topNumber`, `backuptype`); no table/query. |
| MI-backup-restore-69 | backup-restore.yaml | Single `let lookback = ...` statement; query body missing. |
| MI-networking-1 | networking.yaml | Connectivity overview text mixed with `MonLogin`; not valid KQL. |
| MI-networking-23 | networking.yaml | `ExecutedQuery` is only `MonAzureActiveDirService - Overview (visualstudio.com)`. |
| MI-networking-35 | networking.yaml | Mid-pipeline fragment beginning with `| where ...`; source table missing. |
| MI-networking-90 | networking.yaml | Mitigation instructions (“Monitor the progress of seeding...”) stored as KQL. |

## Error Type 3: Wrong Category
| Skill ID | File | Current Category | Should Be |
|----------|------|-----------------|-----------|
| MI-performance-12 | performance.yaml | Performance | Networking / login telemetry |
| MI-availability-8 | availability.yaml | Availability | Networking / read-scale connectivity |
| MI-general-54 | general.yaml | General | Networking / login telemetry |

## Error Type 4: Parameterization Issues

Detected at scale: **132** skills with hard-coded server/DB values or nonstandard placeholders that do not line up with the file’s `CustomizedParameters: [ServerName, DatabaseName]`.

| Skill ID | File | Issue |
|----------|------|-------|
| MI-availability-1 | availability.yaml | Hard-coded server name: `marketman-prod-main-db`. |
| MI-availability-2 | availability.yaml | Hard-coded database name: `MarketManProd`. |
| MI-availability-6 | availability.yaml | Uses `{LogicalServerName}`, `{AppName}`, `{LogicalDatabaseName}` instead of the standardized runtime params. |
| MI-availability-245 | availability.yaml | Uses `{app_name}` even though the template only exposes `ServerName` and `DatabaseName`. |
| MI-backup-restore-2 | backup-restore.yaml | Replaced DB parameter with `{logical_database_guid}` instead of a server/DB template parameter. |
| MI-backup-restore-4 | backup-restore.yaml | Replaced DB parameter with `{logical_database_id}` instead of `DatabaseName`. |
| MI-backup-restore-70 | backup-restore.yaml | Hard-coded server name: `sqlmi-rms-prod-ausoutheast-rpt-301`. |
| MI-networking-11 | networking.yaml | Hard-coded `srv = "servername"` and `db = "databasename"` helper vars. |
| MI-performance-23 | performance.yaml | Hard-coded logical server name: `ish34-pre-db01`. |
| MI-general-6 | general.yaml | Hard-coded placeholder value `xxxxxx` for `managedInstanceName`. |
| MI-general-8 | general.yaml | Hard-coded placeholder value `****` for `managedInstanceName`. |

## Error Type 5: Misattributed Topic
| Skill ID | File | Topic | What the Query Actually Does |
|----------|------|-------|------------------------------|
| MI-performance-12 | performance.yaml | `Lock request timeout` | Only opens `MonLogin` over a time range; no lock/wait/error filter. |
| MI-availability-8 | availability.yaml | `Check Read-scale out connection` | Only queries raw `MonLogin` by time; no read-scale / redirect / replica logic. |
| MI-general-1 | general.yaml | `MI basic info` | Not a query at all; it is an overview paragraph listing multiple areas. |
| MI-general-47 | general.yaml | `How to find MI located Subscription ID and attach in ASC_` | Explanatory prose, not an executable query. |
| MI-general-54 | general.yaml | `Tips with ADF team` | Generic `MonLogin` filter by server/database; no ADF-specific predicate. |

## Recommendations
1. **Fix the exporter first.** Most invalid entries are split notebook/doc cells (`let ...`, mid-pipe fragments, overview text). Adjacent fragments should be merged into one skill or removed.
2. **Keep prose out of `ExecutedQuery`.** Move explanations, links, and runbook text to `Source`/documentation fields only.
3. **Normalize `TableName` from the first real source table** and prevent concatenated values like `MonXxxMonYyy` or `MonTableCheck`.
4. **Standardize parameterization** on `ServerName` / `DatabaseName`, then map them to the right physical column per table (`name`, `logical_server_name`, `server_name`, `managed_database_name`, etc.).
5. **Remove hard-coded customer values** (`marketman-prod-main-db`, `ish34-pre-db01`, `sqlmi-rms-prod-ausoutheast-rpt-301`, etc.) before shipping the template set.
6. **Re-home obvious category/topic outliers** (login telemetry in performance/general, read-scale connectivity under availability) after the broken exports are cleaned up.
