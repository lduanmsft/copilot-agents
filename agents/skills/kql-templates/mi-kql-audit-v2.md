# MI KQL Template Audit V2

## Summary
- Total skills: 1197
- Valid: 995
- Fixed: 8 (TableName corrections, broken removals)
- Prompts enriched: 1197
- Broken entries remaining: 202

## Fixes Applied
| Skill ID | File | Fix Description |
|----------|------|-----------------|
| MI-performance-71 | performance.yaml | TableName MonSQLSystemHealth -> MonDmDbResourceGovernance |
| MI-performance-167 | performance.yaml | TableName MonSQLXStore -> MonManagementOperations |
| MI-performance-193 | performance.yaml | TableName MonDmRealTimeResourceStats -> MonCounterOneMinute |
| MI-performance-194 | performance.yaml | TableName MonDmRealTimeResourceStats -> MonCounterOneMinute |
| MI-availability-53 | availability.yaml | TableName Unknown -> ExtEvents |
| MI-availability-78 | availability.yaml | TableName Unknown -> WinFabLogs |
| MI-availability-94 | availability.yaml | TableName MonFabricClusters -> GetSqlRunnerLog |
| MI-availability-95 | availability.yaml | TableName Unknown -> CAD |

## Remaining Broken Entries
| Skill ID | File | Declared | Detected | Issue |
|----------|------|----------|----------|-------|
| MI-performance-2 | performance.yaml | MonManagedInstanceResourceStats | MonManagedInstanceResourceStats | missing pipe |
| MI-performance-6 | performance.yaml | Unknown | — | missing table |
| MI-performance-30 | performance.yaml | MonWiQueryParamData | — | missing table |
| MI-performance-42 | performance.yaml | Unknown | — | missing table |
| MI-performance-45 | performance.yaml | MonDmCloudDatabaseWaitStats | MonDmCloudDatabaseWaitStats | missing pipe |
| MI-performance-50 | performance.yaml | MonWiQdsWaitStats | MonWiQdsWaitStats | missing pipe |
| MI-performance-59 | performance.yaml | Unknown | oomApps | missing table |
| MI-performance-65 | performance.yaml | MonSqlCaches | — | missing table |
| MI-performance-66 | performance.yaml | MonSqlBrokerRingBuffer | — | missing table |
| MI-performance-67 | performance.yaml | MonRgLoad | — | missing table |
| MI-performance-68 | performance.yaml | MonSqlMemNodeOomRingBufferOOM | — | missing table |
| MI-performance-69 | performance.yaml | MonSqlMemNodeOomRingBuffer | — | missing table |
| MI-performance-70 | performance.yaml | MonSQLSystemHealth | — | missing table |
| MI-performance-72 | performance.yaml | MonDmOsBPoolPerfCountersBuffer | — | missing table |
| MI-performance-73 | performance.yaml | MonWiQdsWaitStats | — | missing table |
| MI-performance-74 | performance.yaml | MonWiQdsExecStatsCheck | — | missing table |
| MI-performance-76 | performance.yaml | MonQueryProcessingMonQueryProcessing | — | missing table |
| MI-performance-77 | performance.yaml | Unknown | — | missing table |
| MI-performance-78 | performance.yaml | MonDmOsWaitstatsMonSqlRgHistory | — | missing table |
| MI-performance-79 | performance.yaml | MonDatabaseMetadata | — | missing table |
| MI-performance-94 | performance.yaml | Unknown | oomApps | missing table |
| MI-performance-105 | performance.yaml | MonBlockedProcessReportFiltered | — | missing table, missing pipe |
| MI-performance-108 | performance.yaml | MonSqlMemNodeOomRingBuffer | MonSqlMemNodeOomRingBuffer | missing pipe |
| MI-performance-111 | performance.yaml | Unknown | systemPoolLimitTable | missing table |
| MI-performance-132 | performance.yaml | Unknown | FilteredResults | missing table |
| MI-performance-133 | performance.yaml | Unknown | FilteredResults | missing table |
| MI-performance-134 | performance.yaml | Unknown | FilteredResults | missing table |
| MI-performance-135 | performance.yaml | MonDmIoVirtualFileStats | MonDmIoVirtualFileStats | missing pipe |
| MI-performance-138 | performance.yaml | Unknown | FilteredResults | missing table |
| MI-performance-139 | performance.yaml | Unknown | FilteredResults | missing table |
| MI-performance-140 | performance.yaml | Unknown | FilteredResults | missing table |
| MI-performance-144 | performance.yaml | Unknown | — | missing table |
| MI-performance-145 | performance.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-performance-147 | performance.yaml | Unknown | FilteredResults | missing table |
| MI-performance-148 | performance.yaml | Unknown | FilteredResults | missing table |
| MI-performance-158 | performance.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-performance-175 | performance.yaml | MonDmIoVirtualFileStats | — | missing table |
| MI-performance-180 | performance.yaml | MonResourcePoolStats | — | missing table |
| MI-performance-196 | performance.yaml | MonSqlRgHistory | BackupsInProgress | missing table |
| MI-performance-197 | performance.yaml | MonSQLXStoreIOStats | BackupsInProgress | missing table |
| MI-performance-229 | performance.yaml | MonCounterFiveMinute | — | missing table |
| MI-performance-238 | performance.yaml | Unknown | — | missing table |
| MI-performance-239 | performance.yaml | Unknown | — | missing table |
| MI-performance-240 | performance.yaml | Unknown | — | missing table |
| MI-performance-245 | performance.yaml | Unknown | — | missing table |
| MI-performance-246 | performance.yaml | MonDmRealTimeResourceStats | — | missing table, missing pipe |
| MI-performance-259 | performance.yaml | MonSqlRgHistory | MonSqlRgHistory | missing pipe |
| MI-performance-260 | performance.yaml | MonSqlRgHistory | MonSqlRgHistory | missing pipe |
| MI-performance-264 | performance.yaml | MonDmRealTimeResourceStats | — | missing table |
| MI-availability-1 | availability.yaml | Unknown | — | missing table |
| MI-availability-2 | availability.yaml | SqlFailovers | UnavailabilityEvents | missing table |
| MI-availability-16 | availability.yaml | Unknown | — | missing table |
| MI-availability-22 | availability.yaml | Unknown | — | missing table |
| MI-availability-41 | availability.yaml | Unknown | — | missing table |
| MI-availability-63 | availability.yaml | Unknown | — | missing table |
| MI-availability-80 | availability.yaml | Unknown | — | missing table |
| MI-availability-103 | availability.yaml | Unknown | — | missing table |
| MI-availability-108 | availability.yaml | MonManagementOperations | — | missing table |
| MI-availability-113 | availability.yaml | Unknown | — | missing table |
| MI-availability-124 | availability.yaml | Unknown | — | missing table |
| MI-availability-125 | availability.yaml | Unknown | — | missing table |
| MI-availability-147 | availability.yaml | MonSQLSystemHealth | MonSQLSystemHealth | missing pipe |
| MI-availability-148 | availability.yaml | MonDmDbHadrReplicaStates | MonDmDbHadrReplicaStates | missing pipe |
| MI-availability-149 | availability.yaml | MonSQLXStore | MonSQLXStore | missing pipe |
| MI-availability-150 | availability.yaml | MonSQLSystemHealth | MonSQLSystemHealth | missing pipe |
| MI-availability-151 | availability.yaml | MonSQLSystemHealth | MonSQLSystemHealth | missing pipe |
| MI-availability-154 | availability.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-availability-155 | availability.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-availability-156 | availability.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-availability-157 | availability.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-availability-158 | availability.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-availability-159 | availability.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-availability-162 | availability.yaml | Unknown | — | missing table |
| MI-availability-178 | availability.yaml | MonAnalyticsDBSnapshot | — | missing table |
| MI-availability-180 | availability.yaml | MonSQLSystemHealth | MonSQLSystemHealth | missing pipe |
| MI-availability-184 | availability.yaml | Unknown | — | missing table |
| MI-availability-186 | availability.yaml | Unknown | — | missing table |
| MI-availability-203 | availability.yaml | MonXdbLaunchSetup | MonXdbLaunchSetup | missing pipe |
| MI-availability-204 | availability.yaml | MonSQLSystemHealth | — | missing table |
| MI-availability-205 | availability.yaml | MonDmDbHadrReplicaStates | MonDmDbHadrReplicaStates | missing pipe |
| MI-availability-206 | availability.yaml | MonSQLSystemHealth | MonSQLSystemHealth | missing pipe |
| MI-availability-220 | availability.yaml | MonWorkerWaitStats | MonWorkerWaitStats | missing pipe |
| MI-availability-248 | availability.yaml | MonManagement | MonManagement | missing pipe |
| MI-availability-249 | availability.yaml | MonManagement | MonManagement | missing pipe |
| MI-availability-250 | availability.yaml | Unknown | — | missing table |
| MI-availability-251 | availability.yaml | MonSQLSystemHealth | MonSQLSystemHealth | missing pipe |
| MI-availability-252 | availability.yaml | MonLogin | — | missing table |
| MI-backup-restore-8 | backup-restore.yaml | Unknown | AllDatabases | missing table |
| MI-backup-restore-14 | backup-restore.yaml | MonRestoreEvents | MonRestoreEvents | missing pipe |
| MI-backup-restore-42 | backup-restore.yaml | MonImportExport | — | missing table |
| MI-backup-restore-72 | backup-restore.yaml | MonSQLSystemHealth | — | missing table |
| MI-backup-restore-75 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-76 | backup-restore.yaml | Unknown | ManagedDatabases | missing table |
| MI-backup-restore-80 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-82 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-86 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-118 | backup-restore.yaml | MonManagedServers | — | missing table |
| MI-backup-restore-121 | backup-restore.yaml | MonManagedInstanceResourceStats | — | missing table |
| MI-backup-restore-122 | backup-restore.yaml | MonManagedInstanceResourceStats | — | missing table |
| MI-backup-restore-123 | backup-restore.yaml | MonSqlRgHistory | — | missing table |
| MI-backup-restore-124 | backup-restore.yaml | MonManagedInstanceResourceStats | — | missing table |
| MI-backup-restore-125 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-126 | backup-restore.yaml | MonManagedServers | — | missing table |
| MI-backup-restore-127 | backup-restore.yaml | MonManagement | — | missing table |
| MI-backup-restore-128 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-129 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-130 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-131 | backup-restore.yaml | MonManagedInstanceResourceStats | — | missing table |
| MI-backup-restore-132 | backup-restore.yaml | MonSqlRgHistory | — | missing table |
| MI-backup-restore-134 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-135 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-137 | backup-restore.yaml | Unknown | BackupsAndAlerts | missing table |
| MI-backup-restore-138 | backup-restore.yaml | Unknown | BackupsAndAlerts | missing table |
| MI-backup-restore-139 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-140 | backup-restore.yaml | MonManagedServers | — | missing table |
| MI-backup-restore-151 | backup-restore.yaml | MonSQLSystemHealth | BackupServiceLogsForImpactedDatabases | missing table |
| MI-backup-restore-152 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-153 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-156 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-158 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-163 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-165 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-168 | backup-restore.yaml | Monitor | — | missing table |
| MI-backup-restore-169 | backup-restore.yaml | Monitor | — | missing table |
| MI-backup-restore-170 | backup-restore.yaml | MonitorId | — | missing table |
| MI-backup-restore-171 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-193 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-202 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-212 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-216 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-217 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-218 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-219 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-220 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-235 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-256 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-276 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-280 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-288 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-291 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-298 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-314 | backup-restore.yaml | MonBackup | — | missing table |
| MI-backup-restore-317 | backup-restore.yaml | MonWatsonAnalysis | — | missing table |
| MI-backup-restore-319 | backup-restore.yaml | MonWatsonAnalysis | — | missing table |
| MI-backup-restore-322 | backup-restore.yaml | MonManagedServers | — | missing table |
| MI-backup-restore-324 | backup-restore.yaml | MonManagedServers | — | missing table |
| MI-backup-restore-334 | backup-restore.yaml | MonManagementOperations | CurrentCount | missing table |
| MI-backup-restore-336 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-339 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-340 | backup-restore.yaml | MonManagementOperations | — | missing table |
| MI-backup-restore-341 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-366 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-373 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-375 | backup-restore.yaml | MonConfigLogicalServerOverrides | — | missing table |
| MI-backup-restore-387 | backup-restore.yaml | MonDatabaseMetadata | — | missing table |
| MI-backup-restore-391 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-392 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-394 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-395 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-400 | backup-restore.yaml | MonManagement | — | missing table |
| MI-backup-restore-405 | backup-restore.yaml | MonRestoreEvents | — | missing table |
| MI-backup-restore-406 | backup-restore.yaml | MonRestoreEvents | — | missing table |
| MI-backup-restore-407 | backup-restore.yaml | MonRestoreEvents | — | missing table |
| MI-backup-restore-447 | backup-restore.yaml | Unknown | — | missing table |
| MI-backup-restore-451 | backup-restore.yaml | Unknown | — | missing table |
| MI-networking-22 | networking.yaml | AlrLogin | — | missing table |
| MI-networking-51 | networking.yaml | MonManagedServers | — | missing table |
| MI-networking-54 | networking.yaml | Unknown | — | missing table |
| MI-networking-55 | networking.yaml | Unknown | — | missing table |
| MI-networking-56 | networking.yaml | Unknown | — | missing table |
| MI-networking-58 | networking.yaml | Unknown | — | missing table |
| MI-networking-59 | networking.yaml | Unknown | — | missing table |
| MI-networking-62 | networking.yaml | Unknown | — | missing table |
| MI-networking-63 | networking.yaml | Unknown | — | missing table |
| MI-networking-64 | networking.yaml | Unknown | — | missing table |
| MI-networking-65 | networking.yaml | Unknown | — | missing table |
| MI-networking-66 | networking.yaml | Unknown | — | missing table |
| MI-networking-67 | networking.yaml | Unknown | — | missing table |
| MI-networking-73 | networking.yaml | Unknown | — | missing table |
| MI-networking-74 | networking.yaml | Unknown | — | missing table |
| MI-networking-75 | networking.yaml | Unknown | — | missing table |
| MI-networking-80 | networking.yaml | MonSQLSystemHealth | — | missing table |
| MI-networking-85 | networking.yaml | Unknown | — | missing table |
| MI-networking-89 | networking.yaml | Unknown | — | missing table |
| MI-networking-90 | networking.yaml | Unknown | — | missing table |
| MI-networking-94 | networking.yaml | Unknown | — | missing table |
| MI-networking-95 | networking.yaml | Unknown | — | missing table |
| MI-networking-110 | networking.yaml | Unknown | — | missing table |
| MI-networking-115 | networking.yaml | MonLogin | — | missing table |
| MI-networking-118 | networking.yaml | MonLogin | — | missing table |
| MI-networking-125 | networking.yaml | Unknown | — | missing table |
| MI-networking-129 | networking.yaml | Monitor | — | missing table |
| MI-networking-130 | networking.yaml | MonitorIPv6DefaultGatewayRouteRunner | — | missing table |
| MI-networking-131 | networking.yaml | Monitor | — | missing table |
| MI-general-1 | general.yaml | MonManagedServers | MonManagedServers | missing pipe |
| MI-general-3 | general.yaml | MonPrivateClusters | — | missing table |
| MI-general-13 | general.yaml | MonDatabaseMetadata | MonDatabaseMetadata | missing pipe |
| MI-general-22 | general.yaml | MonDmIoVirtualFileStats | MonDmIoVirtualFileStats | missing pipe |
| MI-general-24 | general.yaml | MonDmRealTimeResourceStats | MonDmRealTimeResourceStats | missing pipe |
| MI-general-34 | general.yaml | Unknown | — | missing table |
| MI-general-38 | general.yaml | MonPrivateClusters | — | missing table |
| MI-general-39 | general.yaml | MonManagement | — | missing table |

