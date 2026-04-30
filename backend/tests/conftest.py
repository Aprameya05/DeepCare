from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient

from backend.db import ensure_core_tables, get_connection
from backend.main import app
from backend.scripts.seed_country_pricing import _build_pricing_rows
from backend.scripts.seed_disease_test_rules import _build_rules


@pytest.fixture()
def isolated_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "clinicaliq-test.db"
    monkeypatch.setenv("CLINICALIQ_DB_PATH", str(db_path))
    monkeypatch.setenv("CLINICALIQ_REPORTS_DIR", str(tmp_path / "reports"))
    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
    return db_path


@pytest.fixture()
def seed_baseline(isolated_db_path: Path) -> Callable[[], None]:
    def _seed() -> None:
        with get_connection(isolated_db_path) as conn:
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
            conn.commit()

    return _seed


@pytest.fixture()
def client(isolated_db_path: Path, seed_baseline: Callable[[], None]) -> TestClient:
    _ = isolated_db_path
    seed_baseline()
    return TestClient(app)


@pytest.fixture()
def seeded_visit(isolated_db_path: Path, seed_baseline: Callable[[], None]) -> int:
    seed_baseline()
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        conn.execute(
            "INSERT INTO patients(id, name, age, gender, phone, medical_history) VALUES (?, ?, ?, ?, ?, ?)",
            (1, "Asha Rao", 54, "female", "555-0101", "family history of diabetes"),
        )
        conn.execute(
            """
            INSERT INTO visits(id, patient_id, chief_complaint, symptoms, clinical_summary, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                1201,
                1,
                "fatigue, polyuria, polydipsia",
                "fatigue, polyuria, polydipsia",
                "fatigue with classic hyperglycemia symptoms",
                "active",
            ),
        )
        conn.executemany(
            """
            INSERT INTO visit_vitals(visit_id, vital_name, value, unit, normal_min, normal_max)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (1201, "Heart Rate", 92, "bpm", 60, 100),
                (1201, "SpO2", 98, "%", 95, 100),
                (1201, "Systolic BP", 118, "mmHg", 90, 120),
                (1201, "Temperature", 37.0, "C", 36.1, 37.2),
            ],
        )
        conn.executemany(
            """
            INSERT INTO disease_rankings(visit_id, disease_name, confidence, supporting_symptoms, clinical_basis)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (1201, "diabetes", 0.88, "fatigue,polyuria,polydipsia", "classic hyperglycemia"),
                (1201, "thyroid", 0.42, "fatigue", "endocrine differential"),
                (1201, "cardiac", 0.28, "fatigue", "risk screen"),
            ],
        )
        conn.commit()
    return 1201
