"""
Create MI versions of SQLDB Performance investigation.yaml and kql-livesite.yaml files.
Applies all filter replacements and structural changes.
"""
import os
import re

SQLDB_BASE = r"c:\Users\lduan\.copilot\agents\skills\kql-templates\sqldb\performance"
MI_BASE = r"c:\Users\lduan\.copilot\agents\skills\kql-templates\mi\performance"

CATEGORIES = [
    "cpu", "queries", "blocking", "memory", "query-store",
    "compilation", "out-of-disk", "miscellaneous", "sqlos"
]

# Map category to ID prefix used in that category
CATEGORY_ID_PREFIX = {
    "cpu": "LS-CPU",
    "queries": "LS-QUERIES",
    "blocking": "LS-BLOCKING",
    "memory": "LS-MEMORY",
    "query-store": "LS-QDS",
    "compilation": "LS-COMPILE",
    "out-of-disk": "LS-OOD",
    "miscellaneous": "LS-MISC",
    "sqlos": "LS-SQLOS",
}


def deduplicate_logical_server_filter(content: str) -> str:
    """Remove duplicate LogicalServerName filter from consecutive where clauses.
    
    Pattern: When placeholder expansion creates:
      | where LogicalServerName =~ '{ServerName}' and originalEventTimestamp between (...)
      | where LogicalServerName =~ '{ServerName}' and database_name =~ '{DatabaseName}'
    
    The second line's LogicalServerName filter is redundant.
    """
    lines = content.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        if i > 0 and "LogicalServerName =~ '{ServerName}'" in line and '| where' in line:
            prev = lines[i-1]
            if "LogicalServerName =~ '{ServerName}'" in prev and '| where' in prev:
                # Remove the redundant LogicalServerName filter from current line
                line = line.replace("LogicalServerName =~ '{ServerName}' and ", "")
        result.append(line)
    
    return '\n'.join(result)


