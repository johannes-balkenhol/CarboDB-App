import os
import sys
import time
import logging
import subprocess
import json
import tempfile
import sqlite3
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from ..startup import ModelStore, EC_NAMES, KM_EC_CLASSES
from .blast_similar import run_blast_similar

log = logging.getLogger(__name__)

# Define project tmp directory
ROOT = Path(__file__).resolve().parents[2]  # Navigate to project root
TMP_DIR = ROOT / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

# Define valid modes and kingdoms for prediction
VALID_PREDICT_MODES = {"fast", "standard", "pfam", "composite"}
VALID_KINGDOMS = {"bacteria", "plant", "archaea", "fungi"}

# Use local copy of annotation script (standalone, no CarboDB repo needed)
_local = Path(__file__).parent / "annotate.py"

_parent_scripts = Path(__file__).resolve()
candidate = None

for _ in range(6):
    _parent_scripts = _parent_scripts.parent
    possible = _parent_scripts / "scripts" / "11_annotate_sequence.py"
    if possible.exists():
        candidate = possible
        break

SCRIPT_11 = _local if _local.exists() else candidate

if SCRIPT_11 is None:
    log.warning("Could not find annotate.py or scripts/11_annotate_sequence.py")


def _normalise_pfam_hits(pfam_hits):
    """
    Preserve enriched Pfam hit dictionaries from annotate.py / Script 11.

    Supports both the new format:

        [
            {
                "target_name": "RuBisCO_large",
                "accession": "PF00016",
                "evalue": 1.5e-137,
                "bitscore": 458.3,
                "full_sequence_evalue": 1.2e-137,
                "full_sequence_bitscore": 458.6,
                "description": "..."
            }
        ]

    and the old format:

        ["PF00016", "PF02788"]
    """
    normalised = []

    for hit in pfam_hits or []:
        if isinstance(hit, dict):
            normalised.append({
                "target_name": hit.get("target_name"),
                "accession": hit.get("accession"),
                "evalue": hit.get("evalue"),
                "bitscore": hit.get("bitscore"),
                "full_sequence_evalue": hit.get("full_sequence_evalue"),
                "full_sequence_bitscore": hit.get("full_sequence_bitscore"),
                "description": hit.get("description"),
            })
        else:
            # Backwards compatibility with older Script 11 output
            normalised.append({
                "target_name": None,
                "accession": str(hit),
                "evalue": None,
                "bitscore": None,
                "full_sequence_evalue": None,
                "full_sequence_bitscore": None,
                "description": None,
            })

    return normalised


