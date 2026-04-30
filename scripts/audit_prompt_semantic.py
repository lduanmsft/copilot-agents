#!/usr/bin/env python3
"""
Semantic audit of DB KQL prompts: check if prompts accurately describe query content.
Sample skills from each category and cross-check prompt vs query.
"""
import re
import os
import random
from collections import defaultdict

DB_BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

def parse_skills(yaml_path):
    if not os.path.exists(yaml_path):
        return []
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    pattern = r'^- id:\s*(DB-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    skills = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(content)
        block = content[start:end]
        sid = m.group(1)
        tn_m = re.search(r'TableName:\s*(\S+)', block)
        table_name = tn_m.group(1) if tn_m else None
        prompts = []
        prompt_section = re.search(r'Prompts:\s*\n((?:\s*-\s*.+\n)+)', block)
        if prompt_section:
            for pm in re.finditer(r'-\s*(.+)', prompt_section.group(1)):
                prompts.append(pm.group(1).strip())
        eq_pos = block.find('ExecutedQuery:')
        query = ''
        if eq_pos >= 0:
            query = block[eq_pos+len('ExecutedQuery:'):eq_pos+800]
        topic_m = re.search(r'Topic:\s*(.+)', block)
        topic = topic_m.group(1).strip() if topic_m else ''
        source_m = re.search(r'Source:\s*(.+)', block)
        source = source_m.group(1).strip() if source_m else ''
        skills.append({
            'id': sid, 'table_name': table_name, 'prompts': prompts,
            'query': query, 'topic': topic, 'source': source,
        })
    return skills


def check_semantic_issues(skill):
    """Check for semantic mismatch between prompt and query."""
    issues = []
    sid = skill['id']
    prompts = skill['prompts']
    query = skill['query'].strip()
    tn = skill['table_name']
    topic = skill['topic']
    
    if not prompts or not query:
        return issues
    
    p0 = prompts[0].lower() if prompts else ''
    p1 = prompts[1].lower() if len(prompts) > 1 else ''
    p2 = prompts[2].lower() if len(prompts) > 2 else ''
    q_lower = query.lower()
    
    # 1. Prompt says "SQL DB" but query is MI-specific (Worker.CL filter)
    if 'worker.cl' in q_lower and 'sql db' in p0:
        issues.append((sid, 'mi-query-db-prompt', 'Prompt says "SQL DB" but query filters Worker.CL (MI-specific)'))
    
    # 2. Prompt mentions a scenario but query does completely different thing
    scenario_keywords = {
        'backup': ['monbackup', 'backup_type', 'backup_start', 'backup_end'],
        'login': ['monlogin', 'process_login', 'is_success', 'fedauth'],
        'deadlock': ['mondeadlock', 'xml_report', 'deadlock'],
        'blocking': ['monblocked', 'blocked_process', 'blocker'],
        'restore': ['monrestore', 'restore_request', 'restore_database'],
        'failover': ['mongeodr', 'failover_group', 'failover_policy'],
        'seeding': ['mondbseed', 'seeding', 'transferred_size'],
        'performance': ['cpu_percent', 'wait_type', 'resource_stats', 'dtu_limit'],
        'memory': ['memory_clerk', 'memory_usage', 'oom', 'out_of_memory'],
    }
    
    for scenario, kw_list in scenario_keywords.items():
        if scenario in p0:
            # Check if any keyword appears in query
            if not any(kw in q_lower for kw in kw_list):
                # Could be false positive — only flag if prompt is very specific
                if f'investigate {scenario}' in p0 or f'troubleshoot {scenario}' in p0:
                    issues.append((sid, 'scenario-mismatch', f'Prompt says "{scenario}" but query has no related keywords'))
    
    # 3. Prompt[0] and Prompt[2] are auto-generated duplicates (same pattern)
    if len(prompts) >= 3:
        # Common pattern: p0="SQL DB {X}", p2="SQL DB investigate/troubleshoot {X}"
        if p0.replace('sql db ', '') in p2.replace('sql db investigate ', '').replace('sql db troubleshoot ', ''):
            pass  # This is expected pattern, not an issue
    
    # 4. Prompt[1] (table+columns) references columns not in the query
    if len(prompts) >= 2:
        p1_words = set(p1.split())
        q_words = set(re.findall(r'\b\w+\b', q_lower))
        # Extract column-like words from p1 (multi-word with underscores)
        p1_cols = set(re.findall(r'\b([a-z][a-z_0-9]+(?:_[a-z_0-9]+)+)\b', p1))
        q_cols = set(re.findall(r'\b([a-z][a-z_0-9]+(?:_[a-z_0-9]+)+)\b', q_lower))
        
        # Columns in prompt but not in query at all
        phantom_cols = p1_cols - q_cols - {'sql_db', 'time_range', 'server_name', 'logical_server', 'database_name'}
        if len(phantom_cols) > 2:
            issues.append((sid, 'prompt-cols-not-in-query', f'Prompt mentions {len(phantom_cols)} cols not in query: {sorted(phantom_cols)[:3]}'))
    
    # 5. Prompt is clearly auto-generated garbage
    if p0.startswith('sql db ') and len(p0.split()) <= 3:
        # Very short prompt like "SQL DB line" or "SQL DB ago"
        remainder = p0.replace('sql db ', '')
        if remainder in ('line', 'ago', 'now', 'table', 'color', 'web', 'a'):
            issues.append((sid, 'garbage-prompt', f'Prompt is garbage: "{prompts[0]}"'))
    
    # 6. Topic is a date/meeting-notes filename (not a real TSG)
    if re.match(r'^\d+_\d+_\d+$', topic) or 'meeting' in topic.lower() or 'agenda' in topic.lower():
        issues.append((sid, 'non-tsg-topic', f'Topic looks like meeting notes: "{topic}"'))
    
    return issues


