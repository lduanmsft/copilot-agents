# Skill: Search TSG Repos (msdata) — Remote, no local clone

Tested working method for searching SQL DB / SQL MI TSG content **without** any local
git clone, after wiki-based search proved unreliable for several repos.

## Decision matrix — which tool to use

| Need | Tool | Notes |
|------|------|-------|
| **Keyword/identifier search across one or more TSG repos** ⭐ | `mcp_msdata_search_code` | Always-works; use this first. |
| Read full markdown of a known eng.ms page | `mcp_enghub_fetch <url>` | Returns markdown + `Source:` (real git path). |
| Phrase / multi-token search (eng.ms scope) | `mcp_enghub_search` with `scope.urlPath` | Supports `"login failure"`, multi-word. |
| CSS team TSGs / case experience | `mcp_csswiki_search_wiki` project=`AzureSQLDB`/`AzureSQLMI`/`SQLServerWindows` | Different ADO org; complementary. |
| ❌ DO NOT use for `TSG-SQL-MI-Performance` | `mcp_msdata_search_wiki` | Wiki `mappedPath` mis-configured → 0 hits forever. Other 4 MI wikis OK. |
| ❌ Currently disabled | `mcp_msdata_repo_get_file_content` | Use `mcp_enghub_fetch` instead for full file. |

## Required call shape — `mcp_msdata_search_code`

```
project    = ["Database Systems"]
repository = ["TSG-SQL-XX-Yyy", ...]   # one or more repos in a SINGLE call
searchText = "<single token>"
top        = 30
path       = ["/content/sub1/", "/content/sub2/"]   # OPTIONAL but recommended
```

### Parameter rules
1. **`repository`**: pass an array — one call hits all repos in parallel. Saves N round-trips.
2. **`searchText`**: single token works best (`msdtc`, `latch`, `suspend`, `CPU`).
   - ❌ Phrases (`"worker thread"`) → not supported, returns 0.
   - ❌ Boolean (`A AND B`) → not supported.
   - ✅ Filename wildcards (`file:*worker*`) → supported.
3. **`path` filter**: critical for repos that build a docfx site.
   - Always exclude `/content/_site/` (HTML render output — every `.md` has 1-3 `.html` duplicates).
   - Exclude `.attachments` for image noise.
   - For `TSG-SQL-MI-Performance` use:
     - `/content/sql_cloud_lifter_notebook/`
     - `/content/Hermes/`
     - `/content/Azure SQL Managed Instance (CloudLifter) Performance TSGs and SOPs/`

### Result post-processing (deduplication)
After response, drop any path that:
- contains `_site/` (rendered HTML duplicate)
- contains `.attachments` (binary noise)
- doesn't end in `.md`, `.ipynb`, `.yml`, `.kql`

Aggregate by `repository.name` and rank within repo by `len(matches.content)`.

## Repo registry

### SQL MI (5 repos under `Database Systems` project)

| Repo | Wiki search? | Where content lives |
|------|-------------|--------------------|
| TSG-SQL-MI-Availability | ✅ wiki OK | wiki + git `/content/` |
| TSG-SQL-MI-BackupRestore | ✅ wiki OK | wiki + git `/content/` |
| TSG-SQL-MI-Networking | ✅ wiki OK | wiki + git `/content/` |
| TSG-SQL-MI-TransactionalReplication | ✅ wiki OK | wiki + git `/content/` |
| **TSG-SQL-MI-Performance** | ❌ wiki broken | **must** use `search_code` + path filter (3 subdirs above) |

### SQL DB (10 active repos under `Database Systems` project)

`TSG-SQL-DB-Airgap`, `TSG-SQL-DB-Availability`, `TSG-SQL-DB-Connectivity`,
`TSG-SQL-DB-DataIntegration`, `TSG-SQL-DB-GeoDr`, `TSG-SQL-DB-Native`,
`TSG-SQL-DB-Performance`, `TSG-SQL-DB-QueryStore`, `TSG-SQL-DB-RG`,
`TSG-SQL-DB-Telemetry`.

(`TSG-SQL-DB-Hyperscale` disabled, `TSG-SQL-DB-Supportability` near-empty — skip.)

## Example: full call → clean output

Search "suspend" across all SQL DB TSG repos:

```jsonc
{
  "tool": "mcp_msdata_search_code",
  "project": ["Database Systems"],
  "repository": [
    "TSG-SQL-DB-Airgap","TSG-SQL-DB-Availability","TSG-SQL-DB-Connectivity",
    "TSG-SQL-DB-DataIntegration","TSG-SQL-DB-GeoDr","TSG-SQL-DB-Native",
    "TSG-SQL-DB-Performance","TSG-SQL-DB-QueryStore","TSG-SQL-DB-RG",
    "TSG-SQL-DB-Telemetry"
  ],
  "searchText": "suspend",
  "top": 50
}
```

After dedup → 39 results across 7 repos, top hits include
`TSG-SQL-DB-Connectivity:/TSG/gateway/suspend-gateway-connectivity.md` (5 matches),
`TSG-SQL-DB-GeoDr:/content/GEODR/GEODR0011-Logins-failing-due-to-SUSPEND_FROM_REVAL.md` (4 matches),
`TSG-SQL-DB-Availability:/content/.../StorageEngine/Redo-suspension-at-the-specified-LSN.md` (3 matches).

## Linkify TSG paths

Construct clickable git URLs:
```
https://msdata.visualstudio.com/Database%20Systems/_git/<RepoName>?path=<path>
```

Or get rendered eng.ms URL via `mcp_enghub_search` then `mcp_enghub_fetch`.

## Single-repo targeted search

When the user is investigating a specific category, scope `repository` to one repo
(e.g. `["TSG-SQL-MI-BackupRestore"]`) and skip `path` filter unless results are noisy.

## Pitfalls / lessons learned (verified 2026-05-02)

- `TSG-SQL-MI-Performance` wiki search returns 0 for **any** keyword.
  Wiki `mappedPath = /content/Index` but the git repo has no `Index` — only `index.md`.
  Underlying repo is fully indexed by code search.
- Without `path` filter, a search like `tsg` in a docfx repo can return ~74 noisy hits
  (manifest.json, _site/*.html). Adding the 3 real content subdirs reduces to a clean ~10.
- Zero hits ≠ tool broken. Verify by searching a domain-relevant token
  (e.g. `backup` in BackupRestore returns 166 — proves index works).
