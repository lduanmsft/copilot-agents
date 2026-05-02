---
name: router
description: Determines the type of backup/restore issue (log full, LTR SLA violation, restore failure, dropped server) by analyzing symptoms, telemetry patterns, and initial data. Routes to the appropriate diagnostic skills for detailed investigation. This is a shared utility skill used by the BackupRestore agent to route incidents to specialized diagnostic skills.
---

# Backup/Restore Issue Router

This skill analyzes available information to determine the type of backup/restore issue and route to the appropriate diagnostic skills for detailed investigation.

## Required Information

### From User or ICM:
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill:
- **physical_database_id**
- **deployment_type** (e.g., "GP without ZR", "GP with ZR", "BC")
- **service_level_objective**
- All database configuration variables

### From backup-restore-insights skill (PREFERRED):
- **issues_detected**: Array of critical and warning issues from `SREGetBackupRestoreInsights`
- **Scenario**: Type of issue detected (Log Full, LTR Out of SLA, Restore Failure, etc.)
- **Status**: ✔️ No Issue, ⚠️ Warning, ❌ Critical
- **EscalationICMTeam**: Recommended team for escalation
- **RCAText**: Root cause analysis text (if available)

### Optional User Hints:
- Explicit keywords: "log full", "LTR", "restore failure", "dropped server"
- ICM alert type or title
- Error codes (9002, 40552)
- Symptoms described by user

## Workflow

### 0. Use Backup/Restore Insights Results (PREFERRED)

If `backup-restore-insights` skill was executed first, use its results to guide routing:

**Map Scenarios to Skills**:
- **Log Full**, **Log Near Full**, **Log Holdup - ACTIVE_BACKUP_OR_RESTORE**, **Log Holdup - AVAILABILITY_REPLICA**, **Log Holdup - ACTIVE_TRANSACTION**, **Log Holdup - CHECKPOINT**, **Log Holdup - XTP_CHECKPOINT**, **Directory Quota Near Full** → Route to `log-near-full` skill
- **Log Holdup - REPLICATION** → Route to `log-near-full` skill, but also recommend Replication agent for detailed CDC/Synapse Link analysis
- **LTR Out of SLA**, **LTR Backup Failure** → Route to `ltr-backup-out-of-sla` skill
- **Restore Failure**, **Restore Stuck** → Check SLO: if `HS_` prefix (Hyperscale) → Route to `hs-restore` skill; otherwise → Route to `restore-failure` skill
- **Hyperscale Geo-Restore Failure**, **Hyperscale Geo-Restore Slow** → Route to `hs-georestore` skill
- **Server Dropped** → Route to `restore-dropped-server` skill
- **Backup Failure** → Route to `log-near-full` skill (backup failures often related to log issues)

**Confidence from Insights**:
- If `Status = ❌` (Critical) → High confidence routing
- If `Status = ⚠️` (Warning) → Medium confidence, may need additional analysis
- If all `Status = ✔️` → Low confidence, use keyword/telemetry fallback

### 1. Check for Explicit Keywords

If user explicitly mentioned:
- **"log full"**, **"log near full"**, **"9002"**, **"40552"**, **"log truncation"**, **"directory quota"** → Route to the `log-near-full` skill
- **"LTR"**, **"long-term retention"**, **"backup SLA"**, **"missed backup"** → Route to the `ltr-backup-out-of-sla` skill
- **"restore failure"**, **"restore stuck"**, **"PITR"**, **"point in time"** → Route to the `restore-failure` skill (or `hs-restore` if Hyperscale/VLDB context)
- **"geo-restore"** → Check context: if Hyperscale/VLDB → Route to the `hs-georestore` skill; otherwise → Route to the `restore-failure` skill
- **"HS restore"**, **"Hyperscale restore"**, **"VLDB restore"**, **"HS_"** SLO prefix, **"VldbRestoreMetrics"** → Route to the `hs-restore` skill
- **"HS geo-restore"**, **"Hyperscale geo-restore"**, **"VLDB geo-restore"**, **"geo-restore"** with Hyperscale/VLDB context → Route to the `hs-georestore` skill
- **"HS geo-restore metrics"**, **"weekly geo-restore"**, **"geo-restore report"** → Route to the `hs-georestore-metrics` skill
- **"dropped server"**, **"deferred drop"**, **"server deletion"**, **"accidental delete"** → Route to the `restore-dropped-server` skill

