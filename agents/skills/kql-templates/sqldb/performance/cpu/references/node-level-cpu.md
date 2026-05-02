---
name: node-level-cpu
description: This skill analyzes node-level CPU usage including pegged cores detection and CPU balance analysis to identify hardware-level CPU bottlenecks
tools: ['search', 'fetch', 'githubRepo', 'mcp_azure_mcp_kusto']
---

# Debug Node Level CPU Analysis

## Skill Overview

This skill analyzes CPU usage at the node level to detect pegged cores and unbalanced CPU conditions. It identifies scenarios where individual CPU cores are running at near-maximum capacity (>95%) while overall CPU utilization remains moderate, indicating potential resource contention or scheduling issues.

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

### Task 1: Execute the Kusto query below. If required variables (e.g., `{AppNamesNodeNamesWithOriginalEventTimeRange}`) are not available, first run the [appnameandnodeinfo skill](../../../Common/appnameandnodeinfo/SKILL.md) to obtain them.

**⚠️ MANDATORY: Execute this query EXACTLY as written. Do NOT simplify, modify, or create alternative queries. The full query includes pegged cores detection logic that is essential for complete analysis.**

```kql
// ------- Constants ------
// Defines how much usage percent a core needs to surpass to be considered 'pegged'.
let PEGGED_CORE_USAGE_PERCENT_THRESHOLD = 95;
// For the overall usage among all cores that the instance uses (not of the whole cpu), this threshold is used to determine if the
// overall percent usage is high or not. This is then used to determine whether the cpu usage is balanced or unbalanced at any given moment.
let HIGH_OVERALL_USAGE_PERCENT_THRESHOLD = 80;
// The CPU usage can be unbalanced for brief moments or for longer periods. This constant is used to determine at what ratio of unbalancedTime/totalTime
// we consider it unbalanced enough. For example, if the cpu is unbalanced for just 1% of the time, it is not unbalanced enough.
let PERCENT_OF_UNBALANCED_CPU_OVER_PERIOD_THRESHOLD = 60;
//
// ------- Part 1: Find out if instance is not multicore for early skipping the pegged core analysis ------
// Find out if this database has ever been multicore during this time interval. This is used for early skipping the entire pegged core analysis.
// Sub-core/single-core instances often have more than 1 core in their cpu mask so we need to explicitly filter them.
let isMulticore = isnotempty(toscalar(MonDmRealTimeResourceStats
    | where {AppNamesNodeNamesWithOriginalEventTimeRange}
    | where LogicalServerName =~ '{LogicalServerName}' and database_name =~ '{LogicalDatabaseName}'
    | where cpu_cap_in_sec > 1
    | take 1));
//
// ------- Part 2: Find the affinity masks over time and parse them ------
// Finds all the affinity masks this instance had over the time period. They are formatted as a json. The output would be for example:
//   2021-09-22T03:43:12  2021-09-22T05:45:03  { 'Group0' : '0x3fc00000' }
//   2021-09-22T05:46:53  2021-09-23T05:44:55  { 'Group1' : '0xff00000000' }
//   and so on...
//
// Affinity mask:
//   The affinity mask determine the cores that instance use. It is divided in processor groups, a windows concepts, where each group has at most 64 cores, hence each mask is 64 bit mask.
//   Windows tries to keep cores from the same NUMA node in the same processor group.
//
// How we find the affinity mask for each interval:
//   This uses a common pattern that is similar to how ASC finds the node per time interval that database is located.
//   It serializes the table, iterates over it in order, one-by-one, keeping track of the timestamps where the cpuMasksJson changed with the isFirst and isLast fields.
let cpuMasksJsonPerInterval = MonRgLoad
    | where isMulticore // Early skip the pegged cores analysis for non-multicore instances
    | extend originalEventTimestamp = originalEventTimestampFrom
    | extend AppName = tostring(split(application_name, '/')[-1])
    | where {AppNamesNodeNamesWithOriginalEventTimeRange}
    | where event == 'instance_load'
    | extend cpuMasksJson = allocated_cpus
    | summarize cpuMasksJson=any(cpuMasksJson) by originalEventTimestamp
    | order by originalEventTimestamp asc nulls first
    | serialize
    | extend prevCpuMask = prev(cpuMasksJson)
    | extend nextCpuMask = next(cpuMasksJson)
    | extend isFirst = (cpuMasksJson != prevCpuMask)
    | extend isLast = (cpuMasksJson != nextCpuMask)
    | where isFirst== true or isLast == true
    | extend intervalEndTime = next(originalEventTimestamp, 1, datetime({EndTime}))
    | extend intervalStartTime = originalEventTimestamp
    | where isFirst == true
    | extend currentCpuMask = cpuMasksJson
    | project intervalStartTime, intervalEndTime, cpuMasksJson;
// Parse the cpuMasksJson groups so that we have the individual masks ready for further parsing.
// For example, given the following json:
//      2021-09-22T12:00 2021-09-22T12:30 '{Group0: 0x3ff00001, Group1: 0x300000}'
// We'll output a row for each mask with the group, so that it can be further parsed:
//      2021-09-22T12:00 2021-09-22T12:30  0  '0x3ff00001'
//      2021-09-22T12:00 2021-09-22T12:30  1  '0x300000'
// Currently only 2 processor groups are used ('Group0' and 'Group1') but this handles any number of groups, which may increase in the future
// as more cores are supported.
let groupCpuMaskPerInterval = cpuMasksJsonPerInterval
    | extend cpuMasksJson = parse_json(cpuMasksJson)
    | mv-expand cpuMasksJson
    | extend groupKey = tostring(bag_keys(cpuMasksJson)[0]) // { 'Group1': '0xff00' } -> [ 'Group1' ] -> 'Group1'
    | extend groupId = extract('Group([0-9]+)', 1, groupKey, typeof(int)) // 'Group1' -> 1
    | extend groupCpuMask = cpuMasksJson[groupKey]
    | project intervalStartTime, intervalEndTime, groupId, groupCpuMask;
// Parse each mask and generate the perfmon counter names for each of the cores
// For example, given the following mask:
//   group    groupCpuMask
//     1       '0x300000'
// We'll have a row for each of the perfmon counter names:
//   \Processor Information(1,20)\% Processor Time
//   \Processor Information(1,21)\% Processor Time
// To detect each core it creates a single bit mask for each of the possible 64 cores in a group and, for each of those, does a binary_and
// with the group cpu mask.
let singleBitMasks = materialize(
    // Kusto long is 64bits and 1<<63 gracefully overflows. This is officially supported as it is used on the
    // binary_shift_left() official documentation.
    range n from 0 to 63 step 1
    | project n, singleBitMask = binary_shift_left(1, n), dummy = 0);
let coresCounterNamesPerInterval = groupCpuMaskPerInterval
    | extend dummy = 0
    | lookup kind=inner (singleBitMasks) on dummy
    | extend cpuMask = tolong(groupCpuMask)
    | where binary_and(cpuMask, singleBitMask) != 0
    | extend CounterName = strcat(@'\Processor Information(', groupId, ',', n, @')\% Processor Time')
    | project intervalStartTime, intervalEndTime, CounterName;
//
// ------- Part 3: Given the counter names with their time periods, find the pegged cores ------
//
// All perfmon counters for the cores that this instance used, only when it used.
// For example, if during the time period there were 2 affinity masks, during the first interval we'll only have counters for the cores from the first mask
// and during the second interval we'll only have core from the second mask (and not the first mask).
let instanceCoresUsage = materialize(coresCounterNamesPerInterval
    | join kind=inner (
        MonCounterOneMinute
        | where {NodeNamesWithPreciseTimeRange}
        | where CounterName startswith @'\Processor Information' and CounterName endswith 'Processor Time'
        ) on CounterName
    | where PreciseTimeStamp between (intervalStartTime..intervalEndTime)
    | project PreciseTimeStamp, CounterName, CounterValue
    | summarize CounterValue=max(CounterValue) by CounterName, bin(PreciseTimeStamp, 1min) // Ensure timestamps are using the exact minutes
    | sort by CounterName, PreciseTimeStamp asc); // sorting by CounterName first so it can be used by minUsageInLast5MinutesPerCore
// This implements a rolling window that looks at the minimum usage over the last 5 minute window. The goal is to avoid triggering
// the insight for a core that just quickly spiked in usage, so it needs at least 5 continuous minutes of high usage to be considered pegged.
//
// This handles spikes on the first minutes and missing telemetry, while using rolling_percentile() with percentile=0 would not.
// The input rows are first sorted by CounterName so that we reset the rolling window when the counter name changes.
//
// To exemplify the first minutes issue, suppose we have this sequence of values:
//      [100, 0, 0, 0, 0]
// 1. with rolling_percentile() the minUsageInLast5Minutes would be [100, 0, 0, 0, 0] and thus the core would be considered pegged.
// 2. with this implementation it is [0, 0, 0, 0, 0] and the core is not considered pegged because of a single minute.
// For missing telemetry, the first value after the missing telemetry has the same issue with rolling_percentile(). This implementation
// covers that and can only trigger a
//
// To exemplify the missing telemetry issue, suppose we have this sequence of values where the last one, the 6th, is after missing telemetry:
//      [0, 0, 0, 0, 0, 100]
// 1. for rolling_percentile() we would have [0, 0, 0, 0, 0, 100], the same issue that can happen at the beginning.
// 2. with this implementation we have [0, 0, 0, 0, 0, 0]. The first value after missing telemetry would never make us consider it a pegged core,
//    unless it had already been considered on the last minutes before the missing telemetry, in which case there is no problem.
let minUsageInLast5MinutesPerCore = instanceCoresUsage
| serialize
| extend minUsageInLast5Minutes = min_of(CounterValue,
    // The default value of 0.0 on the iff() is used to avoid using the CounterValues from a different core
    // The default value of 0.0 on the prev() ensures that the first 4 minutes will have minUsageInLast5Minutes = 0
    iff(prev(CounterName, 1) == CounterName, prev(CounterValue, 1, 0.0), 0.0),
    iff(prev(CounterName, 2) == CounterName, prev(CounterValue, 2, 0.0), 0.0),
    iff(prev(CounterName, 3) == CounterName, prev(CounterValue, 3, 0.0), 0.0),
    iff(prev(CounterName, 4) == CounterName, prev(CounterValue, 4, 0.0), 0.0));
let peggedCoresCounterNames = minUsageInLast5MinutesPerCore
    | summarize max(minUsageInLast5Minutes) by CounterName
    | where max_minUsageInLast5Minutes > PEGGED_CORE_USAGE_PERCENT_THRESHOLD
    | project CounterName;
//
// ------- Part 4: Find out if the cpu is unbalanced enough ------
// For every minute we check whether the cpu is balanced or not. To do that, for every minute, we check whether the overall core
// usage is low (the average use among all the instance cores) and whether there is any pegged cpu core at that moment.
//
// To check if there is a pegged core at every given minute we do not use the rolling 5 minute window: that would reduce the number of minutes
// with pegged cores. The rolling 5 minute window was only used to avoid showing the insight for cores that quickly spiked, but that is detrimental
// to this per minute analysis.
let isCpuUnbalancedPerMinute = instanceCoresUsage
    | summarize max(CounterValue), avg(CounterValue) by PreciseTimeStamp // Timestamp is already binned to 1 min intervals
    | extend isOverallCoresUsageLow = avg_CounterValue < HIGH_OVERALL_USAGE_PERCENT_THRESHOLD
    | extend anyPeggedCore = max_CounterValue > PEGGED_CORE_USAGE_PERCENT_THRESHOLD
    | extend isCpuUnbalanced = isOverallCoresUsageLow and anyPeggedCore;
let countMinutesOfUnbalancedCpu = toscalar(isCpuUnbalancedPerMinute
    | where isCpuUnbalanced
    | count);
let countMinutesTotal = toscalar(instanceCoresUsage
    | distinct PreciseTimeStamp
    | count);
let isCpuUnbalancedEnough = (100.0 * countMinutesOfUnbalancedCpu / countMinutesTotal) > PERCENT_OF_UNBALANCED_CPU_OVER_PERIOD_THRESHOLD;
//
// ------- Part 5: Plot the total node cpu usage and, if unbalanced and multicore, the pegged cores usage ------
// Shows the total cpu counters and the pegged cores, if any, only on the intervals on which they were used by this instance
MonCounterOneMinute
| where {NodeNamesWithPreciseTimeRange}
| where CounterName == @'\Processor Information(_Total)\% Privileged Time' or CounterName == @'\Processor Information(_Total)\% Processor Time'
| union (
   instanceCoresUsage
   | where isMulticore // Skip the pegged cores analysis for non-multicore instances
   | where isCpuUnbalancedEnough // If the overall cores usage is high, the cpu is balanced and we skip showing pegged cores
   | where CounterName in (peggedCoresCounterNames))
| project PreciseTimeStamp, CounterName, CounterValue=round(CounterValue, 1)
| where CounterName == @'\Processor Information(_Total)\% Processor Time' and CounterValue > 90
| order by PreciseTimeStamp asc
```

