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
| 2–26 | not started |

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
