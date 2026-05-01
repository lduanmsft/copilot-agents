# Terms and Concepts

## General Concepts

1. **Azure SQL Database Overview**: See https://learn.microsoft.com/en-us/azure/azure-sql/database/sql-database-paas-overview?view=azuresql

2. **Application Instance**: Physical SQL Server. An instance can have multiple databases depending on application type.

3. **Service Tiers**:
   - **General Purpose (GP)**: Basic tier with one or two replicas
   - **Business Critical (BC)**: Multiple local replicas per SQL instance
   - **Hyperscale (HS)**: Scalable architecture

4. **Deployment Models**:
   - **Single database**: Fully isolated database
   - **Elastic pool**: Multiple databases in a single SQL process (application instance)

5. **Availability Zones**: SQL instance deployed across multiple availability zones for high availability.
   - Terms used interchangeably: multi-AZ, Zone-redundant, zonal, ZR, zone_resilient

6. **General Purpose and Availability Zones**:
   - **GP without ZR**: One replica only (non-ZR, none-ZR)
   - **GP with ZR**: Two replicas - one with user data access, one standby ready for failover

7. **"Short" or "Shortly"**: Means 5 minutes or less throughout documentation

## Primary Change Behavior

**Multi-replica instances (BC and GP with ZR)**:
- Transition from old primary to secondary replica
- On successful transition, old secondary becomes new primary

**Single-replica instances (GP without ZR)**:
- Only one instance (Single Instance Volatile in Service Fabric)
- On termination, instance is dropped and deleted
- New placement is created
- Process is AddPrimary event (not a transition)

## Telemetry Data Concepts

1. **Logical Server and Logical Database**:
   - Logical server can have multiple SQL instances
   - Instance can have multiple databases
   - Used interchangeably: LogicalServer, Logical_Server, LogicalServerName, Logical_Server_Name
   - Same for: LogicalDatabase, Logical_Database, LogicalDatabaseName, Logical_Database_Name

2. **Application Types**:
   - `AppTypeName` differentiates service tiers
   - Part of `fabric_application_uri`

3. **fabric_application_uri**:
   - `fabric:/Worker.ISO/b3f8a0fbfabf` → General Purpose (GP)
   - `fabric:/Worker.ISO.Premium/c4f8a0fbfabf` → Business Critical (BC)

4. **zone_resilient**:
   - `0` = Single availability zone
   - `1` = Multi-availability zone (zonal, ZR)

5. **tenant_ring_name**: Also known as `ClusterName` in queries
