---
name: error-40613-state-129
description: Diagnoses error 40613 state 129 (HADR not available) which occurs when the database replica is not in a PRIMARY or SECONDARY state and cannot accept connections. This is strongly correlated with Hyperscale (Socrates) page server issues but can also occur in GP/BC during quorum loss, replica deactivation, or extended role transitions. Use when investigating HADR unavailability, Hyperscale page server failures, replica state issues, or persistent "database not currently available" errors where state is 129.
---

# Error 40613 State 129 - HADR Not Available

## Overview

Error 40613 state 129 indicates the database's **HADR (High Availability and Disaster Recovery) subsystem is not in a PRIMARY or SECONDARY state** and therefore cannot accept connections. The replica may be in states such as NONE, RESOLVING, or NOT_AVAILABLE.

**Key observation**: Incident analysis shows state 129 errors are **strongly correlated with Hyperscale (Socrates) SLOs**. All historically observed state 129 incidents involved Hyperscale databases with page server connectivity or lifecycle issues. However, the error can also occur in GP/BC during extended role transitions or quorum loss.

```
Replica HADR States:
──────────────────────────────────────────────────────────────────────────────

  PRIMARY ◄────────────────► SECONDARY     ← Normal operating states
     │                            │           (connections accepted)
     │                            │
     ▼                            ▼
   NONE ◄──────────────────► RESOLVING     ← Abnormal states
     │                            │           (state 129 errors)
     ▼                            ▼
 NOT_AVAILABLE              DEACTIVATED    ← HADR subsystem unavailable
                                              (state 129 errors)
──────────────────────────────────────────────────────────────────────────────
```

**Expected behavior**: State 129 errors are **not** expected during normal failovers. Normal failovers produce state 126 (transition) → state 127 (warmup). State 129 indicates an abnormal HADR state.

**Problem scenario**: The replica's HADR subsystem is not functioning normally, often due to:
- Hyperscale page server failures or connectivity issues
- Quorum loss leaving replica in RESOLVING state
- Replica deactivation by Service Fabric
- Extended role transition where replica is in NONE state

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
- **sql_database_id** - required for filtering MonSQLSystemHealth messages per-database when AppName is shared (elastic pool)

## Workflow

### 1. Confirm Error Pattern and SLO Type

Execute query STATE129-100 from [references/queries.md](references/queries.md) to:
- Confirm error 40613 state 129 is occurring
- Identify the duration and frequency of errors
- Capture `AppName`, `ClusterName`, `NodeName` for subsequent queries

**CRITICAL first check**: After running get-db-info (DBINFO100), check the `service_level_objective`:
- If SLO starts with `SQLDB_HS_` → **Hyperscale (Socrates)** — page server issues are the primary suspect
- If SLO starts with `SQLDB_BC_` or `SQLDB_GP_` → **GP/BC** — quorum loss or role transition issues

**Assessment criteria:**
| Duration | Assessment | Action |
|----------|------------|--------|
| < 30 seconds | ⚠️ Brief HADR disruption | Check for associated failover |
| 30 sec - 5 min | 🚩 Extended HADR unavailability | Investigate replica state, page servers |
| > 5 minutes | 🚩🚩 Persistent HADR failure | Escalate - check quorum, node health |

### 2. Correlate with Failover Events

Execute query STATE129-200 to check `SqlFailovers` table:
- Determine if a failover occurred during the error window
- State 129 may occur **before** a failover (HADR down triggers failover) or **during** extended transitions

**Key correlation:**
- If failover found: State 129 may be transient during the transition
- If **no failover found**: The HADR subsystem is down without a failover in progress — more serious

### 3. Check Replica Role and State

Execute query STATE129-300 to analyze role change and replica state events:
- Look for `hadr_fabric_api_replicator_begin_change_role` / `end_change_role`
- Check `current_state_desc` for abnormal states (NONE, RESOLVING, NOT_AVAILABLE)
- Determine if the replica was transitioning or stuck

**Warning signs:**
- `new_role_desc = 'NONE'` with no subsequent role change to PRIMARY
- `current_state_desc = 'RESOLVING'` — indicates quorum issues
- No role change events at all during the error window — HADR may be completely down

### 4. Check Replica State Transitions

Execute query STATE129-310 to track HADR replica state changes:
- Look for `hadr_fabric_api_replicator_state_change` events
- Track transitions between HADR states
- Identify when/if the replica returned to PRIMARY/SECONDARY

### 5. Check System Health for Errors

