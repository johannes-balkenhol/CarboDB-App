# CarboDB-App — Status & Runbook for Aman

**Date:** 2026-06-24
**Server:** wbbi206 (132.187.22.206)
**Status:** Backend + frontend running, end-to-end prediction verified

---

## 1. Where things live

| Component | Path |
|---|---|
| **Shared webapp code** (rw for `carbodb` group) | `/storage/users/projects/CarboDB-App-v2/` |
| **Running backend code** (Johannes' live copy) | `~/Projects_shared/CarboDB_v3/webapp/` |
| **SQLite database** (49 GB) | `~/Projects_shared/CarboDB_v3/data/primary/carbodb.sqlite` |
| **InterProScan + Pfam HMMs** | `~/Projects_shared/CarboDB_v3/data/dbs/` |
| **Trained models** (XGBoost binary/EC/Km + ESM-2) | `~/Projects_shared/CarboDB_v3/webapp/models/` |
| **Launcher scripts** | `~/carbodb_logs/start_backend.sh`, `start_frontend.sh` |
| **Service logs** | `~/carbodb_logs/uvicorn.log`, `vite.log` |
| **PID files** | `~/carbodb_logs/uvicorn.pid`, `vite.pid` |

Two repos. The `_v3` repo is the science/pipeline repo; the `App-v2` repo is the deployable webapp. The running backend currently imports from `_v3/webapp/` (historical reasons). Long-term we'd consolidate into `App-v2/`.

---

## 2. Start, stop, check, view logs

### Start everything

```bash
# In a fresh shell, conda must be active first
mamba activate carboxylase    # or: conda activate carboxylase

~/carbodb_logs/start_backend.sh    # uvicorn on :8090
~/carbodb_logs/start_frontend.sh   # vite on :5173

# Wait ~30s for models to load, then verify (see §3)
```

### Stop

```bash
kill $(cat ~/carbodb_logs/uvicorn.pid)
kill $(cat ~/carbodb_logs/vite.pid)
```

### Check status

```bash
# Are the processes alive?
ps -p $(cat ~/carbodb_logs/uvicorn.pid) $(cat ~/carbodb_logs/vite.pid)

# Are the ports listening?
ss -tlnp 2>/dev/null | grep -E '5173|8090'

# Smoke tests
curl -s -o /dev/null -w "API HTTP %{http_code}\n" http://localhost:8090/docs
curl -s -o /dev/null -w "UI  HTTP %{http_code}\n" http://localhost:5173/
```

### Watch logs

```bash
tail -f ~/carbodb_logs/uvicorn.log    # backend (model loading + prediction errors)
tail -f ~/carbodb_logs/vite.log       # frontend (compile errors, HMR)
# Ctrl+C to stop watching — does NOT kill the app
```

---

## 3. Test via browser

1. Connect to the VPN
2. Open **http://132.187.22.206:5173/**
3. Click **Analysis** in the top nav
4. Click **RuBisCO** (one of the example buttons) — this prefills a known carboxylase
5. Leave Mode = Standard (~15s, +ESM-2), Kingdom = Plant/Algae
6. Click **Analyze Sequence**
7. Wait 30–90 s (first request after a fresh boot does cold-start InterProScan; subsequent requests are ~15 s)
8. Result should show binary=positive, EC=4.1.1.39 (RuBisCO), Km ≈ 0.01 mM

Expected boot log when everything is healthy (`tail ~/carbodb_logs/uvicorn.log`):

```
INFO CarboDB webapp starting...
INFO Feature names loaded: 1793 features
INFO EC label map: 27 classes
INFO Binary model loaded
INFO EC model loaded
INFO Km model loaded
INFO Loading ESM-2 on cpu...
INFO ESM-2 loaded successfully
INFO Models loaded in ~25s
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8090
```

---

## 4. Recent commits (read these to understand the codebase)

Most recent → oldest, in `CarboDB-App-v2`:

```bash
cd /storage/users/projects/CarboDB-App-v2
git log --oneline -10
```

The key recent commits (all on `main`):

- **chore: stop tracking __pycache__ bytecode** — removed accidentally-tracked Python caches
- **chore: gitignore Python __pycache__** — `.gitignore` updated so caches don't reappear
- **feat(frontend): make vite ports configurable via env vars** — `vite.config.js` now reads `FRONTEND_PORT` and `BACKEND_PORT`. Defaults stay at 5173/8090. Override with `frontend/.env.local` (gitignored) for per-developer ports.
- **docs: setup guide for co-developer (Aman) — shared workspace, env, ports, troubleshooting** — `docs/SETUP_AMAN.md`, the original handoff. Read this first.
- **docs: rewrite top-level README to describe current layout**
- **chore(motifs): commit v2 generator for traceability**

After reading these, the most important files to understand:

| File | What it does |
|---|---|
| `app/main.py` | FastAPI entry point, lifespan loader |
| `app/startup.py` | Loads all 4 models (binary, EC, Km, ESM-2) at boot |
| `app/routes/predict.py` | `/api/v1/predict` endpoint — receives sequence, spawns annotate.py |
| `app/pipeline/predict.py` | Wraps the annotate.py subprocess call |
| `app/pipeline/annotate.py` | Standalone copy of `scripts/11_annotate_sequence.py` — does HMMER + InterProScan + ESM-2 + XGBoost cascade |
| `app/routes/browse.py` | Browse/search endpoints against the SQLite DB |
| `app/routes/external.py` | UniProt/Pfam lookups (cached) |
| `frontend/src/views/AnalysisView.vue` | The sequence input page you tested |
| `frontend/src/views/DatabaseView.vue` | Browse table |
| `frontend/src/views/DetailView.vue` | Per-sequence result page |

---

## 5. Shared group access

You (`s391913`) and Johannes (`job37yv`) are both in the `carbodb` Unix group. Verify on your account:

```bash
groups | grep carbodb
# If empty, log out completely and SSH back in — group only takes effect on new login
```

What the group grants you:

- **Read + write** on `/storage/users/projects/CarboDB-App-v2/` (the shared webapp)
- **Read** on `~/Projects_shared/CarboDB_v3/data/dbs/`, `data/primary/`, `data/models/`, `docs/`, `scripts/`

So you can:
- `git pull`, `git commit`, `git push` in the shared webapp
- Run InterProScan, HMMER, read the SQLite DB without copying anything
- Read all docs and pipeline scripts in CarboDB_v3

You **cannot** write to CarboDB_v3 (that's Johannes' working copy). If you need a change there, ping Johannes.

### Verify you can write

```bash
touch /storage/users/projects/CarboDB-App-v2/test_$USER.txt && rm $_ && echo OK
```

---

## 6. Working on a new feature

```bash
# Clone or pull
cd /storage/users/projects/CarboDB-App-v2
git pull origin main

# Branch
git checkout -b feat/your-feature

# Backend changes: restart uvicorn to pick them up
kill $(cat ~/carbodb_logs/uvicorn.pid)
~/carbodb_logs/start_backend.sh
tail -f ~/carbodb_logs/uvicorn.log

# Frontend changes: vite hot-reloads automatically, no restart needed

# When ready
git add <files>
git commit -m "feat: short description"
git push -u origin feat/your-feature
# Then open a PR on GitHub for Johannes to review
```

### Use your own ports (avoid clashing with Johannes' running instance)

Create `frontend/.env.local` (gitignored — your machine only):

```bash
FRONTEND_PORT=5174
BACKEND_PORT=8091
```

And start your own uvicorn on 8091 with a modified launcher (copy `~/carbodb_logs/start_backend.sh` to your home, change the `--port 8090` to `--port 8091`).

---

## 7. Known gotchas

| Symptom | Cause | Fix |
|---|---|---|
| `Permission denied` on `/storage/users/projects/` | `carbodb` group not active in this shell | log out, log back in |
| `InterProScan ... Unrecognized VM option 'UseFastAccessorMethods'` | Java 17+ instead of Java 11 | `conda install -c conda-forge openjdk=11 -y` |
| `Prediction failed ... timed out after 120 seconds` | Cold-start InterProScan exceeds 120s | already fixed — bumped to 600s in `pipeline/predict.py` and `annotate.py` |
| `ModuleNotFoundError: No module named 'config'` in predictions | `PYTHONPATH` missing from uvicorn env | already fixed — added to `start_backend.sh` |
| `Port 5173 is in use, trying another one` | Old vite still running | `pkill -f vite; ~/carbodb_logs/start_frontend.sh` |
| Browser shows `ERR_CONNECTION_REFUSED` | Nothing listening on that port | Check `ss -tlnp \| grep -E '5173\|8090'`, restart whichever is missing |
| `npm run dev` exits with `vite: not found` | Conda env not active when launcher ran | `mamba activate carboxylase` first, then re-run launcher |

---

## 8. Contact

- Code questions, bugs: open a GitHub issue and tag @johannes-balkenhol
- Server / group / sudo: ping Johannes (sysadmin handles `carbodb` membership)
- Pipeline questions (HMMER, InterProScan, ML models): see `~/Projects_shared/CarboDB_v3/docs/`, then ask

Welcome aboard. The app is up and predictions work — start with the Browse and Detail views to get familiar with the data, then move on to whatever Johannes prioritises next.
