from __future__ import annotations

from pathlib import Path

from backend.db import ensure_core_tables, get_connection
from backend.ml.uncertainty_engine import (
    CONFLICTING_SYMPTOMS,
    INCOMPLETE_HISTORY,
    LOW_MODEL_CONFIDENCE,
    MISSING_CRITICAL_VITALS,
    MULTIPLE_CLOSE_DIFFERENTIALS,
    OUT_OF_RANGE_VITALS,
    PRICING_UNAVAILABLE,
    TESTS_NOT_JUSTIFIED,
)
from backend.ml.test_reasoning import TESTS_NOT_JUSTIFIED as REASONING_TESTS_NOT_JUSTIFIED


def _seed_visit(conn, visit_id: int, symptoms: str, summary: str = "summary") -> None:
    conn.execute(
        "INSERT INTO visits(id, symptoms, clinical_summary) VALUES (?, ?, ?)",
        (visit_id, symptoms, summary),
    )


def _seed_vitals(conn, visit_id: int, spo2: float = 98, heart_rate: float = 82, systolic: float = 118) -> None:
    conn.executemany(
        """
        INSERT INTO visit_vitals(visit_id, vital_name, value, unit, normal_min, normal_max)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (visit_id, "Heart Rate", heart_rate, "bpm", 60, 100),
            (visit_id, "SpO2", spo2, "%", 95, 100),
            (visit_id, "Systolic BP", systolic, "mmHg", 90, 120),
        ],
    )


def _seed_rankings(conn, visit_id: int, rows: list[tuple[str, float]]) -> None:
    conn.executemany(
        "INSERT INTO disease_rankings(visit_id, disease_name, confidence) VALUES (?, ?, ?)",
        [(visit_id, disease, confidence) for disease, confidence in rows],
    )


def test_low_confidence_uncertainty_end_to_end(client, isolated_db_path: Path) -> None:
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        _seed_visit(conn, 610, "fatigue")
        _seed_vitals(conn, 610)
        _seed_rankings(conn, 610, [("diabetes", 0.25)])
        conn.commit()

    payload = client.post("/api/v1/predict/disease-ranking/610").json()
    assert LOW_MODEL_CONFIDENCE in payload["uncertainty_flags"]


def test_conflicting_symptoms_uncertainty_end_to_end(client, isolated_db_path: Path) -> None:
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        _seed_visit(conn, 611, "fever, denies fever")
        _seed_vitals(conn, 611)
        _seed_rankings(conn, 611, [("pneumonia", 0.70)])
        conn.commit()

    payload = client.post("/api/v1/predict/disease-ranking/611").json()
    assert CONFLICTING_SYMPTOMS in payload["uncertainty_flags"]


def test_missing_critical_vitals_uncertainty_end_to_end(client, isolated_db_path: Path) -> None:
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        _seed_visit(conn, 612, "polyuria")
        conn.execute(
            "INSERT INTO visit_vitals(visit_id, vital_name, value, unit) VALUES (?, ?, ?, ?)",
            (612, "Heart Rate", 80, "bpm"),
        )
        _seed_rankings(conn, 612, [("diabetes", 0.72)])
        conn.commit()

    payload = client.post("/api/v1/predict/disease-ranking/612").json()
    assert MISSING_CRITICAL_VITALS in payload["uncertainty_flags"]


def test_out_of_range_vitals_uncertainty_end_to_end(client, isolated_db_path: Path) -> None:
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        _seed_visit(conn, 613, "chest pain")
        _seed_vitals(conn, 613, heart_rate=132)
        _seed_rankings(conn, 613, [("cardiac", 0.82)])
        conn.commit()

    payload = client.post("/api/v1/predict/disease-ranking/613").json()
    assert OUT_OF_RANGE_VITALS in payload["uncertainty_flags"]


def test_incomplete_history_uncertainty_end_to_end(client, isolated_db_path: Path) -> None:
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        _seed_visit(conn, 614, "", "")
        _seed_vitals(conn, 614)
        _seed_rankings(conn, 614, [("diabetes", 0.70)])
        conn.commit()

    payload = client.post("/api/v1/predict/disease-ranking/614").json()
    assert INCOMPLETE_HISTORY in payload["uncertainty_flags"]


def test_close_differentials_uncertainty_end_to_end(client, isolated_db_path: Path) -> None:
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        _seed_visit(conn, 615, "fatigue")
        _seed_vitals(conn, 615)
        _seed_rankings(conn, 615, [("diabetes", 0.62), ("thyroid", 0.59)])
        conn.commit()

    payload = client.post("/api/v1/predict/disease-ranking/615").json()
    assert MULTIPLE_CLOSE_DIFFERENTIALS in payload["uncertainty_flags"]


def test_tests_not_justified_uncertainty_end_to_end(client, isolated_db_path: Path, seed_baseline) -> None:
    seed_baseline()
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        _seed_visit(conn, 616, "fatigue")
        _seed_vitals(conn, 616)
        _seed_rankings(conn, 616, [("cardiac", 0.30)])
        conn.commit()

    tests = client.post("/api/v1/recommend/tests/616").json()
    assert {item["uncertainty_type"] for item in tests["recommendations"]} == {REASONING_TESTS_NOT_JUSTIFIED}
    payload = client.post("/api/v1/predict/disease-ranking/616").json()
    assert TESTS_NOT_JUSTIFIED in payload["uncertainty_flags"]


def test_pricing_unavailable_uncertainty_end_to_end(client, isolated_db_path: Path, seed_baseline) -> None:
    seed_baseline()
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        _seed_visit(conn, 617, "polyuria, fatigue")
        _seed_vitals(conn, 617)
        _seed_rankings(conn, 617, [("diabetes", 0.82)])
        conn.commit()

    payload = client.post("/api/v1/calculate/burden/617?country=Atlantis").json()
    assert PRICING_UNAVAILABLE in payload["ordering"]["uncertainty_flags"]
