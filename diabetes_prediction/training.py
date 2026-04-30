"""Benchmark models, tune hyperparameters, evaluate, persist artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_validate, train_test_split
from sklearn.svm import SVC

from diabetes_prediction import config as cfg
from diabetes_prediction.config import CANONICAL_FEATURES, RANDOM_STATE
from diabetes_prediction.data_validation import prepare_xy_cleaned, validation_report
from diabetes_prediction.preprocessing import (
    build_full_pipeline,
    compare_imputation_strategies,
    extract_scaler_from_fitted_pipeline,
)


def recall_pos():
    return make_scorer(recall_score, pos_label=1)


def _safe_import_xgb():
    try:
        from xgboost import XGBClassifier

        return XGBClassifier
    except ImportError:
        return None


def _safe_import_lgbm():
    try:
        from lightgbm import LGBMClassifier

        return LGBMClassifier
    except ImportError:
        return None


def _safe_import_cat():
    try:
        from catboost import CatBoostClassifier

        return CatBoostClassifier
    except ImportError:
        return None


def model_candidates(scale_pos_weight: float) -> dict[str, Any]:
    """Named sklearn-compatible estimators (some wrapped later for calibration)."""
    candidates: dict[str, Any] = {
        "logistic_regression": LogisticRegression(
            max_iter=5000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            solver="lbfgs",
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=400,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=1,
            max_depth=None,
        ),
        "svm_rbf": SVC(
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
    }

    XGB = _safe_import_xgb()
    if XGB is not None:
        candidates["xgboost"] = XGB(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            scale_pos_weight=scale_pos_weight,
            tree_method="hist",
            n_jobs=1,
        )

    LGBM = _safe_import_lgbm()
    if LGBM is not None:
        candidates["lightgbm"] = LGBM(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=-1,
            num_leaves=48,
            subsample=0.9,
            colsample_bytree=0.9,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=-1,
        )

    CAT = _safe_import_cat()
    if CAT is not None:
        candidates["catboost"] = CAT(
            iterations=400,
            depth=6,
            learning_rate=0.05,
            loss_function="Logloss",
            eval_metric="AUC",
            random_seed=RANDOM_STATE,
            verbose=False,
            auto_class_weights="Balanced",
            allow_writing_files=False,
        )

    return candidates


def evaluate_pipeline(pipe, x_test: pd.DataFrame, y_test: pd.Series, threshold: float) -> dict[str, Any]:
    proba = pipe.predict_proba(x_test)[:, 1]
    y_pred = (proba >= threshold).astype(int)
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_diabetes": float(precision_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "recall_diabetes": float(recall_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "threshold": float(threshold),
    }


def tune_threshold_recall_focus(pipe, x_val: pd.DataFrame, y_val: pd.Series) -> float:
    """Pick threshold maximizing F2 (beta=2 favors recall)."""
    from sklearn.metrics import fbeta_score

    proba = pipe.predict_proba(x_val)[:, 1]
    best_t, best_score = 0.5, -1.0
    for t in np.linspace(0.05, 0.95, 181):
        y_hat = (proba >= t).astype(int)
        s = fbeta_score(y_val, y_hat, beta=2.0, pos_label=1, zero_division=0)
        if s > best_score:
            best_score = s
            best_t = float(t)
    return best_t


def randomized_search(
    best_key: str,
    base_estimator,
    imputer_strategy: str,
    x_train,
    y_train,
    cv_outer,
    fast_mode: bool = False,
):
    pipe = build_full_pipeline(base_estimator, imputer_strategy)
    cv = cv_outer

    def ni(full: int) -> int:
        return max(6, full // 4) if fast_mode else full

    if best_key == "logistic_regression":
        param_dist = {
            "clf__C": np.logspace(-3, 2, 25),
            "clf__penalty": ["l2"],
        }
        search = RandomizedSearchCV(
            pipe,
            param_distributions=param_dist,
            n_iter=ni(24),
            scoring=make_scorer(recall_score, pos_label=1),
            cv=cv,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=1,
        )
        search.fit(x_train, y_train)
        return search.best_estimator_

    if best_key == "random_forest":
        param_dist = {
            "clf__n_estimators": [200, 400, 600],
            "clf__max_depth": [4, 6, 8, 12, None],
            "clf__min_samples_leaf": [1, 2, 4],
            "clf__max_features": ["sqrt", "log2", None],
        }
        search = RandomizedSearchCV(
            pipe,
            param_distributions=param_dist,
            n_iter=ni(28),
            scoring=make_scorer(recall_score, pos_label=1),
            cv=cv,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=1,
        )
        search.fit(x_train, y_train)
        return search.best_estimator_

    if best_key == "xgboost":
        param_dist = {
            "clf__max_depth": [3, 4, 5, 6, 8],
            "clf__learning_rate": np.linspace(0.02, 0.2, 12),
            "clf__subsample": np.linspace(0.7, 1.0, 6),
            "clf__colsample_bytree": np.linspace(0.7, 1.0, 6),
            "clf__min_child_weight": [1, 2, 5],
            "clf__reg_lambda": np.logspace(-2, 2, 10),
            "clf__n_estimators": [200, 400, 600],
        }
        search = RandomizedSearchCV(
            pipe,
            param_distributions=param_dist,
            n_iter=ni(36),
            scoring=make_scorer(recall_score, pos_label=1),
            cv=cv,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=1,
        )
        search.fit(x_train, y_train)
        return search.best_estimator_

    if best_key == "lightgbm":
        param_dist = {
            "clf__num_leaves": [31, 48, 64, 96],
            "clf__learning_rate": np.linspace(0.02, 0.15, 12),
            "clf__n_estimators": [300, 500, 700],
            "clf__subsample": np.linspace(0.7, 1.0, 6),
            "clf__colsample_bytree": np.linspace(0.7, 1.0, 6),
            "clf__reg_lambda": np.logspace(-3, 2, 12),
            "clf__max_depth": [-1, 6, 8, 12],
        }
        search = RandomizedSearchCV(
            pipe,
            param_distributions=param_dist,
            n_iter=ni(36),
            scoring=make_scorer(recall_score, pos_label=1),
            cv=cv,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=1,
        )
        search.fit(x_train, y_train)
        return search.best_estimator_

    if best_key == "catboost":
        param_dist = {
            "clf__depth": [4, 6, 8, 10],
            "clf__learning_rate": np.linspace(0.02, 0.15, 12),
            "clf__iterations": [300, 500, 700],
            "clf__l2_leaf_reg": np.logspace(-1, 2, 10),
        }
        search = RandomizedSearchCV(
            pipe,
            param_distributions=param_dist,
            n_iter=ni(28),
            scoring=make_scorer(recall_score, pos_label=1),
            cv=cv,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=1,
        )
        search.fit(x_train, y_train)
        return search.best_estimator_

    if best_key == "svm_rbf":
        param_dist = {
            "clf__C": np.logspace(-2, 3, 20),
            "clf__gamma": np.logspace(-4, 1, 15),
        }
        search = RandomizedSearchCV(
            pipe,
            param_distributions=param_dist,
            n_iter=ni(28),
            scoring=make_scorer(recall_score, pos_label=1),
            cv=cv,
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=1,
        )
        search.fit(x_train, y_train)
        return search.best_estimator_

    pipe.fit(x_train, y_train)
    return pipe


def cross_val_report(pipe, x, y, cv) -> dict[str, float]:
    scoring = {
        "accuracy": "accuracy",
        "precision": make_scorer(precision_score, pos_label=1, zero_division=0),
        "recall": make_scorer(recall_score, pos_label=1, zero_division=0),
        "f1": make_scorer(f1_score, pos_label=1, zero_division=0),
        "roc_auc": "roc_auc",
    }
    out = cross_validate(pipe, x, y, cv=cv, scoring=scoring, n_jobs=1)
    return {k: float(np.mean(out[f"test_{k}"])) for k in scoring}


def pick_best_model_row(benchmark_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Primary sort: recall (diabetes); tie-break: F1, ROC-AUC, accuracy."""
    return sorted(
        benchmark_rows,
        key=lambda r: (
            r["cv_recall_mean"],
            r["cv_f1_mean"],
            r["cv_roc_auc_mean"],
            r["cv_accuracy_mean"],
        ),
        reverse=True,
    )[0]


