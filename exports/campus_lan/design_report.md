# NetArchitect Design Report: campus_lan

## Summary

- Root prefix: `10.10.0.0/16`
- Sites: Campus (campus)
- Endpoints: 1600
- Topology: Campus: collapsed_core
- Routing: OSPF single-area
- Devices: 8, cables: 14, subnets: 13
- Verification: **PASS**
- Security score: **92/100**
- Resilience score: **100/100**
- Estimated capex: INR 12,010,230 (placeholder prices), monthly WAN: INR 0

## Physical media

| Link | Distance | Media | Transceiver |
|---|---|---|---|
| BldgA--BldgB | 180 m | OM4 multimode fiber | 10GBASE-SR |
| BldgA--BldgC | 350 m | OM4 multimode fiber | 10GBASE-SR |
| BldgB--BldgC | 280 m | OM4 multimode fiber | 10GBASE-SR |

## IP plan

| Subnet | Unit | VLAN | Network | Mask | Wildcard | Gateway | Broadcast | Usable | Util % |
|---|---|---|---|---|---|---|---|---|---|
| Staff-A | Area 0 | 10 | 10.10.0.0/23 | 255.255.254.0 | 0.0.1.255 | 10.10.0.1 | 10.10.1.255 | 510 | 88.82 |
| Staff-B | Area 0 | 11 | 10.10.2.0/23 | 255.255.254.0 | 0.0.1.255 | 10.10.2.1 | 10.10.3.255 | 510 | 79.02 |
| Staff-C | Area 0 | 12 | 10.10.4.0/23 | 255.255.254.0 | 0.0.1.255 | 10.10.4.1 | 10.10.5.255 | 510 | 59.41 |
| Guest-C | Area 0 | 30 | 10.10.6.0/25 | 255.255.255.128 | 0.0.0.127 | 10.10.6.1 | 10.10.6.127 | 126 | 81.75 |
| Servers | Area 0 | 50 | 10.10.6.128/25 | 255.255.255.128 | 0.0.0.127 | 10.10.6.129 | 10.10.6.255 | 126 | 50.0 |
| Voice-A | Area 0 | 20 | 10.10.7.0/25 | 255.255.255.128 | 0.0.0.127 | 10.10.7.1 | 10.10.7.127 | 126 | 81.75 |
| Voice-B | Area 0 | 21 | 10.10.7.128/25 | 255.255.255.128 | 0.0.0.127 | 10.10.7.129 | 10.10.7.255 | 126 | 65.87 |
| APs-A | Area 0 | 40 | 10.10.8.0/26 | 255.255.255.192 | 0.0.0.63 | 10.10.8.1 | 10.10.8.63 | 62 | 69.35 |
| APs-B | Area 0 | 41 | 10.10.8.64/26 | 255.255.255.192 | 0.0.0.63 | 10.10.8.65 | 10.10.8.127 | 62 | 53.23 |
| APs-C | Area 0 | 42 | 10.10.8.128/26 | 255.255.255.192 | 0.0.0.63 | 10.10.8.129 | 10.10.8.191 | 62 | 69.35 |
| CAMPUS-CORE1--CAMPUS-CORE2 | Area 0 |  | 10.10.8.192/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| CAMPUS-CORE1 Loopback0 | Area 0 |  | 10.10.8.194/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| CAMPUS-CORE2 Loopback0 | Area 0 |  | 10.10.8.195/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |

## Architectural rationale

