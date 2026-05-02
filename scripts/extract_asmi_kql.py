r"""
ASMI Troubleshooter KQL Extractor.

Reads each .md file in:
  C:\Users\lduan\Downloads\asmi-troubleshooter-package\skills\mssql-dba\kusto-queries\

Extracts KQL queries (handles split ```kusto fences, let+query patterns)
and routes them to the appropriate kql-asmi.yaml under:
  C:\Users\lduan\.copilot\agents\skills\kql-templates\mi\<category>\

Output format matches existing kql-asmi.yaml entries:
  SqlSkills:
  - id: MI-ASMI-<CAT>-<NN>
    Topic: <md filename without ext>
    Source: kusto-queries/<md filename>
    Prompts: [...]
    CustomizedParameters: [ServerName, DatabaseName]
    KustoQueries:
    - TableName: <Mon...>
      ExecutedQuery: |
        ...
"""
import os
import re
import yaml

# ---- Inline helpers (copied from extract_kql.py to avoid argparse side-effect on import) ----

def is_prose(line):
    prose_patterns = [
        r'^#', r'^Find\s+(wiki|related|example|dump)', r'^Related\s+(wiki|ICM)',
        r'^More\s+Example', r'^Detailed\s+steps', r'^The\s+command\s+is',
        r'^Below\s+content', r'^If\s+this\s+query', r'^You\s+could',
        r'^Check\s+the\s+throttling', r'^Similarly,\s+check',
        r'^There\s+was\s+a\s+customer', r'^Is\s+non-SOS', r'^From\s+the\s+result',
        r'^Example\s+issue', r'^Symptom', r'^Investigation\s+steps',
        r'^Confirm\s+OOM', r'^Error\s+code\s+\d+', r'^Table\s+\d+', r'^Query\s+\d+',
        r'^====', r'^目前', r'^导引', r'^sp_configure', r'^GO\s*$', r'^RECONFIGURE',
        r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', r'^https?://',
        r'^\w+\s*\(\s*visualstudio\.com\)', r'^AppName$', r'^ASC$',
    ]
    return any(re.match(p, line, re.IGNORECASE) for p in prose_patterns)


def is_valid_kql(query):
    if len(query) < 20:
        return False
    has_table = bool(re.search(r'\b(Mon\w+|Alr\w+|OutageReasons|SqlFailovers)\b', query))
    starts_with_let = query.strip().startswith('let ')
    if not has_table and not starts_with_let:
        return False
    has_pipe = '|' in query
    if not has_pipe and not (starts_with_let and has_table):
        return False
    lines = query.strip().split('\n')
    kql_lines = sum(1 for l in lines if l.strip().startswith('|') or
                    l.strip().startswith('let ') or
                    re.match(r'^(Mon|Alr|OutageReasons|SqlFailovers)\w+', l.strip()) or
                    l.strip().startswith('//') or
                    l.strip().startswith(')'))
    if kql_lines / max(len(lines), 1) < 0.3:
        return False
    return True


