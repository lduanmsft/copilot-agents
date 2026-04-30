#!/usr/bin/env python3
"""
Fix remaining prompt issues:
1. MI-specific queries (Worker.CL) in DB templates - fix prompt to mention MI context
2. Stale prompts from old invalid TableNames (e.g. "SQL DB now errors")
"""
import re
import os

DB_BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

# Old invalid TableNames whose prompts still reference the old garbage name
STALE_TABLENAME_PATTERNS = {
    'now', 'ago', 'datetime', 'toscalar', 'cross', 'color', 'line', 'table',
    'background', 'margin', 'font', 'web', 'a', 'can', 'do', 'read',
    'should', 'typically', 'This', 'Set', 'WITH',
}

def fix_stale_prompts(yaml_path):
    """Fix prompts that still reference old garbage TableName values."""
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    original = content
    pattern = r'^- id:\s*(DB-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    fixes = 0
    
    for i in range(len(matches) - 1, -1, -1):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(content)
        block = content[start:end]
        sid = matches[i].group(1)
        
        # Get current TableName (should be fixed already)
        tn_m = re.search(r'TableName:\s*(\S+)', block)
        if not tn_m:
            continue
        current_table = tn_m.group(1)
        
        # Check if prompts still mention old garbage names
        prompts_section = re.search(r'Prompts:\s*\n((?:\s*-\s*.+\n)+)', block)
        if not prompts_section:
            continue
        
        prompts_text = prompts_section.group(1)
        new_prompts = prompts_text
        
        for old_name in STALE_TABLENAME_PATTERNS:
            # Check if prompt[0] is like "SQL DB {old_name} errors" or "SQL DB {old_name} activity"
            pattern_p0 = rf'(- SQL DB ){old_name}( \w+)'
            if re.search(pattern_p0, new_prompts, re.IGNORECASE):
                # Replace with table-based description
                table_desc = current_table.replace('Mon', '').replace('Alr', '')
                # Convert CamelCase to space-separated lowercase
                table_desc = re.sub(r'([A-Z])', r' \1', table_desc).strip().lower()
                new_prompts = re.sub(pattern_p0, rf'\g<1>{table_desc}\2', new_prompts, flags=re.IGNORECASE)
                
            # Check prompt[1] like "SQL DB {old_name} column1 column2"
            pattern_p1 = rf'(- SQL DB ){old_name}( \w+)'
            if re.search(pattern_p1, new_prompts, re.IGNORECASE):
                new_prompts = re.sub(pattern_p1, rf'\g<1>{current_table}\2', new_prompts, count=1, flags=re.IGNORECASE)
        
        if new_prompts != prompts_text:
            block_new = block.replace(prompts_text, new_prompts)
            content = content[:start] + block_new + content[end:]
            fixes += 1
            # Show what changed
            old_lines = [l.strip() for l in prompts_text.strip().split('\n')]
            new_lines = [l.strip() for l in new_prompts.strip().split('\n')]
            for o, n in zip(old_lines, new_lines):
                if o != n:
                    print(f"  {sid}: '{o}' -> '{n}'")
    
    if content != original:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return fixes


def fix_mi_in_db_prompts(yaml_path):
    """Add context note for queries that use Worker.CL in DB templates."""
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    original = content
    pattern = r'^- id:\s*(DB-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    fixes = 0
    
    for i in range(len(matches) - 1, -1, -1):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(content)
        block = content[start:end]
        sid = matches[i].group(1)
        
        # Check if query has Worker.CL
        if 'Worker.CL' not in block and 'worker.cl' not in block.lower():
            continue
        
        # Check if prompt already mentions MI
        prompts_section = re.search(r'Prompts:\s*\n((?:\s*-\s*.+\n)+)', block)
        if not prompts_section:
            continue
        prompts_text = prompts_section.group(1)
        
        if 'MI' in prompts_text or 'managed instance' in prompts_text.lower():
            continue
        
        # Fix prompt[0]: add "(MI context)" suffix
        lines = prompts_text.split('\n')
        for j, line in enumerate(lines):
            if line.strip().startswith('- SQL DB'):
                lines[j] = line.rstrip() + ' (MI/GeoDR context)'
                fixes += 1
                print(f"  {sid}: added MI context to prompt")
                break
        
        new_prompts = '\n'.join(lines)
        block_new = block.replace(prompts_text, new_prompts)
        content = content[:start] + block_new + content[end:]
    
    if content != original:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return fixes


def main():
    db_cats = ['availability', 'connectivity', 'css-wiki', 'data-integration',
               'geodr', 'native', 'performance', 'query-store',
               'resource-governance', 'telemetry']
    
    print("=" * 60)
    print("Fix stale prompts (old garbage TableName remnants)")
    print("=" * 60)
    stale_total = 0
    for cat in db_cats:
        yaml_path = os.path.join(DB_BASE, cat, f'{cat}.yaml')
        if os.path.exists(yaml_path):
            n = fix_stale_prompts(yaml_path)
            if n > 0:
                stale_total += n
    print(f"Fixed: {stale_total} stale prompts")
    
    print(f"\n{'='*60}")
    print("Fix MI-specific queries with DB-only prompts")
    print("=" * 60)
    mi_total = 0
    for cat in db_cats:
        yaml_path = os.path.join(DB_BASE, cat, f'{cat}.yaml')
        if os.path.exists(yaml_path):
            n = fix_mi_in_db_prompts(yaml_path)
            if n > 0:
                mi_total += n
    print(f"Fixed: {mi_total} MI-context prompts")
    
    print(f"\nTotal fixes: {stale_total + mi_total}")


if __name__ == '__main__':
    main()
