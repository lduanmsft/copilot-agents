#!/usr/bin/env python3
"""
Comprehensive audit of MI extracted KQL YAML templates.
Same checks as DB audit: invalid TableName, HTML garbage, missing pipes, etc.
"""
import re
import os
from collections import defaultdict

BASE_DIR = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\mi")

VALID_TABLE_PREFIXES = (
    'Mon', 'Alr', 'Evt', 'Monaco', 'DBFileStats', 'RootHE',
    'PositiveSlopeRQ', 'PrimaryNodes', 'HttpIncomingRequests',
)

INVALID_INDICATORS = {
    'ago', 'now', 'datetime', 'toscalar', 'strcat', 'sum', 'bin', 'color',
    'background', 'margin', 'line', 'font', 'web', 'table', 'a', 'can', 'do', 'read',
    'should', 'typically', 'This', 'Set', 'WITH', 'dynamic', 'query', 'Initial', 'X', 'RG',
    'mediumvioletred', 'quot', 'nulls', 'attot', 'tococoo', 'OICIIO', 'shouldSubstring',
    'my_start_datetime', 'no', "'no'",
    'cpu_usage_percent', 'cv_ComponentOwnerName', 'object_store_total_pages',
    'pfs_close_handle_samples', 'query_hash', 'instance_cpu_mem_table',
    'timeouts', 'timeouts_size', 'timedelta', 'totalXIOBasedDb',
    'AppName', 'log_backup_cumulative_size_mb', 'systemmetadata_written',
    'usergroup_usage', 'blockingchain', 'ExecutionCount', 'input_StartTime',
    'ReplaceWithAppropriateTimestamp',
    'rgPhysStats', 'rgQuality', 'FilteredResults', 'testcase', 'cluster',
    'cross',
}

KNOWN_FUNCTIONS = {
    'GetCrossClusterData', 'GetSqlRunnerLog', 'GetStorageAccountToTenantMapSnapshot',
    'GetBatchedNodesOutOfSLA', 'GetGenerateMwcUserTokenRequests',
    'GetSubscriptionsAssociatedWith', '_ExecuteForProdClusters',
    'SREGetBugsFromWatsonDump',
}

KNOWN_EXTERNAL_TABLES = {
    'CADDAILY', 'CrpResourceMapEvent', 'LogContainerSnapshot', 'LogNodeSnapshot',
    'VMAAgentPing', 'VMA', 'WatsonODATAIngestionPipeline', 'ASTraceAll', 'ASTrace',
    'Incidents', 'customEvents', 'AllMeters', 'DeploymentOperations', 'Resources',
    'Sql_DB_VM_Cache_tb', 'SqlTenant_cache', 'SqlTenantVIPMdMmapping_cache_tb',
    'WinFabLogs', 'dcmInventoryComponentDiskHistory', 'dw_user_table_mappings',
    'PbiToMwcEndToEndProdTraces', 'StandardizedClientReporting', 'TenantsPBIView',
    'OnelakeRequests',
}


def classify_table_name(table_name):
    if not table_name:
        return 'missing'
    if table_name.startswith(VALID_TABLE_PREFIXES):
        return 'valid'
    if table_name in KNOWN_FUNCTIONS:
        return 'function'
    if table_name in KNOWN_EXTERNAL_TABLES:
        return 'external'
    if table_name in INVALID_INDICATORS:
        return 'invalid-keyword'
    if table_name[0].islower() and not table_name.startswith(('let', 'cluster')):
        return 'invalid-variable'
    if len(table_name) <= 2:
        return 'invalid-short'
    return 'unknown'


