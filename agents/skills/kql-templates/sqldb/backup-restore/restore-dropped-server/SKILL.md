---
name: restore-dropped-server
description: Restore Azure SQL Database logical server and databases after accidental server deletion (DevOps only). Validates server is in DeferredDropped state, verifies DNS availability, and provides recovery procedures. Required inputs from calling agent - kusto-cluster-uri, kusto-database, and subscription/server information.
---

# Restore Dropped Azure SQL Database Logical Server (DevOps Only)

Restore Azure SQL Database logical servers and databases after accidental server deletion. This skill is for DevOps engineers handling Customer Reported Incidents (CRI) when customers accidentally drop their servers.

## Background

When customers accidentally drop their Azure SQL Database logical server (or the resource group containing the server), all databases under that server are also dropped. Databases can be recovered within 7 days if:
- Server is in DeferredDropped state with databases in Tombstoned state
- Backups have not yet been cleaned up (compliance/COGS requirement after 7 days)
- DNS name is available OR restore to new server using PITR is possible

**Important**: This guide is for **DevOps engineers only** responding to customer support escalations. CSS engineers should use the ACIS self-service path (TSG BRDB0019.1) to recover servers in DeferredDropped state directly.

## Required Information

This skill requires the following inputs (should be obtained by the calling agent):

### From User or CSS:
- **Subscription ID** of the customer
- **Logical Server Name** (server that was dropped)
- **Dropped Date** (when server was deleted)
- **Region** where server existed prior to drop (optional)

### From execute-kusto-query skill (if region known):
- **kusto-cluster-uri**
- **kusto-database**
- **region**

### Business Justification Validation (required):
- CRI filed within **7 days of drop** (strict requirement)
- Production environment with strong business justification
- Requestor is subscription admin or verified by subscription admin via email
- Customer has created empty databases with identical names (for PITR method)

**Critical**: After 7 days, dropped servers are cleaned up regardless of retention settings.

## Workflow

### 1. Discover Original Region Name (If Not Provided)

If region not provided, use telemetry to find it:

```
Tool: mcp_azure_mcp_kusto
Parameters:
- command: "kusto_query"
- intent: "Find original region for dropped server"
- parameters: {
    "cluster-uri": "https://sqladhoc.kusto.windows.net:443",
    "database": "sqlazure1",
    "query": "MonManagement | where TIMESTAMP >= ago(30d) | where operation_parameters contains '{SubscriptionId}' | where operation_parameters contains '{LogicalServerName}' | where operation_type contains 'Server' | project TIMESTAMP, ClusterName, operation_type, operation_parameters | order by TIMESTAMP desc | take 10"
}
```

**Determine region from `ClusterName` in results**.

### 2. Verify if Server Can Be Restored from DeferredDropped State

#### Step 2.1: Verify DNS Availability

Check if server DNS name is available:

```
Tool: run_in_terminal
Parameters:
- command: "nslookup {LogicalServerName}.database.windows.net"
- explanation: "Checking if DNS name is available for server recovery"
- isBackground: false
```

**Evaluation**:
- **"Non-existent domain"**: DNS is available ✅
- **Returns IP address/result**: DNS is NOT available ❌ (customer or different customer created server with same name)

#### Step 2.2: Verify Server State

Open XTS, select the cluster from Step 1, and open the **Sterling Servers and Databases.xts** view.

Verify the server is in **DeferredDropped** state and databases are in **Tombstoned** state.

**Analysis**:
- **If server found with state = DeferredDropped**: Server can potentially be recovered ✅
- **If no results or state != DeferredDropped**: Server cannot be directly recovered ❌

#### Step 2.3: Verify Expected Databases in DeferredDropped Server

In the same **Sterling Servers and Databases.xts** view, list all databases under the dropped server.

**If expected databases are NOT listed**: 
> 🚩 Server with same name was likely created and dropped again after original drop. Cannot use DeferredDropped recovery method.

### 3. Determine Recovery Method

Based on Step 2 results:

#### Method A: Recover from DeferredDropped (Preferred)

**Requirements**:
- ✅ DNS name is available
- ✅ Server is in DeferredDropped state
- ✅ Expected databases present in Tombstoned state

**Procedure**:

🚩 **CRITICAL WARNING**: Ensure DNS name is available. Failure to verify will cause server to force drop and result in hours of additional recovery work.

Execute Recovery CAS Command:
```
Get-JitAccess -WorkitemSource IcM -WorkItemId {ICM_ID} 
    -Justification "Recover dropped server for customer"

Recover-LogicalServer -SubscriptionId {SubscriptionId} -LogicalServerName {LogicalServerName}
```

**Monitor Recovery**:
- Verify server state changes from DeferredDropped to Ready in XTS
- **Note**: This recovers the server with **master only**. After recovery, the customer must self-service restore individual databases.

**Post-Recovery**:
> ✅ **Server Recovered Successfully**
> - Server: {LogicalServerName}
> - State: Ready
> 
> **Next Steps**:
> 1. Inform customer that the server is recovered with master database
> 2. Customer must self-service restore each database using Azure Portal or PowerShell
> 3. Communicate recovery completion to customer

