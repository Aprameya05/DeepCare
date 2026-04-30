from __future__ import annotations

import json
import uuid
from typing import Any

from backend.db import ensure_core_tables, get_connection
from backend.services.accuracy_scoring_service import score_accuracy


def _feature_snapshot(conn, visit_id: int) -> dict[str, Any]:
    visit_row = conn.execute(
        "SELECT symptoms, clinical_summary FROM visits WHERE id = ?",
        (visit_id,),
    ).fetchone()
    disease_rows = conn.execute(
        """
        SELECT disease_name, confidence, supporting_symptoms, clinical_basis
        FROM disease_rankings
        WHERE visit_id = ?
        ORDER BY confidence DESC
        """,
        (visit_id,),
    ).fetchall()
    test_rows = conn.execute(
        """
        SELECT test_name, priority, source_disease, disease_confidence
        FROM recommended_tests
        WHERE visit_id = ?
        ORDER BY priority ASC
        """,
        (visit_id,),
    ).fetchall()
    return {
        "visit": dict(visit_row) if visit_row else {},
        "disease_rankings": [dict(row) for row in disease_rows],
        "recommended_tests": [dict(row) for row in test_rows],
    }


def process_doctor_override(
    *,
    visit_id: int,
    doctor_id: str,
    confirmed_disease: str,
    confirmed_tests: list[str],
    notes: str = "",
    db_path: str | None = None,
) -> dict[str, Any]:
    override_id = str(uuid.uuid4())
    queue_id = str(uuid.uuid4())
    clean_tests = [str(item).strip() for item in confirmed_tests if str(item).strip()]

    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        conn.execute(
            """
            INSERT INTO doctor_overrides (
                override_id, visit_id, doctor_id, confirmed_disease, confirmed_tests, notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (override_id, visit_id, doctor_id, confirmed_disease, json.dumps(clean_tests), notes),
        )

        conn.execute(
            """
            UPDATE disease_rankings
            SET confirmed_by_doctor = CASE
                WHEN REPLACE(LOWER(disease_name), '_', ' ') = REPLACE(LOWER(?), '_', ' ') THEN 1
                ELSE 0
            END
            WHERE visit_id = ?
            """,
            (confirmed_disease, visit_id),
        )

        conn.execute("UPDATE recommended_tests SET doctor_confirmed = 0 WHERE visit_id = ?", (visit_id,))
        for test_name in clean_tests:
            updated = conn.execute(
                """
                UPDATE recommended_tests
                SET doctor_confirmed = 1
                WHERE visit_id = ?
                  AND LOWER(test_name) = LOWER(?)
                """,
                (visit_id, test_name),
            ).rowcount
            if updated == 0:
                conn.execute(
                    """
                    INSERT INTO recommended_tests (
                        visit_id,
                        test_name,
                        priority,
                        source_disease,
                        disease_confidence,
                        clinical_reason,
                        guideline_reference,
                        recommendation_reason,
                        uncertainty_type,
                        doctor_confirmed
                    )
                    VALUES (?, ?, 2, ?, 1.0, ?, ?, ?, NULL, 1)
                    """,
                    (
                        visit_id,
                        test_name,
                        confirmed_disease,
                        "Added from clinician override.",
                        "Clinician review",
                        f"{test_name} inserted from doctor override for {confirmed_disease}.",
                    ),
                )

        snapshot = _feature_snapshot(conn, visit_id)
        conn.execute(
            """
            INSERT INTO feedback_queue (
                queue_id,
                visit_id,
                override_id,
                feature_vector,
                label_disease,
                label_tests,
                consumed
            )
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (
                queue_id,
                visit_id,
                override_id,
                json.dumps(snapshot),
                confirmed_disease,
                json.dumps(clean_tests),
            ),
        )
        conn.commit()

    accuracy = score_accuracy(
        visit_id=visit_id,
        override_id=override_id,
        confirmed_disease=confirmed_disease,
        confirmed_tests=clean_tests,
        db_path=db_path,
    )
    return {
        "visit_id": visit_id,
        "override_id": override_id,
        "queue_id": queue_id,
        "doctor_id": doctor_id,
        "confirmed_disease": confirmed_disease,
        "confirmed_tests": clean_tests,
        "notes": notes,
        "accuracy": accuracy,
    }
