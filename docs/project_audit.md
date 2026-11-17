# Project audit — 2026-11-18

## Current stage

Local review update (2026-11-18): API and web started on localhost ports 8000 and
5173. All three presets pass live HTTP /design and CLI verification. Latest backend
suite: 423 passed, 1 skipped; frontend lint/build and 4 tests pass. See
`LOCAL_REVIEW.md` for all interface commands. This adds HTTP integration evidence;
browser visual acceptance and external lab validation remain unverified.

NetArchitect is a substantially implemented application in final integration,
external validation, and submission preparation. It is not an early prototype and
is not yet a fully validated submission. No entire numbered phase is wholly absent:
the missing work is concentrated in partially complete phases and acceptance evidence.
This audit covers the root planning/status documents, all docs reference files,
the assignment PDF, source and test inspection, and local automated checks. It is
not a claim of exhaustive line-by-line review or real device certification.

## Phase status

| Phases | Evidence-based status | Remaining qualification |
|---|---|---|
| 0–2: tooling, models, rationale | Implemented; local suite passes | Fresh-machine dependency installation not repeated |
| 3: physical media | Implemented and tested | Optical constants still `[verify]`; real cable/optic validation absent |
| 4: bitwise VLSM | Implemented and tested | Boundary, oracle, and property coverage exists |
| 5–7: topology, L2, routing | Implemented and tested in internal model | Real STP/HSRP, routing and failure behavior needs lab evidence |
| 8: IOS generation | Implemented; golden and documented-command checks pass | Device/platform compatibility still unverified |
| 9–12: presets, parser, simulator, verifier | Implemented; local checks pass | Built-in simulation has deliberate fidelity limits |
| 13: optional Batfish | Adapter present; live acceptance incomplete | 13.2 and 13.3 open; Docker executable exists, daemon unavailable |
| 14–17: failure analysis, security, BOM, diff | Implemented and tested | Convergence is estimated; security score is a rule score; prices are placeholders |
| 18: exporters | CFG, JSON, Markdown report and cabling guide present | GNS3 project archive absent/deferred (18.2, D-030) |
| 19–20: CLI and API | Implemented and locally tested | Public deployment not demonstrated |
| 21: natural language | Client and offline fallback implemented; mocked tests present | Source records a historical live run; no live call repeated in this audit |
| 22: TUI | Implemented; pilot smoke tests in suite | Interactive human acceptance not repeated |
| 23–24: web | Implemented; lint, 4 mocked UI tests and build pass | Real browser/API workflows, responsive and print layout acceptance not checked |
| 25: deployment | Render/Vercel configs and instructions present | 25.3 open; no live URLs or deployment evidence verified |
| 26: docs and AI audit | Documents and three historical bug entries present | 26.3 open: actual lab proof absent; status text needs reconciliation |

## Highest-priority missing evidence

1. **Assignment acceptance: load all three presets in Packet Tracer or GNS3.**
   `docs/proof/` contains only its README. Capture topology, routing neighbors and
   tables, gateway failover where applicable, allowed flows and intended denied
   flows. Preserve lab files, device/platform versions and commands/output alongside
   screenshots. Fix and regression-test any genuine failures before marking 26.3 done.
2. **Resolve physical/IOS uncertainty.** `docs/standards.md` still flags OS2 loss,
   SR/LR/ER channel budgets, interface bandwidth assumptions and other platform
   values. `docs/ios_reference.md` has `?` compatibility entries for HSRPv2, VTI,
   MQC and crypto commands. Verify primary sources and the selected lab platform;
   follow CLAUDE.md for new commands and owner confirmation. Do not remove flags
   based on passing internal tests.
3. **Exercise the web against the actual backend.** Test all presets, custom errors,
   permitted/denied traces, link and node failures, NL confirmation, pasted-config
   lint, saved-version diff, downloads and print-to-PDF. The four current frontend
   tests mock fetch; they do not establish this integration or visual correctness.
4. **Deploy and smoke-test if retaining the hosted-product goal.** Set backend and
   frontend URLs/CORS, verify a cold start and the main workflows, and record real
   URLs and results. Historical RAM measurements are not a fresh deployment test.
