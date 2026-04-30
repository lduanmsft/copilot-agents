#!/usr/bin/env python3
"""
Audit prompt tags in KQL YAML templates against table schema references.
Checks:
1. Prompt mentions the correct TableName
2. Prompt mentions real columns (not hallucinated)
3. Prompt is not too generic/unhelpful
4. Prompt topic matches query content
"""
import re
import os
import sys
from collections import defaultdict

def load_table_schemas(ref_path):
    """Parse table reference markdown and extract table -> set of column names."""
    schemas = {}
    if not os.path.exists(ref_path):
        return schemas
    with open(ref_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    current_table = None
    for line in content.split('\n'):
        # Match table headers like "## MonAnalyticsDBSnapshot — ..."
        m = re.match(r'^## (\w+)\s*—', line)
        if m:
            current_table = m.group(1)
            schemas[current_table] = set()
            continue
        # Match column rows like "| column_name | type | description |"
        if current_table and line.startswith('| ') and not line.startswith('| Column'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3 and parts[1] and not parts[1].startswith('-'):
                col = parts[1].strip('`')
                if col and col != 'Not recovered':
                    schemas[current_table].add(col)
    
    return schemas


def parse_skills(yaml_path, prefix='MI-'):
    """Parse YAML and return list of skill dicts."""
    if not os.path.exists(yaml_path):
        return []
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    pattern = rf'^- id:\s*({prefix}\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    skills = []
    
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(content)
        block = content[start:end]
        sid = m.group(1)
        
        # Extract TableName
        tn_m = re.search(r'TableName:\s*(\S+)', block)
        table_name = tn_m.group(1) if tn_m else None
        
        # Extract Prompts
        prompts = []
        prompt_section = re.search(r'Prompts:\s*\n((?:\s*-\s*.+\n)+)', block)
        if prompt_section:
            for pm in re.finditer(r'-\s*(.+)', prompt_section.group(1)):
                prompts.append(pm.group(1).strip())
        
        # Extract query snippet
        eq_m = re.search(r"ExecutedQuery:\s*['\"]?(.*?)(?:['\"]?\s*$)", block, re.DOTALL)
        query = eq_m.group(1)[:500] if eq_m else ''
        
        skills.append({
            'id': sid,
            'table_name': table_name,
            'prompts': prompts,
            'query_snippet': query,
        })
    
    return skills


def audit_prompts(skills, schemas):
    """Audit prompt quality for a list of skills."""
    issues = []
    
    for skill in skills:
        sid = skill['id']
        tn = skill['table_name']
        prompts = skill['prompts']
        query = skill['query_snippet']
        
        if not prompts:
            issues.append((sid, 'no-prompts', 'Skill has no Prompts'))
            continue
        
        # Check 1: Does any prompt mention the table name?
        table_mentioned = False
        if tn:
            for p in prompts:
                if tn.lower() in p.lower() or tn.replace('Mon', '').lower() in p.lower():
                    table_mentioned = True
                    break
        if not table_mentioned and tn:
            issues.append((sid, 'table-not-in-prompt', f'TableName "{tn}" not mentioned in any prompt'))
        
        # Check 2: Are prompts too short (< 10 chars)?
        for i, p in enumerate(prompts):
            if len(p) < 10:
                issues.append((sid, 'prompt-too-short', f'Prompt[{i}] too short: "{p}"'))
        
        # Check 3: Are prompts too generic?
        generic_patterns = [
            r'^SQL DB\s*$', r'^SQL DB investigate\s*$',
            r'^SQL DB troubleshoot\s*$', r'^investigate\s*$',
            r'^troubleshoot\s*$', r'^check\s*$',
        ]
        for i, p in enumerate(prompts):
            for gp in generic_patterns:
                if re.match(gp, p, re.IGNORECASE):
                    issues.append((sid, 'prompt-too-generic', f'Prompt[{i}] is generic: "{p}"'))
        
        # Check 4: Does prompt[1] (table+columns) mention real columns?
        if len(prompts) >= 2 and tn and tn in schemas:
            p1 = prompts[1]
            # Extract words that look like column names (lowercase with underscores)
            candidate_cols = re.findall(r'\b([a-z][a-z_0-9]+(?:_[a-z_0-9]+)+)\b', p1)
            real_cols = schemas[tn]
            for col in candidate_cols:
                if col not in real_cols and col not in ('sql_db', 'logical_server', 'time_range'):
                    # Don't flag common parameter-like patterns
                    if not col.startswith(('sql_', 'time_', 'server_')):
                        issues.append((sid, 'hallucinated-column', f'Column "{col}" in prompt not in schema for {tn}'))
        
        # Check 5: Prompt mentions wrong table (table in prompt doesn't match TableName)
        if len(prompts) >= 2:
            p1 = prompts[1].lower()
            # Find Mon* table references in prompt
            prompt_tables = re.findall(r'\b(mon[a-z]+)\b', p1, re.IGNORECASE)
            for pt in prompt_tables:
                # Normalize
                pt_normalized = pt
                if tn and pt_normalized.lower() != tn.lower() and pt_normalized.lower() != tn.lower().replace('mon', ''):
                    issues.append((sid, 'wrong-table-in-prompt', f'Prompt mentions "{pt}" but TableName is "{tn}"'))
        
        # Check 6: All 3 prompts are identical
        if len(prompts) >= 3 and prompts[0] == prompts[1] == prompts[2]:
            issues.append((sid, 'identical-prompts', f'All 3 prompts are identical: "{prompts[0]}"'))
        
        # Check 7: Prompt contains URL-encoded characters (from wiki page titles)
        for i, p in enumerate(prompts):
            if '%2D' in p or '%3A' in p or '%2C' in p:
                issues.append((sid, 'url-encoded-prompt', f'Prompt[{i}] has URL encoding: "{p[:80]}"'))
    
    return issues


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'both'
    
    # Load schemas
    mi_ref = os.path.expanduser(r'~\.copilot\agents\skills\kql-templates\mi-tables-reference.md')
    db_ref = os.path.expanduser(r'~\.copilot\agents\skills\kql-templates\sqldb-extracted\db-tables-reference.md')
    
    mi_schemas = load_table_schemas(mi_ref)
    db_schemas = load_table_schemas(db_ref)
    # Merge for cross-reference
    all_schemas = {**mi_schemas, **db_schemas}
    
    print(f"Loaded schemas: MI={len(mi_schemas)} tables, DB={len(db_schemas)} tables, merged={len(all_schemas)}")
    
    all_issues = []
    
    if mode in ('mi', 'both'):
        print("\n" + "="*60)
        print("MI PROMPT AUDIT")
        print("="*60)
        mi_base = os.path.expanduser(r'~\.copilot\agents\skills\kql-templates\mi')
        mi_cats = ['availability', 'backup-restore', 'general', 'networking', 'performance', 'replication']
        total_mi = 0
        for cat in mi_cats:
            yaml_path = os.path.join(mi_base, cat, f'{cat}.yaml')
            skills = parse_skills(yaml_path, 'MI-')
            total_mi += len(skills)
            issues = audit_prompts(skills, all_schemas)
            all_issues.extend([(cat, *i) for i in issues])
            if issues:
                print(f"  {cat}: {len(skills)} skills, {len(issues)} issues")
            else:
                print(f"  {cat}: {len(skills)} skills, OK")
        print(f"  Total MI: {total_mi} skills")
    
    if mode in ('db', 'both'):
        print("\n" + "="*60)
        print("DB PROMPT AUDIT")
        print("="*60)
        db_base = os.path.expanduser(r'~\.copilot\agents\skills\kql-templates\sqldb-extracted')
        db_cats = ['availability', 'connectivity', 'css-wiki', 'data-integration',
                    'geodr', 'native', 'performance', 'query-store',
                    'resource-governance', 'telemetry']
        total_db = 0
        for cat in db_cats:
            yaml_path = os.path.join(db_base, cat, f'{cat}.yaml')
            skills = parse_skills(yaml_path, 'DB-')
            total_db += len(skills)
            issues = audit_prompts(skills, all_schemas)
            all_issues.extend([(cat, *i) for i in issues])
            if issues:
                print(f"  {cat}: {len(skills)} skills, {len(issues)} issues")
            else:
                print(f"  {cat}: {len(skills)} skills, OK")
        print(f"  Total DB: {total_db} skills")
    
    # Summary by issue type
    print(f"\n{'='*60}")
    print(f"TOTAL ISSUES: {len(all_issues)}")
    print("="*60)
    
    by_type = defaultdict(list)
    for cat, sid, itype, detail in all_issues:
        by_type[itype].append((cat, sid, detail))
    
    for itype in sorted(by_type.keys()):
        items = by_type[itype]
        print(f"\n[{itype}] ({len(items)} total)")
        for cat, sid, detail in items[:5]:
            print(f"  {sid}: {detail}")
        if len(items) > 5:
            print(f"  ... and {len(items)-5} more")
    
    # Write report
    report_path = os.path.expanduser(r'~\.copilot\agents\skills\kql-templates\prompt-audit-results.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"Prompt Tag Audit - {len(all_issues)} issues\n\n")
        for itype in sorted(by_type.keys()):
            f.write(f"\n=== [{itype}] ({len(by_type[itype])}) ===\n")
            for cat, sid, detail in sorted(by_type[itype]):
                f.write(f"  {sid}\t{cat}\t{detail}\n")
    print(f"\nFull report: {report_path}")


if __name__ == '__main__':
    main()
