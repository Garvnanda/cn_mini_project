import { useMemo, useState } from "react";
import { api, ApiFailure, saveText } from "./api";
import type { Bom, Bundle, DeviceLint, Rationale, Subnet, Verification } from "./types";

export function Decisions({ rationale }: { rationale: Rationale[] }) {
  const groups = useMemo(() => {
    const g = new Map<string, Rationale[]>();
    for (const r of rationale) g.set(r.domain, [...(g.get(r.domain) ?? []), r]);
    return [...g.entries()];
  }, [rationale]);
  const [filter, setFilter] = useState("");
  return (
    <div>
      <input className="filter" placeholder="Filter decisions…" value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter decisions" />
      {groups.map(([domain, items]) => {
        const shown = items.filter((r) => !filter || (r.text + r.rule_id).toLowerCase().includes(filter.toLowerCase()));
        if (!shown.length) return null;
        return (
          <section key={domain} className="decision-group">
            <h3>{domain} <span className="muted">({shown.length})</span></h3>
            {shown.map((r, i) => (
              <article key={r.rule_id + i} className="card">
                <header><code>{r.rule_id}</code>{r.threshold && <span className="pill">{r.threshold}</span>}</header>
                <p>{r.text}</p>
                <footer className="muted">Ref: {r.standard_ref}</footer>
              </article>
            ))}
          </section>
        );
      })}
    </div>
  );
}

export function IpPlan({ subnets }: { subnets: Subnet[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Subnet</th><th>Unit</th><th>VLAN</th><th>Network</th><th>Mask</th><th>Wildcard</th><th>Gateway</th><th>Broadcast</th><th>Usable</th><th>Utilization</th></tr>
        </thead>
        <tbody>
          {subnets.map((s) => (
            <tr key={s.name}>
              <td>{s.name}</td><td>{s.unit}</td><td>{s.vlan ?? ""}</td>
              <td className="mono">{s.network}/{s.prefix}</td><td className="mono">{s.mask}</td><td className="mono">{s.wildcard}</td>
              <td className="mono">{s.gateway ?? "–"}</td><td className="mono">{s.broadcast ?? "–"}</td><td>{s.usable_hosts}</td>
              <td><div className="bar" title={`${s.utilization_pct}%`}><span style={{ width: `${Math.min(100, s.utilization_pct)}%` }} /></div>{s.utilization_pct}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Configs({ configs }: { configs: Record<string, string> }) {
  const hosts = Object.keys(configs);
  const [host, setHost] = useState(hosts[0]);
  const current = configs[host] ?? configs[hosts[0]];
  return (
    <div>
      <div className="row">
        <select value={host} onChange={(e) => setHost(e.target.value)} aria-label="Device">
          {hosts.map((h) => <option key={h}>{h}</option>)}
        </select>
        <button onClick={() => saveText(current, `${host}.cfg`)}>Download .cfg</button>
        <button onClick={() => navigator.clipboard?.writeText(current)}>Copy</button>
      </div>
      <pre className="config">{current}</pre>
    </div>
  );
}

export function VerifyView({ v }: { v: Verification }) {
  return (
    <div>
      <p className={v.passed ? "ok big" : "error big"}>{v.passed ? "✔ All checks passed" : "✘ Verification failed"}</p>
      <ul className="checks">
        {v.checks.map((c) => (
          <li key={c.name} className={c.passed ? "ok" : "error"}>
            {c.passed ? "✔" : "✘"} {c.name}
            {!c.passed && <ul>{c.details.slice(0, 10).map((d) => <li key={d}>{d}</li>)}</ul>}
          </li>
        ))}
      </ul>
      <details>
        <summary>{v.probes.length} probes (segment pairs + policy flows)</summary>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Source</th><th>Destination</th><th>Proto</th><th>Expected</th><th>Actual</th><th>Reason</th></tr></thead>
            <tbody>
              {v.probes.map((p, i) => (
                <tr key={i} className={p.expected === p.actual ? "" : "row-bad"}>
                  <td>{p.src}</td><td>{p.dst}</td><td>{p.proto}{p.port ? ` ${p.port}` : ""}</td><td>{p.expected}</td><td>{p.actual}</td><td className="muted">{p.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

export function Security({ lint }: { lint: Bundle["lint"] }) {
  const [text, setText] = useState("");
  const [own, setOwn] = useState<DeviceLint | null>(null);
  const [err, setErr] = useState("");
  return (
    <div>
      <p className="big">Security score: <b className={lint.score >= 80 ? "ok" : "error"}>{lint.score}/100</b></p>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Device</th><th>Score</th><th>Rule</th><th>Severity</th><th>Where</th><th>Fix</th></tr></thead>
          <tbody>
            {lint.devices.flatMap((d) => d.findings.map((f, i) => (
              <tr key={d.hostname + f.rule + i}><td>{d.hostname}</td><td>{d.score}</td><td>{f.rule} {f.title}</td><td className={`sev-${f.severity}`}>{f.severity}</td><td>{f.where}</td><td className="mono">{f.fix}</td></tr>
            )))}
          </tbody>
        </table>
      </div>
      <h3>Lint your own config</h3>
      <textarea className="mono" rows={8} placeholder="Paste a Cisco IOS running-config…" value={text} onChange={(e) => setText(e.target.value)} aria-label="IOS config to lint" />
      <button
        disabled={!text.trim()}
        onClick={async () => {
          setErr("");
          try { setOwn(await api.lintText(text)); } catch (e) { setErr(e instanceof ApiFailure ? e.body.message : (e as Error).message); }
        }}
      >Lint</button>
      {err && <p className="error">{err}</p>}
      {own && (
        <div>
          <p>Score for <b>{own.hostname}</b>: <b>{own.score}/100</b></p>
          <ul>{own.findings.map((f, i) => <li key={i} className={`sev-${f.severity}`}>[{f.severity}] {f.where}: {f.rule} {f.title} → <code>{f.fix}</code></li>)}</ul>
        </div>
      )}
    </div>
  );
}

export function BomView({ bom }: { bom: Bom }) {
  const fmt = (n: number) => n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
  return (
    <div>
      <p className="muted">{bom.disclaimer}</p>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Item</th><th>Qty</th><th>Unit</th><th>Unit price</th><th>Total</th><th>Because of</th></tr></thead>
          <tbody>
            {bom.lines.map((x) => (
              <tr key={x.item}><td>{x.item}</td><td>{x.qty}</td><td>{x.unit}</td><td>{fmt(x.unit_price)}</td><td>{fmt(x.total)}</td><td><code>{x.rule_id}</code></td></tr>
            ))}
          </tbody>
          <tfoot>
            <tr><th colSpan={4}>Capex</th><th>{bom.currency} {fmt(bom.capex)}</th><th /></tr>
            <tr><th colSpan={4}>Monthly WAN</th><th>{bom.currency} {fmt(bom.monthly)}</th><th /></tr>
          </tfoot>
        </table>
      </div>
      {Object.keys(bom.poe_watts).length > 0 && (
        <p>PoE budget: {Object.entries(bom.poe_watts).map(([h, w]) => `${h} ${w} W`).join(", ")}</p>
      )}
      {bom.alternatives.map((a) => <p key={a.text} className="hint">💡 {a.text}</p>)}
    </div>
  );
}
