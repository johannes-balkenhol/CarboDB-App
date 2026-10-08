# CarboDB-App v2 Codebase Map

## Overview

CarboDB-App is a FastAPI/Vue3 web application for predicting carboxylase enzymes. The codebase is split into:

- **`app/`** — Frontend-facing FastAPI application (main active codebase)
- **`backend/`** — Legacy Flask backend (archived, not actively used)

---

## `app/` Directory (Active Codebase)

### Root Files

#### [`app/main.py`](app/main.py)
**Purpose**: FastAPI application entry point  
**Responsibilities**:
- Creates FastAPI app instance
- Mounts routers (predict, batch, browse)
- Sets up middleware, CORS, static files
- Initializes DataStore/ModelStore on startup

**Dependencies**:
- `app.startup` — ModelStore initialization
- `app.routes.*` — All route routers
- `app.pipeline.predict` — Prediction function

**Called by**: 
- `start_app.sh` → `uvicorn app.main:app`

---

#### [`app/startup.py`](app/startup.py)
**Purpose**: Application initialization and model loading  
**Responsibilities**:
- Loads XGBoost models (`binary_v5.json`, `ec_v5.json`, `km_v5_weighted.json`)
- Loads feature name mappings
- Populates EC class names and Km-trainable EC list
- Provides global `ModelStore` object

**Dependencies**:
- `xgboost`, `json` — Model/config loading

**Called by**:
- `app.main` — On app startup

---

### Routes (`app/routes/`)

Routes expose prediction endpoints to the Vue frontend via FastAPI.

#### [`app/routes/predict.py`](app/routes/predict.py) ⭐ ACTIVE
**Purpose**: Single-sequence prediction endpoint  
**Endpoint**: `POST /predict`  
**Input JSON**:
```json
{
  "sequence": "MAKT...",
  "mode": "fast|standard|pfam|composite",
  "kingdom": "bacteria|plant|archaea|fungi",
  "seq_id": "optional_query_name"
}
```

**Output JSON**:
```json
{
  "is_carboxylase": true/false,
  "carboxylase_probability": 0.0-1.0,
  "ec_predicted": "4.1.1.39",
  "ec_probabilities": {...},
  "km_predicted_mM": 0.0192,
  "sequence_length": 469,
  "features_used": ["composition", "pfam", "interpro", "esm2"],
  ...
}
```

**Dependencies**:
- `app.pipeline.predict.predict_sequence()` — Core prediction logic
- `app.startup.ModelStore` — Pre-loaded models

**Workflow**:
```
POST /predict
  → predict_sequence(seq, mode, kingdom, seq_id)
    → app/pipeline/predict.py (wrapper)
      → app/pipeline/annotate.py (full pipeline)
```

**Temp Files**: 
- Creates `.faa` (temp FASTA) in `/tmp/` directory
- Creates `.json` (result) in `/tmp/` directory
- **FASTA is deleted after use; JSON is kept for debugging**

---

#### [`app/routes/batch.py`](app/routes/batch.py) ⭐ ACTIVE
**Purpose**: Batch prediction submission and status  
**Endpoints**:
- `POST /batch` — Submit batch job
- `GET /batch/{job_id}` — Get job status/results

**Dependencies**:
- Job submission queue
- Background worker

---

#### [`app/routes/browse.py`](app/routes/browse.py) ⭐ ACTIVE
**Purpose**: Browse CarboDB database  
**Endpoints**: Query sequences by EC, Km, PFAM hits, etc.

**Dependencies**:
- SQLite database

---

#### [`app/routes/predict_old.py`](app/routes/predict_old.py) ❌ LEGACY
**Purpose**: Deprecated Flask-style prediction endpoints (not active in FastAPI)  
**Status**: Kept for archival only; do not edit

---

### Pipeline (`app/pipeline/`)

Core ML/annotation logic.