#### Output
Follow these instructions exactly. Only display output when specified:

**Step 1: Check Query Results**

If the query returns rows where `CounterValue > 90`:
- 🚩 **High Node CPU Detected** - The total node CPU exceeded 90% during the investigation period
- Display the timestamps and CPU values in a table format

If no rows are returned:
- ✅ **Node CPU is within normal range** - Total node CPU did not exceed 90% threshold

**Step 2: Pegged Cores Analysis**

The query also analyzes individual core usage to detect pegged cores (cores running >95% continuously for 5+ minutes).

| Condition | Message |
|-----------|----------|
| `isMulticore = false` | ℹ️ **Single-core instance** - Pegged cores analysis skipped (not applicable) |
| `isCpuUnbalancedEnough = true` | 🚩 **Unbalanced CPU detected** - Some cores are pegged while overall CPU usage is low. This may indicate resource contention or scheduling issues. |
| `isCpuUnbalancedEnough = false` | ✅ **CPU is balanced** - No significant core-level imbalance detected |

---

## Sample Output Format

> **IMPORTANT**: AI agents MUST follow this exact output format when presenting results. This ensures consistency and clarity for engineers reviewing the analysis.

### When High Node CPU is Detected with Unbalanced CPU (Pegged Cores)

#### Node Level CPU Analysis Results