#### Method B: Recovery to New Server Using PITR

**Requirements**:
- ❌ DNS name is NOT available (customer created new server with same name), OR
- ❌ Server not in DeferredDropped state, OR
- ✅ Customer created empty databases with identical names to dropped databases

**Procedure**:

1. **Customer Prerequisites**:
   - Customer must create new server with same name (if DNS available) or different name
   - Customer must create empty databases with **exact same names** as dropped databases

2. **Verify Backup Availability** using query **RSV200** from [references/queries.md](references/queries.md):

RSV200 generates `List-XStoreBlobs` commands to verify backup files exist in storage. If the command returns "StatusCode: NotFound", the backup does not exist and PITR is not possible.

3. **Generate Restore Scripts** using query **RSV300** from [references/queries.md](references/queries.md):

RSV300 generates `Restore-DatabaseFromDroppedServer.ps1` commands for each database. Run these from DS Console (`Scripts\BackupRestore` directory).

**Setup DS Console**:
```
Select-SqlAzureEnvironment Prod
cd Scripts\BackupRestore
```

**Execute the generated restore script for each database**.

**Optional parameters**:
- `-SkipOldDbIdVerification $true`: Skip logical DB ID validation of old database
- `-BlobEndpointSuffix {suffix}`: **Required for non-public clouds** (use RSV400 to find suffix)

**For non-public clouds**: Use query **RSV400** to find the correct BlobEndpointSuffix, then append `-BlobEndpointSuffix {suffix}` to the restore command.

**Script Troubleshooting**:
- **"The specified module 'Azure' was not loaded"**: Install latest Azure PowerShell on SAW machine
- **"Perform-KustoQuery is not recognized"**: Run `Import-Module C:\Users\{YourAlias}\SqlAzureConsole\Modules\SterlingKusto\SterlingKusto.psd1` then retry
- **"Dropped and new servers belong to different subscriptions" (empty subscription)**: Known bug with row count parsing — download updated script from DS Console
- **Script hanging/failing on blob copy**: Cancel and retry. Copy progress from previous iterations will remain
- **"No drop details in Kusto for dropped server"**: Server dropped >7 days ago. Try LogicalDatabaseId from Sterling DataWarehouse
- **Error with `Get-LogicalServer`**: Start new DS Console window (not via XTS), manually select environment and cluster, run `Get-LogicalServer {ServerName}`, then retry
- **Restore request fails**: Manually send restore via `New-RestoreRequest` using parameters from `sterling\sterlingrestorerequests.xts`

### 4. Handle TDE/CMK Scenarios

If databases used customer-managed keys (CMK):
- Customer must grant key vault permissions to new server identity
- For service-managed TDE certificate issues, use `Add-FindAndAddTdeSecretToExternalSecrets` CAS command

### 5. Verify Recovery Success

Verify recovery in the **Sterling Servers and Databases.xts** view:

**Success Criteria**:
- Server state is "Ready"
- For Method A: Master database is accessible; customer self-service restores individual databases
- For Method B: Restored databases show state = "Ready"

## Summary Output Format

After completing recovery, provide summary:

> ## 🔍 **Dropped Server Recovery Summary**
> 
> **Server Information:**
> - Logical Server: {LogicalServerName}
> - Subscription ID: {SubscriptionId}
> - Region: {Region}
> - Dropped Date: {DroppedDate}
> 
> **Recovery Method:**
> - Method Used: {DeferredDropped Recovery / PITR to New Server}
> - DNS Available: {Yes/No}
> 
> **Recovery Results:**
> - Server State: {state}
> - Databases Recovered: {database_count}
> - Recovery Time: {duration}
> 
> **Status:**
> - ✅ Success / ❌ Failed
> - {Any issues or notes}
> 
> **Customer Communication:**
> {Template message for customer notification}

## Critical Notes

⚠️ **7-Day Limit**: Server must be recovered within 7 days of drop. After 7 days, backups are deleted per compliance requirements.

⚠️ **DNS Verification**: Always verify DNS availability before attempting DeferredDropped recovery.

⚠️ **Business Justification**: Ensure proper CRI validation and subscription admin approval before proceeding.

⚠️ **PITR Prerequisites**: Customer must create target databases before PITR can be executed.

## Related References

- [references/queries.md](references/queries.md) — Kusto query definitions (RSV100–RSV500)
- [references/knowledge.md](references/knowledge.md) — Recovery concepts and methods
- [references/principles.md](references/principles.md) — Recovery method decision tree and safety checks
- [references/report.md](references/report.md) — Output format templates
- [references/prep/sources.md](references/prep/sources.md) — TSG source URLs

## Related Skills

- **restore-failure**: For troubleshooting PITR failures during recovery process

## Related TSGs

- **BRDB0019.1**: Dropped Server Restore with ACIS (CSS only) — self-service path for CSS engineers with SAW access
- **BRDB0074**: Restore fails with server certificate — for TDE cert troubleshooting
