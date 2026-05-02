---
name: xevent-session-detection
description: This skill detects and analyzes extended event sessions configured on a database to understand event retention modes and session configurations
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

!!!AI Generated. To be verified!!!

# Debug Xevent Session Detection

## Skill Overview

This skill detects extended event (XEvent) sessions configured on a database. It identifies session names, event types, and event retention modes to help diagnose potential issues related to XEvent session configurations. Understanding event retention modes is critical as improper configurations can impact performance or lead to event loss.

## Prerequisites

- Access to Kusto clusters for SQL telemetry

## Required Parameters

| Parameter | Description | Format | Example |
|-----------|-------------|--------|---------|
| `{LogicalServerName}` | Azure SQL logical server name | string | `myserver` |
| `{StartTime}` | Investigation start time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 10:00` |
| `{EndTime}` | Investigation end time | UTC: yyyy-MM-dd HH:mm | `2026-01-15 12:00` |

## Workflow Overview

**This skill has 1 task.**

| Task | Description | Condition |
|------|-------------|----------|
| Task 1 | Execute Kusto query to detect XEvent sessions | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let mapping=datatable(buffer_flush_policy:long, EVENT_RETENTION_MODE:string, buffer_flush_policyName:string) 
[ 
    0, 'ALLOW_SINGLE_EVENT_LOSS', 'XESBP_DROP_EVENT', 
    1, 'NO_EVENT_LOSS', 'XESBP_BLOCK', 
    2, 'Unknown', 'XESBP_ALLOC', 
    3, 'ALLOW_MULTIPLE_EVENT_LOSS', 'XESBP_DROP_BUFFER',      
]; 
MonXeventsTelemetry
| where {AppNamesNodeNamesWithOriginalEventTimeRange}
| where event != 'xio_failed_request'
| where LogicalServerName =~ '{LogicalServerName}'
| join kind=leftouter (mapping) on buffer_flush_policy 
| project TIMESTAMP, AppName, database_name, event, session_name, EVENT_RETENTION_MODE, NodeName, ClusterName
| order by TIMESTAMP
| take 100
```

### Task 1 Output

| Column | Type | Description | Output Column Name |
|--------|------|-------------|-------------------|
| `TIMESTAMP` | datetime | Time when the event was recorded | Timestamp |
| `AppName` | string | Application identifier | App Name |
| `database_name` | string | Database name where session is configured | Database Name |
| `event` | string | XEvent type being captured | Event Type |
| `session_name` | string | Name of the extended event session | Session Name |
| `EVENT_RETENTION_MODE` | string | Event retention mode configuration | Retention Mode |
| `NodeName` | string | SQL node hosting the database | Node Name |
| `ClusterName` | string | Cluster hosting the node | Cluster Name |

### Issue Detection Logic

- **XEvent sessions found** → 🚩 Display warning about potential performance impact
- **Multiple sessions found** → ⚠️ Review if all sessions are necessary as each session adds overhead
- **No sessions found** → 🟢 No custom XEvent sessions detected during the investigation period

---

## Appendix A: Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When XEvent Sessions Are Detected

#### XEvent Session Detection Results

**XEvent sessions were detected during the investigation period.**

> 🚩 **Warning**: Active user-created XEvent sessions were detected. User XEvent sessions have historically caused performance issues including CPU pressure, login outages, and overall system degradation. These sessions can consume significant system resources and impact database performance. Consider disabling or removing unnecessary user XEvent sessions. If XEvent sessions are required, ensure they use appropriate filtering and target smaller event sets.

#### XEvent Sessions Summary

| Session Name | Event Type | Retention Mode | Database |
|--------------|------------|----------------|----------|
| query_tracking | sql_statement_completed | ALLOW_SINGLE_EVENT_LOSS | mydb |
| error_capture | error_reported | ALLOW_MULTIPLE_EVENT_LOSS | mydb |

#### Analysis

The following XEvent sessions were detected on the logical server:

- **query_tracking**: Uses `ALLOW_SINGLE_EVENT_LOSS` retention mode - this is safe and will drop individual events if buffer is full
- **error_capture**: Uses `ALLOW_MULTIPLE_EVENT_LOSS` retention mode - this is safe and will drop entire buffers if full

#### Root Cause Indicators

This pattern suggests:
- **Custom monitoring in place** - User has configured XEvent sessions for monitoring

---

### When No XEvent Sessions Are Detected

#### XEvent Session Detection Results

**No custom XEvent sessions were detected during the investigation period.**

#### Analysis

No extended event sessions were found on the logical server during the specified time range. This indicates:
- No custom monitoring via XEvents is in place, OR
- XEvent sessions were not active during this period

---

### Output Format Requirements

1. **Always start with a direct answer** - State clearly whether XEvent sessions were detected
2. **Use the retention mode table** - Map buffer_flush_policy values to their descriptions
3. **Include a summary table** - Present all detected sessions with their configurations
4. **Provide analysis** - Explain the implications of each session configuration
5. **Use ⚠️ emoji** - Flag situations requiring attention (multiple sessions, unusual configurations)
6. **Use 🟢 emoji** - Indicate safe configurations or no issues detected

---

## Appendix B: Event Retention Mode Details (Reference Only)

> **Note**: This section provides additional context on event retention modes for troubleshooting.

| Retention Mode | When to Use | Performance Impact |
|----------------|-------------|-------------------|
| ALLOW_SINGLE_EVENT_LOSS | Default for most scenarios - acceptable to lose individual events | Minimal - events dropped under pressure |
| ALLOW_MULTIPLE_EVENT_LOSS | High-volume tracing where some loss is acceptable | Minimal - entire buffers dropped under pressure |
