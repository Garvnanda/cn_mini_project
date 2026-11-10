# Cabling Guide

| # | Device A | Port A | Device B | Port B | Kind | Media | Transceiver | Length |
|---|---|---|---|---|---|---|---|---|
| 1 | CAMPUS-CORE1 | TenGigabitEthernet1/0/1 | CAMPUS-CORE2 | TenGigabitEthernet1/0/1 | routed | Cat6a UTP | 10GBASE-T | in-building patch |
| 2 | CAMPUS-CORE1 | TenGigabitEthernet1/0/2 | CAMPUS-CORE2 | TenGigabitEthernet1/0/2 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 3 | BLDGA-ACC1 | TenGigabitEthernet1/1/1 | CAMPUS-CORE1 | TenGigabitEthernet1/0/3 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 4 | BLDGA-ACC1 | TenGigabitEthernet1/1/2 | CAMPUS-CORE2 | TenGigabitEthernet1/0/3 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 5 | BLDGA-ACC2 | TenGigabitEthernet1/1/1 | CAMPUS-CORE1 | TenGigabitEthernet1/0/4 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 6 | BLDGA-ACC2 | TenGigabitEthernet1/1/2 | CAMPUS-CORE2 | TenGigabitEthernet1/0/4 | trunk | Cat6a UTP | 10GBASE-T | in-building patch |
| 7 | BLDGB-ACC1 | TenGigabitEthernet1/1/1 | CAMPUS-CORE1 | TenGigabitEthernet1/0/5 | trunk | OM4 multimode fiber | 10GBASE-SR | 180 m |
| 8 | BLDGB-ACC1 | TenGigabitEthernet1/1/2 | CAMPUS-CORE2 | TenGigabitEthernet1/0/5 | trunk | OM4 multimode fiber | 10GBASE-SR | 180 m |
| 9 | BLDGB-ACC2 | TenGigabitEthernet1/1/1 | CAMPUS-CORE1 | TenGigabitEthernet1/0/6 | trunk | OM4 multimode fiber | 10GBASE-SR | 180 m |
| 10 | BLDGB-ACC2 | TenGigabitEthernet1/1/2 | CAMPUS-CORE2 | TenGigabitEthernet1/0/6 | trunk | OM4 multimode fiber | 10GBASE-SR | 180 m |
| 11 | BLDGC-ACC1 | TenGigabitEthernet1/1/1 | CAMPUS-CORE1 | TenGigabitEthernet1/0/7 | trunk | OM4 multimode fiber | 10GBASE-SR | 350 m |
| 12 | BLDGC-ACC1 | TenGigabitEthernet1/1/2 | CAMPUS-CORE2 | TenGigabitEthernet1/0/7 | trunk | OM4 multimode fiber | 10GBASE-SR | 350 m |
| 13 | BLDGC-ACC2 | TenGigabitEthernet1/1/1 | CAMPUS-CORE1 | TenGigabitEthernet1/0/8 | trunk | OM4 multimode fiber | 10GBASE-SR | 350 m |
| 14 | BLDGC-ACC2 | TenGigabitEthernet1/1/2 | CAMPUS-CORE2 | TenGigabitEthernet1/0/8 | trunk | OM4 multimode fiber | 10GBASE-SR | 350 m |
