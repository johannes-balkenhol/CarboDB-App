import os
import sys
import time
import logging
import subprocess
import json
import tempfile
from pathlib import Path

import numpy as np

from ..startup import ModelStore, EC_NAMES, KM_EC_CLASSES

log = logging.getLogger(__name__)

# Define project tmp directory
ROOT = Path(__file__).resolve().parents[2]  # Navigate to project root
TMP_DIR = ROOT / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

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
            "warnings": d.get("warnings", []),

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