**🚩 High node CPU detected with unbalanced CPU condition during the investigation period.**

#### Node CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max Node CPU** | 94.5% | 🚩 **High** |
| **Pegged Core Threshold** | 95% | - |
| **High Overall Usage Threshold** | 80% | - |
| **CPU Unbalanced Duration** | 75% of investigation period | 🚩 **Unbalanced** |

#### High CPU Timestamps

| Timestamp (UTC) | Counter | CPU % |
|-----------------|---------|-------|
| 2026-01-15 10:15:00 | \Processor Information(_Total)\% Processor Time | 92.3 |
| 2026-01-15 10:16:00 | \Processor Information(_Total)\% Processor Time | 94.5 |
| 2026-01-15 10:17:00 | \Processor Information(_Total)\% Processor Time | 91.8 |

#### Pegged Cores Detected

| Core Counter | Max Min-5min Usage |
|--------------|-------------------|
| \Processor Information(0,12)\% Processor Time | 98.2% |
| \Processor Information(0,13)\% Processor Time | 97.5% |

#### Analysis

The node experienced high CPU usage with **total node CPU reaching 94.5%**. Additionally, the CPU is **unbalanced** - individual cores are running at near-maximum capacity (>95%) while overall CPU utilization is moderate. The CPU was unbalanced for **75%** of the investigation period (threshold: 60%).

