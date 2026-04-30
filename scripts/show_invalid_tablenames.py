#!/usr/bin/env python3
"""Show invalid TableName entries with their actual query content to determine fix strategy."""
import re, os

BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")
cats = ['availability','connectivity','css-wiki','data-integration','geodr','native','performance','query-store','resource-governance','telemetry']

# All invalid patterns
INVALID_SET = {
    'ago','now','datetime','toscalar','strcat','sum','bin','color','cross',
    'background','margin','line','font','web','table','a','can','do','read',
    'should','typically','This','Set','WITH','dynamic','query','Initial','X','RG',
    'mediumvioletred','quot','nulls','attot','tococoo','OICIIO','shouldSubstring',
    'my_start_datetime','no',"'no'",
    # columns-as-table
    'cpu_usage_percent','cv_ComponentOwnerName','object_store_total_pages',
    'pfs_close_handle_samples','query_hash','instance_cpu_mem_table',
    'timeouts','timeouts_size','timedelta','totalXIOBasedDb',
    'AppName','log_backup_cumulative_size_mb','systemmetadata_written',
    'usergroup_usage','blockingchain','ExecutionCount','input_StartTime',
    'ReplaceWithAppropriateTimestamp',
    # variables
    'rgPhysStats','rgQuality','FilteredResults','testcase','cluster',
}

fixable = 0
unfixable = 0
results = []

for cat in cats:
    path = os.path.join(BASE, cat, f'{cat}.yaml')
    if not os.path.exists(path): continue
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    pattern = r'^- id:\s*(DB-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(content)
        block = content[start:end]
        tn_m = re.search(r'TableName:\s*(\S+)', block)
        if not tn_m: continue
        tn = tn_m.group(1)
        if tn not in INVALID_SET: continue
        
        # Extract query content
        eq_pos = block.find('ExecutedQuery:')
        if eq_pos < 0: continue
        query_part = block[eq_pos:eq_pos+800]
        
        # Find all Mon*/Alr* tables in the query
        tables_in_q = re.findall(r'\b(Mon[A-Z]\w+|Alr[A-Z]\w+|Evt\d+)', query_part)
        # Also check for let statements that reference tables
        let_tables = re.findall(r'(?:cluster\([^)]+\)\.database\([^)]+\)\.)?(Mon[A-Z]\w+|Alr[A-Z]\w+)', query_part)
        all_tables = list(dict.fromkeys(tables_in_q + let_tables))  # dedupe, keep order
        
        real_table = all_tables[0] if all_tables else None
        sid = m.group(1)
        
        # First 2 meaningful lines of query
        q_lines = [l.strip() for l in query_part.split('\n')[1:] if l.strip()][:3]
        q_preview = ' '.join(q_lines)[:150]
        
        if real_table:
            fixable += 1
            results.append((sid, tn, real_table, 'FIX', q_preview))
        else:
            unfixable += 1
            results.append((sid, tn, '???', 'REVIEW', q_preview))

print(f"Fixable (real table found in query): {fixable}")
print(f"Unfixable (no table found): {unfixable}")
print(f"Total: {fixable + unfixable}")
print()

print("=== FIXABLE examples ===")
fix_shown = 0
for sid, old_tn, new_tn, action, q in results:
    if action == 'FIX':
        print(f"  {sid:35s} {old_tn:25s} -> {new_tn}")
        fix_shown += 1
        if fix_shown >= 30: 
            remaining = fixable - 30
            if remaining > 0:
                print(f"  ... and {remaining} more fixable entries")
            break

print()
print("=== UNFIXABLE (need manual review or removal) ===")
for sid, old_tn, new_tn, action, q in results:
    if action == 'REVIEW':
        print(f"  {sid:35s} TN={old_tn:20s} Q={q[:120]}")
