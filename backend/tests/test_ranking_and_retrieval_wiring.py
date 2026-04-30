from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.db import ensure_core_tables, get_connection
from backend.main import app


def _seed_ranking_visit(db_file: Path) -> None:
    with get_connection(str(db_file)) as conn:
        ensure_core_tables(conn)
        conn.execute(
            "INSERT INTO visits(id, symptoms, clinical_summary) VALUES (?, ?, ?)",
            (777, "cough,weight loss", "persistent cough with recent weight loss"),
        )
        conn.execute(
            """
            INSERT INTO disease_rankings(visit_id, disease_name, confidence, supporting_symptoms, clinical_basis)
            VALUES (?, ?, ?, ?, ?)
            """,
            (777, "lung_cancer", 0.73, "cough,weight loss", "respiratory oncology pattern"),
        )
        conn.execute(
            """
            INSERT INTO recommended_tests(
                visit_id, test_name, priority, source_disease, disease_confidence,
                clinical_reason, guideline_reference, recommendation_reason, uncertainty_type, doctor_confirmed
            ) VALUES (?, ?, 1, ?, 0.73, 'c', 'g', 'r', NULL, 0)
            """,
            (777, "Chest X-ray", "lung_cancer"),
        )
        conn.commit()


def test_predict_disease_ranking_returns_pubmed_field(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "clinicaliq.db"
    _seed_ranking_visit(db_file)
    from backend import db as db_module
    from backend.services import disease_ranking_service

    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_file)
    monkeypatch.setattr(
        disease_ranking_service,
        "fetch_pubmed_evidence",
        lambda **kwargs: [{"pmid": "PMID-1003", "title": "Lung cancer reference", "score": 0.88}],
    )

    client = TestClient(app)
    response = client.post("/predict/disease-ranking/777")
    assert response.status_code == 200
    payload = response.json()
    assert payload["predictions"][0]["pubmed_evidence"]


def test_retrieval_similar_cases_endpoint_wiring(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "clinicaliq.db"
    _seed_ranking_visit(db_file)
    from backend import db as db_module
    from backend import main as main_module

    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_file)
    monkeypatch.setattr(
        main_module,
        "get_similar_cases_for_visit",
        lambda **kwargs: [{"case_id": "C-1", "score": 0.9, "disease_tag": "lung_cancer"}],
    )

    client = TestClient(app)
    response = client.get("/api/v1/retrieval/similar-cases?visit_id=777")
    assert response.status_code == 200
    assert response.json()["results"]
