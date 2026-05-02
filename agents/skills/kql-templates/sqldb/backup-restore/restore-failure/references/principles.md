!!!AI Generated. Manually verified!!!

# Debug Principles for Restore Failure Analysis

## Restore Failure Decision Tree

### 1. Is the server accessible?

| Server State | Action |
|-------------|--------|
| Normal / Online | Continue to restore request analysis |
| Disabled | 🚩 Contact provisioning team to re-enable |
| Dropped | 🚩 Use **restore-dropped-server** skill |
| Not found | 🚩 Verify server name, check if dropped |

### 2. Was a restore request created?

| Restore Request State | Action |
|----------------------|--------|
| No request found | Check management validation (RFQ300) for failures |
| Ready (>30 min) | 🚩 Stuck — check backup availability & state machine |
| Restoring (events stopped) | Check WinFabLogs for SQL crashes (RFQ400) |
| Failed | Check `operation_details` in RFQ100 for error message |
| Completed | Restore succeeded, verify DB is online |

### 3. Failure routing by error pattern

Route based on `operation_details` from RFQ100 or `message` from RFQ300:

| Error Pattern | Root Cause | Mitigation |
|--------------|------------|------------|
| Server not found | Server dropped/doesn't exist | Use restore-dropped-server if needed |
| Database already exists | Target name conflict | Drop/rename target, retry |
| Invalid point in time | Outside retention window | Verify time, retry |
| Exit code 1460 | Named pipe timeout (subcore) | Use `Fix-StuckRestore.ps1` |
| Exit code 304 | SQL fast exit | Check sqlsatelliterunner |
| SSL/TLS error (258) | Silent failure | See BRDB0005.6 |
| Error 21105 | Cloud Lifter regression | Use `Set-ServerConfigurationParameters` |

## Pre-Investigation Safety Check

- **Always verify server has not been disabled or dropped** before investigating restore failures
- This is the most common overlooked root cause
