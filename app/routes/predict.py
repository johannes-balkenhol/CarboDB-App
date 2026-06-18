"""
routes/predict.py — Single sequence prediction endpoint
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3, os

from rq.job import Job
from rq.exceptions import NoSuchJobError

from ..rq_queue import get_predict_queue, get_redis_connection
from ..startup import ModelStore

router = APIRouter(tags=["predict"])

class PredictRequest(BaseModel):
    sequence: str
    mode: str = "fast"        # fast | standard | pfam | composite
    kingdom: str = "plant"    # bacteria | plant | archaea | fungi
    seq_id: Optional[str] = "query"

@router.post("/predict")
def submit_predict(req: PredictRequest):
    """
    Submit a single-sequence prediction job.

    This endpoint no longer blocks while prediction runs. It returns a job_id
    that the frontend can poll via GET /predict/{job_id}.
    """
    if not ModelStore.ready:
        raise HTTPException(503, "Models not loaded yet")

    sequence = (req.sequence or "").strip()

    if not sequence or len(sequence) < 10:
        raise HTTPException(400, "Sequence too short")

    if req.mode not in ("fast", "standard", "pfam", "composite"):
        raise HTTPException(400, f"Invalid mode: {req.mode}")

    try:
        queue = get_predict_queue()

        job = queue.enqueue(
            "app.pipeline.predict.run_predict_job",
            sequence=sequence,
            mode=req.mode,
            kingdom=req.kingdom,
            seq_id=req.seq_id or "query",
            job_timeout=int(os.environ.get("PREDICT_JOB_TIMEOUT", "300")),
            result_ttl=int(os.environ.get("PREDICT_RESULT_TTL", "3600")),
            failure_ttl=int(os.environ.get("PREDICT_FAILURE_TTL", "86400")),
        )

        return {
            "job_id": job.id,
            "status": "queued",
            "message": "Prediction job submitted",
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to enqueue prediction job: {e}")

@router.get("/predict/{job_id}")
def get_predict_job(job_id: str):
    """
    Poll a single-sequence prediction job.
    """
    try:
        redis_conn = get_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)

    except NoSuchJobError:
        raise HTTPException(404, "Prediction job not found")

    except Exception as e:
        raise HTTPException(500, f"Failed to fetch prediction job: {e}")

    rq_status = job.get_status(refresh=True)

    response = {
        "job_id": job.id,
        "status": rq_status,
        "result": None,
        "error": None,
    }

    if rq_status in ("queued", "deferred", "scheduled"):
        return response
    
    if rq_status in ("canceled", "cancelled"):
        response["status"] = "cancelled"
        response["error"] = {
            "message": "Prediction job was cancelled",
        }
        return response

    if rq_status == "started":
        response["status"] = "running"
        return response

    if rq_status == "failed":
        response["status"] = "failed"
        response["error"] = {
            "message": job.exc_info or "Prediction job failed",
        }
        return response

    if rq_status == "finished":
        payload = job.result or {}

        # run_predict_job catches biological/runtime errors and returns
        # {"status": "failed", "error": ...}, so inspect payload too.
        if payload.get("status") == "failed":
            response["status"] = "failed"
            response["error"] = payload.get("error") or {
                "message": "Prediction failed",
            }
            return response

        result = payload.get("result")

        if result and result.get("ec_predicted") and result.get("is_carboxylase"):
            result["top_similar"] = get_similar_from_db(
                result["ec_predicted"],
                result.get("km_predicted_uM"),
            )
        elif result:
            result["top_similar"] = []

        response["status"] = "completed"
        response["result"] = result
        response["runtime_seconds"] = payload.get("runtime_seconds")

        return response

    return response

def get_similar_from_db(ec: str, km_uM: Optional[float], limit: int = 8) -> list:
    """Get similar sequences from CarboDB for context."""
    db_path = os.environ.get("DB_PATH", "data/carbodb.sqlite")
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT s.uniprot_id, s.organism, p.km_pred_mM*1000 as km_pred_uM,
                   s.reviewed
            FROM sequences s
            JOIN predictions p ON p.sequence_id = s.id
            WHERE s.label=1 AND s.ec_number=?
            AND p.km_pred_mM IS NOT NULL AND s.reviewed=1
            ORDER BY RANDOM()
            LIMIT ?
        """, (ec, limit))
        rows = cur.fetchall()
        conn.close()
        return [{'uniprot_id': r['uniprot_id'],
                 'organism': r['organism'],
                 'km_predicted_uM': round(r['km_pred_uM'], 1) if r['km_pred_uM'] else None,
                 'km_experimental_uM': None,
                 'reviewed': bool(r['reviewed'])} for r in rows]
    except Exception as e:
        return []
    
# cancellation endpoint

@router.delete("/predict/{job_id}")
def cancel_predict_job(job_id: str):
    """
    Cancel a queued prediction job.

    If the job is already running, RQ cannot reliably kill it without extra worker-control
    setup, so we report that clearly.
    """
    try:
        redis_conn = get_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)

    except NoSuchJobError:
        raise HTTPException(404, "Prediction job not found")

    except Exception as e:
        raise HTTPException(500, f"Failed to fetch prediction job: {e}")

    status = job.get_status(refresh=True)

    if status in ("queued", "deferred", "scheduled"):
        job.cancel()
        return {
            "job_id": job.id,
            "status": "cancelled",
            "message": "Prediction job cancelled before execution",
        }

    if status in ("started",):
        return {
            "job_id": job.id,
            "status": status,
            "message": "Job is already running and cannot be safely cancelled yet",
        }

    return {
        "job_id": job.id,
        "status": status,
        "message": f"Job is already {status}",
    }