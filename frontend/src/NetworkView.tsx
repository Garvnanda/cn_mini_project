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
  const [failureMode, setFailureMode] = useState(false);

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
        <label>Connection type <select value={proto} onChange={(e) => setProto(e.target.value)}><option value="icmp">Reachability (ICMP)</option><option value="tcp">Reliable traffic (TCP)</option><option value="udp">Datagrams (UDP)</option></select></label>
        {proto !== "icmp" && <label>Port <input type="number" min={1} max={65535} value={port} onChange={(e) => setPort(e.target.value)} /></label>}
        <button className="primary" onClick={runTrace} disabled={busy}>Trace packet</button>
      </div>
      <div className="map-tools"><p className="muted">A packet is a small piece of data. Trace it to see which devices it passes through.</p><label><input type="checkbox" checked={failureMode} onChange={e => setFailureMode(e.target.checked)} /> Enable failure testing</label></div>
      {failureMode && <p className="hint">Select a connection or a non-access device to simulate its failure. This only changes the simulation.</p>}
      {err && <p className="error">{err}</p>}
      <Topology
        nodes={bundle.graph.nodes}
        edges={bundle.graph.edges}
        path={path}
        failed={failed}
        spof={[...bundle.spof.spof_devices, ...bundle.spof.spof_cables]}
        onEdge={failureMode && !busy ? (e: GraphEdge) => fail([edgeId(e)], []) : undefined}
        onNode={failureMode && !busy ? (id) => roleOf.get(id) !== "access" && fail([], [id]) : undefined}
      />
      {trace && (
        <div className={`result ${trace.outcome === "delivered" ? "ok" : "error"}`}>
          <h3>{trace.outcome === "delivered" ? "Connection delivered" : trace.outcome === "dropped" ? "Connection blocked" : "Connection could not reach its destination"}</h3>
          <p>{trace.outcome === "delivered" ? "The simulated packet reached the destination." : "The simulator stopped this packet. Check the details to see whether a security rule or an unavailable path caused it."}</p>
          <details><summary>Technical trace · {trace.hops.length} steps</summary><p>{trace.outcome.toUpperCase()}: {trace.reason}</p>
          <ol>
            {trace.hops.map((h, i) => (
              <li key={i} className={i < step ? "" : "dim"}>
                <b>{h.device}</b> <span className="mono">[{h.in_if ?? "–"} → {h.out_if ?? "–"}]</span> {h.action}: {h.detail}
              </li>
            ))}
          </ol>
          </details>
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
      <details>
        <summary>Backup paths & single points of failure · {bundle.spof.score}/100</summary>
        <p>A single point of failure is a device or link whose loss disconnects part of the modeled network. This score measures the modeled topology, not real uptime.</p>
        <ul>{bundle.spof.rationale.map((r) => <li key={r.text}>{r.text}</li>)}</ul>
      </details>
    </div>
  );
}