def extract_kql_from_md(content):
    content = re.sub(r'Execute:?\s*\[Web\].*?\n', '\n', content)
    content = re.sub(r'Execute in \[.*?\].*?\n', '\n', content)
    content = re.sub(r'From <https?://[^>]+>\s*', '', content)
    lines = content.split('\n')
    merged_lines = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^```\s*(kusto|kql|csl)?\s*$', stripped):
            in_fence = not in_fence
            continue
        merged_lines.append(line)
    content = '\n'.join(merged_lines)

    lines = content.split('\n')
    queries = []
    current_block = []
    current_lets = []

    def flush_block():
        nonlocal current_block, current_lets
        if not current_block and not current_lets:
            return
        full = '\n'.join(current_lets + current_block).strip()
        if is_valid_kql(full):
            queries.append(full)
        current_block = []
        current_lets = []

    kql_kw = ['where ', 'project ', 'summarize ', 'extend ', 'join ', 'on ',
              'order by', 'sort by', 'take ', 'limit ', 'render ', 'distinct',
              'union ', 'parse ', 'mv-expand', 'make-series', 'top ']

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_block:
                flush_block()
            continue
        if is_prose(stripped):
            if current_block:
                flush_block()
            continue
        if re.match(r'^let\s+\w+\s*=', stripped):
            current_lets.append(stripped)
            continue
        if re.match(r'^(Mon|Alr|OutageReasons|SqlFailovers)\w+', stripped) and not stripped.startswith('//'):
            if current_block:
                flush_block()
            current_block.append(stripped)
            continue
        if stripped.startswith('|') or stripped.startswith('//|'):
            current_block.append(stripped)
            continue
        if re.match(r'^//\s*[\*=\-]{3,}', stripped) or re.match(r'^//\s*[A-Z]\.\d+', stripped):
            if current_block:
                flush_block()
            continue
        if current_block and any(stripped.startswith(kw) or stripped.startswith('| ' + kw) for kw in kql_kw):
            current_block.append(stripped)
            continue
        if current_block and stripped.startswith('//'):
            current_block.append(stripped)
            continue
        if current_block and re.match(r'^[A-Z][a-zA-Z_]+\s*[,]?\s*$', stripped):
            current_block.append(stripped)
            continue
        if current_block and (stripped.startswith(')') or stripped.startswith(') on')):
            current_block.append(stripped)
            continue
        if current_block:
            flush_block()
    flush_block()

    seen = set()
    unique = []
    for q in queries:
        norm = re.sub(r'\s+', ' ', q.strip())
        if norm not in seen:
            seen.add(norm)
            unique.append(q)
    return unique


def parameterize(q):
    pats = [
        (r'LogicalServerName\s*(?:==?|=~|contains)\s*["\'][\w\-\.]+["\']', 'LogicalServerName =~ "{ServerName}"'),
        (r'server_name\s*(?:==?|=~)\s*["\'][\w\-\.]+["\']', 'server_name =~ "{ServerName}"'),
        (r'logical_server_name\s*(?:==?|=~)\s*["\'][\w\-\.]+["\']', 'logical_server_name =~ "{ServerName}"'),
        (r'logical_database_name\s*(?:==?|=~|contains)\s*["\'][\w\-\.]+["\']', 'logical_database_name =~ "{DatabaseName}"'),
        (r'database_name\s*(?:==?|=~|contains)\s*["\'][\w\-\.]+["\']', 'database_name =~ "{DatabaseName}"'),
        (r'SubscriptionId\s*(?:==?|=~)\s*["\'][\w\-]+["\']', 'SubscriptionId =~ "{SubscriptionId}"'),
        (r'(let\s+ServerName\s*=\s*)["\'][\w\-\.]+["\']', r'\1"{ServerName}"'),
        (r'(let\s+srv\s*=\s*)["\'][\w\-\.]+["\']', r'\1"{ServerName}"'),
        (r'(let\s+db\s*=\s*)["\'][\w\-\.]+["\']', r'\1"{DatabaseName}"'),
    ]
    for pat, repl in pats:
        q = re.sub(pat, repl, q)
    return q


def extract_table_name(query):
    for line in query.split('\n'):
        stripped = line.strip()
        if stripped.startswith('let ') or stripped.startswith('//'):
            continue
        m = re.match(r'^(Mon\w+|Alr\w+|OutageReasons|SqlFailovers)', stripped)
        if m:
            return m.group(1)
    tables = re.findall(r'\b(Mon\w+|Alr\w+)', query)
    return tables[0] if tables else 'Unknown'

SRC = r'C:\Users\lduan\Downloads\asmi-troubleshooter-package\skills\mssql-dba\kusto-queries'
OUT_BASE = r'C:\Users\lduan\.copilot\agents\skills\kql-templates\mi'

# ---- Category routing map (md filename -> category target) ----
# Pattern: filename substring (case-insensitive) -> category subpath under OUT_BASE
# Ordering matters: first match wins
ROUTING = [
    # ── Performance subcategories (specific) ──
    ('Memory grant feedback',     'performance/memory'),
    ('Memory Troubleshooting',    'performance/memory'),
    ('Memory.md',                 'performance/memory'),
    ('Memory-optimized object',   'performance/memory'),
    ('In-Memory',                 'performance/memory'),
    ('Investigation memory',      'performance/memory'),
    ('OOM',                       'performance/memory'),
    ('Blocking & Deadlock',       'performance/blocking'),
    ('Blocking.md',               'performance/blocking'),
    ('Deadlock',                  'performance/blocking'),
    ('Lock request',              'performance/blocking'),
    ('Open transaction',          'performance/blocking'),
    ('CPU.md',                    'performance/cpu'),
    ('Resource Status',           'performance/cpu'),
    ('Governance, Quota',         'performance/cpu'),
    ('Fulltext',                  'performance/cpu'),
    ('Query Compile',             'performance/compilation'),
    ('Query Execution',           'performance/queries'),
    ('Execution Stats',           'performance/queries'),
    ('Query All Cluster',         'performance/queries'),
    ('(T-SQL) Check QDS',         'performance/queries'),
    ('MonQueryProcessing',        'performance/queries'),
    ('Query Store',               'performance/query-store'),
    ('GP IO Throttling',          'performance/io-storage'),
    ('GP Storage',                'performance/io-storage'),
    ('IO Latency',                'performance/io-storage'),
    ('IO.md',                     'performance/io-storage'),
    ('Storage (MonSQLXStore',     'performance/io-storage'),
    ('Disk space usage',          'performance/out-of-disk'),
    ('Log size',                  'performance/out-of-disk'),
    ('TempDb',                    'performance/out-of-disk'),
    ('File Size & Table size',    'performance/out-of-disk'),
    ('Wait DB level',             'performance/miscellaneous'),
    ('Wait Type',                 'performance/miscellaneous'),
    ('Performance Counter',       'performance/miscellaneous'),
    ('Performance.md',            'performance/miscellaneous'),
    ('Database Options',          'performance/miscellaneous'),
    ('TDE',                       'performance/miscellaneous'),
    ('Export & Import',           'performance/miscellaneous'),
    ('Get database id',           'performance/miscellaneous'),
    ('MonLogin - most used',      'performance/miscellaneous'),
    ('MonManagement - most used', 'performance/miscellaneous'),
    # ── Availability ──
    ('Availability.md',           'availability'),
    ('Failover',                  'availability'),
    ('Health of replica',         'availability'),
    ('Slow seeding',              'availability'),
    ('Zone-Redundant',            'availability'),
    ('Code Package Version',      'availability/node-health'),
    ('Distributed Transaction',   'availability/node-health'),
    ('Node history status',       'availability/node-health'),
    ('Node-wide info',            'availability/node-health'),
    # ── Backup & Restore (top-level kql-asmi.yaml) ──
    ('Backup',                    'backup-restore'),
    ('Recovery',                  'backup-restore'),
    ('Restore',                   'backup-restore'),
    ('LTR',                       'backup-restore'),
    ('PVS',                       'backup-restore'),
    ('Shrink',                    'backup-restore'),
    ('Storage_Size',              'backup-restore'),
    ('Log Replay',                'backup-restore'),
    # ── Networking (top-level kql-asmi.yaml) ──
    ('Connectivity',              'networking'),
    ('Gateway issue',             'networking'),
    ('Vnet',                      'networking'),
    ('Login failed',              'networking'),
    ('Proxy',                     'networking'),
    ('Linked Server',             'networking'),
    ('Read-scale',                'networking'),
    ('Windows Auth',              'networking'),
    ('AAD authentication',        'networking'),
    ('Tips with AAD',             'networking'),
    ('Tips with Azure Network',   'networking'),
    # ── Replication ──
    ('CDC',                       'replication'),
    ('Replication',               'replication'),
    ('Managed Instance Link',     'replication'),
    # ── General (uncategorized / cross-cutting) ──
    # everything else falls to 'general'
]


def categorize(md_filename):
    """Return (category_path, subdir) where the .md should be routed."""
    for needle, target in ROUTING:
        if needle.lower() in md_filename.lower():
            return target
    return 'general'


def cat_short_name(category_path):
    """Build the short name used in skill IDs."""
    # availability/node-health -> NODE-HEALTH
    # performance/memory -> MEMORY
    # backup-restore -> BACKUP-RESTORE
    # general -> GENERAL
    last = category_path.rstrip('/').split('/')[-1]
    return last.upper()


def build_prompts(topic):
    """Generate 3 prompt phrases for a Topic."""
    return [
        f'MI {topic}',
        f'Managed Instance {topic}',
        f'Investigate {topic}',
    ]


def main():
    # ---- 1. Inventory all .md files in SRC ----
    md_files = sorted(f for f in os.listdir(SRC) if f.endswith('.md'))
    print(f'Source: {SRC}')
    print(f'Total .md files: {len(md_files)}')
    print()

    # ---- 2. Group by target category ----
    by_target = {}
    for fname in md_files:
        target = categorize(fname)
        by_target.setdefault(target, []).append(fname)

    print('Routing:')
    for target in sorted(by_target):
        print(f'  {target}: {len(by_target[target])} files')
    print()

    # ---- 3. Extract & write ----
    grand_added = 0
    grand_skipped_dup = 0
    grand_skipped_empty = 0
    summary = []

    for target, files_in_target in sorted(by_target.items()):
        target_dir = os.path.join(OUT_BASE, target)
        os.makedirs(target_dir, exist_ok=True)
        out_path = os.path.join(target_dir, 'kql-asmi.yaml')

        # Load existing
        existing_skills = []
        existing_queries = set()
        existing_sources = set()
        if os.path.exists(out_path):
            with open(out_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                existing_skills = data.get('SqlSkills', [])
            for s in existing_skills:
                src = s.get('Source', '')
                existing_sources.add(src)
                for kq in s.get('KustoQueries', []):
                    norm = re.sub(r'\s+', ' ', kq.get('ExecutedQuery', '').strip())
                    if norm:
                        existing_queries.add(norm)

        # Compute next ID counter
        cat_short = cat_short_name(target)
        max_id = 0
        for s in existing_skills:
            sid = s.get('id', '')
            m = re.search(rf'MI-ASMI-{re.escape(cat_short)}-(\d+)', sid)
            if m:
                max_id = max(max_id, int(m.group(1)))
        next_id = max_id + 1

        added_for_target = 0
        for fname in files_in_target:
            src_path = os.path.join(SRC, fname)
            source_ref = f'kusto-queries/{fname}'
            if source_ref in existing_sources:
                # Already covered by old extraction — skip silently
                continue
            try:
                with open(src_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                    content = f.read()
            except Exception as e:
                print(f'    ERR reading {fname}: {e}')
                continue

            queries = extract_kql_from_md(content)
            if not queries:
                grand_skipped_empty += 1
                continue

            topic = os.path.splitext(fname)[0]
            for q in queries:
                norm = re.sub(r'\s+', ' ', q.strip())
                if norm in existing_queries:
                    grand_skipped_dup += 1
                    continue
                existing_queries.add(norm)
                table = extract_table_name(q)
                skill = {
                    'id': f'MI-ASMI-{cat_short}-{next_id:02d}',
                    'Topic': topic,
                    'Source': source_ref,
                    'Prompts': build_prompts(topic),
                    'CustomizedParameters': ['ServerName', 'DatabaseName'],
                    'KustoQueries': [{
                        'TableName': table,
                        'ExecutedQuery': parameterize(q),
                    }],
                }
                existing_skills.append(skill)
                next_id += 1
                added_for_target += 1

        # Save back
        if existing_skills:
            with open(out_path, 'w', encoding='utf-8') as f:
                yaml.dump({'SqlSkills': existing_skills}, f,
                          default_flow_style=False, allow_unicode=True,
                          sort_keys=False, width=200)
        summary.append((target, added_for_target, len(existing_skills)))
        grand_added += added_for_target

    # ---- 4. Print summary ----
    print('=== Per-target results ===')
    for target, added, total in sorted(summary):
        flag = ' (NEW)' if added > 0 else ''
        print(f'  {target:35s} +{added:3d} added (total now: {total}){flag}')
    print()
    print(f'Grand total new skills added: {grand_added}')
    print(f'Skipped duplicates: {grand_skipped_dup}')
    print(f'Skipped (no KQL): {grand_skipped_empty}')


if __name__ == '__main__':
    main()
