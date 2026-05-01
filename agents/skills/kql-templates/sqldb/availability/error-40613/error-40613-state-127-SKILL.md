---
name: error-40613-state-127
description: Diagnoses error 40613 state 127 (Cannot open database during warmup) which occurs after a role change completes but the database is still performing recovery (redo/undo phases) and cannot accept connections. This typically follows state 126 errors. Expected duration is 30 seconds to 2 minutes depending on database size and recovery workload. Use when investigating post-failover unavailability, slow database recovery, or stuck warmup scenarios.
---

# Error 40613 State 127 - Database Warmup Issues

## Overview

Error 40613 state 127 indicates the database is in a **warmup state** after a role change and cannot accept connections. This occurs during:
- Database recovery (redo/undo phases)
- Buffer pool population
- Post-failover initialization

**Timeline context**: State 127 typically follows state 126 errors. After the role change completes (state 126 ends), the new primary must perform database recovery before accepting connections.

```
Timeline: State 126 → State 127 → Database Available
──────────────────────────────────────────────────────────────────────────────
                                                                              
  T+0s              T+20s                 T+30s              T+60s            
   │                  │                     │                  │              
   ▼                  ▼                     ▼                  ▼              
[Begin Role    [Role Change         [Recovery           [Recovery         
 Change]        Complete]            Starts]             Complete]        
                                                                              
   ├──────────────────┼─────────────────────┼──────────────────┤              
   │     STATE 126    │      STATE 127      │   DB AVAILABLE   │              
   │   (transition)   │      (warmup)       │                  │              
   │                  │                     │                  │              
──────────────────────────────────────────────────────────────────────────────
```

**Expected behavior**: State 127 errors resolve within 30 seconds to 2 minutes for most databases after recovery completes.

**Problem scenario**: The error persists beyond 2 minutes, indicating slow or stuck recovery.

## Required Information

