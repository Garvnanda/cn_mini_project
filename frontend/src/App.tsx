import { useEffect, useState } from "react";
import { api, ApiFailure } from "./api";
import { InputPanel } from "./InputPanel";
import { NetworkView } from "./NetworkView";
import { BomView, Configs, Decisions, IpPlan, Security, VerifyView } from "./panels";
import { Report } from "./Report";
import { Versions } from "./Versions";
import type { ApiError, Bundle, DesignInput } from "./types";

const TABS = ["Network", "Decisions", "IP Plan", "Configs", "Verify", "Security", "BOM", "Versions", "Report"] as const;
type Tab = (typeof TABS)[number];

function initialTheme(): string {
  try {
    return localStorage.getItem("netarch.theme") ?? "auto";
  } catch {
    return "auto";
  }
}

export default function App() {
  const [server, setServer] = useState<"waking" | "up" | "down">("waking");
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState<Tab>("Network");
  const [theme, setTheme] = useState(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("netarch.theme", theme); } catch { /* ignore */ }
  }, [theme]);

  // Render free tier sleeps: keep pinging /health until it answers (up to ~90 s)
  useEffect(() => {
    let alive = true;
    let tries = 0;
    const ping = () => {
      api.health()
        .then(() => alive && setServer("up"))
        .catch(() => {
          tries += 1;
          if (!alive) return;
          if (tries > 30) setServer("down");
          else setTimeout(ping, 3000);
        });
    };
    ping();
    return () => { alive = false; };
  }, []);

  async function runDesign(input: DesignInput) {
    setBusy(true);
    setError(null);
    try {
      setBundle(await api.design(input));
    } catch (e) {
      setError(e instanceof ApiFailure ? e.body : { type: "NetworkError", message: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header className="top no-print">
        <h1>NetArchitect</h1>
        <span className="tagline">design → explain → verify → break → re-verify</span>
        <span className={`status ${server}`} role="status">
          {server === "waking" && "Waking server… (free tier cold start can take ~30 s)"}
          {server === "up" && "Server ready"}
          {server === "down" && "Server unreachable: check VITE_API_URL"}
        </span>
        <select value={theme} onChange={(e) => setTheme(e.target.value)} aria-label="Theme">
          <option value="auto">Auto theme</option><option value="light">Light</option><option value="dark">Dark</option>
        </select>
      </header>
      <main>
        <aside className="no-print">
          <InputPanel ready={server === "up"} busy={busy} onDesign={runDesign} />
        </aside>
        <section className="workspace">
          {error && (
            <div className="result error" role="alert">
              <h3>{error.type}</h3>
              <p>{error.message}</p>
            </div>
          )}
          {!bundle && !error && <p className="empty">Pick a preset (or describe your network) and press <b>Design network</b>.</p>}
          {bundle && (
            <>
              <nav className="tabs no-print" role="tablist">
                {TABS.map((t) => (
                  <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>{t}</button>
                ))}
              </nav>
              <div className="summary no-print">
                <span>{bundle.design.routing.protocol}</span>
                <span>{bundle.design.devices.length} devices</span>
                <span className={bundle.verification.passed ? "ok" : "error"}>verify {bundle.verification.passed ? "PASS" : "FAIL"}</span>
                <span>security {bundle.lint.score}/100</span>
                <span>resilience {bundle.spof.score}/100</span>
              </div>
              {tab === "Network" && <NetworkView key={JSON.stringify(bundle.design.input)} bundle={bundle} />}
              {tab === "Decisions" && <Decisions rationale={bundle.design.rationale} />}
              {tab === "IP Plan" && <IpPlan subnets={bundle.design.subnets} />}
              {tab === "Configs" && <Configs configs={bundle.configs} />}
              {tab === "Verify" && <VerifyView v={bundle.verification} />}
              {tab === "Security" && <Security lint={bundle.lint} />}
              {tab === "BOM" && <BomView bom={bundle.bom} />}
              {tab === "Versions" && <Versions current={bundle.design.input} />}
              {tab === "Report" && <Report bundle={bundle} />}
            </>
          )}
        </section>
      </main>
    </div>
  );
}
