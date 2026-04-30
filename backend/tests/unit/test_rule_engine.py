from __future__ import annotations

from pathlib import Path

from backend.db import ensure_core_tables, get_connection
from backend.ml.test_reasoning import TESTS_NOT_JUSTIFIED
from backend.services.test_recommendation_service import generate_test_recommendations


def test_rule_engine_generates_guideline_backed_recommendations(
    isolated_db_path: Path,
    seed_baseline,
) -> None:
    seed_baseline()
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        conn.execute(
            "INSERT INTO visits(id, symptoms, clinical_summary) VALUES (?, ?, ?)",
            (301, "polyuria, polydipsia, fatigue", "classic diabetes presentation"),
        )
        conn.execute(
            """
            INSERT INTO disease_rankings(visit_id, disease_name, confidence, supporting_symptoms, clinical_basis)
            VALUES (?, ?, ?, ?, ?)
            """,
            (301, "diabetes", 0.84, "polyuria,polydipsia,fatigue", "classic hyperglycemia"),
        )
        conn.commit()

    recommendations = generate_test_recommendations(301, db_path=str(isolated_db_path))

    assert recommendations[0]["test_name"] in {"Fasting Plasma Glucose", "HbA1c"}
    assert all("Guideline:" in item["recommendation_reason"] for item in recommendations)
    assert {item["test_name"] for item in recommendations} >= {"HbA1c", "Fasting Plasma Glucose"}


def test_rule_engine_flags_weakly_supported_recommendations(
    isolated_db_path: Path,
    seed_baseline,
) -> None:
    seed_baseline()
    recommendations = generate_test_recommendations(
        302,
        db_path=str(isolated_db_path),
        ranked_diseases=[
            {
                "disease_name": "cardiac",
                "confidence": 0.30,
                "supporting_symptoms": "fatigue",
                "clinical_basis": "",
            }
        ],
    )

    assert recommendations
    assert {item["uncertainty_type"] for item in recommendations} == {TESTS_NOT_JUSTIFIED}
