import os

from engine.env import load_env


def test_load_env(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text('# comment\nNA_A=1\nexport NA_B="two words"\nNA_C=\'x\'\nNA_KEEP=file\nbad line\n', encoding="utf-8")
    for k in ("NA_A", "NA_B", "NA_C"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("NA_KEEP", "real")
    assert sorted(load_env(f)) == ["NA_A", "NA_B", "NA_C"]
    assert (os.environ["NA_A"], os.environ["NA_B"], os.environ["NA_C"]) == ("1", "two words", "x")
    assert os.environ["NA_KEEP"] == "real"  # real env wins
    for k in ("NA_A", "NA_B", "NA_C"):
        monkeypatch.delenv(k)


def test_missing_file(tmp_path):
    assert load_env(tmp_path / "nope") == []
