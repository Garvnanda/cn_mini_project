# NetArchitect Design Report: metro_man

## Summary

- Root prefix: `10.20.0.0/16`
- Sites: HQ (hq), Branch (branch), Colo (datacenter)
- Endpoints: 550
- Topology: HQ: collapsed_core, Branch: collapsed_core, Colo: collapsed_core
- Routing: OSPF multi-area
- Devices: 14, cables: 22, subnets: 29
- Verification: **PASS**
- Security score: **92/100**
- Resilience score: **97/100**
- Estimated capex: INR 20,658,800 (placeholder prices), monthly WAN: INR 0

## Physical media

| Link | Distance | Media | Transceiver |
|---|---|---|---|
| HQ--Branch | 22000 m | OS2 single-mode fiber | 10GBASE-ER |
| HQ--Colo | 35000 m | OS2 single-mode fiber | 10GBASE-ER |

## IP plan

| Subnet | Unit | VLAN | Network | Mask | Wildcard | Gateway | Broadcast | Usable | Util % |
|---|---|---|---|---|---|---|---|---|---|
| HQ-Users | Area 0 (HQ) | 10 | 10.20.0.0/24 | 255.255.255.0 | 0.0.0.255 | 10.20.0.1 | 10.20.0.255 | 254 | 99.61 |
| HQ-Voice | Area 0 (HQ) | 20 | 10.20.1.0/25 | 255.255.255.128 | 0.0.0.127 | 10.20.1.1 | 10.20.1.127 | 126 | 50.0 |
| HQ-CORE1--HQ-CORE2 | Area 0 (HQ) |  | 10.20.1.128/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| HQ-R1--BRANCH-R1 | Area 0 (HQ) |  | 10.20.1.130/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| HQ-R1--COLO-R1 | Area 0 (HQ) |  | 10.20.1.132/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| HQ-R1--HQ-CORE1 | Area 0 (HQ) |  | 10.20.1.134/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| HQ-R2--BRANCH-R1 | Area 0 (HQ) |  | 10.20.1.136/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| HQ-R2--COLO-R2 | Area 0 (HQ) |  | 10.20.1.138/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| HQ-R2--HQ-CORE2 | Area 0 (HQ) |  | 10.20.1.140/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| HQ-CORE1 Loopback0 | Area 0 (HQ) |  | 10.20.1.142/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| HQ-CORE2 Loopback0 | Area 0 (HQ) |  | 10.20.1.143/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| HQ-R1 Loopback0 | Area 0 (HQ) |  | 10.20.1.144/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| HQ-R2 Loopback0 | Area 0 (HQ) |  | 10.20.1.145/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| Branch-Users | Area 1 (Branch) | 110 | 10.20.2.0/25 | 255.255.255.128 | 0.0.0.127 | 10.20.2.1 | 10.20.2.127 | 126 | 97.62 |
| BRANCH-CORE1--BRANCH-CORE2 | Area 1 (Branch) |  | 10.20.2.128/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| BRANCH-R1--BRANCH-CORE1 | Area 1 (Branch) |  | 10.20.2.130/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| BRANCH-R1--BRANCH-CORE2 | Area 1 (Branch) |  | 10.20.2.132/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| BRANCH-CORE1 Loopback0 | Area 1 (Branch) |  | 10.20.2.134/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| BRANCH-CORE2 Loopback0 | Area 1 (Branch) |  | 10.20.2.135/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| BRANCH-R1 Loopback0 | Area 1 (Branch) |  | 10.20.2.136/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| Colo-Ops | Area 2 (Colo) | 210 | 10.20.3.0/25 | 255.255.255.128 | 0.0.0.127 | 10.20.3.1 | 10.20.3.127 | 126 | 65.87 |
| Colo-Trading | Area 2 (Colo) | 220 | 10.20.3.128/26 | 255.255.255.192 | 0.0.0.63 | 10.20.3.129 | 10.20.3.191 | 62 | 69.35 |
| COLO-CORE1--COLO-CORE2 | Area 2 (Colo) |  | 10.20.3.192/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| COLO-R1--COLO-CORE1 | Area 2 (Colo) |  | 10.20.3.194/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| COLO-R2--COLO-CORE2 | Area 2 (Colo) |  | 10.20.3.196/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| COLO-CORE1 Loopback0 | Area 2 (Colo) |  | 10.20.3.198/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| COLO-CORE2 Loopback0 | Area 2 (Colo) |  | 10.20.3.199/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| COLO-R1 Loopback0 | Area 2 (Colo) |  | 10.20.3.200/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| COLO-R2 Loopback0 | Area 2 (Colo) |  | 10.20.3.201/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |

