import { useState } from "react";
import { api, ApiFailure } from "./api";
import type { DesignInput, DiffResult } from "./types";

export interface Version { id: string; name: string; time: string; input: DesignInput }

const KEY = "netarch.versions";

export function loadVersions(): Version[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Version[]) : [];
  } catch {
    return [];
  }
}

function store(v: Version[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(v));
  } catch {
    /* storage unavailable (private mode): versions live for this tab only */
  }
}

export function Versions({ current }: { current: DesignInput }) {
  const [versions, setVersions] = useState<Version[]>(loadVersions);
  const [name, setName] = useState("");
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [err, setErr] = useState("");

  function save() {
    const v: Version = { id: crypto.randomUUID(), name: name || `${current.profile} v${versions.length + 1}`, time: new Date().toLocaleString(), input: current };
    const next = [v, ...versions];
    setVersions(next);
    store(next);
    setName("");
  }

  function remove(id: string) {
    const next = versions.filter((v) => v.id !== id);
    setVersions(next);
    store(next);
  }

  async function compare() {
    setErr("");
    const va = versions.find((v) => v.id === a);
    const vb = versions.find((v) => v.id === b);
    if (!va || !vb) return;
    try {
      setDiff(await api.diff(va.input, vb.input));
    } catch (e) {
      setErr(e instanceof ApiFailure ? e.body.message : (e as Error).message);
    }
  }

  function exportJson() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(versions, null, 2)], { type: "application/json" }));
    const el = document.createElement("a");
    el.href = url;
    el.download = "netarch_versions.json";
    el.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className="row">
        <input placeholder="Version name" value={name} onChange={(e) => setName(e.target.value)} aria-label="Version name" />
        <button className="primary" onClick={save}>Save current design</button>
        <button onClick={exportJson} disabled={!versions.length}>Download all (JSON)</button>
      </div>
      <p className="muted">Versions are kept in this browser only (no server database).</p>
      <ul className="versions">
        {versions.map((v) => (
          <li key={v.id}><b>{v.name}</b> <span className="muted">{v.time}</span> <button onClick={() => remove(v.id)}>Delete</button></li>
        ))}
      </ul>
      {versions.length >= 2 && (
        <div className="row">
          <select value={a} onChange={(e) => setA(e.target.value)} aria-label="Old version"><option value="">old…</option>{versions.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}</select>
          <select value={b} onChange={(e) => setB(e.target.value)} aria-label="New version"><option value="">new…</option>{versions.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}</select>
          <button onClick={compare} disabled={!a || !b}>Compare</button>
        </div>
      )}
      {err && <p className="error">{err}</p>}
      {diff && (
        diff.empty ? <p>No differences.</p> : (
          <div>
            <h3>Decisions</h3>
            {diff.decisions.map((c) => (
              <article key={c.key} className="card">
                <header><code>{c.key}</code> <span className="pill">{c.change}</span></header>
                {c.old.map((t) => <p key={"o" + t} className="del">− {t}</p>)}
                {c.new.map((t) => <p key={"n" + t} className="add">+ {t}</p>)}
              </article>
            ))}
            {diff.subnets.length > 0 && (<><h3>IP plan</h3><ul>{diff.subnets.map((s) => <li key={s.name}>{s.name}: {s.old ?? "–"} → {s.new ?? "–"} ({s.change})</li>)}</ul></>)}
            {(diff.devices_added.length > 0 || diff.devices_removed.length > 0) && <p>Devices added: {diff.devices_added.join(", ") || "none"}; removed: {diff.devices_removed.join(", ") || "none"}</p>}
            <h3>Configs ({Object.keys(diff.configs).length} changed)</h3>
            {Object.entries(diff.configs).map(([h, d]) => (
              <details key={h}><summary>{h}</summary><pre className="config diff">{d}</pre></details>
            ))}
          </div>
        )
      )}
    </div>
  );
}
