# NetArchitect — Idea Document

**Course:** CIC-307 Computer Networks Mini-Project · **Mode:** Solo · **Status:** Fresh rewrite (Phase 2)

## 1. One-liner

A network-design engine that **thinks like an architect, explains like a teacher, and checks its own work like an auditor.**
You describe a network (preset, JSON, or plain English). NetArchitect designs it end to end. It picks media, VLSM, routing, topology and Cisco IOS configs, and it justifies every choice with physics, math and RFC references. Then it **parses its own configs back in and proves they work** by tracing packets hop by hop. You can break links to watch failover, see the cost of every decision, and export a ready-to-run GNS3 lab.

Most submissions stop at "generate configs". NetArchitect's distinguishing claim is **closed-loop design**: *design → explain → verify → break → re-verify*.

## 1a. The assignment in brief (from the PDF)
- **Course:** CIC-307 Computer Networks mini-project, 100 points, solo or a team of 2. The PDF's stated due date is 10 Nov 2026; the owner chose to ignore time limits and build the best possible version.
- **Task:** a software tool (CLI, web or API) that takes preset or custom enterprise network parameters, runs algorithmic rule engines, and outputs infrastructure recommendations plus deployment-ready device configs.
- **3 profiles:**
  - *Campus LAN:* 3 buildings, <400 m apart, 1,600 endpoints, PoE APs. Focus: Cat6a vs MMF, 802.1Q VLANs, RSTP, single-area OSPF.
  - *Metro MAN:* HQ + 2 remote sites (15–35 km), 450 users, FinTech colo. Focus: OS2 SMF, EVPL, sub-5 ms QoS, dual-homed failover.
  - *Global WAN:* 4 cities + cloud VPC, 2,000 IoT devices / scanners. Focus: IPsec VPN, multi-area OSPF/BGP, route summarization.
- **Mandatory:** an explainable decision engine. Every choice comes with a natural-language justification, including math and RFC references.
- **Required flow:** input ingestion → L1/L2 media engine → L3 VLSM & routing → explainable exporter (configs + rationale log).
- **AI policy:** AI tools are allowed, but the student acts as the validator. `ai_audit_log.md` must record ≥2 real AI networking bugs, each with diagnosis, fix and packet-flow validation.
- **Deliverables:** source repo (interface + explainability engine + pytest), `ai_audit_log.md`, and config exports for the 3 presets loaded into Packet Tracer or GNS3.

## 1b. Owner choices (from the Q&A)
| Topic | Choice |
|---|---|
| Team | Solo |
| Codebase | Old phase-1 demo deleted; full rewrite from scratch |
| Ambition | No time constraint; aim for the best, not a basic version |
| Interfaces | All three: web dashboard, CLI, rich TUI |
| Stack | Python backend + React frontend |
| Unique features | Self-verifying configs, what-if failure sim, NL input, GNS3/PT export, BOM/cost, design diff & versioning, security score, PDF report |
| LLM | OpenRouter API key (model set via env) |
| Verification | Own simulator + Batfish, but must stay light on storage/CPU, so Batfish is optional and local only |
| Deploy | Free tier: Vercel (frontend) + Render (backend) |
| Git | Owner does all commits and pushes; AI never does |

## 1c. Project docs map
| File | Purpose |
|---|---|
| `idea.md` | This file: what we are building and why |
| `CLAUDE.md` | Strict rules for AI assistants (anti-hallucination, no git) |
| `implementation.md` | Phase-by-phase task checklist (Phases 0–26) |
| `implemented.md` | What is actually built and tested |
| `ai_audit_log.md` | Real AI bug post-mortems (graded, 20 pts) |
| `docs/standards.md` | Only allowed source of networking numbers and RFCs |
| `docs/ios_reference.md` | Only allowed Cisco IOS commands |
| `docs/decisions.md` | Architecture decision log |

## 2. What the spec requires (baseline, must be flawless)

