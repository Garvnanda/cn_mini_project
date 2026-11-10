"""Hand-built mini topologies with known answers (Phase 11.6)."""

import pytest

from engine.models import Cable
from verify.ios_parser import PAclEntry, parse_config
from verify.simulator import Host, Simulator, ospf_cost

R1 = """hostname R1
interface Loopback0
 ip address 1.1.1.1 255.255.255.255
interface Gi0/0
 ip address 10.0.12.0 255.255.255.254
interface Gi0/1
 ip address 192.168.1.1 255.255.255.0
{acl_in}
{extra_if}
router ospf 1
 router-id 1.1.1.1
 network 1.1.1.1 0.0.0.0 area 0
 network 10.0.12.0 0.0.0.0 area 0
 network 192.168.1.1 0.0.0.0 area 0
{extra}
"""

R2 = """hostname R2
interface Loopback0
 ip address 2.2.2.2 255.255.255.255
interface Gi0/0
 ip address 10.0.12.1 255.255.255.254
interface Gi0/1
 ip address 192.168.2.1 255.255.255.0
{r2_ospf}
{extra}
"""

R2_OSPF = """router ospf 1
 router-id 2.2.2.2
 network 2.2.2.2 0.0.0.0 area 0
 network 10.0.12.1 0.0.0.0 area 0
 network 192.168.2.1 0.0.0.0 area 0
"""

ACL = """ip access-list extended BLOCK
 deny tcp 192.168.1.0 0.0.0.255 192.168.2.0 0.0.0.255 eq 22
 permit ip any any
"""

CABLES = [Cable(a="R1", a_if="Gi0/0", b="R2", b_if="Gi0/0", kind="routed")]
HOSTS = [
    Host(ip="192.168.1.10", mask="255.255.255.0", gateway="192.168.1.1", segment="LAN1"),
    Host(ip="192.168.2.10", mask="255.255.255.0", gateway="192.168.2.1", segment="LAN2"),
]


def sim(acl_in="", r2_ospf=R2_OSPF, r1_extra="", r2_extra="", extra_if="", acl=""):
    r1 = acl + R1.format(acl_in=acl_in, extra=r1_extra, extra_if=extra_if)
    r2 = R2.format(r2_ospf=r2_ospf, extra=r2_extra)
    return Simulator({"R1": parse_config(r1), "R2": parse_config(r2)}, CABLES, hosts=list(HOSTS))


def test_two_router_ospf_delivery():
    t = sim().trace("192.168.1.10", "192.168.2.10")
    assert t.outcome == "delivered"
    assert [h.device for h in t.hops] == ["host 192.168.1.10", "R1", "R2"]
    assert "ospf" in t.hops[1].detail


def test_acl_drop_on_ingress():
    s = sim(acl_in=" ip access-group BLOCK in", acl=ACL)
    t = s.trace("192.168.1.10", "192.168.2.10", "tcp", 22)
    assert t.outcome == "dropped" and "line 1" in t.reason
    assert s.trace("192.168.1.10", "192.168.2.10", "tcp", 443).outcome == "delivered"


def test_no_route_without_ospf_on_r2():
    t = sim(r2_ospf="").trace("192.168.1.10", "192.168.2.10")
    assert t.outcome == "no-route"


def test_static_loop():
    s = sim(r2_ospf="", r1_extra="ip route 172.16.0.0 255.255.0.0 10.0.12.1",
            r2_extra="ip route 172.16.0.0 255.255.0.0 10.0.12.0")
    assert s.trace("192.168.1.10", "172.16.5.5").outcome == "loop"


def test_null0_discard_and_floating_static():
    s = sim(r1_extra="ip route 192.168.2.0 255.255.255.0 Null0")
    t = s.trace("192.168.1.10", "192.168.2.10")
    assert t.outcome == "dropped" and "Null0" in t.reason  # AD 1 static beats OSPF AD 110
    s = sim(r1_extra="ip route 192.168.2.0 255.255.255.0 Null0 254")
    assert s.trace("192.168.1.10", "192.168.2.10").outcome == "delivered"  # floating static loses


def test_longest_prefix_wins():
    s = sim(r1_extra="ip route 192.168.0.0 255.255.0.0 Null0")
    assert s.trace("192.168.1.10", "192.168.2.10").outcome == "delivered"  # /24 OSPF beats /16 static