Execute query STATE129-400 to check MonSQLSystemHealth:
- Look for HADR-related error messages
- Page server errors (Hyperscale)
- Storage or I/O failures
- Any error messages around the time of state 129

For Hyperscale databases, also execute STATE129-410:
- Check for Socrates/page server specific messages
- Look for page server connectivity failures

### 6. Check LoginOutages for Impact Assessment

Execute query STATE129-500 to:
- Determine total outage duration reported by the platform
- Identify `OutageType` and `OwningTeam`
- Check `OutageReasonLevel1` for HADR-related reasons

### 7. Check Write Status

Execute query STATE129-600 to verify write status:
- Check if write status was ever revoked
- Track when/if write status was restored

## Decision Tree

```
Error 40613 State 129 detected
│
├─ SLO is Hyperscale (SQLDB_HS_*)?
│   └─ YES → Primary suspect: Page server issues
│       ├─ Check MonSQLSystemHealth for page server errors (STATE129-410)
│       ├─ Check LoginOutages (STATE129-500)
│       │   └─ OutageReasonLevel1, OutageReasonLevel2, or OutageReasonLevel3 contains "PageServer" or "Socrates"?
│       │       └─ YES → Page server root cause confirmed
│       │       └─ NO → Check role changes (STATE129-300)
│       └─ Escalate to Hyperscale/Socrates team if persistent
│
├─ SLO is Business Critical (SQLDB_BC_*)?
│   └─ Check role change events (STATE129-300)
│       ├─ Replica in `RESOLVING` state?
│       │   └─ Quorum loss — escalate to quorum-loss skill
│       ├─ Replica in NONE state with no recovery?
│       │   └─ Extended role transition — escalate to failover skill
│       └─ No role change events?
│           └─ HADR subsystem down — check node-health skill
│
└─ SLO is General Purpose (SQLDB_GP_*)?
    └─ Check role change events (STATE129-300)
        ├─ Associated failover found?
        │   └─ Transient during failover — monitor
        └─ No failover?
            └─ Check for deactivation or node issues
                └─ Escalate to node-health or failover skill
```

## Root Cause Categories

| Category | Description | SLO Affinity | Typical Duration | Action |
|----------|-------------|--------------|------------------|--------|
| **Page server failure** | Socrates page server connectivity lost | Hyperscale | 1-5 min | Check page server health, escalate to Socrates team |
| **Quorum loss** | Replica stuck in `RESOLVING` | BC/GP | Variable | Use quorum-loss skill |
| **Extended role transition** | Replica in NONE state too long | All | 30s-5 min | Use failover skill |
| **Replica deactivation** | SF deactivating replica | All | Variable | Check node-health skill |
| **HADR startup failure** | HADR subsystem failed to initialize | All | Variable | Check error logs, escalate |
| **Node failure** | Underlying node problems | All | Variable | Use node-health skill |

## Execute Queries

Execute queries from [references/queries.md](references/queries.md):

**Step 1: Error Pattern**
- STATE129-100 (Error Volume and Duration)
- STATE129-110 (Error Summary by Time Window)

**Step 2: Failover Correlation**
- STATE129-200 (SqlFailovers)

**Step 3: Replica State**
- STATE129-300 (Role Change Events)
- STATE129-310 (Replica State Transitions)

**Step 4: System Health**
- STATE129-400 (SQL Error Log Messages)
- STATE129-410 (Hyperscale/Page Server Messages — HS SLOs only)

**Step 5: Impact Assessment**
- STATE129-500 (LoginOutages)

**Step 6: Write Status**
- STATE129-600 (Write Status)

**Step 7: Full Timeline (if needed)**
- STATE129-700 (Full Timeline Combined View)

## Escalation

- **Brief disruption (< 30 sec)**: Monitor, may be transient during reconfiguration
- **Hyperscale page server issues**: Escalate to Socrates/Hyperscale team
- **Quorum loss**: Invoke `quorum-loss` skill
- **Extended HADR failure (> 5 min)**: Invoke `failover` skill, then `node-health` skill
- **Repeated state 129**: Check for recurring page server or infrastructure issues

## Related Skills

- `error-40613-state-126` - Role change/transition issues (normal failover path)
- `error-40613-state-127` - Database warmup issues (normal failover path)
- `failover` - Detailed failover analysis
- `quorum-loss` - When HADR stuck in RESOLVING due to quorum issues
- `node-health` - When underlying node problems affect HADR

## Related Categories

- Category 2: High Availability & Failover Issues

## Routing Teams

- ComponentCode.Failover
- AZURESQLDB\Availability
- AZURESQLDB\Socrates (for Hyperscale page server issues)