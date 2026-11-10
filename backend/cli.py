"""Phase 19: `netarch` command-line interface. Thin shell over the engine (no design logic here)."""

import json
import sys
from pathlib import Path

import typer

from engine.env import load_env

load_env()

from analysis.bom import build_bom
from analysis.diff import diff as design_diff
from analysis.lint import lint_configs, lint_text
from analysis.whatif import simulate_failure, spof_analysis
from engine import errors as E
from engine.configgen import render_all
from engine.models import DesignResult
from engine.planner import design as run_design
from engine.rationale import RationaleLog
from export.exporter import export_design
from verify.verifier import build_simulator, verify

for _stream in (sys.stdout, sys.stderr):  # Windows pipes default to cp1252; rationale text uses ≤, µ, →
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

app = typer.Typer(help="NetArchitect: explainable network design, config generation and verification.",
                  no_args_is_help=True, add_completion=False)
PRESETS = Path(__file__).resolve().parent / "presets"

EXIT = {  # most specific first
    E.PhysicalDistanceViolationError: 4,
    E.AddressSpaceExhaustedError: 5,
    E.TopologyError: 6,
    E.InvalidPrefixError: 3,
    E.InvalidParameterError: 2,
    E.NetArchError: 2,
}


def _fail(err: E.NetArchError) -> None:
    typer.echo(f"error [{type(err).__name__}]: {err.message}", err=True)
    code = next(c for cls, c in EXIT.items() if isinstance(err, cls))
    raise typer.Exit(code)


def load_design(target: str) -> DesignResult:
    """TARGET = preset name (campus_lan, metro_man, global_wan) or a path to a JSON input."""
    path = PRESETS / f"{target}.json" if (PRESETS / f"{target}.json").exists() else Path(target)
    if not path.exists():
        typer.echo(f"error: '{target}' is not a preset ({', '.join(p.stem for p in PRESETS.glob('*.json'))}) "
                   f"or an existing file", err=True)
        raise typer.Exit(2)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        typer.echo(f"error: {path} is not valid JSON: {e}", err=True)
        raise typer.Exit(2)
    try:
        return run_design(data)
    except E.NetArchError as e:
        _fail(e)


@app.command()
def design(target: str, export: Path = typer.Option(None, "--export", "-o", help="Write configs + reports here")):
    """Run the full design and print a summary."""
    r = load_design(target)
    typer.echo(f"Profile:  {r.input.profile.value}")
    typer.echo(f"Topology: {', '.join(f'{k}={v}' for k, v in r.tiers.items())}")
    typer.echo(f"Routing:  {r.routing.protocol}")
    typer.echo(f"Devices:  {len(r.devices)}  cables: {len(r.cables)}  subnets: {len(r.subnets)}")
    for m in r.media:
        typer.echo(f"  {m.link}: {m.media} ({m.transceiver})")
    if export:
        paths = export_design(r, export)
        typer.echo(f"Exported {len(paths)} files to {export}")


@app.command()
def explain(target: str, domain: str = typer.Option(None, help="Only one domain: L1, TOPO, L2, VLSM, ROUTE, ACL")):
    """Print every decision with its justification."""
    r = load_design(target)
    log = RationaleLog()
    log.extend([x for x in r.rationale if domain is None or x.domain == domain.upper()])
    typer.echo(log.to_markdown())


@app.command("verify")
def verify_cmd(target: str):
    """Parse the generated configs back and prove reachability + policy intent."""
    rep = verify(load_design(target))
    typer.echo(rep.summary())
    for c in rep.checks:
        for d in c.details[:10] if not c.passed else []:
            typer.echo(f"    {d}")
    raise typer.Exit(0 if rep.passed else 1)


@app.command()
def trace(target: str, src: str, dst: str, proto: str = "icmp", port: int = typer.Option(None)):
    """Trace a packet hop by hop. SRC/DST = segment name or IP address."""
    r = load_design(target)
    sim, _ = build_simulator(r)
    by_seg = {h.segment: h.ip for h in sim.hosts}
    s, d = by_seg.get(src, src), by_seg.get(dst, dst)
    t = sim.trace(s, d, proto, port)
    typer.echo(f"{t.src} -> {t.dst} {proto}{' ' + str(port) if port else ''}: {t.outcome.upper()} ({t.reason})")
    for n, h in enumerate(t.hops, start=1):
        typer.echo(f"  {n}. {h.device} [{h.in_if or '-'} -> {h.out_if or '-'}] {h.action}: {h.detail}")
    raise typer.Exit(0 if t.outcome == "delivered" else 1)


