# Cisco IOS Command Reference — allowed commands only

Rule: templates may only emit commands listed here. A test parses generated configs and fails on unknown commands.
Add a command only after confirming its exact syntax (Cisco docs or tested in Packet Tracer/GNS3). Note where it was verified.
Note: Packet Tracer supports a subset of IOS; mark PT support per command.

| Context | Command syntax | Purpose | PT support | Verified in |
|---|---|---|---|---|
| global | `hostname <NAME>` | device name | yes | |
| global | `service password-encryption` | encrypt type-7 passwords | yes | |
| global | `no ip domain-lookup` | stop DNS lookup on typos | yes | |
| global | `ip domain-name <domain>` | needed for RSA keys | yes | |
| global | `crypto key generate rsa modulus 2048` | SSH keys | yes | |
| global | `ip ssh version 2` | SSHv2 only | yes | |
| global | `vlan <id>` / `name <NAME>` | create VLAN | yes | |
| global | `spanning-tree mode rapid-pvst` | RSTP | yes | |
| global | `spanning-tree vlan <list> root primary\|secondary` | root bridge | yes | |
| interface | `switchport mode access` | access port | yes | |
| interface | `switchport access vlan <id>` | access VLAN | yes | |
| interface | `switchport mode trunk` | trunk | yes | |
| interface | `switchport trunk native vlan <id>` | native VLAN | yes | |
| interface | `switchport trunk allowed vlan <list>` | prune trunk | yes | |
| interface | `spanning-tree portfast` | edge port | yes | |
| interface | `spanning-tree bpduguard enable` | BPDU guard | yes | |
| interface | `ip address <ip> <mask>` | L3 address | yes | |
| interface | `no shutdown` / `shutdown` | admin state | yes | |
| interface | `description <text>` | label | yes | |
| global | `interface vlan <id>` | SVI | yes | |
| global | `ip routing` | enable L3 on switch | yes | |
| global | `router ospf <pid>` | OSPF process | yes | |
| ospf | `router-id <a.b.c.d>` | RID | yes | |
| ospf | `network <net> <wildcard> area <n>` | OSPF enable | yes | |
| ospf | `area <n> range <net> <mask>` | ABR summary | yes | |
| ospf | `auto-cost reference-bandwidth <mbps>` | cost scaling | yes | |
| ospf | `passive-interface <if>` | no hellos to hosts | yes | |
| global | `router bgp <asn>` | BGP process | yes | |
| bgp | `neighbor <ip> remote-as <asn>` | peer | yes | |
| bgp | `network <net> mask <mask>` | advertise | yes | |
| global | `ip access-list extended <NAME>` | named ACL | yes | |
| acl | `permit\|deny <proto> <src> <wc> <dst> <wc> [eq <port>]` | ACE | yes | |
| interface | `ip access-group <NAME> in\|out` | apply ACL | yes | |
| global | `ip route <net> <mask> <next-hop>` | static | yes | |
| line | `line vty 0 4` / `transport input ssh` / `login local` | SSH only | yes | |

IPsec (crypto isakmp / crypto map) commands: to be added in Phase 8 after verification — PT support is limited, check first.
