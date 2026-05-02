---
name: miscellaneous
description: Analyzes miscellaneous performance and reliability issues including worker thread exhaustion, database corruption, Azure Key Vault errors, SQL restart/failover detection, kill command analysis, process ID display, XEvent session detection, and Azure profiler traces for Azure SQL databases.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
keywords: ['worker thread', 'thread exhaustion', 'blocking', 'corruption', 'database corruption', 'AKV', 'Azure Key Vault', 'restart', 'failover', 'kill command', 'profiler', 'trace', 'dump', 'SQL dump', 'process ID', 'PID', 'pid', 'process lifecycle', 'xevent', 'extended event', 'event session', 'event retention']
---

# Miscellaneous Diagnostics Skill

## Skill Overview

This skill provides comprehensive analysis of various miscellaneous performance and reliability issues in Azure SQL databases that don't fall into the primary performance categories (CPU, memory, disk, QDS). It covers system-level issues, corruption detection, external service integration problems, and diagnostic trace analysis.

**Default Checks (Always Run)**:
- ⭐ Worker Thread Exhaustion Analysis
- ⭐ Database Corruption Detection
- ⭐ Azure Key Vault (AKV) Error Detection
- ⭐ Azure Profiler Trace Discovery
- ⭐ Dump Summary Analysis
- ⭐ XEvent Session Detection

**Optional Checks (Conditional)**:
- Worker Session Similarity Analysis
- SQL Restart and Failover Detection
- Kill Command Analysis

## When to Use This Skill

This skill should be triggered when the user reports or asks about:
- **Worker thread exhaustion** or thread starvation
- **Database corruption** or consistency issues
- **Azure Key Vault (AKV)** errors or connectivity problems
- **SQL restart** or **failover** events
- **Kill command** execution and analysis
- **Azure profiler traces** for advanced diagnostics
- **SQL dump** creation events
- **XEvent sessions** or extended event configurations
- Session blocking or worker session analysis
- Unusual system behavior not related to CPU/memory/disk

## Prerequisites

- Access to Kusto clusters for SQL telemetry
- Logical server name and database name
- Time range for investigation

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |

## Execution Order

Execute the following diagnostic checks. The checks are split into **Default Checks** (always run) and **Optional Checks** (run conditionally based on context).

**⚠️ IMPORTANT: Output Filtering Rule**
- **ONLY display results from a sub-skill if it detects an issue (🚩)**
- **DO NOT display any output from a sub-skill if no issue is detected (✅)**
- This keeps the report concise and focused on actionable findings

---

## Default Checks (Always Run)

These checks are **MANDATORY** and should be executed in every miscellaneous investigation to ensure comprehensive coverage of common miscellaneous issues.

### Step 1: Worker Thread Exhaustion Analysis ⭐ DEFAULT
**Reference**: [worker-thread-exhaustion-analysis](references/worker-thread-exhaustion-analysis.md)

Analyzes worker thread availability and detects thread exhaustion scenarios that can cause query timeouts and performance degradation. Examines worker thread usage patterns, blocking chains, and resource waits.

**Why default**: Worker thread issues are common and can manifest as various symptoms (timeouts, blocking, slow queries). Always check this to rule out or identify thread-related problems.

**Output Rule**: Only include this section if worker thread issues are detected.

---

### Step 2: Database Corruption Detection ⭐ DEFAULT
**Reference**: [database-corruption-detection](references/database-corruption-detection.md)

Detects database corruption events from SQL Server error logs and system health telemetry. Identifies CHECKDB errors, page corruption, and consistency check failures.

**Why default**: Corruption can cause unpredictable behavior and must be ruled out early in any investigation. Critical for data integrity.

**Output Rule**: Only include this section if corruption events are detected.

---

### Step 3: Azure Key Vault (AKV) Error Detection ⭐ DEFAULT
**Reference**: [akv-error-detection](references/akv-error-detection.md)

Analyzes Azure Key Vault connectivity and operation errors. Detects issues with TDE (Transparent Data Encryption), Always Encrypted, or other AKV-dependent features.

**Why default**: AKV errors can prevent database access entirely. Always check to ensure encryption keys are accessible.

**Output Rule**: Only include this section if AKV errors are detected.

---

### Step 4: Azure Profiler Trace Discovery ⭐ DEFAULT
**Reference**: [azure-profiler-trace](references/azure-profiler-trace.md)

Queries MonRgManager and MonManagement tables to discover Azure profiler trace files that were collected for the database during the investigation time window. Lists traces collected by IcM Automation AzProfilerGeneva or by users running CAS commands.

**Why default**: Profiler traces provide deep insights into database behavior and should always be checked when available.

**Output Rule**: Only include this section if profiler traces were collected. If traces are found, display the list and inform the user they can run "analyze azure profiler trace <traceName>" for CPU hotspot analysis.

---

### Step 5: Dump Summary Analysis ⭐ DEFAULT
**Reference**: [dump-summary](../../common/dump-summary/SKILL.md)

Analyzes SQL Server dump file creation events to determine if dumps were created during the investigation time window. Checks the MonSqlDumperActivity table for dump events, identifies the most frequent stack signatures, and provides details about dump error types.

**Why default**: Dump files indicate critical system events (crashes, hangs, memory issues) that can explain performance problems. Always check for dumps to identify underlying system failures.

**Output Rule**: Only include this section if dump events are detected.

---

### Step 6: XEvent Session Detection ⭐ DEFAULT
**Reference**: [xevent-session-detection](references/xevent-session-detection.md)

Detects and analyzes extended event (XEvent) sessions configured on a database. Identifies session names, event types, and event retention modes to help diagnose potential issues related to XEvent session configurations.

