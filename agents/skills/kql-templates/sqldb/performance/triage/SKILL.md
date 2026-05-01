---
name: triage
description: "**MAIN ENTRY POINT FOR PERFORMANCE TROUBLESHOOTING.** This skill is the primary gateway for all performance investigations. It determines the type of performance issue (high CPU, memory pressure, QDS readonly, disk space, query performance, etc.) by analyzing symptoms, telemetry patterns, and initial data. Routes to the appropriate diagnostic skills (CPU, memory, QDS, out-of-disk, Queries, APRC, Compilation, miscellaneous, SOS) for detailed investigation."
---

# Performance Issue Triage

This skill analyzes available information to determine the type of performance issue and route to the appropriate diagnostic skills for detailed investigation.

## Required Information

### From User or ICM:
- **Incident ID** (optional - if investigating an existing ICM incident)
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00`)
- **EndTime** (UTC format: `2026-01-01 03:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill:
- **deployment_type** (e.g., "GP without ZR", "GP with ZR", "BC")
- **service_level_objective**
- All database configuration variables

### From appnameandnodeinfo skill (obtained in Step 0):
- **AppNamesNodeNamesWithOriginalEventTimeRange** - Filter string for telemetry queries
- **AppNamesNodeNamesWithPreciseTimeRange** - Filter string using PreciseTimeStamp
- **AppNamesOnly** - Comma-separated list of AppNames
- **SumCpuMillisecondOfAllApp** - Total CPU capacity
- **ActualSumCpuMillisecondOfAllApp** - Actual CPU consumed
- **isInElasticPool** - Whether database is in an Elastic Pool
- **edition** - Database service tier
- All other variables from appnameandnodeinfo (see [appnameandnodeinfo/SKILL.md](../../Common/appnameandnodeinfo/SKILL.md))

### Optional User Hints:
- Explicit keywords: "high CPU", "memory", "QDS readonly", etc.
- Symptoms described by user

## Workflow

### 0. Obtain Metadata Variables (MANDATORY FIRST STEP)

**⚠️ CRITICAL**: This step MUST be executed FIRST, before any other workflow steps. The variables obtained here are passed to ALL subsequent diagnostic skills.

**Action**: Execute [appnameandnodeinfo/SKILL.md](../../Common/appnameandnodeinfo/SKILL.md) to obtain:

| Variable | Description | Used By |
|----------|-------------|---------|
| `{AppNamesNodeNamesWithOriginalEventTimeRange}` | Filter string for telemetry queries | All diagnostic skills |
| `{AppNamesNodeNamesWithPreciseTimeRange}` | Filter string using PreciseTimeStamp | Some diagnostic skills |
| `{AppNamesOnly}` | Comma-separated list of AppNames | Query filtering |
| `{NodeNamesWithOriginalEventTimeRange}` | Node-level filter string | Node analysis |
| `{SumCpuMillisecondOfAllApp}` | Total CPU capacity in milliseconds | CPU skill |
| `{ActualSumCpuMillisecondOfAllApp}` | Actual CPU consumed | CPU skill |
| `{isInElasticPool}` | Whether database is in Elastic Pool | CPU, QDS skills |
| `{edition}` | Database service tier | Service tier checks |
| `{service_level_objective}` | SLO of the database | Resource limit checks |

**Store all variables** - they will be passed to each selected diagnostic skill to avoid redundant queries.

### 1. Extract ICM Incident Information (if Incident ID Available)

Run this FIRST if an ICM incident ID is provided.** ICM is used **ONLY** to extract the 4 required parameters for investigation.

**⚠️ IMPORTANT**: Do NOT use ICM title, description, or AI summary for skill selection. Only extract the parameters below.

**Step 1a: Get incident details:**

```
Tool: mcp_icm-prod_get_incident_details_by_id
Parameters:
  incidentId: "{incident_id}"
```

**Step 1b: Extract ONLY these 4 parameters:**

| Field | Source | Variable |
| ----- | ------ | -------- |
| **Logical Server Name** | Custom field `ServerName` or `LogicalServerName` | `logical_server_name` |
| **Logical Database Name** | Custom field `DatabaseName` or `LogicalDatabaseName` | `logical_database_name` |
| **StartTime** | Priority: `ObservedStartTime` > `ImpactStartTime` > `CreatedDate` | `start_time` |
| **EndTime** | Priority: `MitigateTime` > Current UTC (capped at StartTime + 7h) | `end_time` |

