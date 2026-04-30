#!/usr/bin/env python3
"""
Fix the CamelCase-to-readable conversion issues from the previous script.
Correct: "s q l system health" -> "SQL system health"
Correct: "analytics d b snapshot" -> "analytics DB snapshot"
"""
import re
import os

DB_BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

# Known table name -> readable name mappings
TABLE_READABLE = {
    'MonSQLSystemHealth': 'SQL system health',
    'MonSQLXStore': 'SQL XStore',
    'MonSQLXStoreIOStats': 'SQL XStore IO stats',
    'MonSQLRBPEXStats': 'SQL RBPEX stats',
    'MonSQLNodeSnapshot': 'SQL node snapshot',
    'MonAnalyticsDBSnapshot': 'analytics DB snapshot',
    'MonAnalyticsRPSnapshot': 'analytics RP snapshot',
    'MonDmRealTimeResourceStats': 'real time resource stats',
    'MonDmCloudDatabaseWaitStats': 'cloud database wait stats',
    'MonDmDbHadrReplicaStates': 'HADR replica states',
    'MonDmDbResourceGovernance': 'DB resource governance',
    'MonDmIoVirtualFileStats': 'IO virtual file stats',
    'MonDmOsMemoryClerks': 'OS memory clerks',
    'MonDmOsSpinlockStats': 'OS spinlock stats',
    'MonDmOsWaitStats': 'OS wait stats',
    'MonDmTempDbFileSpaceUsage': 'tempdb file space usage',
    'MonDmTranActiveTransactions': 'active transactions',
    'MonDmContinuousCopyStatus': 'continuous copy status',
    'MonDmDbMirroringConnections': 'DB mirroring connections',
    'MonGeoDRFailoverGroups': 'GeoDR failover groups',
    'MonSqlRgHistory': 'SQL RG history',
    'MonSqlMemoryClerkStats': 'SQL memory clerk stats',
    'MonSqlMemNodeOomRingBuffer': 'SQL memory OOM ring buffer',
    'MonSqlMemNodeOomRingBufferOOM': 'SQL memory OOM ring buffer',
    'MonSqlCaches': 'SQL caches',
    'MonSqlDump': 'SQL dump',
    'MonSqlDumperActivity': 'SQL dumper activity',
    'MonSqlDumpSignal': 'SQL dump signal',
    'MonSqlFrontend': 'SQL frontend',
    'MonSqlSecurityService': 'SQL security service',
    'MonSqlShrinkInfo': 'SQL shrink info',
    'MonSqlTransactions': 'SQL transactions',
    'MonSqlVolumeGovernance': 'SQL volume governance',
    'MonSqlIdleMemCollectorStats': 'SQL idle mem collector stats',
    'MonSqlIdleMemCollectorStatsServerless': 'SQL idle mem collector stats serverless',
    'MonSqlLocking': 'SQL locking',
    'MonSqlPerfCounters': 'SQL perf counters',
    'MonSqlSystemHealth': 'SQL system health',
    'MonSqlXStore': 'SQL XStore',
    'MonXlogSrv': 'xlog server',
    'MonXdbhost': 'XDB host',
    'MonXdbHost': 'XDB host',
    'MonWiQdsExecStats': 'QDS exec stats',
    'MonWiQdsWaitStats': 'QDS wait stats',
    'MonWiQueryParamData': 'query param data',
    'MonRgLoad': 'RG load',
    'MonRgManager': 'RG manager',
    'MonCDCTraces': 'CDC traces',
    'MonCTTraces': 'CT traces',
    'MonCLRTelemetry': 'CLR telemetry',
    'MonQPTelemetry': 'QP telemetry',
    'MonMDMEvent': 'MDM event',
    'MonFSM': 'FSM',
    'MonLogin': 'login',
    'MonBackup': 'backup',
    'MonManagement': 'management',
    'MonRedirector': 'redirector',
    'MonSocrates': 'socrates',
    'MonRecoveryTrace': 'recovery trace',
    'MonRestoreEvents': 'restore events',
    'MonColumnStoreRowGroupPhysicalStats': 'columnstore row group stats',
    'MonBlockedProcessReportFiltered': 'blocked process report',
    'MonDeadlockReportsFiltered': 'deadlock reports',
    'MonFabricApi': 'fabric API',
    'MonFabricClusters': 'fabric clusters',
    'MonFabricDebug': 'fabric debug',
    'MonManagedServers': 'managed servers',
    'MonManagementOperations': 'management operations',
    'MonManagementResourceProvider': 'management resource provider',
    'MonResourcePoolStats': 'resource pool stats',
    'MonGovernorResourcePools': 'governor resource pools',
    'MonGovernorWorkloadGroups': 'governor workload groups',
    'MonManagedInstanceResourceStats': 'managed instance resource stats',
    'MonClusterLoad': 'cluster load',
    'MonCvTestMigrations': 'CV test migrations',
    'MonCvPeople': 'CV people',
    'MonSynapseLinkTraces': 'synapse link traces',
    'MonQueryProcessing': 'query processing',
    'MonQueryStoreInfo': 'query store info',
    'MonDatabaseMetadata': 'database metadata',
    'MonWebQueryEndpoint': 'web query endpoint',
    'AlrLogin': 'login alerts',
    'AlrSQLErrorsReported': 'SQL errors reported',
    'AlrMAEventFiveMinutes': 'MA event five minutes',
    'GetScenariosRunOnAgent': 'get scenarios run on agent',
    'GetSqlRunnerLog': 'get SQL runner log',
    'DD_Cluster': 'DD cluster',
    'DataCatalog_Manifest_Snapshot': 'data catalog manifest snapshot',
    'ASTrace': 'AS trace',
    'GenevaMetrics': 'Geneva metrics',
    'MonJobsQuery': 'jobs query',
    'MonAgentHost': 'agent host',
}