#### [`app/pipeline/config.py`](app/pipeline/config.py) ⭐ CORE
**Purpose**: Configuration, paths, constants  
**Exports**:
- `CFG` — tunable parameters (seq length limits, E-value thresholds, etc.)
- `PATHS` — all file/directory locations
- `setup_logging(name)` — logging initialization

**Key Constants**:
- `PFAM_HMM` → `data/dbs/pfam/Pfam-A.hmm`
- `MODELS` → `models/` (XGBoost JSONs)
- `ML_DIR` → `data/ml/` (feature name lists, EC label maps)

**Used by**: Nearly all pipeline scripts

---

#### [`app/pipeline/predict.py`](app/pipeline/predict.py) ⭐ PRIMARY WRAPPER
**Purpose**: Bridge between routes and annotate.py; handles temp file management  
**Main Function**: `predict_sequence(sequence, mode, kingdom, seq_id)`

**Workflow**:
1. Create temp FASTA file in `/storage/users/projects/CarboDB-App-v2/tmp/`
2. Create temp JSON output path in same directory
3. Call `annotate.py` via subprocess
4. Parse & reformat result to FastAPI schema
5. **Delete FASTA; keep JSON for debugging**

**Temp Directory**: 
- Base: `TMP_DIR = ROOT / "tmp"` (project-local, not `/tmp/`)
- Files created: `NamedTemporaryFile(..., dir=str(TMP_DIR))`

**Dependencies**:
- `subprocess.run()` → `app/pipeline/annotate.py`
- `json` parsing

**Called by**:
- `app.routes.predict.predict()` — REST endpoint

---

#### [`app/pipeline/annotate.py`](app/pipeline/annotate.py) ⭐ MAIN PIPELINE
**Purpose**: Full annotation pipeline for a single sequence  
**Main Function**: `annotate_sequence(seq_id, seq, use_esm2, kingdom) → dict`

**Pipeline Steps**:
1. **Validation** — Check sequence length, composition
2. **Composition (489 dims)** — AA composition, dipeptides, physicochemical
3. **Pfam** — Run HMMER scan against Pfam-A.hmm → 19 Pfam features
4. **InterPro** — Count hits per database (pseudo-features from Pfam)
5. **ESM-2** — Protein language model embeddings (1280 dims)
6. **Feature Assembly** — Stack all features in model order
7. **Binary Prediction** — Is it a carboxylase? (XGBoost binary classifier)
8. **EC Prediction** — Which EC class? (XGBoost multi-class; 10 classes)
9. **Km Prediction** — Estimated Km for CO₂ (XGBoost regressor; only if carb + trainable EC)

**Key Functions**:
- `compute_composition(seq)` — Basic composition features
- `run_hmmer_pfam(seq_id, seq, tmp_dir)` — HMMER scan
- `compute_esm2(seq_id, seq)` — ESM-2 embeddings
- `assemble_feature_vector(...)` — Stack features
- `predict_binary/ec/km(booster, vec)` — XGBoost predictions

**Dependencies**:
- `hmmscan` (binary, external)
- `esm` package (torch)
- `xgboost` (Booster.predict)
- `config.py` — Paths, constants

**Output**: JSON with full prediction + diagnostics

**CLI Usage**:
```bash
python app/pipeline/annotate.py --sequence MAKT... --out result.json --no-esm2
python app/pipeline/annotate.py --fasta input.faa --out result.json
```

---

#### [`app/pipeline/carbodb_features_ref.py`](app/pipeline/carbodb_features_ref.py)
**Purpose**: Alternative annotation implementation (reference/comparison)  
**Status**: Nearly identical to `annotate.py`; kept for reference

**Note**: Both use project `tmp/` directory; temp files are **NOT auto-deleted**

---

#### [`app/pipeline/composition.py`](app/pipeline/composition.py)
**Purpose**: Standalone composition feature extractor  
**Main Function**: `compute_composition(seq) → dict`

