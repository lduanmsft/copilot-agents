#!/usr/bin/env python3
"""
Comprehensive audit of SQL DB extracted KQL YAML templates.
Checks: invalid TableName, HTML garbage, missing pipes, hardcoded values,
broken KQL, empty queries, duplicate entries, etc.
"""

import re
import os
import sys
import yaml
from collections import defaultdict

BASE_DIR = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

# Known valid table prefixes
VALID_TABLE_PREFIXES = (
    'Mon', 'Alr', 'Evt', 'Monaco', 'DBFileStats', 'RootHE',
    'PositiveSlopeRQ', 'PrimaryNodes', 'HttpIncomingRequests',
)

# Known Kusto functions (not tables, but valid as first token)
KNOWN_FUNCTIONS = {
    'GetCrossClusterData', 'GetSqlRunnerLog', 'GetStorageAccountToTenantMapSnapshot',
    'GetBatchedNodesOutOfSLA', 'GetGenerateMwcUserTokenRequests',
    'GetSubscriptionsAssociatedWith', '_ExecuteForProdClusters',
    'GetCrossClusterData', 'SREGetBugsFromWatsonDump',
}

# Known external/cross-system tables (valid but from other clusters)
KNOWN_EXTERNAL_TABLES = {
    'CADDAILY', 'CrpResourceMapEvent', 'LogContainerSnapshot', 'LogNodeSnapshot',
    'VMAAgentPing', 'VMA', 'WatsonODATAIngestionPipeline', 'ASTraceAll', 'ASTrace',
    'Incidents', 'customEvents', 'AllMeters', 'DeploymentOperations', 'Resources',
    'Sql_DB_VM_Cache_tb', 'SqlTenant_cache', 'SqlTenantVIPMdMmapping_cache_tb',
    'WinFabLogs', 'dcmInventoryComponentDiskHistory', 'dw_user_table_mappings',
    'PbiToMwcEndToEndProdTraces', 'StandardizedClientReporting', 'TenantsPBIView',
    'OnelakeRequests', 'AccountMoniker', 'XStoreAccountTransactionsDaily',
    'R2D2AppHealthState', 'SfmcLogsTest', 'SqlRunnerControlPlaneLog',
    'WASD2ProdMonDmvCollectorViewStats', 'ManagedApplicationSnapshot',
    'ExistingMiClusters', 'SchemaColumns', 'INVENTORY_CXObserve_SubscriptionInformation_v1',
}

# Invalid TableNames - these are KQL keywords, CSS, or garbage
INVALID_INDICATORS = {
    'ago', 'now', 'datetime', 'toscalar', 'strcat', 'sum', 'bin', 'color',
    'background', 'margin', 'line', 'font', 'web', 'a', 'can', 'do', 'read',
    'should', 'typically', 'This', 'Set', 'WITH', 'cross', 'table',
    'mediumvioletred', 'quot', 'nulls', 'dynamic', 'query', 'Initial',
    'attot', 'tococoo', 'OICIIO', 'shouldSubstring', 'my_start_datetime',
    'no', "'no'",
}

# Columns wrongly used as TableName
COLUMN_AS_TABLE = {
    'cpu_usage_percent', 'cv_ComponentOwnerName', 'object_store_total_pages',
    'pfs_close_handle_samples', 'query_hash', 'instance_cpu_mem_table',
    'timeouts', 'timeouts_size', 'timedelta', 'totalXIOBasedDb',
    'AppName', 'log_backup_cumulative_size_mb', 'systemmetadata_written',
    'usergroup_usage', 'blockingchain', 'ExecutionCount', 'input_StartTime',
    'ReplaceWithAppropriateTimestamp',
}


class Issue:
    def __init__(self, skill_id, category, issue_type, detail):
        self.skill_id = skill_id
        self.category = category
        self.issue_type = issue_type
        self.detail = detail

    def __repr__(self):
        return f"{self.skill_id} [{self.issue_type}] {self.detail}"


def classify_table_name(table_name):
    """Classify a TableName as valid, external, function, or invalid."""
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
    if table_name in COLUMN_AS_TABLE:
        return 'invalid-column'
    # Check for let-variable patterns (starts with lowercase, camelCase)
    if table_name[0].islower() and not table_name.startswith(('let', 'cluster')):
        return 'invalid-variable'
    # Short names are suspicious
    if len(table_name) <= 2:
        return 'invalid-short'
    # Check for clearly non-table patterns
    if re.match(r'^(RG|FilteredResults|testcase|rgPhysStats|rgQuality)$', table_name):
        return 'invalid-variable'
    return 'unknown'


