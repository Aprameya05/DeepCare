from __future__ import annotations

from fastapi import FastAPI

from backend.services.test_recommendation_service import generate_test_recommendations

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
