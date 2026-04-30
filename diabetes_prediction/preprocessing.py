"""Imputation pipelines: median vs KNN; scaling."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from diabetes_prediction.config import CANONICAL_FEATURES, ZERO_AS_MISSING_COLS_CANONICAL


def mask_invalid_zeros(df: pd.DataFrame) -> pd.DataFrame:
    """Replace medically invalid zeros with NaN for imputation."""
    out = df.copy()
    for c in ZERO_AS_MISSING_COLS_CANONICAL:
        if c not in out.columns:
            continue
        out.loc[out[c] == 0, c] = np.nan
    return out


def _mask_frame(X):
    if not isinstance(X, pd.DataFrame):
        X = pd.DataFrame(X, columns=CANONICAL_FEATURES)
    return mask_invalid_zeros(X)[CANONICAL_FEATURES]


def build_preprocess_pipeline(imputer_strategy: str) -> Pipeline:
    """
    imputer_strategy: 'median' | 'knn'
    Pipeline steps: mask invalid zeros -> impute -> scale (dense numeric block).
    """
    numeric = CANONICAL_FEATURES
    if imputer_strategy == "median":
        imp = SimpleImputer(strategy="median")
    elif imputer_strategy == "knn":
        imp = KNNImputer(n_neighbors=5, weights="distance")
    else:
        raise ValueError("imputer_strategy must be 'median' or 'knn'")

    mask_step = FunctionTransformer(_mask_frame, validate=False)
    ct = ColumnTransformer(
        transformers=[("num", Pipeline([("imputer", imp), ("scale", StandardScaler())]), numeric)],
        remainder="drop",
    )
    return Pipeline([("mask", mask_step), ("prep", ct)])


def build_full_pipeline(estimator, imputer_strategy: str) -> Pipeline:
    """Classifier wrapped with masking + imputation + scaling."""
    prep_only = build_preprocess_pipeline(imputer_strategy)
    return Pipeline(list(prep_only.steps) + [("clf", estimator)])


def extract_scaler_from_fitted_pipeline(pipe: Pipeline) -> StandardScaler:
    """Return fitted StandardScaler from a fitted full pipeline."""
    ct = pipe.named_steps["prep"]
    num_pipe = ct.named_transformers_["num"]
    return num_pipe.named_steps["scale"]


def compare_imputation_strategies(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    estimator,
    cv,
    scoring_recall_pos,
) -> tuple[str, dict]:
    """Cross-validated recall (diabetic class) + tie-break ROC-AUC / F1."""
    from sklearn.model_selection import cross_validate

    results = {}
    for name in ("median", "knn"):
        pipe = build_full_pipeline(estimator, name)
        cv_out = cross_validate(
            pipe,
            x_train,
            y_train,
            cv=cv,
            scoring={"recall_pos": scoring_recall_pos, "roc_auc": "roc_auc", "f1": "f1"},
            n_jobs=1,
        )
        results[name] = {
            "recall_mean": float(np.mean(cv_out["test_recall_pos"])),
            "recall_std": float(np.std(cv_out["test_recall_pos"])),
            "roc_auc_mean": float(np.mean(cv_out["test_roc_auc"])),
            "f1_mean": float(np.mean(cv_out["test_f1"])),
        }

    r_med = results["median"]["recall_mean"]
    r_knn = results["knn"]["recall_mean"]
    eps = 1e-6
    if r_med > r_knn + eps:
        best_name = "median"
    elif r_knn > r_med + eps:
        best_name = "knn"
    elif results["knn"]["roc_auc_mean"] > results["median"]["roc_auc_mean"] + eps:
        best_name = "knn"
    elif results["median"]["roc_auc_mean"] > results["knn"]["roc_auc_mean"] + eps:
        best_name = "median"
    else:
        best_name = "knn" if results["knn"]["f1_mean"] >= results["median"]["f1_mean"] else "median"

    return best_name, results
