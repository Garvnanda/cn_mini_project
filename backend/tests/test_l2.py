import ipaddress

import pytest

from engine.l2 import pick_native
from tests.conftest import NAMES


def test_pick_native():
    assert pick_native({10, 20}) == 999
    assert pick_native({999}) == 4094
    assert pick_native({999, 4094}) == 4093


@pytest.mark.parametrize("name", NAMES)
def test_trunks_pruned_to_far_side_vlans(designs, name):
    r = designs[name]
    for d in r.devices:
        for i in d.interfaces:
            if i.mode != "trunk":
                continue
            peer = r.device(i.peer.split()[0])
            assert i.allowed_vlans, f"{d.hostname} {i.name} carries nothing"
            assert i.native_vlan not in i.allowed_vlans and i.native_vlan != 1
            access = d if d.role == "access" else peer if peer.role == "access" else None
            if access:
                assert set(i.allowed_vlans) == set(access.vlans) - {i.native_vlan}


@pytest.mark.parametrize("name", NAMES)
def test_unused_ports_parked_and_shut(designs, name):
    for d in designs[name].devices:
        for i in d.interfaces:
            if i.mode == "unused":
                assert i.vlan == 999


def test_stp_root_on_gateway_pair(designs):
    r = designs["campus"]
    c1, c2 = r.device("CAMPUS-CORE1"), r.device("CAMPUS-CORE2")
    assert c1.stp_primary == c2.stp_secondary == sorted(s.vlan for s in r.input.segments)
    assert not any(d.stp_primary for d in r.devices if d.role == "access")


def test_hsrp(designs):
    r = designs["campus"]
    subs = {s.name: s for s in r.subnets}
    for seg in r.input.segments:
        svis = [i for d in r.devices for i in d.interfaces if i.segment == seg.name]
        assert len(svis) == 2
        s = subs[seg.name]
        net = ipaddress.IPv4Network(f"{s.network}/{s.prefix}")
        assert {i.hsrp_vip for i in svis} == {s.gateway}
        assert {i.hsrp_priority for i in svis} == {110, 100}
        ips = {i.ip for i in svis}
        assert len(ips) == 2 and s.gateway not in ips
        assert all(ipaddress.IPv4Address(x) in net for x in ips)


def test_single_gateway_no_hsrp(designs):
    for d in designs["three_tier"].devices:
        for i in d.interfaces:
            assert i.hsrp_group is None
