from functools import lru_cache
import json
from pathlib import Path

try:
    from .config import PATHS
except ImportError:
    from config import PATHS


GROUP_LABELS = {
    "Pfam": "Pfam domains",
    "ESM-2": "ESM-2 embedding",
    "ESM2": "ESM-2 embedding",
    "Dipeptide": "Dipeptide composition",
    "AAC": "Amino acid composition",
    "PseudoAAC": "Amino acid composition",
    "Physicochemical": "Physicochemical",
    "Catalytic_motif": "Catalytic core motifs",
    "EC_onehot": "EC one-hot",
    "InterPro": "InterPro",
    "Kingdom": "Other",
    "Other": "Other",
}


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def _load_shap_files():
    shap_dir = PATHS.SHAP
    return {
        "ec_per_class": _load_json(shap_dir / "shap_ec_per_class.json") or {},
        "km_global": _load_json(shap_dir / "shap_km_global.json") or {},
        "km_per_ec": _load_json(shap_dir / "shap_km_per_ec.json") or {},
        "km_within_ec": _load_json(shap_dir / "shap_km_within_ec.json") or {},
    }


def _pretty_group(group):
    if not group:
        return "Other"
    return GROUP_LABELS.get(group, group)


def _infer_group(feature: str) -> str:
    if feature.startswith("pfam_"):
        return "Pfam domains"
    if feature.startswith("esm2_"):
        return "ESM-2 embedding"
    if feature.startswith("dp_"):
        return "Dipeptide composition"
    if feature.startswith("aac_") or feature.startswith("pse_"):
        return "Amino acid composition"
    if feature.startswith("phys_"):
        return "Physicochemical"
    if feature.startswith("motif_"):
        return "EC-specific motifs"
    if feature.startswith("inv_"):
        return "Catalytic core motifs"
    if feature.startswith("ec_oh_"):
        return "EC one-hot"
    if feature.startswith("n_"):
        return "InterPro"
    return "Other"

def _extract_feature_rows(obj):
    """
    SHAP JSON files may store feature rows either directly as a list,
    or nested inside a dict under keys such as top_features/top_global.
    Return a list of feature-row dicts.
    """
    if obj is None:
        return []

    if isinstance(obj, list):
        return obj

    if isinstance(obj, dict):
        for key in [
            # EC per-class files
            "top_features_true_pos",
            "top_features_global",

            # generic / fallback keys
            "top_features",
            "top_features_by_shap",
            "top_class_features",
            "top_ec_features",
            "features_ranked",
            "ranked_features",
            "top",
            "features",
            "top_global",
            "top_pfam_by_shap",
            "important_features",
            "rows",
        ]:
            val = obj.get(key)
            if isinstance(val, list):
                return val

    return []

def _normalise_rows(rows, limit=10):
    rows = _extract_feature_rows(rows)

    if not rows:
        return []

    out = []
    for i, row in enumerate(rows[:limit], start=1):
        if not isinstance(row, dict):
            continue

        feature = row.get("feature") or row.get("feature_name") or row.get("name")
        if not feature:
            continue

        group = _pretty_group(row.get("group") or row.get("feature_group") or _infer_group(feature))

        item = {
            "rank": int(row.get("rank") or i),
            "feature": feature,
            "group": group,
        }

        # Frontend can display either pct_importance or mean_abs_shap.
        if row.get("pct_importance") is not None:
            item["pct_importance"] = float(row["pct_importance"])
        elif row.get("importance_pct") is not None:
            item["pct_importance"] = float(row["importance_pct"])
        elif row.get("mean_abs_shap") is not None:
            item["mean_abs_shap"] = float(row["mean_abs_shap"])
        elif row.get("diff_shap") is not None:
            item["mean_abs_shap"] = abs(float(row["diff_shap"]))

        if row.get("direction") is not None:
            item["direction"] = row["direction"]
        if row.get("ec") is not None:
            item["ec"] = row["ec"]
        if row.get("ec_name") is not None:
            item["ec_name"] = row["ec_name"]

        out.append(item)

    return out


def _normalise_group_importance(group_map):
    if not group_map:
        return None

    out = {}
    for group, value in group_map.items():
        pretty = _pretty_group(group)
        out[pretty] = out.get(pretty, 0.0) + float(value)

    total = sum(out.values())
    if total > 0:
        out = {k: (v / total) * 100 for k, v in out.items()}

    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


def _group_importance_from_rows(rows):
    groups = {}
    for row in rows:
        group = row.get("group") or "Other"
        value = row.get("pct_importance")
        if value is None:
            value = row.get("mean_abs_shap") or 0
        groups[group] = groups.get(group, 0.0) + float(value)

    total = sum(groups.values())
    if total > 0:
        groups = {k: (v / total) * 100 for k, v in groups.items()}

    return dict(sorted(groups.items(), key=lambda kv: kv[1], reverse=True))


def build_shap_payload(ec_predicted=None, limit=10):
    data = _load_shap_files()

    # EC classification SHAP: nested under "per_class".
    ec_per_class = data["ec_per_class"].get("per_class", {})
    ec_obj = ec_per_class.get(ec_predicted, {}) if ec_predicted else {}
    ec_rows_raw = ec_obj
    ec_group_raw = ec_obj.get("group_importance") if isinstance(ec_obj, dict) else None

    # Km SHAP: prefer EC-specific if present, then global.
    km_per_ec = data["km_per_ec"].get("per_ec", {})
    km_rows_raw = km_per_ec.get(ec_predicted, []) if ec_predicted else []

    km_group_raw = None

    # If within-EC file has this EC, it has useful group_importance_all.
    within = data["km_within_ec"].get(ec_predicted, {}) if ec_predicted else {}
    if within:
        km_group_raw = within.get("group_importance_all")

    # Do NOT fall back to global Km SHAP for per-sequence detail pages.
    # Otherwise every entry gets the same generic Km panel.
    if not _extract_feature_rows(km_rows_raw):
        km_rows_raw = []

    if km_group_raw is None:
        km_group_raw = None

    ec_rows = _normalise_rows(ec_rows_raw, limit=limit)
    km_rows = _normalise_rows(km_rows_raw, limit=limit)

    payload = {
        "ec_classification": ec_rows,
        "km_regression": km_rows,
        "ec_group_importance": _normalise_group_importance(ec_group_raw) or _group_importance_from_rows(ec_rows),
        "km_group_importance": _normalise_group_importance(km_group_raw) or _group_importance_from_rows(km_rows),
    }

    if not ec_rows and not km_rows:
        return None

    return payload