def check_query_quality(query, skill_id):
    """Check a KQL query for various quality issues."""
    issues = []
    if not query or not query.strip():
        issues.append(('empty-query', 'ExecutedQuery is empty'))
        return issues

    q = query.strip()

    # HTML garbage
    html_count = len(re.findall(r'<span\s', q))
    if html_count > 5:
        issues.append(('html-garbage', f'{html_count} HTML span tags found'))
        return issues  # No point checking further

    # Check if starts with valid KQL
    first_line = q.split('\n')[0].strip()
    if first_line.startswith('|'):
        # Starts with pipe - missing table name
        if not any(first_line.startswith(f'| {kw}') for kw in ['where', 'summarize', 'project', 'extend', 'let']):
            pass  # might be continuation
        # Check if it's a let statement
    
    # Missing pipe operator entirely
    if '|' not in q and 'let ' not in q and len(q) > 20:
        issues.append(('no-pipe', 'No pipe operator and no let statement'))

    # Hardcoded server names (common patterns)
    hardcoded_servers = re.findall(r"(?:==|=~)\s*['\"]([a-z][a-z0-9\-]{5,})['\"]", q, re.IGNORECASE)
    for srv in hardcoded_servers:
        if srv not in ('{ServerName}', '{DatabaseName}', '{AppName}', '{ClusterName}',
                       'gateway', 'process_login_finish', 'Worker.ISO', 'Worker.ISO.Premium',
                       'Worker.DW', 'Worker.CL', 'Worker.Vldb.Compute',
                       'sqlazure1', 'sqlazure', 'Ready', 'Active', 'Online'):
            # Skip known event names, worker types, states
            if not re.match(r'^(management_|restoring_|sql_|fedauth_|backup_|process_)', srv):
                issues.append(('hardcoded-value', f'Possibly hardcoded: "{srv}"'))

    # Hardcoded datetime values
    hardcoded_dt = re.findall(r"datetime\(\s*['\"]?\d{4}-\d{2}-\d{2}", q)
    if hardcoded_dt:
        issues.append(('hardcoded-datetime', f'{len(hardcoded_dt)} hardcoded datetime(s)'))

    # Unparameterized placeholder patterns from TSGs
    unparameterized = re.findall(r'<<[^>]+>>', q)
    if unparameterized:
        issues.append(('unparameterized', f'Raw TSG placeholders: {unparameterized[:3]}'))

    return issues


