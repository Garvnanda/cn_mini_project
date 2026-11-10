"""Phase 13: optional cross-check against Batfish (local Docker only, D-005).

Runs only when BATFISH_HOST is set and pybatfish is installed (requirements-batfish.txt).
Otherwise returns status "skipped"; the built-in verifier stays the source of truth.

UNVERIFIED: written against pybatfish 2026.9.17 signatures (Session, init_snapshot, HeaderConstraints),
but not yet run against a live Batfish server. The question names (`undefinedReferences`,
`traceroute`) and disposition strings follow the Batfish docs.
"""

import os
import tempfile
from pathlib import Path

from pydantic import BaseModel

from engine.configgen import render_all
from engine.models import DesignResult
from verify.verifier import build_simulator, verify

SUCCESS = {"ACCEPTED", "DELIVERED_TO_SUBNET", "EXITS_NETWORK"}


class Comparison(BaseModel):
    src: str
    dst: str
    proto: str
    ours: str
    batfish: str
    agree: bool


class BatfishReport(BaseModel):
    status: str  # skipped | ok | error
    message: str
    undefined_references: list[str] = []
    comparisons: list[Comparison] = []

    @property
    def disagreements(self) -> list[Comparison]:
        return [c for c in self.comparisons if not c.agree]


def availability() -> tuple[bool, str]:
    host = os.environ.get("BATFISH_HOST", "").strip()
    if not host:
        return False, "Batfish: not available (BATFISH_HOST not set), using built-in verifier"
    try:
        import pybatfish  # noqa: F401
    except ImportError:
        return False, "Batfish: pybatfish not installed (pip install -r requirements-batfish.txt)"
    return True, host


def run_batfish(result: DesignResult, configs: dict[str, str] | None = None) -> BatfishReport:
    ok, info = availability()
    if not ok:
        return BatfishReport(status="skipped", message=info)
    from pybatfish.client.session import Session
    from pybatfish.datamodel.flow import HeaderConstraints

    configs = configs if configs is not None else render_all(result)
    ours = verify(result, configs)
    sim, _ = build_simulator(result, configs)
    try:
        bf = Session(host=info)
        bf.set_network("netarchitect")
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / "configs"
            cfg_dir.mkdir()
            for host, text in configs.items():
                (cfg_dir / f"{host}.cfg").write_text(text, encoding="utf-8")
            bf.init_snapshot(tmp, name="design", overwrite=True)

        undef = bf.q.undefinedReferences().answer().frame()
        refs = [f"{r['File_Name']}: {r['Struct_Type']} {r['Ref_Name']}" for _, r in undef.iterrows()]

        hosts = {h.segment: h for h in sim.hosts}
        comps = []
        for p in ours.probes:
            src = hosts[p.src]
            gw = sim._gateway_owner(src)
            if gw is None:
                continue
            hc = HeaderConstraints(srcIps=src.ip, dstIps=hosts[p.dst].ip, ipProtocols=[p.proto.upper()],
                                   dstPorts=str(p.port) if p.port else None)
            frame = bf.q.traceroute(startLocation=f"@enter({gw[0].lower()}[{gw[1]}])", headers=hc).answer().frame()
            disp = {t.disposition for t in frame.iloc[0]["Traces"]} if len(frame) else {"NO_RESULT"}
            theirs = "delivered" if disp & SUCCESS else "dropped"
            comps.append(Comparison(src=p.src, dst=p.dst, proto=p.proto, ours=p.actual,
                                    batfish=theirs, agree=theirs == p.actual))
    except Exception as e:  # network / server errors must not break the design flow
        return BatfishReport(status="error", message=f"Batfish error: {type(e).__name__}: {e}")
    bad = sum(not c.agree for c in comps)
    return BatfishReport(status="ok", message=f"Batfish: {len(comps)} flows compared, {bad} disagreement(s)",
                         undefined_references=refs, comparisons=comps)