**Computes**:
- 20 AA composition (aac_*)
- 400 dipeptide frequencies (dp_*)
- 20 pseudo-AAC features (pse_*)
- ~15 physicochemical (phys_*)
- 5 catalytic motifs (inv_*)
- 17 EC-motif placeholders (motif_*, set to 0 for unknown)

**Total**: ~489 features

**Status**: Active; extracted from `annotate.py`

**Used by**:
- `annotate.py` — Step 1 of pipeline

---

#### [`app/pipeline/feature_extraction_v5.py`](app/pipeline/feature_extraction_v5.py)
**Purpose**: Advanced feature extraction (alternative/experimental)  
**Status**: Contains similar methods to `composition.py`; may be newer version

---

#### [`app/pipeline/feature_extraction.py`](app/pipeline/feature_extraction.py) ❌ LEGACY
**Purpose**: Older feature extraction (v3)  
**Status**: Kept for archival; do not use

**Replacement**: `feature_extraction_v5.py`

---

#### [`app/pipeline/feature_extraction_old.py`](app/pipeline/feature_extraction_old.py) ❌ LEGACY
**Purpose**: Very old feature extraction  
**Status**: Kept for archival; do not use

---

### Data Access (`app/db/`)

#### [`app/db/models_old.py`](app/db/models_old.py) ❌ LEGACY
**Purpose**: SQLAlchemy ORM models (Flask-SQLAlchemy era)  
**Status**: Kept for archival; main app uses FastAPI/SQLite directly

---

---

## `backend/` Directory (Legacy — Not Active)

**Status**: Archived from `Carboxylase_Server` prototype  
**Purpose**: Original Flask-based backend  
**Note**: Do not edit; kept only for reference and potential data exports

### Key Files
- `backend/main.py` — Flask app (not running)
- `backend/config.py` — Configuration
- `backend/carboxylase_search/` — BLAST/HMMER/PROSITE search logic (not integrated into FastAPI)
- `backend/repository/` — Database layer (not used)

---

## Dependency Graph

```
FastAPI App Entry
│
└─→ app/main.py
    ├─→ app/startup.py  [Loads models on startup]
    │   ├─ xgboost models
    │   ├─ feature names
    │   └─ EC mappings
    │
    └─→ app/routes/predict.py  [REST endpoint]
        └─→ app/pipeline/predict.py  [Wrapper + temp management]
            └─→ app/pipeline/annotate.py  [Full pipeline] ⭐
                ├─→ composition.py  [Step 1: Features]
                ├─→ config.py  [Paths + constants]
                ├─ HMMER binary  [Step 3: Pfam scan]
                ├─ ESM model  [Step 5: Embeddings]
                └─→ xgboost/Booster  [Steps 7-9: Predictions]
```

---

## Data Flow: Single Prediction Request

```
1. Vue Frontend
   │
   └─ POST /predict {"sequence": "MAKT...", "mode": "fast", ...}
      │
      └─ app/routes/predict.py
         │
         └─ predict_sequence(seq, mode, kingdom, seq_id)
            │
            ├─ Create temp FASTA in /storage/users/projects/CarboDB-App-v2/tmp/
            ├─ Create temp JSON output path
            │
            └─ subprocess.run([
                  "python", "app/pipeline/annotate.py",
                  "--fasta", fasta_path,
                  "--out", json_path,
                  "--kingdom", kingdom
               ])
               │
               └─ app/pipeline/annotate.py
                  │
                  ├─ Step 1: compute_composition() → 489 features
                  ├─ Step 2-3: run_hmmer_pfam() → 19 Pfam features + 5 InterPro counts
                  ├─ Step 4: compute_esm2() → 1280 embeddings (if mode != "fast")
                  ├─ Step 5: assemble_feature_vector() → single 1814-dim vector
                  ├─ Step 6: predict_binary() → is_carboxylase + confidence
                  ├─ Step 7: predict_ec() → EC class + top-5 probabilities
                  └─ Step 8: predict_km() → Km prediction (if applicable)
                     │
                     └─ Write JSON to output path
            │
            ├─ Read JSON result
            ├─ Reformat to FastAPI schema
            ├─ Delete temp FASTA
            └─ Return result to frontend

2. Vue Frontend receives result
   └─ Display predictions, features, confidence, etc.
```