def test_shutdown_gateway():
    s = sim(extra_if="interface Gi0/1\n ip address 192.168.1.1 255.255.255.0\n shutdown")
    t = s.trace("192.168.1.10", "192.168.2.10")
    assert t.outcome == "dropped" and "gateway" in t.reason


def test_unknown_source():
    assert sim().trace("8.8.8.8", "192.168.2.10").outcome == "dropped"


@pytest.mark.parametrize("ifname, cost", [("TenGigabitEthernet1/0/1", 10), ("GigabitEthernet0/0", 100),
                                          ("Loopback0", 1), ("Tunnel1", 65535)])
def test_ospf_cost(ifname, cost):
    assert ospf_cost(ifname, 100_000) == cost


def test_acl_first_match_and_implicit_deny():
    entries = [PAclEntry(action="permit", proto="tcp", src="10.0.0.0", src_wc="0.0.0.255",
                         dst="any", dst_wc="255.255.255.255", port=443)]
    assert Simulator.acl_permits(entries, "10.0.0.5", "1.1.1.1", "tcp", 443)[0]
    ok, why = Simulator.acl_permits(entries, "10.0.0.5", "1.1.1.1", "tcp", 80)
    assert not ok and why == "implicit deny"
    assert not Simulator.acl_permits(entries, "10.0.1.5", "1.1.1.1", "tcp", 443)[0]


def test_l2_domain_requires_both_trunk_ends():
    sw = """hostname {h}
vlan 10
 name A
spanning-tree mode rapid-pvst
interface Te1
 switchport mode trunk
 switchport trunk allowed vlan {allowed}
"""
    cab = [Cable(a="S1", a_if="Te1", b="S2", b_if="Te1", kind="trunk")]
    ok = Simulator({"S1": parse_config(sw.format(h="S1", allowed="10")),
                    "S2": parse_config(sw.format(h="S2", allowed="10"))}, cab)
    assert ok.domain("S1", 10) == ok.domain("S2", 10)
    pruned = Simulator({"S1": parse_config(sw.format(h="S1", allowed="10")),
                        "S2": parse_config(sw.format(h="S2", allowed="20"))}, cab)
    assert pruned.domain("S1", 10) != pruned.domain("S2", 10)


AUTH_R1 = R2_OSPF.replace("router ospf 1\n", "router ospf 1\n area 0 authentication message-digest\n")


def _auth_sim(k1, k2, r2_auth=True):
    r1 = R1.format(acl_in=f" ip ospf message-digest-key 1 md5 {k1}", extra="", extra_if="").replace(
        "router ospf 1\n", "router ospf 1\n area 0 authentication message-digest\n")
    # move the key line onto Gi0/0 (R1 template puts acl_in under Gi0/1)
    r1 = r1.replace(f"interface Gi0/1\n ip address 192.168.1.1 255.255.255.0\n ip ospf message-digest-key 1 md5 {k1}",
                    "interface Gi0/1\n ip address 192.168.1.1 255.255.255.0").replace(
        "interface Gi0/0\n ip address 10.0.12.0 255.255.255.254",
        f"interface Gi0/0\n ip address 10.0.12.0 255.255.255.254\n ip ospf message-digest-key 1 md5 {k1}")
    r2 = R2.format(r2_ospf=AUTH_R1 if r2_auth else R2_OSPF, extra="").replace(
        "interface Gi0/0\n ip address 10.0.12.1 255.255.255.254",
        f"interface Gi0/0\n ip address 10.0.12.1 255.255.255.254\n ip ospf message-digest-key 1 md5 {k2}")
    return Simulator({"R1": parse_config(r1), "R2": parse_config(r2)}, CABLES, hosts=list(HOSTS))


@pytest.mark.parametrize("k1, k2, r2_auth, outcome", [
    ("KEY", "KEY", True, "delivered"),
    ("KEY", "OTHER", True, "no-route"),     # key mismatch: no adjacency
    ("KEY", "KEY", False, "no-route"),      # auth on one side only
])
def test_ospf_md5_adjacency(k1, k2, r2_auth, outcome):
    assert _auth_sim(k1, k2, r2_auth).trace("192.168.1.10", "192.168.2.10").outcome == outcome
