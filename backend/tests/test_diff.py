import copy
import json

import pytest

from analysis.diff import diff, load_snapshot, snapshot
from engine.planner import design
from tests.conftest import load


def test_distance_380_to_420_flips_media():
    a = load("campus")
    b = copy.deepcopy(a)
    b["links"][1]["distance_m"] = 420
    d = diff(design(a), design(b))
    media = next(c for c in d.decisions if c.key == "L1.media[link=BldgA--BldgC]")
    assert media.change == "changed" and media.old_rules == ["L1.mmf"] and media.new_rules == ["L1.smf_lr"]
    assert "OM4" in media.old[0] and "OS2" in media.new[0]
    assert d.configs and all("10GBASE-LR" in x for x in d.configs.values())
    assert not d.subnets and not d.devices_added


def test_identical_designs_empty(designs):
    assert diff(designs["campus"], designs["campus"]).empty


def test_snapshot_round_trip(designs):
    r = designs["global_wan"]
    data = json.loads(json.dumps(snapshot(r)))
    assert diff(r, load_snapshot(data)).empty


def test_snapshot_version_checked(designs):
    with pytest.raises(ValueError):
        load_snapshot({"version": 99, "design": {}})


def test_added_segment_shows_in_all_layers():
    a = load("campus")
    b = copy.deepcopy(a)
    b["segments"].append({"name": "Cameras", "vlan": 60, "hosts": 20, "role": "iot", "location": "BldgB"})
    d = diff(design(a), design(b))
    assert any(s.name == "Cameras" and s.change == "added" for s in d.subnets)
    assert any("Cameras" in c.key and c.change == "added" for c in d.decisions)
    assert any("vlan 60" in x for x in d.configs.values())
