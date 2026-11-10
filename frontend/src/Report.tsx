import { download } from "./api";
import { Topology } from "./Topology";
import type { Bundle } from "./types";

export function Report({ bundle }: { bundle: Bundle }) {
  const d = bundle.design;
  const name = d.input.profile;
  const fmt = (n: number) => n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
  return (
    <div className="report">
      <div className="row no-print">
        <button className="primary" onClick={() => window.print()}>Print / save as PDF</button>
        <button onClick={() => download("zip", d.input, `${name}.zip`)}>Download configs + reports (.zip)</button>
        <button onClick={() => download("report", d.input, `${name}_report.md`)}>Report (.md)</button>
        <button onClick={() => download("json", d.input, `${name}_design.json`)}>Design (.json)</button>
        <button onClick={() => download("cabling", d.input, `${name}_cabling.md`)}>Cabling guide</button>
      </div>
      <h1>NetArchitect design report: {name}</h1>
      <ul>
        <li>Root prefix: <code>{d.input.root_prefix}</code></li>
        <li>Topology: {Object.entries(d.tiers).map(([k, v]) => `${k}: ${v}`).join(", ")}</li>
        <li>Routing: {d.routing.protocol}</li>
        <li>{d.devices.length} devices, {d.cables.length} cables, {d.subnets.length} subnets</li>
        <li>Verification: <b>{bundle.verification.passed ? "PASS" : "FAIL"}</b> · Security {bundle.lint.score}/100 · Resilience {bundle.spof.score}/100</li>
        <li>Estimated capex: {bundle.bom.currency} {fmt(bundle.bom.capex)} (placeholder prices)</li>
      </ul>
      <Topology nodes={bundle.graph.nodes} edges={bundle.graph.edges} spof={[...bundle.spof.spof_devices, ...bundle.spof.spof_cables]} />
      <h2>Physical media</h2>
      <table><thead><tr><th>Link</th><th>Distance</th><th>Media</th><th>Transceiver</th></tr></thead>
        <tbody>{d.media.map((m) => <tr key={m.link}><td>{m.link}</td><td>{m.distance_m} m</td><td>{m.media}</td><td>{m.transceiver}</td></tr>)}</tbody></table>
      <h2>IP plan</h2>
      <table><thead><tr><th>Subnet</th><th>Network</th><th>Gateway</th><th>Usable</th><th>Util %</th></tr></thead>
        <tbody>{d.subnets.map((s) => <tr key={s.name}><td>{s.name}</td><td>{s.network}/{s.prefix}</td><td>{s.gateway ?? "–"}</td><td>{s.usable_hosts}</td><td>{s.utilization_pct}</td></tr>)}</tbody></table>
      <h2>Architectural rationale</h2>
      <ol>{d.rationale.map((r, i) => <li key={i}><code>{r.rule_id}</code> {r.text} <i>({r.standard_ref})</i></li>)}</ol>
      <h2>Verification</h2>
      <ul>{bundle.verification.checks.map((c) => <li key={c.name}>{c.passed ? "✔" : "✘"} {c.name}</li>)}</ul>
      <h2>Bill of materials</h2>
      <table><thead><tr><th>Item</th><th>Qty</th><th>Total</th><th>Because of</th></tr></thead>
        <tbody>{bundle.bom.lines.map((x) => <tr key={x.item}><td>{x.item}</td><td>{x.qty}</td><td>{fmt(x.total)}</td><td>{x.rule_id}</td></tr>)}</tbody></table>
      <h2>Configurations</h2>
      {Object.entries(bundle.configs).map(([h, c]) => <section key={h} className="cfg-print"><h3>{h}</h3><pre className="config">{c}</pre></section>)}
    </div>
  );
}
