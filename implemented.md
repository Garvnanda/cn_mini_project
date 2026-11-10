# Implemented — NetArchitect

Source of truth for what exists and works. Update after every completed task.
Only list items whose tests were actually run and passed.

## Format
```
### <task id> — <title>  (YYYY-MM-DD)
- Files: path, path
- Tests: `pytest -q tests/test_x.py` → N passed
- Notes: limits, known gaps, anything unverified
```

## Status summary
| Phase | Status |
|---|---|
| 0 Skeleton | done |
| 1 Models & errors | done |
| 2 Rationale engine | done |
| 3 L1 media engine | done (loss constants UNVERIFIED) |
| 4 Bitwise VLSM | done |
| 5 Topology builder | done |
| 6 L2 decisions | done |
| 7 Routing selector | done |
| 8 Config generator | done (PT compatibility unchecked) |
| 9 Presets | done |
| 10 IOS parser | done |
| 11 Simulator | done |
| 12 Verifier | done |
| 13 Batfish adapter | code written; live run UNVERIFIED (13.2, 13.3 open) |
| 14 What-if | done |
| 15 Security linter | done |
| 16 BOM | done (placeholder prices) |
| 17 Diff & versioning | done |
| 18 Exporters | done except 18.2 GNS3 (deferred, D-030) |
| 19 CLI | done |
| 20 FastAPI | done |
| 21 NL input | done (OpenRouter path UNVERIFIED without a real key; offline parser tested) |
| 22 TUI | done |
| 23 Frontend setup | done |
| 24 Frontend features | done |
| 25 Deployment | config + DEPLOY.md done, RAM measured; owner deploys (DEPLOY.md) |
| 26 Audit & docs | done except 26.3 Packet Tracer screenshots (owner) |

## Done
### Docs bootstrap  (2026-11-10)
- Files: `idea.md`, `CLAUDE.md`, `implementation.md`, `implemented.md`, `ai_audit_log.md`, `docs/standards.md`, `docs/ios_reference.md`, `docs/decisions.md`
- Tests: n/a (no code yet)
- Notes: old phase-1 demo deleted; fresh start.

### Phase 0 — Skeleton & tooling  (2026-11-10)
- Files: `backend/requirements.txt` (runtime, pinned), `backend/requirements-dev.txt` (+pytest, hypothesis), `backend/pytest.ini`, `backend/engine/__init__.py`, `backend/tests/test_smoke.py`, `.gitignore`, `.env.example`, `README.md`; dirs `backend/{engine,tests,presets,templates}`, `frontend/`, `exports/`
- Venv: `backend/.venv` (Python 3.11.7). Pinned: pydantic 2.14.3, Jinja2 3.1.6, fastapi 0.162.2, uvicorn 0.54.0, typer 0.29.0, textual 8.2.8, httpx 0.28.1, pytest 9.2.0, hypothesis 6.170.15
- Notes: used `requirements.txt` instead of `pyproject.toml`. Run tests from `backend/`.

### Phase 1 — Domain models & errors  (2026-11-10)
- Files: `backend/engine/errors.py`, `backend/engine/models.py`, `backend/tests/test_models.py`
- Errors: `NetArchError` (message + details, `to_dict()` → `{type, message, details}`) and subclasses `PhysicalDistanceViolationError`, `AddressSpaceExhaustedError`, `InvalidPrefixError`, `InvalidParameterError`, `TopologyError`
- Input models: `Site`, `Building`, `Link`, `Segment`, `Policy`, `DesignInput`; enums `Profile`, `SiteKind`, `SegmentRole`, `MediaPreference`, `Resiliency`, `PolicyAction`. All input models use `extra="forbid"`.
- Validation: VLAN 2–4094 (VLAN 1 rejected); hosts ≥ 1; distance > 0; root prefix strict CIDR (host bits must be 0, length required); unique site/building/segment names and VLAN ids; every link, segment and policy reference must exist; link ends must differ.
- `parse_design_input(dict)` converts Pydantic errors to `InvalidPrefixError` (root prefix) or `InvalidParameterError` (all others), with a per-field error list.
- Output models: `Rationale`, `MediaDecision`, `Subnet`, `RoutingDecision`, `Interface`, `Device`, `DesignResult`
- Tests: `cd backend && .venv/Scripts/python -m pytest` → 32 passed
- Notes: `Rationale` model lives in `models.py`; Phase 2 adds the collector/templates in `rationale.py`. `ipaddress` is used only for root-prefix parsing (allowed by D-007).