### L1
- **[L1.mmf]** Selected OM4 multimode fiber with 10GBASE-SR (850 nm) for BldgA--BldgB because 180.0 m exceeds the 100 m copper limit of 10GBASE-T (IEEE 802.3an) but is within the 400 m OM4 reach. At 850 nm, modal dispersion in multimode fiber caps 10G reach at 400 m on OM4. _(ref: IEEE 802.3ae (10GBASE-SR), TIA-492AAAD (OM4))_
- **[L1.budget]** Optical budget for BldgA--BldgB (10GBASE-SR): fiber 0.63 dB (0.18 km × 3.5 dB/km) + 2 connectors × 0.75 dB + 0 splices × 0.3 dB = 2.13 dB against 2.9 dB allowed, margin 0.77 dB (pass, but below the 3.0 dB design margin: verify with an OTDR test). _(ref: IEEE 802.3ae channel insertion loss; TIA-568 component loss)_
- **[L1.mmf]** Selected OM4 multimode fiber with 10GBASE-SR (850 nm) for BldgA--BldgC because 350.0 m exceeds the 100 m copper limit of 10GBASE-T (IEEE 802.3an) but is within the 400 m OM4 reach. At 850 nm, modal dispersion in multimode fiber caps 10G reach at 400 m on OM4. _(ref: IEEE 802.3ae (10GBASE-SR), TIA-492AAAD (OM4))_
- **[L1.budget]** Optical budget for BldgA--BldgC (10GBASE-SR): fiber 1.22 dB (0.35 km × 3.5 dB/km) + 2 connectors × 0.75 dB + 0 splices × 0.3 dB = 2.72 dB against 2.9 dB allowed, margin 0.18 dB (pass, but below the 3.0 dB design margin: verify with an OTDR test). _(ref: IEEE 802.3ae channel insertion loss; TIA-568 component loss)_
- **[L1.mmf]** Selected OM4 multimode fiber with 10GBASE-SR (850 nm) for BldgB--BldgC because 280.0 m exceeds the 100 m copper limit of 10GBASE-T (IEEE 802.3an) but is within the 400 m OM4 reach. At 850 nm, modal dispersion in multimode fiber caps 10G reach at 400 m on OM4. _(ref: IEEE 802.3ae (10GBASE-SR), TIA-492AAAD (OM4))_
- **[L1.budget]** Optical budget for BldgB--BldgC (10GBASE-SR): fiber 0.98 dB (0.28 km × 3.5 dB/km) + 2 connectors × 0.75 dB + 0 splices × 0.3 dB = 2.48 dB against 2.9 dB allowed, margin 0.42 dB (pass, but below the 3.0 dB design margin: verify with an OTDR test). _(ref: IEEE 802.3ae channel insertion loss; TIA-568 component loss)_
- **[L1.in_building]** 6 in-building connection(s) (switch-to-switch and router-to-switch in the same building) are patch runs assumed ≤ 100 m, so Cat6a 10GBASE-T is used. _(ref: IEEE 802.3an-2006)_

### TOPO
- **[TOPO.collapsed_core]** Campus: collapsed-core design (core and distribution combined) because the site has 3 building(s), below the 4-building point where a separate distribution layer pays off. Fewer devices and hops for 1600 endpoints. _(ref: Cisco hierarchical campus design; Project rule)_
- **[TOPO.access]** BldgA: 650 access ports needed, so 14 × 48-port switch(es) in 2 stack(s) (≤ 8 members per stack). 22 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.poe]** BLDGA-ACC2: 140 PoE port(s) × 30.0 W (802.3at Type 2) = 4200.0 W of PoE budget required from the switch power supplies. _(ref: IEEE 802.3at)_
- **[TOPO.access]** BldgB: 510 access ports needed, so 11 × 48-port switch(es) in 2 stack(s) (≤ 8 members per stack). 18 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.poe]** BLDGB-ACC2: 110 PoE port(s) × 30.0 W (802.3at Type 2) = 3300.0 W of PoE budget required from the switch power supplies. _(ref: IEEE 802.3at)_
- **[TOPO.access]** BldgC: 440 access ports needed, so 10 × 48-port switch(es) in 2 stack(s) (≤ 8 members per stack). 40 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.poe]** BLDGC-ACC2: 40 PoE port(s) × 30.0 W (802.3at Type 2) = 1200.0 W of PoE budget required from the switch power supplies. _(ref: IEEE 802.3at)_
- **[TOPO.redundant]** Campus: resiliency is high, so core switches are paired and every access stack is dual-homed to both gateways. Any single device or uplink can fail without isolating users. _(ref: Project rule (resiliency=high))_

