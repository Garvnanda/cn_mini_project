import { useState } from "react";
import { API_URL } from "./api";

export function CopyCommand({ children }: { children: string }) {
  const [message, setMessage] = useState("");
  return <div className="command"><code>{children}</code><button onClick={async () => {
    try { await navigator.clipboard.writeText(children); setMessage("Copied"); }
    catch { setMessage("Select and copy the command manually"); }
  }}>Copy</button>{message && <span role="status">{message}</span>}</div>;
}

export const TERMS: Record<string, string> = {
  "Network": "A group of devices connected so they can exchange information.",
  "Switch": "Connects devices within a local network, such as computers on one floor.",
  "Router": "Moves information between different networks or sites.",
  "Topology": "The map of devices and the links between them.",
  "IP address": "A numerical address used to identify a device on a network.",
  "Subnet / VLSM": "A subnet is a group of IP addresses. VLSM gives each group a suitably sized block, reducing wasted addresses.",
  "Gateway": "The device a computer sends traffic to when the destination is outside its own subnet.",
  "VLAN": "A logical group on a switch. It separates groups such as staff, guests and servers even when they share hardware.",
  "Trunk": "A link between switches that carries traffic for several VLANs.",
  "OSPF / BGP": "Routing protocols: rules routers use to share available paths. This project uses OSPF within the organization and BGP at a separate network boundary.",
  "ACL": "An access control list: ordered rules that allow or block traffic, such as blocking guests from servers.",
  "Packet": "A small piece of information sent across a network. A packet trace shows the path it would take.",
  "PoE": "Power over Ethernet supplies electrical power through the network cable, for devices such as wireless access points.",
  "Cat6a / OM4 / OS2": "Cable types: Cat6a is copper, OM4 is multimode optical fiber, and OS2 is single-mode optical fiber. Distance and optical loss affect the choice.",
  "Transceiver": "The module that sends and receives signals through a cable or optical fiber.",
  "HSRP / redundancy": "Redundancy adds backup paths or devices. HSRP lets a pair of devices share a gateway address so another can take over.",
  "STP": "Spanning Tree Protocol prevents loops in switched networks by controlling which links forward traffic.",
  "IPsec": "A set of protocols used to protect traffic crossing an untrusted network, such as the internet.",
  "QoS / latency": "Quality of Service prioritizes selected traffic. Latency is its travel time. This tool checks propagation estimates, not measured delay under load.",
  "Cisco IOS configuration": "Text commands intended to configure a Cisco network device. The selected device and software must support them.",
};

export function Guide() {
  const [search, setSearch] = useState("");
  return <div className="guide">
    <h2>A network plan you can understand.</h2>
    <p className="lead">Imagine connecting a college campus, a company’s branches, or offices across cities. NetArchitect helps decide what connects them, how addresses are shared, and which traffic is allowed.</p>
    <p>You provide the requirements. Fixed rules build a plan and explain the choices. A built-in simulator then checks the generated device instructions. It does not change your computer’s network or configure real equipment.</p>
    <h3>Your first design</h3>
    <ol className="guide-steps">
      <li><b>Choose Campus LAN.</b> It is a ready-made example of three buildings. You do not need to edit any code.</li>
      <li><b>Select Design network.</b> Read the overview, then open Network map to see the connections.</li>
      <li><b>Open Why these choices?</b> See why a cable, address block or routing approach was selected.</li>
      <li><b>Try a connection.</b> In Network map, trace Guest-C to Servers. It should be blocked by the example’s security rule. A blocked connection can be the correct result.</li>
      <li><b>Try a failure.</b> Enable failure testing and select a link or device. Compare broken connections and connections that find a backup path.</li>
      <li><b>Save or export.</b> Save versions before changing inputs, or download a report and device instructions from Export & report.</li>
    </ol>
    <h3>Four ways to use the same engine</h3>
    <div className="table-wrap"><table><thead><tr><th>Interface</th><th>Use it when</th><th>What to expect</th></tr></thead><tbody>
      <tr><td><b>Web app</b></td><td>You are learning, exploring or presenting.</td><td>Visual map, explanations, forms, reports and interactive tests. Start here.</td></tr>
      <tr><td><b>TUI</b> · terminal interface</td><td>You want an interactive dashboard inside a terminal.</td><td>Choose presets and switch between results using keyboard and mouse.</td></tr>
      <tr><td><b>CLI</b> · command line</td><td>You want a repeatable task or a script.</td><td>One command produces one result. Useful for verification, traces and exports.</td></tr>
      <tr><td><b>API</b> · program interface</td><td>You want another program to use the engine.</td><td>Send structured requests and receive JSON. The web app uses this too.</td></tr>
    </tbody></table></div>
    <details><summary>Run the TUI or CLI locally</summary>
      <p>Open PowerShell in the project folder, then enter <code>cd backend</code>. Commands below use the project’s Windows Python environment.</p>
      <h4>Open the terminal dashboard</h4><CopyCommand>{".\\.venv\\Scripts\\python.exe tui.py"}</CopyCommand>
      <p>Choose a preset, press Run, and use the tabs. Press Tab to move between controls. Ctrl+C closes the dashboard.</p>
      <h4>Build a plan</h4><CopyCommand>{".\\.venv\\Scripts\\python.exe cli.py design campus_lan"}</CopyCommand>
      <h4>Check generated instructions</h4><CopyCommand>{".\\.venv\\Scripts\\python.exe cli.py verify global_wan"}</CopyCommand>
      <h4>Follow an allowed connection</h4><CopyCommand>{".\\.venv\\Scripts\\python.exe cli.py trace metro_man Branch-Users Colo-Trading --proto tcp --port 443"}</CopyCommand>
      <h4>See every command</h4><CopyCommand>{".\\.venv\\Scripts\\python.exe cli.py --help"}</CopyCommand>
      <p>Preset names: <code>campus_lan</code>, <code>metro_man</code>, <code>global_wan</code>. You can also supply a JSON file path.</p>
    </details>
    <details><summary>Use the API</summary><p>Open <a href={`${API_URL}/docs`} target="_blank" rel="noreferrer">the interactive API documentation</a>. Run <code>GET /presets/campus_lan</code>, copy its response, and use it as the body for <code>POST /design</code>. Select Try it out, then Execute. The response contains the plan and checks.</p></details>
    <h3>What the results mean</h3>
    <p><b>Checks passed</b> means the built-in model found no failures in its checks. Real device compatibility and performance still need a lab test. <b>Security score</b> summarizes configuration rules, not a security certification. <b>Resilience</b> describes modeled single failures, not a guarantee of uptime. <b>Costs</b> use placeholder prices for comparison, not supplier quotes.</p>
    <h3>Networking terms, in plain language</h3>
    <input className="filter" aria-label="Search networking terms" placeholder="Search a term, e.g. VLAN or gateway" value={search} onChange={e => setSearch(e.target.value)} />
    <dl className="glossary">{Object.entries(TERMS).filter(([term, meaning]) => `${term} ${meaning}`.toLowerCase().includes(search.toLowerCase())).map(([term, meaning]) => <div key={term}><dt>{term}</dt><dd>{meaning}</dd></div>)}</dl>
  </div>;
}
