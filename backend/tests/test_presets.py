import pytest

from engine.errors import AddressSpaceExhaustedError, InvalidParameterError, PhysicalDistanceViolationError
from engine.planner import design
from tests.conftest import PRESET_NAMES, load


def test_campus_spec(designs):
    r = designs["campus_lan"]
    inp = r.input
    assert len(inp.buildings) == 3 and all(ln.distance_m < 400 for ln in inp.links)
    assert sum(s.hosts for s in inp.segments) == 1600
    assert any(s.poe for s in inp.segments)
    assert r.routing.protocol == "OSPF single-area"
    assert {m.transceiver for m in r.media} == {"10GBASE-SR"}  # 101-400 m backbone -> OM4


def test_metro_spec(designs):
    r = designs["metro_man"]
    inp = r.input
    assert len(inp.sites) == 3 and all(15_000 <= ln.distance_m <= 35_000 for ln in inp.links)
    assert sum(s.hosts for s in inp.segments if s.role.value == "user") == 450
    assert {m.media for m in r.media} == {"OS2 single-mode fiber"}
    assert r.routing.protocol == "OSPF multi-area"
    for site in ("BRANCH", "COLO"):
        hq = [c for c in r.cables if {c.a, c.b} & {"HQ-R1", "HQ-R2"}
              and any(x.startswith(site + "-R") for x in (c.a, c.b))]
        assert len(hq) == 2 and len({c.a for c in hq} | {c.b for c in hq}) >= 3, "remote site must be dual-homed"


def test_wan_spec(designs):
    r = designs["global_wan"]
    inp = r.input
    assert sum(s.kind.value != "cloud" for s in inp.sites) == 4 and any(s.kind.value == "cloud" for s in inp.sites)
    assert sum(s.hosts for s in inp.segments if s.role.value == "iot") == 2000
    assert r.routing.protocol == "OSPF multi-area + eBGP"
    assert any(d.ipsec_peers for d in r.devices)
    assert any(d.ospf and d.ospf.summaries for d in r.devices)


@pytest.mark.parametrize("name", PRESET_NAMES)
def test_preset_every_domain_explained(designs, name):
    domains = {x.domain for x in designs[name].rationale}
    assert {"L1", "TOPO", "VLSM", "L2", "ROUTE"} <= domains


@pytest.mark.parametrize(
    "name, err",
    [
        ("invalid_copper_150m", PhysicalDistanceViolationError),
        ("invalid_exhausted", AddressSpaceExhaustedError),
        ("invalid_bad_vlan", InvalidParameterError),
    ],
)
def test_invalid_examples(name, err):
    with pytest.raises(err):
        design(load(name))


def test_custom_example():
    r = design(load("custom_small_office"))
    assert r.routing.protocol == "OSPF single-area" and len(r.devices) == 2
