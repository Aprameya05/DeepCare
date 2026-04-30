from __future__ import annotations

from pathlib import Path

from backend.db import get_connection
from backend.services.burden_calculation_service import calculate_burden_score


def test_burden_formula_persists_raw_and_normalized_scores(isolated_db_path: Path) -> None:
    result = calculate_burden_score(
        visit_id=401,
        total_cost=500.0,
        duration_days=14,
        frequency_count=2,
        severity_score=0.7,
        db_path=str(isolated_db_path),
    )

    assert result["raw_burden"] == 9800.0
    assert result["category"] in {"Low", "Medium", "High"}

    with get_connection(isolated_db_path) as conn:
        row = conn.execute(
            "SELECT raw_burden, normalized_score FROM burden_scores WHERE visit_id = ?",
            (401,),
        ).fetchone()
    assert float(row["raw_burden"]) == 9800.0
    assert float(row["normalized_score"]) == result["normalized_score"]
