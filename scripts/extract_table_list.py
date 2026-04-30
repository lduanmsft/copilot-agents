#!/usr/bin/env python3
"""
Extract fresh table list from cleaned YAML templates.
Compare with db-tables-list.txt and db-tables-reference.md.
Output: gap analysis + updated db-tables-list.txt
"""
import re
import os
from collections import defaultdict

BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

categories = [
    'availability', 'connectivity', 'css-wiki', 'data-integration',
    'geodr', 'native', 'performance', 'query-store',
    'resource-governance', 'telemetry'
]

# 1. Extract all TableName from YAML + dashboard
table_usage = defaultdict(lambda: defaultdict(int))  # table -> {category: count}

for cat in categories:
    yaml_path = os.path.join(BASE, cat, f'{cat}.yaml')
    if not os.path.exists(yaml_path):
        continue
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    tables = re.findall(r'TableName:\s*(\S+)', content)
    for t in tables:
        table_usage[t][cat] += 1

# Dashboard
dashboard_path = os.path.join(BASE, 'dashboard.yaml')
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    # Dashboard format uses "tables:" list
    dashboard_tables = re.findall(r'^\s+- (Mon\w+|Alr\w+)', content, re.MULTILINE)
    for t in dashboard_tables:
        table_usage[t]['dashboard'] += 1
    # Also scan query bodies for table refs
    body_tables = re.findall(r'\b(Mon[A-Z]\w+|Alr[A-Z]\w+)', content)
    for t in body_tables:
        table_usage[t]['dashboard-body'] += 1

all_tables_from_yaml = sorted(table_usage.keys())

print(f"=== Tables extracted from YAML (post-cleanup) ===")
print(f"Total unique tables: {len(all_tables_from_yaml)}")

# 2. Read existing db-tables-list.txt
list_path = os.path.join(BASE, 'db-tables-list.txt')
existing_list = set()
if os.path.exists(list_path):
    with open(list_path, 'r') as f:
        for line in f:
            t = line.strip()
            if t and not t.startswith('#'):
                existing_list.add(t)

print(f"\nExisting db-tables-list.txt: {len(existing_list)} entries")

# 3. Read db-tables-reference.md - extract table names that have schema
ref_path = os.path.join(BASE, 'db-tables-reference.md')
tables_with_schema = set()
if os.path.exists(ref_path):
    with open(ref_path, 'r', encoding='utf-8', errors='replace') as f:
        ref_content = f.read()
    # Match ## TableName — or ## TableName —
    for m in re.finditer(r'^## (\w+)\s*—', ref_content, re.MULTILINE):
        tables_with_schema.add(m.group(1))

print(f"Tables with schema in db-tables-reference.md: {len(tables_with_schema)}")

# 4. Read db-tables-code-reference.md - extract table names
code_ref_path = os.path.join(BASE, 'db-tables-code-reference.md')
tables_with_code_ref = set()
if os.path.exists(code_ref_path):
    with open(code_ref_path, 'r', encoding='utf-8', errors='replace') as f:
        code_content = f.read()
    for m in re.finditer(r'^## (?:\d+\.\s+)?(\w+)\s*—', code_content, re.MULTILINE):
        tables_with_code_ref.add(m.group(1))

print(f"Tables with code ref in db-tables-code-reference.md: {len(tables_with_code_ref)}")

# 5. Gap analysis
yaml_set = set(all_tables_from_yaml)

# Filter to only Mon*/Alr*/Evt* (real Kusto tables)
real_tables = {t for t in yaml_set if re.match(r'^(Mon|Alr|Evt)', t)}
print(f"\nReal Kusto tables (Mon*/Alr*/Evt*): {len(real_tables)}")

# External/function tables
external_tables = yaml_set - real_tables
if external_tables:
    print(f"External/function tables (not Mon/Alr/Evt): {len(external_tables)}")
    for t in sorted(external_tables):
        cats = ', '.join(f"{k}:{v}" for k, v in sorted(table_usage[t].items()))
        print(f"  {t} ({cats})")

# Tables in YAML but NOT in list
new_in_yaml = real_tables - existing_list
if new_in_yaml:
    print(f"\n--- NEW tables in YAML, not in db-tables-list.txt ({len(new_in_yaml)}) ---")
    for t in sorted(new_in_yaml):
        cats = ', '.join(f"{k}:{v}" for k, v in sorted(table_usage[t].items()))
        print(f"  {t} ({cats})")

# Tables in list but NOT in YAML (orphaned)
orphaned = existing_list - real_tables
if orphaned:
    print(f"\n--- ORPHANED in db-tables-list.txt, not in any YAML ({len(orphaned)}) ---")
    for t in sorted(orphaned):
        print(f"  {t}")

# Tables in YAML but NO schema
no_schema = real_tables - tables_with_schema
if no_schema:
    print(f"\n--- Tables used in YAML but NO schema in db-tables-reference.md ({len(no_schema)}) ---")
    for t in sorted(no_schema):
        count = sum(table_usage[t].values())
        cats = ', '.join(f"{k}:{v}" for k, v in sorted(table_usage[t].items()))
        print(f"  {t} (used {count}x in: {cats})")

# Tables with schema but NO code ref
has_schema_no_code = tables_with_schema - tables_with_code_ref
# Only care about DB-specific ones (shared ones are in mi-tables-code-reference.md)
print(f"\n--- Tables with schema but NO code reference ({len(has_schema_no_code)}) ---")
print(f"  (Many are shared tables documented in mi-tables-code-reference.md)")

# Tables in YAML but NO code ref
no_code_ref = real_tables - tables_with_code_ref
print(f"\n--- Tables used in YAML but NO code reference ({len(no_code_ref)}) ---")
# Top 30 by usage
by_usage = [(t, sum(table_usage[t].values())) for t in no_code_ref]
by_usage.sort(key=lambda x: -x[1])
for t, count in by_usage[:30]:
    cats = ', '.join(sorted(table_usage[t].keys()))
    print(f"  {t} (used {count}x in: {cats})")
if len(by_usage) > 30:
    print(f"  ... and {len(by_usage) - 30} more")

# 6. Write updated db-tables-list.txt
new_list = sorted(real_tables)
new_list_path = os.path.join(BASE, 'db-tables-list-new.txt')
with open(new_list_path, 'w') as f:
    for t in new_list:
        f.write(t + '\n')
print(f"\nWrote {len(new_list)} tables to db-tables-list-new.txt")

# 7. Summary
print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
print(f"Real tables in cleaned YAMLs:     {len(real_tables)}")
print(f"Previously in db-tables-list.txt: {len(existing_list)}")
print(f"New tables found:                 {len(new_in_yaml)}")
print(f"Orphaned (removed from YAMLs):    {len(orphaned)}")
print(f"Tables with schema:               {len(tables_with_schema)}")
print(f"Tables with code reference:       {len(tables_with_code_ref)}")
print(f"Tables missing schema:            {len(no_schema)}")
print(f"Tables missing code ref:          {len(no_code_ref)}")
