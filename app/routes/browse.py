from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import sqlite3, os

from ..browse_cache import BrowseCache, load_browse_cache

router = APIRouter(tags=["browse"])

# @router.get("/browse")
# def browse(
#     organism: Optional[str] = Query(None),
#     ec: Optional[str] = Query(None),
#     kingdom: Optional[str] = Query(None),
#     km_min: Optional[float] = Query(None),
#     km_max: Optional[float] = Query(None),
#     reviewed: Optional[bool] = Query(None),
#     limit: int = Query(50, le=500),
#     offset: int = Query(0)
# ):
#     db_path = os.environ.get("DB_PATH", "data/carbodb.sqlite")
#     if not os.path.exists(db_path):
#         return {"total": 0, "results": [], "error": "Database not found"}

#     conn = sqlite3.connect(db_path, timeout=30)
#     conn.row_factory = sqlite3.Row

#     where = ["s.label=1", "p.km_pred_mM IS NOT NULL"]
#     params = []

#     if organism:
#         where.append("s.organism LIKE ?")
#         params.append(f"%{organism}%")
#     if ec:
#         where.append("s.ec_number LIKE ?")
#         params.append(f"{ec}%")
#     if kingdom:
#         where.append("s.kingdom=?")
#         params.append(kingdom)
#     if km_min is not None:
#         where.append("p.km_pred_mM*1000 >= ?")
#         params.append(km_min)
#     if km_max is not None:
#         where.append("p.km_pred_mM*1000 <= ?")
#         params.append(km_max)
#     if reviewed is not None:
#         where.append("s.reviewed=?")
#         params.append(1 if reviewed else 0)

#     where_str = " AND ".join(where)

#     try:
#         count_row = conn.execute(
#             "SELECT COUNT(*) FROM sequences s "
#             "JOIN predictions p ON p.sequence_id=s.id "
#             "WHERE " + where_str,
#             params).fetchone()
#         total = count_row[0]

#         rows = conn.execute(
#             "SELECT s.uniprot_id, s.organism, s.ec_number, s.length, "
#             "s.reviewed, s.source, p.km_pred_mM*1000 as km_uM "
#             "FROM sequences s "
#             "JOIN predictions p ON p.sequence_id=s.id "
#             "WHERE " + where_str + " "
#             "ORDER BY p.km_pred_mM "
#             "LIMIT ? OFFSET ?",
#             params + [limit, offset]).fetchall()

#         conn.close()
#         return {"total": total, "limit": limit, "offset": offset,
#                 "results": [dict(r) for r in rows]}
#     except Exception as e:
#         conn.close()
#         return {"total": 0, "results": [], "error": str(e)}


