import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

import api
from tests.conftest import load

client = TestClient(api.app)


def test_health_and_presets():
    assert client.get("/health").json()["status"] == "ok"
    names = {p["name"] for p in client.get("/presets").json()}
    assert names == {"campus_lan", "metro_man", "global_wan"}
    assert client.get("/presets/metro_man").json()["profile"] == "metro_man"
    assert client.get("/presets/nope").status_code == 404


def test_design_bundle():
    r = client.post("/design", json=load("metro_man"))
    assert r.status_code == 200
    b = r.json()
    assert set(b) == {"design", "graph", "configs", "verification", "lint", "bom", "spof"}
    assert b["verification"]["passed"] and b["design"]["routing"]["protocol"] == "OSPF multi-area"
    assert len(b["graph"]["nodes"]) == len(b["design"]["devices"])


@pytest.mark.parametrize("name, typ", [
    ("invalid_copper_150m", "PhysicalDistanceViolationError"),
    ("invalid_exhausted", "AddressSpaceExhaustedError"),
    ("invalid_bad_vlan", "InvalidParameterError"),
])
def test_typed_errors_422(name, typ):
    r = client.post("/design", json=load(name))
    assert r.status_code == 422 and r.json()["type"] == typ and r.json()["message"]


def test_trace_whatif_spof():
    inp = load("campus_lan")
    t = client.post("/trace", json={"input": inp, "src": "Guest-C", "dst": "Servers"}).json()
    assert t["outcome"] == "dropped"
    w = client.post("/whatif", json={"input": load("metro_man"), "links": ["HQ-R1--BRANCH-R1"]}).json()
    assert w["survives"] and w["rerouted"]
    assert client.post("/whatif", json={"input": inp, "nodes": ["NOPE"]}).status_code == 422
    assert client.post("/spof", json=inp).json()["score"] == 100


def test_lint_bom_diff_verify():
    assert "SEC-06" in {f["rule"] for f in client.post("/lint", json={"text": "hostname X\nline vty 0 4\n transport input telnet\n"}).json()["findings"]}
    assert client.post("/lint", json={"input": load("campus_lan")}).json()["score"] >= 80
    assert client.post("/lint", json={}).status_code == 400
    assert client.post("/bom", json=load("metro_man")).json()["capex"] > 0
    b = load("campus_lan")
    b["links"][1]["distance_m"] = 420
    d = client.post("/diff", json={"a": load("campus_lan"), "b": b}).json()
    assert not d["empty"] and any(c["key"].startswith("L1.media") for c in d["decisions"])
    assert client.post("/verify", json=load("global_wan")).json()["passed"]


def test_exports():
    inp = load("campus_lan")
    z = client.post("/export/zip", json=inp)
    assert z.status_code == 200
    names = zipfile.ZipFile(io.BytesIO(z.content)).namelist()
    assert "campus_lan/design_report.md" in names and "campus_lan/CAMPUS-CORE1.cfg" in names
    assert json.loads(client.post("/export/json", json=inp).text)["version"] == 1
    assert "# NetArchitect Design Report" in client.post("/export/report", json=inp).text
    assert "# Cabling Guide" in client.post("/export/cabling", json=inp).text
    assert client.post("/export/pdf", json=inp).status_code == 404


def test_nl_and_rate_limit(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(api, "NL_RATE_PER_MIN", 2)
    api._nl_hits.clear()
    r = client.post("/nl", json={"text": "HQ and 2 branches at 22 km and 35 km, 450 users"})
    assert r.status_code == 200 and r.json()["source"] == "fallback" and r.json()["valid"]
    client.post("/nl", json={"text": "x"})
    assert client.post("/nl", json={"text": "x"}).status_code == 429
    api._nl_hits.clear()
    assert client.post("/nl", json={"text": "a" * 5000}).status_code == 413


def test_cors_header():
    r = client.options("/design", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    r = client.options("/design", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") is None
