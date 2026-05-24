# CarboDB-App-v2 — Co-developer Setup (Aman)

**Last updated:** 2026-05-24
**Maintainer:** Johannes (job37yv)
**Co-developer:** Aman (s391913)

This document describes how to get the webapp running on `wbbi206` in the shared workspace, without duplicating the 50 GB of databases or the 49 GB SQLite file.

---

## TL;DR

```bash
ssh s391913@wbbi206
groups | grep carbodb || echo "Log out and back in — group not active yet"
cd /storage/users/projects/CarboDB-App-v2
# edit .env (see below), then:
conda activate carboxylase
conda install -c conda-forge openjdk=11 -y     # one-time, for InterProScan
cd frontend && npm install                      # one-time
# Two shells from here on:
#   shell A: uvicorn app.main:app --port 8091 --host 0.0.0.0
#   shell B: cd frontend && npm run dev         # serves on 5174
```

---

## 1. Layout

```
/storage/users/projects/CarboDB-App-v2/          ← shared webapp (rw for carbodb)
├── app/                                          ← FastAPI backend
├── frontend/                                     ← Vue + Vite frontend
├── docker/
├── docker-compose.yml
├── .env                                          ← config (edit this — see §3)
└── README.md

/storage/users/job37yv/Projects/CarboDB_v3/      ← read-only data dependencies (carbodb group)
├── data/primary/carbodb.sqlite                  ← 49 GB SQLite DB
├── data/dbs/interpro/interproscan-5.72-103.0/   ← InterProScan binaries + databases
├── data/dbs/pfam/Pfam-A.hmm                     ← Pfam HMM database
└── data/models/                                  ← XGBoost v5 binary + EC + Km models
```

Do **not** copy the data dependencies — they're large and already accessible via the `carbodb` Unix group.

---

## 2. Verify access (do this first)

After logging in:

```bash
# Group membership
groups | grep carbodb           # must print 'carbodb'

# If missing: log out completely and SSH back in.
# Group membership only takes effect on new login sessions.

# Shared webapp
ls /storage/users/projects/CarboDB-App-v2/ | head
touch /storage/users/projects/CarboDB-App-v2/test_$USER.txt && rm $_ && echo OK

# InterProScan
/storage/users/job37yv/Projects/CarboDB_v3/data/dbs/interpro/interproscan-5.72-103.0/interproscan.sh --version
# Expected: "InterProScan version 5.72-103.0"

# SQLite DB
ls -la /storage/users/job37yv/Projects/CarboDB_v3/data/primary/carbodb.sqlite
# Expected: ~49 GB, readable
```

If any of these fail, ping Johannes before proceeding.

---

## 3. Configure `.env`

Edit `/storage/users/projects/CarboDB-App-v2/.env` to point at the shared data and use the parallel ports (so we don't clash with Johannes' running instance on 8090/5173):

```bash
# Shared webapp code
APP_ROOT=/storage/users/projects/CarboDB-App-v2

# Read-only data dependencies (in Johannes' CarboDB_v3)
DB_PATH=/storage/users/job37yv/Projects/CarboDB_v3/data/primary/carbodb.sqlite
INTERPROSCAN_PATH=/storage/users/job37yv/Projects/CarboDB_v3/data/dbs/interpro/interproscan-5.72-103.0/interproscan.sh
PFAM_HMM_PATH=/storage/users/job37yv/Projects/CarboDB_v3/data/dbs/pfam/Pfam-A.hmm
MODELS_DIR=/storage/users/job37yv/Projects/CarboDB_v3/data/models

# Temp dir for InterProScan output (writable per-user)
INTERPROSCAN_TEMP=/storage/users/projects/CarboDB-App-v2/tmp/interproscan

# Parallel-deploy ports (Johannes uses 8090 + 5173)
BACKEND_PORT=8091
FRONTEND_PORT=5174
```

Create the temp dir:

```bash
mkdir -p /storage/users/projects/CarboDB-App-v2/tmp/interproscan
```

---

## 4. Conda environment

Use the existing `carboxylase` env. Installation reminders if rebuilding:

```bash
# Three-step install (the one-shot conda install fails due to pytorch + cuda):
# 1. Base conda packages
conda env create -f environment.yml   # or per project's requirements
# 2. pip-only packages
pip install -r requirements.txt
# 3. PyTorch separately (CUDA-matched)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### InterProScan needs Java 11

InterProScan 5.72 uses JVM flags (`-XX:+AggressiveOpts`, `-XX:+UseFastAccessorMethods`) that are deprecated in Java 17+ and will crash with `Unrecognized VM option`. Fix:

```bash
conda install -c conda-forge openjdk=11 -y
java -version   # should print 11.0.x
```

If your shell still resolves to system Java, force the conda one explicitly:

```bash
export JAVA_HOME=$CONDA_PREFIX
export PATH=$CONDA_PREFIX/bin:$PATH
```

Test from inside the conda env (where the backend will spawn it):

```bash
$INTERPROSCAN_PATH --version
```

---

## 5. Frontend (Vite)

Vite = dev server + bundler for the Vue frontend. Three commands cover almost everything:

```bash
cd /storage/users/projects/CarboDB-App-v2/frontend

