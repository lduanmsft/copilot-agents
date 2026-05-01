# Terms and Concepts for Node Health Diagnostics

!!!AI Generated. To be verified!!!

## Core Concepts

### Node Health

Node health refers to the overall operational status of a Service Fabric node hosting SQL Database workloads. A healthy node:
- Reports `health_state = Ok`
- Has `node_status = Up`
- Has no active repair tasks
- Has no infrastructure faults (bugchecks, network issues)

### Degraded Node

A "degraded node" is a node where Service Fabric does not detect it as unhealthy, but applications are experiencing problems. This is a common scenario where:
- Service Fabric health reports show Ok
- But apps running on the node have issues (slow responses, failures)
- Root cause may be at Guest OS, container, host, or network layer

### Node State Transitions

Service Fabric nodes can be in various states:

| State | Description |
| ----- | ----------- |
| **Up** | Node is operational and accepting workloads |
| **Down** | Node is not responding to Service Fabric |
| **Disabling** | Node is being prepared for maintenance/repair |
| **Disabled** | Node is disabled and not accepting new workloads |
| **Unknown** | Node state cannot be determined |

### Health States

| Health State | Description |
| ------------ | ----------- |
| **Ok** | Node is healthy |
| **Warning** | Node has potential issues requiring attention |
| **Error** | Node has critical issues affecting workloads |

## Service Fabric Components

### RepairPolicyEngine

The RepairPolicyEngine is an automated system that manages unhealthy nodes through a repair workflow:

1. **Reboot** - Restart the node
2. **Heal** - Apply healing actions
3. **Reimage** - Rebuild the node from scratch

Repair tasks are tracked in WinFabLogs with state transitions that can be monitored via Kusto queries.

### Emitter Node vs. Affected Node

In Service Fabric health reports:
- **Emitter Node**: The node that generates the health report
- **Affected Node**: The actual node experiencing the issue

🚩 **Important**: These can be different! Always verify which node is actually failing by checking the health report details.

## Infrastructure Events

### Bugcheck Events

A bugcheck (also known as "blue screen" or system crash) indicates a critical OS-level failure:
- Logged in MonSystemEventLogErrors
- Contains bugcheck codes (e.g., `0x0000007E`)
- Causes node restart and potential workload disruption

Common bugcheck codes:
| Code | Description |
| ---- | ----------- |
| `0x0000007E` | System thread exception not handled |
| `0x0000009F` | Driver power state failure |
| `0x000000D1` | Driver IRQL not less or equal |
| `0x00000050` | Page fault in non-paged area |

### Node Repair Tasks

Repair tasks are initiated when nodes require maintenance:
- Tracked in WinFabLogs
- Have multiple states: Created, Preparing, Approved, Executing, Completed
- Can take extended time (hours to days)
- May be initiated by automated systems or manually

## Diagnostic Tools

### SQL Node Health Dashboard

A Kusto-based dashboard for monitoring node health across PaasV2 rings:
- Shows ring and node health states
- Provides historical health data
- Enables quick identification of problematic nodes

### Service Fabric Explorer (SFE)

Web-based tool for viewing Service Fabric cluster state:
- Shows real-time node status
- Displays health reports
- **Warning**: Do not use SFE's restart option for nodes (only restarts fabric.exe, not the machine)

### ASI Tool (EEE RODS - VM Availability)

Used to verify VM, host, and network health:
- Checks VM-level health
- Identifies host-level issues
- Detects network problems
- Access via sqlconnlsi or manual entry of node/container IDs

### FCShell and psping

Command-line tools for real-time node status checks:
- **FCShell**: Service Fabric command shell
- **psping**: Network connectivity testing

## Common Root Causes

### Infrastructure Issues

1. **VM/Host Issues**
   - Hardware failures
   - Host OS problems
   - VMSS scale issues

2. **Network Issues**
   - Network partitions
   - Connectivity timeouts
   - DNS resolution failures

3. **Storage Issues**
   - Disk I/O problems
   - Storage throttling
   - XStore connectivity

### Service Fabric Issues

1. **Lease Loss**
   - Node loses lease with cluster
   - Causes node to be marked as Down

2. **Bootstrap Failures**
   - Service Fabric fails to start properly
   - Prevents node from joining cluster

3. **Startup Task Failures**
   - SQL startup tasks fail
   - Node becomes unreachable for workloads

## Escalation Paths

### Severity Levels

| Severity | Description | Example |
| -------- | ----------- | ------- |
| **Sev1** | Ring collapse, major customer impact | Multiple nodes down, widespread outage |
| **Sev2** | Significant impact, needs immediate attention | Single node affecting critical workloads |
| **Sev3** | Deployment blockers, minor impact | Node issues blocking deployments |

### When to Escalate

- **To Compute Team**: VM-level issues, VMSS problems, host failures
- **To Platform Team**: Service Fabric issues, infrastructure-wide problems
- **To SQL Availability**: Database-specific issues on the node

## Related Documentation

- [Investigate node health issues TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/sqlmh008-investigate-node-health-issues)
- [Node health quick identification TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/draft-sqlmh000-node-health-quick-identification-and-mitigation)
- [PaasV2 node repairs TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-deployment-infrastructure/azure-sql-db-deployment/machine-health/sqlmh002-paasv2-node-repairs)
- [Alias DB - SF node error state TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/alias/alias-db-node-error-state)
