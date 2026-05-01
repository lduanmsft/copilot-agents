# Debug Principles for Node Health Diagnostics

!!!AI Generated. To be verified!!!

## Triage Principles

### 1. Identify the Affected Node

**First step**: Always confirm which node is actually affected:

1. **Check if database was on the node** (NH100 - Locate Database Node)
2. **Verify node health state** (NH200 - Check Service Fabric Node State)
3. **Distinguish emitter vs affected node** in health reports

🚩 **Warning**: Service Fabric health reports may show an emitter node that is different from the affected node. Always verify by checking the health report details.

### 2. Determine Issue Layer

Classify the issue by layer to route to appropriate team:

| Layer | Symptoms | Queries | Escalation |
| ----- | -------- | ------- | ---------- |
| **Application/SQL** | SQL errors, login failures | MonLogin queries | SQL Availability |
| **Service Fabric** | Node state changes, lease loss | MonClusterLoad, WinFabLogs | Platform Team |
| **Guest OS** | Bugchecks, OS crashes | MonSystemEventLogErrors | Compute Team |
| **Container/VM** | VM unresponsive, resource exhaustion | ASI Tool | Compute Team |
| **Host/Network** | Network timeouts, host issues | ASI Tool | Compute Team |

### 3. Check Node Up Time

**Principle**: If `node_up_time` is small, the node was recently restarted.

- Query MonClusterLoad for `node_up_time` field
- Small value indicates recent restart
- Correlate restart time with incident start time

## Investigation Workflow

### 4. Start with Database Location

Before investigating node health:
1. **Confirm which nodes hosted the database** during the incident (NH100)
2. **Get ClusterName and NodeName** for subsequent queries
3. If multiple nodes, investigate each

### 5. Check Service Fabric State First

Priority order for node diagnostics:
1. **Node state changes** (NH200) - Were there Up/Down transitions?
2. **Health state changes** - Did health degrade from Ok to Warning/Error?
3. **Infrastructure events** (NH300) - Were there platform-level faults?
4. **Bugchecks** (NH400) - Did the node crash?
5. **Repair tasks** (NH600) - Was the node under repair?

### 6. Use Extended Time Windows

**Principle**: Node issues may manifest before/after the incident window:

| Query | Before Window | After Window | Reason |
| ----- | ------------- | ------------ | ------ |
| Infrastructure events | -12h | +24h | Events may be delayed |
| Repair tasks | 0 | +3 days | Tasks can take days to complete |
| Node state | -1h | +1h | Capture state transitions |

## Warning Patterns

### 🚩 Immediate Attention Required

1. **Bugcheck detected**: Node crashed - check bugcheck code
2. **Node Down for extended period**: > 5 minutes requires investigation
3. **Multiple nodes affected**: Could indicate ring-level issue
4. **Repair task stuck**: Task not progressing through states
5. **Health state Error**: Critical node issues

### 🚩 Degraded Node Signs

Signs of a degraded node (SF shows Ok but apps have issues):
- Login failures specific to one node
- High latency only on certain node
- Intermittent failures not explained by SF health
- Resource exhaustion (CPU/memory) not triggering SF alerts

## Expected Timings

| Event | Normal | Warning | Critical |
| ----- | ------ | ------- | -------- |
| Node restart recovery | < 5 min | 5-15 min | > 15 min |
| Repair task completion | < 4 hours | 4-24 hours | > 24 hours |
| Health state recovery | < 2 min | 2-10 min | > 10 min |
| Node Up transition | < 30 sec | 30s-2min | > 2 min |

## Root Cause Categories

### 7. Categorize by Root Cause

| Category | Indicators | Action |
| -------- | ---------- | ------ |
| **Planned Maintenance** | Repair task present, scheduled | Wait for completion |
| **Bugcheck/Crash** | Bugcheck event, sudden Down state | Analyze bugcheck code, escalate to Compute |
| **Network Issue** | Connectivity errors, lease loss | Check ASI tool, escalate to Network |
| **Resource Exhaustion** | High CPU/memory, throttling | Check MonDmRealTimeResourceStats |
| **SF Bootstrap Failure** | Node never reaches Up state | Check SF logs, escalate to Platform |

## Repair Task States

### 8. Repair Task Analysis

Track repair task progression:

```
Created → Preparing → Approved → Executing → Completed
```

🚩 **Stuck indicators**:
- Task in same state for > 4 hours
- Task not reaching Completed after 24 hours
- Multiple failed repair attempts

**Caution**: Do NOT use Service Fabric Explorer's restart option to restart nodes - this only restarts fabric.exe, not the machine itself.

## Escalation Criteria

### 🚩 Escalate to Compute Team When:

- Bugcheck events detected
- VM-level issues confirmed via ASI
- Host/network problems identified
- VMSS scale issues

### 🚩 Escalate to Platform Team When:

- Service Fabric bootstrap failures
- Ring-level node health issues
- Repair tasks not progressing
- Multiple nodes affected simultaneously

### 🚩 Escalate to SQL Availability When:

- Database-specific issues on healthy nodes
- Login failures not explained by node state
- Workload issues after node recovery

## Post-Investigation Steps

### 9. Document Findings

Always document:
1. Timeline of node state changes
2. Root cause category identified
3. Repair tasks initiated or completed
4. Escalation actions taken
5. Customer impact duration

### 10. Verify Recovery

After mitigation:
1. Confirm node health_state = Ok
2. Confirm node_status = Up
3. Verify database accessibility (MonLogin success)
4. Check no new infrastructure events

## Related Documentation

- [Investigate node health issues TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/sqlmh008-investigate-node-health-issues)
- [Node health quick identification TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/draft-sqlmh000-node-health-quick-identification-and-mitigation)
- [PaasV2 node repairs TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/sqlmh002-paasv2-node-repairs)
