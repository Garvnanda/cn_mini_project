import copy

import pytest

from engine.errors import InvalidParameterError, InvalidPrefixError, NetArchError
from engine.models import DesignInput, Rationale, Subnet, parse_design_input

VALID = {
    "profile": "campus_lan",
    "root_prefix": "10.10.0.0/16",
    "sites": [{"name": "Campus", "kind": "campus"}],
    "buildings": [{"name": "BldgA", "site": "Campus"}, {"name": "BldgB", "site": "Campus"}],
    "links": [{"a": "BldgA", "b": "BldgB", "distance_m": 250}],
    "segments": [
        {"name": "Staff", "vlan": 10, "hosts": 500, "role": "user", "location": "BldgA"},
        {"name": "Guest", "vlan": 30, "hosts": 200, "role": "guest", "location": "BldgB"},
    ],
    "policies": [{"src": "Guest", "dst": "Staff", "action": "deny"}],
}


def mutate(fn):
    d = copy.deepcopy(VALID)
    fn(d)
    return d


def test_valid_input_parses():
    d = parse_design_input(VALID)
    assert isinstance(d, DesignInput)
    assert d.links[0].media_preference == "auto"
    assert d.links[0].required_gbps == 10


@pytest.mark.parametrize("prefix", ["10.10.0.1/16", "10.10.0.0/33", "300.0.0.0/8", "abc", "10.0.0.0"])
def test_bad_root_prefix(prefix):
    with pytest.raises(InvalidPrefixError):
        parse_design_input(mutate(lambda d: d.update(root_prefix=prefix)))


@pytest.mark.parametrize("vlan", [0, 1, 4095, 5000])
def test_bad_vlan(vlan):
    with pytest.raises(InvalidParameterError, match="vlan"):
        parse_design_input(mutate(lambda d: d["segments"][0].update(vlan=vlan)))


@pytest.mark.parametrize("vlan", [2, 4094])
def test_vlan_bounds_ok(vlan):
    parse_design_input(mutate(lambda d: d["segments"][0].update(vlan=vlan)))


@pytest.mark.parametrize(
    "fn, match",
    [
        (lambda d: d["segments"][1].update(vlan=10), "duplicate VLAN"),
        (lambda d: d["segments"][1].update(name="Staff"), "duplicate segment"),
        (lambda d: d["segments"][0].update(hosts=0), "hosts"),
        (lambda d: d["segments"][0].update(location="Nowhere"), "unknown location"),
        (lambda d: d["links"][0].update(distance_m=0), "distance_m"),
        (lambda d: d["links"][0].update(distance_m=-5), "distance_m"),
        (lambda d: d["links"][0].update(b="BldgA"), "must differ"),
        (lambda d: d["links"][0].update(b="BldgZ"), "unknown site/building"),
        (lambda d: d["links"][0].update(media_preference="carrier-pigeon"), "media_preference"),
        (lambda d: d["buildings"][0].update(site="Mars"), "unknown site"),
        (lambda d: d["buildings"].append({"name": "Campus", "site": "Campus"}), "both a site and a building"),
        (lambda d: d["policies"][0].update(dst="Ghost"), "unknown segment"),
        (lambda d: d["policies"][0].update(port=70000), "port"),
        (lambda d: d.update(segments=[]), "segments"),
        (lambda d: d.update(sites=[]), "sites"),
        (lambda d: d.update(bogus=1), "bogus"),
        (lambda d: d.update(profile="lunar_base"), "profile"),
    ],
)
def test_invalid_inputs(fn, match):
    with pytest.raises(InvalidParameterError, match=match):
        parse_design_input(mutate(fn))


def test_error_to_dict():
    with pytest.raises(NetArchError) as ei:
        parse_design_input(mutate(lambda d: d["segments"][0].update(hosts=0)))
    out = ei.value.to_dict()
    assert out["type"] == "InvalidParameterError"
    assert out["details"]["errors"][0]["loc"] == "segments.0.hosts"


def test_output_models_construct():
    r = Rationale(rule_id="L1.copper", domain="L1", standard_ref="IEEE 802.3an", text="x")
    s = Subnet(
        name="Staff", vlan=10, requested_hosts=500, network="10.10.0.0", prefix=23,
        mask="255.255.254.0", wildcard="0.0.1.255", gateway="10.10.0.1", broadcast="10.10.1.255",
        first_usable="10.10.0.1", last_usable="10.10.1.254", usable_hosts=510, utilization_pct=98.0,
    )
    assert r.inputs == {} and s.prefix == 23
