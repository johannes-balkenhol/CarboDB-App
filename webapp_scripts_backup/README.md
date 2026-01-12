# CarboxyPred Webapp Scripts Backup
## January 12, 2026

This package contains all the new scripts developed for the CarboxyPred webapp after the docker-working branch.

## What's New (compared to docker-working branch)

### 1. Database Schema v2
- Evidence-based architecture (EC/Km from multiple sources)
- Priority-based annotation resolution
- 447 ML features storage
- Views for best annotations and evidence comparison

### 2. ML Prediction Pipeline
- Binary classifier v3 (main model)
- Binary classifier v5 (14 EC classes)
- EC classifier (25 classes)
- Km predictor with EC-conditional model
- **CRITICAL FIX**: Km conversion `km_uM = (10 ** km_log) * 1000`

### 3. Database API
- `/db/stats` - Database statistics
- `/db/search` - Filtered search with pagination
- `/db/sequence/<id>` - Full sequence record
- `/db/sequence/<id>/features` - 447 features
- `/db/ec-classes` - EC class list
- `/db/evidence-comparison` - Exp vs predicted

### 4. Batch Prediction
- FASTA input parsing
- Full pipeline (v3, v5, EC, Km)
- Database matching for known sequences
- TSV export

---

## Directory Structure

```
webapp_scripts_backup/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── routes.py            # Main API routes + prediction endpoints
│   │   ├── db_routes.py         # Database API routes
│   │   ├── database_service.py  # Database access layer
│   │   ├── ml_prediction.py     # ML prediction module
│   │   ├── batch_prediction.py  # Batch prediction pipeline
│   │   └── tasks.py             # Scheduled tasks
│   ├── database/
│   │   └── schema.sql           # Database schema v2
│   ├── Dockerfile               # Backend container
│   ├── config.py                # Flask configuration
│   ├── main.py                  # Entry point
│   └── requirements.txt         # Python dependencies
├── docker-compose.yml           # Docker services
├── import_695k_predictions.py   # Import script for HPC results
└── README.md                    # This file
```

---

## Quick Start

### 1. Merge with docker-working branch

```bash
# Clone old version
git clone -b docker-working https://github.com/Eva-jcr/Carboxylase_Server.git
cd Carboxylase_Server

# Copy new scripts
cp -r /path/to/webapp_scripts_backup/backend/app/* backend/app/
cp /path/to/webapp_scripts_backup/backend/Dockerfile backend/
cp /path/to/webapp_scripts_backup/backend/config.py backend/
cp /path/to/webapp_scripts_backup/docker-compose.yml .
cp /path/to/webapp_scripts_backup/backend/database/schema.sql backend/database/
```

### 2. Setup Database

```bash
# Create database from schema
sqlite3 backend/database_files/carboxylase.db < backend/database/schema.sql

# Import 695k predictions (8.2 GB CSV from HPC)
python import_695k_predictions.py \
    carboxypred_update/data/full_predictions_20260107_190147.csv \
    backend/database_files/carboxylase.db
```

### 3. Copy Models

```bash
# Models from HPC (or carboxypred_update folder)
mkdir -p models
cp carboxypred_update/models/*.pkl models/
```

### 4. Run with Docker

```bash
docker-compose build
docker-compose up -d

# Test
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/db/stats
```

---

## Key Files Explained

### backend/app/ml_prediction.py
Main ML prediction module with:
- Feature extraction (447 features)
- v3/v5 binary classification
- EC classification
- Km prediction with **CORRECT unit conversion**

```python
# CRITICAL: Correct Km conversion
# Model outputs log10(Km_mM)
km_uM = (10 ** km_log) * 1000
```

### backend/app/db_routes.py
Database API endpoints:
- Search with filters (EC, organism, length, etc.)
- Evidence-based annotation retrieval
- Feature importance

### backend/app/batch_prediction.py
Batch analysis pipeline:
- FASTA parsing
- Database matching
- Similar sequence lookup
- TSV export

### backend/database/schema.sql
Evidence-based database schema:
- `sequences` - Core sequence data
- `ec_evidence` - EC annotations with sources
- `km_evidence` - Km values with sources
- `binary_predictions` - ML predictions
- `sequence_features` - 447 features JSON
- Views for best annotations

---

## API Endpoints Summary

### Prediction
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Single sequence prediction |
| `/predict-batch` | POST | Batch FASTA prediction |
| `/model-info` | GET | Model status |

### Database
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/db/stats` | GET | Database statistics |
| `/db/search` | GET | Search with filters |
| `/db/sequence/<id>` | GET | Full sequence record |
| `/db/sequence/<id>/features` | GET | 447 ML features |
| `/db/ec-classes` | GET | All EC classes |
| `/db/evidence-comparison` | GET | Exp vs predicted |

---

## Model Files Required

Place these in `models/` directory:
- `binary_classifier_v3.pkl` - Main binary classifier
- `binary_classifier_v5.pkl` - 14-EC binary classifier
- `ec_classifier_v3.pkl` - EC class predictor
- `km_predictor_v3.pkl` - Km regressor

**Version Requirements:**
- scikit-learn==1.5.2
- numpy==1.26.4
- pandas==2.2.3

---

## Validation Results (695k scan)

| Metric | Value |
|--------|-------|
| Sequences processed | 695,384 |
| Pearson R (log Km) | **0.975** |
| Within 2-fold | 90.8% |
| Within 3-fold | 96.1% |
| V3 positive | 99.5% |

---

## Contact

Questions about this backup? Check the chat transcripts in `/mnt/transcripts/`

Key transcripts:
- `2026-01-06-18-17-38-carboxypred-database-integration-complete.txt`
- `2026-01-07-09-43-40-carboxypred-database-v2-webapp-complete.txt`
- `2026-01-07-11-09-21-batch-prediction-pipeline-integration.txt`
