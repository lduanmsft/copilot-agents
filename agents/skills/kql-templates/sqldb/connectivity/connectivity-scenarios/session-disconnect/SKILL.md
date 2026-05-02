---
name: session-disconnect
description: Debug Azure SQL Database session disconnect issues including unexpected disconnections, timeouts, and related problems. Use when investigating SQL Database session stability issues. Accepts either ICM ID or direct parameters (logical server name, database name, time window). Executes Kusto queries via Azure MCP to analyze telemetry data including session events, disconnects, and timeout occurrences.
---

# Debug Azure SQLDB Session Disconnect Issues

## Required Information

This skill requires the following inputs (should be obtained by the calling agent):

### From User or ICM:
- **Logical Server Name** (e.g., `my-server`)
- **Logical Database Name** (e.g., `my-db`)
- **StartTime** (UTC format: `2026-01-01 02:00:00`)
- **EndTime** (UTC format: `2026-01-01 03:00:00`)

### From execute-kusto-query skill:
- **kusto-cluster-uri** (e.g., `https://sqlazureeus12.kusto.windows.net:443`)
- **kusto-database** (e.g., `sqlazure1`)
- **region** (e.g., `eastus1`)

### From get-db-info skill (one or more configurations):
- **AppName** (sql_instance_name)
- **ClusterName** (tenant_ring_name)
- **logical_database_id**
- **physical_database_id**
- **fabric_partition_id**
- **service_level_objective**
- **zone_resilient**
- **deployment_type** (e.g., "GP without ZR", "GP with ZR", "BC")
- **config_start_time** (when this configuration was active from)
- **config_end_time** (when this configuration was active until)
- All other database environment variables

**Note**: The calling agent should use the `execute-kusto-query` skill and the `get-db-info` skill before invoking this skill. If multiple database configurations exist (e.g., tier change during incident), the agent should invoke this skill separately for each configuration with its respective time window.

**Note**: For a better understanding of session disconnect issues, [knowledge.md](references/knowledge.md) explains how to correlate login events across the different components that participate in the login process. This file also contains definitions of commonly-used debugging columns that are relevant when investigating session disconnects.


## Workflow

**Important**: Output the results from each step as specified, and ensure to complete the execution verification checklist before providing any conclusions or summaries to the user.

### 1: Validate Inputs

Ensure all required parameters are provided:
- From user/ICM: LogicalServerName, LogicalDatabaseName, StartTime, EndTime
- From execute-kusto-query: kusto-cluster-uri, kusto-database, region
- From get-db-info: AppName, ClusterName, physical_database_id, fabric_partition_id, deployment_type, config_start_time, config_end_time, and all other database variables

**Note**: If analyzing a specific database configuration (when multiple exist), use config_start_time and config_end_time to scope the analysis to that configuration's active period.

Calculate `Duration` between StartTime and EndTime (e.g., `1h`, `101m`).

### 2: Determine login target
Follow **.github/skills/Connectivity/connectivity-base/determine-login-target/SKILL.md** skill.

### 3: Analyze session disconnects

Analyze the server/database over the relevant time period to identify and troubleshoot applicable session disconnect events.

#### Query 1: Session Disconnect Events

Sample Kusto Query 1:
```
let startDT = datetime(2026-04-01 10:38);
let endDT = datetime(2026-04-01 12:32);
let serverName = "v33kcbn4iu";
let dbName = "Content_86177_108";
MonLogin
| where originalEventTimestamp between (startDT .. endDT)
| where logical_server_name =~ serverName and database_name =~ dbName
| where event in~ ("proxy_close_connection","process_close_connection")
| where isnotempty(error) and error != 0
| summarize n=count() by error, state, package, event
| sort by n;
```

Note: 
1. The `startDT`, `endDT`, `serverName` and `dbName` are variables which can be input by user, and correspond to the input variables for this skill defined above.
2. Sample Output:

| error | state | package    | event                  | n   |
|-------|-------|------------| -----------------------|-----|
| 17900 | 25    | sqlserver  | proxy_close_connection | 820 |
| 7885  | 8     | sqlserver  | proxy_close_connection | 2   |

In this output, the most prevalent issue is error 17900 state 25, which occurred 820 times. This indicates that the majority of session disconnects during the specified time window were caused by this particular error. The secondary issue, error 7885 state 8, occurred only 2 times and is less significant in comparison.

The most common issue will likely occur significantly more frequently than the secondary issue, indicating that error 17900 state 25 is the primary cause of session disconnects during the specified time window. 

Using the error and state values from the most common issue (error 17900 state 25), the agent further investigate the root cause of the session disconnects with the following query.