def check_query_quality(query):
    issues = []
    if not query or not query.strip():
        issues.append(('empty-query', 'ExecutedQuery is empty'))
        return issues
    q = query.strip()
    html_count = len(re.findall(r'<span\s', q))
    if html_count > 5:
        issues.append(('html-garbage', f'{html_count} HTML span tags'))
        return issues
    if '|' not in q and 'let ' not in q and len(q) > 20:
        issues.append(('no-pipe', 'No pipe operator and no let statement'))
    hardcoded_dt = re.findall(r"datetime\(\s*['\"]?\d{4}-\d{2}-\d{2}", q)
    if hardcoded_dt:
        issues.append(('hardcoded-datetime', f'{len(hardcoded_dt)} hardcoded datetime(s)'))
    unparameterized = re.findall(r'<<[^>]+>>', q)
    if unparameterized:
        issues.append(('unparameterized', f'Raw TSG placeholders: {unparameterized[:3]}'))
    return issues


def audit_category(category_dir, category_name):
    yaml_file = os.path.join(category_dir, f"{category_name}.yaml")
    if not os.path.exists(yaml_file):
        return [], 0

    with open(yaml_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    pattern = r'^- id:\s*(MI-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    issues = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]
        sid = match.group(1)

        tn_m = re.search(r'TableName:\s*(\S+)', block)
        table_name = tn_m.group(1) if tn_m else None

        tn_class = classify_table_name(table_name)
        if tn_class.startswith('invalid'):
            issues.append((sid, category_name, f'bad-tablename-{tn_class}', f"TableName='{table_name}'"))
        elif tn_class == 'missing':
            issues.append((sid, category_name, 'missing-tablename', 'No TableName'))
        elif tn_class == 'unknown':
            issues.append((sid, category_name, 'unknown-tablename', f"TableName='{table_name}'"))

        eq_m = re.search(r"ExecutedQuery:\s*['\"]?(.*?)(?:['\"]?\s*$|\n\s*(?:DisplayedQuery|EvaluationTrue|EvaluationFalse|\- id:))", block, re.DOTALL)
        query = eq_m.group(1).strip() if eq_m else ''
        q_issues = check_query_quality(query)
        for itype, detail in q_issues:
            issues.append((sid, category_name, itype, detail))

    return issues, len(matches)


def main():
    categories = ['availability', 'backup-restore', 'general', 'networking', 'performance', 'replication']
    all_issues = []
    total_skills = 0

    print("=" * 60)
    print("MI KQL Template Audit")
    print("=" * 60)

    for cat in categories:
        cat_dir = os.path.join(BASE_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        issues, skill_count = audit_category(cat_dir, cat)
        all_issues.extend(issues)
        total_skills += skill_count
        print(f"  {cat}: {skill_count} skills, {len(issues)} issues")

    print(f"\nTOTAL: {total_skills} skills, {len(all_issues)} issues")
    print("=" * 60)

    by_type = defaultdict(list)
    for sid, cat, itype, detail in all_issues:
        by_type[itype].append((sid, cat, detail))

    print("\n--- Issues by Type ---")
    for itype in sorted(by_type.keys()):
        items = by_type[itype]
        print(f"\n[{itype}] ({len(items)} total)")
        for sid, cat, detail in items[:5]:
            print(f"  {sid}: {detail}")
        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")

    critical = [i for i in all_issues if i[2] in ('html-garbage', 'no-pipe', 'empty-query')]
    print(f"\n--- CRITICAL (candidates for removal): {len(critical)} ---")
    for sid, cat, itype, detail in critical:
        print(f"  {sid} [{itype}] {detail}")

    # Table stats
    print("\n--- Table Stats ---")
    tables = defaultdict(int)
    for cat in categories:
        yaml_path = os.path.join(BASE_DIR, cat, f'{cat}.yaml')
        if not os.path.exists(yaml_path):
            continue
        with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        for m in re.findall(r'TableName:\s*(\S+)', content):
            tables[m] += 1
    
    real_tables = {t for t in tables if re.match(r'^(Mon|Alr|Evt)', t)}
    invalid_tables = {t for t in tables if classify_table_name(t).startswith('invalid')}
    print(f"Total unique TableNames: {len(tables)}")
    print(f"Real Kusto tables: {len(real_tables)}")
    print(f"Invalid TableNames: {len(invalid_tables)}")
    if invalid_tables:
        for t in sorted(invalid_tables):
            print(f"  {t} (used {tables[t]}x)")


if __name__ == '__main__':
    main()