def apply_filter_replacements(content: str) -> str:
    """Apply all MI filter replacements to content."""

    # 1. {AppNamesNodeNamesWith7DayOriginalEventTimeRange} (must be before the regular one)
    content = content.replace(
        "{AppNamesNodeNamesWith7DayOriginalEventTimeRange}",
        "LogicalServerName =~ '{ServerName}' and originalEventTimestamp between (datetime_add('day', -7, datetime({StartTime}))..datetime({EndTime}))"
    )

    # 2. {ApplicationNamesNodeNamesWithOriginalEventTimeRange}
    # This is used in MonRgLoad queries — add AppTypeName == 'Worker.CL'
    content = content.replace(
        "{ApplicationNamesNodeNamesWithOriginalEventTimeRange}",
        "LogicalServerName =~ '{ServerName}' and originalEventTimestamp between (datetime({StartTime})..datetime({EndTime})) and AppTypeName == 'Worker.CL'"
    )

    # 3. {AppNamesNodeNamesWithOriginalEventTimeRange}
    content = content.replace(
        "{AppNamesNodeNamesWithOriginalEventTimeRange}",
        "LogicalServerName =~ '{ServerName}' and originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))"
    )

    # 4. {NodeNamesWithPreciseTimeRange}
    content = content.replace(
        "{NodeNamesWithPreciseTimeRange}",
        "LogicalServerName =~ '{ServerName}' and PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))"
    )

    # 5. {AppNamesNodeNamesWithPreciseTimeRange}
    content = content.replace(
        "{AppNamesNodeNamesWithPreciseTimeRange}",
        "LogicalServerName =~ '{ServerName}' and PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))"
    )

    # 6. {NodeNamesWithOriginalEventTimeRange}
    content = content.replace(
        "{NodeNamesWithOriginalEventTimeRange}",
        "LogicalServerName =~ '{ServerName}' and originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))"
    )

    # 7. {AppNamesOnly} → '{AppName}'
    content = content.replace("{AppNamesOnly}", "'{AppName}'")

    # 8. LogicalServerName =~ '{LogicalServerName}' → LogicalServerName =~ '{ServerName}'
    content = content.replace(
        "LogicalServerName =~ '{LogicalServerName}'",
        "LogicalServerName =~ '{ServerName}'"
    )
    content = content.replace(
        "LogicalServerName=~'{LogicalServerName}'",
        "LogicalServerName =~ '{ServerName}'"
    )
    content = content.replace(
        "LogicalServerName =~'{LogicalServerName}'",
        "LogicalServerName =~ '{ServerName}'"
    )

    # 9. database_name =~ '{LogicalDatabaseName}' → database_name =~ '{DatabaseName}'
    content = content.replace(
        "database_name =~ '{LogicalDatabaseName}'",
        "database_name =~ '{DatabaseName}'"
    )
    content = content.replace(
        "database_name  =~ '{LogicalDatabaseName}'",
        "database_name =~ '{DatabaseName}'"
    )
    content = content.replace(
        "database_name=~'{LogicalDatabaseName}'",
        "database_name =~ '{DatabaseName}'"
    )

    # 10. logical_database_name =~ '{LogicalDatabaseName}' → logical_database_name =~ '{DatabaseName}'
    content = content.replace(
        "logical_database_name =~ '{LogicalDatabaseName}'",
        "logical_database_name =~ '{DatabaseName}'"
    )
    content = content.replace(
        "logical_database_name  =~ '{LogicalDatabaseName}'",
        "logical_database_name =~ '{DatabaseName}'"
    )
    content = content.replace(
        "logical_database_name=~'{LogicalDatabaseName}'",
        "logical_database_name =~ '{DatabaseName}'"
    )

    # 11. {SumCpuMillisecondOfAllApp} references → comment + placeholder
    content = content.replace(
        "/{SumCpuMillisecondOfAllApp}",
        "/1 // MI: CPU capacity placeholder not available, raw values used"
    )
    content = content.replace(
        "{SumCpuMillisecondOfAllApp}",
        "1 // MI: CPU capacity placeholder not available, raw values used"
    )

    # 12. {ActualSumCpuMillisecondOfAllApp} references → comment + placeholder
    content = content.replace(
        "/{ActualSumCpuMillisecondOfAllApp}",
        "/1 // MI: actual CPU capacity placeholder not available, raw values used"
    )
    content = content.replace(
        "{ActualSumCpuMillisecondOfAllApp}",
        "1 // MI: actual CPU capacity placeholder not available, raw values used"
    )

    # 13. {HistoricalTenantRingNames} → '{ClusterName}'
    content = content.replace("{HistoricalTenantRingNames}", "'{ClusterName}'")

    # 14. {NodeNames} → '{NodeName}' (but not {NodeNamesWithXxx} which is already handled)
    # Use regex to only match standalone {NodeNames}
    content = re.sub(r'\{NodeNames\}(?!With)', "'{NodeName}'", content)

    # 15. Replace remaining '{LogicalDatabaseName}' references in string contexts
    content = content.replace("'{LogicalDatabaseName}'", "'{DatabaseName}'")
    content = content.replace("{LogicalDatabaseName}", "{DatabaseName}")

    # 16. Deduplicate LogicalServerName filter from consecutive where clauses
    content = deduplicate_logical_server_filter(content)

    return content


def apply_id_prefix(content: str, category: str) -> str:
    """Change LS-xxx IDs to MI-LS-xxx."""
    prefix = CATEGORY_ID_PREFIX[category]
    # Match id references like LS-CPU-01, LS-QUERIES-02, etc.
    # Handle in id: fields, condition references, kql_ref, cross_ref, sub_skills
    content = content.replace(f"{prefix}-", f"MI-{prefix}-")
    return content


def apply_investigation_structural_changes(content: str, category: str) -> str:
    """Apply structural changes specific to investigation.yaml."""

    # Change RequiredParameters
    content = content.replace("    - LogicalServerName\n", "    - ServerName           # MI uses ServerName\n")
    content = content.replace("    - LogicalDatabaseName\n", "    - DatabaseName         # MI uses DatabaseName\n")

    # Add MI-specific parameters
    if "    - AppName" not in content and "AppName" in content:
        content = content.replace(
            "    - ServerName           # MI uses ServerName\n",
            "    - ServerName           # MI uses ServerName\n    - AppName              # MI AppName\n    - ClusterName          # MI ClusterName\n"
        )

    # Remove AppNamesNodeNamesWithOriginalEventTimeRange from RequiredParameters (handled by filter inline)
    content = content.replace("    - AppNamesNodeNamesWithOriginalEventTimeRange   # from appnameandnodeinfo\n", "")
    content = content.replace("    - AppNamesNodeNamesWithOriginalEventTimeRange\n", "")
    content = content.replace("    - ApplicationNamesNodeNamesWithOriginalEventTimeRange\n", "")
    content = content.replace("    - NodeNamesWithOriginalEventTimeRange\n", "")
    content = content.replace("    - AppNamesNodeNamesWithPreciseTimeRange\n", "")
    content = content.replace("    - AppNamesOnly\n", "")
    content = content.replace("    - HistoricalTenantRingNames\n", "")
    content = content.replace("    - NodeNames\n", "")

    # Remove SumCpuMillisecondOfAllApp from RequiredParameters
    content = content.replace("    - SumCpuMillisecondOfAllApp\n", "")
    content = content.replace("    - ActualSumCpuMillisecondOfAllApp\n", "")

    # Change isElasticPool to isBusinessCritical
    content = content.replace("isElasticPool", "isBusinessCritical")

    return content


