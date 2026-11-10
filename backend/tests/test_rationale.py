import json
import re

import pytest

from engine.rationale import RULES, RationaleError, RationaleLog, _fields, explain


@pytest.mark.parametrize("rule_id", sorted(RULES))
def test_every_rule_renders(rule_id):
    fields = {f: "X" for f in _fields(RULES[rule_id][3])}
    r = explain(rule_id, **fields)
    assert r.text and "{" not in r.text
    assert r.standard_ref and r.domain == rule_id.split(".")[0]


def test_every_rule_cites_a_standard():
    for rule_id, (_, ref, _, _) in RULES.items():
        assert re.search(r"(IEEE|RFC|TIA|Cisco|Assignment|Project)", ref), rule_id


def test_unknown_rule():
    with pytest.raises(RationaleError, match="unknown rule"):
        explain("L9.nope")


def test_missing_field():
    with pytest.raises(RationaleError, match="distance_m"):
        explain("L1.copper", link="A--B")


def test_log_collects_and_exports():
    log = RationaleLog()
    log.add("L1.copper", link="A--B", distance_m=80)
    log.add("VLSM.p2p", name="R1-R2")
    assert set(log.by_domain()) == {"L1", "VLSM"}
    md = log.to_markdown()
    assert "## L1" in md and "IEEE 802.3an" in md and "80 m" in md
    assert len(json.loads(log.to_json())) == 2
