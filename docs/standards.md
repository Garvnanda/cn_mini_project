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
| OS2 attenuation @1550 nm (typical) | 0.3 dB/km [verify] | vendor typical |
| Mated connector pair loss (max) | 0.75 dB | TIA-568 |
| Fusion splice loss (max) | 0.3 dB | TIA-568 |
| Design safety margin | 3 dB | project choice (docs/decisions.md) |
| SFP+ LR power budget | [verify from datasheet] | vendor datasheet |
| SFP+ ER power budget | [verify from datasheet] | vendor datasheet |

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

## Project thresholds (from assignment, not standards)
| Rule | Value |
|---|---|
| Single-area OSPF limit | < 50 subnets in one AS |
| Multi-site / multi-cloud | Multi-area OSPF or eBGP |
