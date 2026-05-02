---
name: error-17900-state-25
description: This error occurs when a TdsProtocolError is encountered with error code 17900 and state 25. It typically indicates an issue with the TDS protocol communication between the client and the SQL Server, which can lead to a session disconnect. This error is often seen in scenarios involving Multiple Active Result Sets (MARS) connections, where multiple underlying connections are used within a single session.
---

## Potential Causes
Potential causes for this error include:
- Network issues causing interruptions in the TDS protocol communication.
- Client improperly handling closure of result sets in MARS connections.
- Client-side issues with the TDS protocol implementation.
- Resource constraints on the SQL Server leading to session disconnects.


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


## Troubleshooting Steps

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


### 3: Get Details

Sample Kusto Query:
```
let startDT = datetime(2026-04-01 10:38);
let endDT = datetime(2026-04-01 12:32);
let serverName = "v33kcbn4iu";
let dbName = "Content_86177_108";
let frequentCxPeerId = MonLogin
| where originalEventTimestamp between (startDT .. endDT)
| where logical_server_name =~ serverName and database_name =~ dbName
| where error == 17900 and state == 25
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
2. Sample Output:

| originalEventTimestamp      | AppName      | package   | event                    | is_success | is_user_error | is_mars | error | state | kill_reason      | connection_id                        | connection_peer_id                   | total_time_ms | message                    | extra_info                                                                                |
|-----------------------------|--------------|-----------|--------------------------|------------|---------------|---------|-------|-------|------------------|--------------------------------------|--------------------------------------|---------------|----------------------------|-------------------------------------------------------------------------------------------|
| 2026-04-01 12:03:41.1486001 | Worker       | xdbhost   | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 7CDB5E11-FA0B-4B69-BA08-088699E5A43C | 2030AF5E-403B-4A9D-91AB-227B062EF94E | 6             |                            | <events><Ack_Received_FromSQL>5</Ack_Received_FromSQL></events>                           |
| 2026-04-01 12:03:41.1526099 | f24c8d476f1e | sqlserver | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 266DD04A-A0B5-45A7-B57E-72061FC5F149 | 2030AF5E-403B-4A9D-91AB-227B062EF94E | 7             | <waitstats>...</waitstats> | <events><NspLoginCheckEnd>4</NspLoginCheckEnd></events>                                   |
| 2026-04-01 12:08:07.5813671 | f24c8d476f1e | sqlserver | process_close_connection |            |               | FALSE   | 17900 | 25    | TdsProtocolError | 266DD04A-A0B5-45A7-B57E-72061FC5F149 | 2030AF5E-403B-4A9D-91AB-227B062EF94E |               |                            | <events><NspLoginCheckEnd>4</NspLoginCheckEnd><Error_SniRead>121</Error_SniRead></events> |

In this output, we can observe the sequence of events leading up to the session disconnects. This example shows only a single connection_peer_id, but there may be up to 3 of them, each with their own connection sequence like the 1 shown here. The first row is a successful login completion from the perspective of xdbhost. The second row is a successful login completion from the perspective of sqlserver. The third row indicates a session disconnect event from sqlserver with error 17900 and state 25, along with the kill reason "TdsProtocolError". The `extra_info` column provides additional context about the events, including the `Error_SniRead` value, which may help in diagnosing the root cause of the disconnect.

The `is_mars` column is also of note here, as it indicates whether the session was using Multiple Active Result Sets (MARS). In this case, the value is `FALSE`, meaning MARS was not in use for this session. This information can be relevant when diagnosing session disconnects, as MARS sessions may have different behaviors and potential issues compared to non-MARS sessions. For MARS connections it is possible that some connections will close propertly while others do not, which will throw a session disconnect error.

4. Another Sample Output:

| originalEventTimestamp  | AppName      | package    | event                    | is_success | is_user_error | is_mars | error | state | kill_reason      | connection_id                        | connection_peer_id                   | total_time_ms | message                    | extra_info                                                                                                                                                                                                                                                                                 |
|-------------------------|--------------|------------|--------------------------|------------|---------------|---------|-------|-------|------------------|--------------------------------------|--------------------------------------|---------------|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2026-04-01 10:38:48.351 | Worker       | xdbhost    | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 8493A41D-54AC-4B81-BCA7-471BDC582265 | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE | 18            |                            | <events><End_ProcessLogin>29</End_ProcessLogin><Ack_Received_FromSQL>30</Ack_Received_FromSQL></events>                                                                                                                                                                                    |
| 2026-04-01 10:38:48.352 | Gateway      | xdbgateway | process_login_finish     | TRUE       | FALSE         | FALSE   | 0     | 0     |                  | 70A888C7-474D-4443-BE59-67803DDCC4FA | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE | 3             | <waitstats>...</waitstats> | <events><InitSecurityContext>2</InitSecurityContext><Proxy_Login>42</Proxy_Login></events>                                                                                                                                                                                                 |
| 2026-04-01 10:38:48.352 | f8d1a83d14b2 | sqlserver  | process_login_finish     | TRUE       | FALSE         | TRUE    | 0     | 0     |                  | 86198C9A-5292-4052-A208-0E3CEF3A4867 | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE |               |                            | <events><Init_TDSDuplicateConnection>0x00000244FBEA8050</Init_TDSDuplicateConnection><LoginTask_SchedulerId>10</LoginTask_SchedulerId><LoginTask_CpuId>10</LoginTask_CpuId><Wait_LoginDispatcher>0</Wait_LoginDispatcher><SocketDupAckSentToXdbHost>0</SocketDupAckSentToXdbHost></events> |
| 2026-04-01 10:38:48.371 | f8d1a83d14b2 | sqlserver  | process_close_connection |            |               | TRUE    | 0     | 0     | NormalLogout     | 86198C9A-5292-4052-A208-0E3CEF3A4867 | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE |               |                            | <events><Init_TDSDuplicateConnection>0x00000244FBEA8050</Init_TDSDuplicateConnection><LoginTask_SchedulerId>10</LoginTask_SchedulerId><LoginTask_CpuId>10</LoginTask_CpuId><Wait_LoginDispatcher>0</Wait_LoginDispatcher><SocketDupAckSentToXdbHost>0</SocketDupAckSentToXdbHost></events> |
| 2026-04-01 10:38:48.371 | f8d1a83d14b2 | sqlserver  | process_close_connection |            |               | TRUE    | 17900 | 25    | TdsProtocolError | CF86007B-72C8-4E4E-8BF5-D405C32F449C | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE |               | <waitstats>...</waitstats> | <events><Init_SniMutex>0</Init_SniMutex></events>                                                                                                                                                                                                                                          |
| 2026-04-01 10:38:48.371 | f8d1a83d14b2 | sqlserver  | process_close_connection |            |               | TRUE    | 17900 | 25    | TdsProtocolError | 403BD483-7083-4A89-A153-68D239F5FB34 | 467A316F-E5B6-4903-AE57-FEE1AC5A94EE |               |                            | <events><Init_SniMutex>0</Init_SniMutex></events>                                                                                                                                                                                                                                          |

This example shows a scenario with 3 MARS connections to sqlserver, again as part of a single connection_peer_id. 1 closed correctly, while the other 2 experienced a TdsProtocolError with error code 17900 and state 25, leading to a session disconnect. This illustrates how a MARS connection can have multiple underlying connections, and if some of them fail to close properly, it can result in a session disconnect error.


## Output
Based on the query results, output a summary of the session disconnect events caused by error 17900 state 25. Explain when the error occurred, if MARS connections were involved, and the impact on the session. If there are notable values for `kill_reason`, `message` or `extra_info`, include them in the summary.


## Suggested TSG
https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/connection/tds-protocol-error