def remove_elastic_pool_steps_investigation(content: str) -> str:
    """Remove Elastic Pool specific steps from investigation.yaml."""
    # Remove elastic_pool deployment variant in CPU investigation
    # Remove step 1b in query-store (EP detection)
    lines = content.split('\n')
    result = []
    skip_until_indent = None
    skip_ep_variant = False
    ep_variant_indent = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip elastic_pool deployment variant block
        if 'elastic_pool:' in line and ('deployment_variants:' in '\n'.join(lines[max(0,i-3):i]) or 'condition: "isInElasticPool' in '\n'.join(lines[i:i+3])):
            # Find the indentation level
            indent = len(line) - len(line.lstrip())
            # Skip this entire block
            i += 1
            while i < len(lines) and (not lines[i].strip() or (len(lines[i]) - len(lines[i].lstrip()) > indent)):
                i += 1
            continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def remove_hyperscale_steps_kql(content: str) -> str:
    """Remove Hyperscale-specific entries from kql-livesite.yaml."""
    lines = content.split('\n')
    result = []
    skip_block = False
    block_indent = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect Hyperscale blocks by id: MI-LS-MISC-04 or MI-LS-MISC-06
        if ('MI-LS-MISC-04' in line or 'MI-LS-MISC-06' in line) and 'id:' in line:
            # Find the start of this block (go back to find '  - id:')
            # Skip everything until the next '  - id:' block
            i += 1
            while i < len(lines):
                if lines[i].strip().startswith('- id:') and 'MI-LS-MISC-04' not in lines[i] and 'MI-LS-MISC-06' not in lines[i]:
                    break
                i += 1
            continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def remove_hyperscale_steps_investigation(content: str) -> str:
    """Remove Hyperscale-specific steps from investigation.yaml."""
    lines = content.split('\n')
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip step 3b and 4b (Hyperscale variants) in miscellaneous
        if ('step: 3b' in line or 'step: 4b' in line) and 'name:' not in line:
            # Find indent level
            indent = len(line) - len(line.lstrip())
            i += 1
            while i < len(lines):
                curr_line = lines[i]
                if curr_line.strip() and not curr_line.startswith(' ' * (indent + 1)) and not curr_line.startswith(' ' * (indent + 2)):
                    if curr_line.strip().startswith('- step:') or curr_line.strip().startswith('#'):
                        break
                i += 1
            continue

        # Skip Hyperscale conditions in ExecutionOrder
        if 'Hyperscale' in line and ('replaces' in line or 'condition' in line):
            # Skip this line and the steps line if present
            i += 1
            if i < len(lines) and 'steps:' in lines[i]:
                i += 1
            continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def add_mi_header(content: str, file_type: str) -> str:
    """Add MI header comment at the top of the file."""
    header_line = "# Ported from SQLDB SQLLivesiteAgents, adapted for Managed Instance (MI)\n"
    lines = content.split('\n')
    # Insert after the first ============ line
    for i, line in enumerate(lines):
        if '============' in line:
            lines.insert(i + 1, header_line.rstrip())
            break
    return '\n'.join(lines)


def update_header_comments(content: str) -> str:
    """Update header comments to reflect MI."""
    content = content.replace("# KQL 模板引用: sqldb/", "# KQL 模板引用: mi/")
    content = content.replace("SQLLSinvest_perf_", "MI_SQLLSinvest_perf_")
    return content


