---
name: analyze-azure-profiler-trace
description: This skill analyzes Azure Profiler CPU traces for SQL Server processes. It identifies the hottest methods by exclusive CPU usage using the azure-profiler-mcp CLI tool.
---

# Analyze Azure Profiler Trace

## Skill Overview

This skill analyzes Azure Profiler CPU traces for SQL Server processes. It identifies the hottest methods by exclusive CPU usage using the `azure-profiler-mcp` tool (CLI or MCP server mode).

## Prerequisites

- Access to the `azure-profiler-mcp` tool
- Valid authentication (`az login`) for accessing Azure Profiler data

## Required Parameters

| Parameter | Description | Format | Example | Required | Default |
|-----------|-------------|--------|---------|----------|---------|
| `{traceName}` | The trace role name | string | `rgserver_fb1aa04baca2_2026_03_07_15_57_04_` | Yes | — |
| `{date}` | Trace date | YYYY-MM-DD | `2026-03-07` | Yes | — |
| `{group}` | Profiler group name | string | `Azure SQL` | No | `Azure SQL` |
| `{process}` | Process name to analyze | string | `sqlservr.exe` | No | `sqlservr.exe` |
| `{topN}` | Number of top methods to retrieve | number | `50` | No | `32` |

## Workflow Overview

**This skill has 2 tasks.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Invoke the azure-profiler-mcp tool | Always |
| Task 2 | Source code lookup | Optional, on user request |

## Execution Steps

### Task 1: Execute the CLI command below to get the top `{topN}` hottest methods sorted by exclusive CPU (samples descending). If the tool does not exist, display installation instructions.
```powershell
& "$env:USERPROFILE\.dotnet\tools\azure-profiler-mcp.exe" get-hottest-methods `
    --group   "{group}" `
    --role    "{traceName}" `
    --date    "{date}" `
    --process "{process}" `
    --sort    exclusive `
    --top     {topN}
```

#### Output
Follow these instructions exactly:

1. **If tool does not exist**:
   Display the following message:
   
   > The azure-profiler-mcp tool is not installed. To install:
   > 1. Request **MTP - InnerSource - Contributor** entitlement: https://coreidentity.microsoft.com/manage/entitlement/entitlement/mtpinnersour-hxrm
   > 2. Run the installation command below
   ```powershell
   # Install the tool
   dotnet tool install azure-profiler-mcp -g --add-source https://pkgs.dev.azure.com/microsoft/_packaging/WDATP/nuget/v3/index.json
   ```
   > 3. Verify installation
   ```powershell
   # Verify installation (should return True)
   Test-Path "$env:USERPROFILE\.dotnet\tools\azure-profiler-mcp.exe"
   ```

2. **If query returns results (rowcount > 0)**:
   - Display the formatted results table with columns: `#`, `Proc%`, `Mach%`, `ExclProc%`, `Samples`, `Method`
   - Include Web Portal and Flamegraph links for full symbol names

3. **If query returns no results (rowcount = 0)**:
   - Display: "No methods found. Verify `traceName` spelling (case-sensitive) and confirm `date` matches the capture date. Merged streams are available after ~2 AM UTC for the previous day."

4. **If error occurs**: Surface the raw error message and suggest recovery action per the Error Handling table below.

---

### Task 2: Source Code Lookup (Optional). If the user asks for deeper analysis on any hot method, use the Bluebird/Engineering Copilot code search (`do_fulltext_search` or `do_vector_search`) to locate the source file for the function.

1. Read the implementation and summarize what the function does.
2. Suggest potential optimization opportunities if applicable.

---

## Error Handling

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| Tool not installed | `Test-Path` returns `False` | Run `dotnet tool install azure-profiler-mcp -g`, then retry |
| Trace not found | `[NO DATA] No merged profile data found` | Verify `traceName` spelling (case-sensitive); confirm `date` matches capture date |
| Auth failure | `[AUTH]` error, 401 response | Re-authenticate with `az login` |
| Empty results | Tool returns 0 methods | Try broader date range or confirm `process` name |
| Invalid date format | Parse failure | Use `YYYY-MM-DD` format |

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Profiler Results are Found

#### Azure Profiler CPU Analysis for {traceName}

**Top {topN} Hottest Methods (Exclusive CPU — Samples Descending)**

| # | Proc% | Mach% | ExclProc% | Samples | Method |
|---|-------|-------|-----------|---------|--------|
| 1 | 3.62% | 5.23% | 3.61% | 107,348 | ntoskrnl.exe!HalpInterruptSendIpi |
| 2 | 1.36% | 0.88% | 1.36% | 17,970 | ...tInfo<LogBlockId>,0>::WaitUntilSequenceAdvances |
| 3 | 1.26% | 1.50% | 1.26% | 30,818 | ...pinlock<5,8,268435714>::SpinToAcquireOptimistic |
| 4 | 1.22% | 0.78% | 1.22% | 16,062 | ...dWaitInfo<LogBlockId>,0>::RemoveWaiterFromLists |
| 5 | 0.62% | 0.38% | 0.62% | 7,707 | sqlmin.dll!lck_GetSessionMode |

**Column definitions:**

| Column | Description |
|--------|-------------|
| `#` | Rank (1 = hottest) |
| `Proc%` | Inclusive % of process CPU |
| `Mach%` | Inclusive % of machine CPU |
| `ExclProc%` | **Exclusive** % of process CPU — primary sort key |
| `Samples` | Raw exclusive sample count |
| `Method` | `module.dll!MethodName` — truncated with `...` prefix if long |

**Note**: 
- When a symbol is too long to display, the tool truncates the left side and prefixes with `...`
- Use the Web Portal or Flamegraph links to view full untruncated symbol names

**Links for full symbol names:**
- Web Portal: `https://azureprofiler.azurewebsites.net/collection/Azure/Azure+SQL/...`
- Process Flamegraph: `https://azureprofiler.azurewebsites.net/collection/Azure/Azure+SQL/.../flamegraph`

---

### When No Results are Found

#### Azure Profiler CPU Analysis for {traceName}

No methods found for this trace. Verify the trace name spelling (role names are case-sensitive) and confirm the date matches the capture date. Merged streams are available after ~2 AM UTC for the previous day.
