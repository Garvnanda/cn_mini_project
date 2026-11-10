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

  useEffect(() => {
    if (!ready) return;
    api.presets().then(setPresets).catch(() => setPresets([]));
  }, [ready]);

  useEffect(() => {
    if (!ready) return;
    api.preset(preset).then((p) => setJson(JSON.stringify(p, null, 2))).catch(() => undefined);
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
    try {
      setNl(await api.nl(text));
    } catch (e) {
      setNlErr(e instanceof ApiFailure ? e.body.message : (e as Error).message);
    }
  }

  return (
    <section className="panel input-panel" aria-label="Design input">
      <div className="seg-toggle" role="tablist">
        <button role="tab" aria-selected={mode === "preset"} className={mode === "preset" ? "on" : ""} onClick={() => setMode("preset")}>
          Preset / JSON
        </button>
        <button role="tab" aria-selected={mode === "nl"} className={mode === "nl" ? "on" : ""} onClick={() => setMode("nl")}>
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
          <button disabled={!ready || !text.trim()} onClick={extract}>Extract parameters</button>
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
          <label htmlFor="preset">Preset</label>
          <select id="preset" value={preset} onChange={(e) => setPreset(e.target.value)} disabled={!ready}>
            {presets.map((p) => (
              <option key={p.name} value={p.name}>{p.name} ({p.endpoints} endpoints)</option>
            ))}
          </select>
          <label htmlFor="json">Design input (editable JSON)</label>
          <textarea id="json" className="mono" rows={16} spellCheck={false} value={json} onChange={(e) => setJson(e.target.value)} />
          {jsonErr && <p className="error">{jsonErr}</p>}
          <button className="primary" disabled={!ready || busy || !json} onClick={run}>
            {busy ? "Designing…" : "Design network"}
          </button>
        </div>
      )}
    </section>
  );
}