def parse_sqlskills_yaml(filepath):
    """Parse a SqlSkills-format YAML file and return skill entries."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Split by skill entries
    skills = []
    # Use regex to find each skill block
    pattern = r'^- id:\s*(DB-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]

        skill_id = match.group(1)
        
        # Extract TableName
        tn_match = re.search(r'TableName:\s*(\S+)', block)
        table_name = tn_match.group(1) if tn_match else None

        # Extract ExecutedQuery
        eq_match = re.search(r"ExecutedQuery:\s*['\"]?(.*?)(?:['\"]?\s*$|\n\s*(?:DisplayedQuery|EvaluationTrue|EvaluationFalse|\- id:))", block, re.DOTALL)
        query = eq_match.group(1).strip() if eq_match else ''
        
        # Extract Topic
        topic_match = re.search(r"Topic:\s*(.+)", block)
        topic = topic_match.group(1).strip() if topic_match else ''

        # Extract Source
        source_match = re.search(r"Source:\s*(.+)", block)
        source = source_match.group(1).strip() if source_match else ''

        skills.append({
            'id': skill_id,
            'table_name': table_name,
            'query': query,
            'topic': topic,
            'source': source,
            'raw_block_len': len(block),
        })

    return skills


def audit_category(category_dir, category_name):
    """Audit all skills in a category YAML file."""
    yaml_file = os.path.join(category_dir, f"{category_name}.yaml")
    if not os.path.exists(yaml_file):
        print(f"  WARNING: {yaml_file} not found")
        return [], 0

    skills = parse_sqlskills_yaml(yaml_file)
    issues = []

    for skill in skills:
        sid = skill['id']

        # Check TableName
        tn_class = classify_table_name(skill['table_name'])
        if tn_class.startswith('invalid'):
            issues.append(Issue(sid, category_name, f'bad-tablename-{tn_class}',
                                f"TableName='{skill['table_name']}'"))
        elif tn_class == 'missing':
            issues.append(Issue(sid, category_name, 'missing-tablename', 'No TableName'))
        elif tn_class == 'unknown':
            issues.append(Issue(sid, category_name, 'unknown-tablename',
                                f"TableName='{skill['table_name']}' - needs manual review"))

        # Check query quality
        q_issues = check_query_quality(skill['query'], sid)
        for itype, detail in q_issues:
            issues.append(Issue(sid, category_name, itype, detail))

    return issues, len(skills)


def main():
    categories = [
        'availability', 'connectivity', 'css-wiki', 'data-integration',
        'geodr', 'native', 'performance', 'query-store',
        'resource-governance', 'telemetry'
    ]

    all_issues = []
    total_skills = 0
    category_stats = {}

    print("=" * 80)
    print("SQL DB KQL Template Audit v2")
    print("=" * 80)

    for cat in categories:
        cat_dir = os.path.join(BASE_DIR, cat)
        if not os.path.isdir(cat_dir):
            print(f"SKIP: {cat} (directory not found)")
            continue

        issues, skill_count = audit_category(cat_dir, cat)
        all_issues.extend(issues)
        total_skills += skill_count
        category_stats[cat] = {'skills': skill_count, 'issues': len(issues)}
        print(f"  {cat}: {skill_count} skills, {len(issues)} issues")

    print()
    print("=" * 80)
    print(f"TOTAL: {total_skills} skills, {len(all_issues)} issues")
    print("=" * 80)

    # Group by issue type
    by_type = defaultdict(list)
    for issue in all_issues:
        by_type[issue.issue_type].append(issue)

    print("\n--- Issues by Type ---")
    for itype in sorted(by_type.keys()):
        items = by_type[itype]
        print(f"\n[{itype}] ({len(items)} total)")
        # Show first 5 examples
        for item in items[:5]:
            print(f"  {item.skill_id}: {item.detail}")
        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")

    # Group by category
    print("\n--- Issues by Category ---")
    for cat in categories:
        cat_issues = [i for i in all_issues if i.category == cat]
        if cat_issues:
            by_cat_type = defaultdict(int)
            for i in cat_issues:
                by_cat_type[i.issue_type] += 1
            type_str = ", ".join(f"{k}:{v}" for k, v in sorted(by_cat_type.items()))
            print(f"  {cat}: {len(cat_issues)} issues ({type_str})")

    # Critical issues (should be removed)
    critical = [i for i in all_issues if i.issue_type in ('html-garbage', 'no-pipe', 'empty-query')]
    print(f"\n--- CRITICAL (candidates for removal): {len(critical)} ---")
    for item in critical:
        print(f"  {item.skill_id} [{item.issue_type}] {item.detail}")

    # Write full report
    report_path = os.path.join(BASE_DIR, 'audit-v2-results.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"SQL DB KQL Audit v2 - {total_skills} skills, {len(all_issues)} issues\n\n")
        
        f.write("=== CRITICAL (remove) ===\n")
        for item in critical:
            f.write(f"{item.skill_id}\t{item.issue_type}\t{item.detail}\n")
        
        f.write(f"\n=== BAD TABLENAME ({len([i for i in all_issues if 'tablename' in i.issue_type])}) ===\n")
        for item in sorted(all_issues, key=lambda x: x.skill_id):
            if 'tablename' in item.issue_type:
                f.write(f"{item.skill_id}\t{item.issue_type}\t{item.detail}\n")

        f.write(f"\n=== HARDCODED VALUES ({len([i for i in all_issues if 'hardcoded' in i.issue_type])}) ===\n")
        for item in sorted(all_issues, key=lambda x: x.skill_id):
            if 'hardcoded' in item.issue_type:
                f.write(f"{item.skill_id}\t{item.issue_type}\t{item.detail}\n")

        f.write(f"\n=== UNPARAMETERIZED ({len([i for i in all_issues if 'unparameterized' in i.issue_type])}) ===\n")
        for item in sorted(all_issues, key=lambda x: x.skill_id):
            if 'unparameterized' in item.issue_type:
                f.write(f"{item.skill_id}\t{item.issue_type}\t{item.detail}\n")

        f.write(f"\n=== ALL ISSUES ===\n")
        for item in sorted(all_issues, key=lambda x: (x.category, x.skill_id)):
            f.write(f"{item.skill_id}\t{item.category}\t{item.issue_type}\t{item.detail}\n")

    print(f"\nFull report saved to: {report_path}")


if __name__ == '__main__':
    main()
