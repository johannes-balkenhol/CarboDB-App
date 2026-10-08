####################################################
# Helper script for database Km operations
####################################################

import os
import sqlite3
import math
from typing import Optional, Any


DB_PATH_DEFAULT = "data/primary/carbodb.sqlite"

KM_EVIDENCE_SUBQUERY_SQL = """
    SELECT
        ke.sequence_id,
        ke.km_value_mM AS km_experimental_mM,
        ke.substrate AS km_exp_substrate,
        ke.source AS km_exp_source
    FROM km_evidence ke
    JOIN (
        SELECT
            sequence_id,
            MIN(km_value_mM) AS km_experimental_mM
        FROM km_evidence
        WHERE (evidence_tier = 1 OR LOWER(source) = 'brenda')
          AND km_value_mM IS NOT NULL
        GROUP BY sequence_id
    ) best
      ON best.sequence_id = ke.sequence_id
     AND best.km_experimental_mM = ke.km_value_mM
    WHERE (ke.evidence_tier = 1 OR LOWER(ke.source) = 'brenda')
      AND ke.km_value_mM IS NOT NULL
    GROUP BY ke.sequence_id
"""


# KM_SELECT_SQL = """
#     p.km_pred_mM,
#     p.km_pred_log10,
#     p.km_pred_mM * 1000.0 AS km_predicted_uM,

#     COALESCE(kexp.km_experimental_mM, s.km_best_mM) AS km_experimental_mM,
#     COALESCE(kexp.km_experimental_mM, s.km_best_mM) * 1000.0 AS km_experimental_uM,
#     kexp.km_exp_substrate,
#     kexp.km_exp_source
# """

KM_SELECT_SQL = """
    p.km_pred_mM,
    p.km_pred_log10,
    p.km_pred_mM * 1000.0 AS km_predicted_uM,

    kexp.km_experimental_mM AS km_experimental_mM,
    kexp.km_experimental_mM * 1000.0 AS km_experimental_uM,
    kexp.km_exp_substrate,
    kexp.km_exp_source,

    s.km_best_mM AS km_best_mM,
    s.km_best_mM * 1000.0 AS km_best_uM,

    CASE
        WHEN kexp.km_experimental_mM IS NOT NULL THEN 1
        ELSE 0
    END AS has_direct_experimental_km,

    CASE
        WHEN kexp.km_experimental_mM IS NOT NULL THEN 'experimental_table'
        WHEN s.km_best_mM IS NOT NULL THEN 'sequence_best_km'
        ELSE NULL
    END AS km_source_type
"""


KM_JOIN_SQL = f"""
    LEFT JOIN predictions p
        ON p.sequence_id = s.id

    LEFT JOIN (
{KM_EVIDENCE_SUBQUERY_SQL}
    ) kexp
        ON kexp.sequence_id = s.id
"""


def db_path() -> str:
    return os.environ.get("DB_PATH", DB_PATH_DEFAULT)

def normalise_sequence_km_row(row: dict[str, Any]) -> dict[str, Any]:
    row["reviewed"] = bool(row.get("reviewed"))

    if row.get("is_co2_pred") is not None:
        row["is_carboxylase"] = bool(row.get("is_co2_pred"))
    elif row.get("is_carboxylase_pred") is not None:
        row["is_carboxylase"] = bool(row.get("is_carboxylase_pred"))
    else:
        row["is_carboxylase"] = bool(row.get("label") == 1)

    row["ec_number"] = row.get("ec_predicted") or row.get("ec_known")
    row["km_uM"] = row.get("km_predicted_uM")
    row["km_predicted_log10"] = row.get("km_pred_log10")
    row["carboxylase_probability"] = row.get(
        "co2_prob",
        row.get("carboxylase_probability"),
    )
    row["has_direct_experimental_km"] = bool(row.get("has_direct_experimental_km"))

    if row.get("km_experimental_uM") is not None:
        row["km_display_uM"] = row.get("km_experimental_uM")
        row["km_display_source_type"] = "experimental_table"
    elif row.get("km_best_uM") is not None:
        row["km_display_uM"] = row.get("km_best_uM")
        row["km_display_source_type"] = "sequence_best_km"
    else:
        row["km_display_uM"] = None
        row["km_display_source_type"] = None

        row["has_direct_experimental_km"] = bool(row.get("has_direct_experimental_km"))

    return row