**⛔ DO NOT extract or use:**
- ICM Title (do not scan for keywords)
- ICM Description (do not scan for keywords)
- ICM AI Summary (do not use for triage)
- Alert Source or other metadata for skill selection

**After extracting parameters**, proceed directly to Step 2 (user keywords) or Step 3 (default skills).

### 2. Check for Explicit Keywords from User

If user explicitly mentioned:
- **"high CPU"**, **"CPU usage"**, **"CPU spike"** → Include the `CPU` skill
- **"memory"**, **"OOM"**, **"memory pressure"**, **"overbooking"**, **"buffer pool"** → Include the `memory` skill
- **"QDS"**, **"Query Store"**, **"readonly"** → Include the `query-store` skill
- **"plan regression"**, **"APRC"**, **"FORCE_LAST_GOOD_PLAN"** → Include the `APRC` skill
- **"slow query"**, **"query performance"**, **"failed queries"** → Include the `Queries` skill
- **"compilation"**, **"compile error"** → Include the `Compilation` skill
- **"disk space"**, **"disk full"**, **"tempdb full"** → Include the `out-of-disk` skill
- **"worker thread"**, **"blocking"**, **"corruption"**, **"AKV"** → Include the `miscellaneous` skill
- **"non-yielding"**, **"scheduler"**, **"dump"** → Include the `SOS` skill
- **"LSASS"**, **"telemetry hole"**, **"telemetry gap"**, **"sluggish VM"**, **"frozen VM"**, **"watchdog"**, **"residual LSASS"**, **"LSASS cascade"**, **"connection pool exhaustion"**, **"step-change"**, **"VM unresponsive"** → Include the `LSASS` skill
- **"pause failed"**, **"resume failed"**, **"deactivation stuck"**, **"pause/resume"**, **"LongTime Activation"**, **"activation mitigation spike"**, **"stuck activation"**, **"resume latency"**, **"slow resume"** → Include the `DynamicDeactivation/incident-rca` skill

### 3. Select Diagnostic Skills

**Build the selected_skills list based on user keywords OR use defaults:**

```
selected_skills = []

# ONLY source: User-provided keywords (ICM keywords are NOT used)
if user_mentioned_cpu:
    selected_skills.append("CPU")
if user_mentioned_memory:
    selected_skills.append("memory")
if user_mentioned_qds:
    selected_skills.append("query-store")
if user_mentioned_aprc:
    selected_skills.append("APRC")
if user_mentioned_queries:
    selected_skills.append("Queries")
if user_mentioned_compilation:
    selected_skills.append("compilation")
if user_mentioned_disk:
    selected_skills.append("out-of-disk")
if user_mentioned_misc:
    selected_skills.append("miscellaneous")
if user_mentioned_sos:
    selected_skills.append("SOS")
if user_mentioned_lsass:
    selected_skills.append("LSASS")
if user_mentioned_DynamicDeactivation_rca:
    selected_skills.append("DynamicDeactivation/incident-rca")

# Default if no user keywords - run general performance checks
if selected_skills is empty:
    selected_skills = ["CPU", "memory", "out-of-disk", "query-store", "miscellaneous"]
```

**⚠️ NOTE**: ICM keywords are intentionally NOT used for skill selection. This ensures consistent, comprehensive performance analysis regardless of how the ICM was titled or described.

**Decision matrix:**

| User Keyword | Selected Skills | Confidence |
| ------------ | --------------- | ---------- |
| "high CPU" | `["CPU"]` | High |
| "memory" | `["memory"]` | High |
| "disk full" | `["out-of-disk"]` | High |
| "plan regression" | `["APRC"]` | High |
| "QDS" | `["query-store"]` | High |
| (none) | `["CPU", "memory", "out-of-disk", "query-store", "miscellaneous"]` (default) | Standard |

**Multiple skills** are selected when user mentions multiple issue types.

**Default**: If no user keywords provided → `["CPU", "memory", "out-of-disk", "query-store", "miscellaneous"]` (comprehensive performance check)

### 4. Validate Selection

If incident type is ambiguous:
> ⚠️ **Incident type unclear.** Running default performance checks: CPU, memory, out-of-disk, QDS, and miscellaneous analysis.
> 
> Consider refining the triage logic if this becomes a frequent issue.

## Output (MANDATORY)

**⚠️ CRITICAL**: The triage output is MANDATORY and must appear **exactly once** in the final investigation report.

