# Debug Principles for Availability Issues

## Principles for AddPrimary Events (GP without ZR)

1. **Write Status GRANTED** should happen shortly after AddPrimary (failover)
   - If this happens quickly, failover is good
   - No need for further analysis for this failover

2. **Image Download Event** must occur:
   - Can be shortly before or after AddPrimary
   - If too far after AddPrimary, Service Fabric is delaying it (not normal)

3. **CodePackage Activation Event** must occur:
   - Can be shortly before or after AddPrimary
   - If too far after AddPrimary, Service Fabric is delaying it (not normal)

4. **SQL Process Starting Event** must occur:
   - Must be close to AddPrimary event time

5. **After SQL Process Starts**, these events should follow within 5 minutes:
   - **Tempdb Recovery Completed**: Should be short (typically 1-3 seconds)
   - **CFabricReplicaManager Initialized**: Critical to create replicas and accept connections
     - If >5 minutes, indicates Service Fabric coordination or resource issues
   - **SQL Server Ready for Connections**: Message "SQL Server is now ready for client connections"

## Principles for All Failover Types (New Primary Node)

### SQL Instance Level Analysis

1. **Error Message Events** (Check using query HA4000):
   - **Purpose**: Identify SQL Server errors during failover that may indicate problems
   - **Common expected errors during failover**:
     - **Error 18401**: Login failed errors (transient during failover transition)
       - Full message: `Error: 18401, Severity: 14, State: 1. Reason: Server is in script upgrade mode. Only administrator can connect at this time.%2`
       - This error is expected during failover when server is transitioning
     - **Error 9001**: Database log errors (can occur during recovery)
   - **What to check**:
     - Error count and frequency
     - First seen vs last seen timestamps
     - Duration of error occurrence
   - **Normal behavior**:
     - Errors should be transient (within 5 minutes of failover)
     - Error count should be low
     - Errors should stop after failover completes
   - **🚩 Problematic patterns**:
     - Errors lasting >5 minutes after failover start
     - High error count (hundreds or thousands)
     - Errors continuing well after Write Status GRANTED
     - New unexpected error types (not 18401 or 9001)
   - **Action**: If errors are prolonged or unusual, include HA4000 query results in output
   - **CRITICAL: Analysis guidance for problematic Error 18401**:
     - Calculate duration: (LastSeenTimeStamp - FirstSeenTimestamp)
     - If duration >5 minutes, this is a **PRIMARY AVAILABILITY ISSUE**, not a secondary issue
     - Report in Root Cause Analysis section with exact time window: "Error 18401 persisted from [FirstSeenTimestamp] to [LastSeenTimeStamp] ([X] minutes, expected < 5 minutes), indicating the server remained in script upgrade mode during this period, preventing non-administrator connections."
     - Include this time window in the "Impact Summary" section as a contributor to database unavailability
     - This suggests issues with server initialization or upgrade process completion and directly causes connection failures

2. **SQL Instance Errorlog Gaps** (Check using query HA4010):
   - **Purpose**: Detect telemetry gaps that could hide problems
   - **What to check**: Continuous telemetry flow during failover window
   - **Normal behavior**: Consistent log entries throughout failover
   - **🚩 Problematic**: Gaps >5 minutes indicate monitoring or SQL process issues

3. **Recovery Completed for Database Event** (Check using query HA4020):
   - **Purpose**: Verify database recovery completed successfully
   - **What to check**: 
     - Recovery completion timestamp
     - Time from failover start to recovery completion
   - **Normal behavior**: Recovery completes shortly after failover
   - **🚩 Problematic**: 
     - Recovery takes >5 minutes
     - No recovery completion event found
     - Recovery failures or errors

4. **XEvent Analysis** (Check using query HA5000):
   - **Purpose**: Analyze Service Fabric role change operations
   - **Required events**:
     - `hadr_fabric_api_replicator_begin_change_role` must appear shortly after failover
     - Must have matching `hadr_fabric_api_replicator_end_change_role`
   - **Matching criteria**: Events match when `work_id` and `process_id` are identical
   - **Normal behavior**: Matching end event should happen shortly after begin event
   - **🚩 Problematic**:
     - Missing begin or end event
     - Unmatched events (no corresponding begin/end pair)
     - Long duration between begin and end (>5 minutes)
     - Multiple begin events without corresponding end events

### Telemetry Quality Check

5. **Telemetry Gaps** (Check using query HA3000):
   - **Purpose**: Ensure telemetry is reliable during investigation window
   - **What to check**: Count of messages per 5-minute bin
   - **Normal behavior**: Consistent message count throughout window
   - **🚩 Problematic**: 
     - 5-minute periods with zero messages
     - Significant drops in message volume
     - Extended gaps (>10 minutes)
   - **Action**: If gaps exist, note that analysis may be incomplete

## Expected Timings

