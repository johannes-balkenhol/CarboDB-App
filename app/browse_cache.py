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
            s.uniprot_id,
            s.organism,
            s.ec_number,
            s.length,
            s.reviewed,
            s.source,
            p.km_pred_mM,
            p.km_pred_mM * 1000.0 AS km_uM
        FROM sequences s
        JOIN predictions p ON p.sequence_id = s.id
        WHERE s.label = 1
          AND p.km_pred_mM IS NOT NULL
    """

    try:
        conn = sqlite3.connect(db_path, timeout=60)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(query).fetchall()
        conn.close()

        BrowseCache.rows = sorted(
            [dict(r) for r in rows],
            key=lambda r: r["km_pred_mM"] if r["km_pred_mM"] is not None else float("inf"),
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