# NetArchitect Design Report: global_wan

## Summary

- Root prefix: `10.100.0.0/16`
- Sites: Delhi (hq), Mumbai (branch), Bengaluru (branch), Singapore (branch), CloudVPC (cloud)
- Endpoints: 2200
- Topology: Delhi: collapsed_core, Mumbai: collapsed_core, Bengaluru: collapsed_core, Singapore: collapsed_core
- Routing: OSPF multi-area + eBGP
- Devices: 17, cables: 16, subnets: 24
- Verification: **PASS**
- Security score: **88/100**
- Resilience score: **4/100**
- Estimated capex: INR 15,287,200 (placeholder prices), monthly WAN: INR 150,000

## Physical media

| Link | Distance | Media | Transceiver |
|---|---|---|---|
| Delhi--Mumbai | 1.15e+06 m | carrier handoff (Cat6a UTP) | 10GBASE-T |
| Delhi--Bengaluru | 1.74e+06 m | carrier handoff (Cat6a UTP) | 10GBASE-T |
| Delhi--Singapore | 4.15e+06 m | internet handoff (Cat6a UTP) | 10GBASE-T |
| Delhi--CloudVPC | 1000 m | internet handoff (Cat6a UTP) | 10GBASE-T |

## IP plan

| Subnet | Unit | VLAN | Network | Mask | Wildcard | Gateway | Broadcast | Usable | Util % |
|---|---|---|---|---|---|---|---|---|---|
| Delhi-IoT | Area 0 (Delhi) | 10 | 10.100.0.0/22 | 255.255.252.0 | 0.0.3.255 | 10.100.0.1 | 10.100.3.255 | 1022 | 58.81 |
| DELHI-R1 Tunnel1--SINGAPORE-R1 Tunnel1 | Area 0 (Delhi) |  | 10.100.4.0/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| DELHI-R1 Tunnel2--CLOUDVPC-VGW Tunnel1 | Area 0 (Delhi) |  | 10.100.4.2/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| DELHI-R1--BENGALURU-R1 | Area 0 (Delhi) |  | 10.100.4.4/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| DELHI-R1--DELHI-CORE1 | Area 0 (Delhi) |  | 10.100.4.6/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| DELHI-R1--MUMBAI-R1 | Area 0 (Delhi) |  | 10.100.4.8/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| DELHI-CORE1 Loopback0 | Area 0 (Delhi) |  | 10.100.4.10/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| DELHI-R1 Loopback0 | Area 0 (Delhi) |  | 10.100.4.11/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| Mumbai-IoT | Area 1 (Mumbai) | 20 | 10.100.8.0/23 | 255.255.254.0 | 0.0.1.255 | 10.100.8.1 | 10.100.9.255 | 510 | 98.24 |
| MUMBAI-R1--MUMBAI-CORE1 | Area 1 (Mumbai) |  | 10.100.10.0/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| MUMBAI-CORE1 Loopback0 | Area 1 (Mumbai) |  | 10.100.10.2/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| MUMBAI-R1 Loopback0 | Area 1 (Mumbai) |  | 10.100.10.3/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| Blr-IoT | Area 2 (Bengaluru) | 30 | 10.100.12.0/23 | 255.255.254.0 | 0.0.1.255 | 10.100.12.1 | 10.100.13.255 | 510 | 98.24 |
| BENGALURU-R1--BENGALURU-CORE1 | Area 2 (Bengaluru) |  | 10.100.14.0/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| BENGALURU-CORE1 Loopback0 | Area 2 (Bengaluru) |  | 10.100.14.2/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| BENGALURU-R1 Loopback0 | Area 2 (Bengaluru) |  | 10.100.14.3/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| Sg-IoT | Area 3 (Singapore) | 40 | 10.100.16.0/23 | 255.255.254.0 | 0.0.1.255 | 10.100.16.1 | 10.100.17.255 | 510 | 78.63 |
| SINGAPORE-R1--SINGAPORE-CORE1 | Area 3 (Singapore) |  | 10.100.18.0/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| SINGAPORE-CORE1 Loopback0 | Area 3 (Singapore) |  | 10.100.18.2/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| SINGAPORE-R1 Loopback0 | Area 3 (Singapore) |  | 10.100.18.3/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| VPC-Apps | Cloud CloudVPC | 100 | 10.100.20.0/24 | 255.255.255.0 | 0.0.0.255 | 10.100.20.1 | 10.100.20.255 | 254 | 79.13 |
| CLOUDVPC-VGW Loopback0 | Cloud CloudVPC |  | 10.100.21.0/32 | 255.255.255.255 | 0.0.0.0 | - | - | 1 | 100.0 |
| DELHI-R1--CLOUDVPC-VGW underlay | internet underlay |  | 203.0.113.0/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |
| DELHI-R1--SINGAPORE-R1 underlay | internet underlay |  | 203.0.113.2/31 | 255.255.255.254 | 0.0.0.1 | - | - | 2 | 100.0 |

