import pytest

from analysis.whatif import cable_id, simulate_failure, spof_analysis
from engine.errors import InvalidParameterError


def test_metro_survives_single_hq_uplink_loss(designs):
    imp = simulate_failure(designs["metro_man"], links=["HQ-R1--BRANCH-R1"])
    assert imp.survives
    assert imp.rerouted  # traffic moved to HQ-R2
    assert all("HQ-R2" in x.after_path for x in imp.rerouted if "Branch" in (x.src + x.dst))
    assert imp.rationale[0].rule_id == "WHATIF.ospf"


def test_metro_survives_active_core_loss(designs):
    imp = simulate_failure(designs["metro_man"], nodes=["HQ-CORE1"])
    assert imp.survives
    assert imp.rationale[0].rule_id == "WHATIF.hsrp"


def test_metro_branch_core_not_spof_after_fix(designs):
    """Regression: a lone branch router used to uplink only to CORE1, making CORE1 a SPOF."""
    assert simulate_failure(designs["metro_man"], nodes=["BRANCH-CORE1"]).survives
    rep = spof_analysis(designs["metro_man"])
    assert rep.spof_devices == ["BRANCH-R1"]


def test_single_core_campus_spof(designs):
    r = designs["three_tier"]
    rep = spof_analysis(r)
    assert "UNI-CORE1" in rep.spof_devices
    imp = simulate_failure(r, nodes=["UNI-CORE1"])
    assert not imp.survives and imp.broken
    assert rep.score < 50


def test_redundant_campus_has_no_spof(designs):
    rep = spof_analysis(designs["campus_lan"])
    assert rep.spof_devices == [] and rep.spof_cables == [] and rep.score == 100


def test_trunk_failure_uses_rstp_rationale(designs):
    r = designs["campus_lan"]
    trunk = next(c for c in r.cables if c.kind == "trunk" and c.a.startswith("BLDGB-ACC"))
    imp = simulate_failure(r, links=[cable_id(trunk).replace(f"{trunk.a}:", f"{trunk.a}:", 1)])
    assert imp.survives and imp.rationale[0].rule_id == "WHATIF.rstp"


def test_wan_branch_router_loss_isolates_branch(designs):
    imp = simulate_failure(designs["global_wan"], nodes=["MUMBAI-R1"])
    assert not imp.survives
    assert {b.src for b in imp.broken} | {b.dst for b in imp.broken} >= {"Mumbai-IoT"}


@pytest.mark.parametrize("spec", ["nonsense", "X--Y"])
def test_bad_specs(designs, spec):
    with pytest.raises(InvalidParameterError):
        simulate_failure(designs["campus"], links=[spec])


def test_unknown_node(designs):
    with pytest.raises(InvalidParameterError):
        simulate_failure(designs["campus"], nodes=["NOPE"])