# Bad conversions to fix
BAD_CONVERSIONS = {
    's q l system health': 'SQL system health',
    's q l x store': 'SQL XStore',
    's q l r b p e x stats': 'SQL RBPEX stats',
    's q l node snapshot': 'SQL node snapshot',
    'analytics d b snapshot': 'analytics DB snapshot',
    'analytics r p snapshot': 'analytics RP snapshot',
    'd m real time resource stats': 'real time resource stats',
    'd m cloud database wait stats': 'cloud database wait stats',
    'd m db hadr replica states': 'HADR replica states',
    'd m db resource governance': 'DB resource governance',
    'd m io virtual file stats': 'IO virtual file stats',
    'd m os memory clerks': 'OS memory clerks',
    'd m os spinlock stats': 'OS spinlock stats',
    'd m os wait stats': 'OS wait stats',
    'd m temp db file space usage': 'tempdb file space usage',
    'd m tran active transactions': 'active transactions',
    'd m continuous copy status': 'continuous copy status',
    'd m db mirroring connections': 'DB mirroring connections',
    'geo d r failover groups': 'GeoDR failover groups',
    'sql rg history': 'SQL RG history',
    'sql memory clerk stats': 'SQL memory clerk stats',
    'sql mem node oom ring buffer': 'SQL memory OOM ring buffer',
    'c d c traces': 'CDC traces',
    'c t traces': 'CT traces',
    'c l r telemetry': 'CLR telemetry',
    'q p telemetry': 'QP telemetry',
    'm d m event': 'MDM event',
    'f s m': 'FSM',
    'xlog srv': 'xlog server',
    'xdb host': 'XDB host',
    'xdbhost': 'XDB host',
    'wi qds exec stats': 'QDS exec stats',
    'wi qds wait stats': 'QDS wait stats',
    'wi query param data': 'query param data',
    'rg load': 'RG load',
    'rg manager': 'RG manager',
    'column store row group physical stats': 'columnstore row group stats',
    'blocked process report filtered': 'blocked process report',
    'deadlock reports filtered': 'deadlock reports',
    'dm real time resource stats': 'real time resource stats',
    'get scenarios run on agent': 'get scenarios run on agent',
    'd d_ cluster': 'DD cluster',
    'data catalog_ manifest_ snapshot': 'data catalog manifest snapshot',
    'MonWebQueryEndpoint query endpoint query endpoint': 'web query endpoint',
}


def fix_bad_conversions(yaml_path):
    """Fix the bad CamelCase conversions in prompts."""
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    original = content
    fixes = 0
    
    for bad, good in BAD_CONVERSIONS.items():
        count = content.count(bad)
        if count > 0:
            content = content.replace(bad, good)
            fixes += count
    
    if content != original:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return fixes


def main():
    db_cats = ['availability', 'connectivity', 'css-wiki', 'data-integration',
               'geodr', 'native', 'performance', 'query-store',
               'resource-governance', 'telemetry']
    
    print("=" * 60)
    print("Fix bad CamelCase conversions in prompts")
    print("=" * 60)
    
    total = 0
    for cat in db_cats:
        yaml_path = os.path.join(DB_BASE, cat, f'{cat}.yaml')
        if os.path.exists(yaml_path):
            n = fix_bad_conversions(yaml_path)
            if n > 0:
                print(f"  {cat}: fixed {n} bad conversions")
                total += n
    
    print(f"\nTotal fixes: {total}")


if __name__ == '__main__':
    main()
