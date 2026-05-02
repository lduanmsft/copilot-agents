!!!AI Generated. Manually verified!!!

# Report Format for Log Full/Near Full Analysis

## Summary Output Format

After completing analysis, provide summary:

> ## 🔍 **Log Full/Near Full Analysis Summary**
>
> **Database Information:**
> - Physical Database ID: {PhysicalDatabaseID}
> - Logical Server: {LogicalServerName}
> - Logical Database: {LogicalDatabaseName}
> - Cluster/Node: {ClusterName}/{NodeName}
>
> **Log Space Analysis:**
> - Peak Usage: {PeakLogUsedPercentage}%
> - Max Log Size: {MaxLogSizeGB} GB
> - Peak Used: {PeakLogUsedGB} GB
> - Analysis Window: {StartTime} to {EndTime}
>
> **Root Cause:**
> - Primary Holdup Reason: {PrimaryLogHoldupReason}
> - {Additional diagnostic findings}
>
> **Recommended Actions:**
> {Numbered list of specific mitigation steps}
>
> **Related TSGs:**
> {List of relevant TSG links}

## Step Output Templates

### Log Space Analysis Complete

> ✅ **Log Space Analysis Complete**
> - **Peak Log Usage**: {PeakLogUsedPercentage}%
> - **Max Log Size**: {MaxLogSizeGB} GB
> - **Peak Used**: {PeakLogUsedGB} GB
> - **Primary Holdup Reason**: {PrimaryLogHoldupReason}

### DirectoryQuotaNearFull Detected

> 🚩 **DirectoryQuotaNearFull Issue Detected**
> - **Directory**: {target_directory}
> - **Size**: {size_gb} GB
> - **Detection Time**: {stale_folder_time}
>
> **Recommended Action**: Transfer incident to **Azure SQL DB/SQL DB Perf : InterProcessRG/ResourceLimits** queue or refer to TSG PERFTS016 for directory quota resolution.
