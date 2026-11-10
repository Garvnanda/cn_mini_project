# Cabling Guide

| # | Device A | Port A | Device B | Port B | Kind | Media | Transceiver | Length |
|---|---|---|---|---|---|---|---|---|
| 1 | DELHI-ACC1 | TenGigabitEthernet1/1/1 | DELHI-CORE1 | TenGigabitEthernet1/0/1 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 2 | DELHI-ACC2 | TenGigabitEthernet1/1/1 | DELHI-CORE1 | TenGigabitEthernet1/0/2 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 3 | DELHI-R1 | TenGigabitEthernet0/0/0 | DELHI-CORE1 | TenGigabitEthernet1/0/3 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 4 | MUMBAI-ACC1 | TenGigabitEthernet1/1/1 | MUMBAI-CORE1 | TenGigabitEthernet1/0/1 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 5 | MUMBAI-ACC2 | TenGigabitEthernet1/1/1 | MUMBAI-CORE1 | TenGigabitEthernet1/0/2 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 6 | MUMBAI-R1 | TenGigabitEthernet0/0/0 | MUMBAI-CORE1 | TenGigabitEthernet1/0/3 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 7 | BENGALURU-ACC1 | TenGigabitEthernet1/1/1 | BENGALURU-CORE1 | TenGigabitEthernet1/0/1 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 8 | BENGALURU-ACC2 | TenGigabitEthernet1/1/1 | BENGALURU-CORE1 | TenGigabitEthernet1/0/2 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 9 | BENGALURU-R1 | TenGigabitEthernet0/0/0 | BENGALURU-CORE1 | TenGigabitEthernet1/0/3 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 10 | SINGAPORE-ACC1 | TenGigabitEthernet1/1/1 | SINGAPORE-CORE1 | TenGigabitEthernet1/0/1 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 11 | SINGAPORE-ACC2 | TenGigabitEthernet1/1/1 | SINGAPORE-CORE1 | TenGigabitEthernet1/0/2 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 12 | SINGAPORE-R1 | TenGigabitEthernet0/0/0 | SINGAPORE-CORE1 | TenGigabitEthernet1/0/3 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 13 | DELHI-R1 | TenGigabitEthernet0/0/1 | MUMBAI-R1 | TenGigabitEthernet0/0/1 | routed | carrier handoff (Cat6a UTP) | 10GBASE-T | 1.15e+06 m |
| 14 | DELHI-R1 | TenGigabitEthernet0/0/2 | BENGALURU-R1 | TenGigabitEthernet0/0/1 | routed | carrier handoff (Cat6a UTP) | 10GBASE-T | 1.74e+06 m |
| 15 | DELHI-R1 | TenGigabitEthernet0/0/3 | SINGAPORE-R1 | TenGigabitEthernet0/0/1 | underlay | internet handoff (Cat6a UTP) | 10GBASE-T | 4.15e+06 m |
| 16 | DELHI-R1 | TenGigabitEthernet0/0/4 | CLOUDVPC-VGW | TenGigabitEthernet0/0/1 | underlay | internet handoff (Cat6a UTP) | 10GBASE-T | 1000 m |
