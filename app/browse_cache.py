import os
import sqlite3
import time
import logging
from typing import Optional

log = logging.getLogger(__name__)


class BrowseCache:
    ready: bool = False
    loaded_at: Optional[float] = None
    rows: list[dict] = []
    error: Optional[str] = None


def load_browse_cache():
    """
    Load the flat browse dataset into app memory.

    This does NOT modify the SQLite database.
    It only reads from sequences + predictions once at app startup.
    """
    db_path = os.environ.get("DB_PATH", "data/primary/carbodb.sqlite")

    BrowseCache.ready = False
    BrowseCache.error = None
    BrowseCache.rows = []

    if not os.path.exists(db_path):
        BrowseCache.error = f"Database not found: {db_path}"
        log.warning(BrowseCache.error)
        return

    t0 = time.time()

    query = """
        SELECT
            s.id AS sequence_id,
            s.cdb_id,
            s.uniprot_id,
            s.organism,

            -- known / original EC from sequence table
            s.ec_number AS ec_known,

            -- model-predicted EC from predictions table
            p.ec_pred AS ec_predicted,
            p.ec_prob AS ec_confidence,
            p.co2_prob AS carboxylase_probability,
            p.is_co2_pred AS is_carboxylase_pred,

            s.label,
            s.length,
            s.reviewed,
            s.source,

            -- predicted Km from model, stored in mM
            p.km_pred_mM,
            p.km_pred_log10,
            p.km_pred_mM * 1000.0 AS km_predicted_uM,

            -- experimental Km from best sequence field or BRENDA evidence
            COALESCE(kexp.km_experimental_mM, s.km_best_mM) AS km_experimental_mM,
            COALESCE(kexp.km_experimental_mM, s.km_best_mM) * 1000.0 AS km_experimental_uM,
            kexp.km_exp_substrate,
            kexp.km_exp_source,

            -- BLAST summary fields available in current schema
            fb.blast_best_pident,
            fb.blast_best_evalue,
            fb.blast_best_ec,
            fb.blast_has_hit

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

        LEFT JOIN features_blast fb
            ON fb.sequence_id = s.id

        WHERE s.label = 1
    """

    try:
        conn = sqlite3.connect(db_path, timeout=60)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(query).fetchall()
        conn.close()

        rows = [dict(r) for r in rows]

        for r in rows:
            r["reviewed"] = bool(r.get("reviewed"))

            # Frontend boolean: use prediction if available, otherwise fall back to label.
            if r.get("is_carboxylase_pred") is not None:
                r["is_carboxylase"] = bool(r.get("is_carboxylase_pred"))
            else:
                r["is_carboxylase"] = bool(r.get("label") == 1)

            # Backward-compatible aliases for the old static frontend.
            r["ec_number"] = r.get("ec_predicted") or r.get("ec_known")
            r["km_uM"] = r.get("km_predicted_uM")

        BrowseCache.rows = sorted(
            rows,
            key=lambda r: (
                r.get("km_pred_mM") is None,
                r.get("km_pred_mM") if r.get("km_pred_mM") is not None else float("inf"),
            ),
        )
        BrowseCache.loaded_at = time.time()
        BrowseCache.ready = True

        log.info(
            "Browse cache loaded: %s rows in %.1fs",
            len(BrowseCache.rows),
            time.time() - t0,
        )

    except Exception as e:
        BrowseCache.error = str(e)
        BrowseCache.ready = False
        log.exception("Failed to load browse cache")