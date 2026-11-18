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

1. Open **How to use** for the glossary and interface guide. Design each example and start with **Overview**.
2. Trace Guest-C to Servers in Campus, then Branch-Users to Colo-Trading with TCP
   port 443 in Metro. Inspect the displayed hop details.
3. Fail a link or device in **Network map** (enable failure testing first) and inspect broken/rerouted flows.
4. Edit custom JSON; try invalid JSON and the files under backend/examples.
5. Extract plain English, review assumptions and confirm the resulting parameters.
6. Save two versions with a changed distance and inspect the diff.
7. Paste a config in Security; inspect BOM; download ZIP/configs/report/JSON/cabling.
8. Open **Export & report**, print to PDF, and inspect page breaks before saving.

## API review

Open /docs. Execute GET /presets/campus_lan and copy its JSON response into
POST /design or POST /verify. Explore /trace, /whatif, /lint, /bom, /diff, /nl
and /export/{fmt} using their request schemas.

## Verified baseline

2026-11-18: 433 backend tests passed with live Batfish enabled; no skips, one
Starlette deprecation warning. Frontend lint/build and 5 tests passed. Actual
browser/API checks cover all three presets, allowed/blocked traces, keyboard link
failure, downloads, guide, responsive views and PDF generation. TUI is covered
by the automated pilot and includes its own How to use tab.

Campus and Metro agree with live Batfish. Global WAN has 14 disagreements among
21 comparisons; see docs/proof/batfish/. These software checks do not replace
actual Packet Tracer/GNS3 labs. Remaining work is in docs/project_audit.md.

## Pick an interface

- Web: learning, network map, packet tracing, guide, version comparison and reports.
- TUI: terminal dashboard for presets, explanations and failure experiments.
- CLI: repeatable commands, export files and automation. A denied trace exits 1 by design.
- API: integrate another program; /docs provides interactive request examples.

Neither web, CLI, TUI nor API changes your real network. Exported device instructions
need platform validation and replacement of placeholder credentials before use.
