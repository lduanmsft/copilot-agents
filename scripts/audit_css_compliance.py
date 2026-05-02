"""
Scan all MI investigation.yaml files for CSS-forbidden actions.

CSS can ONLY:
  - Run Kusto KQL read-only queries
  - Identify root cause
  - Escalate to other teams
  - Generate RCA reports

CSS CANNOT:
  - JIT (Just-In-Time access / 提权)
  - CAS commands (Cluster Admin Shell)
  - PowerShell on nodes / SSH / RDP
  - kill / restart / reboot processes
  - T-SQL writes (ALTER/DROP/UPDATE/sp_configure/TRACE FLAG)
  - Configuration changes (SLO update / TDE rotate / cert reset)
  - Debugger / WinDbg / dump trigger
"""
import os
import re
import yaml

BASE = r'C:\Users\lduan\.copilot\agents\skills\kql-templates\mi'

# Patterns to flag (case-insensitive)
FORBIDDEN_PATTERNS = [
    (r'\bJIT\b', 'JIT (proviledged access)'),
    (r'\bCAS\b(?!\w)', 'CAS commands'),
    (r'\bcluster\s*admin', 'cluster admin'),
    (r'\bnode-?level\s*command', 'node-level command'),
    (r'\bpowershell\b', 'PowerShell'),
    (r'\b(?:Enter-PSSession|Invoke-Command|Stop-Process|Restart-Service|Start-Process|Get-Process)\b', 'PowerShell cmdlet'),
    (r'\b(?:ssh|rdp)\b', 'SSH/RDP'),
    (r'\bkill\s+(?:fabricdns|sql|process|task)', 'kill process'),
    (r'\brestart\s+(?:containerd|service|server|node|sql)', 'restart service/node'),
    (r'\breboot\b', 'reboot'),
    (r'\bsp_configure\b', 'sp_configure (config change)'),
    (r'\bDBCC\s+TRACE(?:ON|OFF)\b', 'DBCC TRACEON/OFF'),
    (r'\bALTER\s+(?:DATABASE|SERVER|SYSTEM|INDEX)', 'T-SQL ALTER (write)'),
    (r'\bDROP\s+(?:TABLE|INDEX|DATABASE)', 'T-SQL DROP (write)'),
    (r'\bUPDATE\s+(?:Mon|Alr|sys\.)', 'T-SQL UPDATE on system'),
    (r'\bDELETE\s+FROM\s+(?:Mon|Alr|sys\.)', 'T-SQL DELETE on system'),
    (r'\bdump\s+trigger', 'dump trigger'),
    (r'\b(?:windbg|WinDbg|debugger\s+attach)', 'debugger'),
    (r'\brotate\s+(?:cert|certificate|key|tde)', 'rotate cert/key'),
    (r'\b(?:enable|disable)\s+job\b', 'enable/disable job'),
    (r'\bchange\s+slo\b', 'change SLO (config)'),
    (r'\btde\s+rotat', 'TDE rotation'),
    (r'\bAKV\s+(?:rotat|reset|update)', 'AKV rotate/reset'),
    (r'\bdrain\s+node\b', 'drain node'),
    (r'\bfailover\s+(?:trigger|initiate)', 'manual failover trigger'),
    (r'\bmove[-\s]?replica', 'move replica'),
    (r'\bRECONFIGURE\b', 'RECONFIGURE (config write)'),
]


def scan_file(filepath):
    """Return list of (line_no, line_content, matched_pattern) tuples."""
    findings = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for lineno, line in enumerate(lines, 1):
        # Skip pure-comment lines that are part of the CSS scope declaration
        # (they describe what's forbidden — we don't want to flag those as findings)
        # Heuristic: if line is in the first 30 lines and contains "forbidden" / "CSSScope" / "DO NOT VIOLATE",
        # treat as policy text, skip.
        if lineno < 35 and ('CSSScope' in line or 'forbidden:' in line or 'DO NOT VIOLATE' in line or '禁止' in line):
            continue
        for pat, label in FORBIDDEN_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                # ignore the line if it already says CSS DO NOT or similar warning
                if re.search(r'CSS\s*(?:DO\s*NOT|cannot|not allowed|css_warning|css_note|forbidden)', line, re.IGNORECASE):
                    continue
                findings.append((lineno, line.rstrip(), label))
                break  # one finding per line
    return findings


def main():
    files = []
    for root, dirs, fs in os.walk(BASE):
        for f in fs:
            if f == 'investigation.yaml':
                files.append(os.path.join(root, f))
    files.sort()

    print(f'Scanning {len(files)} investigation.yaml files...')
    print()
    grand_total = 0
    for fp in files:
        rel = os.path.relpath(fp, BASE).replace('\\', '/')
        findings = scan_file(fp)
        if findings:
            print(f'### {rel}  ({len(findings)} findings)')
            for lineno, line, label in findings:
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:117] + '...'
                print(f'  L{lineno:>4}  [{label}]')
                print(f'         {snippet}')
            print()
            grand_total += len(findings)
        else:
            print(f'### {rel}  ✅ CLEAN')
    print()
    print(f'=== TOTAL findings across {len(files)} files: {grand_total} ===')


if __name__ == '__main__':
    main()