### From User or ICM:
- **logical_server_name**: The logical server name (e.g., `my-server`)
- **database_name**: The logical database name (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### Obtained from get-db-info skill:
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **physical_database_id**
- **PartitionId** (fabric_partition_id)
- **logical_database_id** - required for filtering MonSQLSystemHealth messages per-database when database is in an elastic pool

## Workflow

### 1. Confirm Error Pattern and Timeline

Execute query STATE127-100 from [.github/skills/error-40613-state-126/references/queries.md](.github/skills/error-40613-state-126/references/queries.md) to:
- Confirm error 40613 state 127 is occurring
- Identify the duration and frequency of errors
- Determine if errors are transient or persistent
- Capture `AppName`, `ClusterName`, `DBNodeName` for subsequent queries

**Assessment criteria:**
| Duration | Assessment | Action |
|----------|------------|--------|
| < 1 minute | ✅ Expected transient error | Normal warmup - no action needed |
| 1 - 2 min | ⚠️ Prolonged warmup | Investigate recovery delays |
| > 2 minutes | 🚩 Stuck warmup | Check for recovery issues, storage problems |

### 2. Correlate with Failover Events

Execute query STATE127-200 to check `SqlFailovers` table:
- Identify the preceding failover event
- Check `FailoverEndTime` - state 127 should start around this time
- Calculate gap between `FailoverEndTime` and when state 127 errors stop

**Key correlation:**
- State 127 errors should START around `FailoverEndTime` (when role change completes)
- State 127 errors should STOP when database recovery completes

### 3. Check Role Change Completion

Execute query STATE127-300 to verify role change completed:
- Look for `hadr_fabric_api_replicator_end_change_role` with success
- Confirm `new_role_desc = 'Primary'`
- If role change never completed successfully, escalate to state 126 skill

### 4. Check Database Recovery Status

Execute query STATE127-400 to check recovery progress:
- Look for "Starting up database" messages
- Look for "Recovery completed for database" messages
- Calculate recovery duration

**Recovery phases to monitor:**
1. **Analysis phase**: Determining what needs to be recovered
2. **Redo phase**: Replaying committed transactions
3. **Undo phase**: Rolling back uncommitted transactions

Execute query STATE127-410 for detailed recovery progress:
- Track redo/undo progress messages
- Identify if Parallel redo is being used
- Check for any recovery errors

### 5. Check for Recovery Blockers

If recovery is taking too long, check for blockers:

Execute query STATE127-500 to identify potential issues:
- Long-running transactions requiring undo
- Large redo workload
- Storage I/O issues
- Tempdb recovery delays

Execute query STATE127-510 to check for tempdb recovery:
- Tempdb must recover before user databases
- Check "Recovery completed for database tempdb"

### 6. Check LoginOutages for Impact Assessment

Execute query STATE127-600 to:
- Determine total outage duration reported by the platform
- Identify `OutageType` and `OwningTeam`
- Check if `OutageReasonLevel1` contains warmup-related reasons

## Decision Tree

```
Error 40613 State 127 detected
│
├─ Duration < 1 minute?
│   └─ YES → Expected warmup during normal failover
│            Action: RCA shows normal HA behavior, no issue
│
├─ Duration 1 - 2 minutes?
│   └─ Check recovery progress (STATE127-400)
│       ├─ Recovery completed but errors continue?
│       │   └─ Check write status granted (STATE127-700)
│       │       └─ Write status granted? → Issue resolved
│       │       └─ No write status? → Escalate to failover skill
│       └─ Recovery still running?
│           └─ Check for blockers (STATE127-500)
│               └─ Monitor and wait if normal progress
│               └─ Escalate if stuck or errors
│
└─ Duration > 2 minutes?
    └─ 🚩 Stuck warmup - Investigate immediately
        ├─ Recovery never completed?
        │   └─ Check storage issues, error logs
        ├─ Tempdb recovery stuck?
        │   └─ Check for DropTempObjectsOnDBStartup issues
        └─ No clear blocker?
            └─ Escalate to failover skill for deep analysis
```

## Root Cause Categories

| Category | Description | Typical Duration | Action |
|----------|-------------|------------------|--------|
| **Normal warmup** | Standard recovery after failover | < 1 min | No action - canned RCA |
| **Large redo workload** | Many transactions to replay | 1-2 min | Monitor, expected for busy databases |
| **Long undo** | Large uncommitted transaction rollback | 1-10 min | Monitor, check for long-running transactions |
| **Tempdb delays** | DropTempObjectsOnDBStartup taking time | 1-5 min | Check temp object count |
| **Storage issues** | I/O problems during recovery | Variable | Check XStore, disk metrics |
| **Stuck recovery** | Recovery not progressing | > 2 min | Escalate, may need replica restart |

## Execute Queries

Execute queries from [references/queries.md](references/queries.md):

**Step 1: Error Pattern**
- STATE127-100 (Error Volume and Duration)
- STATE127-110 (Error Summary by Time Window)

**Step 2: Failover Correlation**
- STATE127-200 (SqlFailovers)

**Step 3: Role Change Completion**
- STATE127-300 (Role Change End Events)

**Step 4: Recovery Status**
- STATE127-400 (Database Recovery Messages)
- STATE127-410 (Detailed Recovery Progress)

**Step 5: Recovery Blockers**
- STATE127-500 (SQL Error Log Messages)
- STATE127-510 (Tempdb Recovery)

**Step 6: Impact Assessment**
- STATE127-600 (LoginOutages)

**Step 7: Write Status (if needed)**
- STATE127-700 (Write Status Granted)

## Escalation

- **Transient errors (< 1 min)**: No escalation needed - expected behavior
- **Prolonged warmup (1-2 min)**: Monitor recovery progress, escalate if stuck
- **Stuck warmup (> 2 min)**: Invoke the `failover` skill for detailed analysis
- **Recovery errors**: Check error logs, may need node-health skill
- **Storage issues**: Check XStore/storage health

## Related Skills

- `error-40613-state-126` - Role change/transition issues (precedes state 127)
- `failover` - Detailed failover analysis when warmup issues persist
- `quorum-loss` - When recovery blocked due to quorum issues
- `node-health` - When underlying node problems affect recovery

## Related Categories

- Category 2: High Availability & Failover Issues

## Routing Teams

- ComponentCode.Failover
- AZURESQLDB\Availability