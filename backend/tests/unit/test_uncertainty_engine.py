from __future__ import annotations

import pytest

from backend.ml.uncertainty_engine import (
    ALL_UNCERTAINTY_TYPES,
    CONFLICTING_SYMPTOMS,
    INCOMPLETE_HISTORY,
    LOW_MODEL_CONFIDENCE,
    MISSING_CRITICAL_VITALS,
    MULTIPLE_CLOSE_DIFFERENTIALS,
    OUT_OF_RANGE_VITALS,
    PRICING_UNAVAILABLE,
    TESTS_NOT_JUSTIFIED,
    detect_uncertainties,
)


@pytest.mark.parametrize(
    ("expected", "kwargs"),
    [
        (LOW_MODEL_CONFIDENCE, {"predictions": [{"disease_name": "diabetes", "confidence": 0.20}]}),
        (CONFLICTING_SYMPTOMS, {"symptoms": "fever, denies fever"}),
        (MISSING_CRITICAL_VITALS, {"vitals": [{"vital_name": "Heart Rate", "value": 80}]}),
        (
            OUT_OF_RANGE_VITALS,
            {"vitals": [
                {"vital_name": "Heart Rate", "value": 130},
                {"vital_name": "SpO2", "value": 98},
                {"vital_name": "Systolic BP", "value": 118},
            ]},
        ),
        (INCOMPLETE_HISTORY, {"symptoms": "", "clinical_summary": ""}),
        (
            MULTIPLE_CLOSE_DIFFERENTIALS,
            {"predictions": [
                {"disease_name": "diabetes", "confidence": 0.62},
                {"disease_name": "thyroid", "confidence": 0.59},
            ]},
        ),
        (TESTS_NOT_JUSTIFIED, {"recommendations": [{"uncertainty_type": TESTS_NOT_JUSTIFIED}]}),
        (PRICING_UNAVAILABLE, {"pricing_flags": [PRICING_UNAVAILABLE]}),
    ],
)
def test_uncertainty_engine_detects_all_eight_types(expected: str, kwargs: dict) -> None:
    base = {
        "predictions": [{"disease_name": "diabetes", "confidence": 0.82}],
        "symptoms": "polyuria, fatigue",
        "clinical_summary": "complete history",
        "vitals": [
            {"vital_name": "Heart Rate", "value": 82},
            {"vital_name": "SpO2", "value": 98},
            {"vital_name": "Systolic BP", "value": 118},
        ],
        "recommendations": [],
        "pricing_flags": [],
    }
    base.update(kwargs)

    flags = detect_uncertainties(**base)

    assert expected in flags


def test_uncertainty_engine_exports_exact_eight_types() -> None:
    assert len(ALL_UNCERTAINTY_TYPES) == 8
