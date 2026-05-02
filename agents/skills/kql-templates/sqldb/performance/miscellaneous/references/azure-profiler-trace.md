---
name: azure-profiler-trace
description: This skill displays all the Azure profiler traces collected in the Nodes where this Azure DB was running.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Azure Profiler Trace

## Skill Overview

This skill displays all the Azure profiler traces collected in the Nodes where this Azure DB was running. It queries MonRgManager and MonManagement tables to find any Azure profiler trace files that were collected either by IcM Automation AzProfilerGeneva or by users running CAS commands.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |

## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Query Azure profiler traces | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{ApplicationNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.
```kql
let rg_server_traces =(MonRgManager
| where {ApplicationNamesNodeNamesWithOriginalEventTimeRange}
| where event =='rg_process_azure_profiler_request'
| where is_success==1
| extend trace_name = tostring(split(message, ':', 1)[0])
| extend trace_name = replace_regex(trace_name, @'\s+', '')//remove the whitespaces
| extend trace_name = trim('"', trace_name)
| project TIMESTAMP,application_name, trace_name,NodeName,ClusterName);
let casCommand_traces=(MonManagement
| extend ClusterName = ring_name
| extend NodeName = node_name
| extend application_name
| where {NodeNamesWithOriginalEventTimeRange}
| where event =~ 'cas_workflow_take_azure_profiler_trace_complete'
| extend trace_name = strcat(NodeName,'_',ClusterName)
| project TIMESTAMP, application_name, trace_name,NodeName,ClusterName);
union rg_server_traces,casCommand_traces
| project-away ClusterName
| order by TIMESTAMP asc
```

#### Output
Follow these instructions exactly:

1. **If query returns results (rowcount > 0)**:
   - Display: "{rowcount} Azure profiler trace file(s) was/were collected for this Azure DB or its nodes while the database was running. (Please note that the file name is only correct if it was created by IcM Automation AzProfilerGeneva. If you find that this file does not exist, it was collected by a user running the CAS command. Please contact the user who issued the command to obtain the file name) You can run '**show me the process IDs**'  to get all process IDs of this Azure DB during the investigation time range. See [process-id-display.md](process-id-display.md) for details."
   - Render the query results as a formatted table showing: TIMESTAMP, application_name, trace_name, NodeName

2. **If query returns no results (rowcount = 0)**:
   - Display: "The Azure Profiler trace was not collected for this Azure DB or its nodes while the database was running."

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When Azure Profiler Traces are Found

#### Azure Profiler Traces for {LogicalDatabaseName}

**3 Azure profiler trace file(s) were collected for this Azure DB or its nodes while the database was running. (Please note that the file name is only correct if it was created by IcM Automation AzProfilerGeneva. If you find that this file does not exist, it was collected by a user running the CAS command. Please contact the user who issued the command to obtain the file name ) You can run '**show me the process IDs**' to get all process IDs of this Azure DB during the investigation time range. See [process-id-display.md](process-id-display.md) for details.**


| Timestamp (UTC) | Application Name | Trace Name | Node Name |
|-----------------|------------------|------------|-----------|
| 2026-03-07T09:56:19 | fabric:/Worker.ISO.Premium/fb1aa04baca2 | | _DB_15 |
| 2026-03-07T10:01:19 | fabric:/Worker.ISO.Premium/fb1aa04baca2 | rgserver_fb1aa04baca2_2026_03_07_09_56_00_ | _DB_15 |
| 2026-03-07T10:56:20 | fabric:/Worker.ISO.Premium/fb1aa04baca2 | | _DB_15 |

**Note**: 
- Rows with empty `Trace Name` indicate traces that were either in progress or collected via CAS command
- Trace file naming convention is `rgserver_{AppName}_{YYYY_MM_DD_HH_MM_SS}_`
- To analyze a captured trace file, type `analyze azure profiler trace <fileName>`.

---

### When No Azure Profiler Traces are Found

#### Azure Profiler Traces for {LogicalDatabaseName}

The Azure Profiler trace was not collected for this Azure DB or its nodes while the database was running.
