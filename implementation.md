# Implementation Plan — NetArchitect

Phases are ordered by dependency. Each task is small enough for one session.
Tick `[x]` only after code + tests pass and `implemented.md` is updated.
Each phase ends with an **Exit check** that must hold before moving on.

---

## Phase 0 — Project skeleton & tooling
- [x] 0.1 Create layout: `backend/`, `frontend/`, `docs/`, `exports/`
- [x] 0.2 `backend/pyproject.toml` (or `requirements.txt`) with pinned: pydantic, jinja2, fastapi, uvicorn, typer, textual, httpx, pytest, hypothesis
- [x] 0.3 `pytest.ini`, empty `backend/engine/__init__.py`, one trivial passing test
- [x] 0.4 `.gitignore` (venv, node_modules, `__pycache__`, `.env`, exports/tmp)
- [x] 0.5 `.env.example` with `OPENROUTER_API_KEY=`, `OPENROUTER_MODEL=`, `BATFISH_HOST=`
- [x] 0.6 `README.md` stub: setup + run commands

**Exit check:** `pytest -q` passes on a fresh venv.

## Phase 1 — Domain models & errors
- [x] 1.1 `engine/errors.py`: `NetArchError` base; `PhysicalDistanceViolationError`, `AddressSpaceExhaustedError`, `InvalidPrefixError`, `InvalidParameterError`, `TopologyError`
- [x] 1.2 `engine/models.py` input models: `Site`, `Building`, `Link` (distance_m, required_gbps, media_preference), `Segment` (name, vlan, hosts, role: user/voice/guest/server/mgmt/iot), `DesignInput` (profile, root_prefix, sites, links, segments, resiliency, policies)
- [x] 1.3 Output models: `Rationale`, `MediaDecision`, `Subnet`, `RoutingDecision`, `Device`, `Interface`, `DesignResult`
- [x] 1.4 Pydantic validators: positive hosts, VLAN 1–4094 (reject 1 for user data), unique VLAN ids, valid CIDR root
- [x] 1.5 Tests for validation failures

**Exit check:** invalid inputs raise typed errors with clear messages.

## Phase 2 — Rationale engine (explainability core)
- [x] 2.1 `engine/rationale.py`: `Rationale(rule_id, domain, inputs, threshold, standard_ref, text)`
- [x] 2.2 `RationaleLog` collector (append, by_domain, to_markdown, to_json)
- [x] 2.3 Sentence templates per rule id (no free-form strings scattered in code)
- [x] 2.4 Tests: each rule id renders; missing fields raise

**Exit check:** a dummy decision renders a full sentence with a standard citation.

## Phase 3 — L1 media engine
- [x] 3.1 `engine/constants.py`: load thresholds from `docs/standards.md` values (copper 100 m, OM4 400 m, LR 10 km, ER 40 km, loss figures)
- [x] 3.2 `select_media(link)`: ≤100 m Cat6a, 101–400 m OM4 SR, >400 m OS2 LR/ER
- [x] 3.3 Copper preference > 100 m → `PhysicalDistanceViolationError` with attenuation message
- [x] 3.4 Optical power budget calc: fiber loss/km × km + connectors + splices + margin vs transceiver budget → pass/fail + rationale
- [x] 3.5 Distance > ER limit → error (no silent fallback)
- [x] 3.6 Tests at 100/101, 400/401, 10000/10001, 40000/40001 m; copper 101 m error; budget fail case

**Exit check:** every link gets a media decision + rationale, or a typed error.

## Phase 4 — Bitwise VLSM allocator
- [x] 4.1 `engine/bitmath.py`: ip↔int, prefix↔mask, wildcard (`~mask & 0xFFFFFFFF`), network, broadcast, block size, alignment
- [x] 4.2 `hosts_to_prefix(n)`: smallest prefix with `2^(32-p) - 2 ≥ n` (+1 for gateway policy as documented)
- [x] 4.3 `/31` for P2P links (RFC 3021), `/32` loopbacks
- [x] 4.4 `allocate(root, requests)`: sort desc, aligned first-fit, no overlap
- [x] 4.5 Per-subnet: network, mask, wildcard, gateway (first usable), broadcast, usable range, utilization %
- [x] 4.6 Overall efficiency rationale (allocated vs requested vs root)
- [x] 4.7 Exhaustion → `AddressSpaceExhaustedError` with needed vs available
- [x] 4.8 Tests: wildcard for all /0–/32, oracle vs `ipaddress`, Hypothesis no-overlap/inside-root, exhaustion, /31, /32

**Exit check:** Hypothesis 500 random cases, zero overlap.

## Phase 5 — Topology builder
- [ ] 5.1 Tier selection: collapsed core vs three-tier, based on size/buildings (rationale)
- [ ] 5.2 Device generation: core/distribution/access switches, routers, edge/VPN gateways, cloud VPC edge
- [ ] 5.3 Port assignment: access ports per VLAN, uplinks, P2P links
- [ ] 5.4 Access switch count from host density (ports per switch constant) + PoE budget per switch
- [ ] 5.5 Redundancy: dual-homed uplinks when `resiliency=high`
- [ ] 5.6 Topology as graph (plain adjacency dict, no networkx) with coordinates for UI
- [ ] 5.7 Tests: device counts per preset, no orphan ports