## Sample Enriched Prompts

### MI-performance-1 (performance.yaml)

**Before**
```yaml
Prompts:
- MI resource resource usage by server
- MonDmRealTimeResourceStats server_name TIMESTAMP ServerName
- Check server_name ServerName
```

**After**
```yaml
Prompts:
- MI database CPU and memory stats by server
- MonDmRealTimeResourceStats server_name TIMESTAMP
- Investigate CPU pressure
```

### MI-performance-2 (performance.yaml)

**Before**
```yaml
Prompts:
- MI resource resource usage
- MonManagedInstanceResourceStats
- MI cpu investigation
```

**After**
```yaml
Prompts:
- MI instance CPU and memory stats
- MonManagedInstanceResourceStats
- Investigate CPU pressure
```

### MI-performance-3 (performance.yaml)

**Before**
```yaml
Prompts:
- MI resource resource usage
- MonGovernorWorkloadGroups whereAppName abb79ba9ec32
- Check whereAppName abb79ba9ec32
```

**After**
```yaml
Prompts:
- MI blocking chain details
- MonGovernorWorkloadGroups AppName
- Check MonGovernorWorkloadGroups AppName
```

### MI-performance-4 (performance.yaml)

**Before**
```yaml
Prompts:
- MI blocking blocking chain
- MonBlockedProcessReportFiltered TIMESTAMP 13:00:00
- Check TIMESTAMP 13:00:00
```

