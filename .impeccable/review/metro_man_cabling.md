# Cabling Guide

| # | Device A | Port A | Device B | Port B | Kind | Media | Transceiver | Length |
|---|---|---|---|---|---|---|---|---|
| 1 | HQ-CORE1 | TenGigabitEthernet1/0/1 | HQ-CORE2 | TenGigabitEthernet1/0/1 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 2 | HQ-CORE1 | TenGigabitEthernet1/0/2 | HQ-CORE2 | TenGigabitEthernet1/0/2 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 3 | HQ-ACC1 | TenGigabitEthernet1/1/1 | HQ-CORE1 | TenGigabitEthernet1/0/3 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 4 | HQ-ACC1 | TenGigabitEthernet1/1/2 | HQ-CORE2 | TenGigabitEthernet1/0/3 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 5 | HQ-R1 | TenGigabitEthernet0/0/0 | HQ-CORE1 | TenGigabitEthernet1/0/4 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 6 | HQ-R2 | TenGigabitEthernet0/0/0 | HQ-CORE2 | TenGigabitEthernet1/0/4 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 7 | BRANCH-CORE1 | TenGigabitEthernet1/0/1 | BRANCH-CORE2 | TenGigabitEthernet1/0/1 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 8 | BRANCH-CORE1 | TenGigabitEthernet1/0/2 | BRANCH-CORE2 | TenGigabitEthernet1/0/2 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 9 | BRANCH-ACC1 | TenGigabitEthernet1/1/1 | BRANCH-CORE1 | TenGigabitEthernet1/0/3 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 10 | BRANCH-ACC1 | TenGigabitEthernet1/1/2 | BRANCH-CORE2 | TenGigabitEthernet1/0/3 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 11 | BRANCH-R1 | TenGigabitEthernet0/0/0 | BRANCH-CORE1 | TenGigabitEthernet1/0/4 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 12 | BRANCH-R1 | TenGigabitEthernet0/0/1 | BRANCH-CORE2 | TenGigabitEthernet1/0/4 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 13 | COLO-CORE1 | TenGigabitEthernet1/0/1 | COLO-CORE2 | TenGigabitEthernet1/0/1 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 14 | COLO-CORE1 | TenGigabitEthernet1/0/2 | COLO-CORE2 | TenGigabitEthernet1/0/2 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 15 | COLO-ACC1 | TenGigabitEthernet1/1/1 | COLO-CORE1 | TenGigabitEthernet1/0/3 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 16 | COLO-ACC1 | TenGigabitEthernet1/1/2 | COLO-CORE2 | TenGigabitEthernet1/0/3 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 17 | COLO-R1 | TenGigabitEthernet0/0/0 | COLO-CORE1 | TenGigabitEthernet1/0/4 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 18 | COLO-R2 | TenGigabitEthernet0/0/0 | COLO-CORE2 | TenGigabitEthernet1/0/4 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 19 | HQ-R1 | TenGigabitEthernet0/0/1 | BRANCH-R1 | TenGigabitEthernet0/0/2 | routed | OS2 single-mode fiber | 10GBASE-ER | 22000 m |
| 20 | HQ-R2 | TenGigabitEthernet0/0/1 | BRANCH-R1 | TenGigabitEthernet0/0/3 | routed | OS2 single-mode fiber | 10GBASE-ER | 22000 m |
| 21 | HQ-R1 | TenGigabitEthernet0/0/2 | COLO-R1 | TenGigabitEthernet0/0/1 | routed | OS2 single-mode fiber | 10GBASE-ER | 35000 m |
| 22 | HQ-R2 | TenGigabitEthernet0/0/2 | COLO-R2 | TenGigabitEthernet0/0/1 | routed | OS2 single-mode fiber | 10GBASE-ER | 35000 m |
