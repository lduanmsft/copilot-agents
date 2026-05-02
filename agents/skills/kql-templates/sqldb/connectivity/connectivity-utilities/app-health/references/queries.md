# Kusto Queries for App Health Check

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (ISO 8601 format)
- `{EndTime}`: End timestamp in UTC (ISO 8601 format)

**Infrastructure identifiers:**
- `{AppName}`: SQL instance app name (from get-db-info skill)
- `{ClusterName}`: Tenant ring/cluster name (e.g., `tr1234.eastus1-a.worker.database.windows.net`)
- `{NodeName}`: DB node name (e.g., `_DB_39`)

**Resource identifiers:**
- `{LogicalServerName}`: Logical server name (e.g., `myserver`)
- `{LogicalDatabaseName}`: Logical database name

---

## Step 1: Detect Process Restarts

### AH100 - Process ID Change Detection

**Purpose:** Confirm whether the `sqlservr` process restarted during the incident window by detecting distinct `process_id` values in `MonSQLSystemHealth`.

**What to look for:**
- Two or more distinct `process_id` values within the time window confirm a restart
- A temporal gap between the `max_time` of the old process and `min_time` of the new process approximates the restart duration
- 🚩 Any restart detected is noteworthy; gap > 60 seconds is unusual

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
MonSQLSystemHealth
| where originalEventTimestamp between (_startTime .. _endTime)
| where AppName =~ '{AppName}'
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{NodeName}'
| summarize min_time = min(originalEventTimestamp), max_time = max(originalEventTimestamp)
    by process_id
| order by min_time asc
```

**Expected output:**
- **process_id**: SQL Server process identifier — two different values confirm a restart
- **min_time / max_time**: First and last seen timestamp for each process

---

## Step 2: Check for Automation/User Actions

### AH200 - LoginOutages Audit

**Purpose:** Determine if any automation or user-initiated outage actions were recorded against the database during the incident window.

**What to look for:**
- `OutageReasonLevel1 = "CAS"` and `OutageReasonLevel2 = "KillProcess"` — manual or automated process kill
- `OutageReasonLevel1 = "Bot"` with `ResolveUnavailability` mention — bot-driven kill
- Any outage reason involving `sqlservr` — correlate with process restart from AH100
- 🚩 Actions temporally close to a detected restart are strong indicators of external trigger

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
LoginOutages
| where TIMESTAMP between (_startTime .. _endTime)
| where logical_server_name =~ '{LogicalServerName}'
| where database_name =~ '{LogicalDatabaseName}'
| project TIMESTAMP, logical_server_name, database_name, OutageReasonLevel1, OutageReasonLevel2, OutageReasonLevel3
| order by TIMESTAMP asc
```

**Expected output:**
- **OutageReasonLevel1/2/3**: Hierarchical outage classification
- Correlate timestamps with restart gaps from AH100

---

### AH210 - MonNonPiiAudit Trail

**Purpose:** Check if any automation or user-initiated actions were executed against the AppName or node during the incident window. Pay special attention to actions targeting `sqlservr`.

