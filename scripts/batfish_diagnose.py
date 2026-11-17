"""Run from backend with its Python; diagnostic output contains generated configs only."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from engine.planner import design
from verify.batfish_adapter import run_batfish
from pybatfish.client.session import Session
result = design(json.loads(Path("presets/global_wan.json").read_text()))
report = run_batfish(result)
print(report.message)
b = Session(host="localhost")
b.set_network("netarchitect")
b.set_snapshot("design")
for name in ["parseWarning", "ipsecSessionStatus", "initIssues"]:
    print(name)
    print(getattr(b.q, name)().answer().frame().to_string(index=False))
