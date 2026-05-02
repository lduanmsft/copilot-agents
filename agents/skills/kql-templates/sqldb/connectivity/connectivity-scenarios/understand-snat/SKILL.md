---
name: understand-snat
description: This skill helps AI to understand the SNAT concept and how it works in Azure SQL connectivity, especially in the scenario of connectivity rings and proxy mode. And the relationship between SNAT and common connectivity error like 40613 State 22.
---

## A. Understand the Load Balancer outbound port allocation mechanism
When load balancing rules are selected to use default port allocation, or outbound rules are configured with "Use the default number of outbound ports", SNAT ports are allocated by default based on the backend pool size. Backends will receive the number of ports defined by the table, per frontend IP, up to a maximum of 1024 ports. (https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-outbound-connections#preallocatedports)

Pool size (VM instances)	Default SNAT ports
1-50	1,024
51-100	512
101-200	256
201-400	128
401-800	64
801-1,000	32

In each Control Ring, we have less than 100 VMs, so we would fit the first line and each Gateway Node (VMSS instance) obtain 512 ports to connect to Internet destination, if the LB use the default LB port allocation method.

## B. Understand the general traffic between CR and TR in proxy mode
1. The CR GW instances are listening on port 1433
![alt text](image.png)
2. When CR forwards to TR ring in proxy mode, on the CR instance you would see CR instance private IP sends traffic to the Public IP of the TR LB (Run Netstat -ano on GW instance). In the screenshot 10.0.0.46 is a GW instance private IP and 168.61.137.x is the TR rings:
![alt text](image-1.png)

3. When the packet reaches VFP/VM-Switch, the source of the packet is translated to 40.78.200.133 which is the CR LB Public IP, so that the packet is routble.

4. With the above information, we can understand when CR talks to TR in proxy mode without any private links and service tunnel, the traffic flow will be translated to Public IP and SNAT port will be consumed.

## C. Understand the impact of SNAT
As we discussed each backend VM machine (CR node and TR node) gets assigned 512 SNAT ports, however these ports can be reused at the same time if the destination IPs or ports are different. Since customer's databases are located on different TR nodes, it has a very low chance that one customer has a SNAT port exhaustion on the CR would impact the customer using the same CR ring.

If a CR node has 512 connections to (TR Ring A - DB Node 1), with the destination IP 1.1.1.1:11065; 
this CR node is capable to have another 512 connections to (TR Ring A - DB Node 2) with destination IP 1.1.1.1:11066;
this CR node is also capable to have another 512 connections to (TR Ring B - DB Node x), with destination IP 2.2.2.2:11065.

Login Error 40613 State 22 usually associate with SNAT port exhaustion, because when CR Node could not route out traffic to specific destination (IP:port) on its SLB/VFP layer, the connections are timed-out and could not reach the destination.

Note:
1. Root cause of Error 40613 State 22 is not always SNAT port exhaustion, it could also be:
    a. Networking unstable including LoadBalancer, physical networking, NIC
    b. DB node is unhealthy or unavaliable or too busy to process the TCP traffic
    c. Too many logins in a short time that XDBhost or sqlserver could not handle
    d. other causes
Refer **.github/skills/Connectivity/connectivity-errors/error-40613-state-22/SKILL.md** for more information.

2. SNAT port exhaustion is not consider as the root cause of a problem, usually huge number of traffic flows to some SQL instances in a short time using proxy mode. Sometime huge traffic flow involves failed authentication, so customer keeps retry.
Refer **.github/skills/Connectivity/connectivity-errors/error-40613-state-22/SKILL.md** for more information.
