from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.db import ensure_core_tables, get_connection
from backend.main import app
from backend.services.accuracy_scoring_service import score_accuracy


def _seed_visit_for_accuracy(db_file: Path) -> None:
    with get_connection(str(db_file)) as conn:
        ensure_core_tables(conn)
        conn.execute("INSERT INTO visits(id, symptoms, clinical_summary) VALUES (?, ?, ?)", (501, "fatigue,polyuria", "fatigue and polyuria over weeks"))
        conn.executemany(
            """
            INSERT INTO disease_rankings(visit_id, disease_name, confidence, supporting_symptoms, clinical_basis)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (501, "diabetes", 0.8, "fatigue,polyuria", "glycemic pattern"),
                (501, "thyroid", 0.5, "fatigue", "endocrine differential"),
                (501, "cardiac", 0.3, "fatigue", "risk profile"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO recommended_tests(
                visit_id, test_name, priority, source_disease, disease_confidence,
                clinical_reason, guideline_reference, recommendation_reason, uncertainty_type, doctor_confirmed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            [
                (501, "HbA1c", 1, "diabetes", 0.8, "c", "g", "r", None),
                (501, "Fasting Plasma Glucose", 1, "diabetes", 0.8, "c", "g", "r", None),
                (501, "Lipid Panel", 2, "diabetes", 0.8, "c", "g", "r", None),
            ],
        )
        conn.commit()


def test_score_accuracy_composite_formula_exact(tmp_path: Path) -> None:
    db_file = tmp_path / "clinicaliq.db"
    _seed_visit_for_accuracy(db_file)
    result = score_accuracy(
        visit_id=501,
        override_id="ovr-1",
        confirmed_disease="diabetes",
        confirmed_tests=["HbA1c", "Lipid Panel"],
        db_path=str(db_file),
    )
    # top1=1, top3=1, overlap=2/3, severity_delta=0 => composite=0.916666...
    expected = round(0.40 * 1 + 0.20 * 1 + 0.25 * (2 / 3) + 0.15 * (1 - 0), 6)
    assert result["composite_score"] == expected


def test_override_creates_accuracy_and_feedback_queue(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "clinicaliq.db"
    _seed_visit_for_accuracy(db_file)

    from backend import db as db_module

    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_file)

    client = TestClient(app)
    payload = {
        "doctor_id": "dr-42",
        "confirmed_disease": "diabetes",
        "confirmed_tests": ["HbA1c", "Lipid Panel"],
        "notes": "Clinician confirms diabetes and focuses core metabolic tests.",
    }
    response = client.post("/api/v1/doctor/override/501", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["accuracy"]["composite_score"] > 0

    with get_connection(str(db_file)) as conn:
        accuracy_count = conn.execute(
            "SELECT COUNT(*) AS c FROM ai_accuracy_tracking WHERE visit_id = 501"
        ).fetchone()["c"]
        queue_count = conn.execute(
            "SELECT COUNT(*) AS c FROM feedback_queue WHERE visit_id = 501"
        ).fetchone()["c"]
    assert int(accuracy_count) == 1
    assert int(queue_count) == 1