## Architectural rationale

### L1
- **[L1.provider]** Delhi--Mumbai uses a carrier service: the inter-site physical layer belongs to the provider, so only the local handoff is designed (Cat6a 10GBASE-T to the demarc, assumed ≤ 100 m). _(ref: IEEE 802.3an-2006 (handoff))_
- **[L1.provider]** Delhi--Bengaluru uses a carrier service: the inter-site physical layer belongs to the provider, so only the local handoff is designed (Cat6a 10GBASE-T to the demarc, assumed ≤ 100 m). _(ref: IEEE 802.3an-2006 (handoff))_
- **[L1.provider]** Delhi--Singapore uses a internet service: the inter-site physical layer belongs to the provider, so only the local handoff is designed (Cat6a 10GBASE-T to the demarc, assumed ≤ 100 m). _(ref: IEEE 802.3an-2006 (handoff))_
- **[L1.provider]** Delhi--CloudVPC uses a internet service: the inter-site physical layer belongs to the provider, so only the local handoff is designed (Cat6a 10GBASE-T to the demarc, assumed ≤ 100 m). _(ref: IEEE 802.3an-2006 (handoff))_
- **[L1.in_building]** 12 in-building connection(s) (switch-to-switch and router-to-switch in the same building) are patch runs assumed ≤ 100 m, so Cat6a 10GBASE-T is used. _(ref: IEEE 802.3an-2006)_

### TOPO
- **[TOPO.collapsed_core]** Delhi: collapsed-core design (core and distribution combined) because the site has 1 building(s), below the 4-building point where a separate distribution layer pays off. Fewer devices and hops for 600 endpoints. _(ref: Cisco hierarchical campus design; Project rule)_
- **[TOPO.access]** Delhi: 600 access ports needed, so 13 × 48-port switch(es) in 2 stack(s) (≤ 8 members per stack). 24 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.collapsed_core]** Mumbai: collapsed-core design (core and distribution combined) because the site has 1 building(s), below the 4-building point where a separate distribution layer pays off. Fewer devices and hops for 500 endpoints. _(ref: Cisco hierarchical campus design; Project rule)_
- **[TOPO.access]** Mumbai: 500 access ports needed, so 11 × 48-port switch(es) in 2 stack(s) (≤ 8 members per stack). 28 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.collapsed_core]** Bengaluru: collapsed-core design (core and distribution combined) because the site has 1 building(s), below the 4-building point where a separate distribution layer pays off. Fewer devices and hops for 500 endpoints. _(ref: Cisco hierarchical campus design; Project rule)_
- **[TOPO.access]** Bengaluru: 500 access ports needed, so 11 × 48-port switch(es) in 2 stack(s) (≤ 8 members per stack). 28 spare port(s) are shut down. _(ref: Project rule)_
- **[TOPO.collapsed_core]** Singapore: collapsed-core design (core and distribution combined) because the site has 1 building(s), below the 4-building point where a separate distribution layer pays off. Fewer devices and hops for 400 endpoints. _(ref: Cisco hierarchical campus design; Project rule)_
- **[TOPO.access]** Singapore: 400 access ports needed, so 9 × 48-port switch(es) in 2 stack(s) (≤ 8 members per stack). 32 spare port(s) are shut down. _(ref: Project rule)_

