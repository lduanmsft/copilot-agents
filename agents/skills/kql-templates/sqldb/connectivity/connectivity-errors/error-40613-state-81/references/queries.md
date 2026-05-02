> **AI-generated content — verify before use**

# Kusto Queries for Error 40613 State 81 (PaaSv2 IPv6 Prefix Mismatch)

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Time parameters:**
- `{StartTime}`: Start timestamp in UTC (ISO 8601 format)
- `{EndTime}`: End timestamp in UTC (ISO 8601 format)

**Resource identifiers:**
- `{LogicalServerName}`: Logical server name (e.g., `myserver`)
- `{LogicalDatabaseName}`: Logical database name

---

## Step 1: Confirm Error 40613 State 81 on PaaSv2 Cluster

### CONN81-100 - Error 40613 State 81 Volume and Scope

**Purpose:** Confirm error 40613 state 81 is occurring and assess the volume, time range, and affected tenant rings.

**What to look for:**
- Sustained error volume indicating active customer impact
- Errors occurring across multiple clients with proper VNet source prefix (`fde4:8dba`)
- Which tenant ring(s) and DB nodes are affected

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where TIMESTAMP between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where error == 40613 and state == 81
| where event == "process_login_finish"
| extend TargetTRRing = substring(instance_name, indexof(instance_name, ".") + 1)
| extend instance = tostring(split(instance_name, ".")[0])
| extend DBNode = tostring(split(fabric_node_name, "\\")[1])
| summarize ErrorCount = count(),
            min_time = min(TIMESTAMP),
            max_time = max(TIMESTAMP),
            dcount_peer = dcount(peer_address)
    by TargetTRRing, DBNode, instance
| order by ErrorCount desc
```

**Expected output:**
- **TargetTRRing**: Tenant ring receiving the connections
- **DBNode**: DB node name
- **ErrorCount**: Number of errors
- **dcount_peer**: Distinct client IPs affected
- 🚩 If errors span the entire cluster (multiple tenant rings), this strongly suggests a platform-level IPv6 prefix mismatch

---

## Step 2: Verify Error Timeline

### CONN81-200 - Error 40613 State 81 Over Time

**Purpose:** Understand the error timeline to assess ongoing impact and correlate with any config changes.

**What to look for:**
- When errors started and whether they are ongoing
- Whether error rate is constant or spiking (constant suggests config mismatch)

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where TIMESTAMP between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where error == 40613 and state == 81
| where event == "process_login_finish"
| summarize ErrorCount = count(),
            dcount_connections = dcount(connection_id)
    by bin(TIMESTAMP, 3m)
| order by TIMESTAMP asc
```

**Expected output:**
- **TIMESTAMP**: 3-minute time bins
- **ErrorCount**: Number of errors per bin
- **dcount_connections**: Distinct connection attempts

---

## Step 3: Verify Post-Mitigation (After CAB Applied)

### CONN81-300 - Post-Mitigation Login Verification

**Purpose:** After applying the IPv6 prefix config override CAB, verify that logins are now successful.

**What to look for:**
- Error count should drop to 0 or near 0 after CAB completion
- Successful logins should appear for the same server/database
- 🚩 If errors persist after CAB, Gateway restart may be needed

```kql
let StartTime = datetime({StartTime});
let EndTime = datetime({EndTime});
let ServerName = '{LogicalServerName}';
let DbName = '{LogicalDatabaseName}';
MonLogin
| where TIMESTAMP between (StartTime..EndTime)
| where logical_server_name =~ ServerName
| where database_name =~ DbName
| where event == "process_login_finish"
| summarize SuccessCount = countif(is_success == true),
            Error_40613_81 = countif(error == 40613 and state == 81),
            OtherErrors = countif(is_success == false and not(error == 40613 and state == 81))
    by bin(TIMESTAMP, 5m)
| order by TIMESTAMP asc
```

**Expected output:**
- **SuccessCount**: Should increase after mitigation
- **Error_40613_81**: Should drop to 0 after mitigation
- 🚩 If Error_40613_81 persists after CAB completion, check if Gateway apps need restart