## Architectural rationale

### L1
- **[L1.smf_er]** Selected OS2 single-mode fiber with 10GBASE-ER (1550 nm) for HQ--Branch because 22000.0 m exceeds the 10 km 10GBASE-LR reach. 10GBASE-ER uses the lower-loss 1550 nm window and reaches 40 km. _(ref: IEEE 802.3ae (10GBASE-ER))_
- **[L1.budget]** Optical budget for HQ--Branch (10GBASE-ER): fiber 5.5 dB (22.0 km × 0.25 dB/km) + 2 connectors × 0.75 dB + 0 splices × 0.3 dB = 7.0 dB against 11.0 dB allowed, margin 4.0 dB (pass). _(ref: IEEE 802.3ae channel insertion loss; TIA-568 component loss)_
- **[L1.latency]** HQ--Branch: 22.0 km × 5.0 µs/km = 0.11 ms one-way propagation, within the 5.0 ms budget (4.89 ms left for serialization, queuing and switching). Delay-sensitive traffic still needs priority queuing so congestion does not consume that headroom. _(ref: Project rule; physics: fiber propagation ≈ 5 µs/km)_
- **[L1.smf_er]** Selected OS2 single-mode fiber with 10GBASE-ER (1550 nm) for HQ--Colo because 35000.0 m exceeds the 10 km 10GBASE-LR reach. 10GBASE-ER uses the lower-loss 1550 nm window and reaches 40 km. _(ref: IEEE 802.3ae (10GBASE-ER))_
- **[L1.budget]** Optical budget for HQ--Colo (10GBASE-ER): fiber 8.75 dB (35.0 km × 0.25 dB/km) + 2 connectors × 0.75 dB + 0 splices × 0.3 dB = 10.25 dB against 11.0 dB allowed, margin 0.75 dB (pass, but below the 3.0 dB design margin: verify with an OTDR test). _(ref: IEEE 802.3ae channel insertion loss; TIA-568 component loss)_
- **[L1.latency]** HQ--Colo: 35.0 km × 5.0 µs/km = 0.175 ms one-way propagation, within the 5.0 ms budget (4.825 ms left for serialization, queuing and switching). Delay-sensitive traffic still needs priority queuing so congestion does not consume that headroom. _(ref: Project rule; physics: fiber propagation ≈ 5 µs/km)_
- **[L1.in_building]** 18 in-building connection(s) (switch-to-switch and router-to-switch in the same building) are patch runs assumed ≤ 100 m, so Cat6a 10GBASE-T is used. _(ref: IEEE 802.3an-2006)_

