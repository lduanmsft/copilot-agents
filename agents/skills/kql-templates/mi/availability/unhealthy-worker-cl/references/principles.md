# Debug Principles for Unhealthy Worker.CL Applications

## Triage Principles

### 1. Always Verify State is Ongoing

**Principle**: Health state can be transient.

**How to apply**:
- Query the health state timeline (QL100) covering the incident window
- Look for **sustained** unhealthy state (lasting > 5 minutes)
- Distinguish between:
  - One-time spike (transient failover) → likely self-resolved
  - Sustained unhealthy → requires investigation
  - Intermittent oscillation (Unhealthy ↔ Warning ↔ Healthy) → underlying issue with recurrence

**What to look for**:
- Chart showing continuous red (value 0) in time window
- Absence of green (value 2) for extended period
- Comparison: is current timestamp showing healthy state?

### 2. Exclude Administrative Operations First

**Principle**: Expected operations cause temporary unhealthiness. Don't treat expected states as incidents.

**Update SLO (Scale)**:
- Target Application can be unhealthy during scale operations and that is normal
- Check `update_slo_requests` table or `MonManagedServers` for matching instance.
- If `state == "UpdatingPricingTier"` anf 'target_sql_instance_name' matches app name : No investigation needed; wait for completion

**Database Operations**:
- CREATE: New database creation 
- DROP: Database deletion
- COPY: Geo-replication setup
- RESTORE: Point-in-time restore

**Check these before diving deeper:**
- Is there an SLO update in progress?
- Are any databases stuck in create/copy/restore?
- Are there related incidents on other queues?

### 3. Error Message Taxonomy

**Principle**: Root cause is usually indicated by specific errors. Route based on error, not generic "unhealthy."

**Priority order (what to check first)**:

| Priority | Error Type | Impact | Route | 
|----------|-----------|--------|-------|
| 🚩 Critical | "Azure Key Vault" / "Cannot find server asymmetric key" | Cannot decrypt; SQL blocked | **TDE** |
| 🚩 Critical | CodePackage launch failures | Cannot start; replica stuck | **Mi Perf** or **Telemetry** |
| 2 | Storage quota exceeded | Operations blocked | **Mi Perf** |
| 2 | Remote storage errors (12002, 12030, 87) | Replica cannot build | **Mi Perf** |
| 2 | Remote storage network errors (12007, 12017, 12175) | Customer network issue | **Connectivity** |
| 3 | SQL process container startup failed | Container/networking issue | **Connectivity** |
| 3 | Node unresponsive (no telemetry) | Node-level infrastructure issue | **Platform & T-Train** |
| 3 | Database InCreate/Copy/Restore | Long-running operation | **GeoDR** / **DB CRUD** / **B/R** |
| 3 | GeoDR connectivity | Replication delayed | **GeoDR** |
| 4 | MI Disabled state | Administrative; no SQL issue | **MI CRUD/Provisioning** |
| 4 | DB services unhealthy | SQL/replication issue | **Availability** or **Platform** |
| 4 | Database under recovery (QL1000) | DB recovery causing unhealthy state | **Availability** |

**Decision rule**: 
- If multiple error types → address in priority order
- If no clear errors → check platform status, check if other instances affected

### 4. Information Tracing Pattern

**Principle**: Investigation follows a phased approach with parallel execution for speed.

**Phase 1 — Validate (sequential, early exit)**:
1. Is the state actually unhealthy RIGHT NOW? → QL100
2. Should the state be unhealthy (Update SLO/admin op)? → QL200
3. If excluded → Stop, no further action

**Phase 2 — Diagnose (all in parallel)**:
After validation passes, run ALL diagnostic queries simultaneously:

- **Batch A** (main cluster, 8 parallel queries): QL300, QL400, QL600, QL700, QL901, QL902, QL904, QL905
- **Batch B** (main cluster, requires LogicalServerName): QL500, QL501, QL903
- **Batch C** (NorthEurope cluster, requires LogicalServerName): QL800

All batches run in parallel with each other. Expected time: ~2-3 minutes total (vs 15-25 min sequential).

**Phase 2a — Database Recovery Check (conditional)**:
- Only if Phase 2 QL905 shows DB services unhealthy (state 0) → Run QL1000 database recovery check
- Correlate recovery timeline with the QL905 unhealthy window to determine root cause

**Phase 3 — Related Incidents (conditional)**:
- Only if Phase 2/2a finds no root cause → Run QL906 tiered incident search

