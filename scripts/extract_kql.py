"""
MI KQL Extractor — Extract KQL queries from TSG repos and generate YAML templates.

Usage:
  python extract_kql.py --repo <repo_path> --category <category_name>
  python extract_kql.py --all   (process all known MI TSG repos)

Handles these KQL patterns in markdown:
  1. ```kusto fences split a single query into fragments → merge them
  2. let variables before query body → merge into one query
  3. "Execute in [Web][Desktop]" prefix → strip and keep KQL
  4. // comments as section markers → preserve as context
  5. Prose text interleaved with KQL → skip prose, keep KQL
"""
import os
import re
import yaml
import json


def extract_kql_from_md(content):
    """Extract complete KQL queries from markdown, handling split code fences and let+query patterns."""
    
    # Step 1: Normalize the content
    # Remove "Execute in [Web] [Desktop] ..." lines
    content = re.sub(r'Execute:?\s*\[Web\].*?\n', '\n', content)
    content = re.sub(r'Execute in \[.*?\].*?\n', '\n', content)
    
    # Remove "From <https://...>" reference lines
    content = re.sub(r'From <https?://[^>]+>\s*', '', content)
    
    # Step 2: Merge split code fences
    # Pattern: text outside fence + ```kusto\n text inside fence \n``` → merge into continuous text
    # Remove ```kusto and ``` markers but keep the content
    lines = content.split('\n')
    merged_lines = []
    in_fence = False
    
    for line in lines:
        stripped = line.strip()
        # Handle opening fence
        if re.match(r'^```\s*(kusto|kql|csl)?\s*$', stripped):
            if in_fence:
                in_fence = False  # closing fence
            else:
                in_fence = True   # opening fence
            continue  # skip the fence marker itself
        merged_lines.append(line)
    
    content = '\n'.join(merged_lines)
    
    # Step 3: Split into query blocks
    # A query block starts with: Mon*, Alr*, let, or a // comment followed by a table name
    lines = content.split('\n')
    queries = []
    current_block = []
    current_lets = []
    
    def flush_block():
        """Save current block as a query if it's valid KQL."""
        nonlocal current_block, current_lets
        if not current_block and not current_lets:
            return
        
        # Combine lets + query body
        full_query_lines = current_lets + current_block
        full_query = '\n'.join(full_query_lines).strip()
        
        if is_valid_kql(full_query):
            queries.append(full_query)
        
        current_block = []
        current_lets = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines - they might separate blocks
        if not stripped:
            # If we have a block with actual query content (not just lets), flush it
            if current_block:
                flush_block()
            continue
        
        # Skip pure prose/headers/links
        if is_prose(stripped):
            if current_block:
                flush_block()
            continue
        
        # Detect let statements - accumulate them
        if re.match(r'^let\s+\w+\s*=', stripped):
            current_lets.append(stripped)
            continue
        
        # Detect table name start (new query)
        if re.match(r'^(Mon|Alr|OutageReasons|SqlFailovers)\w+', stripped) and not stripped.startswith('//'):
            # If we already have a block, flush it first
            if current_block:
                flush_block()
            current_block.append(stripped)
            continue
        
        # Detect pipe continuation
        if stripped.startswith('|') or stripped.startswith('//|'):
            current_block.append(stripped)
            continue
        
        # Detect comment lines that look like section headers (// B.01, // *****)
        if re.match(r'^//\s*[\*=\-]{3,}', stripped) or re.match(r'^//\s*[A-Z]\.\d+', stripped):
            if current_block:
                flush_block()
            continue
        
        # Detect KQL continuation (join, extend, project, where without leading pipe)
        kql_keywords = ['where ', 'project ', 'summarize ', 'extend ', 'join ', 'on ', 
                        'order by', 'sort by', 'take ', 'limit ', 'render ', 'distinct',
                        'union ', 'parse ', 'mv-expand', 'make-series', 'top ']
        if current_block and any(stripped.startswith(kw) or stripped.startswith('| ' + kw) for kw in kql_keywords):
            current_block.append(stripped)
            continue
        
        # Detect inline comment continuation
        if current_block and stripped.startswith('//'):
            current_block.append(stripped)
            continue
        
        # Detect closing parts of a query (things like: FailoverCount, IsNodeDownOrUp, etc.)
        if current_block and re.match(r'^[A-Z][a-zA-Z_]+\s*[,]?\s*$', stripped):
            current_block.append(stripped)
            continue
        
        # Detect ) on ... for join closings
        if current_block and (stripped.startswith(')') or stripped.startswith(') on')):
            current_block.append(stripped)
            continue
        
        # Otherwise, it's likely prose - flush current block
        if current_block:
            flush_block()
    
    # Don't forget the last block
    flush_block()
    
    # Deduplicate
    seen = set()
    unique = []
    for q in queries:
        normalized = re.sub(r'\s+', ' ', q.strip())
        if normalized not in seen:
            seen.add(normalized)
            unique.append(q)
    
    return unique


