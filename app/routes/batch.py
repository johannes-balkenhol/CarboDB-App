from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from typing import Optional
import os

from rq.job import Job
from rq.exceptions import NoSuchJobError

from ..rq_queue import get_batch_queue, get_redis_connection

router = APIRouter(tags=["batch"])

JOBS_DIR = os.environ.get("JOBS_DIR", "jobs")
MAX_FAST = int(os.environ.get("MAX_BATCH_FAST", 5000))
MAX_STANDARD = int(os.environ.get("MAX_BATCH_STANDARD", 500))


@router.post("/batch")
def submit_batch(
    file: UploadFile = File(...),
    mode: str = Form("fast"),
    kingdom: str = Form("plant"),
    email: Optional[str] = Form(None),
):
    """
    Submit a batch FASTA prediction job to RQ.
    """
    if mode not in ("fast", "standard"):
        raise HTTPException(400, "Batch mode must be fast or standard")

    content = file.file.read()
    text = content.decode("utf-8", errors="ignore")

    n_seqs = count_fasta_sequences(text)

    if n_seqs == 0:
        raise HTTPException(400, "No sequences found in FASTA file")

    max_seqs = MAX_STANDARD if mode == "standard" else MAX_FAST

    if n_seqs > max_seqs:
        raise HTTPException(400, f"Too many sequences: {n_seqs} > max {max_seqs}")

    try:
        queue = get_batch_queue()

        job = queue.enqueue(
            "app.pipeline.predict.run_batch_predict_job",
            fasta_text=text,
            mode=mode,
            kingdom=kingdom,
            job_timeout=int(os.environ.get("BATCH_JOB_TIMEOUT", "3600")),
            result_ttl=int(os.environ.get("BATCH_RESULT_TTL", "86400")),
            failure_ttl=int(os.environ.get("BATCH_FAILURE_TTL", "86400")),
        )

        est_min = round(n_seqs * (45 if mode == "standard" else 3) / 60)

        return {
            "job_id": job.id,
            "status": "queued",
            "n_sequences": n_seqs,
            "estimated_minutes": est_min,
            "message": "Batch prediction job submitted",
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to enqueue batch job: {e}")


@router.get("/batch/{job_id}")
def get_batch_job(job_id: str):
    """
    Poll a batch prediction job.
    """
    try:
        redis_conn = get_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)

    except NoSuchJobError:
        raise HTTPException(404, "Batch job not found")

    except Exception as e:
        raise HTTPException(500, f"Failed to fetch batch job: {e}")

    rq_status = job.get_status(refresh=True)

    response = {
        "job_id": job.id,
        "status": rq_status,
        "result": None,
        "summary": None,
        "error": None,
    }

    if rq_status in ("queued", "deferred", "scheduled"):
        return response

    if rq_status in ("canceled", "cancelled"):
        response["status"] = "cancelled"
        response["error"] = {
            "message": "Batch job was cancelled",
        }
        return response

    if rq_status == "started":
        response["status"] = "running"
        return response

    if rq_status == "failed":
        response["status"] = "failed"
        response["error"] = {
            "message": job.exc_info or "Batch job failed",
        }
        return response

    if rq_status == "finished":
        payload = job.result or {}

        if payload.get("status") == "failed":
            response["status"] = "failed"
            response["error"] = payload.get("error") or {
                "message": "Batch prediction failed",
            }
            return response

        response["status"] = "completed"
        response["result"] = payload.get("results", [])
        response["summary"] = payload.get("summary")
        response["n_sequences"] = payload.get("n_sequences")
        response["runtime_seconds"] = payload.get("runtime_seconds")

        return response

    return response


@router.get("/batch/{job_id}/results.tsv")
def download_batch_results(job_id: str):
    """
    Download batch prediction results as TSV.
    """
    try:
        redis_conn = get_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)

    except NoSuchJobError:
        raise HTTPException(404, "Batch job not found")

    except Exception as e:
        raise HTTPException(500, f"Failed to fetch batch job: {e}")

    rq_status = job.get_status(refresh=True)

    if rq_status != "finished":
        raise HTTPException(400, f"Batch job not completed. Status: {rq_status}")

    payload = job.result or {}

    if payload.get("status") != "completed":
        raise HTTPException(400, "Batch job did not complete successfully")

    tsv = payload.get("tsv")

    if not tsv:
        raise HTTPException(404, "Results TSV not found")

    return Response(
        content=tsv,
        media_type="text/tab-separated-values",
        headers={
            "Content-Disposition": f'attachment; filename="carbodb_batch_{job_id}.tsv"'
        },
    )