| Spec item | Points | How we cover it |
|---|---|---|
| 3 presets + custom params, boundary handling | 15 | Campus LAN, Metro MAN, Global WAN + custom JSON. Pydantic validation, typed errors (`PhysicalDistanceViolationError`, `AddressSpaceExhaustedError`, …) |
| Explainable decision engine | 25 | Every decision emits a `Rationale` object: rule, inputs, threshold, standard (802.3an, RFC 1878/3021/2328/4271), human sentence |
| Bitwise VLSM + IOS configs | 25 | Integer bitwise allocator (no `ipaddress` shortcuts in the core path; `ipaddress` used only as a test oracle). Jinja2 IOS templates: switches, routers, SVIs, ACLs, OSPF/BGP, IPsec |
| Unit tests | 15 | pytest: distance violations, exhaustion, wildcard masks (/0–/32, /31, /32), overlap property tests (Hypothesis) |
| AI audit log | 20 | `ai_audit_log.md`: ≥2 real AI bugs with prompt, bad code, packet-flow proof from **our own simulator**, and the fix |
| Deliverables | — | Exports for the 3 presets, loadable in Packet Tracer / GNS3 |

### Decision rules (from spec)
- **L1:** ≤100 m → Cat6a 10GBASE-T (802.3an). 101–400 m → OM4 10GBASE-SR (850 nm, modal dispersion). >400 m → OS2 10GBASE-LR (≤10 km) / ER (≤40 km), with an optical power budget calculation. Copper requested above 100 m → `PhysicalDistanceViolationError`.
- **VLSM:** root prefix + host array → sort descending → aligned, non-overlapping allocation → network, mask, wildcard, gateway, broadcast, utilization %.
- **Routing:** single AS with <50 subnets → OSPF Area 0. Multi-site → multi-area OSPF. Multi-cloud / multi-AS boundary → eBGP plus summarization.

## 3. Unique features (the differentiators)

### 3.1 Self-verifying configs — "the engine audits itself"
- **Lightweight simulator (core, always on):** parses the *generated IOS text* (not the internal model) into a device model with interfaces, VLANs, SVIs, trunks, static and OSPF routes (computed with our own SPF), and ACLs.
- **Packet tracer:** `trace(src_ip, dst_ip, proto, port)` walks hop by hop. Each hop shows an L2 VLAN check, an L3 longest-prefix match, and the ACL line that matched. Result: delivered / dropped (with the reason) / loop / blackhole.
- **Automatic checks after every design:** full reachability matrix between VLANs, gateway reachability, no overlapping subnets, ACL intent satisfied (e.g. "Guest cannot reach Servers"), no routing loops.
- **Batfish (optional, local only):** if a Batfish Docker container is reachable, the same checks are cross-validated against it. It is not in the deployed build, because Batfish needs about 2 GB RAM and Docker. The UI shows "Batfish: not available, using built-in verifier".
- Why it matters: this is direct evidence for the 20-point AI-audit section ("validated with packet flow analysis").

### 3.2 What-if failure simulator
- Click a link or device in the topology to fail it. OSPF SPF reruns, the new paths are highlighted, and the dual-homed failover in Metro MAN is visible.
- Shows: affected flows, reroute path, metric change, estimated convergence (hello/dead timers, BFD if enabled), and single points of failure (articulation points in the graph).
- A "resilience score" lists every single link and node whose loss partitions the network.

### 3.3 Natural-language input (OpenRouter)
- "3-building campus, 1600 users, PoE APs, guest Wi-Fi isolated, buildings 250 m apart" → LLM → **strict JSON schema** → validated by Pydantic → rule engine.
- **The LLM never makes network decisions.** It only fills the input form. All decisions stay deterministic and explainable.
- The UI shows the extracted parameters for the user to confirm or edit before design runs.
- Model is configurable via env (`OPENROUTER_MODEL`), default is a cheap or free model. Falls back to a regex/keyword parser when no key is set.

### 3.4 GNS3 / Packet Tracer export
- Generates a `.gns3project` zip: topology JSON (nodes, links, coordinates) plus startup-configs per device. Import it and the lab is ready.
- Packet Tracer `.pkt` is a closed binary format, so we export per-device `.cfg` files plus a cabling guide (which port connects to which) for manual building in PT.

### 3.5 Cost / BOM estimator
- Bill of materials: cable meters per type, transceivers (SFP+ SR/LR/ER), switch and router counts, PoE budget (W) for each access switch.
- Approximate INR prices from a static `prices.json` (editable). Each line links back to the decision that caused it ("2× SFP+-LR because the Branch1 link is 22 km").
- "Cheaper alternative" hint where valid (e.g. OM3 instead of OM4 if the distance is ≤300 m).

