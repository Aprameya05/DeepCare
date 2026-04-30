from __future__ import annotations

from pathlib import Path

from backend.db import get_connection
from backend.services.burden_calculation_service import calculate_burden_score


def test_burden_formula_and_persistence(tmp_path: Path) -> None:
    db_file = tmp_path / "clinicaliq.db"
    result = calculate_burden_score(
        visit_id=9001,
        total_cost=500.0,
        duration_days=14,
        frequency_count=2,
        severity_score=0.7,
        db_path=str(db_file),
    )
    assert result["raw_burden"] == 9800.0
    assert 80.0 <= float(result["normalized_score"]) <= 90.0
    assert result["category"] in {"Medium", "High"}
    assert "total_cost=500.0" in str(result["explanation"])
    assert "duration_days=14" in str(result["explanation"])
    assert "frequency_count=2" in str(result["explanation"])
    assert "severity_score=0.7" in str(result["explanation"])

    with get_connection(str(db_file)) as conn:
        row = conn.execute(
            "SELECT raw_burden, normalized_score FROM burden_scores WHERE visit_id = ?",
            (9001,),
        ).fetchone()
    assert row is not None
    assert float(row["raw_burden"]) == 9800.0
