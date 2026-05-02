---
name: error-40613-state-81
description: Diagnoses login error 40613 with state 81 on PaaSv2 clusters caused by IPv6 DIP prefix mismatch. The error occurs when the PaaSv2VnetIPv6Prefix configured in XTS does not match the actual IPv6 prefix on VM NICs, causing VNet Service Endpoint packets to be incorrectly classified during login. Mitigation involves running a CAB to override the config prefix. This is a platform-side infrastructure issue, not a customer configuration problem.
---

# Error 40613 State 81 - IPv6 Prefix Mismatch on PaaSv2 Clusters

## Overview

Login failures with error 40613 state 81 on PaaSv2 clusters when clients connect using VNet Service Endpoints. The root cause is a **mismatch between the IPv6 DIP prefix** expected for the cloud/region (configured in XTS as `PaaSv2VnetIPv6Prefix`) and the actual IPv6 DIP prefix on the VM NICs used during cluster buildout. This causes packets to be incorrectly classified during login.

Clients experience errors even with proper source prefix (e.g., `fde4:8dba`) in packets.

> **Note**: If the triage does not match this problem (i.e., no IPv6 prefix mismatch is found), please be advised there is a known issue for Azure SQL Data Warehouse in national clouds, which could be a dw service side issue. Refer to Incident [31000000555918](https://portal.microsofticm.com/imp/v5/incidents/details/31000000555918/summary) for the latest development.

Source: [Error 40613 State 81 on PaaSv2 Clusters TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/networking/vnet/error-40613-state-81-error-on-paasv2-clusters)

## Required Information

- **LogicalServerName**: The logical server name
- **LogicalDatabaseName**: The logical database name
- **StartTime** and **EndTime**: Time window of the issue (UTC)
- **kusto-cluster-uri** and **kusto-database**: From the "execute-kusto-query" skill
- **Affected tenant ring / cluster name**: To check XTS configuration

## Investigation Workflow

### 1. Confirm Error Pattern

Run query CONN81-100 from [references/queries.md](references/queries.md) to:
- Confirm error 40613 state 81 is occurring on a PaaSv2 cluster
- Identify which tenant ring(s) and DB nodes are affected
- Assess volume and number of distinct clients impacted

### 2. Verify Error Timeline

Run query CONN81-200 to:
- Understand when errors started
- Determine if errors are ongoing or resolved
- A constant error rate suggests a config mismatch (vs. intermittent for other causes)

### 3. Check IPv6 Prefix in XTS

Use XTS view `jimoha\configapptypeeffectivesettings.xts` to:
- Identify the effective `PaaSv2VnetIPv6Prefix` value for the affected tenant ring
- Record this value (e.g., `2001:4899`)

### 4. Check Actual IPv6 Prefix on VM NICs

**Method A: Azure Portal**
- Get JIT access to the portal for the cluster's subscription ID (from Service Fabric Explorer)
- Check the IPv6 Address configured on the NIC
- Extract the prefix (e.g., `2001:4899:6100:6::d` → prefix `2001:4899`)

**Method B: Geneva Actions**
- Check the actual IPv6 VNET address under the respective environment
- Example (Mooncake): expected `2404:7940`, actual `2001:4899:6800:6::/64`

### 5. Compare Prefixes

- 🚩 **If XTS prefix ≠ NIC prefix** → this is the root cause. Proceed to mitigation.
- If XTS prefix = NIC prefix → this TSG does not apply. Please be advised there is a known issue for Azure SQL Data Warehouse in national clouds, which could be a dw service side issue. Refer to Incident [31000000555918](https://portal.microsofticm.com/imp/v5/incidents/details/31000000555918/summary) for the latest development.

```
From: Shravan Vuggrala <shravan.vuggrala@microsoft.com> 
Sent: Wednesday, March 11, 2026 4:39 AM
To: Ben Oberhaus <Benjamin.Oberhaus@microsoft.com>; Peter Gvozdjak <pgvozdjak@microsoft.com>; Rajesh Prajapati <raprajapati@microsoft.com>
Cc: Jitesh Mohan <jimoha@microsoft.com>; Manish Gajjaria <mgajjaria@microsoft.com>; Liang Hu <Liang.Hu@microsoft.com>; SQL Connectivity Team & SREs <sqlconnectivityext@microsoft.com>
Subject: Re: MC DW Dedicated Gen2 Paasv2 ring vnet/ipv6 issues: VnetIpv6ParsingPrefixFromDest
 
From initial discussions we thought to add fDestIpIsFromVnetSvcEndpointsAdapter flag in OriginalNetworkAddressInfoConnectionProvider.cs.
But this required change in SqlClient code as well as to accommodate the new flag.
So, after reviewing again the value, IsVnetAddress, should get set here MPDW VnetAddress Setting. 
If this value is set then DwEngine connection to ShellDB should carry the bit in CTAIP and should ignore the check again in SQL in ParseIPv6Address.
I feel the value of IsVnetAddress from conn is not updated properly during login path, causing this issue. 
We need to test with redirect login tests to identify the path to fix, looks that's where we are now.
```

### 6. Apply Mitigation (IPv6 Prefix Config Override)

See [references/principles.md](references/principles.md) for detailed mitigation steps.

**Procedural (non-urgent):**
- Duplicate the CAB template with large slice bake setting (will be slow)

**Urgent (SEV 2 or higher):**
- Duplicate the CAB template with 0 bake time

**Steps:**
1. Configure the CAB with the correct cluster and IPv6 prefix (set to the actual NIC value)
2. Choose Add or Remove override depending on the scenario
3. Submit and get CAB approved
4. Wait for CAB execution to complete
5. Verify effective configuration is applied
6. 🚩 **If Gateway application**: restart Gateway apps on all nodes (Kill Gateway)
7. Verify using MonLogin that logins are successful (run query CONN81-300)
8. Email `paasv2connectivity@microsoft.com` regarding the mitigation

## Execute Queries

Execute queries from [references/queries.md](references/queries.md):

**Step 1: Confirm Error**
- CONN81-100 (Error Volume and Scope)

**Step 2: Timeline**
- CONN81-200 (Error Over Time)

**Step 3: Post-Mitigation Verification**
- CONN81-300 (Post-Mitigation Login Verification)

## Escalation

- **Before escalation**: Always attempt triage and mitigation first
- 🚩 **Urgent / high customer impact**: Request assistance in IcM to `Azure SQL DB/Expert: Gateway escalations only from people in the Gateway queue`
- **Non-urgent / minimal impact**: Email `sqldb_connectivity@microsoft.com` and reach out via the Connectivity Teams channel

## Reference

See [references/knowledge.md](references/knowledge.md) for detailed definitions and concepts.
See [references/principles.md](references/principles.md) for debug principles and mitigation procedures.

## Related Documentation

- [VNet service endpoints and rules for Azure SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/vnet-service-endpoint-rule-overview?view=azuresql)
- [Azure virtual network service endpoints](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-service-endpoints-overview)
