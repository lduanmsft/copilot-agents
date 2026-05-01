"""Fix remaining duplicate LogicalServerName filters in MI kql-livesite.yaml files."""
import os
import re

MI_BASE = r"c:\Users\lduan\.copilot\agents\skills\kql-templates\mi\performance"

CATEGORIES = [
    "cpu", "queries", "blocking", "memory", "query-store",
    "compilation", "out-of-disk", "miscellaneous", "sqlos"
]

def fix_duplicate_server_filter(content: str) -> str:
    """Remove duplicate LogicalServerName =~ '{ServerName}' from consecutive where clauses."""
    lines = content.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        if i > 0:
            prev = result[-1] if result else ''
            # Check if both current and previous lines have LogicalServerName filter in where clauses
            if ("LogicalServerName =~ '{ServerName}'" in line and 
                "LogicalServerName =~ '{ServerName}'" in prev and
                '| where' in line):
                # Remove from current line — the previous where already has it
                # Handle: | where LogicalServerName =~ '{ServerName}' and database_name =~ ...
                fixed = line.replace("LogicalServerName =~ '{ServerName}' and ", "")
                # Handle: | where LogicalServerName =~ '{ServerName}'  (standalone, no 'and')
                if "LogicalServerName =~ '{ServerName}'" in fixed and fixed.strip() == "| where LogicalServerName =~ '{ServerName}'":
                    # Skip this line entirely — it's redundant
                    continue
                result.append(fixed)
                continue
        result.append(line)
    
    return '\n'.join(result)


fixed_count = 0
for category in CATEGORIES:
    for fname in ['investigation.yaml', 'kql-livesite.yaml']:
        fpath = os.path.join(MI_BASE, category, fname)
        if not os.path.exists(fpath):
            continue
        
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed = fix_duplicate_server_filter(content)
        
        if fixed != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            # Count how many lines changed
            diff = sum(1 for a, b in zip(content.split('\n'), fixed.split('\n')) if a != b)
            print(f"[FIXED] {category}/{fname} — {diff} lines")
            fixed_count += diff
        else:
            print(f"[OK] {category}/{fname}")

print(f"\nTotal lines fixed: {fixed_count}")
