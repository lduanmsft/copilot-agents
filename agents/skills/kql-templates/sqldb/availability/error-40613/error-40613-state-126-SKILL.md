---
name: error-40613-state-126
description: Diagnoses error 40613 state 126 (Database in transition) which occurs when a database cannot accept connections because it is actively undergoing a role change or failover. This is typically transient (<30 seconds) but becomes a problem when the transition state persists. Use when investigating prolonged unavailability during failovers, stuck role changes, or persistent "database in transition" errors.
---

# Error 40613 State 126 - Database in Transition

## Overview

Error 40613 state 126 indicates the database is in a **transitional state** and cannot accept connections. This occurs during:
- Replica role changes (secondary becoming primary)
- Active failover operations
- Service Fabric reconfiguration events

**Expected behavior**: This error is transient and typically resolves within 30 seconds as the role change completes.

**Problem scenario**: The error persists beyond 1-2 minutes, indicating a stuck or delayed transition.

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
- **PartitionId** (fabric_partition_id)
- **DatabaseId** (database ID #) used to filter MonSQLSystemHealth messages per-database, required when database is in an elastic pool where AppName is shared across multiple databases)

## Workflow

### 1. Confirm Error Pattern and Timeline

Execute query STATE126-100 from [references/queries.md](references/queries.md) to:
- Confirm error 40613 state 126 is occurring
- Identify the duration and frequency of errors
- Determine if errors are transient or persistent

**Assessment criteria:**
| Duration | Assessment | Action |
|----------|------------|--------|
| < 30 seconds | ✅ Expected transient error | No action needed - normal failover behavior |
| 30 sec - 2 min | ⚠️ Prolonged transition | Investigate role change delays |
| > 2 minutes | 🚩 Stuck transition | Escalate to failover investigation |

Execute query STATE126-110 from [references/queries.md](references/queries.md) to:
- Aggregates errors to identify persistence patterns

### 2. Correlate with Failover Events

Execute query STATE126-200 to check `SqlFailovers` table:
- Identify if a failover occurred during the error window
- Check `FailoverStartTime` and `FailoverEndTime` to correlate timing
- Determine `ReconfigurationType` (planned vs. unplanned)

**Key correlation:**
- State 126 errors should START when failover starts
- State 126 errors should STOP when failover completes
- If errors persist AFTER `FailoverEndTime`, there's a problem

### 3. Check Role Change Events

Execute query STATE126-300 to analyze role change XEvents:
- Look for `hadr_fabric_api_replicator_begin_change_role`
- Look for `hadr_fabric_api_replicator_end_change_role`
- Calculate time between begin and end events

**Warning signs:**
- `begin_change_role` without corresponding `end_change_role`
- Large gap (>60 seconds) between begin and end
- Multiple consecutive failed role changes

### 4. Check for Recovery Delays

If role change completed but errors persist, check database recovery:

Execute query STATE126-400 and STATE126-410 to check recovery status:
- Look for "Recovery completed" messages in `MonSQLSystemHealth`
- If recovery never completed, the database may be stuck in warmup (escalate to state 127 investigation)
- STATE126-410 tracks database startup and recovery progress.

### 5. Check LoginOutages for Impact Assessment

Execute query STATE126-500 to:
- Determine total outage duration reported by the platform
- Identify `OutageType` and `OwningTeam`
- Check if `OutageReasonLevel1` contains transition-related reasons

## Decision Tree

```
Error 40613 State 126 detected
│
├─ Duration < 30 seconds?
│   └─ YES → Expected transient error during normal failover
│            Action: RCA shows normal HA behavior, no issue
│
├─ Duration 30 sec - 2 min?
│   └─ Check SqlFailovers for corresponding failover
│       ├─ Failover found and completed?
│       │   └─ YES → Check recovery queries (STATE126-400)
│       │       └─ Recovery completed? → Issue resolved
│       │       └─ Recovery stuck? → Escalate to state 127 skill
│       └─ No failover found?
│           └─ Check WinFabLogs for reconfiguration events
│               └─ Escalate to failover skill for deep analysis
│
└─ Duration > 2 minutes?
    └─ 🚩 Stuck transition - Escalate immediately
        └─ Use failover skill for detailed role change analysis
```

## Root Cause Categories

| Category | Description | Typical Duration | Action |
|----------|-------------|------------------|--------|
| **Normal failover** | Standard role change during planned/unplanned failover | < 30 sec | No action |
| **Slow role change** | Role change taking longer than expected | 30 sec - 2 min | Monitor, check for resource contention |
| **Recovery delay** | Role change complete but database recovery slow | 1-5 min | Check state 127 skill, buffer pool warmup |
| **Stuck reconfiguration** | Service Fabric reconfiguration blocked | > 2 min | Escalate to failover skill, check quorum |
| **Node health issue** | Underlying node problems preventing transition | Variable | Check node-health skill |

## Execute Queries

Execute queries from [references/queries.md](references/queries.md):

**Step 1: Error Pattern**
- STATE126-100 (Error Volume and Duration)
- STATE126-110 (Error Summary by Time Window)

**Step 2: Failover Correlation**
- STATE126-200 (SqlFailovers)

**Step 3: Role Changes**
- STATE126-300 (Role Change XEvents)

**Step 4: Recovery Status**
- STATE126-400 (Database Recovery)
- STATE126-410 (Recovery Progress Messages)

**Step 5: Impact Assessment**
- STATE126-500 (LoginOutages)

## Escalation

- **Transient errors (< 30 sec)**: No escalation needed - expected behavior - Canned RCA
- **Prolonged errors (> 2 min)**: Invoke the `failover` skill for detailed role change analysis
- **Pattern of repeated state 126**: Check for frequent failovers using `freq-failover` skill
- **Node-related issues**: Invoke `node-health` skill

## Related Skills

- `failover` - Detailed failover analysis when transition delays detected
- `error-40613-state-127` - Database warmup issues (often follows state 126)
- `quorum-loss` - When role change blocked due to quorum issues
- `freq-failover` - When state 126 errors occur repeatedly

## Related Categories

- Category 2: High Availability & Failover Issues

## Routing Teams

- ComponentCode.Failover
- AZURESQLDB\Availability