### 3.6 Design diff & versioning
- Every design run is stored as a version (in browser localStorage plus downloadable JSON; no DB is needed).
- Change one parameter and get a diff in three layers: **decisions changed** (with old vs new rationale), **IP plan changed**, **config lines changed** (unified diff).
- Example: "Distance 380 → 420 m: media changed OM4 → OS2 because…"

### 3.7 Security posture score
- Lint rules on the generated configs: trunk allowed-VLAN not pruned, native VLAN 1, no BPDU guard / PortFast on access ports, unused ports not shut, no `service password-encryption`, telnet enabled, no OSPF authentication, ACL missing implicit-deny logging, and so on.
- Score from 0 to 100, with each finding mapped to the config line and a fix. The engine's own output should score high. Feeding it a "bad AI config" shows the score drop, which ties into the audit log.
- Users can paste their *own* IOS config to lint it.

### 3.8 Exportable PDF report
- One-click architecture report: topology diagram, decision rationale table, IP plan, BOM, verification results, security score, and configs as an appendix.
- Generated client-side (browser print-to-PDF with a print stylesheet), so the server stays light.

## 4. Interfaces (three front-ends, one engine)

| Interface | Tech | Use |
|---|---|---|
| **Web dashboard** | React + Vite + TypeScript, React Flow (topology), Monaco (config view/diff) | Main demo: design, topology, trace, failure sim, BOM, diff, report |
| **CLI** | Typer | Grading and scripting: `netarch design campus_lan --export out/`, `netarch trace …`, `netarch lint cfg.txt` |
| **TUI** | Textual (Rich) | Terminal dashboard: tabs for Decisions / IP Plan / Configs / Verify, live failure toggles |

All three call the same `engine` package, so there is no duplicated logic.

## 5. Architecture

```
            NL text ──► OpenRouter ──► JSON ┐
 Preset / Custom JSON ──────────────────────┤
                                            ▼
                               ┌─ Input Validator (Pydantic) ─┐
                               ▼                              │
     L1/L2 Media Engine ──► Topology Builder ──► VLSM Allocator ──► Routing Selector
            │                     │                    │                 │
            └──────────── Rationale Log (every decision) ◄───────────────┘
                                            ▼
                               Config Generator (Jinja2 IOS)
                                            ▼
             ┌────────── IOS Parser ──► Simulator (SPF, LPM, ACL) ──────────┐
             ▼                  ▼                    ▼                      ▼
        Verifier          What-if Engine       Security Linter         BOM / Cost
             └──────────────► Exporters: cfg, GNS3, JSON, PDF, Diff ◄──────┘
```

### Repo layout (planned)
```
backend/
  engine/        media, vlsm, routing, topology, rationale, configgen, errors, models
  verify/        ios_parser, simulator, spf, trace, checks, batfish_adapter (optional)
  analysis/      whatif, lint, bom, diff
  nl/            openrouter client, schema, fallback parser
  export/        gns3, cfg, json
  presets/       campus_lan.json, metro_man.json, global_wan.json
  templates/     *.j2
  api.py         FastAPI
  cli.py         Typer
  tui.py         Textual
  tests/
frontend/        React + Vite + TS
ai_audit_log.md
idea.md
README.md
```

## 6. Deployment (free tier, lightweight)

- **Frontend:** Vercel (static Vite build).
- **Backend:** Render free web service (FastAPI + uvicorn, 512 MB). Pure Python only: no Docker-only tools, no DB, no heavy ML libraries. Expected idle RAM is under 150 MB.
- **State:** no server DB. Versions are kept in localStorage or exported as JSON.
- **Secrets:** `OPENROUTER_API_KEY` in Render environment variables, never in the frontend.
- **Batfish:** local dev only (`docker run batfish/allinone`), auto-detected.
- Render free tier cold-starts in about 30 s, so the UI shows a "waking server" state.

