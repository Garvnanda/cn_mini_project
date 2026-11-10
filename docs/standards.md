# Standards Reference — the only allowed source of networking numbers

Rule: code constants and rationale text must use values from this file. Values marked **[verify]** must be checked against a primary source (IEEE/TIA/RFC text or vendor datasheet) and the marker removed before use in final output.

## Physical media (L1)
| Item | Value | Source |
|---|---|---|
| 10GBASE-T max reach on Cat6a | 100 m | IEEE 802.3an-2006 |
| 10GBASE-T reach on Cat6 | 55 m | IEEE 802.3an-2006 |
| 10GBASE-SR on OM3 (850 nm) | 300 m | IEEE 802.3ae |
| 10GBASE-SR on OM4 (850 nm) | 400 m | IEEE 802.3ae / TIA-492AAAD |
| 10GBASE-LR on OS2 (1310 nm) | 10 km | IEEE 802.3ae |
| 10GBASE-ER on OS2 (1550 nm) | 40 km | IEEE 802.3ae |
| Spec rule: copper ≤100 m, OM4 101–400 m, OS2 >400 m | — | Assignment PDF §3 |

### Loss figures for optical budget
| Item | Value | Source |
|---|---|---|
| MMF attenuation @850 nm (max) | 3.5 dB/km | TIA-568 |
| OS2 attenuation @1310 nm (typical) | 0.4 dB/km [verify] | vendor typical |
| OS2 attenuation @1550 nm (typical) | 0.25 dB/km [verify] | vendor typical (changed from 0.3, see D-012) |
| Mated connector pair loss (max) | 0.75 dB | TIA-568 |
| Fusion splice loss (max) | 0.3 dB | TIA-568 |
| Low-margin warning threshold | 3 dB | project choice (D-012): warns, does not fail |
| 10GBASE-SR max channel insertion loss (OM4, 400 m) | 2.9 dB [verify] | IEEE 802.3ae / vendor |
| 10GBASE-LR max channel insertion loss | 6.2 dB [verify] | IEEE 802.3ae |
| 10GBASE-ER max channel insertion loss | 11.0 dB [verify] | IEEE 802.3ae |

Budget rule: total loss (fiber + connectors + splices) must be ≤ channel insertion loss.
Consequence with current values: ER passes up to 38 km with 2 connectors; 40 km fails (11.5 dB). Revisit after verifying.

## PoE
| Standard | Power at PSE port | Source |
|---|---|---|
| 802.3af (Type 1) | 15.4 W | IEEE 802.3af |
| 802.3at (Type 2, PoE+) | 30 W | IEEE 802.3at |
| 802.3bt Type 3 | 60 W | IEEE 802.3bt |
| 802.3bt Type 4 | 90 W | IEEE 802.3bt |

## L2
| Item | Value / Ref |
|---|---|
| VLAN tagging | IEEE 802.1Q |
| Usable VLAN IDs | 1–4094 (0 and 4095 reserved) |
| Rapid Spanning Tree | IEEE 802.1w (merged into 802.1D-2004) |

## L3 addressing
| Item | Ref |
|---|---|
| Subnetting | RFC 950 |
| VLSM examples | RFC 1878 |
| CIDR | RFC 4632 |
| Private address space (10/8, 172.16/12, 192.168/16) | RFC 1918 |
| /31 point-to-point links | RFC 3021 |
| Usable hosts per prefix p (p ≤ 30) | 2^(32−p) − 2 |

## Routing
| Item | Value / Ref |
|---|---|
| OSPFv2 | RFC 2328 |
| OSPF hello / dead (broadcast & P2P) | 10 s / 40 s (RFC 2328 defaults, Cisco default) |
| Cisco OSPF auto-cost reference bandwidth (default) | 100 Mbps |
| BGP-4 | RFC 4271 |
| Private 16-bit ASNs | 64512–65534 (RFC 6996) |
| Cisco AD: connected / static / eBGP / OSPF / iBGP | 0 / 1 / 20 / 110 / 200 |

## Security / VPN
| Item | Ref |
|---|---|
| IPsec architecture | RFC 4301 |
| IKEv2 | RFC 7296 |
| ESP | RFC 4303 |

## Simulator assumptions (Phase 11)
| Item | Value | Source |
|---|---|---|
| Interface bandwidth for OSPF cost: TenGigabitEthernet | 10000 Mb/s | interface speed |
| GigabitEthernet / Vlan SVI | 1000 Mb/s [verify SVI default per platform] | Cisco default |
| Tunnel interface | 0.1 Mb/s (100 kb/s) [verify per IOS version] | Cisco default |
| OSPF cost | ref_bw / bw, min 1, max 65535; loopback 1 | RFC 2328 / Cisco |
| Floating static AD for BGP anchors | 254 | project choice (D-021) |

## Other references used (Phases 5-8)
| Item | Ref |
|---|---|
| HSRP (Cisco Hot Standby Router Protocol) | RFC 2281 |
| Documentation address ranges (203.0.113.0/24 used as stand-in public IPs) | RFC 5737 |
| IKEv1 policy used: AES-256, SHA-256, DH group 14, PSK | Cisco IOS crypto docs [verify per platform] |
| OSPF area summarization on ABR | RFC 2328 |

## Project thresholds (from assignment, not standards)
| Rule | Value | Source |
|---|---|---|
| Single-area OSPF limit | < 50 subnets in one AS | Assignment §3 |
| Multi-site / multi-cloud | Multi-area OSPF or eBGP | Assignment §3 |
| Three-tier when a site has | ≥ 4 buildings | project choice (D-017) |
| Access switch ports | 48 per member | project choice |
| Stack members | ≤ 8 per stack | project choice [verify per platform] |
| PoE per AP port assumed | 30 W (802.3at) | project choice using IEEE value |
| OSPF reference bandwidth | 100000 Mbps | project choice (D-016 context) |
| Native / parking VLAN | 999 (or highest free) | project choice |
| HSRP priorities | 110 active / 100 standby (IOS default) | project choice |
| Enterprise / cloud ASN | 65000 / 65100+ | RFC 6996 range |
