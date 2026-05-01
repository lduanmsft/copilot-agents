# Triage Queries

This file will contain Kusto queries for incident triage and classification.

## Query Parameter Placeholders

Replace these placeholders with actual values:
- `{StartTime}`: Start timestamp (e.g., `2026-01-01 02:00:00`)
- `{EndTime}`: End timestamp (e.g., `2026-01-01 03:00:00`)
- `{Duration}`: Duration (e.g., `1h`, `101m`, `4h + 30m`) - See [Kusto Timespan Format](../../../copilot-instructions.md#kusto-timespan-format)
- `{LogicalServerName}`: Logical server name
- `{LogicalDatabaseName}`: Logical database name
- `{ClusterName}`: From get-db-info skill (tenant_ring_name)
- `{AppName}`: From get-db-info skill (sql_instance_name)
- `{physical_database_id}`: From get-db-info skill
- `{fabric_partition_id}`: From get-db-info skill

---

## TRIAGE100 - Check SqlFailovers (TO BE IMPLEMENTED)

Query SqlFailovers to identify completed failover events during the incident window.

**Purpose**: Determine if this is a failover-related issue.

```kql
SqlFailovers
| where StartTime >= datetime({StartTime}) and EndTime <= datetime({EndTime})
| where LogicalServerName =~ '{LogicalServerName}' and LogicalDatabaseName =~ '{LogicalDatabaseName}'
| project StartTime, EndTime, FailoverType, Reason, Duration=EndTime-StartTime
| order by StartTime asc
```

---

## TRIAGE200 - Check LoginOutages (TO BE IMPLEMENTED)

Query LoginOutages for connectivity issues during the incident window.

**Purpose**: Understand customer impact and outage patterns.

```kql
LoginOutages
| where OutageStartTime >= datetime({StartTime}) and OutageEndTime <= datetime({EndTime})
| where LogicalServerName =~ '{LogicalServerName}' and LogicalDatabaseName =~ '{LogicalDatabaseName}'
| project OutageStartTime, OutageEndTime, OutageType, ImpactedLogins, Duration=OutageEndTime-OutageStartTime
| order by OutageStartTime asc
```

---

## TRIAGE300 - Check Service Fabric Health (TO BE IMPLEMENTED)

Query for Service Fabric health events indicating quorum loss or partition health issues.

**Purpose**: Identify quorum loss or Service Fabric-level problems.

```kql
// TO BE ADDED
// Check for System.FM health reports with quorum loss
// Check for partition state transitions
```

---

## Future Queries

Additional queries to be added:
- Check for replica health degradation patterns
- Analyze XEvent patterns for failure signatures
- Query for infrastructure events (compute, network, storage)
- Check for geo-replication link failures
- Analyze backup/restore operations

---

## Related Resources

- [SKILL.md](../SKILL.md) - Main skill documentation
