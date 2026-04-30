from __future__ import annotations

from pathlib import Path

from backend.db import ensure_core_tables, get_connection
from backend.services.accuracy_scoring_service import score_accuracy


def test_accuracy_scoring_composite_formula(isolated_db_path: Path) -> None:
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        conn.executemany(
            "INSERT INTO disease_rankings(visit_id, disease_name, confidence) VALUES (?, ?, ?)",
            [(501, "diabetes", 0.8), (501, "thyroid", 0.4), (501, "cardiac", 0.3)],
        )
        conn.executemany(
            """
            INSERT INTO recommended_tests(
                visit_id, test_name, priority, source_disease, disease_confidence,
                clinical_reason, guideline_reference, recommendation_reason, uncertainty_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (501, "HbA1c", 1, "diabetes", 0.8, "c", "g", "r", None),
                (501, "Fasting Plasma Glucose", 1, "diabetes", 0.8, "c", "g", "r", None),
                (501, "Lipid Panel", 2, "diabetes", 0.8, "c", "g", "r", None),
            ],
        )
        conn.commit()

    result = score_accuracy(
        visit_id=501,
        override_id="override-1",
        confirmed_disease="diabetes",
        confirmed_tests=["HbA1c", "Lipid Panel"],
        db_path=str(isolated_db_path),
    )

    expected = round(0.40 + 0.20 + 0.25 * (2 / 3) + 0.15, 6)
    assert result["composite_score"] == expected
    assert result["top1_match"] == 1.0