**Timing Rule**:
- Do NOT display triage output during intermediate data gathering steps
- Do NOT display triage output immediately after triage is complete
- The "✅ Triage Complete" section should appear **only in the final structured report**, after the Incident Summary and Database Environment sections, and before the detailed diagnostic analysis

**Why**: Displaying triage output during intermediate steps AND in the final report causes duplicate sections, which confuses users.

Return to the calling agent:
- **selected_skills**: Array of skill names (e.g., `["CPU"]` or `["CPU", "memory", "QDS"]`)
- **triage_reason**: Brief explanation of why these skills were selected
- **triage_evidence**: Key keywords/patterns found that led to the selection
- **confidence**: `"high"`, `"standard"` (based on evidence strength)

**Confidence levels:**
| Level | Criteria |
| ----- | -------- |
| **High** | User explicitly specified the issue type (e.g., "high CPU", "memory") |
| **Standard** | Running default performance checks (comprehensive analysis) |

**MANDATORY Display Format (appears EXACTLY ONCE in final report):**

```
## ✅ Triage Complete

| Field | Value |
|-------|---------|
| **Selected Skills** | {selected_skills} |
| **Reason** | {triage_reason} |
| **Evidence** | {triage_evidence} |
| **Confidence** | {confidence} |
```

**⚠️ IMPORTANT**: This section must appear **exactly once** in the entire response. Do not duplicate it.

**Example output (user provided keywords):**

```
## ✅ Triage Complete

| Field | Value |
|-------|-------|
| **Selected Skills** | ["CPU", "memory"] |
| **Reason** | User explicitly mentioned CPU and memory issues |
| **Evidence** | User keywords: "high CPU", "memory pressure" |
| **Confidence** | High |
```

**Example output (no user keywords - default):**

```
## ✅ Triage Complete

| Field | Value |
|-------|-------|
| **Selected Skills** | ["CPU", "memory", "out-of-disk", "query-store", "miscellaneous"] |
| **Reason** | No explicit user keywords provided - running comprehensive performance checks |
| **Evidence** | Default skill selection |
| **Confidence** | Standard |
```

**After triage is complete**, the agent stores the results internally and proceeds to invoke each selected skill in sequence. The triage output is included in the final report only.

## Skill Execution Order

When multiple skills are selected, execute them in this recommended order:

1. **CPU** - High CPU analysis (user pool, kernel, system pool)
2. **memory** - Memory pressure analysis (overbooking, OOM, buffer pool)
3. **out-of-disk** - Disk space issues (quota, tempdb full, XStore errors)
4. **QDS** - Query Data Store readonly detection
5. **APRC** - Automatic Plan Correction and plan regressions
6. **Queries** - Query performance analysis (top queries, waits, failed queries)
7. **Compilation** - Query compilation analysis (failed/successful compilations)
8. **miscellaneous** - Worker threads, corruption, AKV errors, restart/failover
9. **SQLOS** - Non-yielding schedulers, dump analysis
10. **DynamicDeactivation/incident-rca** - Single-database pause/resume incident RCA

**⚠️ IMPORTANT**: Pass all variables obtained in Step 0 (appnameandnodeinfo) to each skill. Skills should NOT re-execute appnameandnodeinfo - they receive the variables from triage.

This order ensures:
- CPU issues are detected first (most common performance issue)
- Memory pressure is checked second (often related to CPU)
- Disk space is checked early (disk issues can cause various symptoms)
- QDS state is checked after resource issues (QDS readonly can be caused by CPU/memory/disk)
- Query-specific diagnostics follow resource checks
- System-level issues are checked last

**Skill paths:**
- CPU: [../CPU/SKILL.md](../CPU/SKILL.md)
- memory: [../memory/SKILL.md](../memory/SKILL.md)
- out-of-disk: [../out-of-disk/SKILL.md](../out-of-disk/SKILL.md)
- query-store: [../query-store/SKILL.md](../query-store/SKILL.md)
- APRC: [../APRC/SKILL.md](../APRC/SKILL.md)
- Queries: [../Queries/SKILL.md](../Queries/SKILL.md)
- Compilation: [../Compilation/](../Compilation/)
- miscellaneous: [../miscellaneous/SKILL.md](../miscellaneous/SKILL.md)
- SQLOS: [../sqlos/](../sqlos/)
- DynamicDeactivation/incident-rca: [../DynamicDeactivation/incident-rca/SKILL.md](../DynamicDeactivation/incident-rca/SKILL.md)