### 5. Replica State Interpretation

**Principle**: Replica states in SFE reveal what service fabric is trying to do.

**State patterns and meanings**:

| Pattern | Meaning | Investigation |
|---------|---------|-----------------|
| All replicas Ready | Normal | Issue likely transient or resolved |
| 1+ replica InBuild | Rebuilding after failover | Check why build is taking long |
| All secondaries InBuild | Cannot build any replica | Critical infrastructure issue |
| Marker service replica InBuild | Container issues likely | Check container issues query QL901 and QL902
| Primary not Ready | Primary crashed/stuck | Check for CodePackage errors |
| Partition quorum loss | Lost majority of replicas | Escalate immediately |
| Rapid failovers (SFE history) | Unstable; keeps crashing | Check logs for crash reasons |

## Error-Specific Principles

### TDE Certificate Errors

**Error pattern**: 
- "Azure Key Vault" in error message
- "Cannot find server asymmetric key with thumbprint"
- EXCLUDING: "Triggering deny external connections db due to Azure Key Vault Client Error"

**Principle**: TDE errors block ALL SQL operations. These are highest priority.

**Investigation**:
1. Run QL300 to confirm TDE error
2. Do NOT run further diagnostic steps
3. Transfer immediately to **TDE team**
4. Provide: AppName, error message, timestamp, customer subscription

### CodePackage Launch Failures

**Error pattern**:
- "ProcessUnexpectedTermination" with XdbPackageLauncherSetup
- "failed to start" with XdbPackageLauncher.exe
- "failed to start" with MDS

**Principle**: These are platform-level failures. Route based on component.

**Investigation**:
1. Run QL400 
2. Parse `transfer_queue` field:
   - "Perf" → SQL Engine/Launcher issue
   - "Telemetry" → Monitoring/MDS issue
3. Provide: component, error details, failure count, time window

**Guidance**:
- If multiple processes failing → likely node-level issue (hardware/OS problem)
- If specific package always failing → corrupted package deployment

### Storage Errors

**Error pattern**:
- `storage_space_used_mb >= reserved_storage_mb`
- `AccountQuotaExceeded` errors
- "No space left on device" type messages

**Principle**: Storage quota is a hard limit. Cannot bypass; must increase resources.

**Investigation**:
1. Run QL500 to confirm instance storage utilization
2. Run QL501 to confirm XStore account quota
3. Identify: which is hitting limit? Instance or account?

**Guidance**:
- Instance hitting limit → Customer needs higher SLO tier or delete data
- Account hitting limit → Platform team may need to address (rare)
- Provide: Current usage, reserved, time until full

### Remote Storage Connectivity Errors

**Error patterns**:
- Error 12007, 12017, 12175: Network connectivity (customer-side)
- Error 12002, 12030: Service connectivity (platform-side)
- Error 87: Metadata too large
- `is_zero_request = 1`: Request never reached storage (network infrastructure)

**Principle**: Different errors = different root cause and different routing.

**Investigation**:
1. Run QL600
2. Classify by error code and `is_zero_request`:
   - Network errors + zero_request = 1 → Transient network issue
   - Network errors + retry_count > 10 → Persistent customer network issue
   - SQL errors (12002, 12030) → Platform storage issue
   - Error 87 → Metadata corruption

**Guidance**:
- Network errors → Connectivity team (customer firewall/NSG/routing)
- SQL errors → Performance team (platform storage availability)
- Metadata error → Performance team (corruption or size issue)

### Database Operation Stuck (InCreate/InRestore)

**Scenario**: Database stuck in CREATE, COPY, or RESTORE state > 60 minutes

**Principle**: Long operations may be expected, but > 60 min indicates blocking issue.

**Investigation**:
1. Run QL700 (InCreate) to identify the operation type
2. Identify operation type and current state
3. Check `fabric_property_updating` events and exception messages

**Guidance**:
- InCreate/Copy > 60 min: Check remote storage (QL600) or GeoDR connectivity (QL800)
- InRestore > 60 min: Transfer to Backup & Restore team

**Escalation**:
- If state unchanged for 30+ min → Escalate to relevant team
- If state rapidly changing → May self-resolve; monitor more
- Do NOT wait indefinitely; escalate at 60+ min mark

## Escalation Decision Tree

