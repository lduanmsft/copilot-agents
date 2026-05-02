---
name: correlated-incidents
description: Searches the IcM DataWarehouse (Kusto database) for IcM incidents that involve the same logical server, database, or AppName as those under investigation. This skill may be called by itself or as part of a larger diagnostic workflow.
---

# Correlated Incidents Search

This skill searches IcM DataWarehouse (Kusto database) for IcM incidents whose discussion entries include relevant identifiers (the logical server name, the database name, and/or the AppName). A primary goal of this skill is for CSS engineers to locate relevant IcM incidents which may prevent them from needing to file their own CRI.

## Allowed Tools (STRICT WHITELIST)

**⚠️ CRITICAL: Only the following tools may be used for correlated incidents search. Using any other tools (e.g., ADO work item search, ADO wiki search) is PROHIBITED.**

### Primary Search Tools

| Tool | Purpose | When to Use |
| ---- | ------- | ----------- |
| `get-db-info` | Tool for obtaining AppName values | Step 2 |
| `mcp_azure_mcp_kusto` | Azure MCP server's tool for executing Kusto queries | Step 3 |

### 🚫 PROHIBITED Tools

**DO NOT use these tools for correlated incidents search:**
- ❌ `mcp_ado_search_wiki` - This is for wiki documentation, NOT IcM incident search
- ❌ `mcp_ado_search_workitem` - This is for ADO work items, NOT IcM incident search
- ❌ Any other ADO tools (`mcp_ado_*`) - These are not for IcM incident search
- ❌ `mcp_icm-prod_get_similar_incidents` - We are not looking for incidents with similar symptoms, we are looking for incidents with the same identifiers in discussion entries
- ❌ `semantic_search` or `grep_search` - These search local files, not IcM incidents

**If you find yourself reaching for a tool not in the whitelist above, STOP and reconsider.**

---

## Required Information

This skill requires the following inputs (which should be provided by the calling agent):

### From User or IcM:
- **Current Incident ID** (optional - if investigating an existing incident)
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From the `get-db-info` Skill:
- **AppName** (e.g., `a1597ec8d948`)

## Output Requirement (MANDATORY)

**⚠️ CRITICAL**: The "📊 Correlated Incidents Analysis" section MUST appear in EVERY investigation report, regardless of whether correlated incidents are found.

**This section is MANDATORY and cannot be skipped.**

## Workflow

### 1. Validate Inputs

Ensure required parameters are provided:
- LogicalServerName, LogicalDatabaseName
- Time window for context (StartTime and EndTime)
- Optionally, one or more AppName values

### 2. Determine the Correct AppName Value(s) to Use for Searching

If AppName values were explicitly provided by the calling agent, use those for searching. If not, use the AppName value(s) obtained from the `get-db-info` skill. If multiple AppName values are available, use each one of them for searching.

If not AppName values are available at all, stop execution and inform the caller that an error has occurred ("Could not determine the correct AppName value(s) for searching. Please provide AppName value(s) or ensure the `get-db-info` skill returns AppName information.").

### 3. Search for Correlated Incidents

Use the `ICMDW100` query (see [references/queries.md](references/queries.md)) as the basis for searching for correlated incidents. This query searches the IcM DataWarehouse for incidents whose discussion entries contain the logical server name, database name, and/or AppName value. Use the `mcp_azure_mcp_kusto` tool to execute the query, as described in the "Query Execution Format" section of [references/queries.md](references/queries.md).

Execute the query once for each AppName value available (if multiple), and combine results together. If no AppName values are available, stop execution and inform the caller that an error has occurred ("Could not determine the correct AppName value(s) for searching. Please provide AppName value(s) or ensure the `get-db-info` skill returns AppName information.").

If multiple AppName values are used for searching, de-duplicate results before moving on to Step 4.

### 4. Determine Which Search Results are Most Relevant

Select up to 5 of the most relevant correlated incidents based on:

