#!/usr/bin/env python3
"""
P1 Cleanup: Fix invalid TableName entries in SQL DB KQL YAML templates.
1. Auto-fix: replace invalid TableName with first Mon*/Alr* table found in query
2. Remove: entries with empty queries or pure garbage
3. Set function name: for cross-cluster/function queries
"""
import re
import os
from collections import defaultdict

BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

# All invalid TableName values to check
INVALID_SET = {
    'ago', 'now', 'datetime', 'toscalar', 'strcat', 'sum', 'bin', 'color', 'cross',
    'background', 'margin', 'line', 'font', 'web', 'table', 'a', 'can', 'do', 'read',
    'should', 'typically', 'This', 'Set', 'WITH', 'dynamic', 'query', 'Initial', 'X', 'RG',
    'mediumvioletred', 'quot', 'nulls', 'attot', 'tococoo', 'OICIIO', 'shouldSubstring',
    'my_start_datetime', 'no', "'no'",
    # columns-as-table
    'cpu_usage_percent', 'cv_ComponentOwnerName', 'object_store_total_pages',
    'pfs_close_handle_samples', 'query_hash', 'instance_cpu_mem_table',
    'timeouts', 'timeouts_size', 'timedelta', 'totalXIOBasedDb',
    'AppName', 'log_backup_cumulative_size_mb', 'systemmetadata_written',
    'usergroup_usage', 'blockingchain', 'ExecutionCount', 'input_StartTime',
    'ReplaceWithAppropriateTimestamp',
    # variables
    'rgPhysStats', 'rgQuality', 'FilteredResults', 'testcase', 'cluster',
}

# Known Kusto functions that can serve as "table" in KQL
KNOWN_FUNCTIONS = {
    'soc_get_matching_apps_in_interval': 'MonSocrates',
    'GetSqlRunnerLog': 'GetSqlRunnerLog',
    'ScanAllTables': 'ASTrace',
    'GetRaidMwcAll': 'MwcTrace',
    'MwcToPbiEndToEndProdTraces': 'PbiToMwcEndToEndProdTraces',
    'geneva_metrics_request': 'GenevaMetrics',
    'GetScenariosRunOnAgent': 'GetScenariosRunOnAgent',
}


def find_real_table(query_text):
    """Try to find the real table name from query content."""
    if not query_text or not query_text.strip():
        return None, 'empty'

    q = query_text.strip()

    # Strategy 1: Find Mon*/Alr*/Evt* table names
    tables = re.findall(r'\b(Mon[A-Z]\w+|Alr[A-Z]\w+|Evt\d+\w*)', q)
    if tables:
        return tables[0], 'auto-fix'

    # Strategy 2: Find known function calls
    for func_name, table_equiv in KNOWN_FUNCTIONS.items():
        if func_name in q:
            return table_equiv, 'function'

    # Strategy 3: Cross-cluster table reference
    cross_match = re.search(r'\.table\("(\w+)"\)', q)
    if cross_match:
        return cross_match.group(1), 'cross-cluster'

    # Strategy 4: Check for ASTrace (PBI/Trident)
    if 'ASTrace' in q:
        return 'ASTrace', 'external'

    # Strategy 5: Check for DataCatalog or other known tables
    known_ext = re.findall(r'\b(DataCatalog\w*|DD_Cluster|CADDAILY)\b', q)
    if known_ext:
        return known_ext[0], 'external'

    # Empty or garbage
    if len(q) < 10:
        return None, 'empty'

    return None, 'unknown'


