---
name: backup-restore-insights
description: Get general backup and restore insights for Azure SQL Database by querying the SREGetBackupRestoreInsights function. Use this skill as an initial triage step to quickly identify log full, LTR SLA violations, restore failures, and other backup/restore-related issues. Returns a summary of detected scenarios with status indicators and escalation guidance. Required inputs from calling agent - kusto-cluster-uri, kusto-database, LogicalServerName, LogicalDatabaseName, StartTime, EndTime.
---

# Get Backup/Restore Insights

Quickly triage Azure SQL Database backup and restore issues by querying the `SREGetBackupRestoreInsights` function.

## Purpose

This skill provides a comprehensive overview of backup/restore-related issues detected for a database, including:
- Transaction log full/near full scenarios
- Log truncation holdup reasons (REPLICATION, ACTIVE_BACKUP_OR_RESTORE, AVAILABILITY_REPLICA, etc.)
- Long-Term Retention (LTR) backup SLA violations
- Restore failures and stuck operations
- Backup failures and delays
- Directory quota issues

## Required Information

This skill requires the following inputs (should be obtained by the calling agent):

### From User or ICM:
- **LogicalServerName** (e.g., `my-server`) - **Required**
- **LogicalDatabaseName** (e.g., `my-db`) - **Required**
- **StartTime** (UTC format: `2026-01-01 00:00:00`) - **Required**
- **EndTime** (UTC format: `2026-01-02 00:00:00`) - **Required**

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

**Note**: The calling agent should use the `execute-kusto-query` skill before invoking this skill.

## When to Use This Skill

- **Initial triage** of any backup or restore incident
- Quick health check for log space, backup, and restore status
- When you need a broad overview before diving into specific diagnostic skills
- As a first step to determine which specialized skills to invoke next

## Workflow

### Step 1: Execute Backup/Restore Insights Query

Execute the `SREGetBackupRestoreInsights` function to get a comprehensive overview:

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Get backup/restore insights summary for database"
- parameters: 
  {
    "cluster-uri": "https://sqlstage.kusto.windows.net",
    "database": "sqlazure1",
    "query": "SREGetBackupRestoreInsights('{kusto-cluster-uri}', datetime('{StartTime}'), datetime('{EndTime}'), '{LogicalServerName}', '{LogicalDatabaseName}')"
  }
