from __future__ import annotations

from typing import Iterable

TESTS_NOT_JUSTIFIED = "TESTS_NOT_JUSTIFIED"


def _format_confidence(confidence: float) -> str:
    return f"{round(confidence * 100):d}%"


def _clean_token(token: str) -> str:
    return " ".join(token.replace("_", " ").strip().split())


def normalize_symptoms(symptoms: str | Iterable[str] | None) -> list[str]:
    if symptoms is None:
        return []
    if isinstance(symptoms, str):
        raw_tokens = symptoms.split(",")
    else:
        raw_tokens = [str(item) for item in symptoms]

    cleaned = [_clean_token(item) for item in raw_tokens if _clean_token(item)]
    return cleaned[:5]


def summarize_symptoms(symptoms: str | Iterable[str] | None) -> str:
    normalized = normalize_symptoms(symptoms)
    if not normalized:
        return "no strongly discriminative symptoms documented"
    return ", ".join(normalized)


def build_recommendation_reason(
    *,
    disease_name: str,
    disease_confidence: float,
    test_name: str,
    clinical_basis: str,
    supporting_symptoms: str | Iterable[str] | None,
    clinical_reason: str,
    guideline_reference: str,
    priority: int,
) -> str:
    # Deterministic assembly: fixed clause order, no stochastic generation.
    disease_label = _clean_token(disease_name).title()
    basis = _clean_token(clinical_basis) or "clinical pattern matching"
    symptoms_text = summarize_symptoms(supporting_symptoms)
    confidence_text = _format_confidence(disease_confidence)
    return (
        f"{test_name} is Priority {priority} for {disease_label} ({confidence_text} confidence) "
        f"based on {basis}; supporting symptoms: {symptoms_text}. "
        f"Clinical basis: {clinical_reason} (Guideline: {guideline_reference})."
    )


def detect_tests_not_justified(
    *,
    disease_confidence: float,
    supporting_symptoms: str | Iterable[str] | None,
    clinical_basis: str | None,
) -> str | None:
    # Stage-5 Type 7: flag recommendations where disease confidence and evidence are weak.
    symptom_count = len(normalize_symptoms(supporting_symptoms))
    basis = _clean_token(clinical_basis or "")
    if disease_confidence < 0.35 and symptom_count <= 1 and not basis:
        return TESTS_NOT_JUSTIFIED
    return None
