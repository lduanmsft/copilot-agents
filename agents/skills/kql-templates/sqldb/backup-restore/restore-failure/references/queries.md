!!!AI Generated. Manually verified!!!

# Kusto Queries for Restore Failure Analysis

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Resource identifiers:**
- `{LogicalServerName}`: Logical server name (target server for restore)
- `{SourceDatabaseName}`: Source database name
- `{TargetDatabaseName}`: Target database name
- `{RestoreRequestId}`: Restore request ID (GUID)
- `{RequestId}`: Management request ID
- `{ClusterName}`: Cluster name
- `{NodeName}`: Node name
- `{AppName}`: Application name (appname for the restoring database)

---

## RFQ100 - Find Restore Request State

**Purpose:** Find restore request and its current state from MonRestoreRequests.

**What to look for:**
- `state`: Ready (not triggered), Restoring (in progress), Completed, Failed, Cancelled
- `operation_details`: Error messages for failed restores
- For progress percentage, use RFQ200 (`MonRestoreEvents.restore_progress_percentage`)

```kql
MonRestoreRequests
| where target_logical_server_name =~ '{LogicalServerName}'
| where target_logical_database_name =~ '{TargetDatabaseName}'
| project TIMESTAMP, restore_request_id, state, operation_details, restore_type, target_logical_server_name, target_logical_database_name
| order by TIMESTAMP desc
| take 10
```

---

## RFQ200 - Check Restore Events Progress

**Purpose:** Monitor restore event progress and identify errors.

**What to look for:**
- Repeating same events = stuck restore
- `exception_type` not empty = errors occurring
- "Non retriable error" with SSL/TLS = silent failure (see BRDB0005.6)
- error 21105 with REPLICATION = Cloud Lifter regression

```kql
MonRestoreEvents
| where restore_request_id =~ '{RestoreRequestId}'
| order by originalEventTimestamp desc
| project originalEventTimestamp, event, restore_database_progress, message, exception_type
| take 20
```

---

## RFQ300 - Management Operation Status

**Purpose:** Check management workflow for validation failures or stuck operations.

**What to look for:**
- `management_workflow_restore_request_failure` event = validation error (check message column)
- Common validation failures: invalid point-in-time, server mismatch, database already exists
- Only `management_workflow_restore_request_begin` without failure = hanging request

```kql
MonManagementOperations
| where request_id contains '{RestoreRequestId}'
| where event in ('management_operation_success', 'management_operation_failure', 'management_operation_canceled', 'management_workflow_restore_request_begin', 'management_workflow_restore_request_failure')
| project originalEventTimestamp, event, operation_type, request_id, message
| order by originalEventTimestamp desc
```

---

## RFQ400 - Check SqlServer Exit Codes (Stuck Restore)

**Purpose:** Check if sqlservr.exe is failing to start or restarting during restore (blank or repeating MonRestoreEvents).

**What to look for:**
- Exit code **1460** = named pipe timeout on subcore SLOs. Mitigate with `Fix-StuckRestore.ps1`
- Exit code **7148** = WinFab terminated process (check other codes)
- Exit code **304** = SQL fast exit (check sqlsatelliterunner)
- High event count from PLB = app being moved around frequently

```kql
WinFabLogs
| where ClusterName == '{ClusterName}'
| where NodeName == '{NodeName}'
| where Text contains "sqlservr.exe" or Text contains "sqlsatelliterunner"
| project PreciseTimeStamp, NodeName, Text
| order by PreciseTimeStamp desc
| take 100
```

---

## RFQ500 - Post-Mitigation Verify Restore State

**Purpose:** Confirm restore reached a terminal state after mitigation.

**What to look for:**
- state = Completed: Restore successful
- state = Failed: Review operation_details for failure reason
- state = Cancelled: Restore was cancelled (target DB dropped)
- state = Restoring: Check RFQ200 for advancing restore_progress_percentage

```kql
MonRestoreRequests
| where target_logical_server_name =~ '{LogicalServerName}'
| where target_logical_database_name =~ '{TargetDatabaseName}'
| project TIMESTAMP, restore_request_id, state, operation_details, restore_type, target_logical_server_name, target_logical_database_name
| order by TIMESTAMP desc
| take 10
```

---

## Notes

- Hyperscale restores: Follow BRDB0005.1 instead
- V-instance (restore verification) stuck: Follow BRDB0005.7
- Insufficient disk space restoring to pool: Follow BRDB0005.9
- For `SterlingRestoreRequests.xts`: Enter server name to see all restore requests from CMS
- Cancel restore: Customer can drop target DB, or DevOps can use `Cancel-RestoreRequest -OperationId <request_id>`
- Source TSG: BRDB0005 (ADO Wiki: `/BackupRestore/BRDB0005 Restore Stuck_Failure Investigation` in TSG-SQL-DB-DataIntegration)
