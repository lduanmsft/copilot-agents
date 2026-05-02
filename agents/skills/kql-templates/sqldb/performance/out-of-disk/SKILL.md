---
name: out-of-disk
description: Analyzes space issues including drive out of space, directory quota limits, data/log file size limits, tempdb issues, and XStore storage errors for Azure SQL databases.
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
keywords: ['disk space limit', 'file limit', 'file full', 'out of space', 'disk full', 'quota', 'tempdb full', 'log full', 'data full', 'drive full', 'storage limit', 'xstore', 'xio_failed_request']
---

# Space Issue Analysis Skill

## Skill Overview

This skill provides comprehensive analysis of disk space and storage related issues in Azure SQL databases. It detects and diagnoses various problems including drive capacity issues, directory quota limits, data/log file size limits, space allocation failures, and XStore (Azure storage layer) errors.

## When to Use This Skill

This skill should be triggered when the user reports or asks about:
- **Disk space limit** issues
- **File limit** or **file full** errors
- **Out of space** conditions
- **Drive full** or **storage limit** problems
- **Quota exceeded** errors
- **Tempdb full** issues
- **Transaction log full** errors
- **XStore** or **storage layer** errors
- **I/O failure** errors (xio_failed_request)
- SQL errors: 3257, 9002, 5149, 1105, 1101

## Prerequisites

- Access to Kusto clusters for SQL telemetry
- Logical server name and database name
- Time range for investigation

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{LogicalDatabaseName}` | Azure SQL logical database name | string | `mydb` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |

## Execution Order

Execute the following skills in order to comprehensively analyze disk space issues.

**⚠️ IMPORTANT: Output Filtering Rule**
- **ONLY display results from a sub-skill if it detects an issue (🚩)**
- **DO NOT display any output from a sub-skill if no issue is detected (✅)**
- This keeps the report concise and focused on actionable findings

### Step 1: Drive Out of Space
**Reference**: [drive-out-of-space.md](references/drive-out-of-space.md)

Analyzes drive usage on Azure SQL nodes to detect if drives have reached alert thresholds (96%) or near-full conditions.

**Output Rule**: Only include this section in the report if drive usage exceeds threshold.

### Step 2: Directory Quota Hit Limit
**Reference**: [directory-quota-hit-limit.md](references/directory-quota-hit-limit.md)

Determines if the App work\data directory quota has hit its limit.

**Output Rule**: Only include this section in the report if directory quota was hit.

### Step 3: Data or Log Reached Max Size
**Reference**: [data-or-log-reached-max-size.md](references/data-or-log-reached-max-size.md)

Checks if user database or tempdb data/log files have reached their maximum configured size.

**Output Rule**: Only include this section in the report if any file (data or log) reached max size.

### Step 4: Has Out of Space Issue
**Reference**: [has-out-of-space-issue.md](references/has-out-of-space-issue.md)

Analyzes space related allocation failures recorded in SQL errorlog (Errors 3257, 9002, 5149, 1105, 1101).

**Output Rule**: Only include this section in the report if out-of-space errors were found.

### Step 5: Tempdb Full Analysis
**Reference**: [tempdb-full-analysis.md](references/tempdb-full-analysis.md)

Provides detailed analysis of tempdb space usage and identifies potential causes of tempdb full conditions.

**Output Rule**: Only include this section in the report if tempdb issues were detected.

### Step 6: Out of Space Nodes
**Reference**: [out-of-space-nodes.md](references/out-of-space-nodes.md)

Identifies specific nodes experiencing out-of-space allocation failures from SQL errorlog (Errors 3257, 9002, 5149, 1105, 1101). Returns node-level details including available space, required space, and error timestamps.

**Output Rule**: Only include this section in the report if out-of-space errors were found on any node.

### Step 7: XStore Error Analysis
**Reference**: [xstore-error-analysis.md](references/xstore-error-analysis.md)

Analyzes XStore (Azure SQL Database storage layer) errors that may indicate storage-related issues. Checks for failed I/O requests (xio_failed_request events) on MDF, NDF, and LDF files.

**Output Rule**: Only include this section in the report if XStore errors were detected.

## Output Summary

After executing all steps, generate a summary containing **ONLY the issues that were detected**:

**Formatting Rules:**
1. **If NO issues detected in ANY sub-skill**: Display a single message: "✅ No disk space issues detected during the investigation period."
2. **If issues ARE detected**: Only list the sub-skills that found problems. Do not include rows for checks that passed.

**Example Output (with issues):**

| Check | Status | Details |
|-------|--------|---------|
| Data File Max Size | 🚩 | User DB data file reached 350 GB limit |
| Log File Max Size | 🚩 | User DB log file reached 180 GB limit |
| XStore Errors | 🚩 | 15 xio_failed_request events detected with error code 1117 |

*(Only shows the 3 checks that found issues; the other 4 checks are omitted because they passed)*

**Example Output (no issues):**

✅ No disk space issues detected during the investigation period.

## Sub-Skills Reference

| Step | Sub-Skill | File | Description |
|------|-----------|------|-------------|
| 1 | Drive Out of Space | [drive-out-of-space.md](references/drive-out-of-space.md) | Analyzes drive usage on nodes |
| 2 | Directory Quota Hit Limit | [directory-quota-hit-limit.md](references/directory-quota-hit-limit.md) | Checks App work/data directory quota |
| 3 | Data or Log Reached Max Size | [data-or-log-reached-max-size.md](references/data-or-log-reached-max-size.md) | Checks file size limits |
| 4 | Has Out of Space Issue | [has-out-of-space-issue.md](references/has-out-of-space-issue.md) | Detects allocation failure errors |
| 5 | Tempdb Full Analysis | [tempdb-full-analysis.md](references/tempdb-full-analysis.md) | Analyzes tempdb space usage |
| 6 | Out of Space Nodes | [out-of-space-nodes.md](references/out-of-space-nodes.md) | Node-level out-of-space details |
| 7 | XStore Error Analysis | [xstore-error-analysis.md](references/xstore-error-analysis.md) | Storage layer I/O errors |