#### Root Cause Indicators

This pattern suggests:
- **Hardware-level CPU bottleneck** - Individual cores are pegged while overall usage is not maxed
- **Potential scheduling issues** - Workload may not be distributing evenly across cores
- **Resource contention** - Specific threads may be monopolizing certain cores

#### Recommendations

1. **Review workload distribution** - Investigate if specific queries or operations are causing core imbalance
2. **Check for parallel query issues** - Verify MAXDOP settings are appropriate
3. **Consider scaling up** - If pegged cores persist, additional CPU resources may be needed

---

### When High Node CPU is Detected but CPU is Balanced

#### Node Level CPU Analysis Results

**🚩 High node CPU detected, but CPU usage is balanced across cores.**

#### Node CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max Node CPU** | 95.2% | 🚩 **High** |
| **CPU Balance Status** | ✅ Balanced | - |

#### High CPU Timestamps

| Timestamp (UTC) | Counter | CPU % |
|-----------------|---------|-------|
| 2026-01-15 11:30:00 | \Processor Information(_Total)\% Processor Time | 93.7 |
| 2026-01-15 11:31:00 | \Processor Information(_Total)\% Processor Time | 95.2 |
| 2026-01-15 11:32:00 | \Processor Information(_Total)\% Processor Time | 92.1 |