def permutation_importance_safe(pipe, x_val, y_val) -> dict[str, float]:
    from sklearn.inspection import permutation_importance

    r = permutation_importance(
        pipe,
        x_val,
        y_val,
        n_repeats=15,
        random_state=RANDOM_STATE,
        scoring=make_scorer(recall_score, pos_label=1),
        n_jobs=1,
    )
    return {CANONICAL_FEATURES[i]: float(v) for i, v in enumerate(r.importances_mean)}


def save_shap_summary(pipe, x_bg: pd.DataFrame, out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import shap
    except ImportError:
        return
    tree = pipe.named_steps["clf"]
    x_s = pipe[:-1].transform(x_bg.iloc[: min(400, len(x_bg))])
    explainer = shap.TreeExplainer(tree)
    shap_vals = explainer.shap_values(x_s)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    shap.summary_plot(
        shap_vals,
        x_s,
        feature_names=CANONICAL_FEATURES,
        show=False,
        plot_size=(10, 6),
    )
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def run_training(
    save_shap_plot: bool = True,
    generate_eval_plots: bool = True,
    fast_mode: bool = False,
) -> dict[str, Any]:
    cfg.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    report = validation_report()
    x, y = prepare_xy_cleaned()
    x = x[CANONICAL_FEATURES]

    neg = int((y == 0).sum())
    pos = int((y == 1).sum())
    scale_pos_weight = neg / max(pos, 1)

    cv_splits = 3 if fast_mode else 5
    cv_quick = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=RANDOM_STATE)

    probe_n_estimators = 50 if fast_mode else 200
    probe_estimator = RandomForestClassifier(
        n_estimators=probe_n_estimators,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    best_imp_name, imp_compare = compare_imputation_strategies(
        x,
        y,
        probe_estimator,
        cv_quick,
        recall_pos(),
    )

    all_candidates = model_candidates(scale_pos_weight)
    if fast_mode:
        fast_keys = ["logistic_regression", "random_forest", "xgboost"]
        candidates = {k: all_candidates[k] for k in fast_keys if k in all_candidates}
    else:
        candidates = all_candidates
    benchmark_rows: list[dict[str, Any]] = []

    for name, est in candidates.items():
        print(f"Benchmarking model: {name}...")
        pipe = build_full_pipeline(est, best_imp_name)
        cv_scores = cross_val_report(pipe, x, y, cv_quick)
        print(f"  Recall (CV): {cv_scores['recall']:.3f}")
        benchmark_rows.append(
            {
                "model": name,
                "cv_accuracy_mean": cv_scores["accuracy"],
                "cv_precision_mean": cv_scores["precision"],
                "cv_recall_mean": cv_scores["recall"],
                "cv_f1_mean": cv_scores["f1"],
                "cv_roc_auc_mean": cv_scores["roc_auc"],
            }
        )

    winner = pick_best_model_row(benchmark_rows)
    best_key = winner["model"]
    base_estimator = candidates[best_key]

    x_train, x_hold, y_train, y_hold = train_test_split(
        x,
        y,
        test_size=0.25,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_hold,
        y_hold,
        test_size=0.5,
        stratify=y_hold,
        random_state=RANDOM_STATE,
    )

    print(f"Tuning winner: {best_key}...")
    final_pipe = randomized_search(
        best_key,
        base_estimator,
        best_imp_name,
        x_train,
        y_train,
        cv_outer=cv_quick,
        fast_mode=fast_mode,
    )
    print("Threshold tuning...")
    threshold = tune_threshold_recall_focus(final_pipe, x_val, y_val)
    print(f"  Best threshold: {threshold:.3f}")

    metrics_test = evaluate_pipeline(final_pipe, x_test, y_test, threshold)

    cv_final = cross_val_report(final_pipe, x_train, y_train, cv_quick)

    proba_test = final_pipe.predict_proba(x_test)[:, 1]
    y_pred_test = (proba_test >= threshold).astype(int)
    cm = confusion_matrix(y_test, y_pred_test).tolist()

    feat_imp = permutation_importance_safe(final_pipe, x_val, y_val)

    plots_dir = cfg.MODELS_DIR / "plots"
    if generate_eval_plots:
        plots_dir.mkdir(parents=True, exist_ok=True)
        try:
            import matplotlib.pyplot as plt

            ConfusionMatrixDisplay.from_predictions(y_test, y_pred_test)
            plt.savefig(plots_dir / "confusion_matrix_test.png", dpi=150)
            plt.close()

            fpr, tpr, _ = roc_curve(y_test, proba_test)
            plt.figure(figsize=(6, 5))
            plt.plot(fpr, tpr, label=f"AUC={metrics_test['roc_auc']:.3f}")
            plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
            plt.xlabel("False positive rate")
            plt.ylabel("True positive rate")
            plt.legend()
            plt.tight_layout()
            plt.savefig(plots_dir / "roc_curve_test.png", dpi=150)
            plt.close()
        except ImportError:
            pass

    if save_shap_plot and best_key in ("xgboost", "lightgbm", "catboost", "random_forest"):
        plots_dir.mkdir(parents=True, exist_ok=True)
        target_png = plots_dir / "shap_summary.png"
        try:
            save_shap_summary(final_pipe, x_train, target_png)
        except Exception:
            pass

    metadata = {
        "dataset_validation": report,
        "imputation_comparison": imp_compare,
        "chosen_imputer": best_imp_name,
        "benchmark": benchmark_rows,
        "selected_model": best_key,
        "scale_pos_weight_used": scale_pos_weight,
        "threshold_validation_f2beta2": threshold,
        "cross_validation_train_fold_metrics_mean": cv_final,
        "test_holdout_metrics": metrics_test,
        "confusion_matrix_test": cm,
        "classification_report_test": classification_report(
            y_test,
            y_pred_test,
            labels=[0, 1],
            target_names=["non_diabetic", "diabetic"],
            zero_division=0,
        ),
        "feature_importance_permutation_recall": feat_imp,
        "canonical_features_order": CANONICAL_FEATURES,
        "random_state": RANDOM_STATE,
        "calibration_applied": False,
        "disclaimer": (
            "Educational screening aid only — not a medical device. "
            "Requires clinician interpretation and laboratory confirmation."
        ),
    }

    joblib.dump(final_pipe, cfg.MODEL_PATH)

    scaler = extract_scaler_from_fitted_pipeline(final_pipe)
    joblib.dump(scaler, cfg.SCALER_PATH)

    cfg.METADATA_PATH.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    return metadata


if __name__ == "__main__":
    import os

    _fast = os.environ.get("TRAIN_FAST", "").lower() in ("1", "true", "yes")
    meta = run_training(fast_mode=_fast)
    print(json.dumps({k: meta[k] for k in meta if k != "classification_report_test"}, indent=2, default=str))
    print(meta["classification_report_test"])
