import ipaddress

import pytest

from engine.errors import TopologyError
from engine.planner import design
from engine.routing import select_protocol
from tests.conftest import NAMES


def net(s):
    return ipaddress.IPv4Network(f"{s.network}/{s.prefix}")


@pytest.mark.parametrize(
    "n, multi, three, expected",
    [
        (49, False, False, "ospf_single"),
        (50, False, False, "ospf_large_flat"),
        (49, False, True, "ospf_single"),
        (50, False, True, "ospf_multi_campus"),
        (3, True, False, "ospf_multi_site"),
    ],
)
def test_select_protocol_boundaries(n, multi, three, expected):
    assert select_protocol(n, multi, three) == expected


def test_protocols_per_fixture(designs):
    assert designs["campus"].routing.protocol == "OSPF single-area"
    assert designs["three_tier"].routing.protocol == "OSPF single-area"
    assert designs["metro"].routing.protocol == "OSPF multi-area"
    assert designs["wan"].routing.protocol == "OSPF multi-area + eBGP"


@pytest.mark.parametrize("name", NAMES)
def test_no_overlap_inside_root(designs, name):
    r = designs[name]
    root = ipaddress.IPv4Network(r.input.root_prefix)
    nets = sorted(net(s) for s in r.subnets if s.unit != "internet underlay")
    assert all(n.subnet_of(root) for n in nets)
    for a, b in zip(nets, nets[1:]):
        assert not a.overlaps(b)


@pytest.mark.parametrize("name", NAMES)
def test_every_l3_interface_addressed(designs, name):
    for d in designs[name].devices:
        if not d.l3:
            continue
        for i in d.interfaces:
            if i.mode in ("routed", "svi", "loopback", "tunnel", "underlay"):
                assert i.ip and i.mask, f"{d.hostname} {i.name}"
        if d.role != "cloud":
            assert d.ospf.router_id == d.iface("Loopback0").ip


def _summary_check(r):
    checked = 0
    for d in r.devices:
        if not d.ospf:
            continue
        for area, network, mask in d.ospf.summaries:
            block = ipaddress.IPv4Network(f"{network}/{mask}")
            mine = [s for s in r.subnets if s.unit and s.unit.startswith(f"Area {area} ")]
            assert mine and all(net(s).subnet_of(block) for s in mine)
            others = [s for s in r.subnets if s not in mine and s.unit != "internet underlay"]
            assert not any(net(s).overlaps(block) for s in others), "over-summarization"
            checked += 1
    return checked


def test_metro_summaries_exact(designs):
    r = designs["metro"]
    assert _summary_check(r) == 2  # one ABR per branch
    assert r.device("BRANCH1-R1").ospf.summaries[0][0] == 1
    assert not r.device("HQ-R1").ospf.summaries


def test_wan_summaries_exact(designs):
    assert _summary_check(designs["wan"]) == 3


def big_campus():
    bldgs = ["B1", "B2", "B3", "B4"]
    return {
        "profile": "custom", "root_prefix": "10.40.0.0/16",
        "sites": [{"name": "U", "kind": "campus"}],
        "buildings": [{"name": b, "site": "U"} for b in bldgs],
        "links": [{"a": "B1", "b": b, "distance_m": 200} for b in bldgs[1:]],
        "segments": [
            {"name": f"S{i}", "vlan": 100 + i, "hosts": 20, "role": "user", "location": bldgs[i % 4]}
            for i in range(44)
        ],
    }


def test_multi_area_campus_at_50_subnets():
    r = design(big_campus())
    assert r.routing.protocol == "OSPF multi-area"
    abrs = [d for d in r.devices if d.ospf and d.ospf.summaries]
    assert {d.role for d in abrs} == {"distribution"} and len(abrs) == 4
    assert _summary_check(r) == 4


def test_wan_ebgp_and_ipsec(designs):
    r = designs["wan"]
    r1, vgw = r.device("DELHI-R1"), r.device("CLOUDVPC-VGW")
    assert r1.bgp.asn == 65000 and vgw.bgp.asn == 65100
    vgw_tun = next(i for i in vgw.interfaces if i.mode == "tunnel")
    assert (vgw_tun.ip, 65100) in r1.bgp.neighbors
    vpc = next(s for s in r.subnets if s.name == "VPC-Apps")
    assert (vpc.network, vpc.mask) in vgw.bgp.networks
    assert {sr.next_hop for sr in r1.static_routes} == {"Null0"}
    assert r1.ospf.redistribute_bgp == 65000
    assert vgw.ospf is None and vgw_tun.area is None
    underlay = ipaddress.IPv4Network("203.0.113.0/24")
    for d in r.devices:
        for i in d.interfaces:
            if i.mode == "tunnel":
                assert ipaddress.IPv4Address(i.tunnel_destination) in underlay
                assert d.iface(i.tunnel_source).mode == "underlay"
                peer = r.device(i.peer.split()[0])
                assert i.tunnel_destination == peer.iface(peer.iface(i.peer.split()[1]).tunnel_source).ip


def test_branch_without_backbone_link(raw):
    d = raw("metro")
    d["links"][1] = {"a": "Branch1", "b": "Branch2", "distance_m": 5000}
    with pytest.raises(TopologyError, match="discontiguous"):
        design(d)


def test_every_decision_explained(designs):
    for r in designs.values():
        domains = {x.domain for x in r.rationale}
        assert {"L1", "TOPO", "VLSM", "ROUTE"} <= domains
        assert r.routing.rationale