## 7. Testing strategy
- Unit tests: media thresholds at 100 / 101 / 400 / 401 m, copper >100 m raises an error, wildcard masks for all /0–/32, the /31 (RFC 3021) and /32 cases, exhaustion, and alignment.
- Property tests (Hypothesis): random host arrays never overlap and always fit inside the root.
- Oracle tests: our bitwise allocator compared against Python `ipaddress`.
- Verifier tests: known-good configs reach every destination; injected bugs (wrong mask, missing `switchport trunk allowed vlan`, ACL order) are caught.
- Golden-file tests for the configs of all 3 presets.
- Frontend: a light Vitest smoke test.

## 8. AI audit log plan
Collect real AI mistakes during the build, rather than staging them. Likely candidates:
1. Wildcard mask computed as `~mask` without masking to 32 bits, which gives a negative or overflowing value.
2. Point-to-point link sized /30 when /31 (RFC 3021) was intended, or gateway not excluded from the host count.
3. Trunk with no `allowed vlan` pruning, which leaks the guest VLAN. Shown with a simulator trace: the guest packet reaches the server VLAN.
4. Optical budget that ignores connector and splice loss.

Each entry has: prompt, AI code, symptom, **simulator packet trace proving the bug**, root cause, fix, and a regression test.

## 9. Build phases
1. **Core engine:** models, media, VLSM, routing, rationale, errors, and tests.
2. **Config generation:** Jinja2 templates and the 3 presets exported.
3. **Verifier:** IOS parser, SPF, trace, checks.
4. **Analysis:** what-if, lint, BOM, diff.
5. **Interfaces:** CLI, then FastAPI, then TUI.
6. **Frontend:** React dashboard (topology, trace, failure sim, diff, report).
7. **NL input:** OpenRouter plus fallback.
8. **Exports:** GNS3 project, PDF report.
9. **Deploy:** Render + Vercel, README, audit log finalized.

## 9a. Example walk-through (Metro MAN)
1. Input: HQ ↔ Branch1, 22 km, 10 Gbps, dual-homed, 450 users, root `10.20.0.0/16`.
2. Media: 22 km > 10 km LR limit, so **OS2 + 10GBASE-ER**. Optical budget calculated with ≥3 dB margin → rationale cites IEEE 802.3ae.
3. VLSM: segments sorted descending and allocated bitwise; P2P links get /31 (RFC 3021). Utilization % reported.
4. Routing: multi-site → multi-area OSPF, one area per branch, summaries at the ABRs.
5. Configs generated → parsed back → simulator: every VLAN reaches HQ servers ✓, guest → servers denied ✓.
6. What-if: cut the HQ-R1 uplink → traffic reroutes via HQ-R2, convergence ≈ dead interval (40 s, or faster with BFD).
7. BOM: 4× SFP+ ER, km of OS2, routers, with an INR estimate. Security score 9x/100. Export GNS3 project + PDF.

## 9b. Demo script (viva)
1. Load the Campus preset → topology + rationale cards.
2. Change one building's distance from 380 → 420 m → diff shows OM4 → OS2 with the reason.
3. Request copper at 150 m → `PhysicalDistanceViolationError` explained.
4. Type an NL description → confirm params → design.
5. Packet trace guest → server: dropped at the ACL line shown.
6. Fail a core link → reroute + SPOF list.
7. Paste a buggy AI config → security score drops, verifier shows the leak (ties to the audit log).
8. Export the GNS3 project, open it in GNS3, ping works.

## 9c. Grading map (rubric → feature)
| Rubric | Where it is proven |
|---|---|
| Presets & params (15) | `presets/`, Pydantic validators, typed errors, examples/invalid |
| Explainability (25) | `Rationale` on every decision, decision panel, design_report.md |
| VLSM & configs (25) | bitwise allocator + Hypothesis tests, Jinja2 IOS, simulator proof |
| Unit tests (15) | pytest: distance, exhaustion, wildcard /0–/32, golden configs |
| AI audit (20) | ai_audit_log.md with simulator traces + regression tests |

## 10. Open questions / assumptions
- Prices in INR, from a static table that is approximate and labelled as an estimate.
- Cisco IOS syntax only (no Juniper/Arista).
- IPv4 only; IPv6 is a possible stretch goal.
- Default OpenRouter model to be picked at build time (cheapest capable free model).