### L2
- **[L2.native]** Native VLAN is the unused VLAN 999 on every trunk (not VLAN 1) and it is left out of the allowed lists. This blocks double-tagging VLAN hopping. Unused access ports are parked in it and shut down. _(ref: IEEE 802.1Q)_
- **[L2.edge_ports]** Access ports use PortFast (RSTP edge port, forwards immediately) and BPDU Guard (err-disables the port if a switch is plugged in), preventing accidental loops. _(ref: IEEE 802.1w)_
- **[L2.vlan_plan]** Delhi: VLANs 10 each carry one segment, giving each role its own broadcast domain. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** DELHI-ACC1 trunk to DELHI-CORE1 allows only VLANs 10, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** DELHI-ACC2 trunk to DELHI-CORE1 allows only VLANs 10, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.stp_root]** Delhi: Rapid PVST+ root primary on DELHI-CORE1, so the root bridge is also the default gateway and frames never take a detour through an access switch. _(ref: IEEE 802.1w (Rapid PVST+))_
- **[L2.vlan_plan]** Mumbai: VLANs 20 each carry one segment, giving each role its own broadcast domain. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** MUMBAI-ACC1 trunk to MUMBAI-CORE1 allows only VLANs 20, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** MUMBAI-ACC2 trunk to MUMBAI-CORE1 allows only VLANs 20, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.stp_root]** Mumbai: Rapid PVST+ root primary on MUMBAI-CORE1, so the root bridge is also the default gateway and frames never take a detour through an access switch. _(ref: IEEE 802.1w (Rapid PVST+))_
- **[L2.vlan_plan]** Bengaluru: VLANs 30 each carry one segment, giving each role its own broadcast domain. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BENGALURU-ACC1 trunk to BENGALURU-CORE1 allows only VLANs 30, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** BENGALURU-ACC2 trunk to BENGALURU-CORE1 allows only VLANs 30, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.stp_root]** Bengaluru: Rapid PVST+ root primary on BENGALURU-CORE1, so the root bridge is also the default gateway and frames never take a detour through an access switch. _(ref: IEEE 802.1w (Rapid PVST+))_
- **[L2.vlan_plan]** Singapore: VLANs 40 each carry one segment, giving each role its own broadcast domain. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** SINGAPORE-ACC1 trunk to SINGAPORE-CORE1 allows only VLANs 40, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.trunk_prune]** SINGAPORE-ACC2 trunk to SINGAPORE-CORE1 allows only VLANs 40, the VLANs that have ports behind it, instead of all 4094. This limits broadcast flooding and blast radius. _(ref: IEEE 802.1Q)_
- **[L2.stp_root]** Singapore: Rapid PVST+ root primary on SINGAPORE-CORE1, so the root bridge is also the default gateway and frames never take a detour through an access switch. _(ref: IEEE 802.1w (Rapid PVST+))_

