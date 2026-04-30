#!/usr/bin/env python3
"""
Fix P0 (wrong-table-in-prompt) and P1 (URL-encoded prompts) in MI/DB YAML templates.
"""
import re
import os
import urllib.parse

MI_BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\mi")
DB_BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

# P0: Wrong table in prompt — manually verified corrections
P0_FIXES = {
    # sid: (yaml_dir, yaml_file, wrong_text, correct_text)
    'MI-availability-316': (MI_BASE, 'availability/availability.yaml', None, None),  # "monitor" false positive, skip
    'MI-networking-130': (MI_BASE, 'networking/networking.yaml', 'monazureactivedirservice', 'MonAzureActivDirService'),
    'MI-performance-294': (MI_BASE, 'performance/performance.yaml', None, None),  # needs manual check
    'MI-performance-313': (MI_BASE, 'performance/performance.yaml', None, None),  # needs manual check
    'DB-telemetry-94': (DB_BASE, 'telemetry/telemetry.yaml', None, None),  # "moniker" false positive, skip
}


def fix_url_encoded_prompts(yaml_path):
    """Decode URL-encoded characters in Prompts fields."""
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    original = content
    fixes = 0
    
    # Find all Prompts sections and decode URL-encoded chars in prompt lines
    def decode_prompt_line(match):
        nonlocal fixes
        line = match.group(0)
        if '%2D' in line or '%2d' in line or '%3A' in line or '%3a' in line or '%2C' in line or '%2c' in line or '%28' in line or '%29' in line:
            # Decode common URL encodings
            decoded = line
            decoded = decoded.replace('%2D', '-').replace('%2d', '-')
            decoded = decoded.replace('%3A', ':').replace('%3a', ':')
            decoded = decoded.replace('%2C', ',').replace('%2c', ',')
            decoded = decoded.replace('%28', '(').replace('%28', '(')
            decoded = decoded.replace('%29', ')').replace('%29', ')')
            decoded = decoded.replace('%20', ' ').replace('%20', ' ')
            decoded = decoded.replace('%5B', '[').replace('%5b', '[')
            decoded = decoded.replace('%5D', ']').replace('%5d', ']')
            if decoded != line:
                fixes += 1
                return decoded
        return line
    
    # Match prompt lines: "  - some text with %2D encoding"
    content = re.sub(r'^\s+-\s+.*%[0-9A-Fa-f]{2}.*$', decode_prompt_line, content, flags=re.MULTILINE)
    
    if content != original:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return fixes


def fix_wrong_table_prompts(yaml_path, sid, wrong_table, correct_table):
    """Fix a specific skill's prompt that mentions the wrong table."""
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Find the skill block
    pattern = rf'^- id:\s*{re.escape(sid)}'
    m = re.search(pattern, content, re.MULTILINE)
    if not m:
        print(f"  SKIP: {sid} not found in {yaml_path}")
        return False
    
    start = m.start()
    # Find next skill
    next_m = re.search(r'^- id:\s*', content[start+1:], re.MULTILINE)
    end = start + 1 + next_m.start() if next_m else len(content)
    block = content[start:end]
    
    # Replace wrong table reference in prompts
    fixed_block = re.sub(re.escape(wrong_table), correct_table, block, flags=re.IGNORECASE)
    
    if fixed_block != block:
        content = content[:start] + fixed_block + content[end:]
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  FIXED: {sid} prompt: {wrong_table} -> {correct_table}")
        return True
    else:
        print(f"  SKIP: {sid} no change needed")
        return False


def main():
    print("=" * 60)
    print("P0: Fix wrong-table-in-prompt")
    print("=" * 60)
    
    p0_fixed = 0
    # MI-networking-130: prompt says "monazureactivedirservice" but TableName is "MonAzureActivDirService" — case mismatch only, actually OK
    # MI-performance-294: prompt mentions "monsqlsystemhealth" but TableName is "MonRedirector" — REAL ERROR
    # MI-performance-313: prompt mentions "monwiqueryparamdata" but TableName is "MonSqlRgHistory" — REAL ERROR
    
    # Fix MI-performance-294
    yaml_path = os.path.join(MI_BASE, 'performance', 'performance.yaml')
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Find MI-performance-294 and fix prompt
        m = re.search(r'^- id:\s*MI-performance-294', content, re.MULTILINE)
        if m:
            start = m.start()
            next_m = re.search(r'^- id:\s*MI-', content[start+1:], re.MULTILINE)
            end = start + 1 + next_m.start() if next_m else len(content)
            block = content[start:end]
            
            # Get actual TableName
            tn_m = re.search(r'TableName:\s*(\S+)', block)
            actual_table = tn_m.group(1) if tn_m else 'Unknown'
            
            # Fix: replace monsqlsystemhealth with actual table in prompts
            fixed = block.replace('MonSQLSystemHealth', actual_table).replace('monsqlsystemhealth', actual_table.lower())
            # Also update prompt text to reference correct table
            if fixed != block:
                content = content[:start] + fixed + content[end:]
                p0_fixed += 1
                print(f"  FIXED: MI-performance-294 prompt -> {actual_table}")
        
        # Find MI-performance-313 and fix prompt
        m = re.search(r'^- id:\s*MI-performance-313', content, re.MULTILINE)
        if m:
            start = m.start()
            next_m = re.search(r'^- id:\s*MI-', content[start+1:], re.MULTILINE)
            end = start + 1 + next_m.start() if next_m else len(content)
            block = content[start:end]
            
            tn_m = re.search(r'TableName:\s*(\S+)', block)
            actual_table = tn_m.group(1) if tn_m else 'Unknown'
            
            fixed = block.replace('MonWiQueryParamData', actual_table).replace('monwiqueryparamdata', actual_table.lower())
            if fixed != block:
                content = content[:start] + fixed + content[end:]
                p0_fixed += 1
                print(f"  FIXED: MI-performance-313 prompt -> {actual_table}")
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"\nP0 fixes applied: {p0_fixed}")
    
    print("\n" + "=" * 60)
    print("P1: Decode URL-encoded prompts")
    print("=" * 60)
    
    p1_total = 0
    
    # MI categories
    mi_cats = ['availability', 'backup-restore', 'general', 'networking', 'performance', 'replication']
    for cat in mi_cats:
        yaml_path = os.path.join(MI_BASE, cat, f'{cat}.yaml')
        if os.path.exists(yaml_path):
            n = fix_url_encoded_prompts(yaml_path)
            if n > 0:
                print(f"  MI/{cat}: decoded {n} prompts")
                p1_total += n
    
    # DB categories
    db_cats = ['availability', 'connectivity', 'css-wiki', 'data-integration',
               'geodr', 'native', 'performance', 'query-store',
               'resource-governance', 'telemetry']
    for cat in db_cats:
        yaml_path = os.path.join(DB_BASE, cat, f'{cat}.yaml')
        if os.path.exists(yaml_path):
            n = fix_url_encoded_prompts(yaml_path)
            if n > 0:
                print(f"  DB/{cat}: decoded {n} prompts")
                p1_total += n
    
    print(f"\nP1 fixes applied: {p1_total}")
    print(f"\n{'='*60}")
    print(f"Total: P0={p0_fixed}, P1={p1_total}")
    print("=" * 60)


if __name__ == '__main__':
    main()
