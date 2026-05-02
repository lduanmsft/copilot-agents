!!!AI Generated. Manually verified!!!

# Debug Principles for Dropped Server Restore

## Recovery Method Decision Tree

1. **Check DNS availability** (nslookup {server}.database.windows.net)
   - "Non-existent domain" → DNS available ✅
   - Returns IP address → DNS NOT available ❌

2. **Verify DeferredDropped state** (query MonAnalyticsDBSnapshot)
   - Server found with state = DeferredDropped → Recoverable ✅
   - No results or other state → Cannot directly recover ❌

3. **Verify expected databases present** (query MonAnalyticsDBSnapshot)
   - Expected databases in Tombstoned state → Method A eligible ✅
   - Missing databases → Server may have been re-created ❌

| DNS Available | DeferredDropped | Databases Present | Recovery Method |
|---------------|-----------------|-------------------|----------------|
| ✅ | ✅ | ✅ | Method A: Recover-LogicalServer |
| ❌ | Any | Any | Method B: PITR to new server |
| ✅ | ❌ | Any | Method B: PITR to new server |
| ✅ | ✅ | ❌ | Method B: PITR to new server |

## Critical Safety Checks

- 🚩 **DNS Verification**: ALWAYS verify DNS before DeferredDropped recovery. Failure causes force-drop and hours of recovery work.
- 🚩 **7-Day Limit**: Server must be recovered within 7 days. No exceptions.
- 🚩 **Business Justification**: Verify CRI filed within 7 days, production environment, and subscription admin approval.
- 🚩 **TDE/CMK**: If databases used customer-managed keys, key vault permissions must be set up before restore.
