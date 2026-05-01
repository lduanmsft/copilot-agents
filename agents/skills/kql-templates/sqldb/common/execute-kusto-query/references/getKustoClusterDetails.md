### Step 1: Identify which region stores the telemetry for a given Logical server.

**Choose the appropriate method based on available information:**

#### Option A — ClusterName / tenant_ring_name is available (Managed Instance - Worker.CL.WCOW* incidents)

If a **ClusterName** (also known as `tenant_ring_name` or `PrimaryTenantRing`) is already known — for example from ICM custom fields or from the `get-db-info` skill — extract the region directly from it. **Skip DNS resolution entirely.**

**How to extract the region from ClusterName:**
- Production format: `tr{N}.{region}-{suffix}.worker.database.windows.net`
  - Example: `tr61241.eastus1-a.worker.database.windows.net`
- Stage format: `tr{N}.{region}-{suffix}.worker.sqltest-eg1.mscds.com`
  - Example: `tr144.lkgtst3-a.worker.sqltest-eg1.mscds.com`

Sometimes incident does not contain full ClusterName, but just the region:
  - Example: `eastus1-a`

**Extraction steps** (same for all formats):
  1. Extract the second dot-delimited segment (for full ClusterNames) or use the region value directly: e.g. `eastus1-a`, `lkgtst1-a`
  2. Remove the trailing `-{letter}` suffix: `eastus1`, `lkgtst1`
  3. This is the `telemetry-region` keyword.

#### Option B — No ClusterName available (standard SQL Database path)

1. Identify telemetry-region using [dnsLookup.md](dnsLookup.md)
2. If there is no DNS name returns in the above step, fallback to use [RegionFromHistory.md](RegionFromHistory.md)

**CRITICAL**: STOP and EXIT if you cannot get a region keyword. Notify user the Logical server name in FQDN may not exist on Public cloud in the time range.

### Step 2: Identify Kusto cluster-uri and kusto-database for the region for a given logical server
Now for the telemetry-region discovered in Step 1 identify kusto-cluster-uri and Kusto-database using  [findClusterFromRegion.md](findClusterFromRegion.md)