@router.delete("/batch/{job_id}")
def cancel_batch_job(job_id: str):
    """
    Cancel a queued batch prediction job.
    """
    try:
        redis_conn = get_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)

    except NoSuchJobError:
        raise HTTPException(404, "Batch job not found")

    except Exception as e:
        raise HTTPException(500, f"Failed to fetch batch job: {e}")

    status = job.get_status(refresh=True)

    if status in ("queued", "deferred", "scheduled"):
        job.cancel()
        return {
            "job_id": job.id,
            "status": "cancelled",
            "message": "Batch job cancelled before execution",
        }

    if status == "started":
        return {
            "job_id": job.id,
            "status": status,
            "message": "Batch job is already running and cannot be safely cancelled yet",
        }

    return {
        "job_id": job.id,
        "status": status,
        "message": f"Batch job is already {status}",
    }

@router.get("/jobs/{job_id}/seq/{seq_id}")
def get_job_seq(job_id: str, seq_id: str):
    seq_path = os.path.join(JOBS_DIR, job_id, "seqs", f"{seq_id}.json")
    if not os.path.exists(seq_path):
        raise HTTPException(404, "Sequence not found in job cache")
    try:
        with open(seq_path) as f:
            data = json.load(f)
        return data
    except Exception:
        raise HTTPException(500, "Failed to read cached sequence data")


def run_batch_job(job_id: str, input_path: str, mode: str, kingdom: str):
    from ..pipeline.predict import predict_sequence
    job_dir = os.path.join(JOBS_DIR, job_id)
    meta_path = os.path.join(job_dir, "job.json")
    seqs_dir = os.path.join(job_dir, "seqs")
    os.makedirs(seqs_dir, exist_ok=True)

    def update_meta(updates):
        with open(meta_path) as f:
            meta = json.load(f)
        meta.update(updates)
        with open(meta_path, 'w') as f:
            json.dump(meta, f)

    update_meta({"status": "running", "started_at": datetime.utcnow().isoformat()})
    result_path = os.path.join(job_dir, "results.tsv")
    header = "seq_id\tlength\tis_carboxylase\tprob_binary\tec_predicted\tec_confidence\tkm_predicted_mM\tkm_predicted_uM\tpfam_hits\tnovelty_flag\truntime_seconds\n"
    processed = 0
    try:
        with open(input_path) as fin, open(result_path, 'w') as fout:
            fout.write(header)
            seqs = {}
            sid, buf = None, []
            for line in fin:
                line = line.strip()
                if line.startswith('>'):
                    if sid:
                        seqs[sid] = ''.join(buf)
                    sid = line[1:].split()[0]
                    buf = []
                else:
                    buf.append(line)
            if sid:
                seqs[sid] = ''.join(buf)
            for seq_id, sequence in seqs.items():
                try:
                    r = predict_sequence(sequence, mode=mode,
                                        kingdom=kingdom, seq_id=seq_id)
                    # Cache per-sequence JSON for quick lookups by frontend
                    try:
                        with open(os.path.join(seqs_dir, f"{seq_id}.json"), 'w') as sf:
                            json.dump(r, sf)
                    except Exception:
                        pass
                    
                    pfam_hits = r.get("pfam_hits", [])
                    pfam_str = ";".join(
                        h.get("accession") or h.get("target_name") or ""
                        for h in pfam_hits
                        if isinstance(h, dict)
                    )

                    fout.write(
                        f"{seq_id}\t{r['sequence_length']}\t"
                        f"{r['is_carboxylase']}\t{r['carboxylase_probability']:.4f}\t"
                        f"{r['ec_predicted']}\t{r['ec_confidence']:.4f}\t"
                        f"{r.get('km_predicted_mM') or ''}\t"
                        f"{r.get('km_predicted_uM') or ''}\t"
                        f"{pfam_str}\t{r.get('novelty_flag','')}\t"
                        f"{r.get('runtime_seconds','')}\n"
                    )

                    fout.flush()
                except Exception as e:
                    fout.write(f"{seq_id}\t0\tERROR\t\t\t\t\t\t\t\t{str(e)[:100]}\n")
                    # write error JSON so frontend can at least display the row
                    try:
                        with open(os.path.join(seqs_dir, f"{seq_id}.json"), 'w') as sf:
                            json.dump({'error': str(e)}, sf)
                    except Exception:
                        pass
                processed += 1
                if processed % 10 == 0:
                    update_meta({"processed": processed})
        update_meta({"status": "completed", "processed": processed,
                     "completed_at": datetime.utcnow().isoformat(),
                     "result_file": result_path})
    except Exception as e:
        update_meta({"status": "failed", "error_message": str(e)})

def count_fasta_sequences(text: str) -> int:
    return len([line for line in text.splitlines() if line.strip().startswith(">")])

# keeping old endpoints

@router.get("/jobs/{job_id}")
def get_job_compat(job_id: str):
    return get_batch_job(job_id)


@router.get("/jobs/{job_id}/results.tsv")
def download_results_compat(job_id: str):
    return download_batch_results(job_id)