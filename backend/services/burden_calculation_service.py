from __future__ import annotations

import math
from typing import Any

from backend.db import ensure_core_tables, get_connection
from backend.ml.burden_constants import HIGH_BURDEN_SUFFIX, MAX_EXPECTED_BURDEN


def _categorize(score: float) -> str:
    if score < 35:
        return "Low"
    if score < 70:
        return "Medium"
    return "High"


def calculate_burden_score(
    *,
    visit_id: int,
    total_cost: float,
    duration_days: int,
    frequency_count: int,
    severity_score: float,
    ordering_snapshot: list[dict[str, Any]] | None = None,
    db_path: str | None = None,
) -> dict[str, object]:
    raw_burden = float(total_cost) * float(duration_days) * float(frequency_count) * float(severity_score)
    normalized_score = (
        math.log1p(max(raw_burden, 0.0)) / math.log1p(MAX_EXPECTED_BURDEN)
    ) * 100.0
    normalized_score = round(min(max(normalized_score, 0.0), 100.0), 2)
    category = _categorize(normalized_score)

    explanation = (
        f"Burden computed from total_cost={round(float(total_cost), 2)} USD, "
        f"duration_days={int(duration_days)}, frequency_count={int(frequency_count)}, "
        f"severity_score={round(float(severity_score), 2)}; "
        f"raw={round(raw_burden, 2)}, normalized={normalized_score}/100."
    )
    if category == "High":
        explanation += HIGH_BURDEN_SUFFIX

    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        conn.execute(
            """
            INSERT INTO burden_scores (
                visit_id,
                total_cost,
                duration_days,
                frequency_count,
                severity_score,
                raw_burden,
                normalized_score,
                category,
                explanation,
                ordering_snapshot
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visit_id,
                round(float(total_cost), 2),
                int(duration_days),
                int(frequency_count),
                round(float(severity_score), 4),
                round(raw_burden, 2),
                normalized_score,
                category,
                explanation,
                str(ordering_snapshot or []),
            ),
        )
        conn.commit()

    return {
        "visit_id": visit_id,
        "total_cost": round(float(total_cost), 2),
        "duration_days": int(duration_days),
        "frequency_count": int(frequency_count),
        "severity_score": round(float(severity_score), 4),
        "raw_burden": round(raw_burden, 2),
        "normalized_score": normalized_score,
        "category": category,
        "explanation": explanation,
    }