## Available Performance Skills

| Skill | Path | Description |
|-------|------|-------------|
| **CPU** | `../CPU/SKILL.md` | High CPU analysis (user pool, kernel mode, system pool) |
| **memory** | `../memory/SKILL.md` | Memory overbooking (MRG/DRG), OOM events, buffer pool drops |
| **query-store** | `../query-store/SKILL.md` | Query Data Store readonly detection and root cause |
| **APRC** | `../APRC/SKILL.md` | Automatic Plan Correction and plan regressions |
| **Queries** | `../Queries/SKILL.md` | Query performance (top CPU/memory/waits/reads/writes, failed queries, long-running transactions, query-specific diagnostics) |
| **Compilation** | `../Compilation/` | Query compilation analysis (failed/successful compilations) |
| **out-of-disk** | `../out-of-disk/SKILL.md` | Disk space issues (quota, tempdb full, XStore errors) |
| **miscellaneous** | `../miscellaneous/SKILL.md` | Worker thread exhaustion, corruption, AKV errors, restart/failover, kill commands, profiler traces |
| **SQLOS** | `../sqlos/` | Non-yielding schedulers, dump analysis |
| **DynamicDeactivation/incident-rca** | `../DynamicDeactivation/incident-rca/SKILL.md` | Single-database Pause/Resume incident RCA |

## Current Implementation Status

**Implemented:**
- [x] Extract 4 parameters from ICM (server name, database name, start time, end time)
- [x] User keyword detection for targeted skill selection
- [x] Default skill selection for comprehensive performance analysis

**Intentionally NOT implemented:**
- [ ] ~~ICM keyword extraction~~ — Disabled to ensure consistent analysis
- [ ] ~~ICM title/description scanning~~ — Only parameters are extracted from ICM

## Future Enhancements
- [ ] Add correlation detection between performance issues
- [ ] Integrate with alert classification from ICM
- [ ] Add machine learning model for pattern recognition
- [ ] Support automatic severity-based skill prioritization
- [ ] Enhance confidence scoring with historical data

## Usage Notes

This skill should be called by the Performance agent after the `execute-kusto-query` skill and the `get-db-info` skill, but before invoking diagnostic skills. The selected skill names are used to route the investigation to the appropriate specialized diagnostic skills. The agent may invoke multiple diagnostic skills if triage determines the incident has characteristics of multiple issue types.

## Keyword Reference

### CPU-related Keywords
- "high CPU", "CPU usage", "CPU spike", "CPU performance"
- "CPU limit", "CPU throttling", "CPU 100%", "CPU pressure"
- "user pool CPU", "kernel CPU", "system pool CPU"

### Memory-related Keywords  
- "memory", "OOM", "out of memory", "memory pressure"
- "overbooking", "DRG", "MRG", "dynamic resource group"
- "buffer pool", "bufferpool drop", "MEMORYCLERK"
- "memory reclaim", "memory leak"

### query-store-related Keywords (users may type "QDS" or "Query Store")
- "Query Store", "QDS", "query store readonly"
- "QDS readonly", "statement hash map", "buffered items"
- "Error 65536", "Error 131072", "Error 262144"

### Query-related Keywords
- "slow query", "query performance", "query timeout"
- "failed query", "long-running", "wait queries"
- "PAGEIOLATCH", "CXPACKET", "SOS_SCHEDULER_YIELD"

### APRC-related Keywords
- "plan regression", "APRC", "automatic plan correction"
- "query plan", "FORCE_LAST_GOOD_PLAN", "forced plan regression"

### Compilation-related Keywords
- "compilation", "compile error", "failed compilation"
- "compilation CPU", "successful compilation"

### Disk-related Keywords
- "disk space", "disk full", "quota", "quota exceeded"
- "tempdb full", "log full", "data full", "out of space"
- "XStore", "drive out of space", "directory quota limit"
- "data file max size", "log file max size"

### miscellaneous-related Keywords
- "worker thread", "thread exhaustion", "blocking"
- "corruption", "database corruption", "AKV"
- "Azure Key Vault", "restart", "failover", "kill command"
- "profiler trace"

### SOS-related Keywords
- "non-yielding", "non-yielding scheduler", "scheduler"
- "dump", "hang", "unresponsive", "scheduler hang"
```