### TOPO
- **[TOPO.collapsed_core]** HQ: collapsed-core design (core and distribution combined) because the site has 1 building(s), below the 4-building point where a separate distribution layer pays off. Fewer devices and hops for 310 endpoints. _(ref: Cisco hierarchical campus design; Project rule)_
- **[TOPO.access]** HQ: 310 access ports needed, so 7 × 48-port switch(es) in 1 stack(s) (≤ 8 members per stack). 26 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.poe]** HQ-ACC1: 60 PoE port(s) × 30.0 W (802.3at Type 2) = 1800.0 W of PoE budget required from the switch power supplies. _(ref: IEEE 802.3at)_
- **[TOPO.redundant]** HQ: resiliency is high, so core switches and routers are paired and every access stack is dual-homed to both gateways. Any single device or uplink can fail without isolating users. _(ref: Project rule (resiliency=high))_
- **[TOPO.collapsed_core]** Branch: collapsed-core design (core and distribution combined) because the site has 1 building(s), below the 4-building point where a separate distribution layer pays off. Fewer devices and hops for 120 endpoints. _(ref: Cisco hierarchical campus design; Project rule)_
- **[TOPO.access]** Branch: 120 access ports needed, so 3 × 48-port switch(es) in 1 stack(s) (≤ 8 members per stack). 24 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.redundant]** Branch: resiliency is high, so core switches are paired and every access stack is dual-homed to both gateways. Any single device or uplink can fail without isolating users. _(ref: Project rule (resiliency=high))_
- **[TOPO.collapsed_core]** Colo: collapsed-core design (core and distribution combined) because the site has 1 building(s), below the 4-building point where a separate distribution layer pays off. Fewer devices and hops for 120 endpoints. _(ref: Cisco hierarchical campus design; Project rule)_
- **[TOPO.access]** Colo: 120 access ports needed, so 3 × 48-port switch(es) in 1 stack(s) (≤ 8 members per stack). 24 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.redundant]** Colo: resiliency is high, so core switches and routers are paired and every access stack is dual-homed to both gateways. Any single device or uplink can fail without isolating users. _(ref: Project rule (resiliency=high))_
- **[TOPO.dual_homed]** HQ--Branch is built as 2 circuits (HQ-R1–BRANCH-R1, HQ-R2–BRANCH-R1) so the site survives the loss of either router or circuit. _(ref: Project rule (resiliency=high))_
- **[TOPO.dual_homed]** HQ--Colo is built as 2 circuits (HQ-R1–COLO-R1, HQ-R2–COLO-R2) so the site survives the loss of either router or circuit. _(ref: Project rule (resiliency=high))_

### L2
- **[L2.native]** Native VLAN is the unused VLAN 999 on every trunk (not VLAN 1) and it is left out of the allowed lists. This blocks double-tagging VLAN hopping. Unused access ports are parked in it and shut down. _(ref: IEEE 802.1Q)_
- **[L2.edge_ports]** Access ports use PortFast (RSTP edge port, forwards immediately) and BPDU Guard (err-disables the port if a switch is plugged in), preventing accidental loops. _(ref: IEEE 802.1w)_
- **[L2.vlan_plan]** HQ: VLANs 10,20 each carry one segment, giving each role its own broadcast domain. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** HQ-ACC1 trunk to HQ-CORE1 allows only VLANs 10,20, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** HQ-ACC1 trunk to HQ-CORE2 allows only VLANs 10,20, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.stp_root]** HQ: Rapid PVST+ root primary on HQ-CORE1 and secondary on HQ-CORE2, so the root bridge is also the default gateway and frames never take a detour through an access switch. _(ref: IEEE 802.1w (Rapid PVST+))_
- **[L2.hsrp]** HQ: HSRPv2 gives each VLAN a virtual gateway (first usable address) shared by HQ-CORE1 (priority 110, active) and HQ-CORE2 (priority 100, standby). Each subnet reserves 2 extra addresses for the physical SVIs. _(ref: RFC 2281 (HSRP))_
- **[L2.vlan_plan]** Branch: VLANs 110 each carry one segment, giving each role its own broadcast domain. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BRANCH-ACC1 trunk to BRANCH-CORE1 allows only VLANs 110, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BRANCH-ACC1 trunk to BRANCH-CORE2 allows only VLANs 110, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.stp_root]** Branch: Rapid PVST+ root primary on BRANCH-CORE1 and secondary on BRANCH-CORE2, so the root bridge is also the default gateway and frames never take a detour through an access switch. _(ref: IEEE 802.1w (Rapid PVST+))_
- **[L2.hsrp]** Branch: HSRPv2 gives each VLAN a virtual gateway (first usable address) shared by BRANCH-CORE1 (priority 110, active) and BRANCH-CORE2 (priority 100, standby). Each subnet reserves 2 extra addresses for the physical SVIs. _(ref: RFC 2281 (HSRP))_
- **[L2.vlan_plan]** Colo: VLANs 210,220 each carry one segment, giving each role its own broadcast domain. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** COLO-ACC1 trunk to COLO-CORE1 allows only VLANs 210,220, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** COLO-ACC1 trunk to COLO-CORE2 allows only VLANs 210,220, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.stp_root]** Colo: Rapid PVST+ root primary on COLO-CORE1 and secondary on COLO-CORE2, so the root bridge is also the default gateway and frames never take a detour through an access switch. _(ref: IEEE 802.1w (Rapid PVST+))_
- **[L2.hsrp]** Colo: HSRPv2 gives each VLAN a virtual gateway (first usable address) shared by COLO-CORE1 (priority 110, active) and COLO-CORE2 (priority 100, standby). Each subnet reserves 2 extra addresses for the physical SVIs. _(ref: RFC 2281 (HSRP))_

