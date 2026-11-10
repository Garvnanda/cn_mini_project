import { useState } from "react";
import { api, ApiFailure } from "./api";
import { edgeId, Topology } from "./Topology";
import type { Bundle, GraphEdge, Trace, WhatIf } from "./types";

export function NetworkView({ bundle }: { bundle: Bundle }) {
  const input = bundle.design.input;
  const segs = input.segments.map((s) => s.name);
  const [src, setSrc] = useState(segs[0]);
  const [dst, setDst] = useState(segs[1] ?? segs[0]);
  const [proto, setProto] = useState("icmp");
  const [port, setPort] = useState("");
  const [trace, setTrace] = useState<Trace | null>(null);
  const [whatif, setWhatif] = useState<WhatIf | null>(null);
  const [failed, setFailed] = useState<string[]>([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);

  async function runTrace() {
    setErr("");
    setWhatif(null);
    setFailed([]);
    setBusy(true);
    try {
      const t = await api.trace(input, src, dst, proto, port ? Number(port) : null);
      setTrace(t);
      setStep(0);
      // animate the path hop by hop
      t.hops.forEach((_, i) => setTimeout(() => setStep(i + 1), 350 * (i + 1)));
    } catch (e) {
      setErr(e instanceof ApiFailure ? e.body.message : (e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function fail(links: string[], nodes: string[]) {
    setErr("");
    setTrace(null);
    setBusy(true);
    setFailed([...links, ...nodes]);
    try {
      setWhatif(await api.whatif(input, links, nodes));
    } catch (e) {
      setErr(e instanceof ApiFailure ? e.body.message : (e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const path = trace ? trace.hops.slice(0, step).map((h) => h.device) : [];
  const roleOf = new Map(bundle.graph.nodes.map((n) => [n.id, n.role]));

  return (
    <div>
      <div className="toolbar">
        <label>From <select value={src} onChange={(e) => setSrc(e.target.value)}>{segs.map((s) => <option key={s}>{s}</option>)}</select></label>
        <label>To <select value={dst} onChange={(e) => setDst(e.target.value)}>{segs.map((s) => <option key={s}>{s}</option>)}</select></label>
        <label>Proto <select value={proto} onChange={(e) => setProto(e.target.value)}>{["icmp", "tcp", "udp"].map((p) => <option key={p}>{p}</option>)}</select></label>
        {proto !== "icmp" && <label>Port <input type="number" min={1} max={65535} value={port} onChange={(e) => setPort(e.target.value)} /></label>}
        <button className="primary" onClick={runTrace} disabled={busy}>Trace packet</button>
        <span className="muted">Click a link or a non-access device to fail it.</span>
      </div>
      {err && <p className="error">{err}</p>}
      <Topology
        nodes={bundle.graph.nodes}
        edges={bundle.graph.edges}
        path={path}
        failed={failed}
        spof={[...bundle.spof.spof_devices, ...bundle.spof.spof_cables]}
        onEdge={(e: GraphEdge) => fail([edgeId(e)], [])}
        onNode={(id) => roleOf.get(id) !== "access" && fail([], [id])}
      />
      {trace && (
        <div className={`result ${trace.outcome === "delivered" ? "ok" : "error"}`}>
          <h3>{trace.outcome.toUpperCase()}: {trace.reason}</h3>
          <ol>
            {trace.hops.map((h, i) => (
              <li key={i} className={i < step ? "" : "dim"}>
                <b>{h.device}</b> <span className="mono">[{h.in_if ?? "–"} → {h.out_if ?? "–"}]</span> {h.action}: {h.detail}
              </li>
            ))}
          </ol>
        </div>
      )}
      {whatif && (
        <div className={`result ${whatif.survives ? "ok" : "error"}`}>
          <h3>{whatif.survives ? "Network survives" : "Outage"}: {whatif.broken.length} broken, {whatif.rerouted.length} rerouted, {whatif.unaffected} unaffected</h3>
          <p className="muted">Failed: {whatif.failed.join(", ")}</p>
          {whatif.rationale.map((r) => <p key={r.text}>{r.text}</p>)}
          {whatif.broken.length > 0 && <><h4>Broken</h4><ul>{whatif.broken.slice(0, 30).map((b, i) => <li key={i}>{b.src} → {b.dst}: {b.reason}</li>)}</ul></>}
          {whatif.rerouted.length > 0 && <><h4>Rerouted</h4><ul>{whatif.rerouted.slice(0, 30).map((b, i) => <li key={i}>{b.src} → {b.dst}: {b.after_path.join(" › ")}</li>)}</ul></>}
          <button onClick={() => { setWhatif(null); setFailed([]); }}>Clear</button>
        </div>
      )}
      <details open={!trace && !whatif}>
        <summary>Resilience score {bundle.spof.score}/100</summary>
        <ul>{bundle.spof.rationale.map((r) => <li key={r.text}>{r.text}</li>)}</ul>
      </details>
    </div>
  );
}