| Relevance Criteria | Description |
| ------------------ | ----------- |
| Prioritize `CustomerReported` incidents | `CustomerReported` incidents are more likely to have detailed discussions compared to `LiveSite` incidents. Additionally, every `CustomerReported` incident should be handled by a person whereas some `LiveSite` incidents may only be handled by automation. |
| Priorize high `ReferenceCount` | Incidents with more discussion entries that reference the identifiers are more likely to be relevant. |
| Prioritize multiple identifier matches | Incidents whose discussions reference multiple of the identifiers (e.g. both server name and database name) are more likely to be relevant than incidents that only reference one of the identifiers. Rows in which the `References` column value is `Discussion contains: AppName, Database Name, Logical Server Name` are especially likely to be relevant. |
| Prioritize owned incidents | Incidents that are currently owned by an engineer (i.e. the `OwningContactAlias` column is not blank) are more likely to be relevant than un-owned incidents. |
| Exclude matches of the Database Name if it is too common | If the database name is a common word (e.g. `hosting`), it may be referenced in many incidents that are not actually relevant. In these cases, prioritize matches that include the logical server name and/or AppName over matches that only include the database name. |
| Exclude matches of the Logical Server Name if it is too common | If the logical server name is a common word (e.g. `murphy`), it may be referenced in many incidents that are not actually relevant. In these cases, prioritize matches that include the database name and/or AppName over matches that only include the logical server name. |

### 5. Present Findings in a Report

Use the guidance in [references/report.md](references/report.md) to format the findings. Always include the "Summary Section" output.

If no correlated incidents are found, then use the output from the "No Results Found" section.

If correlated incidents are found, then use the output from the "Results Found" section, including up to 5 of the most relevant incidents based on the relevance criteria in Step 4.

---

### 🚨🚨 MANDATORY EXECUTION CHECKLIST 🚨🚨

**STOP! Before proceeding, you MUST complete ALL of the following steps. Track your progress:**

| Step | Description | Tool to Use | Status |
| ---- | ----------- | ----------- | ------ |
| 1 | Validate inputs | N/A | ⬜ NOT STARTED |
| 2 | Determine the Correct AppName Value(s) to Use for Searching | `get-db-info` | ⬜ NOT STARTED |
| 3 | Search for Correlated Incidents | `mcp_azure_mcp_kusto` | ⬜ NOT STARTED |
| 4 | Determine Which Search Results are Most Relevant | N/A | ⬜ NOT STARTED |
| 5 | Present Findings in a Report | N/A | ⬜ NOT STARTED |

After each Step is executed, update the Status column to "✅ COMPLETE". You must complete ALL steps before presenting the Correlated Incidents Analysis.

**⛔⛔⛔ ABSOLUTE ENFORCEMENT RULES ⛔⛔⛔**

1. **ALL steps 1-5 are MANDATORY** - you MUST execute every single step using the specified tool.
2. **Execute each step in order** - Each step should be executed serially, in the order listed above. Do not skip around.
3. **Verify ALL steps show ✅ COMPLETE** before presenting Correlated Incidents Analysis.

**🚫 FORBIDDEN BEHAVIORS:**
- ❌ Do not execute the Steps if there is not at least one AppName value provided, unless the AppName value(s) can be obtained from the `get-db-info` skill.
- ❌ Do not include duplicate entries in the final report.
- ❌ Do not present the Correlated Incidents Analysis until ALL steps are complete.
- ❌ Do not present more than 5 incidents in the final report.
- ❌ Do not skip any Steps.
- ❌ Do not use any tools other than the ones specified for each Step.

## Future Enhancements

- Add analysis of the "Authored Summary" section of IcM incidents, which may also contain the identifiers.
- Filter or add weight to discussion entries based on the creator of the entry (e.g. engineer vs. automated system).
- Add analysis of the timeline of discussion entries to identify incidents in which the relevant identifiers were mentioned around the same time as the current incident being investigated.
- Add analysis of the identifiers stored in custom properties of the IcM incidents (if available), which yield more weight to incidents that match these identifiers.
