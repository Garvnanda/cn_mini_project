"""Run from backend with its Python; diagnostic output contains generated configs only."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from engine.planner import design
from verify.batfish_adapter import run_batfish
result = design(json.loads((Path(__file__).resolve().parents[1] / "backend/presets/global_wan.json").read_text()))
report = run_batfish(result)
print(report.model_dump_json(indent=2))
sys.exit(0 if report.status == "ok" else 1)
