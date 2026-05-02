---
name: error-40613-state-13
description: This error indicates a failure to enqueue logins within XDBHost. XDBHost maintains a queue per sql instance. This queue holds the login requests that are destined to the particular SQL instance. In order to operate on the queue, threads running in XDBHost attempt to acquire a lock before enqueue/dequeue operations. The lock has a timeout of 5 seconds. A failure to acquire the lock results in the login being failed. This particular condition is logged by xdbhost as 40613/13.
---

## Relative Error Codes
- Error 40613 State 15: XDBHostQueueTimeoutSystemError
- Error 26078 State 15: In XDBHost, when a login request is dequeued we try to ensure that the login has not been in the queue for more than 10 seconds. If the login has remained in the queue for 10 seconds, xdbhost forcibly closes the named pipe connection with SQL and clears the socket duplication queue. 

## Potential causes
1. Slow socket duplication: During the login process, XDBHost duplicates the client socket to establish a connection to the backend SQL instance. If the socket duplication is slow, it can lead to increased time holding locks on the login queue, causing other login requests to timeout.
2. High login volume: If there is a sudden surge in login requests to a SQL instance, it can lead to increased contention for the login queue lock in XDBHost.
3. HighCPU Consumption for XDBHost and LSASS.
4. CPU Consumption for SQL instances: If the backend SQL instance is under heavy load and experiencing high CPU usage, it can lead to slower processing of login requests. 

## Troubleshooting Steps
Follow the skill and output after each step:
.github/skills/Connectivity/connectivity-utilities/xdbhost-metric-check/SKILL.md

## Suggested TSG
https://eng.ms/docs/cloud-ai-platform/azure-data/azure-data-azure-databases/sql-/sql-connectivity/sql-db-connectivity/xdbhost/error-40613-state-13
