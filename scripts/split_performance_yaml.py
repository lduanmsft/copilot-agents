#!/usr/bin/env python3
"""
Split performance.yaml into per-category YAML files.
Categories aligned with SQLLivesiteAgents Performance skills:
  cpu, queries, memory, blocking, query-store, compilation, 
  out-of-disk, miscellaneous, pause-resume, node-health, resource-governance
"""

import yaml
import os
import re
from collections import defaultdict

INPUT_FILE = r"c:\Users\lduan\.copilot\agents\skills\kql-templates\sqldb\performance\performance.yaml"
OUTPUT_DIR = r"c:\Users\lduan\.copilot\agents\skills\kql-templates\sqldb\performance"

# ── Classification rules: (priority order, first match wins) ──
# Each rule: (category, match_function)
# match_function receives (skill_dict) and returns True/False

def get_all_text(skill):
    """Combine all searchable text from a skill entry."""
    parts = []
    parts.append(skill.get('Topic', ''))
    parts.append(skill.get('Source', ''))
    for p in skill.get('Prompts', []):
        parts.append(str(p))
    for kq in skill.get('KustoQueries', []):
        parts.append(kq.get('TableName', ''))
        parts.append(kq.get('ExecutedQuery', ''))
    return ' '.join(parts).lower()

def get_tables(skill):
    """Get all table names from KustoQueries."""
    tables = set()
    for kq in skill.get('KustoQueries', []):
        tn = kq.get('TableName', '')
        if tn:
            tables.add(tn.lower())
        # Also extract tables from query text
        query = kq.get('ExecutedQuery', '')
        if query:
            # Match table names at start of lines or after join/union
            for m in re.findall(r'\b(Mon\w+)\b', query, re.IGNORECASE):
                tables.add(m.lower())
    return tables

RULES = []

# ── Pause/Resume (Serverless) ──
def is_pause_resume(skill):
    txt = get_all_text(skill)
    topic = skill.get('Topic', '').lower()
    return any(k in txt for k in [
        'pause', 'resume', 'deactivat', 'activat', 'serverless',
        'proactive-pause', 'autopause', 'auto_pause',
    ]) and 'ppbot-038' not in topic  # IO RG delay is not pause/resume
RULES.append(('pause-resume', is_pause_resume))

# ── Query Store / QDS ──
def is_query_store(skill):
    txt = get_all_text(skill)
    topic = skill.get('Topic', '').lower()
    return any(k in txt for k in [
        'query store', 'query_store', 'qds', 'querystore',
        'qp-015', 'qp015', 'force_last_good', 'aprc',
    ]) or 'query-store' in topic or 'aprc' in topic
RULES.append(('query-store', is_query_store))

# ── Blocking / Deadlock / Locking ──
def is_blocking(skill):
    txt = get_all_text(skill)
    tables = get_tables(skill)
    return (any(k in txt for k in [
        'deadlock', 'blocking', 'latch contention', 'lck_m_',
        'lock escalat', 'lead blocker', 'blocked',
    ]) or 'latch-contention' in skill.get('Topic', '').lower()
    ) and 'spinlock' not in txt  # spinlock is different
RULES.append(('blocking', is_blocking))

# ── Compilation ──
def is_compilation(skill):
    txt = get_all_text(skill)
    tables = get_tables(skill)
    return (any(k in txt for k in [
        'compil', 'query timeout during compilation',
        'monqueryprocessing', 'monwiqueryparamdata',
        'failed_compilation', 'compile_cpu',
    ]) or 'monqueryprocessing' in tables
    or 'monwiqueryparamdata' in tables)
RULES.append(('compilation', is_compilation))

# ── Memory ──
def is_memory(skill):
    txt = get_all_text(skill)
    topic = skill.get('Topic', '').lower()
    tables = get_tables(skill)
    memory_keywords = [
        'memory', 'oom', 'overbooking', 'overbook', 'overcommit',
        'memoryclerk', 'buffer pool', 'bufferpool', 'bpe',
        'memory_clerk', 'memory grant', 'memory_grant',
        'heap leak', 'heap_leak', 'memory leak', 'memory_leak',
        'mmsop', 'mm0', 'memorymgr', 'memorymanager',
        'schemamgr', 'sql_clr', 'sqlclr',
        'sos_target', 'resource_monitor', 'resourcemonitor',
        'internal-cache-shrinking',
    ]
    memory_tables = ['mondmosmemoryclerks', 'monresourcemonitor']
    return (any(k in txt for k in memory_keywords)
            or any(t in tables for t in memory_tables)
            or any(k in topic for k in ['mm0', 'mmsop', 'memory', 'overbooking', 'overcommit', 'leak']))
RULES.append(('memory', is_memory))

# ── Out-of-Disk / Storage / Space ──
def is_out_of_disk(skill):
    txt = get_all_text(skill)
    topic = skill.get('Topic', '').lower()
    return any(k in txt for k in [
        'out of space', 'out-of-space', 'outofspace', 'disk full',
        'tempdb full', 'tempdb-out', 'quota', 'directory quota',
        'disk usage', 'disk space', 'file size', 'file_size',
        'max size', 'max_size', 'storage account',
        'xstore', 'xio', 'blob tier', 'fileshare',
        'pfs', 'dynamic-file-allocation', 'dfa',
    ]) or any(k in topic for k in [
        'tsgpfs', 'tsgrs', 'tsgrg', 'ppbot-009', 'ppbot-037',
        'ppbot-039', 'ppbot-040', 'ppbot-062', 'perfts016',
        'storage', 'pp0006', 'backfill-data',
    ])
RULES.append(('out-of-disk', is_out_of_disk))

