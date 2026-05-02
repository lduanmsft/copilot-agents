!!!AI Generated.  To be verified!!!

# Debug Principles for Error 40613 State 81 (PaaSv2 IPv6 Prefix Mismatch)

## Triage Principles

1. **Confirm this is the PaaSv2 IPv6 prefix mismatch variant**: This TSG covers a specific platform-side issue. If the triage does not match (i.e., the error is due to customer VNet rule misconfiguration rather than IPv6 prefix mismatch), use the general TSG: "Error 40613 State 81 - Vnet Service Endpoints login failures".

2. **Confirm the error pattern**: Verify that errors are error 40613 with state 81 on a PaaSv2 cluster.
   - Clients experience errors even with proper source prefix `fde4:8dba` in packets
   - 🚩 If the cluster is NOT PaaSv2, this TSG does not apply

3. **This is a platform-side infrastructure issue**: The root cause is a mismatch between the IPv6 DIP prefix configured in XTS (`PaaSv2VnetIPv6Prefix`) and the actual IPv6 prefix on the VM NICs. This is NOT a customer configuration problem.

## Diagnosis Steps

### Step 1: Check the configured prefix in XTS
- Use the XTS view `jimoha\configapptypeeffectivesettings.xts`
- Identify the effective `PaaSv2VnetIPv6Prefix` value for the affected tenant ring
- Example: tr801 has value `2001:4899` for `PaaSv2VnetIPv6Prefix`

### Step 2: Check the actual IPv6 DIP prefix on VM NICs
Two methods:

**Method A: Azure Portal**
- Get JIT access to the portal for the cluster's subscription ID
- Subscription ID can be fetched from Service Fabric Explorer
- Check the IPv6 Address prefix configured on the NIC
- Example: NIC has IPv6 Address `2001:4899:6100:6::d` → actual prefix is `2001:4899`

**Method B: Geneva Actions**
- Perform the check under the respective environment
- Example (Mooncake): expected prefix `2404:7940`, actual configured IPv6 subnet `2001:4899:6800:6::/64`

### Step 3: Compare prefixes
- Compare the XTS configured value with the actual prefix from portal/Geneva
- 🚩 **If there is a mismatch** → proceed with the IPv6 prefix config override mitigation
- If they match → this TSG does not apply; use the general VNet Service Endpoints login failures TSG

## Mitigation: IPv6 Prefix Config Override

### Procedural (non-urgent) — use CAB with large slice bake:
- Duplicate the CAB template (large slice bake setting, will be SLOW)
- Configure with the correct cluster and IPv6 prefix

### Urgent (SEV 2 or higher) — use CAB with 0 bake time:
- Duplicate the CAB template with bake time set to 0
- Configure with the correct cluster and IPv6 prefix

### CAB Configuration
- Set the prefix to the value found on the portal/Geneva (the actual NIC prefix)
- Example: if XTS has `2470:489a` but portal NIC shows `2001:4899`, configure the CAB override to `2001:4899`
- Choose Add or Remove override depending on the scenario (sometimes removing an incorrect override is needed)

### Post-Mitigation
1. Submit CAB and get it approved
2. Wait for CAB to complete execution
3. Verify the effective configuration is applied to the cluster
4. 🚩 **If the override is on the Gateway application**: restart Gateway apps on all nodes for the configuration to take effect (use Kill Gateway procedure)
5. Verify using MonLogin that logins are now successful
6. Send email to `paasv2connectivity@microsoft.com` regarding the mitigation

## Escalation

- **Before escalation**: Always attempt triage and mitigation first
- 🚩 **Urgent / high customer impact**: Request assistance in IcM to the Gateway expert queue: `Azure SQL DB/Expert: Gateway escalations only from people in the Gateway queue`
- **Non-urgent / minimal impact**: Email `sqldb_connectivity@microsoft.com` and reach out via the Connectivity Teams channel