**Exit check:** each preset yields a connected graph.

## Phase 6 — L2 decisions
- [ ] 6.1 VLAN plan from segments, 802.1Q trunks with explicit allowed-VLAN lists (never "all")
- [ ] 6.2 Native VLAN = unused dedicated VLAN (not 1)
- [ ] 6.3 RSTP root primary/secondary on core pair
- [ ] 6.4 Access port hardening flags (PortFast, BPDU guard)
- [ ] 6.5 Rationale for each
- [ ] 6.6 Tests: no trunk carries a VLAN with no member on far side

## Phase 7 — L3 routing selector
- [ ] 7.1 Rules: single site & <50 subnets → OSPF area 0; multi-site → multi-area OSPF; multi-AS/cloud → eBGP at boundary
- [ ] 7.2 Area assignment per site, ABR selection
- [ ] 7.3 Route summarization per area (compute aggregates bitwise; verify no over-summarization)
- [ ] 7.4 Router-IDs from loopbacks, OSPF reference bandwidth
- [ ] 7.5 BGP ASN plan (private ASNs), neighbor list
- [ ] 7.6 IPsec tunnel plan for WAN/cloud (peers, protected subnets)
- [ ] 7.7 Tests: rule boundaries (49/50 subnets), summary covers exactly the area's subnets

## Phase 8 — Config generator (Cisco IOS)
- [ ] 8.1 `docs/ios_reference.md` filled for every command used
- [ ] 8.2 Jinja2 templates: base (hostname, banner, services, SSH), access switch, core switch (SVIs, HSRP when redundant), router, OSPF, BGP, ACL, IPsec
- [ ] 8.3 ACLs from policies (e.g. guest → deny internal, permit internet)
- [ ] 8.4 Render per device to `.cfg`
- [ ] 8.5 Golden-file tests for 3 presets; config uses no command missing from `ios_reference.md` (test enforced)

**Exit check:** 3 preset configs export cleanly.

## Phase 9 — Presets & custom input
- [ ] 9.1 `presets/campus_lan.json` (3 buildings, <400 m, 1600 endpoints, PoE APs)
- [ ] 9.2 `presets/metro_man.json` (HQ + 2 remotes 15–35 km, 450 users, colo, dual-homed, QoS)
- [ ] 9.3 `presets/global_wan.json` (4 cities + cloud VPC, 2000 IoT, IPsec, multi-area/BGP)
- [ ] 9.4 `examples/` invalid inputs (copper 150 m, exhausted root, bad VLAN)
- [ ] 9.5 `engine/planner.py` orchestrator: input → full `DesignResult`
- [ ] 9.6 Tests: each preset end-to-end; each invalid example raises the right error

## Phase 10 — IOS parser (verification input)
- [ ] 10.1 Parse generated `.cfg` back: hostname, interfaces, IP/mask, switchport mode/VLANs, SVIs, static routes, OSPF networks/areas, BGP neighbors, ACLs, ACL bindings
- [ ] 10.2 Round-trip test: generate → parse → matches model

## Phase 11 — Simulator & packet tracer
- [ ] 11.1 Build L2 domains from parsed trunks/access ports
- [ ] 11.2 SPF (Dijkstra) per OSPF area + inter-area routes; BGP simplified best-path
- [ ] 11.3 RIB per device with AD; FIB longest-prefix match
- [ ] 11.4 ACL evaluator (first match, implicit deny)
- [ ] 11.5 `trace(src, dst, proto, port)` → hop list with reason per hop; outcomes: delivered/dropped/loop/no-route
- [ ] 11.6 Tests: hand-built mini topologies with known answers

## Phase 12 — Automated verifier
- [ ] 12.1 Reachability matrix between all segments
- [ ] 12.2 Policy intent checks (expected allow/deny pairs from input policies)
- [ ] 12.3 Gateway reachability, no overlap, no loop
- [ ] 12.4 `VerificationReport` with pass/fail + traces
- [ ] 12.5 Bug-injection tests: wrong mask, unpruned trunk, ACL order swapped → verifier catches each

## Phase 13 — Batfish adapter (optional, local)
- [ ] 13.1 Detect `BATFISH_HOST`; skip cleanly if absent
- [ ] 13.2 Upload snapshot, run reachability + undefined-references questions
- [ ] 13.3 Compare with own verifier, report differences
- [ ] 13.4 Test marked `@pytest.mark.batfish` (skipped by default)

## Phase 14 — What-if failure engine
- [ ] 14.1 Fail link / node → rebuild graph → rerun SPF → new paths
- [ ] 14.2 Affected flows diff (before vs after trace)
- [ ] 14.3 Convergence estimate from timers (values from standards.md)
- [ ] 14.4 Single points of failure (articulation points + bridges)
- [ ] 14.5 Resilience score + rationale
- [ ] 14.6 Tests: Metro MAN survives single HQ uplink loss; campus SPOF detected

