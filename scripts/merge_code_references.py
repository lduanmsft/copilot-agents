#!/usr/bin/env python3
"""
Merge MI code reference entries into DB code reference for shared tables.
Also incorporate sub-agent research results for DB-specific tables.
Goal: make db-tables-code-reference.md self-contained.
"""
import re
import os

BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")
MI_CODE_REF = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\mi-tables-code-reference.md")
DB_CODE_REF = os.path.join(BASE, 'db-tables-code-reference.md')

# 1. Get list of tables used in DB YAMLs
db_tables = set()
categories = ['availability', 'connectivity', 'css-wiki', 'data-integration',
              'geodr', 'native', 'performance', 'query-store',
              'resource-governance', 'telemetry']
for cat in categories:
    yaml_path = os.path.join(BASE, cat, f'{cat}.yaml')
    if not os.path.exists(yaml_path):
        continue
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    for m in re.findall(r'TableName:\s*(\S+)', content):
        if re.match(r'^(Mon|Alr|Evt)', m):
            db_tables.add(m)

# Also from dashboard
dashboard_path = os.path.join(BASE, 'dashboard.yaml')
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    for m in re.findall(r'\b(Mon[A-Z]\w+|Alr[A-Z]\w+)', content):
        db_tables.add(m)

print(f"DB tables used in YAMLs: {len(db_tables)}")

# 2. Get tables already in DB code ref
with open(DB_CODE_REF, 'r', encoding='utf-8', errors='replace') as f:
    db_code_content = f.read()

db_code_tables = set()
for m in re.finditer(r'^## (?:\d+\.\s+)?(\w+)\s*—', db_code_content, re.MULTILINE):
    db_code_tables.add(m.group(1))
print(f"Tables already in DB code ref: {len(db_code_tables)}")

# 3. Get MI code ref sections
with open(MI_CODE_REF, 'r', encoding='utf-8', errors='replace') as f:
    mi_code_content = f.read()

# Parse MI code ref into sections by table name
mi_sections = {}
mi_pattern = r'^(## (?:\d+\.\s+)?(\w+)\s*—.*?)(?=\n## |\Z)'
for m in re.finditer(mi_pattern, mi_code_content, re.MULTILINE | re.DOTALL):
    section_text = m.group(1).strip()
    table_name = m.group(2)
    mi_sections[table_name] = section_text

mi_code_tables = set(mi_sections.keys())
print(f"Tables in MI code ref: {len(mi_code_tables)}")

# 4. Find shared tables: used in DB YAMLs AND in MI code ref AND NOT already in DB code ref
shared_to_copy = db_tables & mi_code_tables - db_code_tables
print(f"Shared tables to copy from MI → DB: {len(shared_to_copy)}")
for t in sorted(shared_to_copy):
    print(f"  {t}")

# 5. Find tables used in DB YAMLs with NO code ref anywhere
no_code_ref = db_tables - db_code_tables - mi_code_tables
print(f"\nTables with NO code ref (MI or DB): {len(no_code_ref)}")
for t in sorted(no_code_ref):
    print(f"  {t}")

# 6. Build the merged content
# Keep existing DB code ref, add shared tables section
new_sections = []
for t in sorted(shared_to_copy):
    section = mi_sections[t]
    # Renumber: remove old numbering
    section = re.sub(r'^## \d+\.\s+', '## ', section, count=1)
    new_sections.append(section)

if new_sections:
    shared_block = "\n\n# Shared Tables — Code Definitions (from MI Reference)\n\n"
    shared_block += "The following table code definitions are shared between SQL DB and MI.\n"
    shared_block += "They were originally documented in `mi-tables-code-reference.md` and are included here for self-contained reference.\n\n---\n\n"
    shared_block += "\n\n---\n\n".join(new_sections)

    # Append to DB code ref
    with open(DB_CODE_REF, 'a', encoding='utf-8') as f:
        f.write("\n\n" + shared_block + "\n")
    
    print(f"\nAppended {len(new_sections)} shared table sections to db-tables-code-reference.md")

# 7. Summary
total_in_db_code = len(db_code_tables) + len(shared_to_copy)
print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
print(f"Tables in DB YAMLs:               {len(db_tables)}")
print(f"Tables in DB code ref (before):   {len(db_code_tables)}")
print(f"Shared tables added from MI:      {len(shared_to_copy)}")
print(f"Tables in DB code ref (after):    {total_in_db_code}")
print(f"Still missing code ref:           {len(no_code_ref)}")
print(f"Coverage: {total_in_db_code}/{len(db_tables)} = {total_in_db_code/len(db_tables)*100:.1f}%")
