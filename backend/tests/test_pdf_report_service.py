from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.db import ensure_core_tables, get_connection
from backend.main import app
from backend.scripts.seed_country_pricing import _build_pricing_rows
from backend.scripts.seed_disease_test_rules import _build_rules


def _seed_report_visit(db_file: Path) -> None:
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
        conn.execute(
            "INSERT INTO visits(id, symptoms, clinical_summary) VALUES (?, ?, ?)",
            (990, "polyuria,fatigue", "persistent polyuria with fatigue"),
        )
        conn.execute(
            """
            INSERT INTO disease_rankings(visit_id, disease_name, confidence, supporting_symptoms, clinical_basis)
            VALUES (?, ?, ?, ?, ?)
            """,
            (990, "diabetes", 0.84, "polyuria,fatigue", "metabolic pattern"),
        )
        conn.executemany(
            """
            INSERT INTO visit_vitals(visit_id, vital_name, value, unit, normal_min, normal_max)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (990, "Heart Rate", 115, "bpm", 60, 100),
                (990, "Temperature", 38.1, "C", 36.1, 37.2),
            ],
        )
        conn.commit()


def test_generate_and_download_report(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "clinicaliq.db"
    reports_dir = tmp_path / "reports"
    _seed_report_visit(db_file)

    from backend import db as db_module
    from backend.services import pdf_report_service

    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_file)
    monkeypatch.setattr(pdf_report_service, "_reports_dir", lambda: reports_dir)

    client = TestClient(app)
    generated = client.post("/api/v1/reports/generate/990")
    assert generated.status_code == 200
    payload = generated.json()
    report_path = Path(payload["report_path"])
    assert report_path.exists()

    download = client.get("/api/v1/reports/990")
    assert download.status_code == 200
    assert download.headers.get("content-type", "").startswith("application/pdf")

    with get_connection(str(db_file)) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM report_history WHERE visit_id = ?",
            (990,),
        ).fetchone()
    assert int(row["c"]) >= 1