### ROUTE
- **[ROUTE.ospf_multi_site]** Multi-area OSPF because the design spans 5 sites: Delhi is the backbone (area 0) and every other site gets its own area, so flooding and SPF runs stay inside one site. _(ref: RFC 2328; Assignment §3)_
- **[ROUTE.ipsec]** Delhi--Singapore runs over the internet, so traffic between DELHI-R1 and SINGAPORE-R1 is encrypted in a route-based IPsec tunnel (VTI, AES-256 / SHA-256, DH group 14). Underlay addresses come from 203.0.113.0/24 (RFC 5737 documentation range): replace them with the real public IPs. _(ref: RFC 4301; RFC 5737)_
- **[ROUTE.ipsec]** Delhi--CloudVPC runs over the internet, so traffic between DELHI-R1 and CLOUDVPC-VGW is encrypted in a route-based IPsec tunnel (VTI, AES-256 / SHA-256, DH group 14). Underlay addresses come from 203.0.113.0/24 (RFC 5737 documentation range): replace them with the real public IPs. _(ref: RFC 4301; RFC 5737)_
- **[ROUTE.area]** Area 0 (Delhi) is OSPF area 0 with address block 10.100.0.0/21. _(ref: RFC 2328)_
- **[ROUTE.area]** Area 1 (Mumbai) is OSPF area 1 with address block 10.100.8.0/22. _(ref: RFC 2328)_
- **[ROUTE.area]** Area 2 (Bengaluru) is OSPF area 2 with address block 10.100.12.0/22. _(ref: RFC 2328)_
- **[ROUTE.area]** Area 3 (Singapore) is OSPF area 3 with address block 10.100.16.0/22. _(ref: RFC 2328)_
- **[ROUTE.rid]** Router IDs come from Loopback0 /32 addresses. A loopback never goes down with a physical interface, so OSPF and BGP identities stay stable. _(ref: RFC 2328)_
- **[ROUTE.ref_bw]** OSPF reference bandwidth is 100000 Mbps. With the default 100 Mbps every link of 100 Mb/s or more gets cost 1, so 10G and 1G paths would look equal. _(ref: RFC 2328 (interface cost))_
- **[ROUTE.summary]** ABR MUMBAI-R1 summarizes area 1 as 10.100.8.0/22 (1 route instead of 4), which works because the area's subnets were allocated from one contiguous block. _(ref: RFC 2328; RFC 4632)_
- **[ROUTE.summary]** ABR BENGALURU-R1 summarizes area 2 as 10.100.12.0/22 (1 route instead of 4), which works because the area's subnets were allocated from one contiguous block. _(ref: RFC 2328; RFC 4632)_
- **[ROUTE.summary]** ABR SINGAPORE-R1 summarizes area 3 as 10.100.16.0/22 (1 route instead of 4), which works because the area's subnets were allocated from one contiguous block. _(ref: RFC 2328; RFC 4632)_
- **[ROUTE.bgp_anchor]** DELHI-R1 anchors its 4 BGP-advertised area block(s) with Null0 static routes at administrative distance 254 (floating). BGP `network` needs an exact route in the RIB, but an AD-1 static would beat the OSPF summary for the same prefix and blackhole remote areas; at AD 254 the static is used only when OSPF has no route. _(ref: RFC 4271; Cisco IOS administrative distance)_
- **[ROUTE.ebgp]** eBGP between DELHI-R1 (AS 65000) and CLOUDVPC-VGW (AS 65100) because the cloud VPC is a separate administrative domain. BGP keeps policy control at the boundary and OSPF is not extended into the provider. Both ASNs are private (RFC 6996). _(ref: RFC 4271; RFC 6996)_