def fetch_sequence_km_detail(
    conn: sqlite3.Connection,
    uniprot_id: str,
) -> Optional[dict[str, Any]]:
    row = conn.execute(
        f"""
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
            {KM_SELECT_SQL}

        FROM sequences s
        {KM_JOIN_SQL}
        WHERE s.uniprot_id = ?
        LIMIT 1
        """,
        (uniprot_id,),
    ).fetchone()

    if row is None:
        return None

    result = normalise_sequence_km_row(dict(row))
    result["id"] = result.get("uniprot_id")
    result["sequence_length"] = result.get("length")
    result["mode"] = "db_lookup"
    result["kingdom"] = None
    result["features_used"] = []
    result["runtime_seconds"] = 0

    return result

def get_same_ec_experimental_km_neighbors(
    conn: sqlite3.Connection,
    ec: Optional[str],
    exclude_uniprot: Optional[str] = None,
    km_predicted_uM: Optional[float] = None,
    limit: int = 8,
    include_query_prediction: bool = False,
) -> list[dict[str, Any]]:
    if not ec:
        return []

    params = []
    exclude_sql = ""

    if exclude_uniprot:
        exclude_sql = "AND s.uniprot_id != ?"
        params.append(exclude_uniprot)

    params.append(ec)

    rows = conn.execute(
        f"""
        SELECT
            s.uniprot_id,
            s.organism,
            s.ec_number,
            s.length,
            s.reviewed,
            {KM_SELECT_SQL}

        FROM sequences s
        {KM_JOIN_SQL}

        WHERE s.label = 1
          {exclude_sql}
          AND s.ec_number = ?
          AND kexp.km_experimental_mM IS NOT NULL

        LIMIT 300
        """,
        tuple(params),
    ).fetchall()

    neighbors = []

    for r in rows:
        d = dict(r)
        exp_uM = d.get("km_experimental_uM")

        if km_predicted_uM and exp_uM and km_predicted_uM > 0 and exp_uM > 0:
            d["_distance"] = abs(math.log10(km_predicted_uM) - math.log10(exp_uM))
        else:
            d["_distance"] = 999.0

        d["_reviewed_sort"] = 0 if d.get("reviewed") else 1
        neighbors.append(d)

    neighbors.sort(key=lambda d: (d["_distance"], d["_reviewed_sort"]))

    out = []

    for i, d in enumerate(neighbors[:limit], start=1):
        item = {
            "rank": i,
            "uniprot_id": d.get("uniprot_id"),
            "organism": d.get("organism"),
            "ec_number": d.get("ec_number"),
            "length": d.get("length"),
            "reviewed": bool(d.get("reviewed")),

            "km_experimental_uM": d.get("km_experimental_uM"),
            "km_exp_substrate": d.get("km_exp_substrate"),
            "km_exp_source": d.get("km_exp_source"),

            "has_direct_experimental_km": True,
            "km_source_type": "experimental_table",

            "identity_pct": None,
            "evalue": None,
            "align_length": None,

            "tier": "same_ec_experimental_km",
            "tier_label": "same EC experimental Km",
        }

        if include_query_prediction:
            item["km_predicted_uM"] = (
                round(km_predicted_uM, 1)
                if km_predicted_uM is not None
                else None
            )

            if item["km_experimental_uM"] is not None:
                item["km_experimental_uM"] = round(item["km_experimental_uM"], 1)

        out.append(item)

    return out