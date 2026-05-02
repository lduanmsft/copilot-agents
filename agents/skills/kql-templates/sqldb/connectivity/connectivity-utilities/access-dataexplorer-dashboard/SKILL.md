---
name: access-dataexplorer-dashboard
description: Generates a pre-filled Azure Data Explorer dashboard link for the SQL Connectivity Livesite Dashboard. Constructs the URL with region, cluster, node, and time parameters derived from the investigation context, enabling direct navigation to specific dashboard pages (Gateway Health, XDBHost, VM Node).
---

# Data Explorer Dashboard Link Generator

Generates a pre-filled link to the SQL Connectivity Livesite Dashboard in Azure Data Explorer. Parameters are populated from the investigation context so the DRI can immediately view relevant metrics without manual configuration.

## When to Use

- When the investigation has identified a specific cluster, node, and time window
- When the DRI needs visual dashboard access for Gateway, XDBHost, or VM Node metrics
- When `aka.ms/sqlconnlsi` is referenced and a pre-filled link adds value

## Dashboard ID

`ff00559d-35c6-41c1-93eb-43b67381a3cf`

Base URL: `https://dataexplorer.azure.com/dashboards/ff00559d-35c6-41c1-93eb-43b67381a3cf`

## Required Input

| Field | Source | Example |
|-------|--------|---------|
| StartTime | ICM / user (UTC) | `2026-04-04 20:00:00` |
| EndTime | ICM / user (UTC) | `2026-04-04 23:00:00` |
| ClusterName | get-db-info FQDN | `tr6730.southeastasia1-a.worker.database.windows.net` |
| NodeName | ICM / triage | `_DB_59` |
| SqlInstances | Kusto query (optional) | `a151c2d79ec9` or `all` |
| PartitionIds | Kusto query (optional) | specific ID or `all` |
| servicefabric_id | Kusto query (optional) | specific ID or `all` |
| logicalServerName | ICM (optional) | `myserver` or `all` |

## Dashboard Pages

| Page | Fragment | Typical Use |
|------|----------|-------------|
| Gateway Health | `#5e91c7d7-e156-45bf-85bf-23332f6c490c` | Gateway login success rates, resource usage |
| XDBHost | `#90bdce43-0daf-4aec-ad80-f2cdb0b236ba` | XDBHost process metrics, per-instance view |
| VM Node | `#8214d7e9-7ff1-4313-930a-7bb0807b73fa` | VM-level CPU, memory, disk metrics |

Select the page matching the investigation type.

## URL Construction Rules

### 1. Time Format

Replace colons with dashes and wrap in ISO 8601 format:

```
2026-04-04 20:00:00 → 2026-04-04T20-00-00Z
```

### 2. RegionFqdn

Extract the second `.`-delimited segment of the cluster FQDN:

| ClusterName | RegionFqdn |
|-------------|------------|
| `tr6730.southeastasia1-a.worker.database.windows.net` | `southeastasia1-a` |
| `cr9.australiacentral2-a.control.database.windows.net` | `australiacentral2-a` |
| `tr43583.eastus2-a.worker.database.windows.net` | `eastus2-a` |

### 3. Value Prefix `v-`

Parameters that are dashboard variables use a `v-` prefix on their values. Time parameters and defaulted `all` values for certain fields do not.

| Parameter | Specific Value | Default Value |
|-----------|---------------|---------------|
| `p-RegionFqdn` | `v-{regionFqdn}` | — |
| `p-ClusterNameVar` | `v-{clusterFQDN}` | — |
| `p-NodeNameVar` | `v-{nodeName}` | — |
| `p-SqlInstances` | `v-{instancePrefix}` | `v-all` |
| `p-NodeRoleVar` | — | `all` |
| `p-PartitionIds` | specific ID | `all` |
| `p-servicefabric_id` | specific ID | `all` |
| `p-_logicalServerName` | `{serverName}` | `all` |
| `p-_startTime` | No prefix | — |
| `p-_endTime` | No prefix | — |

### 4. Assemble URL

```
https://dataexplorer.azure.com/dashboards/ff00559d-35c6-41c1-93eb-43b67381a3cf?{params}#{fragment}
```

Join parameters with `&`. Append the page fragment.

## Sample URLs

### Gateway Health

```
https://dataexplorer.azure.com/dashboards/ff00559d-35c6-41c1-93eb-43b67381a3cf?p-_startTime=2026-01-23T18-20-00Z&p-_endTime=2026-01-23T21-20-00Z&p-RegionFqdn=v-australiacentral2-a&p-ClusterNameVar=v-cr9.australiacentral2-a.control.database.windows.net&p-NodeRoleVar=all&p-NodeNameVar=v-_GW_1#5e91c7d7-e156-45bf-85bf-23332f6c490c
```

### XDBHost (Worker)

```
https://dataexplorer.azure.com/dashboards/ff00559d-35c6-41c1-93eb-43b67381a3cf?p-_startTime=2026-01-23T18-20-00Z&p-_endTime=2026-01-23T21-20-00Z&p-RegionFqdn=v-eastus2-a&p-ClusterNameVar=v-tr43583.eastus2-a.worker.database.windows.net&p-NodeRoleVar=all&p-NodeNameVar=v-_DB_51&p-SqlInstances=v-a151c2d79ec9&p-_logicalServerName=all#90bdce43-0daf-4aec-ad80-f2cdb0b236ba
```

### VM Node

```
https://dataexplorer.azure.com/dashboards/ff00559d-35c6-41c1-93eb-43b67381a3cf?p-_startTime=2026-01-26T00-00-00Z&p-_endTime=2026-01-27T23-59-59Z&p-RegionFqdn=v-switzerlandnorth1-a&p-ClusterNameVar=v-tr2594.switzerlandnorth1-a.worker.database.windows.net&p-NodeRoleVar=all&p-NodeNameVar=v-_DB_0&p-SqlInstances=all#8214d7e9-7ff1-4313-930a-7bb0807b73fa
```

## Step-by-Step Workflow

1. **Collect parameters** from calling skill context (StartTime, EndTime, ClusterName, NodeName, optional fields)
2. **Derive RegionFqdn** — split ClusterName by `.`, take segment at index 1
3. **Format timestamps** — replace `:` → `-`, format as `{date}T{time}Z`
4. **Select dashboard page** — pick the fragment matching the investigation type
5. **Apply `v-` prefix** to variable values per the rules table
6. **Assemble URL** — base URL + `?` + parameters joined by `&` + `#` + fragment
7. **Output the link** in the report for DRI use
