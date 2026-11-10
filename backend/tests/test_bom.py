import copy

from analysis.bom import build_bom, load_prices
from engine.planner import design
from engine.rationale import RULES
from tests.conftest import load


def qty(b, item):
    return sum(x.qty for x in b.lines if x.item == item)


def test_campus_counts(designs):
    r = designs["campus_lan"]
    b = build_bom(r)
    members = sum(d.members for d in r.devices if d.role == "access")
    assert qty(b, "48-port PoE+ access switch") + qty(b, "48-port access switch") == members
    assert qty(b, "Core switch") == 2
    assert qty(b, "SFP+ 10GBASE-SR") == 2 * sum(1 for c in r.cables if c.transceiver == "10GBASE-SR")
    om4 = sum(1.1 * next(ln.distance_m for ln in r.input.links if ln.key == c.link)
              for c in r.cables if c.media == "OM4 multimode fiber")
    assert qty(b, "OM4 multimode fiber") == -(-om4 // 1)
    assert b.poe_watts and all(w > 0 for w in b.poe_watts.values())


def test_metro_counts(designs):
    b = build_bom(designs["metro_man"])
    assert qty(b, "SFP+ 10GBASE-ER") == 8  # 2 links x 2 circuits x 2 ends
    assert qty(b, "Router") == 5
    assert b.monthly == 0


def test_wan_monthly(designs):
    b = build_bom(designs["global_wan"])
    p = load_prices()
    assert b.monthly == 2 * p["wan_service_per_month"]["carrier"] + 2 * p["wan_service_per_month"]["internet"]


def test_every_line_links_a_rule(designs):
    for name in ("campus_lan", "metro_man", "global_wan"):
        for x in build_bom(designs[name]).lines:
            assert x.rule_id in RULES
            assert x.total == round(x.qty * x.unit_price, 2)


def test_capex_sum(designs):
    b = build_bom(designs["campus_lan"])
    assert b.capex == round(sum(x.total for x in b.lines), 2)


def test_om3_alternative_only_when_all_runs_fit(designs):
    assert not build_bom(designs["campus_lan"]).alternatives  # 350 m run > 300 m OM3 limit
    d = load("campus_lan")
    for ln in d["links"]:
        ln["distance_m"] = min(ln["distance_m"], 290)
    alts = build_bom(design(d)).alternatives
    assert alts and "OM3" in alts[0].text


def test_custom_prices(designs):
    p = copy.deepcopy(load_prices())
    p["switch"]["core"] = 1
    b = build_bom(designs["campus_lan"], p)
    assert next(x for x in b.lines if x.item == "Core switch").total == 2
