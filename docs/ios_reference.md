# Cisco IOS Command Reference — allowed commands only

Rule: templates may only emit commands listed here. `tests/test_configs.py::test_only_documented_commands` parses every generated config and fails on any line whose command prefix is not in this table.
How the test reads this file: every backticked command in a table row is one allowed form. The prefix before the first `<` or `[` is matched against the config line; `a\|b` in the prefix means either word.
Add a command only after confirming its exact syntax (Cisco docs or tested in Packet Tracer/GNS3). Fill "Verified in" when tested.
PT = Cisco Packet Tracer support; "?" = not yet checked.

| Context | Command syntax | Purpose | PT | Verified in |
|---|---|---|---|---|
| global | `hostname <NAME>` | device name | yes | |
| global | `service password-encryption` | encrypt type-7 passwords | yes | |
| global | `no ip domain-lookup` | stop DNS lookup on typos | yes | |
| global | `ip domain-name <domain>` | needed for RSA keys | yes | |
| global | `enable secret <secret>` | privileged password (hashed) | yes | |
| global | `username <name> privilege 15 secret <secret>` | local admin account | yes | |
| global | `crypto key generate rsa modulus 2048` | SSH keys | ? | |
| global | `ip ssh version 2` | SSHv2 only | yes | |
| global | `banner motd ^<text>^` | login banner | yes | |
| global | `ip routing` | enable L3 on switch | yes | |
| global | `vlan <id>` / `name <NAME>` | create VLAN | yes | |
| global | `spanning-tree mode rapid-pvst` | RSTP | yes | |
| global | `spanning-tree vlan <list> root primary\|secondary` | root bridge | yes | |
| global | `interface <name>` | enter interface (physical, Vlan, Loopback, Tunnel) | yes | |
| global | `interface range <spec>` | enter several ports at once | yes | |
| interface | `description <text>` | label | yes | |
| interface | `switchport mode access` | access port | yes | |
| interface | `switchport access vlan <id>` | access VLAN | yes | |
| interface | `switchport mode trunk` | trunk | yes | |
| interface | `switchport trunk native vlan <id>` | native VLAN | yes | |
| interface | `switchport trunk allowed vlan <list>` | prune trunk | yes | |
| interface | `spanning-tree portfast` | edge port | yes | |
| interface | `spanning-tree bpduguard enable` | BPDU guard | yes | |
| interface | `no switchport` | make a switch port routed | yes | |
| interface | `ip address <ip> <mask>` | L3 address | yes | |
| interface | `no shutdown` / `shutdown` | admin state | yes | |
| interface | `standby version 2` | HSRPv2 (groups 0-4095) | ? | |
| interface | `standby <grp> ip <vip>` | HSRP virtual IP | yes | |
| interface | `standby <grp> priority <n>` | HSRP priority | yes | |
| interface | `standby <grp> preempt` | reclaim active role | yes | |
| interface | `ip access-group <NAME> in\|out` | apply ACL | yes | |
| interface | `tunnel source <if>` | tunnel underlay source | yes | |
| interface | `tunnel destination <ip>` | tunnel peer | yes | |
| interface | `tunnel mode ipsec ipv4` | route-based IPsec VTI | ? | |
| interface | `tunnel protection ipsec profile <NAME>` | bind IPsec profile | ? | |
| global | `router ospf <pid>` | OSPF process | yes | |
| ospf | `router-id <a.b.c.d>` | RID | yes | |
| ospf | `auto-cost reference-bandwidth <mbps>` | cost scaling | yes | |
| ospf | `passive-interface <if>` | no hellos to hosts | yes | |
| ospf | `network <ip> <wildcard> area <n>` | OSPF enable | yes | |
| ospf | `area <n> range <net> <mask>` | ABR summary | yes | |
| ospf | `redistribute bgp <asn> subnets` | import BGP routes | yes | |
| global | `router bgp <asn>` | BGP process | yes | |
| bgp | `bgp router-id <a.b.c.d>` | BGP RID | yes | |
| bgp | `neighbor <ip> remote-as <asn>` | peer | yes | |
| bgp | `network <net> mask <mask>` | advertise (needs exact RIB route) | yes | |
| global | `ip route <net> <mask> <next-hop\|Null0> [<distance>]` | static / discard route; distance makes it floating | yes | |
| global | `ip access-list extended <NAME>` | named ACL | yes | |
| acl | `permit\|deny <proto> <src> <wc> <dst> <wc> [eq <port>]` | ACE (`any` allowed for src/dst) | yes | |
| global | `crypto isakmp policy <n>` | IKEv1 phase 1 policy | yes | |
| isakmp | `encryption aes 256` | phase 1 cipher | yes | |
| isakmp | `hash sha256` | phase 1 integrity | ? | |
| isakmp | `authentication pre-share` | PSK auth | yes | |
| isakmp | `group 14` | DH 2048-bit | ? | |
| isakmp | `lifetime <sec>` | SA lifetime | yes | |
| global | `crypto isakmp key <psk> address <ip>` | PSK per peer | yes | |
| global | `crypto ipsec transform-set <NAME> esp-aes 256 esp-sha256-hmac` | phase 2 proposal | ? | |
| transform | `mode tunnel` | ESP tunnel mode | yes | |
| global | `crypto ipsec profile <NAME>` | profile for VTI | ? | |
| profile | `set transform-set <NAME>` | bind transform set | ? | |
| global | `line con 0` / `line vty 0 4` | console / remote lines | yes | |
| line | `logging synchronous` | clean console output | yes | |
| line | `login local` | use local users | yes | |
| line | `transport input ssh` | SSH only | yes | |
| global | `end` | leave config mode | yes | |

Known Packet Tracer gaps (to check in Phase 26): 3560/3650 in PT may need `switchport trunk encapsulation dot1q` before `switchport mode trunk`; IPsec VTI and HSRPv2 support in PT is unverified.