**What to look for:**
- Entries where `request` or `parameters` contain `sqlservr` — actions directly targeting the SQL Server process
- `request_action` values such as `KillProcess`, `ExecuteKillProcess` are high-signal indicators
- 🚩 Actions targeting `sqlservr` around a detected restart timestamp are strong indicators of an externally triggered restart
- Read-only actions (`Get*`, `ExecuteCMSQuery`, etc.) are excluded by the query filter

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
let _AppName = '{AppName}';
let _ClusterName = '{ClusterName}';
let _NodeName = '{NodeName}';
MonNonPiiAudit
| where TIMESTAMP between (_startTime .. _endTime)
| where * contains _ClusterName and * contains _NodeName and * contains _AppName
| where request_action !in~ ("ExecuteCMSQuery", "FabricClusters()", "FabricNodes()", "ExecuteCMSQueryJSON", "ExecuteQuery") and request_action !startswith "Get"
| project time_created, username, request_action, request, parameters
| order by time_created asc
```

**Expected output:**
- **time_created**: When the action was executed
- **username**: Who or what initiated the action (user alias, bot identity, or automation service)
- **request_action**: The type of action performed (e.g., KillProcess)
- **request / parameters**: Check for `sqlservr` to confirm SQL Server process targeting

---

## Step 3: System Health Messages

### AH305 - Known Warning Pattern Aggregation (MANDATORY — run FIRST)

**Purpose:** Screen MonSQLSystemHealth for known warning/error patterns using KQL aggregation. This query **MUST** be executed before AH300 to ensure critical signals (I/O slow, memory pressure, etc.) are never missed regardless of result size.

**Why this exists:** Raw AH300 results can exceed millions of rows for long time windows. An agent cannot reliably scan all raw messages. AH305 aggregates known patterns in Kusto so critical events are always surfaced.

**What to look for:**
- Any row with `MessageCount > 0` is a 🚩 **warning/error** that must be reported
- `I/O_slow`: SQL Server I/O requests taking longer than 15 seconds — indicates storage latency degradation
- `Memory_pressure`: Low memory or memory broker notifications
- `Deadlock`: Deadlock victim messages
- `StackDump`: SQL Server stack dumps
- `Crash_or_exception`: Fatal errors or unhandled exceptions
- `IO_error`: I/O integrity errors (823/824)
- `Long_recovery`: Long-running recovery
- `Connectivity_issue`: Connection or network level errors from SQL perspective
- For each detected pattern, compare `MinTime` against `{StartTime}` to determine if it is acute (started during/after incident) or chronic (pre-existing)

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
MonSQLSystemHealth
| where originalEventTimestamp between (_startTime .. _endTime)
| where AppName =~ '{AppName}'
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{NodeName}'
| where isnotempty(message)
| extend Pattern = case(
    message contains "I/O requests taking longer than 15 seconds", "I/O_slow",
    message contains "significant part of sql server process memory has been paged out" or message contains "low on virtual memory" or message contains "memory broker", "Memory_pressure",
    message contains "was deadlocked on" or message contains "chosen as the deadlock victim", "Deadlock",
    message contains "stack dump" or message contains "stack signature", "StackDump",
    message contains "fatal error" or message contains "exception" or message contains "access violation", "Crash_or_exception",
    message contains "error: 823" or message contains "error: 824" or message contains "I/O error", "IO_error",
    message contains "recovery of database" and message contains "is" and message contains "% complete", "Long_recovery",
    message contains "connection forcibly closed" or message contains "login timeout" or message contains "transport-level error", "Connectivity_issue",
    "Informational")
| where Pattern != "Informational"
| extend OccurrenceCount = toint(extract("encountered ([0-9]+) occurrence", 1, message))
| summarize MessageCount=count(), TotalOccurrences=sum(coalesce(OccurrenceCount, 1)), MinTime=min(originalEventTimestamp), MaxTime=max(originalEventTimestamp), SampleMessage=take_any(message) by Pattern
| order by MessageCount desc
```

**Expected output:**
- **Pattern**: The category of warning/error
- **MessageCount**: Number of distinct log messages matching this pattern
- **TotalOccurrences**: Sum of occurrence counts (for patterns like I/O slow that report N occurrences per message)
- **MinTime / MaxTime**: Time range when this pattern was observed
- **SampleMessage**: One representative message for context

**MANDATORY follow-up for each non-zero pattern:**
1. Run AH305_pre (see below) to check if the pattern existed **before** the incident window
2. If the pattern is absent in AH305_pre → classify as 🚩 **Acute** (incident-specific)
3. If the pattern is present in AH305_pre → classify as **Chronic** (pre-existing, note but deprioritize)

### AH305_pre - Known Warning Pattern Aggregation (Pre-Window)

**Purpose:** For each warning pattern found in AH305, check if it also existed **before** the incident window to classify as chronic vs. acute.