### 2. Query Telemetry for Backup/Restore Patterns (TO BE IMPLEMENTED)

Execute preliminary queries to understand incident characteristics:
- Check `MonDmLogSpaceInfo` and `MonFabricThrottle` for log space issues
- Check `MonBackup` for backup/restore operations (Reference: BRDB0105 TSG)
- Check ICM incident title for specific alert types
- Analyze patterns and severity

**Queries**: See references/queries.md (TO BE ADDED)

### 3. Analyze Telemetry Patterns (TO BE IMPLEMENTED)

Based on available data:
- **Log full indicators**:
  - Log space usage > 70%
  - Log reuse wait description = ACTIVE_BACKUP_OR_RESTORE, LOG_BACKUP, REPLICATION, AVAILABILITY_REPLICA, ACTIVE_TRANSACTION, XTP_CHECKPOINT
  - DirectoryQuotaNearFull alerts
  - Error 9002 or 40552 in telemetry
  
- **LTR SLA indicators**:
  - Sterling database
  - LTR backup policy configured
  - Missed full backup windows
  - LTR out of SLA alerts
  
- **Restore failure indicators**:
  - Restore operation in Failed state
  - Restore validation errors
  - Stuck restore operations
  - Backup file unavailability
  
- **Dropped server indicators**:
  - Server in DeferredDropped state
  - Recent server deletion events
  - DNS unavailability

### 4. Select Diagnostic Skills

**Default routing logic** (will be enhanced later):
- If explicit keyword match → Use those skills
- If log space issues found → Include skill `log-near-full`
- If LTR patterns detected → Include skill `ltr-backup-out-of-sla`
- If restore patterns detected → Include skill `restore-failure`
- If Hyperscale geo-restore patterns detected → Include skill `hs-georestore`
- If weekly geo-restore metrics requested → Include skill `hs-georestore-metrics`
- If dropped server patterns detected → Include skill `restore-dropped-server`
- Multiple skills may be selected if evidence suggests multiple issue types
- **Default**: skill `log-near-full` (most common scenario)

### 5. Validate Selection

If incident type is ambiguous:
> ⚠️ **Incident type unclear.** Defaulting to the `log-near-full` skill for investigation.
> 
> Consider refining the triage logic if this becomes a frequent issue.

## Output

Return to the calling agent:
- **selected_skills**: Array of skill names (e.g., `["log-near-full"]` or `["restore-failure"]`)
- **triage_reason**: Brief explanation of why these skills were selected
- **confidence**: `"high"`, `"medium"`, `"low"` (based on evidence strength)

**Display to user:**
> ✅ **Triage Complete**
> - **Selected Skills**: {selected_skills}
> - **Reason**: {triage_reason}
> - **Confidence**: {confidence}

## Placeholder Behavior (Current Implementation)

**Until triage logic is fully implemented**, this skill uses simplified routing:

1. **PREFERRED**: Use results from `backup-restore-insights` skill if available
2. Check user prompt for keywords (log full, LTR, restore, dropped server, etc.)
3. Default to `["log-near-full"]` if no clear indicators
4. May return multiple skills if evidence suggests multiple issue types

## Related Skills

- `backup-restore-insights`: Initial triage skill for comprehensive overview (call BEFORE router)
- `log-near-full`: Transaction log full/near full analysis
- `ltr-backup-out-of-sla`: Long-Term Retention backup SLA violations
- `restore-failure`: Restore failures and stuck restore operations (non-Hyperscale)
- `hs-restore`: Hyperscale (VLDB) restore investigation — failed, stuck, or slow restores
- `hs-georestore`: Hyperscale (VLDB) geo-restore investigation — failed or slow geo-restores, geo-replication lag diagnosis
- `hs-georestore-metrics`: Weekly Hyperscale geo-restore metrics and batch failure analysis
- `restore-dropped-server`: Dropped server restore (DevOps only)
