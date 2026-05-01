---
name: node-health
description: Diagnoses node-level issues including node health, node failures, Service Fabric node events, infrastructure problems (bugchecks, reboots), and repair tasks affecting SQL Server nodes. Use when investigating node state changes, degraded nodes, or infrastructure-level faults.
---

# Node Health Diagnostics

!!!AI Generated. To be verified!!!

This skill analyzes Service Fabric node health, node lifecycle events, and infrastructure issues that impact SQL Server availability.

## Scope

- Node health status and failures
- Service Fabric node deactivation/activation
- Infrastructure issues affecting nodes (bugchecks, reboots)
- Node-level resource constraints
- Network connectivity at node level
- Node repair tasks and updates
- Degraded nodes (SF shows Ok but apps have issues)

## Understanding Node Issues

### Degraded Node vs. Down Node

| Aspect | Degraded Node | Down Node |
| ------ | ------------- | --------- |
| **SF Health** | Ok | Warning/Error |
| **Node Status** | Up | Down/Disabled |
| **Detection** | App-level issues | SF health reports |
| **Root Cause** | Guest OS, container, host, network | Node failure, bugcheck |

### Key Investigation Layers

| Layer | Symptoms | Query |
| ----- | -------- | ----- |
| Service Fabric | State changes, lease loss | NH200, NH500 |
| Infrastructure | Faults, network issues | NH300 |
| OS Level | Bugchecks, crashes | NH400 |
| Repair System | Repair tasks | NH600 |

## Required Information

To run this skill, you need:
- **LogicalServerName**: The logical server name
- **LogicalDatabaseName**: The logical database name
- **StartTime**: Start of the time window (ISO format, e.g., 2026-01-27T00:00:00Z)
- **EndTime**: End of the time window (ISO format, e.g., 2026-01-27T23:59:59Z)

## Workflow

The skill performs the following diagnostic steps:

### Step 1: Locate Database Node
**Query**: NH100 - Locate Database Node
- Identifies the node(s) where the database was running during the time window
- Outputs: ClusterName, NodeName
- Use NodeName as `{DBNodeName}` for subsequent queries

### Step 2: Check Service Fabric Node State
**Queries**: NH200, NH210 - Check Service Fabric Node State
- Retrieves Service Fabric node state changes
- Shows health_state and node_status transitions
- Filters to only show state changes
- Check `node_up_time` - small value indicates recent restart

### Step 3: Check Node Health Events
**Query**: NH300 - Check Node Health Events
- Queries MonSQLInfraHealthEvents for any anomalies on the node
- Checks extended time window (12h before to 24h after outage)
- Identifies infrastructure-level faults

### Step 4: Check for Bugcheck Events
**Query**: NH400 - Check for Bugcheck Events
- Searches system event logs for bugcheck/crash events
- Extracts bugcheck codes if present
- 🚩 Bugcheck detected requires escalation to Compute team

### Step 5: Check Node Up/Down Events
**Query**: NH500 - Check Node Up/Down in WinFabLogs
- Searches WinFabLogs for NodeUp/NodeDown events
- Provides timeline of node state transitions

### Step 6: Check Node Repair Tasks
**Query**: NH600 - Check Node Repair Tasks
- Identifies repair tasks targeting the node
- Shows task state transitions and timing
- Extended window (+3 days) to capture long-running tasks

### Step 7: Check Restart Actions
**Query**: NH700 - Check RestartCodePackage Actions
- Identifies automated restart actions by watchdogs
- Shows reason for restart

## Expected Outputs

The skill will identify:
1. Which nodes hosted the database during the incident
2. Any Service Fabric health state changes
3. Infrastructure health events
4. Bugcheck/crash events
5. Node up/down transitions
6. Repair tasks initiated on the node
7. Automated restart actions

## Escalation Criteria

### 🚩 Escalate to Compute Team When:
- Bugcheck events detected (NH400 returns results)
- VM-level issues confirmed
- Host/network problems identified
- VMSS scale issues

### 🚩 Escalate to Platform Team When:
- Service Fabric bootstrap failures
- Ring-level node health issues
- Repair tasks not progressing (stuck > 4 hours)
- Multiple nodes affected simultaneously

### 🚩 Escalate to SQL Availability When:
- Database-specific issues on healthy nodes
- Login failures not explained by node state
- Workload issues after node recovery

## Reference

See [knowledge.md](references/knowledge.md) for detailed definitions and concepts.
See [principles.md](references/principles.md) for debug principles and escalation criteria.

## Related Documentation

- [Investigate node health issues TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/sqlmh008-investigate-node-health-issues)
- [Node health quick identification TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/draft-sqlmh000-node-health-quick-identification-and-mitigation)
- [PaasV2 node repairs TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/sqlmh002-paasv2-node-repairs)
- [Alias DB - SF node error state TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/alias/alias-db-node-error-state)
