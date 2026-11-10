# Verification proof (owner)

Put screenshots here after loading the preset exports into Packet Tracer or GNS3 (task 26.3):

1. `exports/<preset>/cabling_guide.md` gives the port-to-port cabling.
2. Paste each `exports/<preset>/<DEVICE>.cfg` into the matching device.
3. Capture: `show ip ospf neighbor`, `show ip route`, `show standby brief`, a successful `ping` between segments, and a denied flow (e.g. Guest -> Servers on campus_lan).

Known Packet Tracer gaps to check (docs/ios_reference.md, "?" rows): HSRPv2, IPsec VTI, QoS (MQC), `crypto key generate rsa modulus 2048`, and 3560-class switches needing `switchport trunk encapsulation dot1q`.
