"""Flask API for diabetes screening inference."""

from __future__ import annotations

import traceback

from flask import Flask, jsonify, request

from diabetes_prediction.config import CANONICAL_FEATURES
from diabetes_prediction.inference import DiabetesPredictor, explain_features, validate_medical_ranges

app = Flask(__name__)

_predictor: DiabetesPredictor | None = None


def get_predictor() -> DiabetesPredictor:
    global _predictor
    if _predictor is None:
        _predictor = DiabetesPredictor()
    return _predictor


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    if not request.is_json:
        return jsonify({"error": "Expected application/json body."}), 400

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Malformed JSON."}), 400

    missing = [k for k in CANONICAL_FEATURES if k not in payload]
    if missing:
        return jsonify({"error": "Missing fields.", "missing_fields": missing}), 400

    try:
        row, warnings = validate_medical_ranges(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        pred = get_predictor().predict_row(row)
        df_row = None
        try:
            import pandas as pd

            df_row = pd.DataFrame([row])[CANONICAL_FEATURES]
            shap_scores = explain_features(get_predictor().pipe, df_row)
        except Exception:
            shap_scores = {}

        out = {
            "prediction": pred["prediction_text"],
            "prediction_code": pred["prediction_label"],
            "confidence": pred["confidence"],
            "probability_diabetes": pred["probability_diabetes"],
            "probability_non_diabetes": pred["probability_non_diabetes"],
            "decision_threshold": pred["decision_threshold"],
            "warnings": warnings,
            "feature_attribution_shap": shap_scores,
        }
        return jsonify(out)
    except Exception:
        return jsonify({"error": "Inference failure.", "detail": traceback.format_exc(limit=3)}), 500


def create_app():
    return app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