### VLSM
- **[VLSM.block]** Area 0 (Delhi) gets the contiguous block 10.100.0.0/21 (2048 addresses) so all of its subnets can be summarized as one route. _(ref: RFC 4632)_
- **[VLSM.block]** Area 1 (Mumbai) gets the contiguous block 10.100.8.0/22 (1024 addresses) so all of its subnets can be summarized as one route. _(ref: RFC 4632)_
- **[VLSM.block]** Area 2 (Bengaluru) gets the contiguous block 10.100.12.0/22 (1024 addresses) so all of its subnets can be summarized as one route. _(ref: RFC 4632)_
- **[VLSM.block]** Area 3 (Singapore) gets the contiguous block 10.100.16.0/22 (1024 addresses) so all of its subnets can be summarized as one route. _(ref: RFC 4632)_
- **[VLSM.block]** Cloud CloudVPC gets the contiguous block 10.100.20.0/23 (512 addresses) so all of its subnets can be summarized as one route. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 5632 of 65536 addresses in 10.100.0.0/16 (8.59% of the root used). 5632 addresses were actually needed, so packing efficiency is 100.0% (0 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.subnet]** Delhi-IoT: 600 hosts + 1 gateway need 601 usable addresses; the smallest block is /22 (2^10 − 2 = 1022 usable), giving 58.81% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.p2p]** DELHI-R1 Tunnel1--SINGAPORE-R1 Tunnel1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** DELHI-R1 Tunnel2--CLOUDVPC-VGW Tunnel1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** DELHI-R1--BENGALURU-R1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** DELHI-R1--DELHI-CORE1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** DELHI-R1--MUMBAI-R1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.loopback]** DELHI-CORE1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** DELHI-R1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 1036 of 2048 addresses in 10.100.0.0/21 (50.59% of the root used). 613 addresses were actually needed, so packing efficiency is 59.17% (423 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.subnet]** Mumbai-IoT: 500 hosts + 1 gateway need 501 usable addresses; the smallest block is /23 (2^9 − 2 = 510 usable), giving 98.24% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.p2p]** MUMBAI-R1--MUMBAI-CORE1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.loopback]** MUMBAI-CORE1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** MUMBAI-R1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 516 of 1024 addresses in 10.100.8.0/22 (50.39% of the root used). 505 addresses were actually needed, so packing efficiency is 97.87% (11 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.subnet]** Blr-IoT: 500 hosts + 1 gateway need 501 usable addresses; the smallest block is /23 (2^9 − 2 = 510 usable), giving 98.24% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.p2p]** BENGALURU-R1--BENGALURU-CORE1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.loopback]** BENGALURU-CORE1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** BENGALURU-R1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 516 of 1024 addresses in 10.100.12.0/22 (50.39% of the root used). 505 addresses were actually needed, so packing efficiency is 97.87% (11 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.subnet]** Sg-IoT: 400 hosts + 1 gateway need 401 usable addresses; the smallest block is /23 (2^9 − 2 = 510 usable), giving 78.63% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.p2p]** SINGAPORE-R1--SINGAPORE-CORE1: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.loopback]** SINGAPORE-CORE1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.loopback]** SINGAPORE-R1 Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 516 of 1024 addresses in 10.100.16.0/22 (50.39% of the root used). 405 addresses were actually needed, so packing efficiency is 78.49% (111 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.subnet]** VPC-Apps: 200 hosts + 1 gateway need 201 usable addresses; the smallest block is /24 (2^8 − 2 = 254 usable), giving 79.13% utilization. _(ref: RFC 950, RFC 1878)_
- **[VLSM.loopback]** CLOUDVPC-VGW Loopback0: loopback gets a /32, a single stable address used as the router ID. _(ref: RFC 4632)_
- **[VLSM.efficiency]** Allocated 257 of 512 addresses in 10.100.20.0/23 (50.2% of the root used). 202 addresses were actually needed, so packing efficiency is 78.6% (55 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_
- **[VLSM.p2p]** DELHI-R1--CLOUDVPC-VGW underlay: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.p2p]** DELHI-R1--SINGAPORE-R1 underlay: point-to-point link gets a /31 (RFC 3021): both addresses are usable, so no network/broadcast addresses are wasted as a /30 would. _(ref: RFC 3021)_
- **[VLSM.efficiency]** Allocated 4 of 256 addresses in 203.0.113.0/24 (1.56% of the root used). 4 addresses were actually needed, so packing efficiency is 100.0% (0 addresses lost to power-of-two rounding). Blocks were allocated largest-first, so each block starts on its natural boundary and none overlap. _(ref: RFC 1878, RFC 4632)_

### ACL
- **[ACL.policy]** Sg-IoT → VPC-Apps: permit tcp port 8883 via ACL-SG-IOT-IN, applied inbound on the Sg-IoT gateway so the decision is made at the first layer-3 hop. _(ref: Cisco IOS extended ACL (first match))_
- **[ACL.policy]** Sg-IoT → VPC-Apps: deny ip via ACL-SG-IOT-IN, applied inbound on the Sg-IoT gateway so the decision is made at the first layer-3 hop. _(ref: Cisco IOS extended ACL (first match))_
- **[ACL.default]** ACL-SG-IOT-IN ends with 'permit ip any any' so traffic not covered by a policy is allowed; otherwise the IOS implicit deny would drop all other traffic from Sg-IoT. _(ref: Cisco IOS extended ACL (implicit deny))_

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
| DELHI-CORE1 | 84 | SEC-09 OSPF runs without authentication | medium | router ospf 1 | area <n> authentication message-digest + keys |
| DELHI-CORE1 | 84 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| DELHI-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| DELHI-ACC2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| DELHI-R1 | 84 | SEC-09 OSPF runs without authentication | medium | router ospf 1 | area <n> authentication message-digest + keys |
| DELHI-R1 | 84 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| MUMBAI-CORE1 | 84 | SEC-09 OSPF runs without authentication | medium | router ospf 1 | area <n> authentication message-digest + keys |
| MUMBAI-CORE1 | 84 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| MUMBAI-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| MUMBAI-ACC2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| MUMBAI-R1 | 84 | SEC-09 OSPF runs without authentication | medium | router ospf 1 | area <n> authentication message-digest + keys |
| MUMBAI-R1 | 84 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BENGALURU-CORE1 | 84 | SEC-09 OSPF runs without authentication | medium | router ospf 1 | area <n> authentication message-digest + keys |
| BENGALURU-CORE1 | 84 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BENGALURU-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BENGALURU-ACC2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| BENGALURU-R1 | 84 | SEC-09 OSPF runs without authentication | medium | router ospf 1 | area <n> authentication message-digest + keys |
| BENGALURU-R1 | 84 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| SINGAPORE-CORE1 | 84 | SEC-09 OSPF runs without authentication | medium | router ospf 1 | area <n> authentication message-digest + keys |
| SINGAPORE-CORE1 | 84 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| SINGAPORE-CORE1 | 84 | SEC-12 ACL ends with 'permit ip any any' | info | ip access-list ACL-SG-IOT-IN | intended for default-allow policies (D-020) |
| SINGAPORE-ACC1 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| SINGAPORE-ACC2 | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| SINGAPORE-R1 | 84 | SEC-09 OSPF runs without authentication | medium | router ospf 1 | area <n> authentication message-digest + keys |
| SINGAPORE-R1 | 84 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |
| CLOUDVPC-VGW | 92 | SEC-11 Placeholder secrets (CHANGE_ME) present | medium | global | replace every CHANGE_ME value |

