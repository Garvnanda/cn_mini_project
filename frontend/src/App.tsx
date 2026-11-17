import { useEffect, useState } from "react";
import { api, ApiFailure, API_URL } from "./api";
import { Guide } from "./Guide";
import { InputPanel } from "./InputPanel";
import { NetworkView } from "./NetworkView";
import { BomView, Configs, Decisions, IpPlan, Security, VerifyView } from "./panels";
import { Report } from "./Report";
import { Versions } from "./Versions";
import type { ApiError, Bundle, DesignInput } from "./types";

const TABS = ["Overview", "Network map", "Why these choices?", "Address plan", "Device instructions", "Checks", "Security", "Equipment & costs", "Saved versions", "Export & report", "How to use"] as const;
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
  const [tab, setTab] = useState<Tab>("Overview");
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
      setTab("Overview");
    } catch (e) {
      setError(e instanceof ApiFailure ? e.body : { type: "NetworkError", message: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header className="top no-print">
        <a className="brand" href="#" onClick={e => { e.preventDefault(); setTab("Overview"); }}><svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><path d="M7 8L23 8L15 23Z" fill="none" stroke="currentColor" strokeWidth="2"/><circle cx="7" cy="8" r="4" fill="currentColor"/><circle cx="23" cy="8" r="4" fill="currentColor"/><circle cx="15" cy="23" r="4" fill="currentColor"/></svg><span>NetArchitect<small>Network planning, explained.</small></span></a>
        <button className="help-link" onClick={() => setTab("How to use")}>How to use</button>
        <a className="api-link" href={`${API_URL}/docs`} target="_blank" rel="noreferrer">API docs</a>
        <span className={`status ${server}`} role="status">
          {server === "waking" && "Connecting to the engine…"}
          {server === "up" && "Server ready"}
          {server === "down" && "Engine offline · start the backend"}
        </span>
        <select value={theme} onChange={(e) => setTheme(e.target.value)} aria-label="Theme">
          <option value="auto">Auto theme</option><option value="light">Light</option><option value="dark">Dark</option>
        </select>
      </header>
      <main>
        <aside className="no-print">
          <div className="sidebar-heading"><h2>Build your network</h2><p>Start with an example. Explore the plan before changing anything.</p></div>
          <InputPanel ready={server === "up"} busy={busy} onDesign={runDesign} />
          <div className="sidebar-note"><b>New to networking?</b><p>You don’t need to know the commands. The guide explains each step and the terms you’ll meet.</p><button onClick={() => setTab("How to use")}>Open the guide</button></div>
        </aside>
        <section className="workspace">
          {error && (
            <div className="result error" role="alert">
              <h3>{error.type}</h3>
              <p>{error.message}</p>
            </div>
          )}
          {!bundle && tab === "How to use" && <Guide />}
          {!bundle && tab !== "How to use" && <div className="welcome"><h2>From a network idea<br/>to a plan that makes sense.</h2><p className="lead">Connect buildings, teams and cities. See what equipment you need, why it was chosen, and how information travels between devices.</p><div className="journey"><div><b>Describe</b><p>Choose an example or enter your requirements.</p></div><div><b>Understand</b><p>Explore the map and the reasons behind each choice.</p></div><div><b>Try it out</b><p>Check connections and simulate a broken link.</p></div></div><p className="welcome-next">Choose <b>Campus LAN</b> and select <b>Design network</b> to begin.</p><button onClick={() => setTab("How to use")}>Show me how it works</button><p className="muted">This creates a simulated plan. It does not change your actual network.</p></div>}
          {bundle && (
            <>
              <nav className="tabs no-print" aria-label="Design results">
                {TABS.map((t) => (
                  <button key={t} aria-pressed={tab === t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>{t}</button>
                ))}
              </nav>
              {tab === "How to use" && <Guide />}
              {tab === "Overview" && <div className="overview"><h2>Your network, at a glance.</h2><p className="lead">A plan for {bundle.design.input.sites.length} {bundle.design.input.sites.length === 1 ? "site" : "sites"}, connecting {bundle.design.input.segments.reduce((n, s) => n + s.hosts, 0).toLocaleString()} end devices across {bundle.design.input.segments.length} groups.</p><div className="plan-facts"><div><b>{bundle.design.devices.length}</b><span>network devices</span></div><div><b>{bundle.design.cables.length}</b><span>connections</span></div><div><b>{bundle.design.subnets.length}</b><span>address blocks</span></div></div><div className={`verification-banner ${bundle.verification.passed ? "ok" : "error"}`}><b>{bundle.verification.passed ? "The simulated plan passes its checks." : "Some checks need attention."}</b><p>We read the generated instructions back and test connections against your rules. Real equipment still needs separate lab validation.</p><button onClick={() => setTab("Checks")}>See the checks</button></div><h3>Explore your design</h3><div className="next-actions"><button onClick={() => setTab("Network map")}><b>See how it connects</b><span>Open the map, follow a packet, or try a failure.</span></button><button onClick={() => setTab("Why these choices?")}><b>Understand the decisions</b><span>Read why each cable, address block and route was chosen.</span></button><button onClick={() => setTab("Export & report")}><b>Take the plan with you</b><span>Download device instructions and a readable report.</span></button></div></div>}
              {tab !== "Overview" && tab !== "How to use" && <div className="view-heading"><h2>{tab}</h2><p>{({"Network map":"The devices and connections in your plan. Follow a connection or test what happens when something fails.","Why these choices?":"Every decision has a reason. Expand a category to explore the engineering rules behind your plan.","Address plan":"Each group gets its own block of addresses, like a neighborhood gets its own street numbers.","Device instructions":"Generated Cisco IOS commands for each device. Use these when building a compatible lab.","Checks":"Tests of the generated instructions inside the built-in simulator.","Security":"Configuration findings and suggested fixes. This score is a checklist result, not a security certification.","Equipment & costs":"An equipment list, also called a bill of materials (BOM). Prices are placeholders for comparison.","Saved versions":"Save a plan before editing it, then compare what changed. Saved in this browser only.","Export & report":"Download your plan or print a report to share and explain your design."} as Record<string,string>)[tab]}</p></div>}
              {tab === "Network map" && <NetworkView key={JSON.stringify(bundle.design.input)} bundle={bundle} />}
              {tab === "Why these choices?" && <Decisions rationale={bundle.design.rationale} />}
              {tab === "Address plan" && <IpPlan subnets={bundle.design.subnets} />}
              {tab === "Device instructions" && <Configs key={JSON.stringify(bundle.configs)} configs={bundle.configs} />}
              {tab === "Checks" && <VerifyView v={bundle.verification} />}
              {tab === "Security" && <Security lint={bundle.lint} />}
              {tab === "Equipment & costs" && <BomView bom={bundle.bom} />}
              {tab === "Saved versions" && <Versions current={bundle.design.input} />}
              {tab === "Export & report" && <Report bundle={bundle} />}
            </>
          )}
        </section>
      </main>
    </div>
  );
}

