# Project audit - 2026-11-18

## Current stage

**Final local integration; external lab acceptance incomplete.** Web, CLI, TUI and
API are implemented and locally tested. The redesigned web adds a beginner guide,
glossary, overview and progressively disclosed technical detail. No whole numbered
phase is absent, but automatic GNS3 archives are absent. The entire project and
assignment submission must not yet be called complete.

## Phase status

| Phases | Evidence-based status | Remaining qualification |
|---|---|---|
| 0-2: tooling, models, rationale | Implemented and locally tested | Fresh-machine installation not repeated |
| 3: physical media | Implemented; threshold tests pass | OS2 attenuation, ER budget and other flagged values unresolved |
| 4: VLSM | Implemented; boundary, oracle and property checks pass | No new limitation identified |
| 5-8: topology, routing, IOS | Implemented; local/golden checks pass | Platform acceptance and access management IPs remain open |
| 9-12: presets, parser, simulator, verifier | Implemented; all presets pass internally | Simplified model needs external acceptance |
| 13: Batfish | Implemented and live-tested locally | Campus 90/90 and Metro 21/21 agree; WAN has 14/21 disagreements |
| 14-17: failures, security, costs, diff | Implemented and tested | Timer estimates; placeholder prices; model/rule scores |
| 18: exporters | CFG, ZIP, JSON, Markdown and cabling implemented | 18.2 GNS3 archive absent/deferred under D-030 |
| 19-20: CLI/API | Implemented and locally tested | Public hosting deferred by owner |
| 21: natural language | Client, fallback and malformed-response handling implemented | Mocked provider tests; no new live provider call |
| 22: TUI | Implemented; help page and pilot tests | Human terminal acceptance pending |
| 23-24: web | Redesigned; unit, lint, build and browser checks pass | No screen-reader or exhaustive browser-matrix certification |
| 25: deployment | Configurations present | 25.3 deferred: local review before deployment |
| 26: docs and AI audit | Updated; historical bug records retained | 26.3 actual Packet Tracer/GNS3 proof incomplete |

## Current checks

From `backend/`, with `BATFISH_HOST=localhost`:
`.venv/Scripts/python -m pytest -o addopts='' -q`
returned **433 passed, 1 warning in 71.90s**, no skips. Without Batfish configured,
the earlier run returned **431 passed, 2 skipped, 1 warning in 14.09s**.
The warning is Starlette's httpx TestClient deprecation. Live tests cover Campus
and Metro; this total does not imply WAN agreement. Historical logs keep original totals.

From `frontend/`: `npm run lint`, `npm test`, `npm run build` passed: **5 UI tests**;
JS 267.42 kB / 82.08 kB gzip. No runtime dependency was added.

From root: `node scripts/browser_review.cjs <installed-playwright-path>` passed with
installed Edge against the real API: all three designs, Campus guest denial,
Metro TCP 443 allowed/ICMP denied, TCP-to-ICMP switching, keyboard link failure and
survival, all views, guide, mobile width, light/dark captures, PDF generation,
and Metro/WAN ZIP/JSON/Markdown/cabling downloads. An intentionally intercepted
HTTP 503 checked export error feedback; that check is injected, not a real outage.
Captures are in `.impeccable/review/`. The Campus PDF has 29 pages including configs;
pages 1 and 5 were visually inspected, including the added security findings.

CLI checks passed for all preset verification, guest denial (expected exit 1),
Metro TCP 443 delivery, HQ link failure survival and identical-input diff (exit 0).
TUI pilot checks run in pytest. API/web run on ports 8000/5173; restart commands are
in `LOCAL_REVIEW.md`.

## Remaining work and external evidence

1. **WAN disagreement:** actual reports are in `docs/proof/batfish/`. Four directed
   IPsec sessions report phase-2 failure. Batfish grammar differs from generated
   IKE syntax; that does not establish every discrepancy is parser-only. Real IOS
   validation remains required; cryptography was not weakened to make tests green.
2. **Real labs:** owner confirmed Packet Tracer 9.0.1 is installed and no GNS3
   project/images exist. Installed help was inspected: Netcon REST controls a
   simulated network-controller device; IPC requires an external app registered
   through the GUI. No actual lab was loaded or packet capture produced. Stack
   interface names, VTI, HSRPv2 and MQC support remain unresolved. No .pkt was fabricated.
3. **GNS3 archive:** D-030 requires comparison against a real GNS3 export. No usable
   project/image exists here, so 18.2 remains absent rather than silently checked.
4. **Standards:** SR 2.9 dB and LR 6.2 dB now have primary-source links in standards.md.
   Remaining [verify] and ? entries are unresolved; their values were not invented
   or silently approved. Equipment, optic and fiber selection needs real validation.
5. **Access management IPs:** still an acknowledged gap. SSH configuration alone
   does not provide reachability. A management-address design requires rationale,
   regression tests and deliberate golden updates.
6. **Deployment:** deliberately not performed; owner wants local review first.

## Model limits

The verifier parses generated text but shares assumptions with the generator.
It models L2 domains rather than actual STP blocking, representative hosts and
one-way probes rather than full ARP/session/return-path behavior. Metro latency
checks cover propagation only. PoE calculations do not validate a chassis power
budget. Credentials are CHANGE_ME placeholders, underlay IPs are documentation
addresses, and equipment prices are placeholders. Security/resilience scores are
rule/model scores. Passing simulation is not Cisco compatibility, real encryption,
measured convergence, optical viability or end-to-end latency certification.
AI audit provenance was not independently authenticated; no new networking mistake
was fabricated for the log.
