import os

import pytest

from verify.batfish_adapter import availability, run_batfish


def test_skips_cleanly_without_host(designs, monkeypatch):
    monkeypatch.delenv("BATFISH_HOST", raising=False)
    ok, msg = availability()
    assert not ok and "not available" in msg
    rep = run_batfish(designs["campus"])
    assert rep.status == "skipped" and rep.comparisons == []


@pytest.mark.batfish
@pytest.mark.skipif(not os.environ.get("BATFISH_HOST"), reason="needs a running Batfish container")
def test_live_batfish_agrees(designs):
    rep = run_batfish(designs["campus_lan"])
    assert rep.status == "ok", rep.message
    assert not rep.disagreements