### Phase 2 — Rationale engine  (2026-11-10)
- Files: `backend/engine/rationale.py`, `backend/tests/test_rationale.py`
- `RULES` registry: rule_id -> (domain, standard_ref, threshold, template). 14 rules: L1.copper, L1.mmf, L1.smf_lr, L1.smf_er, L1.budget, L1.copper_violation, L1.mmf_violation, L1.distance_exceeded, L1.budget_violation, VLSM.subnet, VLSM.p2p, VLSM.loopback, VLSM.efficiency, VLSM.exhausted
- `explain(rule_id, **inputs)` -> `Rationale`; unknown rule or missing field -> `RationaleError` (a `NetArchError`)
- `RationaleLog`: add, extend, by_domain, to_json, to_markdown
- Tests: every rule renders and cites IEEE/RFC/TIA; error cases; log export

### Phase 3 — L1 media engine  (2026-11-10)
- Files: `backend/engine/constants.py`, `backend/engine/media.py`, `backend/tests/test_media.py`
- `select_media(link, splices=0)`: AUTO ≤100 m Cat6a/10GBASE-T, ≤400 m OM4/10GBASE-SR, else OS2 LR (≤10 km) or ER (≤40 km). Honors copper/multimode/singlemode preferences.
- Errors: copper >100 m and multimode >400 m -> `PhysicalDistanceViolationError` (attenuation/dispersion text); >40 km -> error; ER budget fail -> error; >10 Gb/s -> `InvalidParameterError`
- `optical_budget()`: fiber + connectors + splices vs channel insertion loss; LR budget fail auto-upgrades to ER with rationale; margin < 3 dB warns (D-012)
- Tests: boundaries 100/101, 400/401, 10000/10001, 38 km, 40 km, 40001 m; budget math, fail, low-margin
- Known gap: OS2 dB/km and channel-loss constants are UNVERIFIED (see standards.md). With them, 40 km ER fails budget; 38 km passes. Splice count is a parameter (default 0); `Link` has no splice field yet.

### Phase 4 — Bitwise VLSM  (2026-11-10)
- Files: `backend/engine/bitmath.py`, `backend/engine/vlsm.py`, `backend/tests/test_bitmath.py`, `backend/tests/test_vlsm.py`
- bitmath: ip<->int, prefix<->mask (contiguity check), wildcard (`~mask & 0xFFFFFFFF`), network, broadcast, block size, alignment, CIDR parse (rejects host bits), usable hosts (/31=2, /32=1), `hosts_to_prefix` (reserves gateway, D-013)
- `allocate(root, [AllocRequest])`: kinds lan / p2p (/31) / loopback (/32); largest-first with one aligned cursor (alignment asserted); per-subnet network, mask, wildcard, gateway, broadcast, usable range, utilization; efficiency rationale; `AddressSpaceExhaustedError` with needed/available and minimum root prefix
- Tests: masks/wildcards for all /0-/32 vs `ipaddress`; oracle check of allocations; /31, /32; exact fit; exhaustion; Hypothesis 500 random cases, no overlap, inside root
- Run: `cd backend && .venv/Scripts/python -m pytest` -> 145 passed