### ROUTE
- **[ROUTE.ospf_multi_site]** Multi-area OSPF because the design spans 3 sites: HQ is the backbone (area 0) and every other site gets its own area, so flooding and SPF runs stay inside one site. _(ref: RFC 2328; Assignment §3)_
- **[ROUTE.area]** Area 0 (HQ) is OSPF area 0 with address block 10.20.0.0/23. _(ref: RFC 2328)_
- **[ROUTE.area]** Area 1 (Branch) is OSPF area 1 with address block 10.20.2.0/24. _(ref: RFC 2328)_
- **[ROUTE.area]** Area 2 (Colo) is OSPF area 2 with address block 10.20.3.0/24. _(ref: RFC 2328)_
- **[ROUTE.rid]** Router IDs come from Loopback0 /32 addresses. A loopback never goes down with a physical interface, so OSPF and BGP identities stay stable. _(ref: RFC 2328)_
- **[ROUTE.ospf_auth]** Every OSPF area uses message-digest (MD5) authentication and every adjacency interface carries the key, so a device plugged into a routed link cannot form an adjacency and inject routes. The key in the configs is a placeholder to replace before deployment. _(ref: RFC 2328 Appendix D)_
- **[ROUTE.ref_bw]** OSPF reference bandwidth is 100000 Mbps. With the default 100 Mbps every link of 100 Mb/s or more gets cost 1, so 10G and 1G paths would look equal. _(ref: RFC 2328 (interface cost))_
- **[ROUTE.summary]** ABR BRANCH-R1 summarizes area 1 as 10.20.2.0/24 (1 route instead of 7), which works because the area's subnets were allocated from one contiguous block. _(ref: RFC 2328; RFC 4632)_
- **[ROUTE.summary]** ABR COLO-R1 summarizes area 2 as 10.20.3.0/24 (1 route instead of 9), which works because the area's subnets were allocated from one contiguous block. _(ref: RFC 2328; RFC 4632)_
- **[ROUTE.summary]** ABR COLO-R2 summarizes area 2 as 10.20.3.0/24 (1 route instead of 9), which works because the area's subnets were allocated from one contiguous block. _(ref: RFC 2328; RFC 4632)_

