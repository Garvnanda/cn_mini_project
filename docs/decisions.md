# Decision Log (ADR-lite)

Append-only. Format: `D-NNN — title (date)` · Context · Decision · Why · Consequence.
Do not change a decision without adding a new entry that supersedes it.

### D-001 — Fresh rewrite (2026-11-10)
- Decision: delete phase-1 demo, rebuild from scratch per `idea.md`.

### D-002 — Stack (2026-11-10)
- Decision: Python 3.11 backend (FastAPI, Pydantic v2, Jinja2, Typer, Textual, pytest+Hypothesis); React + Vite + TS frontend.
- Why: `ipaddress` oracle, pytest required by spec, light enough for Render free.

### D-003 — One engine, three front-ends (2026-11-10)
- Decision: web, CLI, TUI are thin shells over `backend/engine`.

### D-004 — LLM fills inputs only (2026-11-10)
- Decision: OpenRouter converts NL → `DesignInput` JSON. It never makes design decisions. User confirms extracted params.
- Why: explainability + determinism; avoids hallucinated designs.

### D-005 — Own verifier is primary, Batfish optional (2026-11-10)
- Decision: built-in IOS parser + simulator always runs; Batfish only when `BATFISH_HOST` set (local Docker).
- Why: Batfish needs Docker + ~2 GB RAM; Render free = 512 MB.

### D-006 — No server database (2026-11-10)
- Decision: versions in browser localStorage + JSON download.

### D-007 — Bitwise core math (2026-11-10)
- Decision: VLSM/mask math via integer bit ops; `ipaddress` only as test oracle / parsing.
- Why: rubric demands bitwise allocation.

### D-008 — Typed errors (2026-11-10)
- Decision: `NetArchError` hierarchy (see implementation.md Phase 1.1). API maps to 422 with `{type, message, details}`.

### D-009 — Optical design margin 3 dB (2026-11-10)
- Decision: power budget must leave ≥ 3 dB margin. Project choice, stated in rationale.

### D-010 — Packet Tracer export (2026-11-10)
- Decision: `.pkt` is closed binary → export `.cfg` + cabling guide. GNS3 project zip supported.

### D-011 — Git owned by user (2026-11-10)
- Decision: AI never commits or pushes.

### D-012 — Optical budget rule (2026-11-10, supersedes D-009)
- Context: D-009 (3 dB margin required) made 10GBASE-LR fail at ~2 km and ER fail for the Metro MAN 35 km links, because the IEEE channel insertion loss figures already include allowances.
- Decision: pass when total loss ≤ max channel insertion loss of the transceiver. Margin < 3 dB passes with a warning in the rationale (recommend OTDR test). If LR fails its budget, upgrade to ER with an explanation; if ER fails, raise `PhysicalDistanceViolationError`.
- Values for OS2 loss and channel insertion loss are marked [verify] in standards.md.

### D-013 — Gateway reserved in host sizing (2026-11-10)
- Decision: LAN subnet must hold requested hosts + 1 gateway (first usable address). Utilization = (hosts + 1) / usable.
- P2P links use /31 (no gateway, no broadcast); loopbacks use /32.

### D-014 — Only 10G transceivers modelled (2026-11-10)
- Decision: `required_gbps > 10` raises `InvalidParameterError`. Keeps scope inside the assignment's 10GBASE rules.

### D-015 — Rationale templates central (2026-11-10)
- Decision: all justification text lives in `engine/rationale.py` `RULES`; engine code calls `explain(rule_id, **inputs)`. `Rationale` model stays in `models.py` and is re-exported.

### D-016 — Hierarchical addressing per area (2026-11-10)
- Decision: when the design has more than one OSPF area or a cloud site, each area/cloud gets one power-of-two block from the root, then VLSM runs inside it. Single-area designs allocate straight from the root.
- Why: makes `area N range` summaries exact (no over-summarization); costs some padding.