---

## Environment Variables & Key Paths

| Env Var | Default | Purpose |
|---------|---------|---------|
| `PFAM_HMM` | `data/dbs/pfam/Pfam-A.hmm` | Pfam HMM database |
| `MODELS_DIR` | `models/` | XGBoost model JSON files |
| `ESM2_DEVICE` | `cuda` (or `cpu`) | GPU/CPU for ESM-2 |

| Path | Purpose |
|------|---------|
| `data/models/` | XGBoost model JSONs (binary_v5, ec_v5, km_v5_weighted) |
| `data/ml/` | Feature name lists, EC label maps |
| `data/dbs/pfam/` | Pfam HMM database |
| `data/dbs/blast/` | BLAST database (legacy) |
| `data/dbs/prosite/` | PROSITE database (legacy) |
| `tmp/` | **Project-local temp directory** (changed to avoid `/tmp/` conflicts) |
| `logs/` | Uvicorn & annotation logs |
| `models/data.sqlite` | SQLite database (optional) |

---

## Active Scripts Summary

| File | Purpose | Entry Point |
|------|---------|-------------|
| `app/main.py` | FastAPI app | `uvicorn app.main:app` |
| `app/startup.py` | Model loading | Called by main.py |
| `app/routes/predict.py` | REST API | `POST /predict` |
| `app/routes/batch.py` | Batch jobs | `POST /batch` |
| `app/routes/browse.py` | Browse DB | Various browse endpoints |
| `app/pipeline/predict.py` | Prediction wrapper | Called by predict.py route |
| `app/pipeline/annotate.py` | Full annotation | Called by predict.py wrapper |
| `app/pipeline/composition.py` | Composition features | Called by annotate.py |
| `app/pipeline/config.py` | Config/paths | Imported by all pipeline scripts |

---

## Deprecated/Legacy Scripts

| File | Reason | Replacement |
|------|--------|-------------|
| `backend/*` | Archived Flask backend | Not used; FastAPI active |
| `app/db/models_old.py` | Old ORM models | Direct SQLite queries |
| `app/routes/predict_old.py` | Flask-style routes | `app/routes/predict.py` |
| `app/pipeline/feature_extraction_old.py` | Old extraction | `feature_extraction_v5.py` |
| `app/pipeline/feature_extraction.py` | v3 extraction | `feature_extraction_v5.py` |
| `app/pipeline/carbodb_features_ref.py` | Reference copy | Use `annotate.py` |

---

## Quick Reference: Key Functions

### Annotation Pipeline
```python
from app.pipeline.annotate import annotate_sequence
result = annotate_sequence("query1", "MAKT...", use_esm2=True, kingdom="Bacteria")
```

### Prediction Wrapper
```python
from app.pipeline.predict import predict_sequence
result = predict_sequence("MAKT...", mode="fast", kingdom="plant")
```

### Composition Features
```python
from app.pipeline.composition import compute_composition
feats = compute_composition("MAKT...")  # Returns dict with 489 features
```

---

## Installation & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Start app (local development)
cd /storage/users/projects/CarboDB-App-v2
uvicorn app.main:app --host 0.0.0.0 --port 8091

# Or use convenience script
./start_app.sh restart
```

---

## Notes

1. **Temp Directory Change**: Moved from system `/tmp/` to project `tmp/` directory to avoid conflicts and enable debugging
2. **ESM-2 Cache**: First run downloads ~650MB model; subsequent runs use cache
3. **Models**: Pre-loaded in memory on app startup
4. **Performance**: Fast mode (~2s), standard (~30s with ESM-2)
5. **DB**: Optional SQLite for batch results storage

---

Generated: 2026-06-02  
Version: CarboDB-App v2 (FastAPI + Vue3)
