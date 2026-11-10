import pytest

from engine import bitmath as B
from engine.configgen import render_device
from tests.conftest import NAMES
from verify.ios_parser import ParseError, parse_acl_entry, parse_config, parse_vlan_list


def test_vlan_list():
    assert parse_vlan_list("10,20-22") == [10, 20, 21, 22]
    assert parse_vlan_list("none") == []
    assert len(parse_vlan_list("all")) == 4094


def test_acl_entry_forms():
    e = parse_acl_entry("deny tcp host 10.0.0.5 any eq 22")
    assert (e.src, e.src_wc, e.dst, e.port) == ("10.0.0.5", "0.0.0.0", "any", 22)
    e = parse_acl_entry("permit ip 10.0.0.0 0.0.0.255 10.1.0.0 0.0.255.255")
    assert (e.dst, e.dst_wc, e.port) == ("10.1.0.0", "0.0.255.255", None)


def test_bad_interface_line():
    with pytest.raises(ParseError, match="line 2"):
        parse_config("interface Gi0/0\n switchport frobnicate\n")


def test_unknown_top_level_kept():
    d = parse_config("hostname X\nsnmp-server community public RO\n")
    assert d.unparsed == ["snmp-server community public RO"]


def test_hsrp_defaults():
    d = parse_config("interface Vlan10\n ip address 10.0.0.2 255.255.255.0\n standby 10 ip 10.0.0.1\n")
    g = d.interfaces["Vlan10"].hsrp[10]
    assert (g.ip, g.priority, g.preempt) == ("10.0.0.1", 100, False)


@pytest.mark.parametrize("name", NAMES)
def test_round_trip(designs, name):
    for dev in designs[name].devices:
        p = parse_config(render_device(dev))
        assert p.unparsed == [], (dev.hostname, p.unparsed)
        assert p.hostname == dev.hostname
        assert p.ip_routing == (dev.role in ("core", "distribution"))
        assert p.vlans.keys() == dev.vlans.keys()
        assert p.stp_primary == dev.stp_primary and p.stp_secondary == dev.stp_secondary
        assert set(p.interfaces) == {i.name for i in dev.interfaces}
        for i in dev.interfaces:
            pi = p.interfaces[i.name]
            assert pi.range == i.range
            assert (pi.ip, pi.mask) == (i.ip, i.mask)
            assert pi.acl_in == i.acl_in
            assert pi.shutdown == (i.mode == "unused")
            if i.mode in ("access", "unused"):
                assert (pi.mode, pi.access_vlan) == ("access", i.vlan)
                assert pi.portfast == pi.bpduguard == (i.mode == "access")
            if i.mode == "trunk":
                assert (pi.allowed_vlans, pi.native_vlan) == (i.allowed_vlans, i.native_vlan)
            if i.hsrp_group is not None:
                g = pi.hsrp[i.hsrp_group]
                assert (g.ip, g.priority, g.preempt, pi.hsrp_version) == (i.hsrp_vip, i.hsrp_priority, True, 2)
            if i.mode == "tunnel":
                assert (pi.tunnel_source, pi.tunnel_destination, pi.tunnel_mode) == (
                    i.tunnel_source, i.tunnel_destination, "ipsec ipv4")
        if dev.ospf:
            o = p.ospf
            assert (o.pid, o.router_id, o.ref_bw) == (dev.ospf.pid, dev.ospf.router_id, dev.ospf.ref_bw)
            assert o.networks == [tuple(x) for x in dev.ospf.networks]
            assert o.passive == dev.ospf.passive
            assert o.summaries == [tuple(x) for x in dev.ospf.summaries]
            assert o.redistribute_bgp == dev.ospf.redistribute_bgp
        else:
            assert p.ospf is None
        if dev.bgp:
            assert (p.bgp.asn, p.bgp.router_id) == (dev.bgp.asn, dev.bgp.router_id)
            assert p.bgp.neighbors == [tuple(x) for x in dev.bgp.neighbors]
            assert p.bgp.networks == [tuple(x) for x in dev.bgp.networks]
        assert [(s.network, s.mask, s.next_hop, s.distance) for s in p.statics] == [
            (s.network, s.mask, s.next_hop, s.distance) for s in dev.static_routes]
        assert {a.name: len(a.entries) for a in dev.acls} == {k: len(v) for k, v in p.acls.items()}
        assert p.isakmp_peers == dev.ipsec_peers


def test_round_trip_acl_semantics(designs):
    dev = designs["metro_man"].device("BRANCH-CORE1")
    p = parse_config(render_device(dev))
    for acl in dev.acls:
        for e, pe in zip(acl.entries, p.acls[acl.name]):
            assert (e.action, e.proto, e.src, e.dst, e.port) == (pe.action, pe.proto, pe.src, pe.dst, pe.port)
            if e.src != "any":
                assert B.ip_to_int(pe.src_wc) == B.ip_to_int(e.src_wc)
