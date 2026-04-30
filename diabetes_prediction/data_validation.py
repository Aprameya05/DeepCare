"""Load PIMA CSV, validate schema, targets, duplicates, zeros, imbalance."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from diabetes_prediction.config import (
    CANONICAL_FEATURES,
    DATA_PATH,
    RAW_COLUMNS,
    RAW_TO_CANONICAL,
)


def load_raw_csv(path: str | None = None) -> pd.DataFrame:
    p = DATA_PATH if path is None else path
    df = pd.read_csv(p)
    missing = set(RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")
    return df


def to_canonical(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Rename columns; drop non-model column `skin` (redundant); encode target 0/1."""
    x = df[list(RAW_TO_CANONICAL.keys())].rename(columns=RAW_TO_CANONICAL).copy()
    y_raw = df["diabetes"].astype(str).str.upper().map({"TRUE": 1, "FALSE": 0, "1": 1, "0": 0})
    if y_raw.isna().any():
        bad = df.loc[y_raw.isna(), "diabetes"].unique().tolist()
        raise ValueError(f"Invalid diabetes labels: {bad}")
    y = y_raw.astype(int)
    return x, y


def validation_report(df: pd.DataFrame | None = None) -> dict[str, Any]:
    df = load_raw_csv() if df is None else df.copy()
    report: dict[str, Any] = {"path": str(DATA_PATH), "shape": list(df.shape)}
    dup = df.duplicated().sum()
    report["duplicate_rows"] = int(dup)

    x, y = to_canonical(df)
    report["target_counts"] = {str(int(k)): int(v) for k, v in y.value_counts().sort_index().items()}
    pos_rate = float(y.mean())
    report["prevalence_diabetes_fraction"] = pos_rate
    report["class_imbalance_note"] = (
        "moderate imbalance" if 0.25 <= pos_rate <= 0.45 else "check distribution"
    )

    zero_cols = ["glucose_conc", "diastolic_bp", "thickness", "insulin", "bmi"]
    zeros = {c: int((df[c] == 0).sum()) for c in zero_cols}
    report["zero_counts_medically_suspicious"] = zeros

    report["missing_any_cell"] = int(df.isna().sum().sum())
    report["feature_columns_canonical"] = CANONICAL_FEATURES

    inf_rows = np.isinf(x.select_dtypes(include=[np.number])).any(axis=1).sum()
    report["non_finite_rows"] = int(inf_rows)

    neg_glucose = int((x["Glucose"] < 0).sum())
    neg_bp = int((x["BloodPressure"] < 0).sum())
    report["negative_where_impossible"] = {"Glucose": neg_glucose, "BloodPressure": neg_bp}

    return report


def prepare_xy_cleaned(df: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """Canonical X/y with duplicates removed."""
    df = load_raw_csv() if df is None else df
    df = df.drop_duplicates().reset_index(drop=True)
    x, y = to_canonical(df)
    return x, y
