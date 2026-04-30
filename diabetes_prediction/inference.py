"""Load persisted pipeline and score patient inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from diabetes_prediction.config import CANONICAL_FEATURES, METADATA_PATH, MODEL_PATH, ZERO_AS_MISSING_COLS_CANONICAL


class DiabetesPredictor:
    def __init__(self, model_path: Path | str | None = None, metadata_path: Path | str | None = None):
        mp = Path(model_path or MODEL_PATH)
        self.pipe = joblib.load(mp)
        md = Path(metadata_path or METADATA_PATH)
        self.metadata = json.loads(md.read_text(encoding="utf-8")) if md.exists() else {}
        self.threshold = float(self.metadata.get("threshold_validation_f2beta2", 0.5))

    def predict_row(self, row: dict[str, Any]) -> dict[str, Any]:
        df = pd.DataFrame([row])[CANONICAL_FEATURES]
        proba_diabetes = float(self.pipe.predict_proba(df)[0, 1])
        pred_label = int(proba_diabetes >= self.threshold)
        label_text = "Diabetic" if pred_label == 1 else "Non-diabetic"
        confidence = float(max(proba_diabetes, 1.0 - proba_diabetes))
        return {
            "prediction_label": pred_label,
            "prediction_text": label_text,
            "probability_diabetes": proba_diabetes,
            "probability_non_diabetes": float(1.0 - proba_diabetes),
            "confidence": confidence,
            "decision_threshold": self.threshold,
        }


def coerce_float(value: Any, field: str) -> float:
    if value is None:
        raise ValueError(f"Missing required field '{field}'.")
    if isinstance(value, bool):
        raise ValueError(f"Field '{field}' cannot be boolean.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Field '{field}' must be numeric.") from exc


def coerce_int(value: Any, field: str) -> int:
    f = coerce_float(value, field)
    if not np.isfinite(f):
        raise ValueError(f"Field '{field}' must be finite.")
    if abs(f - round(f)) > 1e-6:
        raise ValueError(f"Field '{field}' must be an integer value.")
    return int(round(f))


def validate_medical_ranges(row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Returns sanitized row and warning strings for soft anomalies."""
    from diabetes_prediction.config import RANGE_HINTS

    missing = [k for k in CANONICAL_FEATURES if k not in row]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}.")

    warnings: list[str] = []
    out: dict[str, Any] = {}

    out["Pregnancies"] = coerce_int(row["Pregnancies"], "Pregnancies")
    out["Glucose"] = coerce_float(row["Glucose"], "Glucose")
    out["BloodPressure"] = coerce_float(row["BloodPressure"], "BloodPressure")
    out["SkinThickness"] = coerce_float(row["SkinThickness"], "SkinThickness")
    out["Insulin"] = coerce_float(row["Insulin"], "Insulin")
    out["BMI"] = coerce_float(row["BMI"], "BMI")
    out["DiabetesPedigreeFunction"] = coerce_float(row["DiabetesPedigreeFunction"], "DiabetesPedigreeFunction")
    out["Age"] = coerce_int(row["Age"], "Age")

    for k, v in out.items():
        if isinstance(v, float) and not np.isfinite(v):
            raise ValueError(f"Field '{k}' must be finite.")

    impossible_neg = []
    for key in ("Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"):
        if out[key] < 0:
            impossible_neg.append(key)
    if impossible_neg:
        raise ValueError(f"Negative values not permitted for: {', '.join(impossible_neg)}.")

    for zc in ZERO_AS_MISSING_COLS_CANONICAL:
        if float(out[zc]) == 0:
            warnings.append(
                f"{zc}=0 is treated as missing (invalid clinical sentinel), imputed like in training."
            )

    lo_p, hi_p = RANGE_HINTS["Pregnancies"]
    if out["Pregnancies"] < lo_p or out["Pregnancies"] > hi_p:
        warnings.append(f"Pregnancies outside typical recording range [{lo_p}, {hi_p}].")

    for key in CANONICAL_FEATURES:
        if key == "Pregnancies":
            continue
        lo, hi = RANGE_HINTS[key]
        val = float(out[key])
        if val != 0 and (val < lo or val > hi):
            warnings.append(f"{key}={val} is outside typical PIMA ranges [{lo}, {hi}] — verify units.")

    return out, warnings


def explain_features(pipe: Any, row_df: pd.DataFrame) -> dict[str, float]:
    """Approximate contributions via logistic regression-style surrogate skipped — permutation single-pass."""
    try:
        import shap

        clf = pipe.named_steps["clf"]
        bg = pipe[:-1].transform(row_df)
        explainer = shap.TreeExplainer(clf)
        sv = explainer.shap_values(bg)
        if isinstance(sv, list):
            sv = sv[1]
        sv_row = np.asarray(sv).reshape(-1)
        return {CANONICAL_FEATURES[i]: float(sv_row[i]) for i in range(len(CANONICAL_FEATURES))}
    except Exception:
        return {}