def is_prose(line):
    """Check if a line is prose/documentation rather than KQL."""
    prose_patterns = [
        r'^#',                          # Markdown header
        r'^Find\s+(wiki|related|example|dump)',  # Reference text
        r'^Related\s+(wiki|ICM)',
        r'^More\s+Example',
        r'^Detailed\s+steps',
        r'^The\s+command\s+is',
        r'^Below\s+content',
        r'^If\s+this\s+query',
        r'^You\s+could',
        r'^Check\s+the\s+throttling',
        r'^Similarly,\s+check',
        r'^There\s+was\s+a\s+customer',
        r'^Is\s+non-SOS',
        r'^From\s+the\s+result',
        r'^Example\s+issue',
        r'^Symptom',
        r'^Investigation\s+steps',
        r'^Confirm\s+OOM',
        r'^Error\s+code\s+\d+',
        r'^Table\s+\d+',
        r'^Query\s+\d+',
        r'^====',
        r'^目前',
        r'^导引',
        r'^sp_configure',
        r'^GO\s*$',
        r'^RECONFIGURE',
        r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}',  # Timestamp lines
        r'^https?://',                  # URLs
        r'^\w+\s*\(\s*visualstudio\.com\)',  # Wiki links
        r'^AppName$',                   # Stray column name
        r'^ASC$',                       # Stray abbreviation
    ]
    return any(re.match(p, line, re.IGNORECASE) for p in prose_patterns)


def is_valid_kql(query):
    """Check if a string is a valid/complete KQL query."""
    if len(query) < 20:
        return False
    
    # Must reference at least one known table or start with let
    has_table = bool(re.search(r'\b(Mon\w+|Alr\w+|OutageReasons|SqlFailovers)\b', query))
    starts_with_let = query.strip().startswith('let ')
    
    if not has_table and not starts_with_let:
        return False
    
    # Must have at least one pipe operator or be a let+table combo
    has_pipe = '|' in query
    if not has_pipe and not (starts_with_let and has_table):
        return False
    
    # Must not be mostly prose (more than 50% non-KQL words)
    # Simple heuristic: check ratio of pipe operators to total lines
    lines = query.strip().split('\n')
    kql_lines = sum(1 for l in lines if l.strip().startswith('|') or 
                    l.strip().startswith('let ') or 
                    re.match(r'^(Mon|Alr|OutageReasons|SqlFailovers)\w+', l.strip()) or
                    l.strip().startswith('//') or
                    l.strip().startswith(')'))
    
    if kql_lines / max(len(lines), 1) < 0.3:
        return False
    
    return True


def extract_kql_from_ipynb(filepath):
    """Extract KQL from Jupyter notebook cells."""
    queries = []
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            nb = json.load(f)
        for cell in nb.get('cells', []):
            source = ''.join(cell.get('source', []))
            if not any(t in source for t in ['Mon', 'Alr']):
                continue
            # Try %%kql magic blocks
            kql_blocks = re.findall(r'%%kql\s*\n(.*?)(?:\n\n|\Z)', source, re.DOTALL)
            for block in kql_blocks:
                if is_valid_kql(block.strip()):
                    queries.append(block.strip())
            # Try code cells with direct KQL
            if cell.get('cell_type') == 'code' and not kql_blocks:
                if '| where' in source and any(t in source for t in ['Mon', 'Alr']):
                    clean = re.sub(r'%%\w+\s*\n?', '', source).strip()
                    if is_valid_kql(clean):
                        queries.append(clean)
    except Exception as e:
        print(f"  Warning: Error reading {filepath}: {e}")
    return queries


def parameterize(q):
    """Replace hardcoded server/DB names with placeholders."""
    patterns = [
        (r'LogicalServerName\s*(?:==?|=~|contains)\s*["\'][\w\-\.]+["\']', 'LogicalServerName =~ "{ServerName}"'),
        (r'server_name\s*(?:==?|=~)\s*["\'][\w\-\.]+["\']', 'server_name =~ "{ServerName}"'),
        (r'logical_server_name\s*(?:==?|=~)\s*["\'][\w\-\.]+["\']', 'logical_server_name =~ "{ServerName}"'),
        (r'logical_database_name\s*(?:==?|=~|contains)\s*["\'][\w\-\.]+["\']', 'logical_database_name =~ "{DatabaseName}"'),
        (r'database_name\s*(?:==?|=~|contains)\s*["\'][\w\-\.]+["\']', 'database_name =~ "{DatabaseName}"'),
        (r'SubscriptionId\s*(?:==?|=~)\s*["\'][\w\-]+["\']', 'SubscriptionId =~ "{SubscriptionId}"'),
        # let variable assignments with hardcoded server names
        (r'(let\s+ServerName\s*=\s*)["\'][\w\-\.]+["\']', r'\1"{ServerName}"'),
        (r'(let\s+srv\s*=\s*)["\'][\w\-\.]+["\']', r'\1"{ServerName}"'),
        (r'(let\s+db\s*=\s*)["\'][\w\-\.]+["\']', r'\1"{DatabaseName}"'),
    ]
    for pat, repl in patterns:
        q = re.sub(pat, repl, q)
    return q