def process_yaml(yaml_path, category):
    """Process a single YAML file. Returns stats."""
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    pattern = r'^- id:\s*(DB-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    if not matches:
        return {'fixed': 0, 'removed': 0, 'function': 0, 'unchanged': 0}

    stats = defaultdict(int)
    removals = []  # (start, end, skill_id, reason)
    fixes = []     # (old_tn_match_start, old_tn_match_end, old_tn, new_tn, skill_id)

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]
        skill_id = m.group(1)

        # Find TableName
        tn_m = re.search(r'(TableName:\s*)(\S+)', block)
        if not tn_m:
            continue
        old_tn = tn_m.group(2)
        if old_tn not in INVALID_SET:
            continue

        # Find ExecutedQuery
        eq_pos = block.find('ExecutedQuery:')
        if eq_pos < 0:
            removals.append((start, end, skill_id, 'no-query'))
            stats['removed'] += 1
            continue

        query_text = block[eq_pos + len('ExecutedQuery:'):]
        # Trim to just this skill's query (before next YAML key at same indent)
        next_key = re.search(r"\n\s+(DisplayedQuery|EvaluationTrue|EvaluationFalse|'?\n- id:)", query_text)
        if next_key:
            query_text = query_text[:next_key.start()]

        real_table, fix_type = find_real_table(query_text)

        if real_table and fix_type in ('auto-fix', 'function', 'cross-cluster', 'external'):
            # Fix the TableName in place
            abs_tn_start = start + tn_m.start(2)
            abs_tn_end = start + tn_m.end(2)
            fixes.append((abs_tn_start, abs_tn_end, old_tn, real_table, skill_id))
            stats['fixed'] += 1
            if fix_type == 'function':
                stats['function'] += 1
        elif fix_type == 'empty':
            removals.append((start, end, skill_id, 'empty-query'))
            stats['removed'] += 1
        else:
            # Can't fix, can't remove - leave as is but log
            stats['unchanged'] += 1
            print(f"  UNCHANGED: {skill_id} TN={old_tn} (no table found in query)")

    # Apply removals (reverse order)
    for rm_start, rm_end, skill_id, reason in sorted(removals, reverse=True):
        content = content[:rm_start] + content[rm_end:]
        print(f"  REMOVED: {skill_id} ({reason})")

    # Recalculate fix positions after removals
    # Need to re-parse after removals
    if removals:
        # Re-find all matches and re-identify fixes
        matches2 = list(re.finditer(pattern, content, re.MULTILINE))
        fixes = []
        for i, m in enumerate(matches2):
            start = m.start()
            end = matches2[i + 1].start() if i + 1 < len(matches2) else len(content)
            block = content[start:end]
            skill_id = m.group(1)
            tn_m = re.search(r'(TableName:\s*)(\S+)', block)
            if not tn_m:
                continue
            old_tn = tn_m.group(2)
            if old_tn not in INVALID_SET:
                continue
            eq_pos = block.find('ExecutedQuery:')
            if eq_pos < 0:
                continue
            query_text = block[eq_pos + len('ExecutedQuery:'):]
            next_key = re.search(r"\n\s+(DisplayedQuery|EvaluationTrue|EvaluationFalse|'?\n- id:)", query_text)
            if next_key:
                query_text = query_text[:next_key.start()]
            real_table, fix_type = find_real_table(query_text)
            if real_table and fix_type in ('auto-fix', 'function', 'cross-cluster', 'external'):
                abs_tn_start = start + tn_m.start(2)
                abs_tn_end = start + tn_m.end(2)
                fixes.append((abs_tn_start, abs_tn_end, old_tn, real_table, skill_id))

    # Apply fixes (reverse order to preserve positions)
    for abs_start, abs_end, old_tn, new_tn, skill_id in sorted(fixes, reverse=True):
        content = content[:abs_start] + new_tn + content[abs_end:]
        print(f"  FIXED: {skill_id} TableName: {old_tn} -> {new_tn}")

    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return stats


def main():
    categories = [
        'availability', 'connectivity', 'css-wiki', 'data-integration',
        'geodr', 'native', 'performance', 'query-store',
        'resource-governance', 'telemetry'
    ]

    total_stats = defaultdict(int)

    print("=" * 60)
    print("P1 Cleanup: Fix invalid TableName entries")
    print("=" * 60)

    for cat in categories:
        yaml_path = os.path.join(BASE, cat, f'{cat}.yaml')
        if not os.path.exists(yaml_path):
            continue
        print(f"\n[{cat}]")
        stats = process_yaml(yaml_path, cat)
        for k, v in stats.items():
            total_stats[k] += v

    print(f"\n{'=' * 60}")
    print(f"Fixed: {total_stats['fixed']} (of which {total_stats['function']} function-based)")
    print(f"Removed: {total_stats['removed']}")
    print(f"Unchanged: {total_stats['unchanged']}")
    print(f"Total processed: {sum(total_stats.values())}")
    print("=" * 60)

    # Post-cleanup counts
    print("\nPost-cleanup skill counts:")
    grand = 0
    for cat in categories:
        yaml_path = os.path.join(BASE, cat, f'{cat}.yaml')
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
                c = f.read()
            n = len(re.findall(r'^- id:\s*DB-', c, re.MULTILINE))
            grand += n
            print(f"  {cat}: {n}")
    print(f"  TOTAL: {grand}")


if __name__ == '__main__':
    main()