### Phases 5-8 + 9.5 — Topology, L2, routing, configs, planner  (2026-11-10)
- Files: `backend/engine/topology.py`, `l2.py`, `routing.py`, `acl.py`, `configgen.py`, `planner.py`; `backend/templates/*.j2` (base, l2, interfaces, acl, ospf, bgp, ipsec, lines, access_switch, core_switch, router); tests `test_topology.py`, `test_l2.py`, `test_routing.py`, `test_configs.py`, `conftest.py`; fixtures `tests/fixtures/{campus,metro,wan,three_tier}.json`; golden configs `tests/golden/<fixture>/*.cfg`
- Model changes: `Link.transport` (fiber / carrier / internet); `Policy.proto` limited to ip/tcp/udp/icmp, port only with tcp/udp, src != dst; new output models `Cable`, `OspfConfig`, `BgpConfig`, `Acl`, `AclEntry`, `StaticRoute`; `Interface` and `Device` extended; `DesignResult` gains `cables`, `tiers`. VLSM gained `kind="block"` (power-of-two container).
- Topology: per site collapsed core (< 4 buildings) or three-tier (≥ 4); core pair, distribution pair and HQ/DC router pair when resiliency=high; access stacks of 48-port members (≤ 8 per stack) sized from host counts, ports assigned per segment as `interface range`, spare ports shut; PoE watts per stack; access stacks dual-homed to both gateways; inter-site links between routers (dual-homed when one side has 2 routers); internet links become underlay + IPsec VTI tunnel; cloud site = one VGW with routed VPC subnets. TopologyError for a building with no link to its gateway building and for sites not connected to the backbone. `graph()` gives nodes/edges with a layered layout for the UI.
- L2: native/parking VLAN 999 (or highest free), trunks pruned to VLANs present behind them, Rapid PVST+ root primary/secondary on the gateway pair, PortFast + BPDU Guard on access ports, SVIs on gateways with HSRPv2 (VIP = first usable, physical SVIs = next two) when paired.
- Routing: `select_protocol` (multi-site -> multi-area; < 50 subnets -> area 0; >= 50 -> multi-area if three-tier else flat with warning). Areas per site (backbone = first HQ/DC) or per building block. Hierarchical addressing: one power-of-two block per area / cloud, then VLSM inside, so each ABR summarizes its area with `area N range`. Loopback0 /32 router IDs, reference bandwidth 100000. eBGP to cloud VGW (AS 65000 <-> 65100+) with Null0 discard statics, `network` statements and `redistribute bgp`. IPsec underlay from 203.0.113.0/24 (RFC 5737). Area 0 contiguity check (each site needs a direct link to the backbone site).
- ACLs: one extended ACL per policy source segment, policy order kept, ends `permit ip any any`, applied inbound on the source gateway SVI(s).
- Configs: role templates; StrictUndefined; test fails on any IOS line whose prefix is not in `docs/ios_reference.md`.
- Tests: `cd backend && .venv/Scripts/python -m pytest` -> 246 passed
- Known gaps / UNVERIFIED:
  - Packet Tracer compatibility not checked (interface names are Catalyst 9300/9500/ISR style; PT 3560 may need `switchport trunk encapsulation dot1q`; HSRPv2 and IPsec VTI in PT unverified).
  - Access switches have no management IP yet.
  - No QoS for the Metro MAN sub-5 ms requirement yet.
  - Passwords and the IPsec PSK are `CHANGE_ME_*` placeholders.
  - Golden files are regenerated with `UPDATE_GOLDEN=1 pytest tests/test_configs.py` (only on purpose).

