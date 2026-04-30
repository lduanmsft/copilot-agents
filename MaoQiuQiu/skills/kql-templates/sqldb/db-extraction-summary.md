# SQL DB extraction summary

| Category | Original | After dedup | After audit | After v2 cleanup | Final |
| --- | ---: | ---: | ---: | ---: | ---: |
| availability | 875 | 780 | 774 | 768 | 768 |
| connectivity | 357 | 310 | 309 | 303 | 303 |
| data-integration | 547 | 479 | 476 | 471 | 471 |
| geodr | 125 | 110 | 110 | 108 | 108 |
| native | 218 | 182 | 174 | 167 | 167 |
| performance | 1114 | 942 | 916 | 898 | 898 |
| query-store | 33 | 29 | 29 | 29 | 29 |
| resource-governance | 119 | 96 | 95 | 93 | 93 |
| telemetry | 486 | 340 | 317 | 302 | 302 |
| css-wiki | 1095 | 746 | 736 | 715 | 715 |

- Total unique tables found (initial): 306
- Total unique tables remaining (final): 366
- First dedup removed: 955
- Queries parameterized: 369
- Audit v1 removals: 78
- Second dedup removed: 23
- Audit v2 removals: 45 (19 HTML garbage + 26 empty/fragment)
- Audit v2 TableName fixes: 144

## Audit v2 (2026-04-30)

### P0: HTML garbage removed (19 entries)
Entries containing >5 HTML `<span>` tags instead of KQL. Sources were meeting notes,
incident tables, and HTML-rendered wiki pages that had no KQL code blocks.

### P1: Invalid TableName fixed (144 entries)
TableName field was set to KQL keywords (`ago`, `now`, `datetime`, `toscalar`),
CSS properties (`color`, `margin`), column names, or let-variable names.
Fixed by extracting the real table name from the query body.

### P1: Unfixable entries removed (26 entries)
Empty queries, CAS command builders, C# code fragments, pipe-only fragments,
and dynamic `table()` calls that can't resolve to a physical table.

### Remaining known issues (P2, not blocking)
- 661 hardcoded values (mostly event names/states — correct as-is)
- 85 hardcoded datetimes (from TSG case examples)
- 7 unknown TableNames (need manual review)
- 3 unparameterized TSG placeholders (`<<Restore request ID>>`)

## Issues / warnings

- Removed 78 invalid or prose-style entries during audit v1.
- Second dedup removed 23 additional entries after parameterization.
- Unique table count changed from 306 to 366 after audit/dedup.
