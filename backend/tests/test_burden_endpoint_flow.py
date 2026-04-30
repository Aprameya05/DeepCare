from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.db import ensure_core_tables, get_connection
from backend.main import app
from backend.scripts.seed_country_pricing import _build_pricing_rows
from backend.scripts.seed_disease_test_rules import _build_rules


def _seed_for_visit(db_file: Path) -> None:
    with get_connection(str(db_file)) as conn:
        ensure_core_tables(conn)
        conn.executemany(
            """
            INSERT OR REPLACE INTO disease_test_rules(
                disease_name, test_name, priority, clinical_reason, guideline_reference
            ) VALUES (?, ?, ?, ?, ?)
            """,
            _build_rules(),
        )
        conn.executemany(
            """
            INSERT OR REPLACE INTO country_test_pricing(
                country, city, test_name, price_usd, source_note
            ) VALUES (?, ?, ?, ?, ?)
            """,
            _build_pricing_rows(),
        )
        conn.execute("INSERT INTO visits(id, symptoms) VALUES (?, ?)", (222, "polyuria, fatigue"))
        conn.execute(
            """
            INSERT INTO disease_rankings(
                visit_id, disease_name, confidence, supporting_symptoms, clinical_basis
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (222, "diabetes", 0.86, "polyuria,fatigue", "metabolic dysregulation"),
        )
        conn.commit()


def test_burden_endpoint_returns_full_result_and_persists(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "clinicaliq.db"
    _seed_for_visit(db_file)

    from backend import db as db_module
    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_file)

    client = TestClient(app)
    response = client.post("/api/v1/calculate/burden/222?country=US&city=New%20York&insurance_coverage=0.8")
    assert response.status_code == 200
    payload = response.json()
    assert "burden_result" in payload
    assert payload["burden_result"]["category"] in {"Low", "Medium", "High"}
    assert payload["burden_result"]["explanation"]
    assert payload["ordering"]["ordered_tests"]

    with get_connection(str(db_file)) as conn:
        persisted = conn.execute(
            "SELECT COUNT(*) AS c FROM burden_scores WHERE visit_id = ?",
            (222,),
        ).fetchone()["c"]
    assert int(persisted) >= 1
