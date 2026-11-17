import { useEffect, useState } from "react";
import { api, ApiFailure } from "./api";
import type { DesignInput, NLResult } from "./types";

interface Props {
  ready: boolean;
  busy: boolean;
  onDesign: (input: DesignInput) => void;
}

export function InputPanel({ ready, busy, onDesign }: Props) {
  const [presets, setPresets] = useState<{ name: string; endpoints: number }[]>([]);
  const [preset, setPreset] = useState("campus_lan");
  const [json, setJson] = useState("");
  const [jsonErr, setJsonErr] = useState("");
  const [mode, setMode] = useState<"preset" | "nl">("preset");
  const [text, setText] = useState("");
  const [nl, setNl] = useState<NLResult | null>(null);
  const [nlErr, setNlErr] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [loading, setLoading] = useState(false);
  const descriptions: Record<string, [string, string]> = {
    campus_lan: ["Campus LAN", "Three nearby buildings. Learn how computers, guests and servers are connected and separated."],
    metro_man: ["Metro MAN", "A head office, a branch and a data center across a city. Explore backup connections."],
    global_wan: ["Global WAN", "Offices across four cities and a cloud network. Explore long-distance connections."],
  };

  useEffect(() => {
    if (!ready) return;
    api.presets().then(setPresets).catch(() => setPresets([]));
  }, [ready]);

  useEffect(() => {
    if (!ready) return;
    let active = true;
    api.preset(preset).then((p) => { if (active) { setJson(JSON.stringify(p, null, 2)); setJsonErr(""); } }).catch(() => { if (active) setJsonErr("Could not load this example. Check the backend and choose it again."); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [ready, preset]);

  function run() {
    try {
      const parsed = JSON.parse(json) as DesignInput;
      setJsonErr("");
      onDesign(parsed);
    } catch (e) {
      setJsonErr(`Invalid JSON: ${(e as Error).message}`);
    }
  }

  async function extract() {
    setNlErr("");
    setNl(null);
    setExtracting(true);
    try {
      setNl(await api.nl(text));
    } catch (e) {
      setNlErr(e instanceof ApiFailure ? e.body.message : (e as Error).message);
    } finally {
      setExtracting(false);
    }
  }

  return (
    <section className="panel input-panel" aria-label="Design input">
      <div className="seg-toggle" role="group" aria-label="Input method">
        <button aria-pressed={mode === "preset"} className={mode === "preset" ? "on" : ""} onClick={() => setMode("preset")}>
          Examples
        </button>
        <button aria-pressed={mode === "nl"} className={mode === "nl" ? "on" : ""} onClick={() => setMode("nl")}>
          Plain English
        </button>
      </div>

      {mode === "nl" && (
        <div className="nl">
          <label htmlFor="nl-text">Describe the network</label>
          <textarea
            id="nl-text"
            rows={4}
            value={text}
            placeholder="3-building campus, 1600 users, PoE APs, buildings 250 m and 380 m from the main building, redundant core"
            onChange={(e) => setText(e.target.value)}
          />
          <button disabled={!ready || !text.trim() || extracting} onClick={extract}>{extracting ? "Reading your description…" : "Extract parameters"}</button>
          {nlErr && <p className="error">{nlErr}</p>}
          {nl && (
            <div className="nl-result">
              <p className="muted">
                Source: <b>{nl.source}</b>. {nl.note} The AI only fills this form; every design decision is made by the rule engine.
              </p>
              {nl.assumptions.length > 0 && (
                <>
                  <h4>Assumptions</h4>
                  <ul>{nl.assumptions.map((a) => <li key={a}>{a}</li>)}</ul>
                </>
              )}
              {nl.missing.length > 0 && (
                <>
                  <h4>Missing (add them in the JSON)</h4>
                  <ul>{nl.missing.map((a) => <li key={a}>{a}</li>)}</ul>
                </>
              )}
              {!nl.valid && (
                <>
                  <h4>Validation errors</h4>
                  <ul className="error">{nl.errors.map((e) => <li key={e.loc + e.msg}>{e.loc}: {e.msg}</li>)}</ul>
                </>
              )}
              <button
                onClick={() => {
                  setJson(JSON.stringify(nl.input, null, 2));
                  setMode("preset");
                }}
              >
                Review &amp; edit extracted JSON
              </button>
            </div>
          )}
        </div>
      )}

      {mode === "preset" && (
        <div className="json">
          <label htmlFor="preset">Choose a starting point</label>
          <select id="preset" value={preset} onChange={(e) => { setLoading(true); setPreset(e.target.value); }} disabled={!ready || busy}>
            {presets.map((p) => (
              <option key={p.name} value={p.name}>{descriptions[p.name]?.[0] ?? p.name}</option>
            ))}
          </select>
          <p className="preset-description">{descriptions[preset]?.[1]}</p>
          <p className="muted">LAN means local network. MAN spans a city. WAN connects distant locations.</p>
          <details className="advanced-input"><summary>Edit requirements <span className="muted">· advanced JSON</span></summary><p className="muted">JSON is a structured text format. Change the example’s requirements here; the engine validates them before designing.</p>
          <label htmlFor="json">Design input (editable JSON)</label>
          <textarea id="json" className="mono" rows={16} spellCheck={false} value={json} onChange={(e) => setJson(e.target.value)} />
          </details>
          {jsonErr && <p className="error">{jsonErr}</p>}
          <button className="primary" disabled={!ready || busy || loading || !json} onClick={run}>
            {busy ? "Designing…" : "Design network"}
          </button>
        </div>
      )}
    </section>
  );
}