```
DECISION TREE FOR UNHEALTHY WORKER.CL

START: Application Health = 0 (Unhealthy)
│
├─ Duration < 5 minutes?
│  ├─ YES → Monitor for 5 more minutes; if resolves, close as transient
│  └─ NO → Continue
│
├─ Current state is now Healthy?
│  ├─ YES → Close as transient; note in ticket
│  └─ NO → Continue
│
├─ Update SLO in progress? (QL200)
│  ├─ YES → Info: SLO in progress; monitor; no action needed
│  └─ NO → Continue
│
├─ TDE/AKV error? (QL300)
│  ├─ YES → 🚩 ESCALATE to **TDE**
│  └─ NO → Continue
│
├─ CodePackage launch failure? (QL400)
│  ├─ YES (Launcher/Xdb) → ESCALATE to **Mi Perf**
│  ├─ YES (MDS) → ESCALATE to **Telemetry**
│  └─ NO → Continue
│
├─ Storage limit hit? (QL500-501)
│  ├─ YES → 🚩 ESCALATE to **Mi Perf**
│  └─ NO → Continue
│
├─ Remote storage error? (QL600)
│  ├─ YES (Network errors, zero_request=1) → ESCALATE to **Connectivity**
│  ├─ YES (Network errors, persistent) → ESCALATE to **Connectivity**
│  ├─ YES (SQL errors 12002, 12030, 87) → ESCALATE to **Mi Perf**
│  └─ NO → Continue
│
├─ Database InCreate/Copy/Restore? (QL700)
│  ├─ YES (Copy) → ESCALATE to **GeoDR**
│  ├─ YES (Restore) → ESCALATE to **Backup & Restore**
│  ├─ YES (Create) → ESCALATE to **DB CRUD**
│  └─ NO → Continue
│
└─ GeoDR connectivity issue? (QL800)
   ├─ YES → INFO: Known issue; can proceed with upgrade
   ├─ NO → Continue
   │
   ├─ SQL Process NOT Running in Container? (QL901-902)
   │  ├─ YES → ESCALATE to **Connectivity**
   │  └─ NO → Continue
   │
   ├─ Managed Instance Disabled? (QL903)
   │  ├─ YES → ESCALATE to **MI CRUD/Provisioning**
   │  └─ NO → Continue
   │
   ├─ Node Unresponsive? (QL904)
   │  ├─ YES → ESCALATE to **SQL MI Platform & T-Train**
   │  └─ NO → Continue
   │
   ├─ Database Services Unhealthy? (QL905)
   │  ├─ YES (state 0) → Run QL1000 (Database Recovery Check)
   │  │  ├─ Recovery progressing (% increasing)? → No-op; let recovery finish → ESCALATE to **Availability** (no action needed)
   │  │  ├─ Recovery stuck (% not advancing)? → ESCALATE to **Availability** (additional investigation required)
   │  │  ├─ Recovery resets X%→0% multiple times? → SQL process likely killed → ESCALATE to **Availability** + warn: DO NOT kill SQL process
   │  │  └─ No recovery / no overlap → ESCALATE to **Availability** (unknown DB service cause)
   │  ├─ NO (state 2, but app unhealthy) → Check event source; default ESCALATE to **Platform & T-Train**
   │  └─ NO → Continue
   │
   └─ UNKNOWN ROOT CAUSE
      ├─ Check related incidents on other queues
      ├─ Query SFE for replica state patterns
      ├─ 🚩 ESCALATE to **On-Call DRI** with:
      │  - Health state timeline (QL100)
      │  - All diagnostic query results
      │  - SFE replica states
      │  - Time window: when unhealthy started/peaked/ongoing
      └─ Page DRI if > 1 hour unhealthy
```

## Validation Checklist Before Escalation

Before escalating to another queue, verify:

- ✅ **State is ongoing**: QL100 shows sustained unhealthy state
- ✅ **Not an admin operation**: QL200 confirms no SLO/operation in progress  
- ✅ **Root cause identified**: At least one diagnostic query (QL300-QL905, QL1000) shows error
- ✅ **Error message**: Include specific error code or message text
- ✅ **Time window**: Provide OutageStartTime, OutageEndTime
- ✅ **AppName and ClusterName**: Verified from alerts/tickets
- ✅ **Resource context**: LogicalServerName, subscription, region
- ✅ **Replica state**: Checked SFE for replica health snapshot
- ✅ **Related incidents**: Verified no other incidents on SLA-affecting queues

🚩 **Do NOT escalate if**:
- State is currently Healthy (QL100 shows recovery)
- Duration < 5 minutes (likely transient)
- No supporting diagnostic data (run queries first)
