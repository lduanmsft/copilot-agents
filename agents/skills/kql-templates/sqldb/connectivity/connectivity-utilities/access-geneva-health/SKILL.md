---
name: access-geneva-health
description: Generates a Geneva Health Monitor link from ICM incident data. Reconstructs the full portal URL by parsing the CorrelationId and OccurringLocation fields from the incident, enabling direct navigation to the Health Hierarchy view (Region, Cluster, or Node level) in the Geneva portal.
---

# Geneva Health Monitor Link Generator

This skill generates a Geneva Health Monitor portal link from ICM incident data. The link opens the Health Hierarchy view for the exact resource (Region, Cluster, or Node) and monitor that triggered the alert.

## When to Use

- When the incident was created by a Geneva/MDM Health Hierarchy alert (AlertSource contains `MDM`)
- When the CorrelationId starts with `HH-` (Health Hierarchy prefix)
- When you need to navigate to the Geneva portal to inspect monitor state, health timeline, or topology

## Required ICM Fields

| ICM Field | Variable | Example |
|-----------|----------|---------|
| `correlationId` | Full correlation string | See level-specific examples below |
| `occuringLocation.datacenter` | Datacenter/region display name | `Southeast Asia` |
| `createdDate` | Alert timestamp (ISO 8601 UTC) | `2026-04-04T21:31:55.333Z` |

## CorrelationId Parsing

The CorrelationId for Health Hierarchy alerts varies by **hierarchy level**. Split the CorrelationId by `->` and count the segments to determine the level:

| Segment Count | Level | Structure |
|---------------|-------|-----------|
| 2 | **Region** | `HH-{TopologyType}/{Region}->{MonitorName}` |
| 3 | **Cluster** | `HH-{TopologyType}/{Region}->{FQDN}->{MonitorGUID}` |
| 4 | **Node** | `HH-{TopologyType}/{Region}->{FQDN}->{NodeName}->{MonitorGUID}` |

**From segment 1 (index 0), always extract:**
- `TopologyType`: Text between `HH-` and `/` → e.g., `SQLConnectivity-Region`, `SQLConnectivity-Cluster`, `SQLConnectivity-Node`
- `Region`: Text after `/` → e.g., `East US 2 EUAP`, `Southeast Asia`

### Region Level (2 segments)

| Segment | Index | Content | Example |
|---------|-------|---------|---------|
| 1 | 0 | `HH-{TopologyType}/{Region}` | `HH-SQLConnectivity-Region/East US 2 EUAP` |
| 2 | 1 | Monitor name | `SQLConnectivity-Region-ControlRings-Clusters-Unhealthy` |

### Cluster Level (3 segments)

| Segment | Index | Content | Example |
|---------|-------|---------|---------|
| 1 | 0 | `HH-{TopologyType}/{Region}` | `HH-SQLConnectivity-Cluster/East US 2 EUAP` |
| 2 | 1 | FQDN (instance) | `cr22.useuapeast2-a.control.database.windows.net` |
| 3 | 2 | Monitor GUID | `3bce540c-a602-42d2-b6e5-b25d2da1a683` |

### Node Level (4 segments)

| Segment | Index | Content | Example |
|---------|-------|---------|---------|
| 1 | 0 | `HH-{TopologyType}/{Region}` | `HH-SQLConnectivity-Node/Southeast Asia` |
| 2 | 1 | FQDN (instance) | `tr6730.southeastasia1-a.worker.database.windows.net` |
| 3 | 2 | Node name | `_DB_59` |
| 4 | 3 | Monitor GUID | `ec8bf248-21e3-4115-815b-31227d28a02b` |

## Link Construction Rules

### 1. Tenant

```
tenant = "AzureDbProduction" + lowercase(datacenter with spaces removed)
```

| Datacenter | Tenant |
|------------|--------|
| `Southeast Asia` | `AzureDbProductionsoutheastasia` |
| `East US 2 EUAP` | `AzureDbProductioneastus2euap` |
| `West Europe` | `AzureDbProductionwesteurope` |

### 2. Topology Type

**Rule**: Insert `-HealthResource` before the last `-` delimited segment of the TopologyType:

| CorrelationId TopologyType | Geneva Type |
|----------------------------|-------------|
| `SQLConnectivity-Region` | `SQLConnectivity-HealthResource-Region` |
| `SQLConnectivity-Cluster` | `SQLConnectivity-HealthResource-Cluster` |
| `SQLConnectivity-Node` | `SQLConnectivity-HealthResource-Node` |

### 3. Resource Name (level-dependent)

| Level | Name Formula | Example |
|-------|-------------|---------|
| **Region** | `{Region}` | `East US 2 EUAP` |
| **Cluster** | `{FQDN}_{Region}` | `cr22.useuapeast2-a.control.database.windows.net_East US 2 EUAP` |
| **Node** | `{FQDN}_{NodeName}_{Region}` | `tr6730.southeastasia1-a.worker.database.windows.net__DB_59_Southeast Asia` |

Where `_` is the separator (single underscore) and `Region` is the display name with spaces preserved.

> **Note**: If NodeName starts with `_`, the result will have a double underscore (`__`) between FQDN and NodeName. This is expected.

### 4. Monitor (last segment of CorrelationId)

The monitor value is always the **last segment** of the CorrelationId (after the final `->`). It can be either a GUID or a monitor name string at any level.

| Level | Monitor Example |
|-------|-----------------|
| **Region** | `SQLConnectivity-Region-ControlRings-Clusters-Unhealthy` (name) |
| **Cluster** | `3bce540c-a602-42d2-b6e5-b25d2da1a683` (GUID) or `SQLConnectivity-Cluster-ControRing-Nodes-Unhealthy` (name) |
| **Node** | `ec8bf248-21e3-4115-815b-31227d28a02b` (GUID) |