def extract_table_name(query):
    """Extract the primary table name from a KQL query."""
    # First non-let, non-comment line that starts with a table name
    for line in query.split('\n'):
        stripped = line.strip()
        if stripped.startswith('let ') or stripped.startswith('//'):
            continue
        match = re.match(r'^(Mon\w+|Alr\w+|OutageReasons|SqlFailovers)', stripped)
        if match:
            return match.group(1)
    # Fallback: find any table reference
    tables = re.findall(r'\b(Mon\w+|Alr\w+)', query)
    return tables[0] if tables else 'Unknown'


def sanitize(name):
    return re.sub(r'[^\w\-]', '_', name.replace(' ', '_')).strip('_')


# ============================================================================
# Main
# ============================================================================

# Known MI TSG repos
tsg_repos = {
    'backup-restore': r'C:\Users\lduan\repos\mi-tsg\TSG-SQL-MI-BackupRestore',
    'performance': r'C:\Users\lduan\repos\mi-tsg\TSG-SQL-MI-Performance',
    'availability': r'C:\Users\lduan\repos\mi-tsg\TSG-SQL-MI-Availability',
    'networking': r'C:\Users\lduan\repos\mi-tsg\TSG-SQL-MI-Networking',
    'replication': r'C:\Users\lduan\repos\mi-tsg\TSG-SQL-MI-TransactionalReplication',
}

out_base = r'C:\Users\lduan\.copilot\agents\skills\kql-templates\mi'

# ---- Parse arguments ----
import sys
import argparse

parser = argparse.ArgumentParser(description='Extract KQL from MI TSG repos')
parser.add_argument('--repo', type=str, help='Path to a single TSG repo')
parser.add_argument('--category', type=str, help='Category name for the YAML output')
parser.add_argument('--all', action='store_true', help='Process all known MI TSG repos')
args = parser.parse_args()

if args.repo and args.category:
    repos_to_process = {args.category: args.repo}
elif args.all:
    repos_to_process = tsg_repos
else:
    print("Usage: python extract_kql.py --repo <path> --category <name>")
    print("       python extract_kql.py --all")
    sys.exit(1)

# ---- Extract from TSG repos ----
stats = {}

for cat, repo_path in repos_to_process.items():
    cat_dir = os.path.join(out_base, cat)
    # Output to kql-tsg.yaml (was: <cat>.yaml — renamed to clarify provenance)
    existing_yaml_path = os.path.join(cat_dir, 'kql-tsg.yaml')
    
    # Load existing
    existing_skills = []
    existing_queries = set()
    if os.path.exists(existing_yaml_path):
        with open(existing_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data and 'SqlSkills' in data:
                existing_skills = data['SqlSkills']
                for skill in existing_skills:
                    for kq in skill.get('KustoQueries', []):
                        normalized = re.sub(r'\s+', ' ', kq.get('ExecutedQuery', '').strip())
                        existing_queries.add(normalized)
    
    # Next skill ID
    max_id = 0
    for skill in existing_skills:
        match = re.search(r'-(\d+)$', skill.get('id', ''))
        if match:
            max_id = max(max_id, int(match.group(1)))
    skill_id = max_id + 1
    
    new_count = 0
    repo_name = os.path.basename(repo_path)
    
    for root, dirs, files in os.walk(repo_path):
        for fname in sorted(files):
            if not (fname.endswith('.md') or fname.endswith('.ipynb')):
                continue
            filepath = os.path.join(root, fname)
            if os.path.getsize(filepath) < 200:
                continue
            
            rel_path = os.path.relpath(filepath, repo_path).replace('\\', '/')
            topic = os.path.splitext(fname)[0]
            
            if fname.endswith('.md'):
                with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
                    content = f.read()
                queries = extract_kql_from_md(content)
            else:
                queries = extract_kql_from_ipynb(filepath)
            
            for q in queries:
                normalized = re.sub(r'\s+', ' ', q.strip())
                if normalized in existing_queries:
                    continue
                existing_queries.add(normalized)
                
                table = extract_table_name(q)
                skill = {
                    'id': f'MI-{sanitize(cat)}-{skill_id}',
                    'Topic': topic,
                    'Source': f'{repo_name}/{rel_path}',
                    'Prompts': [f'MI {topic}', f'Managed Instance {topic}'],
                    'CustomizedParameters': ['ServerName', 'DatabaseName'],
                    'KustoQueries': [{
                        'TableName': table,
                        'ExecutedQuery': parameterize(q)
                    }]
                }
                existing_skills.append(skill)
                skill_id += 1
                new_count += 1
    
    # Save merged
    if existing_skills:
        yaml_data = {'SqlSkills': existing_skills}
        with open(existing_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=200)
    
    stats[f'tsg-{cat}'] = new_count
    print(f'  {cat}: +{new_count} new from TSG (total: {len(existing_skills)})')

# ---- Summary ----
print("\n=== Summary ===")
total = sum(stats.values())
for cat, count in stats.items():
    print(f'  {cat}: {count} skills')
print(f'Total: {total} skills')
