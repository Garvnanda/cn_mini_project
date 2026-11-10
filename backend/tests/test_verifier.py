import pytest

from engine.configgen import render_all
from tests.conftest import NAMES
from verify.verifier import expected_action, verify


@pytest.mark.parametrize("name", NAMES)
def test_generated_designs_verify(designs, name):
    rep = verify(designs[name])
    assert rep.passed, rep.summary() + "\n" + "\n".join(d for c in rep.checks for d in c.details[:3])
    assert rep.probes and all(p.expected == p.actual for p in rep.probes)


def failing(rep):
    return {c.name for c in rep.checks if not c.passed}


def test_policy_probes_present(designs):
    rep = verify(designs["campus_lan"])
    denied = [p for p in rep.probes if p.src == "Guest-C" and p.dst == "Servers"]
    assert denied and denied[0].actual == "dropped" and "ACL-GUEST-C-IN" in denied[0].reason


def test_expected_action_first_match(designs):
    r = designs["metro_man"]
    assert expected_action(r, "Branch-Users", "Colo-Trading", "tcp", 443) == "delivered"
    assert expected_action(r, "Branch-Users", "Colo-Trading", "icmp", None) == "dropped"
    assert expected_action(r, "Branch-Users", "HQ-Users", "icmp", None) == "delivered"


# ---------------------------------------------------------------- bug injection (12.5)

def test_detects_wrong_mask(designs):
    r = designs["three_tier"]
    cfg = render_all(r)
    sci = next(s for s in r.subnets if s.name == "Sci-Users")
    assert sci.mask == "255.255.255.128"
    cfg["SCI-DIST1"] = cfg["SCI-DIST1"].replace(
        f"ip address {sci.gateway} 255.255.255.128", f"ip address {sci.gateway} 255.255.255.192")
    rep = verify(r, cfg)
    assert "reachability_and_policy" in failing(rep) or "gateway_reachability" in failing(rep)


def test_detects_unpruned_trunk(designs):
    r = designs["campus_lan"]
    cfg = render_all(r)
    text = cfg["BLDGC-ACC1"]
    line = next(x for x in text.splitlines() if "switchport trunk allowed vlan" in x)
    cfg["BLDGC-ACC1"] = text.replace(line, " switchport trunk allowed vlan 10,11,12,20,21,30,40,41,42,50", 1)
    rep = verify(r, cfg)
    assert failing(rep) == {"access_trunk_scope"}


def test_detects_acl_order_swap(designs):
    r = designs["metro_man"]
    cfg = render_all(r)
    for host in ("BRANCH-CORE1", "BRANCH-CORE2"):
        lines = cfg[host].splitlines()
        i = next(n for n, x in enumerate(lines) if x.startswith(" permit tcp"))
        lines[i], lines[i + 1] = lines[i + 1], lines[i]  # deny ip now precedes permit tcp 443
        cfg[host] = "\n".join(lines) + "\n"
    rep = verify(r, cfg)
    assert failing(rep) == {"reachability_and_policy"}
    bad = [p for p in rep.probes if p.expected != p.actual]
    assert any(p.proto == "tcp" and p.port == 443 for p in bad)


def test_detects_ad1_null0_blackhole(designs):
    """Regression for ai_audit_log.md entry 2: AD-1 Null0 anchor beats the OSPF summary."""
    r = designs["global_wan"]
    cfg = render_all(r)
    assert " Null0 254" in cfg["DELHI-R1"]
    cfg["DELHI-R1"] = cfg["DELHI-R1"].replace(" Null0 254", " Null0")
    rep = verify(r, cfg)
    assert "reachability_and_policy" in failing(rep)
    assert any("Null0" in p.reason for p in rep.probes if p.expected != p.actual)


def test_detects_shutdown_gateway(designs):
    r = designs["three_tier"]
    cfg = render_all(r)
    cfg["LIB-DIST1"] = cfg["LIB-DIST1"].replace(
        " description Gateway Lib-Users\n", " description Gateway Lib-Users\n shutdown\n").replace(
        " shutdown\n ip address", " shutdown\n ip address")
    # remove the trailing "no shutdown" of that SVI so it stays down
    lines = cfg["LIB-DIST1"].splitlines()
    start = lines.index("interface Vlan20")
    end = next(n for n in range(start, len(lines)) if lines[n] == "!")
    lines[start:end] = [x for x in lines[start:end] if x != " no shutdown"]
    cfg["LIB-DIST1"] = "\n".join(lines) + "\n"
    rep = verify(r, cfg)
    assert "gateway_reachability" in failing(rep)


def test_detects_overlap(designs):
    r = designs["three_tier"]
    cfg = render_all(r)
    sci = next(s for s in r.subnets if s.name == "Sci-Users")
    eng = next(s for s in r.subnets if s.name == "Eng-Users")
    cfg["SCI-DIST1"] = cfg["SCI-DIST1"].replace(f"ip address {sci.gateway} {sci.mask}",
                                                f"ip address {eng.last_usable} 255.255.255.0")
    rep = verify(r, cfg)
    assert "no_overlapping_subnets" in failing(rep)
