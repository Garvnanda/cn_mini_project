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
