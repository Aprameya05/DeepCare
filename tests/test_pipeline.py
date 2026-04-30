"""End-to-end smoke: validate data, train (fast), predict, API shape."""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Lightweight tests that avoid heavy sklearn imports at collection time
# ---------------------------------------------------------------------------

def test_validation_report_structure():
    from diabetes_prediction.data_validation import validation_report

    rep = validation_report()
    assert rep["shape"][0] >= 700
    assert "0" in rep["target_counts"] and "1" in rep["target_counts"]


def test_prepare_xy_canonical_columns():
    from diabetes_prediction.data_validation import prepare_xy_cleaned

    x, y = prepare_xy_cleaned()
    assert list(x.columns)[:3] == ["Pregnancies", "Glucose", "BloodPressure"]
    assert set(y.unique()) == {0, 1}


def test_validate_medical_ranges_errors():
    from diabetes_prediction.inference import validate_medical_ranges

    base = {
        "Pregnancies": 1,
        "Glucose": 88,
        "BloodPressure": 66,
        "SkinThickness": 20,
        "Insulin": 50,
        "BMI": 26,
        "DiabetesPedigreeFunction": 0.2,
        "Age": 31,
    }
    bad = {**base, "Glucose": -5}
    with pytest.raises(ValueError, match="Negative"):
        validate_medical_ranges(bad)

    with pytest.raises(ValueError, match="Missing"):
        validate_medical_ranges({"Pregnancies": 1})


def test_train_fast_and_predict(tmp_path, monkeypatch):
    # Heavy imports inside the test body so collection stays fast.
    from diabetes_prediction import config as cfg
    from diabetes_prediction.inference import DiabetesPredictor, validate_medical_ranges
    from diabetes_prediction.training import run_training

    monkeypatch.setattr(cfg, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(cfg, "MODEL_PATH", tmp_path / "model.pkl")
    monkeypatch.setattr(cfg, "SCALER_PATH", tmp_path / "scaler.pkl")
    monkeypatch.setattr(cfg, "METADATA_PATH", tmp_path / "metadata.json")

    meta = run_training(
        save_shap_plot=False,
        generate_eval_plots=False,
        fast_mode=True,
    )
    assert "test_holdout_metrics" in meta
    assert (tmp_path / "model.pkl").exists(), "model.pkl not saved"
    assert (tmp_path / "scaler.pkl").exists(), "scaler.pkl not saved"

    row = {
        "Pregnancies": 6,
        "Glucose": 148,
        "BloodPressure": 72,
        "SkinThickness": 35,
        "Insulin": 0,
        "BMI": 33.6,
        "DiabetesPedigreeFunction": 0.627,
        "Age": 50,
    }
    _, warns = validate_medical_ranges(row)
    assert any("Insulin" in w for w in warns), "Expected Insulin=0 warning"

    pred = DiabetesPredictor(
        model_path=tmp_path / "model.pkl",
        metadata_path=tmp_path / "metadata.json",
    ).predict_row(row)
    assert pred["prediction_label"] in (0, 1)
    assert 0.0 <= pred["probability_diabetes"] <= 1.0
    assert pred["confidence"] >= 0.5
