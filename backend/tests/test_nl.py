import json

import httpx
import pytest

from nl import extract, fallback, openrouter
from tests.conftest import load


def mock_client(handler):
    return httpx.Client(base_url=openrouter.BASE_URL, transport=httpx.MockTransport(handler))


def ok_response(content: str):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def test_openrouter_valid_json(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model")
    seen = {}

    def handler(req: httpx.Request):
        seen["auth"] = req.headers["Authorization"]
        seen["body"] = json.loads(req.content)
        return ok_response(json.dumps(load("metro_man")))

    r = extract("metro network", mock_client(handler))
    assert r.source == "openrouter" and r.valid
    assert seen["auth"] == "Bearer test-key" and seen["body"]["model"] == "some/model"
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert "Do NOT choose cables" in seen["body"]["messages"][0]["content"]


def test_openrouter_invalid_fields_reported_not_fixed(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    bad = load("metro_man")
    bad["segments"][0]["vlan"] = 1
    r = extract("x", mock_client(lambda req: ok_response(json.dumps(bad))))
    assert r.source == "openrouter" and not r.valid
    assert r.input["segments"][0]["vlan"] == 1  # never auto-corrected
    assert any("vlan" in e["loc"] for e in r.errors)


@pytest.mark.parametrize("handler", [
    lambda req: httpx.Response(500),
    lambda req: ok_response("not json"),
    lambda req: httpx.Response(401, text="bad key"),
])
def test_openrouter_failure_falls_back(monkeypatch, handler):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    r = extract("HQ and 2 branches at 22 km and 35 km, 450 users", mock_client(handler))
    assert r.source == "fallback" and "OpenRouter failed" in r.note and r.valid


def test_retries_then_succeeds(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        return httpx.Response(503) if calls["n"] < 2 else ok_response(json.dumps(load("campus_lan")))

    assert extract("x", mock_client(handler)).source == "openrouter" and calls["n"] == 2


def test_no_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    r = extract("small office with 60 users")
    assert r.source == "fallback" and "not set" in r.note


def test_fallback_campus():
    d, assumptions, missing = fallback.parse(
        "3-building campus, 1600 users, PoE APs, guest wifi, buildings 250 m and 380 m from main, redundant core")
    assert d["profile"] == "campus_lan" and d["resiliency"] == "high"
    assert [ln["distance_m"] for ln in d["links"]] == [250, 380]
    assert sum(s["hosts"] for s in d["segments"]) == 1600
    assert any("PoE" in m for m in missing) and any("guest" in m for m in missing)
    assert any("10.0.0.0/16" in a for a in assumptions)


def test_fallback_never_invents_distance():
    d, _, missing = fallback.parse("2 buildings with 100 users")
    assert d["links"] == [] and any("distance" in m for m in missing)


def test_fallback_metro_latency_and_wan():
    d, _, _ = fallback.parse("HQ plus 2 branches at 22 km and 35 km, 450 users, under 5 ms latency")
    assert d["profile"] == "metro_man" and all(ln["max_latency_ms"] == 5 for ln in d["links"])
    d, _, missing = fallback.parse("4 cities and a cloud VPC over IPsec, 2000 IoT, 1150 km, 1740 km, 4150 km")
    assert d["profile"] == "global_wan" and len(d["sites"]) == 5
    assert {ln["transport"] for ln in d["links"]} == {"internet"}
    assert any("cloud" in m for m in missing)
