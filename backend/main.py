from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI

from backend.db import ensure_core_tables, get_connection
from backend.ml.disease_severity import DEFAULT_BURDEN_PROFILE, DISEASE_BURDEN_PROFILES
from backend.services.disease_ranking_service import get_disease_ranking_with_evidence
from backend.services.doctor_override_service import process_doctor_override
from backend.services.burden_calculation_service import calculate_burden_score
from backend.services.medcpt_service import fetch_pubmed_evidence, get_similar_cases_for_visit
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


@app.post("/api/v1/doctor/override/{visit_id}")
def doctor_override(visit_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return process_doctor_override(
        visit_id=visit_id,
        doctor_id=str(payload.get("doctor_id", "doctor-unknown")),
        confirmed_disease=str(payload.get("confirmed_disease", "")),
        confirmed_tests=[str(item) for item in payload.get("confirmed_tests", [])],
        notes=str(payload.get("notes", "")),
    )


@app.get("/api/v1/doctor/overrides/{visit_id}")
def get_doctor_overrides(visit_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            """
            SELECT override_id, visit_id, doctor_id, confirmed_disease, confirmed_tests, notes, created_at
            FROM doctor_overrides
            WHERE visit_id = ?
            ORDER BY created_at DESC
            """,
            (visit_id,),
        ).fetchall()
    output: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        try:
            record["confirmed_tests"] = json.loads(str(record.get("confirmed_tests", "[]")))
        except json.JSONDecodeError:
            record["confirmed_tests"] = []
        output.append(record)
    return {"visit_id": visit_id, "overrides": output}


@app.get("/api/v1/accuracy/{visit_id}")
def get_accuracy_for_visit(visit_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        row = conn.execute(
            """
            SELECT visit_id, override_id, top1_match, top3_match, test_overlap, severity_delta,
                   burden_delta, composite_score, created_at
            FROM ai_accuracy_tracking
            WHERE visit_id = ?
            """,
            (visit_id,),
        ).fetchone()
    return {"visit_id": visit_id, "accuracy": dict(row) if row else None}


@app.get("/api/v1/accuracy/system/summary")
def get_accuracy_system_summary() -> dict[str, Any]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_visits,
                COALESCE(AVG(composite_score), 0) AS avg_composite_score,
                COALESCE(AVG(top1_match), 0) AS top1_hit_rate,
                COALESCE(AVG(top3_match), 0) AS top3_hit_rate
            FROM ai_accuracy_tracking
            """
        ).fetchone()
    return dict(row) if row else {"total_visits": 0, "avg_composite_score": 0, "top1_hit_rate": 0, "top3_hit_rate": 0}


@app.post("/predict/disease-ranking/{visit_id}")
@app.post("/api/v1/predict/disease-ranking/{visit_id}")
def predict_disease_ranking(visit_id: int) -> dict[str, Any]:
    predictions = get_disease_ranking_with_evidence(visit_id=visit_id)
    return {"visit_id": visit_id, "predictions": predictions}


@app.get("/api/v1/retrieval/pubmed")
def retrieval_pubmed(disease: str, test: str = "", symptoms: str = "") -> dict[str, Any]:
    evidence = fetch_pubmed_evidence(
        disease=disease,
        symptoms=symptoms,
        top_recommended_test=test,
        limit=3,
    )
    return {"disease": disease, "test": test, "results": evidence}


@app.get("/api/v1/retrieval/similar-cases")
def retrieval_similar_cases(visit_id: int) -> dict[str, Any]:
    cases = get_similar_cases_for_visit(visit_id=visit_id, limit=5)
    return {"visit_id": visit_id, "results": cases}
