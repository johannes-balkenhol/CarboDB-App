# CarboDB-App

Frontend (Vue 3) and serving-side FastAPI for [CarboDB](https://github.com/johannes-balkenhol/CarboDB) —
a database and ML pipeline for CO₂-fixing carboxylases. Predicts whether a sequence
is a carboxylase, classifies its EC number, and estimates its Km for CO₂/HCO₃⁻.

The ML pipeline, training data, and trained models live in the **backend repo**:
[johannes-balkenhol/CarboDB](https://github.com/johannes-balkenhol/CarboDB).
This repo is the **web layer** that exposes the pipeline through a UI.

---

## Repo layout

```
CarboDB-App-v2/
├── app/                       ← FastAPI app (LIVE)
│   ├── main.py                ← uvicorn entrypoint
│   ├── routes/                ← /predict, /batch, /browse
│   ├── pipeline/              ← prediction pipeline used by /predict
│   ├── db/                    ← SQLite helpers
│   └── startup.py             ← model + DB warm-up on app start
├── frontend/                  ← Vue 3 + Vite single-page app (LIVE)
│   ├── src/
│   │   ├── views/             ← page-level components (Home, Analysis, Database, …)
│   │   ├── components/        ← reusable widgets (ResultDetail, ExtendedDetails, …)
│   │   ├── stores/            ← Pinia stores
│   │   └── router/            ← vue-router config
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── models/                    ← XGBoost JSONs (binary_v5, ec_v5, km_v5_weighted)
├── start_app.sh               ← convenience: start | stop | restart | status | logs
├── docker/                    ← Dockerfile + docker-compose (NOT YET in production use)
├── docker-compose.yml         ← top-level compose
├── jobs/                      ← per-job working dirs (live predictions)
├── logs/                      ← uvicorn webapp.log
└── resources/                 ← seed alignments, HMM profiles, prosite patterns
                                  (legacy data, kept because the search routes still reference them)
```

The `/external` route (UniProt + AlphaFold proxy) lives in the **backend repo**
under `webapp/app/routes/external.py`. It runs as part of the same uvicorn process.

### Legacy code, kept on disk but NOT running

These exist for archival reasons; do not edit and do not assume they reflect current behavior:

- `backend/`              — v1 Flask-style backend from the `Carboxylase_Server` prototype
- `app/routes/predict_old.py`
- `app/pipeline/feature_extraction_old.py`
- `app/pipeline/feature_extraction.py`  (older v3 extraction; current is `feature_extraction_v5.py`)
- `app/db/models_old.py`

A future cleanup pass should move these to a `legacy/` branch and delete from `main`.

---

## Quick start (local development)

### Prerequisites
- conda or miniforge (env name: `carboxylase`, provisioned per the backend repo)
- Node.js ≥ 18
- The CarboDB SQLite database (~50 GB) — get it from the backend repo's data
  ingestion pipeline (scripts 01–05) or copy from the shared server.

### Backend

```bash
conda activate carboxylase
export DB_PATH=/path/to/carbodb.sqlite
uvicorn app.main:app --host 0.0.0.0 --port 8090
```

The backend exposes the API at `http://localhost:8090/api/v1/...`.

### Frontend

```bash
cd frontend
npm install
npm run dev    # vite dev server on port 5173
```

The frontend proxies `/api/v1/*` to `http://localhost:8090` via `vite.config.js`.

### Both at once

`./start_app.sh` runs uvicorn + vite together. Subcommands: `start`, `stop`, `restart`,
`status`, `logs`. Reads PIDs from `logs/`.

---

## Environment variables

Backend reads these via `os.environ.get(..., default)`:

| Var | Default | Used by | Purpose |
|-----|---------|---------|---------|
| `DB_PATH` | `data/carbodb.sqlite` | predict.py, browse.py, main.py | SQLite path |
| `MODELS_DIR` | `models` | startup.py | XGBoost JSON dir |
| `JOBS_DIR` | `jobs` | batch.py | Per-batch scratch space |
| `MAX_BATCH_FAST` | `5000` | batch.py | Limit for fast (DB-lookup) batches |
| `MAX_BATCH_STANDARD` | `500` | batch.py | Limit for live-prediction batches |
| `PFAM_HMM` | `data/Pfam-A.hmm` | pipeline/predict.py | Pfam profile DB for hmmscan |
| `ESM2_DEVICE` | `cpu` | startup.py | Set to `cuda` if a GPU is available |
| `BRENDA_EMAIL` | _empty_ | pipeline/carbodb_config.py | BRENDA SOAP credentials (script 01 only) |
| `BRENDA_PASSWORD` | _empty_ | pipeline/carbodb_config.py | SHA256 hash of BRENDA password |

---

## Where to start reading

For full documentation see the backend repo's `docs/` folder, especially:

- [`docs/HANDOFF.md`](https://github.com/johannes-balkenhol/CarboDB/blob/main/docs/HANDOFF.md) — top-level onboarding, what to read first
- [`docs/ARCHITECTURE.md`](https://github.com/johannes-balkenhol/CarboDB/blob/main/docs/ARCHITECTURE.md) — data flow, 3-step ML cascade (binary → EC → Km), feature space, request lifecycles
- [`docs/WEBAPP.md`](https://github.com/johannes-balkenhol/CarboDB/blob/main/docs/WEBAPP.md) — backend route catalog, frontend component tree, debugging hints, Vue 3 / NGL reactivity gotcha
- [`docs/EXTERNAL_INTEGRATION.md`](https://github.com/johannes-balkenhol/CarboDB/blob/main/docs/EXTERNAL_INTEGRATION.md) — UniProt + AlphaFold proxy and caching design
- [`docs/DEPLOYMENT.md`](https://github.com/johannes-balkenhol/CarboDB/blob/main/docs/DEPLOYMENT.md) — install, conda env, services, staged production plan
- [`docs/ROADMAP.md`](https://github.com/johannes-balkenhol/CarboDB/blob/main/docs/ROADMAP.md) — done / in-progress / planned items

The backend repo also contains the schema (`scripts/schema.sql`) and the data-ingestion
pipeline (`scripts/01_*.py … 23_*.py`).

---

## Status

| Component | State |
|-----------|-------|
| Pipeline 01 → 23 | ✅ runnable end-to-end on the server |
| Database (50 GB SQLite, 2.38 M sequences) | ✅ live |
| Backend `/predict` (live mode) | ⚠️  works, ~100s per ~500aa sequence on CPU (ESM-2 bottleneck) |
| Backend `/browse` | ✅ ~12s warm, was 17s |
| Backend `/stats` | ✅ 15 ms warm (was 60 s) |
| Backend `/external` (UniProt + AlphaFold proxy, in CarboDB repo) | ✅ 30-day cache, ~80 ms warm |
| Frontend Database view + ExtendedDetails (NGL viewer) | ✅ working |
| Frontend Analysis page (live prediction) | ✅ working, but no ExtendedDetails yet |
| Docker / containerized deployment | 🚧 Dockerfiles present, not in production use |
| Tests | ❌ not yet — see ROADMAP #18 |
| Production hosting | ❌ planned, see DEPLOYMENT.md |

---

## License

Proprietary — University of Würzburg, Balkenhol lab.