### D-017 — Topology shape (2026-11-10)
- Collapsed core when a site has < 4 buildings, three-tier at >= 4 (project threshold). Gateways (SVIs) on cores (collapsed) or distribution (three-tier).
- Access = stacks of 48-port members, max 8 per stack. Every building needs a direct input link to its gateway building.
- resiliency=high pairs cores, distribution switches and HQ/DC routers; branches keep one router, dual-homed to both HQ routers.

### D-018 — HSRP sizing (2026-11-10)
- Decision: paired gateways use HSRPv2 (group = VLAN id, needs v2 for ids > 255). VIP = first usable; the two physical SVIs take the next two addresses, so each paired LAN requests hosts + 2 extra (on top of D-013).

### D-019 — WAN transports (2026-11-10)
- `Link.transport`: fiber (L1 engine designs it), carrier (EVPL/MPLS, provider owns L1, routed /31), internet (underlay /31 from RFC 5737 203.0.113.0/24 + route-based IPsec VTI, IKEv1 AES-256/SHA-256/DH14).
- Cloud sites: single VGW, eBGP with private ASNs (enterprise 65000, cloud 65100+), enterprise advertises area blocks via Null0 statics and redistributes BGP into OSPF.

### D-020 — Default-allow ACLs (2026-11-10)
- Policies are exceptions: each source ACL ends with `permit ip any any`; applied inbound on the source gateway.

### D-021 — Floating Null0 anchors for BGP (2026-11-10)
- Context: AD-1 Null0 statics used to satisfy BGP `network` blackholed remote OSPF areas (found by the verifier, ai_audit_log.md entry 2).
- Decision: anchor statics use distance 254, so any OSPF route for the same prefix wins and the static only fills in when OSPF has none.

### D-022 — Verifier inputs (2026-11-10)
- Decision: the verifier reads only the rendered config text plus the physical cabling list (cabling is not in configs) and one representative host per segment (last usable address, gateway from the design). Intent comes from input policies with default-allow (D-020).

### D-023 — Access stacks are leaves (2026-11-10)
- Decision: trunks touching an access stack may only carry VLANs that have access ports on that stack; anything more is reported by `access_trunk_scope`.

### D-024 — Batfish optional dependency (2026-11-10)
- Decision: pybatfish lives in `requirements-batfish.txt` (local only, pulls pandas); never in the Render build. Adapter imports it lazily.

### D-025 — Lone router uplinks to every core (2026-11-10)
- Decision: when a site has as many routers as cores they pair 1:1; otherwise each router connects to every core. Found by SPOF analysis (ai_audit_log.md entry 3).

### D-026 — Latency budget per link (2026-11-10)
- Decision: optional `Link.max_latency_ms` (one-way). Engine checks propagation only (5 µs/km); exceeding it raises `PhysicalDistanceViolationError`. Metro preset sets 5 ms. QoS configuration (priority queuing) is not generated yet: it needs new IOS commands in ios_reference.md, pending owner confirmation.

### D-027 — Security score (2026-11-10)
- Decision: 13 rules (SEC-01..13), weights high 15 / medium 8 / low 3 / info 0, each rule counted once per device; device score = 100 − penalties (min 0); design score = average. Generated configs keep SEC-09 (no OSPF auth: commands pending owner OK) and SEC-11 (CHANGE_ME placeholders) on purpose.

### D-028 — BOM prices are placeholders (2026-11-10)
- Decision: `backend/data/prices.json` holds placeholder INR estimates, flagged in every BOM output; cable meters = link distance × circuits × (1 + 10 % slack); optics = 2 per fiber cable; in-building runs counted as patch cords; carrier/internet circuits are monthly.

### D-029 — What-if model (2026-11-10)
- Decision: failures are applied by shutting interfaces in the parsed configs and re-running the simulator over every segment pair; SPOF = removing one non-access device or one cable separates segment-hosting devices; resilience score = 100 × (1 − SPOF elements / infra elements).

### D-030 — GNS3 export deferred (2026-11-10)
- Decision: no `.gns3project` is generated until its schema can be checked against a real GNS3 export (task 18.2). Exports are .cfg files, design.json, design_report.md and cabling_guide.md.