### L2
- **[L2.native]** Native VLAN is the unused VLAN 999 on every trunk (not VLAN 1) and it is left out of the allowed lists. This blocks double-tagging VLAN hopping. Unused access ports are parked in it and shut down. _(ref: IEEE 802.1Q)_
- **[L2.edge_ports]** Access ports use PortFast (RSTP edge port, forwards immediately) and BPDU Guard (err-disables the port if a switch is plugged in), preventing accidental loops. _(ref: IEEE 802.1w)_
- **[L2.vlan_plan]** Campus: VLANs 10,11,12,20,21,30,40,41,42,50 each carry one segment, giving each role its own broadcast domain. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGA-ACC1 trunk to CAMPUS-CORE1 allows only VLANs 10, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGA-ACC1 trunk to CAMPUS-CORE2 allows only VLANs 10, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGA-ACC2 trunk to CAMPUS-CORE1 allows only VLANs 10,20,40,50, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGA-ACC2 trunk to CAMPUS-CORE2 allows only VLANs 10,20,40,50, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGB-ACC1 trunk to CAMPUS-CORE1 allows only VLANs 11, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGB-ACC1 trunk to CAMPUS-CORE2 allows only VLANs 11, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGB-ACC2 trunk to CAMPUS-CORE1 allows only VLANs 11,21,41, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGB-ACC2 trunk to CAMPUS-CORE2 allows only VLANs 11,21,41, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGC-ACC1 trunk to CAMPUS-CORE1 allows only VLANs 12, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGC-ACC1 trunk to CAMPUS-CORE2 allows only VLANs 12, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGC-ACC2 trunk to CAMPUS-CORE1 allows only VLANs 12,30,42, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BLDGC-ACC2 trunk to CAMPUS-CORE2 allows only VLANs 12,30,42, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.stp_root]** Campus: Rapid PVST+ root primary on CAMPUS-CORE1 and secondary on CAMPUS-CORE2, so the root bridge is also the default gateway and frames never take a detour through an access switch. _(ref: IEEE 802.1w (Rapid PVST+))_
- **[L2.hsrp]** Campus: HSRPv2 gives each VLAN a virtual gateway (first usable address) shared by CAMPUS-CORE1 (priority 110, active) and CAMPUS-CORE2 (priority 100, standby). Each subnet reserves 2 extra addresses for the physical SVIs. _(ref: RFC 2281 (HSRP))_

### ROUTE
- **[ROUTE.ospf_single]** Single-area OSPF (area 0) because the design is one site with 13 subnets, below the 50-subnet threshold. One link-state database converges fast and needs no ABRs. _(ref: RFC 2328; Assignment §3)_
- **[ROUTE.area]** Area 0 is OSPF area 0 with address block 10.10.0.0/16. _(ref: RFC 2328)_
- **[ROUTE.rid]** Router IDs come from Loopback0 /32 addresses. A loopback never goes down with a physical interface, so OSPF and BGP identities stay stable. _(ref: RFC 2328)_
- **[ROUTE.ospf_auth]** Every OSPF area uses message-digest (MD5) authentication and every adjacency interface carries the key, so a device plugged into a routed link cannot form an adjacency and inject routes. The key in the configs is a placeholder to replace before deployment. _(ref: RFC 2328 Appendix D)_
- **[ROUTE.ref_bw]** OSPF reference bandwidth is 100000 Mbps. With the default 100 Mbps every link of 100 Mb/s or more gets cost 1, so 10G and 1G paths would look equal. _(ref: RFC 2328 (interface cost))_