```

**Note**: The query is executed against the `sqlstage` cluster.

### Step 2: Interpret Results

The query returns a table with the following columns:

| Column | Description |
|--------|-------------|
| **Scenario** | Type of issue detected (e.g., "Log Full", "Backup Error", "TDE is Enabled") |
| **Description** | Brief description of the scenario |
| **Status** | Status indicator: `✔️ No Issue Found`, `⚠️ Issue detected. Please only escalate if additional details are needed` |
| **Notes** | Additional context, timestamps, metrics, or specific values (e.g., retention days, earliest backup date) |
| **RCAText** | Root cause analysis text, guidance, or TSG links |
| **EscalationICMTeam** | Recommended ICM team or action for escalation (may be empty or contain guidance like "Do not file ICM directly") |
| **Occurrence** | Number of times the issue occurred (null if not applicable)

### Step 3: Categorize Findings

Group the results into categories:

#### 🚩 Issues Detected (⚠️ Status)
Issues that may need investigation. Note the escalation guidance in the Status text itself:

| Scenario | Notes | RCA Text / Guidance | Occurrences |
|----------|-------|---------------------|-------------|
| {Scenario} | {Notes} | {RCAText} | {Occurrence} |

**Important**: Check the `EscalationICMTeam` column - it may contain specific guidance like:
- `"Do not file ICM directly, contact CSS SME alias Engage DI Shadow Escalation Team"` - Do NOT escalate to ICM
- Empty string - Use RCAText for guidance
- Team name - Escalate to that team if needed

#### ✅ No Issues (✔️ Status)
Scenarios that were checked and found to be healthy:
- {List of scenarios with no issues}

### Step 4: Provide Triage Recommendations

Based on the detected issues, recommend next steps:

**If Per Database CMK enabled detected**:
> ⚠️ **Per Database CMK Enabled**: Check for encryption errors before filing ICM. Review TDE/CMK configuration.

**If Backup Restore detected on Subcore detected**:
> ⚠️ **Subcore SLO Backup/Restore**: Review the [Subcore SLO insight TSG](https://supportability.visualstudio.com/AzureSQLDB/_wiki/wikis/AzureSQLDB.wiki/372539/Issues-with-SubCore-SLO-insight). Do NOT file ICM directly - contact CSS SME alias Engage DI Shadow Escalation Team.

**If Short Term Retention Days detected**:
> ℹ️ **Short Term Retention**: Note the configured retention days in the Notes column. Verify if this meets customer requirements.

**If Earliest Full Backup available date detected**:
> ⚠️ **Earliest Full Backup Date**: Restore is NOT possible before this date. Check the Notes column for the exact date. Do NOT file ICM directly - contact CSS SME alias Engage DI Shadow Escalation Team.

**If Log Full detected**:
> 🚩 **Log Full Issues Detected**: Invoke the `log-near-full` skill for detailed log analysis and mitigation steps.

**If Backup Error detected**:
> 🚩 **Backup Error Detected**: Review backup error details. May need to investigate backup infrastructure or storage issues.

**If Server is in Dropped state detected**:
> 🚩 **Server Dropped**: Invoke the `restore-dropped-server` skill for dropped server recovery (DevOps only).

**If Low Memory detected in InMemBackupRestorePool detected**:
> 🚩 **Low Memory in Backup/Restore Pool**: Memory pressure affecting backup/restore operations. May need to investigate memory allocation.

**If Asymmetric key errors reported detected**:
> 🚩 **Asymmetric Key Errors**: Key errors may impact backup/restore operations. Review TDE/CMK configuration.

**If In Progress Backup detected detected**:
> ℹ️ **Backup In Progress**: An active backup operation is running. This may be expected behavior.

**If TDE is Enabled shows No Issue Found**:
> ✅ **TDE Status**: TDE is enabled and healthy.

**If CMK enabled at Server level shows No Issue Found**:
> ✅ **CMK Status**: Server-level CMK is not enabled (or healthy if enabled).

**If Is LTR Backup Enabled shows No Issue Found**:
> ✅ **LTR Status**: LTR backup is not configured or is healthy.

### Step 5: Generate Summary Report

Present a summary to the user:

> ## 📊 **Backup/Restore Insights Summary**
> 
> **Database**: {LogicalServerName} / {LogicalDatabaseName}
> **Analysis Period**: {StartTime} to {EndTime}
> 
> ### Issues Detected
> 
> | Scenario | Notes | Guidance |
> |----------|-------|----------|
> | {Scenario with ⚠️} | {Notes} | {RCAText or EscalationICMTeam guidance} |
> 
> ### Healthy Checks (✔️)
> - {List of scenarios with "No Issue Found"}
> 
> ### Recommended Next Steps
> 
> 1. {First recommended action based on detected issues}
> 2. {Second recommended action}
> 3. {Third recommended action}
> 
> ### Escalation Guidance
> 
> {Review EscalationICMTeam column - many issues say "Do not file ICM directly"}
> {Contact CSS SME alias or specific teams as directed}

## Scenario Reference

### Known Scenarios

| Scenario | Description | Status Meaning | Typical Action |
|----------|-------------|----------------|----------------|
| Per Database CMK enabled | Per-database Customer Managed Key is enabled | ⚠️ Check for encryption errors | Review TDE/CMK config before escalating |
| Backup Restore detected on Subcore | Backup/Restore on Subcore SLO detected | ⚠️ Review TSG | Do NOT file ICM - contact CSS SME |
| Short Term Retention Days | Shows configured PITR retention period | ⚠️ Informational | Verify meets requirements |
| Earliest Full Backup available date | Earliest restorable point | ⚠️ Restore limitation | Cannot restore before this date |
| TDE is Enabled | Transparent Data Encryption status | ✔️ if healthy | Informational |
| CMK enabled at Server level | Server-level Customer Managed Key | ✔️ if not enabled/healthy | Informational |
| Log Full | Transaction log full or near full | ✔️ if healthy, ⚠️ if issue | Invoke `log-near-full` skill |
| Backup Error | Backup operation errors | ✔️ if healthy, ⚠️ if issue | Investigate backup failures |
| Is LTR Backup Enabled | Long-Term Retention configuration | ✔️ if not enabled/healthy | Check LTR policy |
| Server is in Dropped state | Logical server was deleted | ✔️ if not dropped, ⚠️ if dropped | Invoke `restore-dropped-server` |
| Low Memory detected in InMemBackupRestorePool | Memory pressure in backup pool | ✔️ if healthy, ⚠️ if issue | Investigate memory allocation |
| Asymmetric key errors reported | Key errors affecting operations | ✔️ if healthy, ⚠️ if issue | Review TDE/CMK configuration |
| In Progress Backup detected | Active backup operation running | ✔️ if not running, ⚠️ if detected | May be expected behavior |

### Important Notes on Escalation

1. **Many scenarios say "Do not file ICM directly"** - Follow the guidance in `EscalationICMTeam` column
2. **Contact CSS SME alias Engage DI Shadow Escalation Team** - For Subcore SLO and earliest backup issues
3. **Status text includes escalation guidance** - Read the full Status message, not just the emoji

## Output

After analysis, provide:
- **issues_detected**: Array of critical and warning issues
- **recommended_skills**: Array of specialized skills to invoke next
- **escalation_teams**: Array of ICM teams for escalation (if any)
- **summary**: Brief text summary of findings

## Related Skills

Based on insights results, invoke:
- `log-near-full` - For log full/near full and holdup analysis
- `ltr-backup-out-of-sla` - For LTR backup SLA violations
- `restore-failure` - For restore failures and stuck operations
- `restore-dropped-server` - For dropped server recovery (DevOps only)