@app.command()
def fail(target: str, link: list[str] = typer.Option([], help="DEV--DEV or DEV:IF--DEV:IF (repeatable)"),
         node: list[str] = typer.Option([], help="Device hostname (repeatable)")):
    """What-if: fail links/devices and show broken and rerouted flows."""
    r = load_design(target)
    if not link and not node:
        rep = spof_analysis(r)
        for x in rep.rationale:
            typer.echo(f"- {x.text}")
        return
    try:
        imp = simulate_failure(r, links=link, nodes=node)
    except E.NetArchError as e:
        _fail(e)
    typer.echo(f"Failed: {', '.join(imp.failed)}")
    typer.echo(f"Broken flows: {len(imp.broken)}  rerouted: {len(imp.rerouted)}  unaffected: {imp.unaffected}")
    for b in imp.broken[:20]:
        typer.echo(f"  BROKEN {b.src} -> {b.dst}: {b.reason}")
    for x in imp.rerouted[:10]:
        typer.echo(f"  reroute {x.src} -> {x.dst}: {' > '.join(x.after_path)}")
    for x in imp.rationale:
        typer.echo(f"- {x.text}")
    raise typer.Exit(0 if imp.survives else 1)


@app.command()
def lint(target: str):
    """Security posture: TARGET = a .cfg/.txt IOS file, or a preset/design JSON."""
    p = Path(target)
    if p.suffix.lower() in (".cfg", ".txt", ".ios") and p.exists():
        devs = [lint_text(p.read_text(encoding="utf-8"))]
        score = devs[0].score
    else:
        rep = lint_configs(render_all(load_design(target)))
        devs, score = rep.devices, rep.score
    typer.echo(f"Security score: {score}/100")
    for d in devs:
        for f in d.findings:
            typer.echo(f"  [{f.severity}] {d.hostname} {f.where}: {f.rule} {f.title} -> fix: {f.fix}")


@app.command()
def bom(target: str):
    """Bill of materials with placeholder INR prices."""
    b = build_bom(load_design(target))
    for x in b.lines:
        typer.echo(f"  {x.item:<34} {x.qty:>8g} {x.unit:<14} {x.total:>14,.0f}  ({x.rule_id})")
    typer.echo(f"Capex: {b.currency} {b.capex:,.0f}   Monthly WAN: {b.currency} {b.monthly:,.0f}")
    for a in b.alternatives:
        typer.echo(f"- {a.text}")
    typer.echo(f"Note: {b.disclaimer}")


@app.command()
def diff(a: str, b: str):
    """Compare two designs: decisions, IP plan and config lines."""
    d = design_diff(load_design(a), load_design(b))
    if d.empty:
        typer.echo("No differences.")
        return
    for c in d.decisions:
        typer.echo(f"[{c.change}] {c.key}")
        for t in c.old:
            typer.echo(f"   - {t}")
        for t in c.new:
            typer.echo(f"   + {t}")
    for s in d.subnets:
        typer.echo(f"[subnet {s.change}] {s.name}: {s.old} -> {s.new}")
    for h in d.devices_added:
        typer.echo(f"[device added] {h}")
    for h in d.devices_removed:
        typer.echo(f"[device removed] {h}")
    typer.echo(f"{len(d.configs)} config(s) changed: {', '.join(d.configs)}")


@app.command()
def nl(text: str, out: Path = typer.Option(None, "--out", "-o", help="Save the extracted input JSON here")):
    """Plain English -> design input JSON (extraction only; review it, then run `design` on the file)."""
    from nl import extract
    r = extract(text)
    typer.echo(f"Source: {r.source}. {r.note}")
    for a in r.assumptions:
        typer.echo(f"  assumption: {a}")
    for m in r.missing:
        typer.echo(f"  missing:    {m}")
    for e in r.errors:
        typer.echo(f"  invalid:    {e.get('loc')}: {e.get('msg')}")
    body = json.dumps(r.input, indent=2)
    if out:
        out.write_text(body, encoding="utf-8")
        typer.echo(f"Saved to {out}. Review it, then: python cli.py design {out}")
    else:
        typer.echo(body)
    raise typer.Exit(0 if r.valid else 1)


if __name__ == "__main__":
    app()
