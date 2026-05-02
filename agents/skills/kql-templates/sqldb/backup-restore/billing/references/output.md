# Billing Query Output Formats

This document describes the expected output formats for all billing-related Kusto queries defined in [queries.md](queries.md).

---

## Table of Contents

1. [PostReportedUsage2 Queries](#postreportedusage2-queries)
2. [MonManagement - Backup Billing Complete](#monmanagement---backup-billing-complete)
3. [Billing Pipeline Queries](#billing-pipeline-queries)
4. [UAE Usage Data](#uae-usage-data)
5. [P360 Consumption Units](#p360-consumption-units)

---

## PostReportedUsage2 Queries

### 1. Investigate Billed Quantity

**Query Name:** `PostReportedUsage2` - Billed Quantity Report

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `EventDateTime` | datetime | Timestamp of the usage event |
| `ResourceUri` | string | Full Azure resource URI |
| `ServerName` | string | Logical server name |
| `ElasticPoolName` | string | Elastic pool name (if applicable) |
| `DatabaseName` | string | Database name |
| `ElasticPoolId` | string | Elastic pool ID (if applicable) |
| `DatabaseId` | string | Database ID |
| `UsageResourceQuantity` | real | Hourly usage quantity in GB |
| `CurrentCumulativeBackupConsumptionInGB` | real | Cumulative backup consumption (UsageResourceQuantity × 744) |

---

### 2. Daily Aggregated Consumption Report

**Query Name:** `PostReportedUsage2` - Daily Aggregated Consumption

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `Date` | datetime | Date (binned to 1 day) |
| `ServerName` | string | Logical server name |
| `DatabaseName` | string | Database name |
| `ElasticPoolName` | string | Elastic pool name (if applicable) |
| `RestorableDroppedDB` | string | Restorable dropped database identifier |
| `NumberOfHourlyRecords` | long | Count of hourly records in this day |
| `BackupConsumptionInGB` | real | Total backup consumption for the day (rounded to 4 decimals) |

---

## MonManagement - Backup Billing Complete

### 3. Get Insight into Charges (By Database ID)

**Query Name:** `MonManagement` - Detailed Billing Insights

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `BillingCalculationTimestamp` | datetime | When billing calculation occurred |
| `ServerName` | string | Logical server name |
| `DatabaseName` | string | Logical database name |
| `FullBackupCumulativeSizeMB` | real | Cumulative size of full backups (MB) |
| `DiffBackupCumulativeSizeMB` | real | Cumulative size of differential backups (MB) |
| `LogBackupCumulativeSizeMB` | real | Cumulative size of log backups (MB) |
| `CumulativeBackupStorageMB` | real | Total cumulative backup storage (MB) |
| `DatabaseMaxSizeMB` | real | Maximum database size (MB) |
| `BackupRetentionDays` | long | Backup retention period in days |


**Calculated Fields (in original query):**
- `full_ratio` = FullBackupCumulativeSizeMB / CumulativeBackupStorageMB
- `diff_ratio` = DiffBackupCumulativeSizeMB / CumulativeBackupStorageMB
- `log_ratio` = LogBackupCumulativeSizeMB / CumulativeBackupStorageMB

**Use Case:** Detailed breakdown of backup types and their contribution to total backup storage costs
---

### 4. Alternative Query by Server Name

**Query Name:** `MonManagement` - All Databases on Server

**Additional Details:**
- Groups all databases on the specified server
- Includes physical database size on disk
- Correlated with MonDmIoVirtualFileStats for accurate physical sizing

**Use Case:** Server-wide billing analysis, compare backup costs across databases

---

### 5. Query All Databases on a Server (Summary)

**Query Name:** `MonManagement` - Server Database Billing Summary

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `logical_LogicalDatabaseName` | string | Database name |
| `billingCalculationTimestamp` | datetime | Billing calculation timestamp |
| `full_backup_cumulative_size` | real | Cumulative full backup size |
| `diff_backup_cumulative_size` | real | Cumulative differential backup size |
| `log_backup_cumulative_size` | real | Cumulative log backup size |
| `backup_storage_size` | string | Total backup storage size |

**Use Case:** Quick overview of all databases on a server, identify databases with high backup storage

---

## Billing Pipeline Queries

### 6. ScopePostReportedUsage - Sent to PAV2

**Query Name:** `ScopePostReportedUsage` - Actual Sent Billing Data

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `SubscriptionId` | string | Customer subscription ID |
| `BillingProductType` | string | Product type (contains "BackupStorage") |
| `BillingProductName` | string | Full product name |
| `ResourceUri` | string | Azure resource URI |
| `Quantity` | real | Billed quantity |
| `UsageDateTime` | datetime | Usage timestamp |
| `Location` | string | Azure region |

**Use Case:** Final verification of what was billed to customer, compare with actual invoice

**Important:** This is the authoritative source for actual billed amounts sent to Microsoft commerce.

---

### 7. MonBillingPitrBackupSize - DMV Collector Data

**Query Name:** `MonBillingPitrBackupSize` - Source Backup Size Data

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `TIMESTAMP` | datetime | Collection timestamp |
| `PreciseTimeStamp` | datetime | Precise collection time |
| `database_id` | string | Logical database ID |
| `backup_storage_size_mb` | real | Backup storage size in MB |
| `billing_period_start` | datetime | Start of billing period |
| `billing_period_end` | datetime | End of billing period |
| `backup_type` | string | Type of backup (RA-GRS, LRS, etc.) |

**Use Case:** Trace backup size data from DMV collector into billing pipeline, diagnose billing discrepancies

---

## UAE Usage Data

### 8. Query UAE Usage Data for Specific Resource

**Query Name:** `getUAEUsageData()` - Resource-Level Usage

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `resource_provider` | string | Resource provider (SqlAzure) |
| `ProductName` | string | Product name (e.g., "SQL Database Hyperscale - Storage") |
| `ProductType` | string | Product type category |
| `BillingMeterId` | string | Unique billing meter ID |
| `usage_date_time` | datetime | Usage event timestamp |
| `resourceUri` | string | Full resource URI |
| `location` | string | Azure region |
| `quantity` | real | Usage quantity |

**Use Case:** Hyperscale storage billing verification, track storage consumption by hour

**Note:** Requires access to UAE (Usage and Entitlement) cluster

---

## P360 Consumption Units

### 9. P360 Consumption Units - Weekly Summary

**Query Name:** `P360ConsumptionUnitsPROD` - Weekly Aggregation

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `workload_dimensions_service_level_4` | string | Product name |
| `sum_Weekly_1_Quantity` | real | Week 1 consumption |
| `sum_Weekly_2_Quantity` | real | Week 2 consumption |
| `sum_Weekly_3_Quantity` | real | Week 3 consumption |
| `sum_Weekly_4_Quantity` | real | Week 4 consumption |
| `sum_Weekly_5_Quantity` | real | Week 5 consumption |
| `sum_Weekly_6_Quantity` | real | Week 6 consumption |
| `sum_Weekly_7_Quantity` | real | Week 7 consumption |
| `sum_Weekly_8_Quantity` | real | Week 8 consumption |
| `sum_Weekly_9_Quantity` | real | Week 9 consumption |
| `sum_Weekly_10_Quantity` | real | Week 10 consumption |


**Use Case:** Weekly consumption trend analysis, capacity planning, cost forecasting

**Note:** Requires access to P360 consumption cluster (consumptionrptwus3prod.westus3.kusto.windows.net)
---

### 10. P360 Consumption Units - Daily Summary

**Query Name:** `P360ConsumptionUnitsPROD` - Daily Aggregation

**Output Columns:**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `workload_dimensions_service_level_4` | string | Product name |
| `sum_Daily_1_Quantity` | real | Day 1 consumption |
| `sum_Daily_2_Quantity` | real | Day 2 consumption |
| `sum_Daily_3_Quantity` | real | Day 3 consumption |
| `sum_Daily_4_Quantity` | real | Day 4 consumption |
| `sum_Daily_5_Quantity` | real | Day 5 consumption |
| `sum_Daily_6_Quantity` | real | Day 6 consumption |
| `sum_Daily_7_Quantity` | real | Day 7 consumption |
| `sum_Daily_8_Quantity` | real | Day 8 consumption |
| `sum_Daily_9_Quantity` | real | Day 9 consumption |
| `sum_Daily_10_Quantity` | real | Day 10 consumption |

**Use Case:** Daily consumption monitoring, anomaly detection, detailed cost attribution

---

## General Notes

## Handling Null/Empty Values

If any field returns null or empty from the query:

### Data Types

- **datetime**: (UTC format: `2026-01-01 02:00:00`)
- **string**: Text values
- **real**: Floating-point numbers (may include decimals)
- **long**: 64-bit integers

### Common Filters

All queries support filtering by these normalized parameters:
- **Time Range**: `{StartTime}` / `{EndTime}` parameters (UTC format: `2026-01-01 02:00:00`)
- **Server Name**: `{LogicalServerName}` - Logical server name
- **Database Name**: `{LogicalDatabaseName}` - Logical database name
- **Database ID**: `{logical_database_id}` - Logical database identifier (GUID format)
- **Subscription ID**: `{customer_subscription_id}` - Customer subscription identifier (GUID format)

**Note:** Parameter names follow the normalized naming convention defined in [normalize-query-params.prompt.md](../../../prompts/normalize-query-params.prompt.md)

### Empty Results

If queries return empty results, check:
1. **Time range**: Ensure data exists for the specified period
2. **Case sensitivity**: Use `=~` for case-insensitive comparisons
3. **Table retention**: Some tables have limited retention periods
4. **Access permissions**: Verify Kusto cluster access
5. **Deprecated tables**: PostReportedUsage2 may be deprecated

### Billing Calculation Frequency

- **MonManagement** events: Typically every 12 hours
- **MonBillingPitrBackupSize**: Every hour
- **ScopePostReportedUsage**: Hourly aggregation sent to commerce
- **P360ConsumptionUnits**: Weekly/daily rollups with lag

---

## Related References

- [queries.md](queries.md) - Query definitions and KQL code
- [SKILL.md](../SKILL.md) - Main billing skill documentation

---

