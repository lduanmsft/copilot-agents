# PR / CU / Branch Tracking Skill

This skill defines the procedure for tracing a PR fix's availability across SQL Server branches and CUs.
Used by any agent or workflow that finds a relevant PR fix.

**Used by:** `callstack-research`, `errorcode-research`, `lduan-agent` (any mode)

---

## When to Use

Whenever a relevant PR is identified during analysis — whether from bug search, source code analysis, or user-provided information — follow this procedure to determine if the fix is available in the customer's SQL Server version.

---

## Procedure

### Step A — Get PR linked work items

```
msdata-repo_get_pull_request_by_id(repositoryId, pullRequestId, includeWorkItemRefs: true)
→ Extract workItemRefs → list of linked Bug IDs
```

### Step B — Check fix presence via merge commit (PREFERRED — most reliable)

The PR's merge commit ID is the most reliable way to verify fix presence across branches:

```
1. Get merge commit from PR:
   msdata-repo_get_pull_request_by_id(repositoryId, pullRequestId)
   → Extract lastMergeCommit.commitId

2. Search for this commit in each release branch:
   msdata-repo_search_commits(project, repository, commitIds: ["{mergeCommitId}"], version: "rel/box/sql2022/...", versionType: "Branch")
   msdata-repo_search_commits(project, repository, commitIds: ["{mergeCommitId}"], version: "rel/box/sql2025/...", versionType: "Branch")
   msdata-repo_search_commits(project, repository, commitIds: ["{mergeCommitId}"], version: "master", versionType: "Branch")

3. If commit found → fix is in that branch
   If commit not found → fix has NOT been backported to that branch
```

### Step B (fallback) — Check via code search

If merge commit search is inconclusive, search for a unique identifier from the fix (e.g., a new variable name, trace flag define, or function signature) in each branch:

```
msdata-search_code(searchText: "{unique_fix_identifier}", branch: ["rel/box/sql2022/sql2022_rtm_qfe-cu"])
msdata-search_code(searchText: "{unique_fix_identifier}", branch: ["rel/box/sql2025/sql2025_rtm_qfe-cu"])
msdata-search_code(searchText: "{unique_fix_identifier}", branch: ["master"])
```

### Step C — Search CU KB articles for linked Bug IDs

```
microsoft-learn-microsoft_docs_search(query: "SQL Server 2022 cumulative update {bug_id}")
```

Check if any of the linked bug IDs appear in CU fix lists.

### Step D — Check for trace flag

If the PR introduces a trace flag (e.g., `TRCFLG_RETAIL_XLIST_FIX 16405`):
- Search if the TF is documented in the trace flags reference
- Check if it's marked as `Reserved` in the latest branch (= fix is default-on, TF no longer needed)

### Step E — Generate availability table

Include this table in the report:

| Branch | Fix Present | Status |
|--------|------------|--------|
| master | ✅ / ❌ | — |
| rel/box/sql2025/sql2025_rtm_qfe-cu | ✅ / ❌ | — |
| rel/box/sql2022/sql2022_rtm_qfe-cu | ✅ / ❌ | — |
| rel/box/sql2019/sql2019_rtm_qfe-cu | ✅ / ❌ | — |

### Step F — Determine customer recommendation

| Situation | Recommendation |
|-----------|---------------|
| Fix in customer's branch | Identify which CU contains the fix, recommend update |
| Fix NOT in customer's branch | Recommend requesting **OD hotfix** via support case — cite PR number and linked Bug IDs |
| Fix in a newer SQL version | Note as alternative path (e.g., "upgrade to SQL 2025 where fix is included") |
| Fix only in master, not in any release branch | Fix not yet released — recommend OD hotfix or wait for next CU |
