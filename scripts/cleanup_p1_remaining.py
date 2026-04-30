#!/usr/bin/env python3
"""
Remove the 26 remaining invalid TableName entries that couldn't be auto-fixed.
These are empty queries, code fragments, or non-standalone KQL.
"""
import re
import os

BASE = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

# The 26 unchanged entries from P1 cleanup
REMOVE_IDS = {
    # availability - 2 entries
    'DB-availability-181',   # FilteredResults - subquery fragment
    'DB-availability-522',   # strcat - CAS command builder, not KQL

    # css-wiki - 7 entries
    'DB-css-wiki-228',       # ago - let variables only, no table
    'DB-css-wiki-229',       # ago - let variables only, no table
    'DB-css-wiki-307',       # datetime - let variables only, no table
    'DB-css-wiki-617',       # read - empty query
    'DB-css-wiki-618',       # quot - empty query
    'DB-css-wiki-619',       # should - empty query
    'DB-css-wiki-621',       # 'no' - empty query

    # native - 5 entries
    'DB-native-50',          # cluster - pipe-only fragment
    'DB-native-141',         # datetime - let + RAID placeholder only
    'DB-native-142',         # datetime - let + RAID placeholder only
    'DB-native-160',         # ago - let + function call, no table visible
    'DB-native-161',         # ago -> MwcTrace (was fixed but let's verify)

    # performance - 10 entries
    'DB-performance-63',     # toscalar - let trim() only
    'DB-performance-128',    # toscalar - pipe fragment
    'DB-performance-185',    # AppName - no table
    'DB-performance-427',    # datetime - no table
    'DB-performance-525',    # pfs_close_handle_samples - pipe fragment
    'DB-performance-672',    # timeouts - empty query
    'DB-performance-674',    # timeouts_size - empty query
    'DB-performance-682',    # totalXIOBasedDb - join fragment
    'DB-performance-824',    # cv_ComponentOwnerName - build system function
    'DB-performance-825',    # cv_ComponentOwnerName - build system function

    # resource-governance - 1 entry
    'DB-resource-governance-31',  # toscalar - pipe fragment

    # telemetry - 2 entries
    'DB-telemetry-305',      # table - dynamic table() call, can't resolve
    'DB-telemetry-311',      # shouldSubstring - C# code fragment
}

# Remove DB-native-161 from list if it was already fixed
# (the P1 script fixed it to MwcTrace, so it should be fine now)
REMOVE_IDS.discard('DB-native-161')


def remove_skills(yaml_path, ids_to_remove):
    """Remove skill blocks by ID. Returns count removed."""
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    pattern = r'^- id:\s*(DB-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    if not matches:
        return 0

    removed = 0
    for i in range(len(matches) - 1, -1, -1):
        sid = matches[i].group(1)
        if sid in ids_to_remove:
            start = matches[i].start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            block = content[start:end]
            content = content[:start] + content[end:]
            removed += 1
            print(f"  REMOVED: {sid} ({len(block)} bytes)")

    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return removed


def main():
    categories = [
        'availability', 'connectivity', 'css-wiki', 'data-integration',
        'geodr', 'native', 'performance', 'query-store',
        'resource-governance', 'telemetry'
    ]

    total = 0
    print("=" * 60)
    print("Removing 26 unfixable invalid-TableName entries")
    print("=" * 60)

    for cat in categories:
        yaml_path = os.path.join(BASE, cat, f'{cat}.yaml')
        if not os.path.exists(yaml_path):
            continue
        cat_ids = {sid for sid in REMOVE_IDS if sid.startswith(f'DB-{cat}-')}
        if not cat_ids:
            continue
        print(f"\n[{cat}] removing {len(cat_ids)}...")
        n = remove_skills(yaml_path, cat_ids)
        total += n

    print(f"\n{'=' * 60}")
    print(f"Total removed: {total}")
    print("=" * 60)

    # Post counts
    print("\nFinal skill counts:")
    grand = 0
    for cat in categories:
        yaml_path = os.path.join(BASE, cat, f'{cat}.yaml')
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
                c = f.read()
            n = len(re.findall(r'^- id:\s*DB-', c, re.MULTILINE))
            grand += n
            print(f"  {cat}: {n}")
    print(f"  TOTAL: {grand}")


if __name__ == '__main__':
    main()
