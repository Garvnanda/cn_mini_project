# NetArchitect

Explainable network design engine (CIC-307 Computer Networks mini-project).

You describe a network (preset, JSON, or plain English). NetArchitect designs it end to end: cabling and
transceivers, topology tier, VLANs/trunks/STP/HSRP, bitwise VLSM, OSPF areas with summarization, eBGP to
the cloud, IPsec, ACLs, QoS. It justifies every decision with IEEE / RFC references, generates Cisco IOS
configs, then **parses its own configs back and proves they work** with a packet-level simulator. You can
break links or devices to watch failover, lint the security posture, estimate a bill of materials, diff two
designs and export everything.

> design → explain → verify → break → re-verify

See `idea.md` (concept), `implemented.md` (what exists), `docs/rubric_check.md` (rubric → code/tests),
`ai_audit_log.md` (real AI bugs with packet traces).

## Features
| Area | What it does |
|---|---|
| L1 media | ≤100 m Cat6a, ≤400 m OM4, else OS2 LR/ER; optical budget; latency budget; `PhysicalDistanceViolationError` |
| Topology | collapsed core or three-tier, access stacks sized from host counts, PoE budget, redundancy |
| L2 | pruned 802.1Q trunks, unused native VLAN, Rapid PVST+ roots, PortFast + BPDU Guard, HSRPv2 |
| L3 | bitwise VLSM (/31 p2p, /32 loopbacks), single/multi-area OSPF with exact summaries, MD5 auth, eBGP to cloud, IPsec VTI |
| Policy / QoS | ACLs from segment policies; LLQ (EF priority) on latency-budget links |
| Explainability | every decision is a `Rationale` with rule id, threshold and standard reference |
| Verification | IOS parser + simulator: reachability matrix, policy intent, loops, overlaps, trunk scope; optional Batfish |
| What-if | fail links/devices, see broken and rerouted flows; single points of failure + resilience score |
| Security | 13-rule linter with score; works on pasted configs |
| BOM | cable, optics, switches, routers, PoE, monthly WAN (placeholder INR prices) |
| Diff | decisions, IP plan and config diff between two designs |
| Interfaces | web dashboard (React), CLI (Typer), terminal UI (Textual), HTTP API (FastAPI) |
| Natural language | OpenRouter LLM or offline parser fills the input form; the engine makes every decision |

## Setup
```bash
# backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt

# frontend
cd frontend
npm install
cp .env.example .env        # VITE_API_URL=http://localhost:8000
```

## Run
```bash
cd backend && uvicorn api:app --reload          # API on :8000 (docs at /docs)
cd frontend && npm run dev                      # dashboard on :5173
cd backend && python tui.py                     # terminal UI
```

## CLI
```bash
cd backend
python cli.py --help
python cli.py design metro_man --export ../exports/metro_man
python cli.py explain campus_lan --domain L1
python cli.py verify global_wan
python cli.py trace campus_lan Guest-C Servers
python cli.py fail metro_man --link HQ-R1--BRANCH-R1     # no options = SPOF report
python cli.py lint some_router.cfg
python cli.py bom metro_man
python cli.py diff campus_lan my_campus.json
```
Presets: `campus_lan`, `metro_man`, `global_wan` (or a JSON file path). Invalid-input examples: `backend/examples/`.
Exit codes: 0 ok, 1 verification/trace/failure check failed, 2 invalid parameter, 3 invalid prefix,
4 physical distance violation, 5 address space exhausted, 6 topology error.

## Test
```bash
cd backend && pytest            # 419 tests (1 live-Batfish test skipped without a container)
cd frontend && npm run lint && npm test && npm run build
```

## Deploy (free tier)
- **Backend → Render:** `render.yaml` (blueprint, root `backend`, `uvicorn api:app`, health check `/health`).
  Set `CORS_ORIGINS` to the Vercel URL; `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` are optional.
  Measured locally: ~56 MB idle, ~60 MB after designing all three presets (limit 512 MB).
- **Frontend → Vercel:** project root `frontend`, `frontend/vercel.json`; set `VITE_API_URL` to the Render URL.
  The UI shows a "waking server" state while the free Render instance cold-starts.

## Optional: Batfish cross-check (local only)
```bash
docker run -d -p 9996:9996 batfish/allinone
pip install -r backend/requirements-batfish.txt
BATFISH_HOST=localhost pytest -m batfish
```

## Layout
```
backend/
  engine/     media, VLSM, topology, L2, routing, ACLs, QoS, config generator, planner
  verify/     IOS parser, simulator (packet trace), verifier, Batfish adapter
  analysis/   what-if + SPOF, security linter, BOM, design diff
  export/     report, cabling guide, design.json, per-device .cfg
  nl/         OpenRouter client + offline parser
  presets/ examples/ templates/ data/ tests/
  api.py  cli.py  tui.py
frontend/     React + Vite dashboard
docs/         standards, IOS reference, decisions, rubric check, proof/
exports/      generated configs and reports for the 3 presets
```

## Known limits
- Fiber loss figures, some IOS commands (HSRPv2, IPsec VTI, MQC) and Packet Tracer compatibility are marked
  `[verify]` / `?` in `docs/standards.md` and `docs/ios_reference.md`.
- Passwords, OSPF key and IPsec PSK in configs are `CHANGE_ME_*` placeholders; BOM prices are placeholders.
- GNS3 project export is deferred (D-030); Packet Tracer gets per-device configs + a cabling guide.
