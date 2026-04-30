from __future__ import annotations

import json
from typing import Any

from backend.db import ensure_core_tables, get_connection
from backend.ml.disease_severity import DEFAULT_BURDEN_PROFILE, DISEASE_BURDEN_PROFILES


def _normalize_disease(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _get_severity_for_disease(disease_name: str) -> float:
    key = _normalize_disease(disease_name)
    return DISEASE_BURDEN_PROFILES.get(key, DEFAULT_BURDEN_PROFILE).severity_score


def _test_overlap(ai_tests: set[str], doctor_tests: set[str]) -> float:
    if not ai_tests and not doctor_tests:
        return 1.0
    union = ai_tests | doctor_tests
    if not union:
        return 0.0
    return len(ai_tests & doctor_tests) / len(union)


def score_accuracy(
    *,
    visit_id: int,
    override_id: str,
    confirmed_disease: str,
    confirmed_tests: list[str],
    db_path: str | None = None,
) -> dict[str, Any]:
    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        ranked = conn.execute(
            """
            SELECT disease_name, confidence
            FROM disease_rankings
            WHERE visit_id = ?
            ORDER BY confidence DESC
            """,
            (visit_id,),
        ).fetchall()
        top1_prediction = str(ranked[0]["disease_name"]) if ranked else ""
        top3_predictions = {str(row["disease_name"]).strip().lower() for row in ranked[:3]}
        top1_match = 1.0 if _normalize_disease(top1_prediction) == _normalize_disease(confirmed_disease) else 0.0
        top3_match = 1.0 if _normalize_disease(confirmed_disease) in {_normalize_disease(x) for x in top3_predictions} else 0.0

        ai_tests_rows = conn.execute(
            """
            SELECT test_name
            FROM recommended_tests
            WHERE visit_id = ?
            """,
            (visit_id,),
        ).fetchall()
        ai_tests = {str(row["test_name"]).strip().lower() for row in ai_tests_rows}
        doctor_tests = {str(item).strip().lower() for item in confirmed_tests if str(item).strip()}
        test_overlap = _test_overlap(ai_tests, doctor_tests)

        predicted_severity = _get_severity_for_disease(top1_prediction)
        confirmed_severity = _get_severity_for_disease(confirmed_disease)
        severity_delta = abs(predicted_severity - confirmed_severity)

        # Composite formula required by spec.
        composite = (
            0.40 * top1_match
            + 0.20 * top3_match
            + 0.25 * test_overlap
            + 0.15 * (1 - severity_delta)
        )
        composite = round(composite, 6)

        ai_count = len(ai_tests)
        doctor_count = len(doctor_tests)
        burden_delta = round(abs(ai_count - doctor_count) / max(1, doctor_count), 6)

        conn.execute(
            """
            INSERT INTO ai_accuracy_tracking (
                visit_id,
                override_id,
                top1_match,
                top3_match,
                test_overlap,
                severity_delta,
                burden_delta,
                composite_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(visit_id) DO UPDATE SET
                override_id = excluded.override_id,
                top1_match = excluded.top1_match,
                top3_match = excluded.top3_match,
                test_overlap = excluded.test_overlap,
                severity_delta = excluded.severity_delta,
                burden_delta = excluded.burden_delta,
                composite_score = excluded.composite_score
            """,
            (
                visit_id,
                override_id,
                top1_match,
                top3_match,
                test_overlap,
                severity_delta,
                burden_delta,
                composite,
            ),
        )
        conn.commit()

    return {
        "visit_id": visit_id,
        "override_id": override_id,
        "top1_match": top1_match,
        "top3_match": top3_match,
        "test_overlap": round(test_overlap, 6),
        "severity_delta": round(severity_delta, 6),
        "burden_delta": burden_delta,
        "composite_score": composite,
        "formula": "0.40*top1 + 0.20*top3 + 0.25*test_overlap + 0.15*(1-severity_delta)",
        "inputs": json.dumps(
            {
                "top1_prediction": top1_prediction,
                "confirmed_disease": confirmed_disease,
                "ai_tests": sorted(ai_tests),
                "doctor_tests": sorted(doctor_tests),
            }
        ),
    }
