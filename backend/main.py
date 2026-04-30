from __future__ import annotations

from fastapi import FastAPI

from backend.ml.disease_severity import DEFAULT_BURDEN_PROFILE, DISEASE_BURDEN_PROFILES
from backend.services.burden_calculation_service import calculate_burden_score
from backend.services.test_recommendation_service import generate_test_recommendations
from backend.services.test_ordering_service import optimize_test_ordering

app = FastAPI(title="ClinicalIQ Recommendation API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/recommend/tests/{visit_id}")
def recommend_tests(visit_id: int) -> dict[str, object]:
    recommendations = generate_test_recommendations(visit_id)
    return {
        "visit_id": visit_id,
        "count": len(recommendations),
        "recommendations": recommendations,
    }


@app.post("/api/v1/calculate/burden/{visit_id}")
def calculate_burden(
    visit_id: int,
    country: str = "US",
    city: str | None = None,
    insurance_coverage: float = 0.0,
) -> dict[str, object]:
    ordering = optimize_test_ordering(
        visit_id=visit_id,
        country=country,
        city=city,
        insurance_coverage=insurance_coverage,
    )
    ordered_tests = ordering["ordered_tests"]
    if ordered_tests:
        dominant = sorted(
            ordered_tests,
            key=lambda item: float(item["disease_confidence"]),
            reverse=True,
        )[0]
        disease_key = str(dominant["source_disease"]).strip().lower().replace(" ", "_")
        profile = DISEASE_BURDEN_PROFILES.get(disease_key, DEFAULT_BURDEN_PROFILE)
    else:
        profile = DEFAULT_BURDEN_PROFILE

    burden = calculate_burden_score(
        visit_id=visit_id,
        total_cost=float(ordering["total_estimated_cost_usd"]),
        duration_days=profile.duration_days,
        frequency_count=profile.frequency_count,
        severity_score=profile.severity_score,
        ordering_snapshot=ordered_tests,
    )
    return {
        "visit_id": visit_id,
        "country": country,
        "city": city,
        "insurance_coverage": insurance_coverage,
        "ordering": ordering,
        "burden_result": burden,
    }