### VLSM
- **[VLSM.subnet]** Staff-A: 452 hosts + 1 gateway need 453 usable addresses; the smallest block is /23 (2^9 − 2 = 510 usable), giving 88.82% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** Staff-B: 402 hosts + 1 gateway need 403 usable addresses; the smallest block is /23 (2^9 − 2 = 510 usable), giving 79.02% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** Staff-C: 302 hosts + 1 gateway need 303 usable addresses; the smallest block is /23 (2^9 − 2 = 510 usable), giving 59.41% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** Guest-C: 102 hosts + 1 gateway need 103 usable addresses; the smallest block is /25 (2^7 − 2 = 126 usable), giving 81.75% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** Servers: 62 hosts + 1 gateway need 63 usable addresses; the smallest block is /25 (2^7 − 2 = 126 usable), giving 50.0% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** Voice-A: 102 hosts + 1 gateway need 103 usable addresses; the smallest block is /25 (2^7 − 2 = 126 usable), giving 81.75% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** Voice-B: 82 hosts + 1 gateway need 83 usable addresses; the smallest block is /25 (2^7 − 2 = 126 usable), giving 65.87% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** APs-A: 42 hosts + 1 gateway need 43 usable addresses; the smallest block is /26 (2^6 − 2 = 62 usable), giving 69.35% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** APs-B: 32 hosts + 1 gateway need 33 usable addresses; the smallest block is /26 (2^6 − 2 = 62 usable), giving 53.23% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.subnet]** APs-C: 42 hosts + 1 gateway need 43 usable addresses; the smallest block is /26 (2^6 − 2 = 62 usable), giving 69.35% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.p2p]** CAMPUS-CORE1--CAMPUS-CORE2: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.loopback]** CAMPUS-CORE1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** CAMPUS-CORE2 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 2244 of 65536 addresses in 10.10.0.0/16 (3.42% of the root used). 1634 addresses were actually needed, so packing efficiency is 72.82% (610 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_

### ACL
- **[ACL.policy]** Guest-C → Servers: deny ip via ACL-GUEST-C-IN, applied inbound on the Guest-C gateway so the decision is made at the first layer-3 hop. _(ref: Cisco IOS extended ACL (first match))_
- **[ACL.policy]** Guest-C → Staff-A: deny ip via ACL-GUEST-C-IN, applied inbound on the Guest-C gateway so the decision is made at the first layer-3 hop. _(ref: Cisco IOS extended ACL (first match))_
- **[ACL.policy]** Guest-C → Staff-B: deny ip via ACL-GUEST-C-IN, applied inbound on the Guest-C gateway so the decision is made at the first layer-3 hop. _(ref: Cisco IOS extended ACL (first match))_
- **[ACL.policy]** Guest-C → Staff-C: deny ip via ACL-GUEST-C-IN, applied inbound on the Guest-C gateway so the decision is made at the first layer-3 hop. _(ref: Cisco IOS extended ACL (first match))_
- **[ACL.default]** ACL-GUEST-C-IN ends with 'permit ip any any' so traffic not covered by a policy is allowed; otherwise the IOS implicit deny would drop all other traffic from Guest-C. _(ref: Cisco IOS extended ACL (implicit deny))_

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
| CAMPUS-CORE1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| CAMPUS-CORE1 | 92 | SEC-12 ACL ends with 'permit ip any any' | info | ip access-list ACL-GUEST-C-IN | intended for default-allow policies (D-020) |
| CAMPUS-CORE2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| CAMPUS-CORE2 | 92 | SEC-12 ACL ends with 'permit ip any any' | info | ip access-list ACL-GUEST-C-IN | intended for default-allow policies (D-020) |
| BLDGA-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BLDGA-ACC2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BLDGB-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BLDGB-ACC2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BLDGC-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BLDGC-ACC2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |

## Single points of failure

- Resilience score 100/100: 0 of 16 infrastructure elements (non-access devices and cables) are single points of failure. Access stacks are excluded because users on a stack always depend on it.

## Bill of materials

_PLACEHOLDER ESTIMATES in INR, not quotes. Owner must replace with real vendor prices before using totals. Units: per item unless stated._

| Item | Qty | Unit | Unit price | Total | Because of |
|---|---|---|---|---|---|
| OM4 multimode fiber | 2333 | m | 110 | 256,630 | L1.mmf |
| Cat6a patch cord (in-building) | 6 | pcs | 600 | 3,600 | L1.in_building |
| SFP+ 10GBASE-SR | 16 | pcs | 2,500 | 40,000 | L1.mmf |
| 48-port PoE+ access switch | 17 | pcs | 350,000 | 5,950,000 | TOPO.poe |
| 48-port access switch | 18 | pcs | 220,000 | 3,960,000 | TOPO.access |
| Core switch | 2 | pcs | 900,000 | 1,800,000 | TOPO.collapsed_core |
