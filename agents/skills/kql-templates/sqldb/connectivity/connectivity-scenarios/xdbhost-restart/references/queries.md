# Kusto Queries for XdbHost Restart Diagnosis

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (ISO 8601 format)
- `{EndTime}`: End timestamp in UTC (ISO 8601 format)

**Resource identifiers:**
- `{LogicalServerName}`: Logical server name (e.g., `myserver`)
- `{LogicalDatabaseName}`: Logical database name

**Infrastructure identifiers:**
- `{ClusterName}`: Tenant ring/cluster name (e.g., `sqlazure-prod-eus2-a`)
- `{DBNodeName}`: DB node name (e.g., `_DB_39`)

---

## Step 1: Confirm XdbHost Restart

### XR100 - Detect Process ID Change (Restart Confirmation)

**Purpose:** Confirm that an XdbHost restart occurred by detecting a process_id change on the DB node. This is the definitive indicator of a restart.

**What to look for:**
- Two or more distinct `process_id` values within the time window
- A temporal gap between the `max(TIMESTAMP)` of the old process and `min(TIMESTAMP)` of the new process
- The gap duration approximates the restart time
- 🚩 Gap > 60 seconds is unusual and warrants investigation

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonXdbhost
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar and NodeName =~ _NodeNameVar
| summarize min_time = min(TIMESTAMP), max_time = max(TIMESTAMP)
    by process_id
| order by min_time asc
```

**Expected output:**
- **process_id**: XdbHost process identifier — two different values confirm a restart
- **min_time / max_time**: First and last seen timestamp for each process

---

## Step 2: Determine Restart Trigger

### XR200 - XdbHost Process Logs (Trigger Classification)

**Purpose:** Examine XdbHost process logs for error patterns that reveal the restart trigger — SNIOpen failures, InitSendData errors, throttling parameter changes, or socket duplication failures.

**What to look for:**
- Text containing `fail`, `stuck` — general failure indicators

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonXdbhost
| where TIMESTAMP between (StartTime..EndTime)
| where ClusterName =~ _ClusterNameVar and NodeName =~ _NodeNameVar
| where text contains "fail" or text contains "stuck"
| project TIMESTAMP, ClusterName, NodeName, process_id, text
| order by TIMESTAMP asc
```

**Expected output:**
- **TIMESTAMP**: When the event occurred
- **text**: XdbHost log message — classify against trigger patterns above
- **process_id**: Which process instance generated the log

---

## Step 3: Check for Automation/User Actions on Node

### XR300 - Audit Trail for Automation/User Actions on Node

**Purpose:** Check if any automation or user-initiated actions were executed against the node during the incident window. This helps identify whether an external action (e.g., kill) triggered the XdbHost restart.

**What to look for:**
- Entries where `request` or `parameters` contain `xdbhostmain` — these are actions directly targeting XdbHost
- 🚩 Actions targeting XdbHost around the restart timestamp are strong indicators of an externally triggered restart
- Entries targeting other processes (e.g., `sqlservr`) — list as informational context only; these may correlate but are not direct XdbHost triggers
- `request_action` values such as `KillProcess`, `ExecuteKillProcess` are high-signal indicators
- Read-only actions (`Get*`, `ExecuteCMSQuery`, etc.) are excluded by the query filter

```kql
let _startTime = datetime({StartTime});
let _endTime = datetime({EndTime});
let _ClusterNameVar = '{ClusterName}';
let _NodeNameVar = '{DBNodeName}';
MonNonPiiAudit
| where TIMESTAMP between (_startTime.._endTime)
| where * contains _ClusterNameVar and * contains _NodeNameVar
| where request_action !in~ ("ExecuteCMSQuery", "FabricClusters()", "FabricNodes()", "ExecuteCMSQueryJSON", "ExecuteQuery") and request_action !startswith "Get"
| project time_created, username, request_action, request, parameters
| order by time_created asc
```

**Expected output:**
- **time_created**: When the action was executed
- **username**: Who or what initiated the action (user alias, bot identity, or automation service)
- **request_action**: The type of action performed (e.g., KillProcess)
- **request**: The request details — check for `xdbhostmain` to confirm XdbHost targeting
- **parameters**: Additional parameters — check for `xdbhostmain` to confirm XdbHost targeting

---

## Step 4: Characterize Login Error Distribution

### XR400 - Login Error Breakdown by Error Code and State

