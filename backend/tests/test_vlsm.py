import ipaddress

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from engine.errors import AddressSpaceExhaustedError
from engine.vlsm import AllocRequest, allocate


def nets(subnets):
    return [ipaddress.IPv4Network(f"{s.network}/{s.prefix}") for s in subnets]


def test_basic_allocation_largest_first():
    reqs = [AllocRequest("Guest", 100, vlan=30), AllocRequest("Staff", 500, vlan=10),
            AllocRequest("Mgmt", 20, vlan=99)]
    subs, rat = allocate("10.10.0.0/16", reqs)
    assert [s.name for s in subs] == ["Staff", "Guest", "Mgmt"]
    staff = subs[0]
    assert (staff.network, staff.prefix, staff.gateway, staff.broadcast) == (
        "10.10.0.0", 23, "10.10.0.1", "10.10.1.255")
    assert staff.wildcard == "0.0.1.255" and staff.mask == "255.255.254.0"
    assert staff.last_usable == "10.10.1.254" and staff.usable_hosts == 510
    assert rat[-1].rule_id == "VLSM.efficiency"


def test_oracle_matches_ipaddress():
    subs, _ = allocate("172.16.0.0/20", [AllocRequest(f"S{i}", h) for i, h in enumerate([300, 60, 12, 2])])
    for s, n in zip(subs, nets(subs)):
        hosts = list(n.hosts())
        assert s.mask == str(n.netmask) and s.wildcard == str(n.hostmask)
        assert s.broadcast == str(n.broadcast_address)
        assert s.gateway == str(hosts[0]) == s.first_usable
        assert s.last_usable == str(hosts[-1])


def test_p2p_31_and_loopback_32():
    subs, rat = allocate("10.0.0.0/24", [AllocRequest("R1-R2", kind="p2p"), AllocRequest("Lo-R1", kind="loopback")])
    p2p = next(s for s in subs if s.name == "R1-R2")
    lo = next(s for s in subs if s.name == "Lo-R1")
    assert (p2p.prefix, p2p.usable_hosts, p2p.broadcast, p2p.gateway) == (31, 2, None, None)
    assert (p2p.first_usable, p2p.last_usable) == ("10.0.0.0", "10.0.0.1")
    assert (lo.prefix, lo.first_usable, lo.last_usable) == (32, "10.0.0.2", "10.0.0.2")
    assert {r.rule_id for r in rat} >= {"VLSM.p2p", "VLSM.loopback"}


def test_exact_fit():
    subs, _ = allocate("10.0.0.0/24", [AllocRequest("A", 125), AllocRequest("B", 125)])
    assert [s.network for s in subs] == ["10.0.0.0", "10.0.0.128"]


def test_exhaustion():
    with pytest.raises(AddressSpaceExhaustedError) as ei:
        allocate("10.0.0.0/24", [AllocRequest("A", 126), AllocRequest("B", 126)])  # each needs /24
    d = ei.value.details
    assert d["needed"] == 512 and d["available"] == 256
    assert "/23" in ei.value.message


def test_absurd_host_count_exhausts():
    with pytest.raises(AddressSpaceExhaustedError):
        allocate("10.0.0.0/8", [AllocRequest("Huge", 2**32)])


def test_duplicate_names():
    with pytest.raises(ValueError):
        allocate("10.0.0.0/24", [AllocRequest("A", 2), AllocRequest("A", 2)])


requests = st.lists(
    st.one_of(
        st.builds(AllocRequest, name=st.just(""), hosts=st.integers(1, 2000), kind=st.just("lan")),
        st.builds(AllocRequest, name=st.just(""), kind=st.sampled_from(["p2p", "loopback"])),
    ),
    min_size=1, max_size=30,
)


@settings(max_examples=500, deadline=None)
@given(reqs=requests, root_p=st.integers(12, 24))
def test_property_no_overlap_inside_root(reqs, root_p):
    reqs = [AllocRequest(f"n{i:02d}", r.hosts, r.kind) for i, r in enumerate(reqs)]
    root = f"10.0.0.0/{root_p}"
    try:
        subs, _ = allocate(root, reqs)
    except AddressSpaceExhaustedError:
        assert sum(1 << (32 - r.prefix) for r in reqs) > (1 << (32 - root_p))
        return
    root_net = ipaddress.IPv4Network(root)
    ns = sorted(nets(subs))
    for n in ns:
        assert n.subnet_of(root_net)
    for a, b in zip(ns, ns[1:]):
        assert not a.overlaps(b)
    by_name = {s.name: s for s in subs}
    for r in reqs:
        assert by_name[r.name].usable_hosts >= r.needed