- **Shortly**: 5 minutes or less
- **Tempdb Recovery**: 1-3 seconds
- **CFabricReplicaManager**: <5 minutes
- **SQL Ready**: <5 minutes
- **Error Events Duration**: <5 minutes (transient during failover)
- **Database Recovery**: <5 minutes after failover
- **XEvent Begin to End**: <5 minutes (within same failover window)
- **Telemetry**: Continuous (no gaps >5 minutes)

## Analysis Workflow

For each failover:
1. Execute all queries from references/queries.md
2. Compare results against expected timings above
3. Mark events with ✅ (normal) or 🚩 (problematic)
4. For 🚩 events:
   - Include actual query with parameters in output
   - Include result summary
   - Explain deviation from expected behavior
5. Do NOT speculate - base conclusions only on observed data and these principles

## Checking for Process Terminations

Look for gaps in the entries in the SQL Server error log (found in the `MonSQLSystemHealth` Kusto table). Use the `HA6005` query to summarize the SQL Server error log entries by process. If there are any gaps (as indicated by the `hours_present` or `gap_from_previous_in_seconds` column values), then check for process terminations.

First, look for patterns in the process activations and terminations (deactivations) as seen from the Service Fabric level. Use the `HA6010` query to list the pairs of process activations and process terminations. It is normal for the following properties:

- For the "XdbLaunchSqlSetup.exe" process, it is common to see very brief executions (under ten seconds long) with `ExitCode` column values of `0`.

- For the "sqlservr.exe" process, it is common to see a "CodePackageActivated" event without a corresponding "CodePackageDeactivated" event (which shows that SQL Server began executing and continued executing for a long period of time).

- Very few overall process activations and terminations within each hour.

- If there is a process termination for the "sqlservr.exe" process, the `ExitCode` column value should be `0`.

Abnormal (and thus noteworthy) properties include the following:

- Frequent process terminations.

- Process terminations in which the `ExitCode` column value is a number other than `0`.

- Process terminations that happen at a common interval (such as every ten minutes or every eleven minutes).

If there is a pattern of many process terminations that happen at a common interval and have a non-zero exit code, this should be captured in the RCA with the interval and `ExitCode` values.

As indicated by the [Service Fabric code package error codes](https://learn.microsoft.com/en-us/azure/service-fabric/service-fabric-diagnostics-code-package-errors) documentation, `ExitCode` values of `7147` and `7148` indicate that the process was terminated by Service Fabric. This is abnormal and should be noted. Here are the precise meanings:

| `ExitCode` | Description |
| --------- | ----------- |
| `7147` | Indicates that Service Fabric gracefully shut down the process or container by sending it a Ctrl+C signal. |
| `7148` | Indicates that Service Fabric terminated the process or container. Sometimes, this error code indicates that the process or container didn't respond in a timely manner after sending a Ctrl+C signal, and it had to be terminated. |

If the "XdbLaunchSqlSetup.exe" process is terminating with a non-zero exit code, then use the `HA6015` query to check for patterns in the log entries from the `MonXdbLaunchSetup` Kusto table:

- The `FirstMessage` column values should typically be "=================== XdbLaunchSqlSetupEntryPointLog =================" and the `LastMessage` column values should typically be "Exiting XdbSqlLaunchSetup without exceptions". If the values are different, that is interesting and should be noted.

- The `EntriesTimespanInSeconds` column values should typically be less than fifteen seconds long. If there are durations fifteen seconds or longer, that is interesting and should be noted.

If the "sqlservr.exe" process is terminating with a non-zero exit code, then use the `HA6020` query to check for patterns in the log entries from the `MonNodeTraceETW` Kusto table:

- The `FirstMessage` column values should typically be "[InitFabric] Started InitFabric setup!" and the `LastMessage` column values should typically be "** FabricStatefulServiceFactory::Startup **". If the values are different, that is interesting and should be noted.

If the "sqlservr.exe" process is repeatedly terminating with a non-zero exit code, and the `LastMessage` column value is consistent, then look that log entry up in SQL Server's source code to try to identify which function or method emits that particular log entry.

For example, if there were many terminations of the "sqlservr.exe" process, each with an `ExitCode` value of `7147`, and each occurring approximately ten minutes apart, that would indicate that the SQL Server process is getting hung during initialization and that Service Fabric is terminating the process after a ten-minute timeout is reached. If the `LastMessage` column values consistently showed "InitFabric - IsTridentSqlBackendOnGPUHardwarePlatform  = 0.", this would show us where SQL Server is getting hung. Looking that log entry up in SQL Server's source code would show that it comes from the `InitFabric` function. You would then analyze the subsequent lines in the `/Sql/Ntdbms/ksource/dbfabric.cpp` source file and look for anything that could cause an infinite wait.

**Checking for Process Terminations** should be done for every analysis. However, there should not be an output in the final RCA text unless something interesting is found.
