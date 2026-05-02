!!!AI Generated. Manually verified!!!

# Kusto Queries for Dropped Server Restore

## Query Parameter Placeholders

Replace these placeholders with actual values:

**Resource identifiers:**
- `{SubscriptionId}`: Customer subscription ID
- `{LogicalServerName}`: Logical server name that was dropped
- `{LogicalDatabaseName}`: Database name
- `{IcMId}`: ICM incident ID

---

## RSV100 - Discover Original Region

**Purpose:** Find the original region for a dropped server when region is not provided by CSS.

**What to look for:**
- ClusterName in results indicates the region
- Most recent server-related operations

**Pre-requisite:** In Kusto, select `SqlAzure.Stage`. Use `_ExecuteForProdAndStageClusters` macro to search multiple regions.

```kql
let SingleCluster = (clstr: string) {
cluster(clstr).database("sqlazure1").MonManagement
| where TIMESTAMP >= ago(30d)
| where operation_parameters contains '{SubscriptionId}'
| where operation_type contains 'Server'
};
_ExecuteForProdAndStageClusters
```

---

## RSV200 - Verify Backup Existence for PITR

**Purpose:** Verify backups exist before attempting PITR recovery. Generates `List-XStoreBlobs` commands to check for full backups in storage.

**What to look for:**
- If `List-XStoreBlobs` returns "StatusCode: NotFound", backup does not exist and restore is not possible
- If `List-XStoreBlobs` returns blob metadata, backup exists and PITR can proceed

```kql
MonBackup
| where backup_type in ("Full")
| where event_type == "BACKUP_END"
| where LogicalServerName in ('{LogicalServerName}')
| where isnotempty(logical_database_name)
| where logical_database_name != "master"
| summarize arg_max(originalEventTimestamp, *) by LogicalServerName, logical_database_name, logical_database_id
| extend storage_account = extract("https://([^.]+)\\..*", 1, backup_path)
| extend container_name = extract("https://[^/]+/([^/]+)/.*", 1, backup_path)
| extend blob_name = extract("https://[^/]+/[^/]+/(.*)", 1, backup_path)
| extend list_blobs_cmd = strcat("List-XStoreBlobs",
    " -StorageAccountName ", storage_account,
    " -StorageContainerName ", container_name,
    " -BlobName ", blob_name)
| project originalEventTimestamp, LogicalServerName, logical_database_name, backup_path, list_blobs_cmd
```

---

## RSV300 - Generate Restore Script Commands

**Purpose:** Generate the `Restore-DatabaseFromDroppedServer.ps1` commands for each database that needs restoration.

**What to look for:**
- All expected databases are listed
- The `restoreDBScript` column contains the ready-to-run command
- Verify `backup_retention_days` is sufficient for the recovery window

```kql
let IcMId = '{IcMId}';
let oldServerName = '{LogicalServerName}';
let BlobEndpointSuffix = '';
MonAnalyticsDBSnapshot
| where PreciseTimeStamp < ago(1d)
| summarize arg_max(PreciseTimeStamp, *) by logical_database_id
| where logical_server_name in (oldServerName) and logical_database_name <> 'master'
| project customer_subscription_id, logical_server_name, logical_database_name, logical_database_id, backup_retention_days, resource_group, state,
    edition, service_level_objective, max_size_bytes, last_update_time, xtp_enabled, failover_group_id, logical_resource_pool_id, tenant_ring_name, license_type, read_scale_units
| sort by customer_subscription_id, logical_server_name, logical_database_name
| extend restoreDBScript = strcat(
    './Restore-DatabaseFromDroppedServer.ps1 -IncidentNumber ', IcMId,
    ' -SubscriptionId ', customer_subscription_id,
    ' -OldServerName ', logical_server_name,
    ' -OldDatabaseName ', logical_database_name,
    ' -NewServerName ', logical_server_name,
    ' -NewDatabaseName ', logical_database_name,
    '_temp',
    ' -SkipOldDbIdVerification $true'
)
| project customer_subscription_id, logical_server_name, logical_database_name, backup_retention_days, logical_database_id, restoreDBScript
```

---

## RSV400 - Find BlobEndpointSuffix (Non-Public Clouds)

**Purpose:** Determine the correct blob endpoint suffix for non-public cloud environments.

```kql
MonBackup
| where PreciseTimeStamp > ago(1d)
| where backup_type =~ "full"
| where event_type has_any ("metadata", "end", "start")
| where isnotempty(backup_path)
| take 1
| project backup_path
| parse backup_path with *"//" * "." suffix "/" *
```

**Example result:** `blob.core.usgovcloudapi.net`

---

## RSV500 - Check TDE Encryption Type

**Purpose:** Check if the database uses Customer Managed Keys (CMK) for TDE, which requires special handling during restore.

**What to look for:**
- `encryptor_type` = "ASYMMETRIC KEY" indicates CMK — customer must grant new server access to the key vault
- `encryptor_type` = "CERTIFICATE" indicates service-managed TDE — use `Add-FindAndAddTdeSecretToExternalSecrets` CAS

```kql
MonDatabaseEncryptionKeys
| where LogicalServerName contains '{LogicalServerName}'
| where logical_database_id contains '{logical_database_id}'
| where TIMESTAMP > ago(18d)
| where TIMESTAMP < ago(16d)
| project TIMESTAMP, AppName, AppTypeName, logical_database_id, encryptor_type
| order by TIMESTAMP asc
```

---

## Notes

- CRI must be filed within 7 days of server drop — after 7 days, backups are most likely deleted
- Use nslookup to verify DNS availability before DeferredDropped recovery
- Verify server state in `Sterling Servers and Databases.xts` view
- For restore script troubleshooting, see TSG BRDB0019 section "Troubleshooting the restore script"
- Source TSG: BRDB0019 (ADO Wiki: `/BackupRestore/BRDB0019 Dropped Server Restore` in TSG-SQL-DB-DataIntegration)
