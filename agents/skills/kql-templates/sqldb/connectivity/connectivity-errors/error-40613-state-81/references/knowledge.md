!!!AI Generated.  To be verified!!!

# Terms and Concepts

## Core Concepts

### Error 40613 State 81
Error 40613 with state 81 indicates a login failure on PaaSv2 clusters when a client connects using VNet Service Endpoints. The root cause is a **mismatch between the IPv6 DIP prefix** expected for the cloud/region and the actual IPv6 DIP prefix used during cluster buildout. This causes packets to be incorrectly classified during login, even when the client sends proper source prefix (e.g., `fde4:8dba`) in the packets.

This is a **platform-side infrastructure issue**, not a customer configuration problem.

### PaaSv2 Clusters
PaaSv2 is the newer Azure SQL Database cluster architecture. Error 40613 state 81 with IPv6 prefix mismatch is specific to PaaSv2 clusters where VNet service endpoint packet classification occurs during the login process.

### IPv6 DIP Prefix
The IPv6 DIP prefix is an address prefix assigned to the virtual machine NICs in a cluster. Each cloud/region has an expected IPv6 prefix. Examples:
- Public Azure regions may use prefixes like `2001:4899`
- Mooncake (China) uses prefix `2404:7940`

The prefix is configured in XTS via the `PaaSv2VnetIPv6Prefix` setting.

### PaaSv2VnetIPv6Prefix
An XTS configuration setting that specifies the expected IPv6 prefix for VNet-based connections on a tenant ring. When this value does not match the actual IPv6 prefix on the VM NICs, error 40613 state 81 occurs.

## Root Cause

The issue is a mismatch between:
1. **Configured prefix in XTS**: The `PaaSv2VnetIPv6Prefix` value set for the tenant ring
2. **Actual IPv6 DIP prefix on VM NICs**: The IPv6 address prefix physically configured on the network interfaces of the VMs in the cluster

This mismatch causes the gateway to incorrectly classify incoming VNet Service Endpoint packets, resulting in login failures.

## Key Tools and References

| Tool | Purpose |
|------|----------|
| XTS (`configapptypeeffectivesettings.xts`) | View the configured `PaaSv2VnetIPv6Prefix` for a tenant ring |
| Azure Portal (VM NIC) | Check the actual IPv6 address prefix on the VM NICs |
| Geneva Actions | Alternative way to check actual IPv6 VNET address on VMs |
| Service Fabric Explorer | Fetch the subscription ID for the cluster |
| EzCab | Run config override CAB to fix the prefix mismatch |

## Related Errors

- **Error 40613 State 81 (general)**: VNet Service Endpoints login failures due to customer-side misconfigurations (separate TSG)
- **Error 40914**: Client is in a subnet with VNet service endpoints, but the server has no VNet rule granting the subnet access
- **Error 40532 State 150**: VNet firewall rule rejected the login

## Related Documentation
- [VNet service endpoints and rules for Azure SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/vnet-service-endpoint-rule-overview?view=azuresql)
- [Azure virtual network service endpoints](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-service-endpoints-overview)
