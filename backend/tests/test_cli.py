import json

import pytest
from typer.testing import CliRunner

from cli import app

runner = CliRunner()
EX = "examples"


def run(*args):
    return runner.invoke(app, list(args))


def test_design_summary():
    r = run("design", "metro_man")
    assert r.exit_code == 0 and "OSPF multi-area" in r.output and "10GBASE-ER" in r.output


def test_design_export(tmp_path):
    r = run("design", "campus_lan", "--export", str(tmp_path))
    assert r.exit_code == 0 and (tmp_path / "design_report.md").exists()


@pytest.mark.parametrize("file, code", [
    ("invalid_copper_150m.json", 4), ("invalid_exhausted.json", 5), ("invalid_bad_vlan.json", 2)])
def test_exit_codes(file, code):
    r = run("design", f"{EX}/{file}")
    assert r.exit_code == code


def test_unknown_target():
    assert run("design", "does_not_exist").exit_code == 2


def test_bad_json(tmp_path):
    p = tmp_path / "x.json"
    p.write_text("{nope")
    assert run("design", str(p)).exit_code == 2


def test_explain_domain():
    r = run("explain", "campus_lan", "--domain", "L1")
    assert r.exit_code == 0 and "## L1" in r.output and "## ROUTE" not in r.output


def test_verify_pass():
    r = run("verify", "global_wan")
    assert r.exit_code == 0 and "PASS" in r.output


def test_trace_denied_and_delivered():
    r = run("trace", "campus_lan", "Guest-C", "Servers")
    assert r.exit_code == 1 and "DROPPED" in r.output and "ACL-GUEST-C-IN" in r.output
    r = run("trace", "metro_man", "Branch-Users", "Colo-Trading", "--proto", "tcp", "--port", "443")
    assert r.exit_code == 0 and "DELIVERED" in r.output


def test_fail_and_spof():
    r = run("fail", "metro_man", "--link", "HQ-R1--BRANCH-R1")
    assert r.exit_code == 0 and "Broken flows: 0" in r.output
    r = run("fail", "three_tier_dummy")
    assert r.exit_code == 2
    r = run("fail", "metro_man")
    assert "Resilience score" in r.output
    assert run("fail", "metro_man", "--node", "NOPE").exit_code == 2


def test_lint_file_and_design(tmp_path):
    cfg = tmp_path / "bad.cfg"
    cfg.write_text("hostname B\nline vty 0 4\n transport input telnet\n")
    r = run("lint", str(cfg))
    assert "SEC-06" in r.output
    assert "Security score" in run("lint", "campus_lan").output


def test_bom():
    r = run("bom", "metro_man")
    assert r.exit_code == 0 and "SFP+ 10GBASE-ER" in r.output and "PLACEHOLDER" in r.output


def test_diff(tmp_path):
    d = json.loads(open("presets/campus_lan.json", encoding="utf-8").read())
    d["links"][1]["distance_m"] = 420
    p = tmp_path / "c2.json"
    p.write_text(json.dumps(d))
    r = run("diff", "campus_lan", str(p))
    assert r.exit_code == 0 and "L1.media" in r.output
    assert "No differences" in run("diff", "campus_lan", "campus_lan").output


def test_nl_to_file_then_design(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    out = tmp_path / "nl.json"
    r = run("nl", "HQ plus 2 branches at 22 km and 35 km, 450 users", "--out", str(out))
    assert r.exit_code == 0 and "fallback" in r.output and out.exists()
    assert run("design", str(out)).exit_code == 0
    r = run("nl", "2 buildings with 100 users")
    assert r.exit_code == 0 and "missing" in r.output