### 5. Assemble the JSON payload

```json
{
  "health3": {
    "tenant": "{tenant}",
    "checkedNodes": [{
      "dataSourceNode": {
        "id": {
          "topologyName": "{tenant}",
          "type": "{type}",
          "name": "{name}"
        },
        "monitor": "{monitor}",
        "time": "{createdDate}"
      }
    }]
  }
}
```

### 6. Generate the URL

```
https://portal.microsoftgeneva.com/?layout={URL_ENCODED_JSON}
```

URL-encode the JSON payload using `%22` for `"`, `%20` for spaces, `%7B`/`%7D` for `{`/`}`, etc.

## Step-by-Step Workflow

1. **Validate** that the incident has a CorrelationId starting with `HH-`
2. **Parse** the CorrelationId into segments (split by `->`)
3. **Determine level** from segment count: 2 = Region, 3 = Cluster, 4 = Node
4. **Extract** TopologyType, Region from segment 0; remaining fields based on level
5. **Build** tenant from `occuringLocation.datacenter`
6. **Build** type by inserting `-HealthResource` into TopologyType
7. **Build** name using the level-specific formula (see Section 3 above)
8. **Extract** monitor from the last segment of the CorrelationId
9. **Assemble** the JSON payload
10. **URL-encode** and prepend `https://portal.microsoftgeneva.com/?layout=`
11. **Output** the link and optionally open it in Edge

## Output

Provide:
1. The detected hierarchy level (Region / Cluster / Node)
2. The generated Geneva Health link
3. The decoded JSON for readability
4. Optionally, a PowerShell command to open the link:

```powershell
$GenevaHealthUrl = "<generated_url>"; Start-Process "msedge.exe" $GenevaHealthUrl
```

## Examples

### Example 1: Node Level

**ICM Input:**
- `correlationId`: `HH-SQLConnectivity-Node/Southeast Asia->tr6730.southeastasia1-a.worker.database.windows.net->_DB_59->ec8bf248-21e3-4115-815b-31227d28a02b`
- `occuringLocation.datacenter`: `Southeast Asia`
- `createdDate`: `2026-04-04T21:31:55.333Z`

**Parsed (4 segments → Node level):**
- TopologyType: `SQLConnectivity-Node`
- Region: `Southeast Asia`
- FQDN: `tr6730.southeastasia1-a.worker.database.windows.net`
- NodeName: `_DB_59`
- Monitor: `ec8bf248-21e3-4115-815b-31227d28a02b`

**Result:**
- type: `SQLConnectivity-HealthResource-Node`
- name: `tr6730.southeastasia1-a.worker.database.windows.net__DB_59_Southeast Asia`

### Example 2: Cluster Level

**ICM Input:**
- `correlationId`: `HH-SQLConnectivity-Cluster/East US 2 EUAP->cr22.useuapeast2-a.control.database.windows.net->3bce540c-a602-42d2-b6e5-b25d2da1a683`
- `occuringLocation.datacenter`: `East US 2 EUAP`
- `createdDate`: `2026-03-31T22:46:44.623Z`

**Parsed (3 segments → Cluster level):**
- TopologyType: `SQLConnectivity-Cluster`
- Region: `East US 2 EUAP`
- FQDN: `cr22.useuapeast2-a.control.database.windows.net`
- Monitor: `3bce540c-a602-42d2-b6e5-b25d2da1a683`

**Result:**
- type: `SQLConnectivity-HealthResource-Cluster`
- name: `cr22.useuapeast2-a.control.database.windows.net_East US 2 EUAP`

### Example 3: Region Level

**ICM Input:**
- `correlationId`: `HH-SQLConnectivity-Region/East US 2 EUAP->SQLConnectivity-Region-ControlRings-Clusters-Unhealthy`
- `occuringLocation.datacenter`: `East US 2 EUAP`
- `createdDate`: `2026-03-31T22:55:03.917Z`

**Parsed (2 segments → Region level):**
- TopologyType: `SQLConnectivity-Region`
- Region: `East US 2 EUAP`
- Monitor: `SQLConnectivity-Region-ControlRings-Clusters-Unhealthy`

**Result:**
- type: `SQLConnectivity-HealthResource-Region`
- name: `East US 2 EUAP`

**Constructed:**
- tenant: `AzureDbProductioneastus2euap`
- type: `SQLConnectivity-HealthResource-Region`
- name: `East US 2 EUAP`

**Generated Link:**
```
https://portal.microsoftgeneva.com/?layout={%22health3%22:{%22tenant%22:%22AzureDbProductioneastus2euap%22,%22checkedNodes%22:[{%22dataSourceNode%22:{%22id%22:{%22topologyName%22:%22AzureDbProductioneastus2euap%22,%22type%22:%22SQLConnectivity-HealthResource-Region%22,%22name%22:%22East%20US%202%20EUAP%22},%22monitor%22:%22SQLConnectivity-Region-ControlRings-Clusters-Unhealthy%22,%22time%22:%222026-03-31T22:55:03.917Z%22}}]}}
```

## Limitations

- Only works for incidents created by Geneva/MDM Health Hierarchy alerts (`HH-` prefix in CorrelationId)
- The tenant naming convention (`AzureDbProduction` + region) must be validated if new regions are added
- The `-HealthResource` insertion rule is derived from the `SQLConnectivity-Node` type; other topology types should be verified before adding
