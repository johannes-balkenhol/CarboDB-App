## 1. FIXED OUTPUT JSON FOR DOMAIN ANALYSIS

changes in pipeline/predict.py
now bit score evalues and description is visibile on the analysis details
also cahnges in the frontend/src/ExtendedDetails.vue to show these changes

## 2. Batch fix

more cahnges in the predict.py to support batch runs as the JSON output was modifies.

## 3. SYNC JOBS for live prediction

cahnges in predict.py which now runs the jobs directly.
creted rq_queue.py and added rq support.
redis==5.0.8
rq==1.16.2
conda install -c conda-forge redis-server==8.8.0
Refactored single-sequence prediction to run through Redis/RQ instead of blocking the FastAPI request.
Added run_predict_job() in app/pipeline/predict.py as the RQ-compatible worker task wrapper.
Added Redis/RQ queue configuration in app/rq_queue.py.
Renamed the queue helper away from queue.py to avoid shadowing Python’s standard-library queue module.
Updated POST /api/v1/predict to enqueue a prediction job and return a job_id.
Added GET /api/v1/predict/{job_id} for polling queued/running/completed/failed prediction status.
Preserved top_similar enrichment in the polling endpoint so final results match the previous frontend result shape.
Extended /api/v1/health to report Redis connectivity and queue configuration.
Added submit batch() in app/routes/batch.py as the RQ-compatible worker task wrapper.

## Cancel Jobs

Added DELETE /api/v1/predict/{job_id} to cancel queued prediction jobs.
Added DELETE /api/v1/batch/{job_id} to cancel queued batch jobs.
Added Delete button in frontend/src/views/AnalysisView.vue
Added async function cancelPrediction().
Added async function cancelBatchPrediction().

## Loading sqlite cache 

Added Browse_cache.py for app side cache loading
loads db entries in app startup
startup is a bit heavy but response faster
added manual refresh point api/v1/browse/cache/refresh in browse.py