## Phase 15 — Security linter
- [ ] 15.1 Rule set (each with id, severity, fix): unpruned trunk, native VLAN 1, no BPDU guard, unused ports up, telnet, no password encryption, no OSPF auth, no SSH v2, ACL without explicit deny log
- [ ] 15.2 Score 0–100 with weights
- [ ] 15.3 Lint arbitrary pasted IOS
- [ ] 15.4 Tests: generated configs ≥ threshold; bad sample fails expected rules

## Phase 16 — BOM / cost estimator
- [ ] 16.1 `data/prices.json` (INR, labelled estimate, editable)
- [ ] 16.2 Counts: cable m per type (+slack %), transceivers, switches, routers, PoE watts
- [ ] 16.3 Each line linked to decision rule id
- [ ] 16.4 Cheaper-alternative hints (only when constraints still satisfied)
- [ ] 16.5 Tests: counts per preset

## Phase 17 — Design diff & versioning
- [ ] 17.1 Serialize `DesignResult` as versioned JSON
- [ ] 17.2 Diff layers: decisions (old/new rationale), IP plan, configs (unified diff)
- [ ] 17.3 Tests: changing distance 380 → 420 flips media with rationale diff

## Phase 18 — Exporters
- [ ] 18.1 Per-device `.cfg` + `design_report.md` + `design.json`
- [ ] 18.2 GNS3 `.gns3project` zip (topology JSON + configs); verify schema against a real GNS3 export before claiming support
- [ ] 18.3 Packet Tracer cabling guide (port-to-port table)
- [ ] 18.4 Commit `exports/` for 3 presets (owner commits)

## Phase 19 — CLI (Typer)
- [ ] 19.1 `netarch design <preset|file> --export DIR`
- [ ] 19.2 `netarch explain`, `netarch verify`, `netarch trace SRC DST`, `netarch fail LINK`
- [ ] 19.3 `netarch lint FILE`, `netarch bom`, `netarch diff A B`, `netarch nl "text"`
- [ ] 19.4 Exit codes per error type; tests with `CliRunner`

## Phase 20 — FastAPI backend
- [ ] 20.1 Endpoints: `/presets`, `/design`, `/verify`, `/trace`, `/whatif`, `/lint`, `/bom`, `/diff`, `/nl`, `/export/{fmt}`, `/health`
- [ ] 20.2 Error → HTTP mapping (422 with typed error body)
- [ ] 20.3 CORS for Vercel domain only
- [ ] 20.4 Rate limit on `/nl`
- [ ] 20.5 Tests with `TestClient`

## Phase 21 — Natural-language input (OpenRouter)
- [ ] 21.1 JSON schema for `DesignInput` sent to model (structured output)
- [ ] 21.2 httpx client, timeout, retries, model from env
- [ ] 21.3 Validate response with Pydantic; on failure return field errors, never auto-fill decisions
- [ ] 21.4 Offline regex/keyword fallback parser
- [ ] 21.5 Tests with mocked HTTP (no real key in tests)

## Phase 22 — TUI (Textual)
- [ ] 22.1 Preset picker + run
- [ ] 22.2 Tabs: Decisions, IP Plan, Configs, Verify, What-if, BOM, Lint
- [ ] 22.3 Link toggle for failure sim
- [ ] 22.4 Smoke test with Textual pilot

## Phase 23 — Frontend setup
- [ ] 23.1 Vite + React + TS, ESLint, Vitest
- [ ] 23.2 API client (typed from backend OpenAPI), env `VITE_API_URL`
- [ ] 23.3 Layout, routing, theme (light/dark), "server waking" state

## Phase 24 — Frontend features
- [ ] 24.1 Input: preset picker, JSON editor, NL box with confirm-extracted-params step
- [ ] 24.2 Topology view (React Flow), media colored per link
- [ ] 24.3 Decisions panel (rationale cards grouped by domain)
- [ ] 24.4 IP plan table with utilization bars
- [ ] 24.5 Config viewer (Monaco) + download
- [ ] 24.6 Packet trace tool: pick src/dst, animate path
- [ ] 24.7 What-if: click link/node to fail, show reroute + SPOFs
- [ ] 24.8 Security score panel + paste-your-config linter
- [ ] 24.9 BOM table + totals
- [ ] 24.10 Versions (localStorage) + diff view
- [ ] 24.11 Print-stylesheet PDF report
- [ ] 24.12 Vitest smoke tests

## Phase 25 — Deployment
- [ ] 25.1 `render.yaml` (backend, free plan, health check)
- [ ] 25.2 Vercel config for frontend
- [ ] 25.3 Env vars set (owner)
- [ ] 25.4 Measure backend RAM idle/peak; must stay < 400 MB

## Phase 26 — AI audit log & final docs
- [ ] 26.1 ≥2 real entries in `ai_audit_log.md`, each with simulator packet trace proof + regression test
- [ ] 26.2 README final: features, screenshots, run, deploy, test
- [ ] 26.3 Load 3 preset exports into Packet Tracer/GNS3, screenshot proof in `docs/proof/`
- [ ] 26.4 Rubric self-check against PDF (each row mapped to file/test)
