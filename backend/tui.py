"""Phase 22: terminal dashboard (Textual). Thin shell over the engine. Run: python tui.py"""

import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import (
    Button, DataTable, Footer, Header, Markdown, Select, Static, TabbedContent, TabPane, TextArea,
)

from engine.env import load_env

load_env()

from analysis.bom import build_bom  # noqa: E402
from analysis.lint import lint_configs
from analysis.whatif import cable_id, simulate_failure, spof_analysis
from engine.configgen import render_all
from engine.errors import NetArchError
from engine.models import DesignResult
from engine.planner import design
from engine.rationale import RationaleLog
from verify.verifier import verify

PRESETS = Path(__file__).resolve().parent / "presets"


class NetArchTUI(App):
    TITLE = "NetArchitect"
    CSS = """
    #bar { height: 3; }
    #bar Select { width: 40; }
    #status { padding: 0 1; }
    DataTable { height: 1fr; }
    TextArea { height: 1fr; }
    """
    BINDINGS = [("q", "quit", "Quit"), ("r", "run", "Re-run design")]

    def __init__(self) -> None:
        super().__init__()
        self.result: DesignResult | None = None
        self.configs: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        names = sorted(p.stem for p in PRESETS.glob("*.json"))
        with Horizontal(id="bar"):
            yield Select([(n, n) for n in names], value=names[0], id="preset", allow_blank=False)
            yield Button("Design", id="run", variant="primary")
            yield Static("", id="status")
        with TabbedContent(id="tabs"):
            with TabPane("Decisions", id="t-dec"):
                yield Markdown(id="decisions")
            with TabPane("IP Plan", id="t-ip"):
                yield DataTable(id="ipplan")
            with TabPane("Configs", id="t-cfg"):
                yield Select([], id="device", prompt="device")
                yield TextArea(read_only=True, id="config")
            with TabPane("Verify", id="t-ver"):
                yield DataTable(id="verify")
            with TabPane("What-if", id="t-wi"):
                with Horizontal(id="wibar"):
                    yield Select([], id="element", prompt="link or device to fail")
                    yield Button("Fail it", id="fail", variant="warning")
                yield Markdown(id="whatif")
            with TabPane("BOM", id="t-bom"):
                yield DataTable(id="bom")
            with TabPane("Lint", id="t-lint"):
                yield DataTable(id="lint")
        yield Footer()

    def on_mount(self) -> None:
        self.action_run()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            self.action_run()
        elif event.button.id == "fail":
            self.run_failure()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "device" and event.value in self.configs:
            self.query_one("#config", TextArea).text = self.configs[event.value]

    def action_run(self) -> None:
        name = self.query_one("#preset", Select).value
        status = self.query_one("#status", Static)
        try:
            self.result = design(json.loads((PRESETS / f"{name}.json").read_text(encoding="utf-8")))
        except NetArchError as e:
            status.update(f"[red]{type(e).__name__}: {e.message}[/]")
            return
        r = self.result
        self.configs = render_all(r)
        ver = verify(r, self.configs)
        spof = spof_analysis(r)
        status.update(f"{r.routing.protocol} | {len(r.devices)} devices | "
                      f"verify {'PASS' if ver.passed else 'FAIL'} | resilience {spof.score}")

        log = RationaleLog()
        log.extend(r.rationale)
        self.query_one("#decisions", Markdown).update(log.to_markdown())

        ip = self.query_one("#ipplan", DataTable)
        ip.clear(columns=True)
        ip.add_columns("Subnet", "Unit", "VLAN", "Network", "Mask", "Gateway", "Usable", "Util %")
        for s in r.subnets:
            ip.add_row(s.name, s.unit or "", str(s.vlan or ""), f"{s.network}/{s.prefix}", s.mask,
                       s.gateway or "-", str(s.usable_hosts), str(s.utilization_pct))

        dev = self.query_one("#device", Select)
        dev.set_options([(h, h) for h in self.configs])
        self.query_one("#config", TextArea).text = next(iter(self.configs.values()))

        vt = self.query_one("#verify", DataTable)
        vt.clear(columns=True)
        vt.add_columns("Check / probe", "Result", "Detail")
        for c in ver.checks:
            vt.add_row(c.name, "ok" if c.passed else "FAIL", (c.details or [""])[0])
        for p in ver.probes:
            vt.add_row(f"{p.src} -> {p.dst} {p.proto}{' ' + str(p.port) if p.port else ''}",
                       "ok" if p.expected == p.actual else "FAIL", f"{p.actual}: {p.reason}")

        el = self.query_one("#element", Select)
        el.set_options([(cable_id(c), "link:" + cable_id(c)) for c in r.cables if c.kind != "trunk"]
                       + [(d.hostname, "node:" + d.hostname) for d in r.devices if d.role != "access"])
        self.query_one("#whatif", Markdown).update(
            "\n".join(f"- {x.text}" for x in spof.rationale) or "No single points of failure.")

        bt = self.query_one("#bom", DataTable)
        bt.clear(columns=True)
        bom = build_bom(r)
        bt.add_columns("Item", "Qty", "Unit", "Total", "Because of")
        for x in bom.lines:
            bt.add_row(x.item, f"{x.qty:g}", x.unit, f"{x.total:,.0f}", x.rule_id)
        bt.add_row("CAPEX (placeholder prices)", "", bom.currency, f"{bom.capex:,.0f}", "")

        lt = self.query_one("#lint", DataTable)
        lt.clear(columns=True)
        rep = lint_configs(self.configs)
        lt.add_columns("Device", "Score", "Rule", "Severity", "Where", "Fix")
        for d in rep.devices:
            for f in d.findings:
                lt.add_row(d.hostname, str(d.score), f"{f.rule} {f.title}", f.severity, f.where, f.fix)

    def run_failure(self) -> None:
        val = self.query_one("#element", Select).value
        if not self.result or not isinstance(val, str):
            return
        kind, _, target = val.partition(":")
        imp = simulate_failure(self.result, links=[target] if kind == "link" else [],
                               nodes=[target] if kind == "node" else [])
        lines = [f"## Failed: {', '.join(imp.failed)}",
                 f"**{'Survives' if imp.survives else 'OUTAGE'}**: {len(imp.broken)} broken, "
                 f"{len(imp.rerouted)} rerouted, {imp.unaffected} unaffected", ""]
        lines += [f"- BROKEN {b.src} -> {b.dst}: {b.reason}" for b in imp.broken[:30]]
        lines += [f"- reroute {x.src} -> {x.dst}: {' > '.join(x.after_path)}" for x in imp.rerouted[:30]]
        lines += [f"- {x.text}" for x in imp.rationale]
        self.query_one("#whatif", Markdown).update("\n".join(lines))


if __name__ == "__main__":
    NetArchTUI().run()
