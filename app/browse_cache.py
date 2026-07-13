import os
import sqlite3
import time
import logging
from typing import Optional


from .db_km import KM_SELECT_SQL, KM_JOIN_SQL, normalise_sequence_km_row

log = logging.getLogger(__name__)


class BrowseCache:
    ready: bool = False
    loaded_at: Optional[float] = None
    rows: list[dict] = []
    stats: dict = {}
    error: Optional[str] = None

def build_browse_stats(conn: sqlite3.Connection, rows: list[dict]) -> dict:
    """
    Build stats once during browse-cache loading.

    rows are the cached browse rows, currently restricted to s.label = 1.
    Full-database counts are queried directly once here.
    """

    # Full database stats
    all_sequences = conn.execute(
        "SELECT COUNT(*) FROM sequences"
    ).fetchone()[0]

    with_experimental_km_all = conn.execute(
        """
        SELECT COUNT(DISTINCT s.id)
        FROM sequences s
        JOIN km_evidence ke ON ke.sequence_id = s.id
        WHERE ke.km_value_mM IS NOT NULL
          AND (ke.evidence_tier = 1 OR LOWER(ke.source) = 'brenda')
        """
    ).fetchone()[0]

    ec_classes_all = conn.execute(
        """
        SELECT COUNT(DISTINCT ec_number)
        FROM sequences
        WHERE ec_number IS NOT NULL
          AND ec_number != ''
        """
    ).fetchone()[0]

    swissprot_curated_all = conn.execute(
        """
        SELECT COUNT(*)
        FROM sequences
        WHERE reviewed = 1
        """
    ).fetchone()[0]

    # Browse/cache-specific stats: currently label=1 rows only
    cached_carboxylases = len(rows)

    predicted_carboxylases = sum(
        1 for r in rows
        if bool(r.get("is_carboxylase"))
    )

    cached_with_experimental_km = sum(
        1 for r in rows
        if r.get("km_experimental_uM") is not None
    )

    cached_reviewed = sum(
        1 for r in rows
        if bool(r.get("reviewed"))
    )

    ec_distribution = {}
    ec_values = []

    for r in rows:
        ec = r.get("ec_number") or r.get("ec_known") or r.get("ec_predicted")
        if not ec:
            continue

        ec_values.append(ec)
        ec_distribution[ec] = ec_distribution.get(ec, 0) + 1

    ec_distribution = dict(
        sorted(
            ec_distribution.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]
    )

    return {
        # Old compatibility fields
        # In the old route, total_sequences meant label=1, not all DB rows.
        "total_sequences": cached_carboxylases,
        "reviewed": cached_reviewed,
        "ec_distribution": ec_distribution,

        # New stat-card fields
        "all_sequences": all_sequences,
        "predicted_carboxylases": predicted_carboxylases,
        "with_experimental_km": with_experimental_km_all,
        "with_experimental_km_cached": cached_with_experimental_km,
        "ec_classes": ec_classes_all,
        "ec_classes_cached": len(set(ec_values)),
        "swissprot_curated": swissprot_curated_all,

        "cache_rows": len(rows),
    }


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
    BrowseCache.stats = {}

    if not os.path.exists(db_path):
        BrowseCache.error = f"Database not found: {db_path}"
        log.warning(BrowseCache.error)
        return

    t0 = time.time()

    query = f"""
        SELECT
            s.id AS sequence_id,
            s.cdb_id,
            s.uniprot_id,
            s.organism,

            s.ec_number AS ec_known,

            p.ec_pred AS ec_predicted,
            p.ec_prob AS ec_confidence,
            p.co2_prob AS carboxylase_probability,
            p.is_co2_pred AS is_carboxylase_pred,

            s.label,
            s.length,
            s.reviewed,
            s.source,

            {KM_SELECT_SQL},

            fb.blast_best_pident,
            fb.blast_best_evalue,
            fb.blast_best_ec,
            fb.blast_has_hit

        FROM sequences s
        {KM_JOIN_SQL}

        LEFT JOIN features_blast fb
            ON fb.sequence_id = s.id

        WHERE s.label = 1
    """

    try:
        conn = sqlite3.connect(db_path, timeout=60)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(query).fetchall()
        rows = [dict(r) for r in rows]

        for r in rows:
            normalise_sequence_km_row(r)

        BrowseCache.stats = build_browse_stats(conn, rows)

        conn.close()

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