**Purpose:** Understand the full error distribution during the incident window. Distinguish between user errors (customer-side, pre-restart) and system errors (XdbHost restart cascade).

**What to look for:**
- **User errors (is_user_error = true)**: 18456/132 (FedAuthAADLoginJWTUserError), 18456/122 (CloudEmptyUserName), 18456/170 (AadOnlyAuthenticationEnabled)
- **XdbHost restart errors (is_user_error = false)**: 40613 states 10, 12, 13, 44, 126
- **Gateway throttling**: 40613/22 (DueToProxyConnextThrottle), 42127/22
- 🚩 If user errors significantly exceed system errors BEFORE the restart, the restart was likely triggered by automation responding to the user error flood

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where event == "process_login_finish" and error > 0
| summarize ErrorCount = count()
    by error, state, state_desc, is_user_error, bin(originalEventTimestamp, 5m)
| order by originalEventTimestamp asc, ErrorCount desc
```

**Expected output:**
- **error / state / state_desc**: Error classification
- **is_user_error**: true = customer-side error, false = system/infrastructure error
- **ErrorCount**: Volume per 5-minute bin
- Pattern: User errors often precede restart errors in timeline

---

### XR410 - Login Error Time Distribution (1-Minute Bins)

**Purpose:** Get a fine-grained timeline of errors to pinpoint the exact restart window and error cascade sequence.

**What to look for:**
- Tight cluster of different 40613 substates within a 1-5 minute window = single restart event
- State 10 typically dominates the error volume during the restart window
- State 22 appears slightly later as gateway backlog builds

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where event == "process_login_finish"
| summarize SuccessCount = countif(error == 0),
            FailCount = countif(error > 0),
            State10 = countif(error == 40613 and state == 10),
            State12 = countif(error == 40613 and state == 12),
            State13 = countif(error == 40613 and state == 13),
            State22 = countif(error == 40613 and state == 22),
            State44 = countif(error == 40613 and state == 44),
            State126 = countif(error == 40613 and state == 126),
            UserErrors = countif(is_user_error == true)
    by bin(originalEventTimestamp, 1m)
| order by originalEventTimestamp asc
```

**Expected output:**
- **SuccessCount / FailCount**: Overall login health per minute
- **State10..State126**: Individual 40613 substate counts per minute
- **UserErrors**: Customer authentication failures per minute

---

## Step 6: Login Volume Analysis

### XR600 - Login Rate Per Minute Per Instance

**Purpose:** Determine if the instance is under heavy login volume, which can trigger or amplify XdbHost restart incidents.

**What to look for:**
- 🚩 > 2500 logins/minute per instance = extremely high volume
- High login volume + user errors = customer flooding with bad credentials
- Login rate spike correlating with error onset

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where event == "process_login_finish"
| summarize TotalLogins = count(),
            SuccessLogins = countif(error == 0),
            FailedLogins = countif(error > 0),
            UserErrors = countif(is_user_error == true)
    by bin(originalEventTimestamp, 1m)
| order by originalEventTimestamp asc
```

**Expected output:**
- **TotalLogins**: Raw volume per minute
- **SuccessLogins / FailedLogins / UserErrors**: Breakdown
- 🚩 Flag if TotalLogins > 2500 per minute bin

---

## Step 7: Verify Self-Mitigation

### XR700 - Post-Restart Login Success Rate

**Purpose:** After the restart window, verify that logins have resumed successfully and no ongoing error conditions persist.

**What to look for:**
- SuccessCount should steadily increase after the restart window completes
- XdbHost restart errors (states 10, 12, 13, 44, 126) should drop to 0
- 🚩 If 40613/22 persists after restart completes, investigate as a separate gateway/network problem
- 🚩 If any restart-related errors persist > 15 minutes after new process_id appears, escalate

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where originalEventTimestamp between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where event == "process_login_finish"
| summarize SuccessCount = countif(error == 0),
            RestartErrors = countif(error == 40613 and state in (10, 12, 13, 44, 126)),
            ThrottleErrors = countif(error == 40613 and state == 22),
            OtherErrors = countif(error > 0 and not(error == 40613 and state in (10, 12, 13, 22, 44, 126)))
    by bin(originalEventTimestamp, 5m)
| order by originalEventTimestamp asc
```

**Expected output:**
- **SuccessCount**: Should resume after restart
- **RestartErrors**: Should drop to 0 after restart completes
- **ThrottleErrors**: Should subside within minutes of restart completion
- **OtherErrors**: Persistent other errors may indicate a separate issue
