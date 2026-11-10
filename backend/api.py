"""Phase 20: HTTP API. Thin shell over the engine (no design logic here)."""

import io
import os
import tempfile
import time
import zipfile
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from engine.env import load_env

load_env()  # backend/.env (OPENROUTER_API_KEY, CORS_ORIGINS, ...) before reading settings

from analysis.bom import build_bom  # noqa: E402
from analysis.diff import diff as design_diff
from analysis.lint import lint_configs, lint_text
from analysis.whatif import simulate_failure, spof_analysis
from engine.configgen import render_all
from engine.errors import NetArchError
from engine.models import DesignResult
from engine.planner import design as run_design
from engine.topology import graph
from export.exporter import cabling_guide, export_design, report_markdown
from nl import extract
from verify.batfish_adapter import availability
from verify.verifier import build_simulator, verify

PRESETS = Path(__file__).resolve().parent / "presets"
NL_RATE_PER_MIN = int(os.environ.get("NL_RATE_PER_MIN", "10"))
ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

app = FastAPI(title="NetArchitect API", version="1.0.0",
              description="Explainable network design, Cisco IOS generation and self-verification.")
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"])


@app.exception_handler(NetArchError)
async def netarch_error(_: Request, e: NetArchError) -> JSONResponse:
    return JSONResponse(status_code=422, content=e.to_dict())


# ---------------------------------------------------------------- request models
class TraceReq(BaseModel):
    input: dict[str, Any]
    src: str  # segment name or IP
    dst: str
    proto: str = "icmp"
    port: int | None = None


class WhatIfReq(BaseModel):
    input: dict[str, Any]
    links: list[str] = []
    nodes: list[str] = []


class LintReq(BaseModel):
    text: str | None = None
    input: dict[str, Any] | None = None


class DiffReq(BaseModel):
    a: dict[str, Any]
    b: dict[str, Any]


class NLReq(BaseModel):
    text: str


def _design(data: dict[str, Any]) -> DesignResult:
    return run_design(data)


# ---------------------------------------------------------------- endpoints
@app.get("/health")
def health() -> dict:
    ok, msg = availability()
    return {"status": "ok", "batfish": msg if not ok else f"available at {msg}"}


@app.get("/presets")
def presets() -> list[dict]:
    import json
    out = []
    for p in sorted(PRESETS.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        out.append({"name": p.stem, "profile": d["profile"], "sites": len(d["sites"]),
                    "endpoints": sum(s["hosts"] for s in d["segments"])})
    return out


@app.get("/presets/{name}")
def preset(name: str) -> dict:
    import json
    p = PRESETS / f"{name}.json"
    if not p.exists() or p.parent != PRESETS:
        raise HTTPException(404, f"unknown preset '{name}'")
    return json.loads(p.read_text(encoding="utf-8"))


@app.post("/design")
def design(data: dict[str, Any] = Body(...)) -> dict:
    """Everything the dashboard needs in one round trip (Render free tier cold starts are slow)."""
    r = _design(data)
    configs = render_all(r)
    return {
        "design": r.model_dump(mode="json"),
        "graph": graph(r.devices, r.cables),
        "configs": configs,
        "verification": verify(r, configs).model_dump(mode="json"),
        "lint": lint_configs(configs).model_dump(mode="json"),
        "bom": build_bom(r).model_dump(mode="json"),
        "spof": spof_analysis(r).model_dump(mode="json"),
    }


@app.post("/verify")
def verify_ep(data: dict[str, Any] = Body(...)) -> dict:
    return verify(_design(data)).model_dump(mode="json")


@app.post("/trace")
def trace(req: TraceReq) -> dict:
    sim, _ = build_simulator(_design(req.input))
    by_seg = {h.segment: h.ip for h in sim.hosts}
    t = sim.trace(by_seg.get(req.src, req.src), by_seg.get(req.dst, req.dst), req.proto, req.port)
    return t.model_dump(mode="json")


@app.post("/whatif")
def whatif(req: WhatIfReq) -> dict:
    r = _design(req.input)
    imp = simulate_failure(r, links=req.links, nodes=req.nodes)
    return {**imp.model_dump(mode="json"), "survives": imp.survives}


@app.post("/spof")
def spof(data: dict[str, Any] = Body(...)) -> dict:
    return spof_analysis(_design(data)).model_dump(mode="json")


@app.post("/lint")
def lint(req: LintReq) -> dict:
    if req.text is not None:
        return lint_text(req.text).model_dump(mode="json")
    if req.input is not None:
        return lint_configs(render_all(_design(req.input))).model_dump(mode="json")
    raise HTTPException(400, "send either 'text' (IOS config) or 'input' (design input)")


@app.post("/bom")
def bom(data: dict[str, Any] = Body(...)) -> dict:
    return build_bom(_design(data)).model_dump(mode="json")


@app.post("/diff")
def diff(req: DiffReq) -> dict:
    d = design_diff(_design(req.a), _design(req.b))
    return {**d.model_dump(mode="json"), "empty": d.empty}


_nl_hits: dict[str, deque] = defaultdict(deque)


@app.post("/nl")
def nl(req: NLReq, request: Request) -> dict:
    """Natural language -> design input JSON (never a design decision, D-004). Rate limited per client."""
    ip = request.client.host if request.client else "unknown"
    now, window = time.monotonic(), _nl_hits[ip]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= NL_RATE_PER_MIN:
        raise HTTPException(429, f"rate limit: {NL_RATE_PER_MIN} requests per minute")
    window.append(now)
    if len(req.text) > 4000:
        raise HTTPException(413, "text too long (max 4000 characters)")
    return extract(req.text).model_dump(mode="json")


@app.post("/export/{fmt}")
def export(fmt: str, data: dict[str, Any] = Body(...)) -> Response:
    r = _design(data)
    name = r.input.profile.value
    if fmt == "json":
        from analysis.diff import snapshot
        import json
        return Response(json.dumps(snapshot(r), indent=2), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{name}_design.json"'})
    if fmt == "report":
        configs = render_all(r)
        text = report_markdown(r, verify(r, configs), lint_configs(configs), build_bom(r), spof_analysis(r))
        return Response(text, media_type="text/markdown",
                        headers={"Content-Disposition": f'attachment; filename="{name}_report.md"'})
    if fmt == "cabling":
        return Response(cabling_guide(r), media_type="text/markdown",
                        headers={"Content-Disposition": f'attachment; filename="{name}_cabling.md"'})
    if fmt == "zip":
        buf = io.BytesIO()
        with tempfile.TemporaryDirectory() as tmp:
            export_design(r, tmp)
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for p in sorted(Path(tmp).iterdir()):
                    z.write(p, arcname=f"{name}/{p.name}")
        return Response(buf.getvalue(), media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="{name}.zip"'})
    raise HTTPException(404, f"unknown export format '{fmt}' (zip, json, report, cabling)")
