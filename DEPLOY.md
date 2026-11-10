# Deploying NetArchitect (free tier)

Backend (FastAPI) → **Render**. Frontend (React) → **Vercel**. Both deploy from your GitHub repo.
Order matters: backend first (you need its URL for the frontend), then frontend, then tell the backend
the frontend URL (CORS).

Dashboard menu names below were correct when written; if a button is named slightly differently, look for the closest match.

---

## 0. Before you start
1. Push the repo to GitHub (you do all git operations):
   ```bash
   git add -A
   git commit -m "NetArchitect phases 0-26"
   git push
   ```
2. Check that these are **not** in the push (they are git-ignored): `backend/.env`, `backend/.venv/`, `frontend/node_modules/`, `frontend/dist/`.
   ```bash
   git status --ignored --short | grep -E "\.env$|node_modules|\.venv"
   ```
3. Accounts: render.com and vercel.com, both signed in with GitHub.

---

## 1. Backend on Render
1. Render dashboard → **New +** → **Blueprint**.
2. Pick your GitHub repo. Render reads `render.yaml` from the repo root and shows one web service, `netarchitect-api` (plan: free, root dir `backend`).
3. It asks for the env vars marked `sync: false`:
   | Key | Value now |
   |---|---|
   | `CORS_ORIGINS` | `http://localhost:5173` for now (you replace it in step 3) |
   | `OPENROUTER_API_KEY` | your OpenRouter key, or leave empty (then `/nl` uses the offline parser) |
   | `OPENROUTER_MODEL` | optional, e.g. a model id from openrouter.ai/models; empty = `openrouter/auto` |
4. **Apply** / **Deploy**. First build takes a few minutes (`pip install -r requirements.txt`).
5. When it shows **Live**, copy the URL, e.g. `https://netarchitect-api.onrender.com`.
6. Test it in a browser:
   - `https://<your-api>.onrender.com/health` → `{"status":"ok", ...}`
   - `https://<your-api>.onrender.com/docs` → interactive API docs

If the build fails, open **Logs** on the service and send me the last 30 lines.

Free tier note: the service sleeps after ~15 minutes idle; the first request then takes ~30-60 s.
The dashboard shows "Waking server…" during that time.

---

## 2. Frontend on Vercel
1. Vercel dashboard → **Add New…** → **Project** → import the same GitHub repo.
2. **Root Directory**: click **Edit** → choose `frontend`. Framework preset should auto-detect **Vite**
   (build `npm run build`, output `dist`; `frontend/vercel.json` sets the same).
3. **Environment Variables**: add
   | Key | Value |
   |---|---|
   | `VITE_API_URL` | your Render URL from step 1.5, **no trailing slash** |
4. **Deploy**. Copy the production URL, e.g. `https://netarchitect.vercel.app`.

`VITE_` variables are baked in at build time: if you change `VITE_API_URL` later, redeploy the frontend.

---

## 3. Allow the frontend in CORS
1. Render → your service → **Environment** → edit `CORS_ORIGINS` →
   `https://netarchitect.vercel.app,http://localhost:5173` (your real Vercel URL; comma-separated, no spaces needed, no trailing slash).
2. Save → Render redeploys automatically (or **Manual Deploy** → **Deploy latest commit**).

---

## 4. Check the live app
1. Open the Vercel URL. Wait for **Server ready** (top right).
2. Pick `metro_man` → **Design network** → you should see `verify PASS`, security 92/100, resilience 97/100.
3. Network tab → **Trace packet** Branch-Users → Colo-Trading, tcp 443 → DELIVERED.
4. Click a WAN link → what-if result appears.
5. Plain English tab → type a description → **Extract parameters** → source shows `openrouter` if the key is set, else `fallback`.

If the page says **Server unreachable**: check `VITE_API_URL` (step 2.3) and `CORS_ORIGINS` (step 3); open the browser dev tools console and send me the red error line.

---

## 5. Send me
- The Render URL and the Vercel URL.
- Any failing build log (last 30 lines) or browser console error.

I will then run the live smoke test against your URLs.

---

## Local run (no deploy)
```bash
cd backend && .venv/Scripts/python -m uvicorn api:app --reload     # Linux/macOS: .venv/bin/python
cd frontend && npm run dev                                          # http://localhost:5173
```
Keys for local use go in `backend/.env` (copy `backend/.env.example`); it is git-ignored and loaded automatically.
