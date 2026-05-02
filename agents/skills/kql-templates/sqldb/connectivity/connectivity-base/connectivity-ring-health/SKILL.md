---
name: connectivity-ring-health
description: This skill checks the health of the connectivity ring by screening the logs for any anomalies, such as SNAT port exhaustion, gateway process restart, gateway deployment, and other potential issues on the connectivity ring. The skill will run a series of Kusto queries to analyze the logs and identify any potential issues that could impact connectivity. The output will be a summary of any anomalies found, which can help to determine if there is an issue with the connectivity ring that could be causing connectivity problems for customers.
---

**⚠️ ABSOLUTE REQUIREMENTS:**

1. ALWAYS run ALL queries in this task even if you already see anomalies from one query.
2. For GW1100, make sure you run the complete query by joining with the table cluster('azslb.kusto.windows.net').database('azslbmds').SlbHealthEvent.

```
// GW1100
// Confirm if SNAT port exhaustion happens on the connectivity rings
// Refer ".github/skills/Connectivity/connectivity-scenarios/understand-snat/SKILL.md" if SNAT port exhaustion happens.
// If the user gets a Kusto permission error, they may not have access to the Kusto cluster 'azslb.kusto.windows.net'. Please notify the user to request permission from "https://idwebelements.microsoft.com/GroupManagement.aspx?Group=AznwKustoReader&operation=join". For more information on Networking Kusto permissions, refer to the CSS wiki "https://msazure.visualstudio.com/AzureWiki/_wiki/wikis/AzureWiki.wiki/985089/AZN-Data-Access-Tools-Reference".
MonFabricClusters
| where name =~ '{ConnectivityRingName}'
| distinct ipv4_address
| join kind=inner (cluster('azslb.kusto.windows.net').database('azslbmds').SlbHealthEvent
| where env_time between (datetime({StartTime})..datetime({EndTime}))
| where HealthEventType in ("SnatPortExhaustion", "HighSnatPortUsage")
| where env_name == "##Microsoft.Networking.Slb.Core.Monitoring.SlbHealthEvent") on $left.ipv4_address == $right.VipOrIlbPA
| summarize count() by HealthEventType, bin(env_time, 5m)
| render timechart

// GW1110
// Gateway process restart. This could happen on limited nodes as isolated process crash, or an indicator for update deployment if this happened on multiple nodes at a time.
//
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where event =~ "process_login_finish"
| where package =~ 'xdbgateway'
| summarize total_processes = dcount(process_id, 4) by NodeName
| where total_processes > 1

// GW1111
// Confirm the code_package_version
//
MonLogin
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where event =~ "process_login_finish" and package =~ "xdbgateway" and AppName =~ "Gateway"
| summarize min(originalEventTimestamp), max(originalEventTimestamp) by NodeName, process_id, code_package_version
| sort by NodeName asc, min_originalEventTimestamp asc

// GW1112
// Gateway deployment traces
//
MonRolloutProgress
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where cluster_name =~ '{ConnectivityRingName}'
| where application_type_name == "Gateway" or  application_name == "fabric:/Gateway"
| where event in ("start_upgrade_app_type", "app_instance_upgrade_progress", "start_upgrade_app_instance", "start_pause_upgrade_app_type", "start_resume_upgrade_app_type", "set_start_post_bake_blast")
| project originalEventTimestamp, event, cluster_name, target_version, rollout_key, upgrade_state, upgrade_progress, bake_start_time, bake_duration
| extend RolloutKeyCab = extract("^([0-9]*)_(.*)", 1, rollout_key)
| project-away rollout_key
| order by originalEventTimestamp asc

// GW1114
// Gateway process restart event
//
MonRedirector
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where AppTypeName == "Gateway"
| where text startswith "Started XE session xdbgateway_logins"
| project originalEventTimestamp, NodeName, process_id, text

// GW1116
// Gateway process restart duration by MonRedirector
//
MonRedirector
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where AppTypeName =~ "Gateway"
| summarize ST = min(originalEventTimestamp), ET = max(originalEventTimestamp) by NodeName, process_id
| order by NodeName, ST asc
| extend GapInSecond = iff(next(NodeName) == NodeName, datetime_diff('second', next(ST), ET), long(0))
| extend StartTime = ET, EndTime = next(ST), Restart = strcat(process_id, " -> ", next(process_id))
| where GapInSecond != 0
| project NodeName, Restart, StartTime, EndTime, GapInSecond
| sort by StartTime asc

// GW1117
// Check if there were updates or repair tasks on the node. Repair task typically implies we detected some issues on the node.
WinFabLogs
| where ETWTimestamp between (datetime({StartTime})..datetime({EndTime})+3d) // add 3 days to the end time as a task may take very long to report completion
| where ClusterName =~ '{ConnectivityRingName}'
| where Text contains "RepairTask[scope=ClusterRepairScopeIdentifier, taskId="
| parse kind = regex Text with * "taskId=" TaskId ", version" * "state=" State ", flags" * "target=NodeRepairTargetDescription\\[nodeList = \\(" Node "\\)\\], executor" *
| project ClusterName, ETWTimestamp, TaskId, State, Node
| evaluate pivot(State, min(ETWTimestamp))

// GW1120
// AliasDB SF app health state
//
AlrWinFabHealthApplicationState
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where ApplicationName contains "Worker.ISO.Control"
| project ApplicationName, TIMESTAMP, HealthState, NodeName
| sort by ApplicationName asc, TIMESTAMP asc
| extend PrevTime = prev(TIMESTAMP)
| extend NextTime = next(TIMESTAMP)
| extend PrevHealthstate = prev(HealthState)
| extend PrevNodeName = prev(NodeName)
| extend PrevApplicationName = prev(ApplicationName)
| extend NextApplicationName = next(ApplicationName)
| where 
    isnull(PrevTime) or
    isnull(NextTime) or
    (HealthState != PrevHealthstate) or
    (NodeName != PrevNodeName) or
    (ApplicationName != PrevApplicationName) or
    (ApplicationName != NextApplicationName)
| project ApplicationName, TIMESTAMP, HealthState, NodeName
| sort by ApplicationName asc, TIMESTAMP asc

// GW1121
// AliasDB app partition event
//
AlrWinFabHealthPartitionEvent
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where ApplicationName contains "Worker.ISO.Control"
| summarize min(TIMESTAMP), max(TIMESTAMP), count(), take_any(Description) by PartitionId, ApplicationName

// GW1122
// Check if there are health events on nodes
//
AlrWinFabHealthNodeEvent
| where TIMESTAMP between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where HealthState != "Ok"
| project TIMESTAMP, NodeName, NodeEntityName, HealthState, SourceId, Property, Description

// GW1123
// SQL Alias update refresh latency. P90 over 1000 warrants attention.
//
MonRedirector
| where originalEventTimestamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where AppTypeName == "Gateway"    
| where event == "sql_alias_cache_refresh"
| summarize percentile(duration_ms, 90) by NodeName, bin(originalEventTimestamp, 5m)
| render timechart

// GW1130
// Error observed by DNS Cache. This suggests a potential DNS outage.
//
MonSqlDnsOverridePluginTrace
| where PreciseTimeStamp between (datetime({StartTime})..datetime({EndTime}))
| where ClusterName =~ '{ConnectivityRingName}'
| where FQDN != ""
| where TaskName =~ "DNS_result_override_begin" and Message contains "DNS_RCODE_SERVFAIL"
| summarize count() by strcat( Message,":", Error), bin(PreciseTimeStamp, 3m)
| render timechart
```
