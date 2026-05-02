---
name: readonly-capturemode-analysis
description: Analyze Query Data Store CaptureMode settings to identify potential configuration issues
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# QDS CaptureMode Skill

## Skill Overview

This skill analyzes Query Data Store (QDS) CaptureMode settings to identify potential configuration issues. It detects when CaptureMode is set to 'All' or 'Custom' with not recommended settings for capture_policy_execution_count, capture_policy_total_compile_cpu_ms, or capture_policy_total_execution_cpu_ms. When CaptureMode is set to Auto, fewer entries are persisted to QDS, reducing the likelihood of encountering a QDS ReadOnly state.

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
| Task 1 | Execute the Kusto query below | Always |

## Execution Steps

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithPreciseTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

```kql
let CaptureModeMessage= (CaptureModeAllCount:int,CaptureModeAllChange_Count:int,CustomCapture_PolicyExecutionPolicyCount:int,CustomCapture_PolicyExecutionPolicyChangeCount:int)
{
let CaptureModeAllChange_Count_message=case(CaptureModeAllChange_Count==0,"",
strcat("The CaptureMode was changed to 'All' ",CaptureModeAllChange_Count,iff(CaptureModeAllChange_Count==1," time", " times."))
);
let CaptureModeAllCount_Message=case(CaptureModeAllCount==0,"",
strcat("The CaptureMode in 'All' mode was detected ",CaptureModeAllCount,iff(CaptureModeAllCount==1," time", " times."))
);
let CustomCapture_PolicyExecutionPolicyChangeCount_message=case(CustomCapture_PolicyExecutionPolicyChangeCount==0,"",
strcat(" The CaptureMode was changed to 'Custom' with not recommended capture_policy_execution_count/capture_policy_total_compile_cpu_ms/capture_policy_total_execution_cpu_ms ",CustomCapture_PolicyExecutionPolicyChangeCount,iff(CustomCapture_PolicyExecutionPolicyChangeCount==1," time", " times."))
);
let CustomCapture_PolicyExecutionPolicyCount_message=case(CustomCapture_PolicyExecutionPolicyCount==0,"",
strcat(" The CaptureMode in 'Custom' with not recommended capture_policy_execution_count/capture_policy_total_compile_cpu_ms/capture_policy_total_execution_cpu_ms  was detected ",CustomCapture_PolicyExecutionPolicyCount,iff(CustomCapture_PolicyExecutionPolicyCount==1," time", " times."))
);
let BenefitsMessage=case(CaptureModeAllChange_Count+CaptureModeAllCount+CustomCapture_PolicyExecutionPolicyChangeCount+CustomCapture_PolicyExecutionPolicyCount==0,"",
strcat(" Please change CaptureMode to  Auto. Benefits:When CaptureMode is set to Auto, fewer entries are persisted to QDS, reducing the likelihood of encountering a QDS ReadOnly state with ReadOnlyReason 65536/262144.")
);
strcat(CaptureModeAllChange_Count_message,CaptureModeAllCount_Message,CustomCapture_PolicyExecutionPolicyChangeCount_message,CustomCapture_PolicyExecutionPolicyCount_message,BenefitsMessage)
};
let setting1=(MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name  =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_and_state'
| summarize CaptureModeAllCount=countif(capture_policy_mode =~ 'x_qdsCaptureModeAll'),CustomCapture_PolicyExecutionPolicyCount=countif(capture_policy_mode=~'x_qdsCaptureModeCustom' and (capture_policy_execution_count<30 or capture_policy_total_compile_cpu_ms<1000 or capture_policy_total_execution_cpu_ms<100))
| extend joinColumn=1);
let setting2=(MonQueryStoreInfo
| where {AppNamesNodeNamesWith7DayOriginalEventTimeRange}
| where LogicalServerName =~ '{LogicalServerName}' and logical_database_name  =~ '{LogicalDatabaseName}'
| where event == 'query_store_db_settings_changed'
| summarize
captureModeAllChange_Count=countif(capture_policy_mode_old=~ 'x_qdsCaptureModeAll' or capture_policy_mode_new =~ 'x_qdsCaptureModeAll'),
CustomCapture_PolicyExecutionPolicyChangeCount=countif(
(capture_policy_execution_count_old<30 or capture_policy_total_compile_cpu_ms_old<1000 or capture_policy_total_execution_cpu_ms_old<100) or
(capture_policy_execution_count_new<30 or capture_policy_total_compile_cpu_ms_new<1000 or capture_policy_total_execution_cpu_ms_new<100)
)
|extend joinColumn=1);
setting1
| join kind=inner (setting2) on joinColumn
| where CaptureModeAllCount>0 or captureModeAllChange_Count>0 or CustomCapture_PolicyExecutionPolicyCount>0 or CustomCapture_PolicyExecutionPolicyChangeCount>0
| extend captureModeMessage=CaptureModeMessage(CaptureModeAllCount,captureModeAllChange_Count,CustomCapture_PolicyExecutionPolicyCount,CustomCapture_PolicyExecutionPolicyChangeCount)
| project captureModeMessage
```

#### Output
Please follow the instructions carefully. We want to avoid generating large or unrelated outputs that may confuse the end user. Only display the information specified:
1. If the Task3 returns results, display the exact message from the `captureModeMessage` column without any modifications.
2. If the Task3 doesn't return any result, display the following message exactly as written: "We didn't identify any obvious issues in the QDS CaptureMode settings."