**After**
```yaml
Prompts:
- MI blocking chain details
- MonBlockedProcessReportFiltered TIMESTAMP
- Investigate blocking sessions
```

### MI-performance-5 (performance.yaml)

**Before**
```yaml
Prompts:
- MI blocking blocking chain by server
- MonBlockedProcessReportFiltered LogicalServerName TIMESTAMP
- Check LogicalServerName ServerName database_name
```

**After**
```yaml
Prompts:
- MI blocking chain details by server
- MonBlockedProcessReportFiltered LogicalServerName TIMESTAMP
- Investigate blocking sessions
```

### MI-performance-6 (performance.yaml)

**Before**
```yaml
Prompts:
- MI blocking blocking chain
- Unknown monitorLoop last
- Check Unknown monitorLoop last
```

**After**
```yaml
Prompts:
- MI blocking chain details
- Unknown monitorLoop last
- Check Unknown monitorLoop last
```

### MI-performance-7 (performance.yaml)

**Before**
```yaml
Prompts:
- MI blocking blocking chain
- MonBlockedProcessReportFiltered whereTIMESTAMP 10:00:00Z
- Check whereTIMESTAMP 10:00:00Z
```

**After**
```yaml
Prompts:
- MI blocking chain details
- MonBlockedProcessReportFiltered TIMESTAMP
- Investigate blocking sessions
```

### MI-performance-8 (performance.yaml)

**Before**
```yaml
Prompts:
- MI deadlock deadlock details
- MonDeadlockReportsFiltered
- MI deadlock investigation
```

**After**
```yaml
Prompts:
- MI deadlock reports
- MonDeadlockReportsFiltered
- Investigate deadlock graph
```

### MI-performance-9 (performance.yaml)

**Before**
```yaml
Prompts:
- MI network connectivity by server
- MonDeadlockReportsFiltered SubscriptionId LogicalServerName
- Check SubscriptionId SubscriptionId
```

**After**
```yaml
Prompts:
- MI deadlock reports by server
- MonDeadlockReportsFiltered SubscriptionId LogicalServerName
- Check MonDeadlockReportsFiltered SubscriptionId
```

### MI-performance-10 (performance.yaml)

**Before**
```yaml
Prompts:
- MI network connectivity by server
- MonDeadlockReportsFiltered SubscriptionId LogicalServerName
- Check SubscriptionId SubscriptionId
```

**After**
```yaml
Prompts:
- MI deadlock reports by server
- MonDeadlockReportsFiltered SubscriptionId LogicalServerName
- Check MonDeadlockReportsFiltered SubscriptionId
```
