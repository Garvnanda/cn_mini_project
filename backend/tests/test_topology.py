from collections import Counter, defaultdict

import pytest

from engine import constants as C
from engine.errors import TopologyError
from engine.planner import design
from engine.topology import graph, hostname
from tests.conftest import NAMES


@pytest.mark.parametrize(
    "name, counts",
    [
        ("campus", {"core": 2, "access": 6}),
        ("metro", {"core": 6, "router": 4, "access": 3}),
        ("wan", {"core": 4, "router": 4, "access": 8, "cloud": 1}),
        ("three_tier", {"core": 1, "distribution": 4, "access": 4}),
    ],
)
def test_device_counts(designs, name, counts):
    assert Counter(d.role for d in designs[name].devices) == counts


@pytest.mark.parametrize("name", NAMES)
def test_no_orphan_ports_and_unique_names(designs, name):
    r = designs[name]
    for d in r.devices:
        names = [i.name for i in d.interfaces]
        assert len(names) == len(set(names)), d.hostname
    for c in r.cables:
        for host, ifname in ((c.a, c.a_if), (c.b, c.b_if)):
            i = r.device(host).iface(ifname)
            assert i.peer is not None
        assert r.device(c.a).iface(c.a_if).peer == f"{c.b} {c.b_if}"


@pytest.mark.parametrize("name", NAMES)
def test_graph_connected(designs, name):
    r = designs[name]
    adj = defaultdict(set)
    for c in r.cables:
        adj[c.a].add(c.b)
        adj[c.b].add(c.a)
    start = r.devices[0].hostname
    seen, stack = {start}, [start]
    while stack:
        for n in adj[stack.pop()] - seen:
            seen.add(n)
            stack.append(n)
    assert seen == {d.hostname for d in r.devices}
    g = graph(r.devices, r.cables)
    assert len(g["nodes"]) == len(r.devices) and len(g["edges"]) == len(r.cables)


@pytest.mark.parametrize("name", NAMES)
def test_access_ports_match_hosts(designs, name):
    r = designs[name]
    ports = Counter()
    for d in r.devices:
        for i in d.interfaces:
            if i.mode == "access":
                a, _, b = i.name.partition(" - ")
                first = int(a.rsplit("/", 1)[1])
                ports[i.vlan] += (int(b) - first + 1) if b else 1
    for s in r.input.segments:
        if r.input.sites[0].kind.value != "cloud" and any(
            x.name == s.location and x.kind.value == "cloud" for x in r.input.sites
        ):
            continue
        assert ports[s.vlan] == s.hosts, s.name


def test_stack_limits(designs):
    for d in designs["campus"].devices:
        if d.role == "access":
            assert 1 <= d.members <= C.STACK_MAX_MEMBERS


def test_poe_budget(designs):
    acc = [d for d in designs["campus"].devices if d.poe_watts]
    assert sum(d.poe_watts for d in acc) == (30 + 30) * C.POE_WATTS_PER_PORT
    assert any(r.rule_id == "TOPO.poe" for r in designs["campus"].rationale)


def test_tier_rule(designs):
    assert designs["campus"].tiers == {"Campus": "collapsed_core"}
    assert designs["three_tier"].tiers == {"Uni": "three_tier"}


def test_dual_homing(designs):
    r = designs["metro"]
    hq_r = {"HQ-R1", "HQ-R2"}
    b1 = [c for c in r.cables if "BRANCH1-R1" in (c.a, c.b) and ({c.a, c.b} & hq_r)]
    assert len(b1) == 2
    assert all(c.transceiver == "10GBASE-ER" for c in b1)


def test_uplink_media_follows_link(designs):
    r = designs["three_tier"]
    sci = [c for c in r.cables if "SCI-DIST1" in (c.a, c.b) and "UNI-CORE1" in (c.a, c.b)]
    assert sci[0].transceiver == "10GBASE-LR"  # 900 m -> OS2
    lib = [c for c in r.cables if "LIB-DIST1" in (c.a, c.b) and "UNI-CORE1" in (c.a, c.b)]
    assert lib[0].transceiver == "10GBASE-T"   # 90 m -> Cat6a


def test_building_without_link_to_hub(raw):
    d = raw("campus")
    d["links"] = d["links"][:1]  # BldgC loses its link to BldgA
    with pytest.raises(TopologyError, match="BldgC"):
        design(d)


def test_disconnected_site(raw):
    d = raw("metro")
    d["links"] = d["links"][:1]
    with pytest.raises(TopologyError, match="Branch2"):
        design(d)


@pytest.mark.parametrize("raw_name, expected", [("Bldg A", "BLDG-A"), ("1st floor", "N-1ST-FLOOR"), ("a__b", "A-B")])
def test_hostname(raw_name, expected):
    assert hostname(raw_name) == expected