### Phases 9-13 — Presets, IOS parser, simulator, verifier, Batfish adapter  (2026-11-10)
- Presets (`backend/presets/`): `campus_lan.json` (3 buildings, links 180/280/350 m, 1600 endpoints, PoE voice + APs, guest isolation), `metro_man.json` (HQ + Branch 22 km + Colo datacenter 35 km, single-mode fiber, 450 users, resiliency high, Branch -> Colo-Trading allow tcp 443 then deny), `global_wan.json` (Delhi HQ, Mumbai/Bengaluru via carrier, Singapore + CloudVPC via internet IPsec, 2000 IoT, eBGP to cloud).
- Examples (`backend/examples/`): `invalid_copper_150m.json` -> PhysicalDistanceViolationError, `invalid_exhausted.json` -> AddressSpaceExhaustedError, `invalid_bad_vlan.json` -> InvalidParameterError, `custom_small_office.json` (valid).
- `verify/ios_parser.py`: parses IOS text into `PDevice` (hostname, ip routing, VLANs, STP roots, interfaces incl. ranges/switchport/trunk lists/HSRP/ACL bindings/tunnels, OSPF, BGP, statics with optional distance, extended ACLs with any/host/wildcard and eq port, isakmp peers). Unknown top-level lines go to `unparsed`; malformed interface lines raise `ParseError` with line number.
- `verify/simulator.py`: built only from parsed configs + physical cabling. Per-VLAN L2 domains (trunk must allow the VLAN on both ends and the VLAN must exist), links over routed cables / shared L2 domain / IPsec tunnels, RIB from connected, static (floating distance honored), OSPF (Dijkstra, ABR summaries hide component routes outside their area, ABR Null0 summary route, BGP redistribution as external), eBGP (session needs matching neighbor/remote-as both ways; `network` needs exact RIB match). LPM then AD then metric. ACLs first-match with implicit deny. HSRP active = highest priority. `trace(src, dst, proto, port)` -> hop list, outcome delivered / dropped / no-route / loop.
- `verify/verifier.py`: `verify(design, configs=None)` -> `VerificationReport` with checks config_parse, gateway_reachability, reachability_and_policy (every segment pair by ICMP + each policy's own proto/port, compared with intent from the policies), no_routing_loops, no_overlapping_subnets, access_trunk_scope (access stacks are leaves).
- `verify/batfish_adapter.py`: skipped unless `BATFISH_HOST` set and pybatfish installed (`backend/requirements-batfish.txt`, dev/local only); uploads snapshot, asks undefinedReferences + traceroute per probe, compares with own verdicts. UNVERIFIED against a live server.
- Fix during this phase: eBGP Null0 anchor statics are now floating (AD 254). See ai_audit_log.md entry 2.
- Simulator fix: static routes with an IP next hop resolve the egress interface recursively.
- Tests: `test_presets.py`, `test_parser.py` (round trip of every device of all 7 designs), `test_simulator.py` (hand-built 2-router and 2-switch topologies), `test_verifier.py` (all designs pass; injected wrong mask, unpruned trunk, ACL order swap, AD-1 Null0, shutdown gateway, overlapping subnet are each caught), `test_batfish.py`.
- Golden files regenerated on purpose: new presets added; `wan` fixture changed by the AD 254 fix.
- Run: `cd backend && .venv/Scripts/python -m pytest` -> 330 passed, 1 skipped (live Batfish)
- Known gaps / UNVERIFIED: interface bandwidths used for OSPF cost (TenGig 10000, Gig/Vlan 1000, Tunnel 0.1 Mb/s) are [verify]; sim ignores STP blocking (L2 domains only), ARP/return-path is not traced separately (each ordered pair is probed one way, both directions are covered by the matrix); hosts are modelled one per segment (last usable address).

### Completion pass on Phases 0-13  (2026-11-10)
- Latency budget (closes the 9.2 "sub-5 ms" gap at the design level): `Link.max_latency_ms`, `media.check_latency()` (5 µs/km propagation), rules `L1.latency` / `L1.latency_violation`; Metro preset links carry `max_latency_ms: 5` (35 km -> 0.175 ms). QoS config itself not generated (needs new IOS commands; owner OK pending).
- Topology fix found by Phase 14 SPOF analysis: a lone router now uplinks to every core (D-025, ai_audit_log.md entry 3). Goldens for `metro` and `metro_man` regenerated on purpose.
- Still open: 13.2 / 13.3 need a live Batfish container (Docker is installed but its daemon was not running).

### Phases 14-19 — What-if, linter, BOM, diff, exporters, CLI  (2026-11-10)
- `analysis/whatif.py`: `simulate_failure(design, links=["A--B" | "A:IF--B:IF"], nodes=[...])` shuts interfaces in the parsed configs, re-runs the full segment-pair matrix and reports broken / rerouted / unaffected flows with before/after paths; convergence rationale `WHATIF.ospf` (dead 40 s / hello 10 s), `WHATIF.hsrp` (hold 10 s / hello 3 s), `WHATIF.rstp`. `spof_analysis(design)`: removes each non-access device and each cable, reports elements that separate segment-hosting devices, resilience score (campus_lan 100, metro_man 97, global_wan 4).
- `analysis/lint.py`: 13 rules SEC-01..13 (unpruned trunk, native VLAN 1, no BPDU Guard, no PortFast, port left in VLAN 1, telnet/unrestricted VTY, no password encryption, no SSHv2, OSPF without auth, no enable secret, CHANGE_ME placeholders, ACL ends permit any (info), VTY without login). `lint_configs()` for designs, `lint_text()` for pasted IOS (parser `strict=False`). Generated presets score 86-90.
- Parser additions: services, ssh v2, enable secret/password, placeholder detection, `line vty` transport/login/password, OSPF auth (area + interface), non-strict mode.
- `analysis/bom.py` + `data/prices.json` (PLACEHOLDER INR prices): cable meters per media (+10 % slack), optics per cable end, PoE vs non-PoE access members, core/distribution/routers/VGW, monthly carrier/internet circuits, PoE watts per stack; every line names its rule id; OM3 / Cat6 hints only when every run fits (300 m / 55 m).
- `analysis/diff.py`: versioned snapshot (`version: 1`) + `load_snapshot`; diff of decisions (grouped by rule family + identifying inputs, e.g. `L1.media[link=BldgA--BldgC]` L1.mmf -> L1.smf_lr), IP plan, per-device unified config diff, devices added/removed.
- `export/exporter.py`: per-device .cfg, `design.json`, `design_report.md` (summary, media, IP plan, rationale, verification, security findings, SPOFs, BOM), `cabling_guide.md` (port-to-port table for Packet Tracer). `exports/{campus_lan,metro_man,global_wan}/` regenerated (owner commits).
- `cli.py` (Typer): `design [--export]`, `explain [--domain]`, `verify`, `trace TARGET SRC DST [--proto --port]` (segment names or IPs), `fail [--link] [--node]` (no options = SPOF report), `lint FILE|TARGET`, `bom`, `diff A B`. Exit codes: InvalidParameter 2, InvalidPrefix 3, PhysicalDistance 4, AddressSpace 5, Topology 6, verify/trace/fail failure 1. UTF-8 output forced on Windows. Run: `cd backend && .venv/Scripts/python cli.py --help`.
- Tests: `test_whatif.py`, `test_lint.py`, `test_bom.py`, `test_diff.py`, `test_export.py`, `test_cli.py`, latency tests in `test_media.py`.
- Run: `cd backend && .venv/Scripts/python -m pytest` -> 391 passed, 1 skipped (live Batfish)
- Not done: 18.2 GNS3 project (D-030), `nl` command (Phase 21).

### Phases 20-26 + loose ends — API, NL, TUI, frontend, deployment, docs  (2026-11-10)
- Loose ends: OSPF MD5 authentication (D-031) and LLQ QoS on latency-budget links (D-032): models, routing, `engine/qos.py`, templates (`qos.j2`, ospf/interface lines), parser (class-map/policy-map, service-policy, OSPF key), simulator auth check, `docs/ios_reference.md` rows. Generated configs now score 92/100 (only CHANGE_ME placeholders and the info-level default-allow ACL remain).
- Bug fixed: rule thresholds containing `{field}` were returned unformatted; `explain()` now formats them and the test checks it.
- `backend/api.py` (FastAPI): `/health`, `/presets`, `/presets/{name}`, `/design` (bundle), `/verify`, `/trace`, `/whatif`, `/spof`, `/lint` (text or input), `/bom`, `/diff`, `/nl` (per-IP limit, env `NL_RATE_PER_MIN`, 4000-char cap), `/export/{zip|json|report|cabling}`. NetArchError -> 422 `{type, message, details}`. CORS from env `CORS_ORIGINS` (default http://localhost:5173).
- `backend/nl/`: `extract(text)` -> `NLResult` (source, input, valid, errors, assumptions, missing, note). OpenRouter client (`json_object` response, schema in system prompt, 30 s timeout, 2 retries on 5xx/429/transport errors, model from `OPENROUTER_MODEL`); invalid LLM output is reported, never auto-corrected. Offline parser copies only stated facts and lists missing ones (never invents distances).
- `backend/tui.py` (Textual): preset picker, tabs Decisions / IP Plan / Configs / Verify / What-if (fail any link or non-access device) / BOM / Lint.
- `backend/cli.py`: added `nl "text" [--out FILE]`.
- `frontend/` (Vite 8, React 19, TS 5.9, ESLint, Vitest + jsdom 29): input panel (preset, editable JSON, plain-English extraction with confirm step), Network tab (SVG topology coloured by media, animated packet trace, click-to-fail what-if, SPOF highlight), Decisions, IP Plan (utilization bars), Configs (download/copy), Verify, Security (+ paste-your-config linter), BOM, Versions (localStorage + diff), Report (print-to-PDF stylesheet + zip/md/json/cabling downloads), light/dark/auto theme, "waking server" state. `npm run lint`, `npm test` (4 tests), `npm run build` (248 kB JS, 76 kB gzip) all pass.
- Deployment: `render.yaml` (free web service, `uvicorn api:app`, health check, env vars), `frontend/vercel.json`. Measured locally with uvicorn: 56 MB idle, 60 MB after designing all 3 presets; `/design` 0.24-0.31 s.
- Docs: `README.md` final, `docs/rubric_check.md`, `docs/proof/README.md` (what screenshots to take), decisions D-031..D-034.
- Exports for the 3 presets regenerated (`exports/`).
- Tests: `cd backend && pytest` -> 420 passed, 1 skipped (live Batfish); `cd frontend && npm test` -> 4 passed.
- Open (owner): 13.2/13.3 live Batfish run, 18.2 GNS3 export (D-030), 25.3 env vars + deploy, 26.3 Packet Tracer screenshots. Verify `[verify]`/`?` items in standards.md / ios_reference.md.

### Owner hand-off support  (2026-11-10)
- `backend/engine/env.py`: stdlib `.env` loader (real env vars win), called at start of `api.py`, `cli.py`, `tui.py`; `backend/.env.example` lists every setting; `backend/.env` is git-ignored (checked with `git check-ignore`). Test: `tests/test_env.py`.
- `DEPLOY.md`: step-by-step Render (blueprint) + Vercel + CORS + live checks.
- Run: `cd backend && pytest` -> 422 passed, 1 skipped.