@router.get("/browse")
def browse(
    q: Optional[str] = Query(None),
    organism: Optional[str] = Query(None),
    ec: Optional[str] = Query(None),
    kingdom: Optional[str] = Query(None),
    km_min: Optional[float] = Query(None),
    km_max: Optional[float] = Query(None),
    reviewed: Optional[bool] = Query(None),
    has_experimental_km: Optional[bool] = Query(None),
    is_carboxylase: Optional[bool] = Query(None),
    sort: Optional[str] = Query("default"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    if not BrowseCache.ready:
        return {
            "total": 0,
            "limit": limit,
            "offset": offset,
            "results": [],
            "error": BrowseCache.error or "Browse cache not ready",
        }

    q_l = q.lower() if q else None
    organism_q = organism.lower() if organism else None
    ec_q = ec if ec else None

    filtered = []

    for row in BrowseCache.rows:
        if q_l:
            haystack = " ".join([
                str(row.get("uniprot_id") or ""),
                str(row.get("cdb_id") or ""),
                str(row.get("organism") or ""),
                str(row.get("ec_known") or ""),
                str(row.get("ec_predicted") or ""),
            ]).lower()

            if q_l not in haystack:
                continue

        if organism_q and organism_q not in (row.get("organism") or "").lower():
            continue

        if ec_q:
            ec_known = row.get("ec_known") or ""
            ec_pred = row.get("ec_predicted") or ""
            if not (ec_known.startswith(ec_q) or ec_pred.startswith(ec_q)):
                continue

        if km_min is not None:
            km = row.get("km_predicted_uM")
            if km is None or km < km_min:
                continue

        if km_max is not None:
            km = row.get("km_predicted_uM")
            if km is None or km > km_max:
                continue

        if reviewed is not None and bool(row.get("reviewed")) != reviewed:
            continue

        if has_experimental_km and row.get("km_experimental_uM") is None:
            continue

        if is_carboxylase is not None and bool(row.get("is_carboxylase")) != is_carboxylase:
            continue

        filtered.append(row)

        if sort == "km_asc":
            filtered.sort(
                key=lambda r: (
                    r.get("km_predicted_uM") is None,
                    r.get("km_predicted_uM") if r.get("km_predicted_uM") is not None else float("inf"),
                )
            )
        elif sort == "km_desc":
            filtered.sort(
                key=lambda r: (
                    r.get("km_predicted_uM") is None,
                    -(r.get("km_predicted_uM") or 0),
                )
            )
        elif sort == "length_asc":
            filtered.sort(key=lambda r: r.get("length") or 0)
        elif sort == "length_desc":
            filtered.sort(key=lambda r: -(r.get("length") or 0))
        elif sort == "uniprot":
            filtered.sort(key=lambda r: r.get("uniprot_id") or "")
            
    

    total = len(filtered)

    page = filtered[offset:offset + limit]

    results = [
        {
            "sequence_id": r.get("sequence_id"),
            "cdb_id": r.get("cdb_id"),
            "uniprot_id": r.get("uniprot_id"),
            "organism": r.get("organism"),

            "ec_number": r.get("ec_number"),
            "ec_known": r.get("ec_known"),
            "ec_predicted": r.get("ec_predicted"),
            "ec_confidence": r.get("ec_confidence"),

            "length": r.get("length"),
            "reviewed": r.get("reviewed"),
            "source": r.get("source"),
            "is_carboxylase": r.get("is_carboxylase"),
            "carboxylase_probability": r.get("carboxylase_probability"),

            "km_predicted_uM": r.get("km_predicted_uM"),
            "km_predicted_log10": r.get("km_pred_log10"),
            "km_experimental_uM": r.get("km_experimental_uM"),
            "km_exp_substrate": r.get("km_exp_substrate"),
            "km_exp_source": r.get("km_exp_source"),

            "blast_best_pident": r.get("blast_best_pident"),
            "blast_best_evalue": r.get("blast_best_evalue"),
            "blast_best_ec": r.get("blast_best_ec"),
            "blast_has_hit": r.get("blast_has_hit"),

            # old static UI alias
            "km_uM": r.get("km_uM"),
        }
        for r in page
    ]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results,
        "cache": {
            "ready": BrowseCache.ready,
            "rows": len(BrowseCache.rows),
            "loaded_at": BrowseCache.loaded_at,
        },
    }


@router.get("/db/seq/{uniprot_id}")
def db_sequence_detail(uniprot_id: str):
    db_path = os.environ.get("DB_PATH", "data/primary/carbodb.sqlite")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
            SELECT
                s.id AS sequence_id,
                s.cdb_id,
                s.uniprot_id,
                s.organism,
                s.ec_number AS ec_known,
                s.label,
                s.source,
                s.sequence,
                s.length,
                s.reviewed,
                s.km_best_mM,

                p.is_co2_pred,
                p.co2_prob,
                p.ec_pred AS ec_predicted,
                p.ec_prob AS ec_confidence,
                p.km_pred_mM,
                p.km_pred_log10,
                p.km_pred_mM * 1000.0 AS km_predicted_uM,

                COALESCE(kexp.km_experimental_mM, s.km_best_mM) AS km_experimental_mM,
                COALESCE(kexp.km_experimental_mM, s.km_best_mM) * 1000.0 AS km_experimental_uM,
                kexp.km_exp_substrate,
                kexp.km_exp_source

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

            WHERE s.uniprot_id = ?
            LIMIT 1
        """, (uniprot_id,)).fetchone()

        if row is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Sequence not found")

        result = dict(row)

        result["id"] = result.get("uniprot_id")
        result["sequence_length"] = result.get("length")
        result["reviewed"] = bool(result.get("reviewed"))

        if result.get("is_co2_pred") is not None:
            result["is_carboxylase"] = bool(result.get("is_co2_pred"))
        else:
            result["is_carboxylase"] = bool(result.get("label") == 1)

        result["carboxylase_probability"] = result.get("co2_prob")
        result["km_predicted_log10"] = result.get("km_pred_log10")
        result["mode"] = "db_lookup"
        result["kingdom"] = None
        result["features_used"] = []
        result["runtime_seconds"] = 0

        ec_for_neighbors = result.get("ec_predicted") or result.get("ec_known")

        result["top_similar"] = get_same_ec_experimental_km_neighbors(
            conn=conn,
            ec=ec_for_neighbors,
            exclude_uniprot=result.get("uniprot_id"),
            km_predicted_uM=result.get("km_predicted_uM"),
            limit=8,
        )

        conn.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def get_same_ec_experimental_km_neighbors(
    conn: sqlite3.Connection,
    ec: Optional[str],
    exclude_uniprot: Optional[str],
    km_predicted_uM: Optional[float],
    limit: int = 8,
) -> list:
    if not ec:
        return []

    rows = conn.execute("""
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

        WHERE s.uniprot_id != ?
          AND s.ec_number = ?
          AND COALESCE(kexp.km_experimental_mM, s.km_best_mM) IS NOT NULL

        LIMIT 200
    """, (exclude_uniprot or "", ec)).fetchall()

    import math

    neighbors = []
    for r in rows:
        d = dict(r)
        exp_uM = d.get("km_experimental_uM")

        if km_predicted_uM and exp_uM and km_predicted_uM > 0 and exp_uM > 0:
            d["_distance"] = abs(math.log10(km_predicted_uM) - math.log10(exp_uM))
        else:
            d["_distance"] = 999.0

        # reviewed first if distance is equal
        d["_reviewed_sort"] = 0 if d.get("reviewed") else 1
        neighbors.append(d)

    neighbors.sort(key=lambda d: (d["_distance"], d["_reviewed_sort"]))

    out = []
    for i, d in enumerate(neighbors[:limit], start=1):
        out.append({
            "rank": i,
            "uniprot_id": d.get("uniprot_id"),
            "organism": d.get("organism"),
            "ec_number": d.get("ec_number"),
            "length": d.get("length"),
            "reviewed": bool(d.get("reviewed")),

            "km_experimental_uM": d.get("km_experimental_uM"),
            "km_exp_substrate": d.get("km_exp_substrate"),
            "km_exp_source": d.get("km_exp_source") or "brenda",

            # No true BLAST hit-list in current schema, so do not fake these.
            "identity_pct": None,
            "evalue": None,
            "align_length": None,

            "tier": "same_ec",
            "tier_label": "same EC experimental Km",
        })

    return out


@router.post("/browse/cache/refresh")
def refresh_browse_cache():
    load_browse_cache()

    return {
        "ready": BrowseCache.ready,
        "rows": len(BrowseCache.rows),
        "loaded_at": BrowseCache.loaded_at,
        "error": BrowseCache.error,
    }

@router.get("/stats")
def stats():
    db_path = os.environ.get("DB_PATH", "data/carbodb.sqlite")
    if not os.path.exists(db_path):
        return {"error": "Database not found"}
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        total = conn.execute(
            "SELECT COUNT(*) FROM sequences WHERE label=1").fetchone()[0]
        reviewed = conn.execute(
            "SELECT COUNT(*) FROM sequences WHERE label=1 AND reviewed=1").fetchone()[0]
        ec_dist = conn.execute(
            "SELECT ec_number, COUNT(*) as n FROM sequences "
            "WHERE label=1 GROUP BY ec_number ORDER BY n DESC LIMIT 10").fetchall()
        conn.close()
        return {"total_sequences": total, "reviewed": reviewed,
                "ec_distribution": {r[0]: r[1] for r in ec_dist}}
    except Exception as e:
        return {"error": str(e)}
