import json

from analysis.diff import load_snapshot
from export.exporter import cabling_guide, export_design


def test_export_files(designs, tmp_path):
    r = designs["metro_man"]
    paths = export_design(r, tmp_path)
    names = {p.name for p in paths}
    assert {"design.json", "design_report.md", "cabling_guide.md"} <= names
    assert {f"{d.hostname}.cfg" for d in r.devices} <= names
    report = (tmp_path / "design_report.md").read_text(encoding="utf-8")
    for heading in ("## Physical media", "## IP plan", "## Architectural rationale", "## Verification",
                    "## Security findings", "## Single points of failure", "## Bill of materials"):
        assert heading in report
    assert "Verification: **PASS**" in report
    assert load_snapshot(json.loads((tmp_path / "design.json").read_text(encoding="utf-8"))).input == r.input


def test_cabling_guide_rows(designs):
    r = designs["campus_lan"]
    g = cabling_guide(r)
    rows = [x for x in g.splitlines() if x.startswith("| ") and not x.startswith("| #")]
    assert len(rows) == len(r.cables)
    assert "350 m" in g and "in-building patch" in g
