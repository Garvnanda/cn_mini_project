import ipaddress

import pytest

from engine import bitmath as B
from engine.errors import InvalidPrefixError


@pytest.mark.parametrize("p", range(33))
def test_mask_and_wildcard_all_prefixes(p):
    net = ipaddress.IPv4Network(f"0.0.0.0/{p}")
    assert B.int_to_ip(B.prefix_to_mask(p)) == str(net.netmask)
    assert B.int_to_ip(B.wildcard(p)) == str(net.hostmask)
    assert 0 <= B.wildcard(p) <= 0xFFFFFFFF
    assert B.prefix_to_mask(p) | B.wildcard(p) == 0xFFFFFFFF
    assert B.mask_to_prefix(B.prefix_to_mask(p)) == p
    assert B.block_size(p) == net.num_addresses


@pytest.mark.parametrize("p", [-1, 33])
def test_bad_prefix(p):
    with pytest.raises(InvalidPrefixError):
        B.prefix_to_mask(p)


def test_non_contiguous_mask():
    with pytest.raises(InvalidPrefixError):
        B.mask_to_prefix(B.ip_to_int("255.0.255.0"))


@pytest.mark.parametrize("ip", ["0.0.0.0", "10.1.2.3", "255.255.255.255", "192.168.0.1"])
def test_ip_roundtrip(ip):
    assert B.ip_to_int(ip) == int(ipaddress.IPv4Address(ip))
    assert B.int_to_ip(B.ip_to_int(ip)) == ip


@pytest.mark.parametrize("ip", ["256.0.0.1", "1.2.3", "a.b.c.d", "1.2.3.4.5", ""])
def test_bad_ip(ip):
    with pytest.raises(InvalidPrefixError):
        B.ip_to_int(ip)


def test_network_broadcast():
    ip = B.ip_to_int("10.1.2.77")
    assert B.int_to_ip(B.network(ip, 26)) == "10.1.2.64"
    assert B.int_to_ip(B.broadcast(ip, 26)) == "10.1.2.127"


def test_parse_cidr():
    assert B.parse_cidr("10.0.0.0/16") == (B.ip_to_int("10.0.0.0"), 16)
    for bad in ["10.0.0.1/16", "10.0.0.0", "10.0.0.0/x", "10.0.0.0/33"]:
        with pytest.raises(InvalidPrefixError):
            B.parse_cidr(bad)


@pytest.mark.parametrize("p, n", [(30, 2), (24, 254), (31, 2), (32, 1), (0, 2**32 - 2)])
def test_usable_hosts(p, n):
    assert B.usable_hosts(p) == n


@pytest.mark.parametrize(
    "hosts, prefix",
    [(1, 30), (2, 29), (5, 29), (6, 28), (253, 24), (254, 23), (500, 23), (509, 23), (510, 22)],
)
def test_hosts_to_prefix_reserves_gateway(hosts, prefix):
    assert B.hosts_to_prefix(hosts) == prefix
    assert B.usable_hosts(prefix) >= hosts + 1
    if prefix < 30:
        assert B.usable_hosts(prefix + 1) < hosts + 1


def test_hosts_to_prefix_no_gateway():
    assert B.hosts_to_prefix(254, gateway=False) == 24