# One-time
npm install

# Hot-reload dev server (port from .env, default 5174)
npm run dev

# Production build → frontend/dist/, served by FastAPI or nginx
npm run build
```

### Port config

In `frontend/vite.config.js`:

- `server.port` → 5174
- The `/api/v1` proxy target must point at the backend port: `http://localhost:8091`

If the file shows 5173 / 8090, change to 5174 / 8091 to match `.env`. Johannes will mark the exact lines on request — send the current `vite.config.js`.

---

## 6. Backend (FastAPI / uvicorn)

```bash
cd /storage/users/projects/CarboDB-App-v2
conda activate carboxylase
uvicorn app.main:app --port 8091 --host 0.0.0.0 --reload
```

The `--reload` flag picks up code changes automatically.

### Request lifecycle (live `/api/v1/predict`)

For context — what happens when a new sequence comes in:

```
POST /api/v1/predict   { sequence, kingdom, mode }
  1. composition features         (~ms)
  2. HMMER scan vs Pfam-A         (~5–15 s)
  3. InterProScan                 (~30–60 s)        ← Java subprocess
  4. ESM-2 forward pass           (~20–40 s CPU)
  5. assemble 1793-feature vector
  6. xgb_binary.predict_proba
  7. if positive → xgb_ec.predict_proba
  8. if CO2-active EC → xgb_km.predict
  9. SHAP explanation
  10. BLAST vs per-EC db
```

InterProScan is the bottleneck and **must be present** — the XGBoost models were trained on the full 1793-feature stack including InterPro hits. Without it, predictions for new sequences will be silently wrong (not just slower).

---

## 7. Docs to read in order

1. `README.md` — top-level project orientation
2. `docs/HANDOFF.md` (if present) — original Johannes → Aman handoff
3. `docs/DEPLOYMENT.md` — production deploy plan (FastAPI vs nginx for static)
4. `docs/ROADMAP.md` — open issues, known bugs (e.g. `cdb_query_id` vs `uniprot_id`)
5. `docs/API.md` — endpoint reference

For the underlying pipeline + database:

- `~/Projects_shared/CarboDB_v3/docs/DATABASE.md`
- `~/Projects_shared/CarboDB_v3/docs/API.md`
- `~/Projects_shared/CarboDB_v3/docs/FRONTEND_SPEC.md`

---

## 8. Workflow & coordination

We share the same git repo; coordinate via branches:

- `main` — stable, never push broken code
- `feat/<your-feature>` — your work
- Push frequently, PR into main, request review from Johannes before merging

Don't run both backends on the same port. Johannes = 8090/5173, Aman = 8091/5174. If a port is busy:

```bash
ss -tlnp | grep -E '8090|8091|5173|5174'
```

For long-running uvicorn / npm processes, use `tmux` or `screen` so they survive SSH disconnect:

```bash
tmux new -s carbodb-back   # then start uvicorn; detach with Ctrl+b d
tmux attach -t carbodb-back
```

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Permission denied` on /storage/users/projects | `carbodb` group not active in this shell | log out, log back in; check `groups` |
| InterProScan: `Unrecognized VM option 'UseFastAccessorMethods'` | Java 17+ | `conda install -c conda-forge openjdk=11` |
| `Address already in use :8091` | Stale uvicorn | `ss -tlnp \| grep 8091`, kill the PID |
| Vite proxy 502 on `/api/v1/*` | Backend not running or wrong port in vite.config.js | start uvicorn; check proxy target |
| 504 / hanging predict request | Stuck Java subprocess | `ps aux \| grep interproscan`; kill, retry |
| Frontend doesn't pick up new components | Vite HMR miss | hard refresh (Ctrl+Shift+R); restart `npm run dev` |
| `cdb_query_id` vs `uniprot_id` confusion | Known naming bug from May 7 | see `docs/ROADMAP.md` rename plan |

---

## 10. Contact

- Code questions: open a GitHub issue and tag @johannes-balkenhol
- Server access / group issues: ping Johannes directly (sysadmin handles `carbodb` group additions)
- Pipeline / model questions: docs in `CarboDB_v3/docs/`, then ask
