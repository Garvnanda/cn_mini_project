import os
import re
from pathlib import Path

import pytest

from engine.configgen import export, render_all
from tests.conftest import NAMES

DOC = Path(__file__).resolve().parents[2] / "docs" / "ios_reference.md"
GOLDEN = Path(__file__).parent / "golden"


def allowed_prefixes() -> list[str]:
    out = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| Context"):
            continue
        for cmd in re.findall(r"`([^`]+)`", line):
            prefix = re.split(r"[<\[]", cmd)[0].strip().rstrip("^").strip()
            words = prefix.split()
            alts = words[0].split("\\|") if words else []
            for a in alts:
                out.append(" ".join([a, *words[1:]]).replace("\\|", "|"))
    return [p for p in out if p]


PREFIXES = allowed_prefixes()


def documented(line: str) -> bool:
    for p in PREFIXES:
        if "|" in p:  # alternative in a later word, e.g. "root primary|secondary"
            continue
        if line == p or line.startswith(p + " "):
            return True
    return False


def test_doc_parses():
    assert "hostname" in PREFIXES and "permit" in PREFIXES and "deny" in PREFIXES


@pytest.mark.parametrize("name", NAMES)
def test_only_documented_commands(designs, name):
    for host, text in render_all(designs[name]).items():
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("!"):
                continue
            assert documented(s), f"{host}: undocumented IOS command: {s!r}"


@pytest.mark.parametrize("name", NAMES)
def test_golden(designs, name, tmp_path):
    cfgs = render_all(designs[name])
    gdir = GOLDEN / name
    if os.environ.get("UPDATE_GOLDEN"):
        for p in gdir.glob("*.cfg"):
            p.unlink()
        export(designs[name], gdir)
    expected = {p.stem: p.read_text(encoding="utf-8") for p in gdir.glob("*.cfg")}
    assert expected, f"no golden files for {name}; run with UPDATE_GOLDEN=1"
    assert set(cfgs) == set(expected)
    for host, text in cfgs.items():
        assert text == expected[host], f"{name}/{host}.cfg differs from golden"


@pytest.mark.parametrize("name", NAMES)
def test_structure(designs, name):
    for host, text in render_all(designs[name]).items():
        assert text.rstrip().endswith("end")
        assert f"hostname {host}\n" in text
        assert "{{" not in text and "None" not in text


def test_acl_rendered_and_applied(designs):
    cfg = render_all(designs["campus"])["CAMPUS-CORE1"]
    assert "ip access-list extended ACL-GUEST-C-IN" in cfg
    assert " permit ip any any" in cfg
    assert " ip access-group ACL-GUEST-C-IN in" in cfg
    metro = render_all(designs["metro"])["BRANCH2-CORE1"]
    allow = metro.index(" permit tcp")
    deny = metro.index(" deny ip")
    assert allow < deny and " eq 443" in metro  # order of policies kept (first match wins)


def test_routed_switch_ports_use_no_switchport(designs):
    cfgs = render_all(designs["three_tier"])
    assert "no switchport" in cfgs["SCI-DIST1"]
    assert "no switchport" not in render_all(designs["metro"])["HQ-R1"]


def test_ipsec_rendered(designs):
    cfg = render_all(designs["wan"])["DELHI-R1"]
    for s in ["crypto isakmp policy 10", "tunnel mode ipsec ipv4", "tunnel protection ipsec profile VTI-PROFILE",
              "router bgp 65000", "redistribute bgp 65000 subnets", "Null0"]:
        assert s in cfg
