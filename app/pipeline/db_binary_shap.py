import sqlite3

import numpy as np
import xgboost as xgb

from ..startup import ModelStore


INTERPRO_FEATURES = {
    "n_panther",
    "n_gene3d",
    "n_tigrfam",
    "n_prosite_prof",
    "n_prosite_pat",
}


def binary_feature_group(feature_name: str) -> str:
    if feature_name.startswith("pfam_"):
        return "Pfam domains"

    if feature_name.startswith("esm2_"):
        return "ESM-2 embedding"

    if feature_name.startswith("dp_"):
        return "Dipeptide composition"

    if feature_name.startswith(("aac_", "pse_")):
        return "Amino acid composition"

    if feature_name.startswith("phys_"):
        return "Physicochemical properties"

    if feature_name.startswith("motif_"):
        return "Sequence motifs"

    if feature_name.startswith("inv_"):
        return "Catalytic core motifs"

    if feature_name in INTERPRO_FEATURES:
        return "InterPro/domain evidence"

    return "Other"


def _fetch_feature_row(
    conn: sqlite3.Connection,
    table: str,
    sequence_id: int,
) -> sqlite3.Row:
    row = conn.execute(
        f"""
        SELECT *
        FROM {table}
        WHERE sequence_id = ?
        LIMIT 1
        """,
        (sequence_id,),
    ).fetchone()

    if row is None:
        raise ValueError(
            f"No {table} row found for sequence_id={sequence_id}"
        )

    return row


def build_db_binary_vector(
    conn: sqlite3.Connection,
    sequence_id: int,
) -> tuple[np.ndarray, list[str], dict[str, float]]:
    feature_names = ModelStore.feature_names

    if not feature_names:
        raise ValueError("Binary feature names are not loaded")

    required = set(feature_names)
    feature_values: dict[str, float] = {}

    for table in (
        "features_composition",
        "features_domains",
        "features_interpro",
    ):
        row = _fetch_feature_row(
            conn,
            table,
            sequence_id,
        )

        for key in row.keys():
            if key not in required:
                continue

            value = row[key]

            if value is None:
                feature_values[key] = 0.0
            else:
                feature_values[key] = float(value)

    esm_row = _fetch_feature_row(
        conn,
        "features_esm2",
        sequence_id,
    )

    embedding_blob = esm_row["embedding_blob"]

    if embedding_blob is None:
        raise ValueError("ESM-2 embedding is NULL")

    embedding = np.frombuffer(
        embedding_blob,
        dtype=np.float32,
    )

    if embedding.size != 1280:
        raise ValueError(
            f"Expected 1280 ESM-2 values, found {embedding.size}"
        )

    for index, value in enumerate(embedding):
        feature_values[f"esm2_{index}"] = float(value)

    missing = [
        name
        for name in feature_names
        if name not in feature_values
    ]

    if missing:
        raise ValueError(
            f"Missing {len(missing)} binary features: {missing[:10]}"
        )

    vector = np.asarray(
        [feature_values[name] for name in feature_names],
        dtype=np.float32,
    )

    if vector.shape != (1793,):
        raise ValueError(
            f"Expected binary vector shape (1793,), found {vector.shape}"
        )

    if not np.isfinite(vector).all():
        raise ValueError("Binary feature vector contains non-finite values")

    return vector, feature_names, feature_values


def _predict_binary_contributions(
    model,
    vector: np.ndarray,
    feature_names: list[str],
) -> dict:
    dmatrix = xgb.DMatrix(
        vector.reshape(1, -1),
        feature_names=feature_names,
    )

    contributions = model.predict(
        dmatrix,
        pred_contribs=True,
    )[0]

    return {
        "bias": float(contributions[-1]),
        "features": [
            {
                "feature": name,
                "shap_value": float(value),
                "abs_shap": abs(float(value)),
            }
            for name, value in zip(
                feature_names,
                contributions[:-1],
            )
        ],
    }


def _group_binary_contributions(
    explanation: dict,
) -> list[dict]:
    grouped = {}

    for row in explanation["features"]:
        group_name = binary_feature_group(row["feature"])

        group = grouped.setdefault(
            group_name,
            {
                "group": group_name,
                "signed_shap": 0.0,
                "abs_shap": 0.0,
                "positive_shap": 0.0,
                "negative_shap": 0.0,
                "feature_count": 0,
            },
        )

        shap_value = float(row["shap_value"])

        group["signed_shap"] += shap_value
        group["abs_shap"] += abs(shap_value)
        group["feature_count"] += 1

        if shap_value > 0:
            group["positive_shap"] += shap_value
        elif shap_value < 0:
            group["negative_shap"] += abs(shap_value)

    total_abs = sum(
        group["abs_shap"]
        for group in grouped.values()
    )

    output = []

    for group in grouped.values():
        signed = group["signed_shap"]

        group["direction"] = (
            "supports_carboxylase"
            if signed > 0
            else "supports_non_carboxylase"
            if signed < 0
            else "neutral"
        )

        group["importance_pct"] = (
            group["abs_shap"] / total_abs * 100.0
            if total_abs > 0
            else 0.0
        )

        for key in (
            "signed_shap",
            "abs_shap",
            "positive_shap",
            "negative_shap",
        ):
            group[key] = round(group[key], 6)

        group["importance_pct"] = round(
            group["importance_pct"],
            2,
        )

        output.append(group)

    return sorted(
        output,
        key=lambda group: group["abs_shap"],
        reverse=True,
    )


def build_db_binary_explanation(
    conn: sqlite3.Connection,
    sequence_id: int,
    stored_probability: float | None = None,
    top_n: int = 15,
) -> dict:
    if ModelStore.xgb_binary is None:
        raise ValueError("Binary model is not loaded")

    vector, feature_names, feature_values = build_db_binary_vector(
        conn,
        sequence_id,
    )

    dmatrix = xgb.DMatrix(
        vector.reshape(1, -1),
        feature_names=feature_names,
    )

    model_probability = float(
        ModelStore.xgb_binary.predict(dmatrix)[0]
    )

    raw = _predict_binary_contributions(
        ModelStore.xgb_binary,
        vector,
        feature_names,
    )

    groups = _group_binary_contributions(raw)

    top_rows = sorted(
        raw["features"],
        key=lambda row: row["abs_shap"],
        reverse=True,
    )[:top_n]

    probability_difference = (
        abs(model_probability - float(stored_probability))
        if stored_probability is not None
        else None
    )

    return {
        "base_value": round(raw["bias"], 6),
        "stored_probability": stored_probability,
        "model_probability": model_probability,
        "probability_difference": probability_difference,
        "probability_matches": (
            probability_difference <= 1e-6
            if probability_difference is not None
            else None
        ),
        "groups": groups,
        "top_features": [
            {
                "rank": rank,
                "feature": row["feature"],
                "group": binary_feature_group(row["feature"]),
                "feature_value": round(
                    feature_values[row["feature"]],
                    8,
                ),
                "shap_value": round(
                    row["shap_value"],
                    6,
                ),
                "abs_shap": round(
                    row["abs_shap"],
                    6,
                ),
                "direction": (
                    "supports_carboxylase"
                    if row["shap_value"] > 0
                    else "supports_non_carboxylase"
                    if row["shap_value"] < 0
                    else "neutral"
                ),
            }
            for rank, row in enumerate(
                top_rows,
                start=1,
            )
        ],
    }