## Single points of failure

- DELHI-CORE1 is a single point of failure: removing it separates 2 segment-hosting device(s) (DELHI-ACC1, DELHI-ACC2) from the rest of the network.
- DELHI-R1 is a single point of failure: removing it separates 7 segment-hosting device(s) (CLOUDVPC-VGW, DELHI-ACC1, DELHI-ACC2) from the rest of the network.
- MUMBAI-CORE1 is a single point of failure: removing it separates 2 segment-hosting device(s) (MUMBAI-ACC1, MUMBAI-ACC2) from the rest of the network.
- MUMBAI-R1 is a single point of failure: removing it separates 2 segment-hosting device(s) (MUMBAI-ACC1, MUMBAI-ACC2) from the rest of the network.
- BENGALURU-CORE1 is a single point of failure: removing it separates 8 segment-hosting device(s) (BENGALURU-ACC2, CLOUDVPC-VGW, DELHI-ACC1) from the rest of the network.
- BENGALURU-R1 is a single point of failure: removing it separates 7 segment-hosting device(s) (CLOUDVPC-VGW, DELHI-ACC1, DELHI-ACC2) from the rest of the network.
- SINGAPORE-CORE1 is a single point of failure: removing it separates 2 segment-hosting device(s) (SINGAPORE-ACC1, SINGAPORE-ACC2) from the rest of the network.
- SINGAPORE-R1 is a single point of failure: removing it separates 2 segment-hosting device(s) (SINGAPORE-ACC1, SINGAPORE-ACC2) from the rest of the network.
- DELHI-ACC1:TenGigabitEthernet1/1/1--DELHI-CORE1:TenGigabitEthernet1/0/1 is a single point of failure: removing it separates 1 segment-hosting device(s) (DELHI-ACC1) from the rest of the network.
- DELHI-ACC2:TenGigabitEthernet1/1/1--DELHI-CORE1:TenGigabitEthernet1/0/2 is a single point of failure: removing it separates 1 segment-hosting device(s) (DELHI-ACC2) from the rest of the network.
- DELHI-R1:TenGigabitEthernet0/0/0--DELHI-CORE1:TenGigabitEthernet1/0/3 is a single point of failure: removing it separates 2 segment-hosting device(s) (DELHI-ACC1, DELHI-ACC2) from the rest of the network.
- MUMBAI-ACC1:TenGigabitEthernet1/1/1--MUMBAI-CORE1:TenGigabitEthernet1/0/1 is a single point of failure: removing it separates 1 segment-hosting device(s) (MUMBAI-ACC1) from the rest of the network.
- MUMBAI-ACC2:TenGigabitEthernet1/1/1--MUMBAI-CORE1:TenGigabitEthernet1/0/2 is a single point of failure: removing it separates 1 segment-hosting device(s) (MUMBAI-ACC2) from the rest of the network.
- MUMBAI-R1:TenGigabitEthernet0/0/0--MUMBAI-CORE1:TenGigabitEthernet1/0/3 is a single point of failure: removing it separates 2 segment-hosting device(s) (MUMBAI-ACC1, MUMBAI-ACC2) from the rest of the network.
- BENGALURU-ACC1:TenGigabitEthernet1/1/1--BENGALURU-CORE1:TenGigabitEthernet1/0/1 is a single point of failure: removing it separates 8 segment-hosting device(s) (BENGALURU-ACC2, CLOUDVPC-VGW, DELHI-ACC1) from the rest of the network.
- BENGALURU-ACC2:TenGigabitEthernet1/1/1--BENGALURU-CORE1:TenGigabitEthernet1/0/2 is a single point of failure: removing it separates 1 segment-hosting device(s) (BENGALURU-ACC2) from the rest of the network.
- BENGALURU-R1:TenGigabitEthernet0/0/0--BENGALURU-CORE1:TenGigabitEthernet1/0/3 is a single point of failure: removing it separates 7 segment-hosting device(s) (CLOUDVPC-VGW, DELHI-ACC1, DELHI-ACC2) from the rest of the network.
- SINGAPORE-ACC1:TenGigabitEthernet1/1/1--SINGAPORE-CORE1:TenGigabitEthernet1/0/1 is a single point of failure: removing it separates 1 segment-hosting device(s) (SINGAPORE-ACC1) from the rest of the network.
- SINGAPORE-ACC2:TenGigabitEthernet1/1/1--SINGAPORE-CORE1:TenGigabitEthernet1/0/2 is a single point of failure: removing it separates 1 segment-hosting device(s) (SINGAPORE-ACC2) from the rest of the network.
- SINGAPORE-R1:TenGigabitEthernet0/0/0--SINGAPORE-CORE1:TenGigabitEthernet1/0/3 is a single point of failure: removing it separates 2 segment-hosting device(s) (SINGAPORE-ACC1, SINGAPORE-ACC2) from the rest of the network.
- DELHI-R1:TenGigabitEthernet0/0/1--MUMBAI-R1:TenGigabitEthernet0/0/1 is a single point of failure: removing it separates 2 segment-hosting device(s) (MUMBAI-ACC1, MUMBAI-ACC2) from the rest of the network.
- DELHI-R1:TenGigabitEthernet0/0/2--BENGALURU-R1:TenGigabitEthernet0/0/1 is a single point of failure: removing it separates 7 segment-hosting device(s) (CLOUDVPC-VGW, DELHI-ACC1, DELHI-ACC2) from the rest of the network.
- DELHI-R1:TenGigabitEthernet0/0/3--SINGAPORE-R1:TenGigabitEthernet0/0/1 is a single point of failure: removing it separates 2 segment-hosting device(s) (SINGAPORE-ACC1, SINGAPORE-ACC2) from the rest of the network.
- DELHI-R1:TenGigabitEthernet0/0/4--CLOUDVPC-VGW:TenGigabitEthernet0/0/1 is a single point of failure: removing it separates 1 segment-hosting device(s) (CLOUDVPC-VGW) from the rest of the network.
- Resilience score 4/100: 24 of 25 infrastructure elements (non-access devices and cables) are single points of failure. Access stacks are excluded because users on a stack always depend on it.

## Bill of materials

_PLACEHOLDER ESTIMATES in INR, not quotes. Owner must replace with real vendor prices before using totals. Units: per item unless stated._

| Item | Qty | Unit | Unit price | Total | Because of |
|---|---|---|---|---|---|
| Cat6a patch cord (in-building) | 12 | pcs | 600 | 7,200 | L1.in_building |
| 48-port access switch | 44 | pcs | 220,000 | 9,680,000 | TOPO.access |
| Core switch | 4 | pcs | 900,000 | 3,600,000 | TOPO.collapsed_core |
| Router | 4 | pcs | 500,000 | 2,000,000 | ROUTE.ospf_multi_site |
| Cloud virtual gateway | 1 | pcs | 0 | 0 | ROUTE.ebgp |
| Carrier circuit (monthly) | 2 | circuit/month | 60,000 | 120,000 | L1.provider |
| Internet circuit (monthly) | 2 | circuit/month | 15,000 | 30,000 | L1.provider |
