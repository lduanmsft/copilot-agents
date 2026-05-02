---
name: directory-quota-hit-limit
description: Determine if App work\data directory quota hit limit.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Directory Quota Hit Limit

## Skill Overview

This skill determines if the App work\data directory quota has hit its limit on Azure SQL nodes. It analyzes quota usage versus quota limits to detect when directories have exhausted their allocated space.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |



## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Caller Validation | Always |
| Task 2 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Caller Validation

This skill is intended to be invoked exclusively by [out-of-disk](../SKILL.md). If invoked by any other caller (e.g., directly by a user), terminate execution in this markdown file, display the exact message "Calling parent skill instead" and execute [out-of-disk](../SKILL.md) instead.

### Task 2: Execute the Kusto query below. If required variables (e.g., `{AppNamesOnly}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
MonRgLoad
| extend originalEventTimestamp = originalEventTimestampFrom
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| extend AppName = split(application_name, '/')[-1]
| where AppName in ({AppNamesOnly})
| where event =~ 'directory_quota_report_load'
| extend quota_limit_in_GB = quota_limit_in_bytes/1024.0/1024/1024, quota_usage_in_GB = quota_usage_in_bytes/1024.0/1024/1024
| summarize arg_max(quota_usage_in_GB, *) by NodeName
| extend QuotaLimitHit = iff(quota_usage_in_GB >= quota_limit_in_GB, 1, 0)
| summarize sum(QuotaLimitHit)
| extend DirectoryQuotaLimitHit = sum_QuotaLimitHit > 0
| project DirectoryQuotaLimitHit
```

#### Output

**Display Issue Status**

| Condition | Message |
|-----------|---------|
| `DirectoryQuotaLimitHit = 'Yes'` | 🚩 **Directory quota limit has been hit** - One or more nodes have reached their directory quota limit. This may cause application failures due to insufficient disk space. |
| `DirectoryQuotaLimitHit = 'No'` | ✅ **Directory quota limit has not been hit** - All nodes are within their allocated directory quota limits. |

