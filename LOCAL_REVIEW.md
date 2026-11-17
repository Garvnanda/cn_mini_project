# Local review

Web: http://localhost:5173

Interactive API: http://localhost:8000/docs

API health: http://localhost:8000/health

## Restart after closing/rebooting

Open two PowerShell terminals:

```powershell
cd C:\projects\cn_mini_project\backend
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

```powershell
cd C:\projects\cn_mini_project\frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

## TUI

In a separate terminal:

```powershell
cd C:\projects\cn_mini_project\backend
.\.venv\Scripts\python.exe tui.py
```

Choose each preset and inspect Decisions, IP Plan, Configs, Verify, What-if,
BOM and Lint. Try failing a link and a device. Ctrl+C exits.

## CLI

From backend:

```powershell
.\.venv\Scripts\python.exe cli.py --help
.\.venv\Scripts\python.exe cli.py design metro_man
.\.venv\Scripts\python.exe cli.py explain campus_lan --domain L1
.\.venv\Scripts\python.exe cli.py verify global_wan
.\.venv\Scripts\python.exe cli.py trace campus_lan Guest-C Servers
.\.venv\Scripts\python.exe cli.py trace metro_man Branch-Users Colo-Trading --proto tcp --port 443
.\.venv\Scripts\python.exe cli.py fail metro_man --link HQ-R1--BRANCH-R1
.\.venv\Scripts\python.exe cli.py bom metro_man
.\.venv\Scripts\python.exe cli.py lint campus_lan
.\.venv\Scripts\python.exe cli.py diff campus_lan campus_lan
```

The guest trace should be denied (exit code 1 is expected). The TCP 443 trace
should deliver. Identical inputs should produce no diff.

## Web review

1. Design each of the three presets; inspect all tabs.
2. Trace Guest-C to Servers in Campus, then Branch-Users to Colo-Trading with TCP
   port 443 in Metro. Inspect the displayed hop details.
3. Fail a link or device in Network and inspect broken/rerouted flows.
4. Edit custom JSON; try invalid JSON and the files under backend/examples.
5. Extract plain English, review assumptions and confirm the resulting parameters.
6. Save two versions with a changed distance and inspect the diff.
7. Paste a config in Security; inspect BOM; download ZIP/configs/report/JSON/cabling.
8. Open Report, print to PDF, and inspect page breaks before saving.

## API review

Open /docs. Execute GET /presets/campus_lan and copy its JSON response into
POST /design or POST /verify. Explore /trace, /whatif, /lint, /bom, /diff, /nl
and /export/{fmt} using their request schemas.

## Verified baseline

2026-11-18: backend suite 423 passed, 1 skipped (Batfish), 1 warning;
frontend lint/build pass and 4 tests pass. Each preset passed CLI verification
and live POST /design verification. Web GET returned HTTP 200.
TUI is covered by automated pilot tests; browser visual acceptance remains a
user review task. See docs/project_audit.md for external lab/platform gaps.
