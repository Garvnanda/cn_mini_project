# NetArchitect

NetArchitect is a network planning tool built for the CIC-307 Computer Networks mini-project. Give it a list of buildings, distances and user groups. It chooses cables, divides the available network addresses among the groups, and writes Cisco device configurations. You can open any design decision to see the rule and inputs behind it.

The simulator reads the generated configurations back and follows traffic through the proposed network. For example, if campus guests must be isolated from servers, a **blocked** guest connection is the result you want.

## Run locally

Use Python 3.11 and Node.js 24 with npm. Open **two PowerShell terminals in the repository root**. Run the install commands once and keep both servers running while using the dashboard.

**Terminal 1 — start the API**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — start the dashboard**

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open the [dashboard](http://localhost:5173). The [interactive API](http://localhost:8000/docs) and [health check](http://localhost:8000/health) run on port 8000. On Linux or macOS, use `.venv/bin/python` in place of the Windows virtual environment executable.

## Try a design

1. Choose **Campus LAN** and select **Design network**. **Overview** shows the size of the proposed network. **Why these choices?** explains the equipment and addressing decisions.
2. Open **Network map**, choose **Guest-C** as the source and **Servers** as the destination, then select **Trace packet**. The campus security rule blocks the connection. Expand the trace to see where it stopped.
3. Try **Metro MAN** to explore backup paths. Enable **failure testing** on the map and select an HQ-to-branch connection. The result shows which traffic took another route and which connections broke.
4. Open **Export & report** to download device instructions and a cabling guide or save a printable report. **How to use** includes a searchable glossary and terminal examples.

| Starting point | What you can investigate |
|---|---|
| Campus LAN | How three nearby buildings share infrastructure while keeping guest traffic separate |
| Metro MAN | How a head office, branch and data center stay connected across a city |
| Global WAN | How offices across four cities exchange traffic with a cloud network |
| Custom requirements | Edit an example as JSON or describe your network in plain English, then review the extracted fields |

Plain-English input uses an offline parser or an optional OpenRouter key configured on the backend. The same deterministic rules generate the plan from the reviewed inputs in either case.

## Choose an interface

| Interface | When to use it | Where to start |
|---|---|---|
| Web | Learn visually, compare saved designs, trace traffic or print a report | [Dashboard](http://localhost:5173) |
| TUI (terminal dashboard) | Browse presets and simulate failures interactively in a terminal | Run `tui.py` |
| CLI (command line) | Repeat a check, export files or write a script | Run `cli.py --help` |
| API | Send requirements from another program or inspect a request and its response | [API explorer](http://localhost:8000/docs) |

From a third PowerShell terminal in the repository root:

```powershell
cd backend
.\.venv\Scripts\python.exe tui.py
# Press q to exit the dashboard before running the commands below.
.\.venv\Scripts\python.exe cli.py verify campus_lan
.\.venv\Scripts\python.exe cli.py trace metro_man Branch-Users Colo-Trading --proto tcp --port 443
.\.venv\Scripts\python.exe cli.py design metro_man --export ../exports/tmp/metro_demo
```

The Metro trace above should be delivered. The [local walkthrough](LOCAL_REVIEW.md) includes the corresponding denial example, failure tests, configuration checks and design comparisons.

## Verification and remaining work

The latest recorded local run on **18 November 2026** passed **433 backend tests** with live Batfish enabled and **5 frontend tests**. Browser checks exercised all three presets against the API, including packet traces, failure simulation and downloads.

Batfish is an independent configuration analysis tool. It agreed with the built-in simulator on all **90 Campus** and **21 Metro** comparisons. For Global WAN, **14 of 21 comparisons disagreed**. VPN behavior still needs lab validation. The three presets include configuration files and cabling guides. Packet Tracer or GNS3 acceptance, automatic GNS3 project export, access-switch management addresses and some optical assumptions remain open. Equipment prices are estimates and generated credentials are placeholders. [Comparison reports](docs/proof/batfish/) · [Full project audit](docs/project_audit.md)

To rerun the checks, use the backend virtual environment and the installed frontend dependencies:

```powershell
# From backend/
.\.venv\Scripts\python.exe -m pytest -o addopts='' -q

# From frontend/
npm run lint
npm test
npm run build
```

The two optional live Batfish tests skip when its host is unconfigured. See the [Batfish setup and reproduction notes](docs/proof/batfish/README.md).

## Deploy on Render

1. Push the version you want to publish. Create the API from the repository's [Render Blueprint](render.yaml). It builds from `backend/` and checks `/health`.
2. Create a **Static Site** from the same branch. Set the root to `frontend`, build command to `npm ci && npm run build`, and publish directory to `dist`. Set `VITE_API_URL` to the API's public HTTPS origin before building.
3. In the API environment, set `CORS_ORIGINS` to the static site's public HTTPS origin and redeploy the API. Use both origins without trailing slashes. Open the public dashboard and run the Campus example to verify the connection.
4. In UptimeRobot, create an HTTP monitor for the API's public `/health` URL and enable your alert contact. A second monitor can check the dashboard homepage. [UptimeRobot setup](https://help.uptimerobot.com/en/articles/11358364-how-to-create-your-first-monitor-on-uptimerobot-quick-setup-guide)

The repository also includes an [alternative deployment guide using Vercel for the frontend](DEPLOY.md).

## Explore the project

- [Design engine](backend/engine/) and [configuration verifier](backend/verify/) — how requirements become a plan and how the simulator checks it.
- [Exported examples](exports/) — inspect the three designs without starting a server.
- [Standards](docs/standards.md) and [design decisions](docs/decisions.md) — the sources and assumptions behind the rules.
- [Assignment rubric](docs/rubric_check.md) and [AI audit log](ai_audit_log.md) — evidence for the course deliverables and worked examples of networking bugs.
