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
| 9 Presets | 9.5 planner done; presets/examples not started |
| 10–26 | not started |

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
