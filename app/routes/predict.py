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
    """
    Get same-EC experimental Km references from CarboDB.

    Used by GET /predict/{job_id} after a prediction job finishes.
    """
    db_path = os.environ.get("DB_PATH", "data/primary/carbodb.sqlite")

    if not os.path.exists(db_path):
        return []

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT
                s.uniprot_id,
                s.organism,
                s.ec_number,
                s.length,
                s.reviewed,

                COALESCE(kexp.km_experimental_mM, s.km_best_mM) AS km_experimental_mM,
                COALESCE(kexp.km_experimental_mM, s.km_best_mM) * 1000.0 AS km_experimental_uM,
                kexp.km_exp_substrate,
                kexp.km_exp_source

            FROM sequences s

            LEFT JOIN (
                SELECT
                    sequence_id,
                    MIN(km_value_mM) AS km_experimental_mM,
                    substrate AS km_exp_substrate,
                    source AS km_exp_source
                FROM km_evidence
                WHERE evidence_tier = 1
                   OR LOWER(source) = 'brenda'
                GROUP BY sequence_id
            ) kexp
                ON kexp.sequence_id = s.id

            WHERE s.label = 1
              AND s.ec_number = ?
              AND COALESCE(kexp.km_experimental_mM, s.km_best_mM) IS NOT NULL

            LIMIT 300
        """, (ec,))

        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        import math

        for r in rows:
            exp_uM = r.get("km_experimental_uM")

            if km_uM and exp_uM and km_uM > 0 and exp_uM > 0:
                r["_distance"] = abs(math.log10(km_uM) - math.log10(exp_uM))
            else:
                r["_distance"] = 999.0

            r["_reviewed_sort"] = 0 if r.get("reviewed") else 1

        rows.sort(key=lambda r: (r["_distance"], r["_reviewed_sort"]))

        out = []

        for i, r in enumerate(rows[:limit], start=1):
            out.append({
                "rank": i,
                "uniprot_id": r.get("uniprot_id"),
                "organism": r.get("organism"),
                "ec_number": r.get("ec_number"),
                "length": r.get("length"),
                "reviewed": bool(r.get("reviewed")),

                "km_predicted_uM": round(km_uM, 1) if km_uM is not None else None,
                "km_experimental_uM": (
                    round(r["km_experimental_uM"], 1)
                    if r.get("km_experimental_uM") is not None
                    else None
                ),
                "km_exp_substrate": r.get("km_exp_substrate"),
                "km_exp_source": r.get("km_exp_source") or "brenda",

                "identity_pct": None,
                "evalue": None,
                "align_length": None,

                "tier": "same_ec",
                "tier_label": "same EC experimental Km",
            })

        return out

    except Exception as e:
        print(f"get_similar_from_db failed: {e}")
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