def add_mi_cpu_note(content: str) -> str:
    """Add MonManagedInstanceResourceStats note to CPU investigation."""
    if "perf-cpu" in content and "MonManagedInstanceResourceStats" not in content:
        # Add note after description
        content = content.replace(
            '  source: "SQLLivesiteAgents/Performance/CPU"',
            '  source: "SQLLivesiteAgents/Performance/CPU"\n  mi_note: "MI also has MonManagedInstanceResourceStats for instance-level CPU metrics (avg_cpu_percent, virtual_core_count)"'
        )
    return content


def process_investigation(content: str, category: str) -> str:
    """Process investigation.yaml for MI conversion."""
    content = add_mi_header(content, "investigation")
    content = update_header_comments(content)
    content = apply_filter_replacements(content)
    content = apply_id_prefix(content, category)
    content = apply_investigation_structural_changes(content, category)

    if category == "cpu":
        content = add_mi_cpu_note(content)
        # Remove elastic pool deployment variants and steps
        content = remove_elastic_pool_steps_investigation(content)

    if category == "miscellaneous":
        content = remove_hyperscale_steps_investigation(content)

    if category == "query-store":
        # Remove EP step reference
        content = content.replace("isBusinessCritical", "isBusinessCritical")
        # Remove EP-specific steps
        lines = content.split('\n')
        result = []
        skip_ep_step = False
        i = 0
        while i < len(lines):
            line = lines[i]
            # Skip step 1b (EP detection)
            if 'step: 1b' in line and 'name:' not in line:
                indent = len(line) - len(line.lstrip())
                i += 1
                while i < len(lines):
                    curr = lines[i]
                    if curr.strip() and curr.strip().startswith('- step:') or curr.strip().startswith('#'):
                        if not curr.startswith(' ' * (indent + 4)):
                            break
                    i += 1
                continue
            result.append(line)
            i += 1
        content = '\n'.join(result)

    return content


def process_kql_livesite(content: str, category: str) -> str:
    """Process kql-livesite.yaml for MI conversion."""
    content = add_mi_header(content, "kql-livesite")
    content = update_header_comments(content)
    content = apply_filter_replacements(content)
    content = apply_id_prefix(content, category)

    if category == "cpu":
        # Remove Elastic Pool entries (LS-CPU-02, LS-CPU-02b)
        content = remove_ep_kql_entries(content)

    if category == "miscellaneous":
        # Remove Hyperscale entries (MI-LS-MISC-04, MI-LS-MISC-06)
        content = remove_hyperscale_steps_kql(content)

    if category == "query-store":
        # Remove EP entry (MI-LS-QDS-02)
        content = remove_ep_qds_kql_entry(content)

    if category == "queries":
        # Remove elastic_pool deployment variant
        content = remove_ep_variant_from_queries(content)

    return content