5. **Optional/full-idea work:** live Batfish comparisons (13.2/13.3) and a real-schema
   GNS3 archive exporter (18.2). The assignment permits Packet Tracer OR GNS3, so an
   automatic GNS3 project archive is not required to satisfy that deliverable.

## Implementation limits and discrepancies

- The verifier parses generated configs, which is useful, but generator and verifier
  share project assumptions. External validation is still needed. The simulator
  models L2 domains rather than STP blocking; one representative host per segment
  and one-way probes do not model full ARP/session/return-path behavior.
- Metro latency checks cover propagation. Configuring LLQ does not establish a
  measured sub-5 ms end-to-end result under load; switching, serialization and queueing
  are not proven by that check.
- Access-switch management addressing remains an acknowledged implementation gap.
  PoE watts are calculated, but a validated hardware selection/power budget is not
  established merely by that calculation.
- Generated credentials are `CHANGE_ME_*`, public underlay addresses are lab
  documentation addresses, and BOM prices are placeholders. These are lab outputs
  with explicit assumptions, not production deployment certification.
- `idea.md` still labels the project a fresh rewrite and promises ready-to-import
  GNS3 labs. D-030 defers those labs; D-033 replaces React Flow/Monaco with SVG/pre.
  Update the idea/demo wording to reflect these decisions before presenting it.
- README/rubric/historical logs contain different test totals (419/420/422).
  Current measured total is **423 passed, 1 skipped**. Historical entries should
  retain their original results; current summaries should use the new baseline.
- `implemented.md` calls the OpenRouter path unverified, but `nl/openrouter.py`
  records a live check on 2026-11-10 using `openrouter/free`. `DEPLOY.md` says
  `openrouter/auto` is the default. Actual code default is `openrouter/free`.
  Historical/live-now evidence must be kept distinct; no key or paid call was used here.
- `ai_audit_log.md` contains three entries; entries 2 and 3 provide before/after
  packet-flow narratives and corresponding regression tests. Entry 1 explicitly
  lacks packet-flow proof. Original prompt/model provenance cannot be independently
  authenticated from these files; do not invent further evidence.
- The print report contains verification and BOM sections but does not enumerate
  security findings as a dedicated section. Check final report expectations against
  actual print output before calling the full idea complete.
- No CI workflow was found in the tracked project layout. CI is a useful optional
  reproducibility improvement, not a stated assignment requirement.

## Checks performed and one fix

Initial working tree was clean. No secret values were read or printed.

- From `backend/`: `.venv/Scripts/python -m pytest -q` succeeded (double quiet
  suppresses totals because pytest.ini also sets `-q`).
- Additional root invocation exposed three failures in `tests/test_cli.py` caused
  by relative examples/preset paths. Changed these to paths relative to `__file__`;
  no application behavior or golden config changed.
- From repository root after the fix:
  `./backend/.venv/Scripts/python -m pytest -o addopts='' -q backend/tests`
  → **423 passed, 1 skipped, 1 warning in 6.50s**.
- Skipped check is live Batfish. Warning is Starlette TestClient's httpx deprecation;
  it does not fail the suite. No dependency was added to suppress it.
- From `frontend/`: `npm run lint` passed; `npm test` → **4 passed**;
  `npm run build` passed, JS 247.77 kB / gzip 76.06 kB.
- `docker info` could not connect to Docker Desktop's Linux-engine named pipe.
- Assignment PDF text was extracted with pypdf and compared with the rubric.
  No browser visual QA, actual lab import, current external-service verification,
  hosted deployment, fresh dependency installation or new RAM measurement was performed.

## Completion order

Close lab/platform and standards gaps first, fix real findings with regression
tests, then run the actual browser/API acceptance flow. Complete deployment if
wanted, and optionally Batfish/GNS3 archive export for full idea scope. Finally
reconcile docs, regenerate exports only if code changed, and record evidence for
each acceptance gate. Keep unchecked tasks open until their evidence exists.
