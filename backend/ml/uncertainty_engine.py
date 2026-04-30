from __future__ import annotations

from typing import Any, Iterable

LOW_MODEL_CONFIDENCE = "LOW_MODEL_CONFIDENCE"
CONFLICTING_SYMPTOMS = "CONFLICTING_SYMPTOMS"
MISSING_CRITICAL_VITALS = "MISSING_CRITICAL_VITALS"
OUT_OF_RANGE_VITALS = "OUT_OF_RANGE_VITALS"
INCOMPLETE_HISTORY = "INCOMPLETE_HISTORY"
MULTIPLE_CLOSE_DIFFERENTIALS = "MULTIPLE_CLOSE_DIFFERENTIALS"
TESTS_NOT_JUSTIFIED = "TESTS_NOT_JUSTIFIED"
PRICING_UNAVAILABLE = "PRICING_UNAVAILABLE"

ALL_UNCERTAINTY_TYPES = (
    LOW_MODEL_CONFIDENCE,
    CONFLICTING_SYMPTOMS,
    MISSING_CRITICAL_VITALS,
    OUT_OF_RANGE_VITALS,
    INCOMPLETE_HISTORY,
    MULTIPLE_CLOSE_DIFFERENTIALS,
    TESTS_NOT_JUSTIFIED,
    PRICING_UNAVAILABLE,
)

CRITICAL_VITALS = {"SpO2", "Systolic BP", "Heart Rate"}
VITAL_RANGES = {
    "Heart Rate": (60.0, 100.0),
    "Respiratory Rate": (12.0, 20.0),
    "Temperature": (36.1, 37.2),
    "SpO2": (95.0, 100.0),
    "Systolic BP": (90.0, 120.0),
    "Diastolic BP": (60.0, 80.0),
}

CONTRADICTION_PAIRS = (
    ("fever", "denies fever"),
    ("chest pain", "denies chest pain"),
    ("shortness of breath", "denies shortness of breath"),
    ("cough", "denies cough"),
)


def _normalize_prediction(row: dict[str, Any]) -> tuple[str, float]:
    disease = str(row.get("disease_name") or row.get("disease") or "").strip()
    confidence = float(row.get("confidence") or row.get("score") or 0.0)
    if confidence > 1.0:
        confidence = confidence / 100.0
    return disease, min(max(confidence, 0.0), 1.0)


def _symptom_text(symptoms: str | Iterable[str] | None) -> str:
    if symptoms is None:
        return ""
    if isinstance(symptoms, str):
        return symptoms.lower()
    return ", ".join(str(item) for item in symptoms).lower()


def detect_uncertainties(
    *,
    predictions: list[dict[str, Any]] | None = None,
    symptoms: str | Iterable[str] | None = None,
    clinical_summary: str | None = None,
    vitals: list[dict[str, Any]] | None = None,
    recommendations: list[dict[str, Any]] | None = None,
    pricing_flags: Iterable[str] | None = None,
) -> list[str]:
    flags: list[str] = []
    normalized_predictions = [_normalize_prediction(row) for row in predictions or []]
    normalized_predictions = [row for row in normalized_predictions if row[0]]
    text = _symptom_text(symptoms)
    history_text = f"{text} {clinical_summary or ''}".strip()

    if not history_text:
        flags.append(INCOMPLETE_HISTORY)

    if any(positive in text and negative in text for positive, negative in CONTRADICTION_PAIRS):
        flags.append(CONFLICTING_SYMPTOMS)

    if normalized_predictions:
        sorted_predictions = sorted(normalized_predictions, key=lambda item: item[1], reverse=True)
        if sorted_predictions[0][1] < 0.35:
            flags.append(LOW_MODEL_CONFIDENCE)
        if len(sorted_predictions) > 1 and abs(sorted_predictions[0][1] - sorted_predictions[1][1]) <= 0.05:
            flags.append(MULTIPLE_CLOSE_DIFFERENTIALS)
    else:
        flags.append(LOW_MODEL_CONFIDENCE)

    vital_map = {
        str(row.get("vital_name") or row.get("name") or "").strip(): row
        for row in vitals or []
        if str(row.get("vital_name") or row.get("name") or "").strip()
    }
    if not CRITICAL_VITALS.issubset(vital_map):
        flags.append(MISSING_CRITICAL_VITALS)

    for vital_name, row in vital_map.items():
        bounds = VITAL_RANGES.get(vital_name)
        if not bounds:
            continue
        value = float(row.get("value") or 0.0)
        low, high = bounds
        if value < low or value > high:
            flags.append(OUT_OF_RANGE_VITALS)
            break

    recommendation_flags = {
        str(row.get("uncertainty_type") or row.get("cost_uncertainty_type") or "")
        for row in recommendations or []
    }
    if TESTS_NOT_JUSTIFIED in recommendation_flags:
        flags.append(TESTS_NOT_JUSTIFIED)

    if PRICING_UNAVAILABLE in set(pricing_flags or ()) or PRICING_UNAVAILABLE in recommendation_flags:
        flags.append(PRICING_UNAVAILABLE)

    return [flag for flag in ALL_UNCERTAINTY_TYPES if flag in set(flags)]
