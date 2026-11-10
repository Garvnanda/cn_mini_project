"""Networking constants. Every value must match docs/standards.md (CLAUDE.md rule 2.1)."""

# --- Reach limits (metres)
COPPER_MAX_M = 100        # 10GBASE-T on Cat6a, IEEE 802.3an-2006
OM4_MAX_M = 400           # 10GBASE-SR on OM4, IEEE 802.3ae
LR_MAX_M = 10_000         # 10GBASE-LR on OS2, IEEE 802.3ae
ER_MAX_M = 40_000         # 10GBASE-ER on OS2, IEEE 802.3ae
MAX_MODELLED_GBPS = 10    # only 10G transceivers are modelled
FIBER_US_PER_KM = 5.0     # propagation in glass, c / n with n ~ 1.47 (docs/standards.md [verify])

# --- Optical loss figures (dB)
MMF_850_DB_PER_KM = 3.5   # TIA-568 max
# UNVERIFIED: typical values, see docs/standards.md [verify]
OS2_1310_DB_PER_KM = 0.4
OS2_1550_DB_PER_KM = 0.25
CONNECTOR_DB = 0.75       # TIA-568 max per mated pair
SPLICE_DB = 0.3           # TIA-568 max per fusion splice
DEFAULT_CONNECTORS = 2    # one patch panel at each end
LOW_MARGIN_DB = 3.0       # below this margin the rationale warns (D-012)

# UNVERIFIED: IEEE 802.3ae max channel insertion loss, see docs/standards.md [verify]
CHANNEL_LOSS_DB = {
    "10GBASE-SR": 2.9,    # OM4 400 m (UNVERIFIED)
    "10GBASE-LR": 6.2,
    "10GBASE-ER": 11.0,
}

# --- Addressing
IPV4_BITS = 32
ALL_ONES = 0xFFFFFFFF

# --- Topology (project choices, docs/standards.md "Project thresholds")
ACCESS_PORTS_PER_MEMBER = 48      # 48-port access switch
STACK_MAX_MEMBERS = 8             # members per access stack (project choice)
THREE_TIER_MIN_BUILDINGS = 4      # >= this many buildings at a site -> three-tier
POE_WATTS_PER_PORT = 30.0         # 802.3at Type 2 (PoE+) per PSE port

# Interface naming (Catalyst 9300-style access, 9500-style core/dist, ISR/ASR-style router)
ACCESS_PORT = "GigabitEthernet{m}/0/{p}"
PORT_PATTERN = {  # role -> (pattern, first index)
    "access": ("TenGigabitEthernet1/1/{n}", 1),
    "core": ("TenGigabitEthernet1/0/{n}", 1),
    "distribution": ("TenGigabitEthernet1/0/{n}", 1),
    "router": ("TenGigabitEthernet0/0/{n}", 0),
    "cloud": ("TenGigabitEthernet0/0/{n}", 0),
}

# --- L2
NATIVE_VLAN_DEFAULT = 999         # unused VLAN for trunk native + parking unused ports
HSRP_ACTIVE_PRIORITY = 110
HSRP_STANDBY_PRIORITY = 100       # IOS default

# --- Routing
OSPF_PID = 1
OSPF_SINGLE_AREA_MAX_SUBNETS = 50  # assignment rule: single area when < 50 subnets
OSPF_DEFAULT_REF_BW_MBPS = 100     # Cisco default
OSPF_REF_BW_MBPS = 100_000         # 100 Gb/s so 10G links get cost 10, 1G cost 100
FLOATING_STATIC_AD = 254           # BGP anchor routes lose to any OSPF route for the same prefix
ENTERPRISE_ASN = 65000             # RFC 6996 private range
CLOUD_ASN_BASE = 65100
INTERNET_UNDERLAY = "203.0.113.0/24"  # RFC 5737 TEST-NET-3, stands in for public IPs
IPSEC_PSK = "CHANGE_ME_PSK"           # placeholder, must be replaced before deployment

# --- Timers (protocol defaults, docs/standards.md)
OSPF_HELLO_S = 10
OSPF_DEAD_S = 40
HSRP_HELLO_S = 3
HSRP_HOLD_S = 10
