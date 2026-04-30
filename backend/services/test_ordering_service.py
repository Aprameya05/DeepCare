from __future__ import annotations

from collections import defaultdict
from typing import Any

from backend.ml.burden_constants import PRIORITY2_THRESHOLD
from backend.services.cost_estimation_service import get_test_cost
from backend.services.test_recommendation_service import generate_test_recommendations


def optimize_test_ordering(
    *,
    visit_id: int,
    country: str,
    city: str | None = None,
    insurance_coverage: float = 0.0,
    recommendations: list[dict[str, Any]] | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    # Phase 1: Materialize recommendations (or generate from ranked disease evidence).
    recommendation_rows = recommendations or generate_test_recommendations(visit_id, db_path=db_path)

    # Phase 2: Annotate each recommendation with insurance-aware net cost and pricing uncertainty.
    enriched: list[dict[str, Any]] = []
    uncertainty_flags: set[str] = set()
    for item in recommendation_rows:
        cost = get_test_cost(
            test_name=str(item["test_name"]),
            country=country,
            city=city,
            insurance_coverage=insurance_coverage,
            db_path=db_path,
        )
        if cost["uncertainty_type"]:
            uncertainty_flags.add(str(cost["uncertainty_type"]))
        enriched.append(
            {
                **item,
                "gross_cost_usd": cost["gross_cost_usd"],
                "net_cost_usd": cost["net_cost_usd"],
                "pricing_source": cost["pricing_source"],
                "pricing_uncertain": cost["pricing_uncertain"],
                "cost_uncertainty_type": cost["uncertainty_type"],
            }
        )

    # Phase 3: Optimize ordering by priority first, then lower net cost and lower uncertainty.
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        grouped[int(row["priority"])].append(row)

    ordered: list[dict[str, Any]] = []
    for priority in sorted(grouped):
        chunk = sorted(
            grouped[priority],
            key=lambda item: (
                1 if item["pricing_uncertain"] else 0,
                float(item["net_cost_usd"]),
                item["test_name"].lower(),
            ),
        )
        ordered.extend(chunk)

    # Phase 4: Burden-aware trim for optional tests.
    running_cost = 0.0
    for row in ordered:
        running_cost += float(row["net_cost_usd"])
        row["cumulative_net_cost_usd"] = round(running_cost, 2)
        row["defer_recommended"] = bool(
            int(row["priority"]) >= 3 and row["cumulative_net_cost_usd"] > PRIORITY2_THRESHOLD * 20
        )

    return {
        "visit_id": visit_id,
        "country": country,
        "city": city,
        "insurance_coverage": insurance_coverage,
        "ordered_tests": ordered,
        "total_estimated_cost_usd": round(sum(float(row["net_cost_usd"]) for row in ordered), 2),
        "uncertainty_flags": sorted(uncertainty_flags),
    }