### VLSM
- **[VLSM.block]** Area 0 (HQ) gets the contiguous block 10.20.0.0/23 (512 addresses) so all of its subnets can be summarized as one route. _(ref: RFC 4632)_
- **[VLSM.block]** Area 1 (Branch) gets the contiguous block 10.20.2.0/24 (256 addresses) so all of its subnets can be summarized as one route. _(ref: RFC 4632)_
- **[VLSM.block]** Area 2 (Colo) gets the contiguous block 10.20.3.0/24 (256 addresses) so all of its subnets can be summarized as one route. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 1024 of 65536 addresses in 10.20.0.0/16 (1.56% of the root used). 1024 addresses were actually needed, so packing efficiency is 100.0% (0 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.subnet]** HQ-Users: 252 hosts + 1 gateway need 253 usable addresses; the smallest block is /24 (2^8 − 2 = 254 usable), giving 99.61% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** HQ-Voice: 62 hosts + 1 gateway need 63 usable addresses; the smallest block is /25 (2^7 − 2 = 126 usable), giving 50.0% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.p2p]** HQ-CORE1--HQ-CORE2: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** HQ-R1--BRANCH-R1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** HQ-R1--COLO-R1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** HQ-R1--HQ-CORE1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** HQ-R2--BRANCH-R1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** HQ-R2--COLO-R2: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** HQ-R2--HQ-CORE2: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.loopback]** HQ-CORE1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** HQ-CORE2 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** HQ-R1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** HQ-R2 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 402 of 512 addresses in 10.20.0.0/23 (78.52% of the root used). 334 addresses were actually needed, so packing efficiency is 83.08% (68 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.subnet]** Branch-Users: 122 hosts + 1 gateway need 123 usable addresses; the smallest block is /25 (2^7 − 2 = 126 usable), giving 97.62% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.p2p]** BRANCH-CORE1--BRANCH-CORE2: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** BRANCH-R1--BRANCH-CORE1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** BRANCH-R1--BRANCH-CORE2: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.loopback]** BRANCH-CORE1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** BRANCH-CORE2 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** BRANCH-R1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 137 of 256 addresses in 10.20.2.0/24 (53.52% of the root used). 132 addresses were actually needed, so packing efficiency is 96.35% (5 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.subnet]** Colo-Ops: 82 hosts + 1 gateway need 83 usable addresses; the smallest block is /25 (2^7 − 2 = 126 usable), giving 65.87% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** Colo-Trading: 42 hosts + 1 gateway need 43 usable addresses; the smallest block is /26 (2^6 − 2 = 62 usable), giving 69.35% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.p2p]** COLO-CORE1--COLO-CORE2: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** COLO-R1--COLO-CORE1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** COLO-R2--COLO-CORE2: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.loopback]** COLO-CORE1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** COLO-CORE2 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** COLO-R1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** COLO-R2 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 202 of 256 addresses in 10.20.3.0/24 (78.91% of the root used). 136 addresses were actually needed, so packing efficiency is 67.33% (66 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_

### ACL
- **[ACL.policy]** Branch-Users → Colo-Trading: permit tcp port 443 via ACL-BRANCH-USERS-IN, applied inbound on the Branch-Users gateway so the decision is made at the first layer-3 hop. _(ref: Cisco IOS extended ACL (first match))_
- **[ACL.policy]** Branch-Users → Colo-Trading: deny ip via ACL-BRANCH-USERS-IN, applied inbound on the Branch-Users gateway so the decision is made at the first layer-3 hop. _(ref: Cisco IOS extended ACL (first match))_
- **[ACL.default]** ACL-BRANCH-USERS-IN ends with 'permit ip any any' so traffic not covered by a policy is allowed; otherwise the IOS implicit deny would drop all other traffic from Branch-Users. _(ref: Cisco IOS extended ACL (implicit deny))_

### QOS
- **[QOS.llq]** HQ-R1 TenGigabitEthernet0/0/1 toward HQ--Branch: low-latency queuing puts DSCP EF traffic (voice, latency-critical flows) in a strict priority queue capped at 30% of the link, everything else in fair-queue, so queuing delay under congestion does not eat the 5.0 ms budget. Endpoints (e.g. IP phones) are assumed to mark EF. _(ref: RFC 3246 (EF PHB); RFC 2474 (DSCP))_
- **[QOS.llq]** BRANCH-R1 TenGigabitEthernet0/0/2 toward HQ--Branch: low-latency queuing puts DSCP EF traffic (voice, latency-critical flows) in a strict priority queue capped at 30% of the link, everything else in fair-queue, so queuing delay under congestion does not eat the 5.0 ms budget. Endpoints (e.g. IP phones) are assumed to mark EF. _(ref: RFC 3246 (EF PHB); RFC 2474 (DSCP))_
- **[QOS.llq]** HQ-R2 TenGigabitEthernet0/0/1 toward HQ--Branch: low-latency queuing puts DSCP EF traffic (voice, latency-critical flows) in a strict priority queue capped at 30% of the link, everything else in fair-queue, so queuing delay under congestion does not eat the 5.0 ms budget. Endpoints (e.g. IP phones) are assumed to mark EF. _(ref: RFC 3246 (EF PHB); RFC 2474 (DSCP))_
- **[QOS.llq]** BRANCH-R1 TenGigabitEthernet0/0/3 toward HQ--Branch: low-latency queuing puts DSCP EF traffic (voice, latency-critical flows) in a strict priority queue capped at 30% of the link, everything else in fair-queue, so queuing delay under congestion does not eat the 5.0 ms budget. Endpoints (e.g. IP phones) are assumed to mark EF. _(ref: RFC 3246 (EF PHB); RFC 2474 (DSCP))_
- **[QOS.llq]** HQ-R1 TenGigabitEthernet0/0/2 toward HQ--Colo: low-latency queuing puts DSCP EF traffic (voice, latency-critical flows) in a strict priority queue capped at 30% of the link, everything else in fair-queue, so queuing delay under congestion does not eat the 5.0 ms budget. Endpoints (e.g. IP phones) are assumed to mark EF. _(ref: RFC 3246 (EF PHB); RFC 2474 (DSCP))_
- **[QOS.llq]** COLO-R1 TenGigabitEthernet0/0/1 toward HQ--Colo: low-latency queuing puts DSCP EF traffic (voice, latency-critical flows) in a strict priority queue capped at 30% of the link, everything else in fair-queue, so queuing delay under congestion does not eat the 5.0 ms budget. Endpoints (e.g. IP phones) are assumed to mark EF. _(ref: RFC 3246 (EF PHB); RFC 2474 (DSCP))_
- **[QOS.llq]** HQ-R2 TenGigabitEthernet0/0/2 toward HQ--Colo: low-latency queuing puts DSCP EF traffic (voice, latency-critical flows) in a strict priority queue capped at 30% of the link, everything else in fair-queue, so queuing delay under congestion does not eat the 5.0 ms budget. Endpoints (e.g. IP phones) are assumed to mark EF. _(ref: RFC 3246 (EF PHB); RFC 2474 (DSCP))_
- **[QOS.llq]** COLO-R2 TenGigabitEthernet0/0/1 toward HQ--Colo: low-latency queuing puts DSCP EF traffic (voice, latency-critical flows) in a strict priority queue capped at 30% of the link, everything else in fair-queue, so queuing delay under congestion does not eat the 5.0 ms budget. Endpoints (e.g. IP phones) are assumed to mark EF. _(ref: RFC 3246 (EF PHB); RFC 2474 (DSCP))_

## Verification

```
Verification: PASS
  [ok] config_parse
  [ok] gateway_reachability
  [ok] reachability_and_policy
  [ok] no_routing_loops
  [ok] no_overlapping_subnets
  [ok] access_trunk_scope
```

## Security findings

| Device | Score | Rule | Severity | Where | Fix |
|---|---|---|---|---|---|
| HQ-CORE1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| HQ-CORE2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| HQ-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| HQ-R1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| HQ-R2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BRANCH-CORE1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BRANCH-CORE1 | 92 | SEC-12 ACL ends with 'permit ip any any' | info | ip access-list ACL-BRANCH-USERS-IN | intended for default-allow policies (D-020) |
| BRANCH-CORE2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BRANCH-CORE2 | 92 | SEC-12 ACL ends with 'permit ip any any' | info | ip access-list ACL-BRANCH-USERS-IN | intended for default-allow policies (D-020) |
| BRANCH-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BRANCH-R1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| COLO-CORE1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| COLO-CORE2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| COLO-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| COLO-R1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| COLO-R2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |

## Single points of failure

- BRANCH-R1 is a single point of failure: removing it separates 2 segment-hosting device(s) (COLO-ACC1, HQ-ACC1) from the rest of the network.
- Resilience score 97/100: 1 of 33 infrastructure elements (non-access devices and cables) are single points of failure. Access stacks are excluded because users on a stack always depend on it.

## Bill of materials

_PLACEHOLDER ESTIMATES in INR, not quotes. Owner must replace with real vendor prices before using totals. Units: per item unless stated._

| Item | Qty | Unit | Unit price | Total | Because of |
|---|---|---|---|---|---|
| OS2 single-mode fiber | 125400 | m | 70 | 8,778,000 | L1.smf_er |
| Cat6a patch cord (in-building) | 18 | pcs | 600 | 10,800 | L1.in_building |
| SFP+ 10GBASE-ER | 8 | pcs | 25,000 | 200,000 | L1.smf_er |
| 48-port PoE+ access switch | 7 | pcs | 350,000 | 2,450,000 | TOPO.poe |
| 48-port access switch | 6 | pcs | 220,000 | 1,320,000 | TOPO.access |
| Core switch | 6 | pcs | 900,000 | 5,400,000 | TOPO.collapsed_core |
| Router | 5 | pcs | 500,000 | 2,500,000 | ROUTE.ospf_multi_site |