**important** If the most common error is NOT error 17900 state 25, continue executing this skill as normal. If the most common error IS error 17900 state 25, do not execute the "Query 2" section below. Instead, do the following:
- Follow **.github/skills/Connectivity/connectivity-errors/error-17900-state-25/SKILL.md** skill and output the data analysis.
- Execute the "Output" section located after the "Query 2" section.

#### Query 2: Session Disconnect Events for the Most Common Error

Sample Kusto Query 2:
```
let startDT = datetime(2026-04-01 10:38);
let endDT = datetime(2026-04-01 12:32);
let serverName = "v33kcbn4iu";
let dbName = "Content_86177_108";
let errorCode = 7885;
let errorState = 8;
let frequentCxPeerId = MonLogin
| where originalEventTimestamp between (startDT .. endDT)
| where logical_server_name =~ serverName and database_name =~ dbName
| where event in~ ("proxy_close_connection","process_close_connection")
| where error == errorCode and state == errorState
| summarize n=count() by connection_peer_id
| sort by n
| take 3
| project connection_peer_id;
MonLogin
| where originalEventTimestamp between (startDT-30m .. endDT+30m)
| where connection_peer_id in (frequentCxPeerId)
| project originalEventTimestamp, AppName, package, event, is_success, is_user_error, is_mars, error, 
    state, kill_reason, connection_id, connection_peer_id, total_time_ms, message, extra_info
| order by connection_peer_id asc, originalEventTimestamp asc;
```

Note:
1. The `startDT`, `endDT`, `serverName` and `dbName` variables should be the same as used for Sample Kusto Query 1.
2. The `errorCode`, and `errorState` variables should be the same as the most common error identified in Sample Kusto Query 1.
3. Sample Output:

| originalEventTimestamp      | AppName      | package   | event                    | is_success | is_user_error | is_mars | error | state | kill_reason      | connection_id                        | connection_peer_id                   | total_time_ms | message                    | extra_info                                                                                |
|-----------------------------|--------------|-----------|--------------------------|------------|---------------|---------|-------|-------|------------------|--------------------------------------|--------------------------------------|---------------|----------------------------|-------------------------------------------------------------------------------------------|
| 2026-04-01 12:03:41.1486001 | Worker       | xdbhost   | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 7CDB5E11-FA0B-4B69-BA08-088699E5A43C | 2030AF5E-403B-4A9D-91AB-227B062EF94E | 6             |                            | <events><Ack_Received_FromSQL>5</Ack_Received_FromSQL></events>                           |
| 2026-04-01 12:03:41.1526099 | f24c8d476f1e | sqlserver | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 266DD04A-A0B5-45A7-B57E-72061FC5F149 | 2030AF5E-403B-4A9D-91AB-227B062EF94E | 7             | <waitstats>...</waitstats> | <events><NspLoginCheckEnd>4</NspLoginCheckEnd></events>                                   |
| 2026-04-01 12:08:07.5813671 | f24c8d476f1e | sqlserver | process_close_connection |            |               | FALSE   | 7885  | 8     | TdsProtocolError | 266DD04A-A0B5-45A7-B57E-72061FC5F149 | 2030AF5E-403B-4A9D-91AB-227B062EF94E |               |                            | <events><NspLoginCheckEnd>4</NspLoginCheckEnd><Error_SniRead>121</Error_SniRead></events> |

In this output, we can observe the sequence of events leading up to the session disconnects. This example shows only a single connection_peer_id, but there may be up to 3 of them, each with their own connection sequence like the 1 shown here. The first row is a successful login completion from the perspective of xdbhost. The second row is a successful login completion from the perspective of sqlserver. The third row indicates a session disconnect event from sqlserver with error 7885 and state 8, along with the kill reason "TdsProtocolError". The `extra_info` column provides additional context about the events, including the `Error_SniRead` value, which may help in diagnosing the root cause of the disconnect.

The `is_mars` column is also of note here, as it indicates whether the session was using Multiple Active Result Sets (MARS). In this case, the value is `FALSE`, meaning MARS was not in use for this session. This information can be relevant when diagnosing session disconnects, as MARS sessions may have different behaviors and potential issues compared to non-MARS sessions. For MARS connections it is possible that some connections will close propertly while others do not, which will throw a session disconnect error.

4. Another Sample Output:

| originalEventTimestamp  | AppName      | package    | event                    | is_success | is_user_error | is_mars | error | state | kill_reason      | connection_id                        | connection_peer_id                   | total_time_ms | message                    | extra_info                                                                                                                                                                                                                                                                                 |
|-------------------------|--------------|------------|--------------------------|------------|---------------|---------|-------|-------|------------------|--------------------------------------|--------------------------------------|---------------|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2026-04-01 10:38:48.351 | Worker       | xdbhost    | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 8493A41D-54AC-4B81-BCA7-471BDC582265 | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE | 18            |                            | <events><End_ProcessLogin>29</End_ProcessLogin><Ack_Received_FromSQL>30</Ack_Received_FromSQL></events>                                                                                                                                                                                    |
| 2026-04-01 10:38:48.352 | Gateway      | xdbgateway | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 70A888C7-474D-4443-BE59-67803DDCC4FA | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE | 3             | <waitstats>...</waitstats> | <events><InitSecurityContext>2</InitSecurityContext><Proxy_Login>42</Proxy_Login></events>                                                                                                                                                                                                 |
| 2026-04-01 10:38:48.352 | f8d1a83d14b2 | sqlserver  | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 86198C9A-5292-4052-A208-0E3CEF3A4867 | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE |               |                            | <events><Init_TDSDuplicateConnection>0x00000244FBEA8050</Init_TDSDuplicateConnection><LoginTask_SchedulerId>10</LoginTask_SchedulerId><LoginTask_CpuId>10</LoginTask_CpuId><Wait_LoginDispatcher>0</Wait_LoginDispatcher><SocketDupAckSentToXdbHost>0</SocketDupAckSentToXdbHost></events> |
| 2026-04-01 10:38:48.371 | f8d1a83d14b2 | sqlserver  | process_close_connection |            |               | FALSE   | 0     | 0     | NormalLogout     | 86198C9A-5292-4052-A208-0E3CEF3A4867 | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE |               |                            | <events><Init_TDSDuplicateConnection>0x00000244FBEA8050</Init_TDSDuplicateConnection><LoginTask_SchedulerId>10</LoginTask_SchedulerId><LoginTask_CpuId>10</LoginTask_CpuId><Wait_LoginDispatcher>0</Wait_LoginDispatcher><SocketDupAckSentToXdbHost>0</SocketDupAckSentToXdbHost></events> |
| 2026-04-01 10:38:48.371 | f8d1a83d14b2 | sqlserver  | process_close_connection |            |               | FALSE   | 7885  | 8     | TdsProtocolError | CF86007B-72C8-4E4E-8BF5-D405C32F449C | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE |               | <waitstats>...</waitstats> | <events><Init_SniMutex>0</Init_SniMutex></events>                                                                                                                                                                                                                                          |
| 2026-04-01 10:38:48.371 | f8d1a83d14b2 | sqlserver  | process_close_connection |            |               | FALSE   | 7885  | 8     | TdsProtocolError | 403BD483-7083-4A89-A153-68D239F5FB34 | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE |               |                            | <events><Init_SniMutex>0</Init_SniMutex></events>                                                                                                                                                                                                                                          |

This example shows a scenario with multiple connections to sqlserver, again as part of a single connection_peer_id. 1 closed correctly, while the other 2 experienced a TdsProtocolError with error code 7885 and state 8, leading to a session disconnect. This illustrates how if some connections fail to close properly, it can result in a session disconnect error.

### 4: Output

4.1: Share the top 2 results of Query 1 above, and explain what the most prevalent error was and the significance of these results in the context of the session disconnect.

4.2: Based on the results of Query 2 above (or the outout of a different skill that analyzed the session disconnect), inform the user of the cause of the session disconnect for the specified connection_peer_id. Example: The session disconnect was caused by a TdsProtocolError, with error code 7885 and state 8. The `extra_info` column indicates that there was an `Init_SniMutex` with value 0, which may have contributed to the disconnect. Additionally, the session was using Multiple Active Result Sets (MARS), which can influence the behavior of session disconnects.

4.3: If the session disconnect was caused by error 17900 and state 25, refer them to the [TSG](https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/connection/tds-protocol-error) covering this error. If MARS connections are enabled, that TSG also contains helpful content.

4.4: If the session disconnect was caused by a different error or state, refer the user to the appropriate TSG for that specific error or state. If unsure of what content to refer to, use the bluebird-mcp-sql tool to search for the error code and state, it should provide relevant documentation or guidance. The bluebird-mcp-sql tool can be accessed using the following syntax:

```
/mcp.bluebird-mcp-sql what does error_code=<error_code> state=<state> mean?
```

4.5: Suggest to the user that they obtain a client-side networking trace and review it with Azure Networking CSS to help diagnose the root cause of the session disconnect.
** This is a MUST output.**

4.6: Suggest to the user that they make sure they understand the end-to-end (e2e) network path between the client and the server, such as any NVA in place, connection policy, etc. Network issues along this path can contribute to session disconnects.
** This is a MUST output.**


## Reference

- [knowledge.md](references/knowledge.md) — Definitions and key learnings for how to correlate MonLogin events across components.
