#!/usr/bin/env python3
"""
Remove HTML garbage entries (P0) from SQL DB KQL YAML templates.
Removes skill blocks where ExecutedQuery contains >5 HTML span tags.
"""

import re
import os
import sys

BASE_DIR = os.path.expanduser(r"~\.copilot\agents\skills\kql-templates\sqldb-extracted")

# P0: HTML garbage skill IDs to remove
P0_REMOVALS = {
    'availability': ['DB-availability-280'],
    'css-wiki': ['DB-css-wiki-678', 'DB-css-wiki-680', 'DB-css-wiki-681', 'DB-css-wiki-682', 'DB-css-wiki-726'],
    'geodr': ['DB-geodr-25'],
    'performance': ['DB-performance-1', 'DB-performance-102', 'DB-performance-244',
                    'DB-performance-565', 'DB-performance-569', 'DB-performance-764'],
    'resource-governance': ['DB-resource-governance-48'],
    'telemetry': ['DB-telemetry-48', 'DB-telemetry-91', 'DB-telemetry-99',
                  'DB-telemetry-115', 'DB-telemetry-278'],
}


def remove_skills_from_yaml(yaml_path, skill_ids_to_remove):
    """Remove specific skill blocks from a YAML file. Returns count removed."""
    with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Find all skill block boundaries
    pattern = r'^- id:\s*(DB-\S+)'
    matches = list(re.finditer(pattern, content, re.MULTILINE))

    if not matches:
        return 0

    # Build list of ranges to keep
    blocks_to_remove = set()
    for i, match in enumerate(matches):
        skill_id = match.group(1)
        if skill_id in skill_ids_to_remove:
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            blocks_to_remove.add((start, end, skill_id))

    if not blocks_to_remove:
        return 0

    # Remove blocks (from end to start to preserve offsets)
    removed = []
    for start, end, skill_id in sorted(blocks_to_remove, reverse=True):
        block_text = content[start:end]
        # Verify it actually has HTML
        html_count = len(re.findall(r'<span\s', block_text))
        if html_count > 0:
            content = content[:start] + content[end:]
            removed.append(skill_id)
            print(f"  REMOVED: {skill_id} ({html_count} HTML spans, {end - start} bytes)")
        else:
            print(f"  SKIP: {skill_id} (no HTML found, keeping)")

    # Write back
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return len(removed)


def main():
    total_removed = 0

    print("=" * 60)
    print("P0 Cleanup: Removing HTML garbage entries")
    print("=" * 60)

    for category, skill_ids in sorted(P0_REMOVALS.items()):
        yaml_path = os.path.join(BASE_DIR, category, f"{category}.yaml")
        if not os.path.exists(yaml_path):
            print(f"SKIP: {yaml_path} not found")
            continue

        print(f"\n[{category}] removing {len(skill_ids)} entries...")
        count = remove_skills_from_yaml(yaml_path, set(skill_ids))
        total_removed += count

    print(f"\n{'=' * 60}")
    print(f"Total removed: {total_removed}")
    print("=" * 60)

    # Verify counts after cleanup
    print("\nPost-cleanup skill counts:")
    categories = ['availability', 'connectivity', 'css-wiki', 'data-integration',
                   'geodr', 'native', 'performance', 'query-store',
                   'resource-governance', 'telemetry']
    grand_total = 0
    for cat in categories:
        yaml_path = os.path.join(BASE_DIR, cat, f"{cat}.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            count = len(re.findall(r'^- id:\s*DB-', content, re.MULTILINE))
            grand_total += count
            print(f"  {cat}: {count}")
    print(f"  TOTAL: {grand_total}")


if __name__ == '__main__':
    main()