**Why default**: Improper XEvent configurations can impact performance or lead to event loss. Always check to identify any problematic session configurations.

**Output Rule**: Only include this section if XEvent sessions with potential issues are detected.

---

## Optional Checks (Run Conditionally)

These checks are **OPTIONAL** and should only be executed when specific keywords or symptoms are present.

### Step 7: Worker Session Similarity Analysis (Optional)
**Reference**: [worker-session-similarity-analysis](references/worker-session-similarity-analysis.md)

Performs cosine similarity analysis on worker sessions to identify patterns and anomalies in session behavior. Useful for detecting unusual workload patterns.

**When to run**:
- Complementary analysis to worker thread exhaustion (if Step 1 detected issues)
- Need to understand session behavior patterns
- Investigating unusual workload characteristics
- ICM mentions "session patterns" or "workload analysis"

**Output Rule**: Only include this section if significant patterns or anomalies are found.

---

### Step 8: SQL Restart and Failover Detection (Optional)
**Reference**: [sql-restart-and-failover-detection](references/sql-restart-and-failover-detection.md)

Detects SQL Server restart events and failover operations. Analyzes the frequency, timing, and potential causes of restarts or failovers.

**When to run**:
- User reports connection interruptions
- ICM mentions "restart", "failover", or "availability"
- Investigating uptime or availability issues

**Output Rule**: Only include this section if restart/failover events are detected.

---

### Step 9: Kill Command Analysis (Optional)
**Reference**: [kill-command](references/kill-command.md)

Analyzes KILL command execution to understand session terminations. Identifies patterns of forced session kills and potential causes.

**When to run**:
- User reports unexpected session terminations
- ICM mentions "kill command" or "session killed"
- Investigating why sessions were terminated

**Output Rule**: Only include this section if KILL commands are detected.

---

### Step 10: Process ID Display (Optional)
**Reference**: [process-id-display](references/process-id-display.md)

Displays all SQL Server process IDs (SPIDs) that were active for an Azure SQL database during a specified time range. Shows the start and end times for each process on each node, helping identify process lifecycle and activity patterns.

**When to run**:
- User wants to see all process IDs during a time range
- Investigating process lifecycle or restarts
- ICM mentions "process ID", "pid", or "PID"
- Correlating specific processes with other events

**Output Rule**: Display results as a table showing start time, end time, node name, and process ID.

---

## Execution Workflow

### Task 1: Obtain Kusto Cluster Information
**CRITICAL:** Always identify the correct cluster - do NOT use default clusters

Identify telemetry-region and kusto-cluster-uri and Kusto-database using [../../Common/execute-kusto-query/references/getKustoClusterDetails.md](../../Common/execute-kusto-query/references/getKustoClusterDetails.md)
- This will perform DNS lookup to find the region
- Then map the region to the correct Kusto cluster URI

**Store Variables**:
- `{KustoClusterUri}`
- `{KustoDatabase}`

### Task 2: Obtain Database Metadata
**Action**: Use the [appnameandnodeinfo skill](../../Common/appnameandnodeinfo/SKILL.md) to retrieve database configuration variables including AppName, NodeName, and time range information.

### Task 3: Execute Diagnostic Checks

**Default Checks (ALWAYS RUN)**:
Execute these checks in every investigation:
1. **Worker Thread Exhaustion Analysis** (Step 1) ⭐
2. **Database Corruption Detection** (Step 2) ⭐
3. **Azure Key Vault (AKV) Error Detection** (Step 3) ⭐
4. **Azure Profiler Trace Discovery** (Step 4) ⭐
5. **Dump Summary Analysis** (Step 5) ⭐
6. **XEvent Session Detection** (Step 6) ⭐

**Optional Checks (RUN CONDITIONALLY)**:
Execute these only when relevant keywords/symptoms are present:
7. **Worker Session Similarity Analysis** (Step 7) - Run if Step 1 detected issues or ICM mentions session patterns
8. **SQL Restart and Failover Detection** (Step 8) - Run if ICM mentions restart/failover/availability
9. **Kill Command Analysis** (Step 9) - Run if ICM mentions kill command or session termination
10. **Process ID Display** (Step 10) - Run if user wants to see process IDs or ICM mentions PID/SPID

**Output Filtering Rule**: 
- Run each diagnostic check
- Only display results if issues are found (🚩)
- Skip displaying sections with no findings (✅)

### Task 4: Summary
After executing all checks, provide a brief summary:
- List which issues were detected (if any)
- Provide recommendations for further investigation
- If no issues found, state that clearly

## Output Format

```markdown
## 🔧 Miscellaneous Diagnostics

### Summary
[Brief overview of what was checked and what was found]

### [Step Name - only if issue detected]
[Results from the diagnostic check]
🚩 [Issue description]
[Details and recommendations]

### Recommendations
[Actionable next steps based on findings]
```

## Related Skills

This skill complements other performance diagnostics:
- **CPU**: For high CPU issues
- **memory**: For memory pressure issues
- **out-of-disk**: For storage space issues
- **QDS**: For Query Store issues
- **SOS**: For scheduler and OS-level issues

## Notes

- This skill has **6 default checks** that ALWAYS run: worker thread exhaustion, database corruption, AKV errors, profiler traces, dump summary, and XEvent session detection
- **4 optional checks** run conditionally based on ICM keywords or symptoms: worker session similarity, SQL restart/failover, kill commands, and process ID display
- Follow the output filtering rule strictly to keep reports focused
- If multiple miscellaneous issues are detected, they may be related (e.g., worker thread exhaustion causing kill commands)
- Default checks ensure comprehensive coverage while optional checks provide targeted analysis when needed