#### Analysis

The node experienced high CPU usage with **total node CPU reaching 95.2%**. However, the CPU utilization is **balanced** across all cores - no individual cores are pegged while overall usage is low. This indicates the workload is distributed evenly.

#### Root Cause Indicators

This pattern suggests:
- **Uniformly high workload** - All cores are working together on the load
- **No scheduling anomalies** - CPU resources are being utilized efficiently
- **Standard high CPU scenario** - Investigate user workload for optimization opportunities

#### Recommendations

1. **Review user pool CPU analysis** - Check if user queries are driving high CPU
2. **Analyze top queries** - Identify resource-intensive queries that can be optimized
3. **Consider scaling** - If sustained high CPU, additional resources may be beneficial

---

### When Node CPU is Normal

#### Node Level CPU Analysis Results

**✅ Node CPU is within normal range - no high CPU detected during the investigation period.**

#### Node CPU Summary

| Metric | Value | Severity |
|--------|-------|----------|
| **Max Node CPU** | < 90% | ✅ **Normal** |
| **High CPU Threshold** | 90% | - |

#### Analysis

The total node CPU did not exceed the **90% threshold** during the investigation period. No high node CPU events were detected.

#### Conclusion

Node-level CPU is not a contributing factor to performance issues during this time window. Investigate other potential bottlenecks such as memory, I/O, or blocking.

---

### When Single-Core Instance (Pegged Cores Analysis Skipped)

#### Node Level CPU Analysis Results

**ℹ️ Single-core instance - pegged cores analysis not applicable.**

#### Node CPU Summary

| Metric | Value | Note |
|--------|-------|------|
| **Instance Type** | Single-core / Sub-core | - |
| **Pegged Cores Analysis** | ⏭️ Skipped | Not applicable for single-core instances |

#### Analysis

This database instance is a **single-core or sub-core instance** (cpu_cap_in_sec ≤ 1). The pegged cores analysis is designed for multi-core instances and has been skipped. Only total node CPU analysis is relevant for this instance type.

#### Recommendations

1. **Focus on total CPU utilization** - Monitor overall CPU percentage for this instance
2. **Consider workload optimization** - Single-core instances have limited CPU head room