# ── CPU ──
def is_cpu(skill):
    txt = get_all_text(skill)
    topic = skill.get('Topic', '').lower()
    tables = get_tables(skill)
    cpu_keywords = [
        'cpu usage', 'cpu spike', 'cpu pressure', 'high cpu',
        'cpu troubleshoot', 'cpu tab', 'cpu imbalance',
        'pegged core', 'single core', 'singlecore',
        'scheduler imbalance', 'scheduler_data',
        'kernel_load', 'kernel mode cpu', 'kernel cpu',
        'system pool cpu', 'user pool cpu',
        'cpu_percent', 'avg_cpu_percent', 'cpu_cap',
        'globalcapcpu', 'cpu rg', 'sosrg',
        'runnable_tasks', 'signal_wait',
        'profiler', 'xperf',
    ]
    cpu_topics = [
        'cpu0', 'cpu1', 'singlecore', 'ppbot-049',
        'azureprofiler', 'high_cpu', 'perfts004',
        'sosrg', 'pendingimbalance',
    ]
    return (any(k in txt for k in cpu_keywords)
            or any(k in topic for k in cpu_topics)
            or ('monrgload' in tables and 'cpu' in txt))
RULES.append(('cpu', is_cpu))

# ── Node Health / XEvent / Scheduler / Non-yielding ──
def is_node_health(skill):
    txt = get_all_text(skill)
    topic = skill.get('Topic', '').lower()
    return any(k in txt for k in [
        'non-yielding', 'nonyielding', 'dump summary',
        'xe0', 'xevent', 'stuck dispatcher',
        'dmv collector', 'worker thread', 'worker_thread',
        'failover', 'restart', 'why-failover',
        'node health', 'node_health',
    ]) or any(k in topic for k in [
        'xe0', 'ppbot-015', 'ppbot-016', 'ppbot-026',
        'ppbot-024', 'ppbot-043',
    ])
RULES.append(('node-health', is_node_health))

# ── Queries (top queries, query perf, wait types) ──
def is_queries(skill):
    txt = get_all_text(skill)
    tables = get_tables(skill)
    query_tables = ['monwiqdsexecstats', 'monwiqdsexecstatsreplica',
                    'monwiqdsexecstatsagg', 'monwiqdswaitstats']
    return (any(t in tables for t in query_tables)
            or any(k in txt for k in [
                'top queries', 'top cpu queries', 'top wait',
                'query_hash', 'query hash', 'query performance',
                'query slowness', 'exec_type', 'execution_count',
                'wait_category', 'wait category',
                'logical_reads', 'logical reads',
                'query antipattern', 'plan regression',
            ]))
RULES.append(('queries', is_queries))

# ── Resource Governance (catch remaining RG/PPBOT/provisioning) ──
def is_resource_governance(skill):
    txt = get_all_text(skill)
    topic = skill.get('Topic', '').lower()
    tables = get_tables(skill)
    return (any(k in txt for k in [
        'resource govern', 'resource_govern', 'rgdd',
        'slo_name', 'dtu_limit', 'service tier',
        'vectorindex', 'vector index',
    ]) or any(k in topic for k in [
        'rgdd', 'ppbot', 'ppcap', 'pptsg', 'configtsg',
        'vectorindex',
    ]) or 'monsqlrghistory' in tables)
RULES.append(('resource-governance', is_resource_governance))

# ── Fulltext ──
def is_fulltext(skill):
    txt = get_all_text(skill)
    topic = skill.get('Topic', '').lower()
    return any(k in txt for k in ['fulltext', 'full text', 'fdhost', 'full-text'])
RULES.append(('fulltext', is_fulltext))

# ── Corruption / DBCC ──
def is_corruption(skill):
    txt = get_all_text(skill)
    return any(k in txt for k in [
        'corruption', 'dbcc', 'checkdb', '8630', '8646',
        '823', '824', '1117', 'rbpex',
    ])
RULES.append(('corruption', is_corruption))


def classify_skill(skill):
    """Classify a skill into a category. First match wins."""
    for category, match_fn in RULES:
        try:
            if match_fn(skill):
                return category
        except Exception:
            pass
    return 'miscellaneous'


def main():
    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    skills = data.get('SqlSkills', [])
    print(f"Total skills: {len(skills)}")

    # Classify
    categorized = defaultdict(list)
    for skill in skills:
        cat = classify_skill(skill)
        categorized[cat].append(skill)

    # Print summary
    print("\n=== Classification Summary ===")
    for cat in sorted(categorized.keys()):
        items = categorized[cat]
        print(f"  {cat}: {len(items)} skills")
        # Show sample topics
        topics = set(s.get('Topic', '?') for s in items[:10])
        for t in sorted(topics)[:5]:
            print(f"    - {t}")
        if len(topics) > 5:
            print(f"    ... and {len(set(s.get('Topic','?') for s in items)) - 5} more topics")

    # Write files
    print(f"\n=== Writing files to {OUTPUT_DIR} ===")
    for cat, items in sorted(categorized.items()):
        filename = f"{cat}.yaml"
        filepath = os.path.join(OUTPUT_DIR, filename)
        out_data = {'SqlSkills': items}
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(out_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=200)
        print(f"  Wrote {filepath} ({len(items)} skills)")

    # Rename original
    backup = INPUT_FILE + '.bak'
    if not os.path.exists(backup):
        os.rename(INPUT_FILE, backup)
        print(f"\n  Original renamed to {backup}")
    else:
        print(f"\n  Backup already exists at {backup}, original not renamed")

    print("\nDone!")


if __name__ == '__main__':
    main()
