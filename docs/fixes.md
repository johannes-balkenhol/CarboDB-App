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

## Fixed SQLiteDB connection

Changes to connection in browse.py and browse_cache.py
Changes in pipeline/predict.py and routes/predict.py in def get_similar_from_db
Fixed the predict path so experimental Km no not None, by updating get_similar_from_db() in app/routes/predict.py.
Sdded experimental-Km enrichment after predict_sequence().

## Fixed vite app unresponsiveness

In DatabaseView.vue changed lines with toLocalString() eg.,
<div class="stat-value">{{ fmtInt(stats?.total_sequences) }}</div>

## Details view

Fixed prediction/detail rendering by splitting the shared detail view into prediction vs database detail components while keeping ResultDetail.vue as a dispatcher.

Restored real BLAST nearest-hit behavior for predictions: backend top_similar now comes from run_blast_similar, and routes/predict.py no longer overwrites it with same-EC Km references.

Removed the misleading BLAST/same-EC section.S 

Added database entry metadata such as UniProt ID, CarboDB ID, organism, known/predicted EC, source, reviewed status, length, and amino-acid sequence with copy/link support.



## To DO:
Blast info for browser detials is still missing.

Workspace: /storage/users/job37yv/Projects/CarboDB-App-v2/ (you're in carbodb group — log out + back in if groups doesn't show it). Pull main, read docs/2026-06-24_AMAN_REPORT.md for start/stop/logs. Test the running app in browser (VPN on): http://132.187.22.206:5173/ → Analysis → click RuBisCO example → Analyze. Should return EC 4.1.1.39 after ~30-90s.


Use ec_known/ec_number before ec_predicted in browse.py, so database entries are explained using their curated EC annotation.
Also filter out pfam_n_hits from shap_summary.py, because it is too generic and makes weak support look misleadingly moderate.

change front end how details are shown very non user friendly


fixing the database EC dropdown