---
name: overall-top-queries
description: This skill analyzes database queries including wait, cpu, logical read, logical write, memory grant, tempdb usage, log usage, compilation CPU of successful compilation, Compilation Time of successful compilation, compilation CPU of failed compilation, and Compilation Time of failed compilation
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Overall Top Queries

## Skill Overview

This skill performs comprehensive query analysis by executing multiple sub-skills to investigate various query performance metrics including wait queries, CPU usage, logical reads, logical writes, memory grants, tempdb usage, log usage, and compilation statistics for both successful and failed compilations.

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
| Task 1 | Execute Sub-Skills | Always |

## Execution Steps

### Task 1: Execute Sub-Skills 

This skill performs following sub-skills one by one
- [Top CPU queries](top-cpu-queries.md)
- [Top Failed Compilations by CPU](top-failed-compilations-by-cpu.md)
- [Top Failed Compilations by Compilation Time](top-failed-compilations-by-compilation-time.md)
- [Top logical reads queries](top-logical-reads-queries.md)
- [Top logical writes queries](top-logical-writes-queries.md)
- [Top Log queries](top-log-queries.md)
- [Top memory grant queries](top-memory-grant-queries.md)
- [Top Queries by compilation CPU](top-queries-by-compilation-cpu.md)
- [Top Queries by Compilation Time](top-queries-by-compilation-time.md)
- [Top wait queries](top-wait-queries.md)
