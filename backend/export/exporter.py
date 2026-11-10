"""Phase 18: write a design to disk: per-device .cfg, design.json, design_report.md, cabling_guide.md."""

import json
from pathlib import Path

from analysis.bom import Bom, build_bom
from analysis.diff import snapshot
from analysis.lint import LintReport, lint_configs
from analysis.whatif import SpofReport, spof_analysis
from engine.configgen import render_all
from engine.models import DesignResult
from engine.rationale import RationaleLog
from verify.verifier import VerificationReport, verify


def cabling_guide(result: DesignResult) -> str:
    """Port-to-port table for building the lab by hand (Packet Tracer has no importable format, D-010)."""
    links = {ln.key: ln for ln in result.input.links}
    rows = ["# Cabling Guide", "", "| # | Device A | Port A | Device B | Port B | Kind | Media | Transceiver | Length |",
            "|---|---|---|---|---|---|---|---|---|"]
    for n, c in enumerate(result.cables, start=1):
        length = f"{links[c.link].distance_m:g} m" if c.link else "in-building patch"
        rows.append(f"| {n} | {c.a} | {c.a_if} | {c.b} | {c.b_if} | {c.kind} | {c.media} | {c.transceiver} | {length} |")
    return "\n".join(rows) + "\n"


def report_markdown(result: DesignResult, ver: VerificationReport, lint: LintReport, bom: Bom, spof: SpofReport) -> str:
    inp = result.input
    out = [f"# NetArchitect Design Report: {inp.profile.value}", "",
           "## Summary", "",
           f"- Root prefix: `{inp.root_prefix}`",
           f"- Sites: {', '.join(f'{s.name} ({s.kind.value})' for s in inp.sites)}",
           f"- Endpoints: {sum(s.hosts for s in inp.segments)}",
           f"- Topology: {', '.join(f'{k}: {v}' for k, v in result.tiers.items())}",
           f"- Routing: {result.routing.protocol}",
           f"- Devices: {len(result.devices)}, cables: {len(result.cables)}, subnets: {len(result.subnets)}",
           f"- Verification: **{'PASS' if ver.passed else 'FAIL'}**",
           f"- Security score: **{lint.score}/100**",
           f"- Resilience score: **{spof.score}/100**",
           f"- Estimated capex: {bom.currency} {bom.capex:,.0f} (placeholder prices), monthly WAN: {bom.currency} {bom.monthly:,.0f}",
           "", "## Physical media", "", "| Link | Distance | Media | Transceiver |", "|---|---|---|---|"]
    out += [f"| {m.link} | {m.distance_m:g} m | {m.media} | {m.transceiver} |" for m in result.media]
    out += ["", "## IP plan", "", "| Subnet | Unit | VLAN | Network | Mask | Wildcard | Gateway | Broadcast | Usable | Util % |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    out += [f"| {s.name} | {s.unit or ''} | {s.vlan or ''} | {s.network}/{s.prefix} | {s.mask} | {s.wildcard} | "
            f"{s.gateway or '-'} | {s.broadcast or '-'} | {s.usable_hosts} | {s.utilization_pct} |" for s in result.subnets]
    log = RationaleLog()
    log.extend(result.rationale)
    out += ["", log.to_markdown().replace("# Architectural Rationale", "## Architectural rationale").replace("\n## ", "\n### ")]
    out += ["## Verification", "", "```", ver.summary(), "```", ""]
    out += ["## Security findings", "", "| Device | Score | Rule | Severity | Where | Fix |", "|---|---|---|---|---|---|"]
    for d in lint.devices:
        for f in d.findings:
            out.append(f"| {d.hostname} | {d.score} | {f.rule} {f.title} | {f.severity} | {f.where} | {f.fix} |")
    out += ["", "## Single points of failure", ""]
    out += [f"- {r.text}" for r in spof.rationale]
    out += ["", "## Bill of materials", "", f"_{bom.disclaimer}_", "",
            "| Item | Qty | Unit | Unit price | Total | Because of |", "|---|---|---|---|---|---|"]
    out += [f"| {x.item} | {x.qty:g} | {x.unit} | {x.unit_price:,.0f} | {x.total:,.0f} | {x.rule_id} |" for x in bom.lines]
    out += [f"- {a.text}" for a in bom.alternatives]
    return "\n".join(out) + "\n"


def export_design(result: DesignResult, out_dir: str | Path) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    configs = render_all(result)
    paths = []
    for host, text in configs.items():
        p = out / f"{host}.cfg"
        p.write_text(text, encoding="utf-8")
        paths.append(p)
    ver, lint, bom, spof = verify(result, configs), lint_configs(configs), build_bom(result), spof_analysis(result)
    files = {
        "design.json": json.dumps(snapshot(result), indent=2),
        "design_report.md": report_markdown(result, ver, lint, bom, spof),
        "cabling_guide.md": cabling_guide(result),
    }
    for name, text in files.items():
        p = out / name
        p.write_text(text, encoding="utf-8")
        paths.append(p)
    return paths