```kql
let _checkStart = datetime({StartTime}) - 2h;
let _checkEnd = datetime({StartTime});
MonSQLSystemHealth
| where originalEventTimestamp between (_checkStart .. _checkEnd)
| where AppName =~ '{AppName}'
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{NodeName}'
| where isnotempty(message)
| extend Pattern = case(
    message contains "I/O requests taking longer than 15 seconds", "I/O_slow",
    message contains "significant part of sql server process memory has been paged out" or message contains "low on virtual memory" or message contains "memory broker", "Memory_pressure",
    message contains "was deadlocked on" or message contains "chosen as the deadlock victim", "Deadlock",
    message contains "stack dump" or message contains "stack signature", "StackDump",
    message contains "fatal error" or message contains "exception" or message contains "access violation", "Crash_or_exception",
    message contains "error: 823" or message contains "error: 824" or message contains "I/O error", "IO_error",
    message contains "recovery of database" and message contains "is" and message contains "% complete", "Long_recovery",
    message contains "connection forcibly closed" or message contains "login timeout" or message contains "transport-level error", "Connectivity_issue",
    "Informational")
| where Pattern != "Informational"
| summarize MessageCount=count(), MinTime=min(originalEventTimestamp), MaxTime=max(originalEventTimestamp) by Pattern
```

**Expected output:** Same schema as AH305. Compare patterns found here against AH305 results.

---

### AH300 - MonSQLSystemHealth Messages (Raw — Optional Drill-Down)

**Purpose:** Retrieve raw system health messages for detailed inspection. **Only run this if AH305 finds a warning pattern that requires further investigation** (e.g., to extract file paths from I/O slow messages, or to see the timeline of a specific pattern).

**⚠️ IMPORTANT — Large Result Handling:** This query can return thousands of rows for long time windows. If you need to drill into a specific pattern found by AH305, **add a filter** for that pattern instead of retrieving all messages. For example, add `| where message contains 'I/O requests taking longer than 15 seconds'` to investigate I/O slow events specifically.

**What to look for:**
- Use best judgement to see if a message is informational only or a warning/error.
- For any message classified as Warning/Error, the agent MUST also check whether the same message appears **outside** the incident window (before `{StartTime}` and after `{EndTime}`) using query AH310

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
MonSQLSystemHealth
| where originalEventTimestamp between (_startTime .. _endTime)
| where AppName =~ '{AppName}'
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{NodeName}'
| where isnotempty(message)
| project originalEventTimestamp, NodeName, message
| order by originalEventTimestamp asc
```

**Expected output:**
- **originalEventTimestamp**: When the message was logged
- **NodeName**: The node that generated the message
- **message**: The system health message — classify each as informational or warning/error

---

### AH310 - System Health Messages Outside Incident Window

**Purpose:** For warning/error messages found in AH300, check if the same messages also appear **before** and **after** the incident window. This determines whether the messages are chronic (persistent background noise) vs. acute (specific to the incident).

**How to use:**
- Run this query twice: once for the **pre-window** period and once for the **post-window** period
- For pre-window: set `_checkStart` = `{StartTime}` minus 1 hour, `_checkEnd` = `{StartTime}`
- For post-window: set `_checkStart` = `{EndTime}`, `_checkEnd` = `{EndTime}` plus 1 hour
- Compare the messages found with those from AH300

**What to look for:**
- If a warning/error message from AH300 also appears outside the window → likely **chronic/background** issue (note but deprioritize)
- If a warning/error message from AH300 does NOT appear outside the window → likely **acute** and incident-related (🚩 highlight)

```kql
let _checkStart = datetime({CheckStartTime});
let _checkEnd = datetime({CheckEndTime});
MonSQLSystemHealth
| where originalEventTimestamp between (_checkStart .. _checkEnd)
| where AppName =~ '{AppName}'
| where ClusterName =~ '{ClusterName}'
| where NodeName =~ '{NodeName}'
| where isnotempty(message)
| project originalEventTimestamp, NodeName, message
| order by originalEventTimestamp asc
```

**Expected output:**
- Same schema as AH300
- Compare with AH300 results to classify chronic vs. acute messages
