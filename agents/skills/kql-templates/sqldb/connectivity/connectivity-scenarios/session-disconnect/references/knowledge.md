# Terms and Concepts

## Core Concepts

### MonLogin Table
Login data is stored in the `MonLogin` table. The `process_login_finish` event indicates the completion of a login process and is the primary event used for login analysis.

### Login Correlation
Correlating login events across components (gateway, xdbhost, sqlserver) is essential for tracing connection flow and diagnosing session disconnect root causes.

### Gateway to Backend Correlation
Uses two columns for correlation:

| Column | Description |
|--------|-------------|
| `Peer_activity_id` | One per thread on client side |
| `Peer_activity_seq` | Incremented by 1 for every new connection created on that thread |

Login to backend and login to frontend will have the same `peer_activity_id`, with `peer_activity_seq` differing by 1 (backend = gateway login + 1).

**Note:** Some drivers have a bug where `peer_activity_seq` loops around after 255. This should be accounted for in queries.

### XdbHost to SqlServer Correlation
Uses `Connection_peer_id` for correlation. This column is unique per connection and set by the client. The `process_login_finish` event on xdbhost and sqlserver will have the same `connection_peer_id`.

### Gateway to Backend (End-to-End) Correlation
Gateway sets `connection_peer_id` to the value provided by the client (if provided in the driver) before creating a connection to backend. This allows correlation between gateway and backend using `connection_peer_id`.

## Login Timing Columns

Timing columns on the `process_login_finish` event break down where time is spent during login processing.

| Column | Scope | Description |
|--------|-------|-------------|
| `Total_time_ms` | All | Total time of `process_login_finish` (sqlalias lookup + winfab lookup for gateway; dosguard, authentication, firewall, xodbc etc. for sqlserver) |
| `Enqueue_time_ms` | All | Time taken for `sos_scheduler` to enqueue the login processing thread |
| `Netwrite_time_ms` | All | Sum of time taken while writing packets to SNI |
| `Netread_time_ms` | All | Sum of time taken while reading packets from SNI |
| `Ssl_time_ms` | All | Total time spent during SSL encrypt/decrypt |
| `Fedauth-*_time_ms` | All | Multiple columns for corresponding steps in fedauth |
| `Proxy_dispatcher_time_ms` | Gateway only | Time spent by proxy open task in the dispatcher actively running |
| `Proxy_dispatcher_wait_list_time_ms` | Gateway only | Time spent by login waiting to be picked up by dispatcher. Long time here indicates another login (to another database) hogging dispatcher pool time (max 200 active proxy open tasks) |
| `Proxy_open_time_ms` | Gateway only | Time spent by proxy open connection in the process of opening a connection |

## Key Telemetry Tables

| Table | Purpose |
|-------|---------|
| **MonLogin** | Login success/failure analysis — `process_login_finish` events, error codes, timing columns, correlation IDs |
