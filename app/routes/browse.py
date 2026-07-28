from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import sqlite3, os
import json

from ..browse_cache import BrowseCache, load_browse_cache
from ..db_km import fetch_sequence_km_detail, get_same_ec_experimental_km_neighbors 
from app.pipeline.shap_summary import build_shap_payload
from app.pipeline.db_binary_shap import (
    build_db_binary_explanation,
)

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

    if sort in ("km_asc", "km_pred_asc"):
        filtered.sort(
            key=lambda r: (
                r.get("km_predicted_uM") is None,
                r.get("km_predicted_uM")
                if r.get("km_predicted_uM") is not None
                else float("inf"),
            )
        )

    elif sort in ("km_desc", "km_pred_desc"):
        filtered.sort(
            key=lambda r: (
                r.get("km_predicted_uM") is None,
                -(r.get("km_predicted_uM") or 0),
            )
        )

    elif sort == "km_exp_asc":
        filtered.sort(
            key=lambda r: (
                r.get("km_experimental_uM") is None,
                r.get("km_experimental_uM")
                if r.get("km_experimental_uM") is not None
                else float("inf"),
            )
        )

    elif sort == "km_exp_desc":
        filtered.sort(
            key=lambda r: (
                r.get("km_experimental_uM") is None,
                -(r.get("km_experimental_uM") or 0),
            )
        )
    elif sort == "length_asc":
        filtered.sort(key=lambda r: r.get("length") or 0)
    elif sort == "length_desc":
        filtered.sort(key=lambda r: -(r.get("length") or 0))
    elif sort == "uniprot":
        filtered.sort(key=lambda r: r.get("uniprot_id") or "")
    
    elif sort == "organism_asc":
        filtered.sort(
            key=lambda r: (
                r.get("organism") is None or not str(r.get("organism")).strip(),
                str(r.get("organism") or "").lower(),
            )
        )

    elif sort == "organism_desc":
        with_organism = [
            r for r in filtered
            if r.get("organism") and str(r.get("organism")).strip()
        ]
        without_organism = [
            r for r in filtered
            if not r.get("organism") or not str(r.get("organism")).strip()
        ]

        with_organism.sort(
            key=lambda r: str(r.get("organism")).lower(),
            reverse=True,
        )

        filtered = with_organism + without_organism
    

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

        result = fetch_sequence_km_detail(conn, uniprot_id)

        if result is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Sequence not found")

        ec_for_neighbors = result.get("ec_predicted") or result.get("ec_known")

        experimental_km_neighbors = get_same_ec_experimental_km_neighbors(
            conn=conn,
            ec=ec_for_neighbors,
            exclude_uniprot=result.get("uniprot_id"),
            km_predicted_uM=result.get("km_predicted_uM"),
            limit=8,
            include_query_prediction=True,
        )

        result["experimental_km_neighbors"] = experimental_km_neighbors

        # temporary frontend compatibility
        result["top_similar"] = experimental_km_neighbors

        # explicit placeholder until real BLAST is implemented
        result["nearest_km_blast_hits"] = []
        result["nearest_blast_hit"] = None

        # added shap code to fetch SHAP payload for the sequence

        # Ensure DB detail response has frontend-compatible Pfam hits.
        # ResultDetail.vue expects result["pfam_hits"] with accession fields.
        try:
            seq_id = result.get("sequence_id") or result.get("id")

            dom_row = conn.execute(
                """
                SELECT pfam_hits_json, pfam_n_hits
                FROM features_domains
                WHERE uniprot_id = ? OR sequence_id = ?
                LIMIT 1
                """,
                (uniprot_id, seq_id),
            ).fetchone()

            # Composition / physicochemical features for DB detail view.
            # Prediction results already expose these as result["features_computed"];
            # DB detail must use the same key so ResultDetail.vue can render the shared panel.
            try:
                seq_id = result.get("sequence_id") or result.get("id")

                comp_row = conn.execute(
                    """
                    SELECT *
                    FROM features_composition
                    WHERE uniprot_id = ? OR sequence_id = ?
                    LIMIT 1
                    """,
                    (uniprot_id, seq_id),
                ).fetchone()

                if comp_row:
                    comp = dict(comp_row)

                    # Keep only real feature values for the frontend.
                    for meta_key in ("id", "sequence_id", "uniprot_id"):
                        comp.pop(meta_key, None)

                    result["features_computed"] = {
                        k: v for k, v in comp.items()
                        if v is not None
                    }

                    result.setdefault("features_used", [])
                    if "composition" not in result["features_used"]:
                        result["features_used"].append("composition")

            except Exception as e:
                result.setdefault("features_computed", {})
                result.setdefault("warnings", []).append(
                    f"Composition/physicochemical features unavailable: {e}"
                )

            pfam_accessions = []
            if dom_row:
                # Works whether row is sqlite Row or dict-like
                pfam_json = dom_row["pfam_hits_json"] if "pfam_hits_json" in dom_row.keys() else dom_row[0]

                if pfam_json:
                    pfam_accessions = json.loads(pfam_json)

            result["pfam_hits"] = [
                {
                    "accession": acc,
                    "name": acc,
                    "description": None,
                }
                for acc in pfam_accessions
            ]

            result["pfam_accessions"] = pfam_accessions

        except Exception as e:
            result["pfam_hits"] = []
            result["pfam_accessions"] = []
            result.setdefault("warnings", []).append(f"Pfam annotations unavailable: {e}")
        
        ec_for_shap = (
            result.get("ec_predicted")
            or result.get("ec_known")
            or result.get("ec")
            or result.get("ec_number")
        )

        is_carb = bool(result.get("is_carboxylase")) or result.get("label") == 1

        result["shap"] = build_shap_payload(ec_for_shap) if is_carb and ec_for_shap else None

        try:
            sequence_id = result.get("sequence_id")

            result["binary_explanation"] = build_db_binary_explanation(
                conn=conn,
                sequence_id=sequence_id,
                stored_probability=result.get("carboxylase_probability"),
            )

        except Exception as e:
            result["binary_explanation"] = None
            result.setdefault("warnings", []).append(
                f"Local binary explanation unavailable: {e}"
            )

        conn.close()
        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    if not BrowseCache.ready:
        return {
            "total_sequences": 0,
            "reviewed": 0,
            "ec_distribution": {},
            "all_sequences": 0,
            "predicted_carboxylases": 0,
            "with_experimental_km": 0,
            "with_experimental_km_cached": 0,
            "ec_classes": 0,
            "ec_classes_cached": 0,
            "swissprot_curated": 0,
            "cache_rows": 0,
            "cache": {
                "ready": BrowseCache.ready,
                "rows": len(BrowseCache.rows),
                "loaded_at": BrowseCache.loaded_at,
                "error": BrowseCache.error or "Browse cache not ready",
            },
        }

    payload = dict(BrowseCache.stats)

    payload["cache"] = {
        "ready": BrowseCache.ready,
        "rows": len(BrowseCache.rows),
        "loaded_at": BrowseCache.loaded_at,
        "error": BrowseCache.error,
    }

    return payload