def main():
    db_cats = ['availability', 'connectivity', 'css-wiki', 'data-integration',
               'geodr', 'native', 'performance', 'query-store',
               'resource-governance', 'telemetry']
    
    all_issues = []
    total_skills = 0
    
    print("=" * 60)
    print("DB KQL Prompt Semantic Audit")
    print("=" * 60)
    
    for cat in db_cats:
        yaml_path = os.path.join(DB_BASE, cat, f'{cat}.yaml')
        skills = parse_skills(yaml_path)
        total_skills += len(skills)
        
        cat_issues = []
        for skill in skills:
            issues = check_semantic_issues(skill)
            cat_issues.extend(issues)
        
        all_issues.extend(cat_issues)
        if cat_issues:
            print(f"  {cat}: {len(skills)} skills, {len(cat_issues)} semantic issues")
        else:
            print(f"  {cat}: {len(skills)} skills, OK")
    
    print(f"\nTotal: {total_skills} skills, {len(all_issues)} semantic issues")
    print("=" * 60)
    
    by_type = defaultdict(list)
    for sid, itype, detail in all_issues:
        by_type[itype].append((sid, detail))
    
    for itype in sorted(by_type.keys()):
        items = by_type[itype]
        print(f"\n[{itype}] ({len(items)} total)")
        for sid, detail in items[:8]:
            print(f"  {sid}: {detail}")
        if len(items) > 8:
            print(f"  ... and {len(items)-8} more")
    
    # Also print some random samples for manual review
    print(f"\n{'='*60}")
    print("RANDOM SAMPLES FOR MANUAL REVIEW")
    print("="*60)
    
    all_skills = []
    for cat in db_cats:
        yaml_path = os.path.join(DB_BASE, cat, f'{cat}.yaml')
        skills = parse_skills(yaml_path)
        for s in skills:
            s['category'] = cat
        all_skills.extend(skills)
    
    random.seed(42)
    samples = random.sample(all_skills, min(20, len(all_skills)))
    for s in samples:
        print(f"\n--- {s['id']} ({s['category']}) ---")
        print(f"  Table: {s['table_name']}")
        print(f"  Topic: {s['topic']}")
        for i, p in enumerate(s['prompts']):
            print(f"  P[{i}]: {p}")
        # First meaningful line of query
        q_lines = [l.strip() for l in s['query'].split('\n') if l.strip() and not l.strip().startswith("'")][:3]
        print(f"  Query: {' | '.join(q_lines)[:150]}")


if __name__ == '__main__':
    main()