def get_similar_from_db(ec: str, km_uM: Optional[float], limit: int = 8) -> list[dict[str, Any]]:
    """
    Get same-EC database sequences that have experimental Km values.

    This fills result["top_similar"] for /predict and batch details.
    It is not true BLAST hit-list logic yet; it uses same EC class and
    ranks references by closeness between predicted Km and experimental Km.
    """
    db_path = os.environ.get("DB_PATH", "data/primary/carbodb.sqlite")

    if not os.path.exists(db_path):
        return []

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                s.uniprot_id,
                s.organism,
                s.ec_number,
                s.length,
                s.reviewed,

                p.km_pred_mM * 1000.0 AS db_predicted_km_uM,

                kexp.km_experimental_mM AS km_experimental_mM,
                kexp.km_experimental_mM * 1000.0 AS km_experimental_uM,
                kexp.km_exp_substrate,
                kexp.km_exp_source,
                1 AS has_direct_experimental_km,
                'experimental_table' AS km_source_type

            FROM sequences s

            LEFT JOIN predictions p
                ON p.sequence_id = s.id

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
              AND kexp.km_experimental_mM IS NOT NULL

            LIMIT 300
            """,
            (ec,),
        )

        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        import math

        for r in rows:
            exp_uM = r.get("km_experimental_uM")

            if km_uM and exp_uM and km_uM > 0 and exp_uM > 0:
                r["_distance"] = abs(math.log10(km_uM) - math.log10(exp_uM))
            else:
                r["_distance"] = 999.0

            # Prefer reviewed entries if distances are similar/equal.
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
                "km_exp_source": r.get("km_exp_source"),
                "has_direct_experimental_km": True,
                "km_source_type": "experimental_table",

                # No true pairwise BLAST identity here yet.
                "identity_pct": None,
                "evalue": None,
                "align_length": None,

                "tier": "same_ec_experimental_km",
                "tier_label": "same EC experimental Km",
            })

        return out

    except Exception:
        log.exception("Failed to query experimental Km references from DB")
        return []

def predict_sequence(sequence, mode="fast", kingdom="plant", seq_id="query"):
    t = time.time()

    if SCRIPT_11 is None:
        raise FileNotFoundError(
            "Could not find annotation script: expected local annotate.py "
            "or scripts/11_annotate_sequence.py"
        )

    # Write sequence to temp FASTA
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".faa",
        delete=False,
        dir=str(TMP_DIR),
    ) as f:
        f.write(f">{seq_id}\n{sequence.strip()}\n")
        fasta_path = f.name

    with tempfile.NamedTemporaryFile(
        suffix=".json",
        delete=False,
        dir=str(TMP_DIR),
    ) as f:
        out_path = f.name

    try:
        cmd = [
            sys.executable,
            str(SCRIPT_11),
            "--fasta",
            fasta_path,
            "--out",
            out_path,
            "--kingdom",
            kingdom,
        ]

        if mode in ("fast", "pfam"):
            cmd.append("--no-esm2")

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=120,
            env={
                **os.environ,
                "PFAM_HMM": os.environ.get("PFAM_HMM", "data/Pfam-A.hmm"),
            },
        )

        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")[:500]
            raise ValueError(stderr)

        with open(out_path) as fh:
            raw = json.load(fh)

        d = raw[0] if isinstance(raw, list) else raw

        pfam_hits = _normalise_pfam_hits(d.get("pfam_hits", []))

        pfam_accessions = [
            hit["accession"]
            for hit in pfam_hits
            if hit.get("accession")
        ]

        pfam_target_names = [
            hit["target_name"]
            for hit in pfam_hits
            if hit.get("target_name")
        ]

        pfam_descriptions = [
            hit["description"]
            for hit in pfam_hits
            if hit.get("description")
        ]

        carb_prob = d.get("carboxylase_probability", 0.0) or 0.0
        km_mM = d.get("km_predicted_mM")

        # Normalise output to webapp format
        return {
            # Query metadata
            "cdb_query_id": d.get("cdb_query_id", seq_id),
            "sequence_length": d.get("sequence_length", 0),

            # Binary prediction
            "is_carboxylase": d.get("is_carboxylase", False),
            "carboxylase_probability": carb_prob,
            "confidence": d.get("confidence"),

            # EC prediction
            "ec_predicted": d.get("ec_predicted", "unknown"),
            "ec_name": d.get("ec_name", ""),
            "ec_confidence": d.get("ec_probabilities", {}).get(
                d.get("ec_predicted", ""),
                0.0,
            ),
            "ec_probabilities": d.get("ec_probabilities", {}),

            # Km prediction
            "km_predicted_mM": km_mM,
            "km_predicted_uM": km_mM * 1000 if km_mM is not None else None,
            "km_predicted_log10": d.get("km_predicted_log10"),
            "km_ec_used": d.get("km_ec_used"),

            # Enriched Pfam hits: preserved from Script 11 JSON
            "pfam_hits": pfam_hits,

            # Convenience fields for frontend display/filtering
            "pfam_accessions": pfam_accessions,
            "pfam_target_names": pfam_target_names,
            "pfam_descriptions": pfam_descriptions,

            # Other annotation metadata
            "features_used": d.get("features_used", []),
            "features_computed": d.get("features_computed", {}),
            "shap": d.get("shap"),
            "warnings": d.get("warnings", []),
            "binary_explanation": d.get("binary_explanation"),

            # Webapp-level metadata
            "novelty_flag": (
                "known" if pfam_hits and carb_prob > 0.8 else
                "borderline" if carb_prob > 0.5 else
                "novel"
            ),
            "mode": mode,
            "kingdom": kingdom,
            "runtime_seconds": round(time.time() - t, 2),
            "annotate_runtime_seconds": d.get("runtime_seconds"),
            "top_similar": [],
        }

    finally:
        # Clean up only FASTA; keep JSON output for debugging
        try:
            os.unlink(fasta_path)
        except Exception:
            pass

# new routine for worker task

def run_predict_job(
    sequence: str,
    mode: str = "fast",
    kingdom: str = "plant",
    seq_id: str = "query",
    include_similar: bool = True,
) -> Dict[str, Any]:
    """
    RQ-compatible worker task for one sequence prediction.

    This function is intentionally top-level and only accepts JSON-serializable
    arguments so it can be enqueued as:

        queue.enqueue(
            "app.pipeline.predict.run_predict_job",
            sequence,
            mode,
            kingdom,
            seq_id,
        )

    It returns a structured payload that can be stored directly in Redis/RQ.
    """

    started_at = time.time()

    try:
        sequence = (sequence or "").strip()
        mode = mode or "fast"
        kingdom = kingdom or "plant"
        seq_id = seq_id or "query"

        if len(sequence) < 10:
            raise ValueError("Sequence too short")

        if mode not in VALID_PREDICT_MODES:
            raise ValueError(f"Invalid mode: {mode}")

        if kingdom not in VALID_KINGDOMS:
            raise ValueError(f"Invalid kingdom: {kingdom}")

        result = predict_sequence(
            sequence=sequence,
            mode=mode,
            kingdom=kingdom,
            seq_id=seq_id,
        )

        if include_similar and result.get("ec_predicted") and result.get("is_carboxylase"):
            try:
                result["top_similar"] = run_blast_similar(
                    sequence=sequence,
                    ec_predicted=result["ec_predicted"],
                    limit=8,
                    manifest_path=os.environ.get(
                        "BLAST_EXP_MANIFEST",
                        "data/blast_ec_dbs_exp/manifest.json",
                    ),
                )
            except Exception as exc:
                log.warning("BLAST nearest-hit lookup failed: %s", exc)
                result["top_similar"] = []
        else:
            result["top_similar"] = []

        return {
            "status": "completed",
            "result": result,
            "error": None,
            "runtime_seconds": round(time.time() - started_at, 2),
        }

    except Exception as exc:
        log.exception("Prediction worker task failed")

        return {
            "status": "failed",
            "result": None,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(limit=5),
            },
            "runtime_seconds": round(time.time() - started_at, 2),
        }

def parse_fasta_text(text: str) -> dict[str, str]:
    """
    Parse FASTA text into {seq_id: sequence}.
    """
    seqs = {}
    sid, buf = None, []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith(">"):
            if sid:
                seqs[sid] = "".join(buf)
            sid = line[1:].split()[0]
            buf = []
        else:
            buf.append(line)

    if sid:
        seqs[sid] = "".join(buf)

    return seqs


def pfam_hits_to_string(pfam_hits) -> str:
    """
    Convert Pfam hit objects/strings to a semicolon-separated TSV field.
    """
    return ";".join(
        (
            h.get("accession")
            or h.get("target_name")
            or ""
        )
        if isinstance(h, dict)
        else str(h)
        for h in (pfam_hits or [])
    )


def run_batch_predict_job(
    fasta_text: str,
    mode: str = "fast",
    kingdom: str = "plant",
) -> Dict[str, Any]:
    """
    RQ-compatible worker task for batch FASTA prediction.

    Returns JSON-serializable batch results plus a TSV string.
    """
    started_at = time.time()

    try:
        mode = mode or "fast"
        kingdom = kingdom or "plant"

        if mode not in {"fast", "standard"}:
            raise ValueError("Batch mode must be fast or standard")

        if kingdom not in VALID_KINGDOMS:
            raise ValueError(f"Invalid kingdom: {kingdom}")

        seqs = parse_fasta_text(fasta_text or "")

        if not seqs:
            raise ValueError("No sequences found in FASTA file")

        results = []

        header = [
            "seq_id",
            "length",
            "is_carboxylase",
            "prob_binary",
            "ec_predicted",
            "ec_confidence",
            "km_predicted_mM",
            "km_predicted_uM",
            "pfam_hits",

            # Frontend expects these when parsing batch TSV
            "nearest_uniprot",
            "nearest_km_exp_uM",
            "nearest_organism",
            "nearest_pident",
            "nearest_tier",

            "novelty_flag",
            "runtime_seconds",
        ]

        tsv_lines = ["\t".join(header)]

        processed = 0

        for seq_id, sequence in seqs.items():
            try:
                r = predict_sequence(
                    sequence=sequence,
                    mode=mode,
                    kingdom=kingdom,
                    seq_id=seq_id,
                )

                # Add BLAST nearest experimental-Km hits for batch results too.
                if r.get("is_carboxylase") and r.get("ec_predicted"):
                    try:
                        r["top_similar"] = run_blast_similar(
                            sequence=sequence,
                            ec_predicted=r["ec_predicted"],
                            limit=8,
                            manifest_path=os.environ.get(
                                "BLAST_EXP_MANIFEST",
                                "data/blast_ec_dbs_exp/manifest.json",
                            ),
                        )
                    except Exception as exc:
                        log.warning("Batch BLAST nearest-hit lookup failed for %s: %s", seq_id, exc)
                        r["top_similar"] = []
                else:
                    r["top_similar"] = []

                top_hit = r["top_similar"][0] if r["top_similar"] else None

                r["nearest_neighbor"] = (
                    {
                        **top_hit,
                        "km_experimental": top_hit.get("km_experimental_uM"),
                    }
                    if top_hit
                    else None
                )

                pfam_str = pfam_hits_to_string(r.get("pfam_hits", []))

                row = {
                    **r,
                    "id": seq_id,
                    "length": r.get("sequence_length", len(sequence)),
                    "co2_prob_v3": r.get("carboxylase_probability", 0),
                    "co2_prob_v5": r.get("carboxylase_probability", 0),
                    "consensus": r.get("is_carboxylase", False),
                    "pfam_string": pfam_str,
                    "error": None,
                }

                results.append(row)

                nn = r.get("nearest_neighbor") or {}

                nearest_uniprot = nn.get("uniprot_id") or ""
                nearest_km_exp_uM = nn.get("km_experimental") or nn.get("km_experimental_uM") or ""
                nearest_organism = nn.get("organism") or ""
                nearest_pident = nn.get("identity_pct") or ""
                nearest_tier = nn.get("tier") or ""

                tsv_lines.append(
                    "\t".join([
                        seq_id,
                        str(r.get("sequence_length", len(sequence))),
                        str(r.get("is_carboxylase", False)),
                        f"{r.get('carboxylase_probability', 0):.4f}",
                        str(r.get("ec_predicted", "")),
                        f"{r.get('ec_confidence', 0):.4f}",
                        str(r.get("km_predicted_mM") or ""),
                        str(r.get("km_predicted_uM") or ""),
                        pfam_str,

                        str(nearest_uniprot),
                        str(nearest_km_exp_uM),
                        str(nearest_organism),
                        str(nearest_pident),
                        str(nearest_tier),

                        str(r.get("novelty_flag", "")),
                        str(r.get("runtime_seconds", "")),
                    ])
                )

            except Exception as exc:
                error_row = {
                    "id": seq_id,
                    "length": len(sequence),
                    "is_carboxylase": False,
                    "consensus": False,
                    "carboxylase_probability": 0,
                    "co2_prob_v3": 0,
                    "co2_prob_v5": 0,
                    "ec_predicted": "",
                    "ec_confidence": 0,
                    "km_predicted_mM": None,
                    "km_predicted_uM": None,
                    "pfam_hits": [],
                    "pfam_string": "",
                    "novelty_flag": "",
                    "runtime_seconds": None,
                    "error": str(exc),
                }

                results.append(error_row)

                tsv_lines.append(
                    "\t".join([
                        seq_id,
                        str(len(sequence)),
                        "ERROR",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",

                        "",  # nearest_uniprot
                        "",  # nearest_km_exp_uM
                        "",  # nearest_organism
                        "",  # nearest_pident
                        "",  # nearest_tier

                        "",
                        str(exc)[:100],
                    ])
                )

            processed += 1

        summary = {
            "total": len(results),
            "consensus_positive": sum(1 for r in results if r.get("consensus")),
            "with_errors": sum(1 for r in results if r.get("error")),
        }

        return {
            "status": "completed",
            "results": results,
            "summary": summary,
            "tsv": "\n".join(tsv_lines) + "\n",
            "n_sequences": len(results),
            "runtime_seconds": round(time.time() - started_at, 2),
            "error": None,
        }

    except Exception as exc:
        log.exception("Batch prediction worker task failed")

        return {
            "status": "failed",
            "results": [],
            "summary": {
                "total": 0,
                "consensus_positive": 0,
                "with_errors": 1,
            },
            "tsv": "",
            "n_sequences": 0,
            "runtime_seconds": round(time.time() - started_at, 2),
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        }