def remove_ep_kql_entries(content: str) -> str:
    """Remove Elastic Pool KQL entries (CPU-02, CPU-02b)."""
    lines = content.split('\n')
    result = []
    skip = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is an EP entry
        if '  - id: MI-LS-CPU-02b' in line or '  - id: MI-LS-CPU-02' in line:
            # Don't skip MI-LS-CPU-02x where x is a digit (like MI-LS-CPU-021 etc.) - but 02b and 02 exactly
            stripped = line.strip()
            if stripped in ['- id: MI-LS-CPU-02', '- id: MI-LS-CPU-02b']:
                # Skip until next entry (  - id:) or end of list
                i += 1
                while i < len(lines):
                    if lines[i].strip().startswith('- id:'):
                        break
                    if lines[i].strip().startswith('# ─') and i + 1 < len(lines) and lines[i+1].strip().startswith('# '):
                        # Comment block for next entry - check if next has - id:
                        j = i
                        while j < len(lines) and (lines[j].strip().startswith('#') or not lines[j].strip()):
                            j += 1
                        if j < len(lines) and lines[j].strip().startswith('- id:'):
                            break
                    i += 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def remove_ep_qds_kql_entry(content: str) -> str:
    """Remove Elastic Pool QDS KQL entry (QDS-02)."""
    lines = content.split('\n')
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if '  - id: MI-LS-QDS-02' in line and line.strip() == '- id: MI-LS-QDS-02':
            # Skip until next entry
            i += 1
            while i < len(lines):
                if lines[i].strip().startswith('- id:'):
                    break
                if lines[i].strip().startswith('# ─'):
                    j = i
                    while j < len(lines) and (lines[j].strip().startswith('#') or not lines[j].strip()):
                        j += 1
                    if j < len(lines) and lines[j].strip().startswith('- id:'):
                        break
                i += 1
            continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def remove_ep_variant_from_queries(content: str) -> str:
    """Remove elastic_pool deployment variant from queries kql-livesite.yaml."""
    lines = content.split('\n')
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if 'deployment_variants:' in line.strip() or ('elastic_pool:' in line and 'condition:' not in line):
            indent = len(line) - len(line.lstrip())
            # Check if this is a deployment_variants block
            if 'deployment_variants:' in line:
                i += 1
                # Skip the entire deployment_variants block
                while i < len(lines):
                    curr = lines[i]
                    if curr.strip() and (len(curr) - len(curr.lstrip())) <= indent:
                        break
                    i += 1
                continue
            elif 'elastic_pool:' in line:
                i += 1
                while i < len(lines):
                    curr = lines[i]
                    if curr.strip() and (len(curr) - len(curr.lstrip())) <= indent:
                        break
                    i += 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def main():
    created = []
    errors = []

    for category in CATEGORIES:
        sqldb_dir = os.path.join(SQLDB_BASE, category)
        mi_dir = os.path.join(MI_BASE, category)

        os.makedirs(mi_dir, exist_ok=True)

        # Process investigation.yaml
        inv_src = os.path.join(sqldb_dir, "investigation.yaml")
        inv_dst = os.path.join(mi_dir, "investigation.yaml")

        if os.path.exists(inv_src):
            with open(inv_src, 'r', encoding='utf-8') as f:
                inv_content = f.read()

            mi_inv = process_investigation(inv_content, category)

            with open(inv_dst, 'w', encoding='utf-8') as f:
                f.write(mi_inv)
            created.append(inv_dst)
            print(f"[OK] {category}/investigation.yaml")
        else:
            errors.append(f"[MISS] {inv_src}")

        # Process kql-livesite.yaml
        kql_src = os.path.join(sqldb_dir, "kql-livesite.yaml")
        kql_dst = os.path.join(mi_dir, "kql-livesite.yaml")

        if os.path.exists(kql_src):
            with open(kql_src, 'r', encoding='utf-8') as f:
                kql_content = f.read()

            mi_kql = process_kql_livesite(kql_content, category)

            with open(kql_dst, 'w', encoding='utf-8') as f:
                f.write(mi_kql)
            created.append(kql_dst)
            print(f"[OK] {category}/kql-livesite.yaml")
        else:
            errors.append(f"[MISS] {kql_src}")

    print(f"\n=== Summary ===")
    print(f"Created: {len(created)} files")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  {e}")

    # Verify key replacements
    print(f"\n=== Verification ===")
    for fpath in created:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []
        if '{LogicalServerName}' in content:
            issues.append("{LogicalServerName} still present")
        if '{LogicalDatabaseName}' in content:
            issues.append("{LogicalDatabaseName} still present")
        if '{AppNamesNodeNamesWithOriginalEventTimeRange}' in content:
            issues.append("{AppNamesNodeNamesWithOriginalEventTimeRange} still present")
        if '{ApplicationNamesNodeNamesWithOriginalEventTimeRange}' in content:
            issues.append("{ApplicationNamesNodeNamesWithOriginalEventTimeRange} still present")
        if '{NodeNamesWithPreciseTimeRange}' in content:
            issues.append("{NodeNamesWithPreciseTimeRange} still present")
        if '{AppNamesNodeNamesWithPreciseTimeRange}' in content:
            issues.append("{AppNamesNodeNamesWithPreciseTimeRange} still present")
        if '{NodeNamesWithOriginalEventTimeRange}' in content:
            issues.append("{NodeNamesWithOriginalEventTimeRange} still present")
        # Check ID prefix
        category_name = os.path.basename(os.path.dirname(fpath))
        prefix = CATEGORY_ID_PREFIX.get(category_name, "")
        if prefix:
            # Look for non-MI prefixed IDs
            pattern = rf'(?<![A-Z-]){re.escape(prefix)}-\d'
            matches = re.findall(pattern, content)
            if matches:
                issues.append(f"Non-MI prefixed IDs found: {matches[:3]}")

        if issues:
            print(f"  [WARN] {os.path.basename(os.path.dirname(fpath))}/{os.path.basename(fpath)}:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            short = fpath.replace(MI_BASE + "\\", "")
            print(f"  [PASS] {short}")


if __name__ == "__main__":
    main()
