from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.db import ensure_core_tables, get_connection
from backend.ml.disease_severity import DEFAULT_BURDEN_PROFILE, DISEASE_BURDEN_PROFILES
from backend.ml.score_fusion import fuse_disease_scores
from backend.ml.uncertainty_engine import detect_uncertainties
from backend.services.disease_ranking_service import get_disease_ranking_with_evidence
from backend.services.doctor_override_service import process_doctor_override
from backend.services.burden_calculation_service import calculate_burden_score
from backend.services.medcpt_service import fetch_pubmed_evidence, get_similar_cases_for_visit
from backend.services.test_recommendation_service import generate_test_recommendations
from backend.services.test_ordering_service import optimize_test_ordering
from backend.services.pdf_report_service import generate_pdf_report

app = FastAPI(title="NexioraDx Recommendation API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


VITAL_INPUT_MAP = {
    "heart_rate": ("Heart Rate", "bpm", 60, 100),
    "respiratory_rate": ("Respiratory Rate", "breaths/min", 12, 20),
    "temperature": ("Temperature", "C", 36.1, 37.2),
    "oxygen_saturation": ("SpO2", "%", 95, 100),
    "systolic_bp": ("Systolic BP", "mmHg", 90, 120),
    "diastolic_bp": ("Diastolic BP", "mmHg", 60, 80),
}

SYMPTOM_QUESTIONS = [
    {"id": "fatigue", "text": "Is the patient experiencing fatigue?", "type": "boolean"},
    {"id": "polyuria", "text": "Is the patient urinating more frequently than usual?", "type": "boolean"},
    {"id": "polydipsia", "text": "Is the patient reporting excessive thirst?", "type": "boolean"},
    {"id": "chest_pain", "text": "Does the patient report chest pain?", "type": "boolean"},
    {"id": "shortness_of_breath", "text": "Does the patient have shortness of breath?", "type": "boolean"},
    {"id": "cough", "text": "Is cough present?", "type": "boolean"},
    {"id": "fever", "text": "Is fever present?", "type": "boolean"},
    {"id": "pain_score", "text": "Rate the overall symptom burden.", "type": "scale"},
    {"id": "notes", "text": "Add any additional symptom context.", "type": "text"},
]


def _payload_visit_id(payload: dict[str, Any]) -> int:
    value = payload.get("visit_id") or payload.get("visitId") or payload.get("id")
    if value is None:
        raise HTTPException(status_code=422, detail="visit_id is required")
    return int(value)


def _ensure_seed_data(conn) -> None:
    rules_count = conn.execute("SELECT COUNT(*) AS c FROM disease_test_rules").fetchone()["c"]
    pricing_count = conn.execute("SELECT COUNT(*) AS c FROM country_test_pricing").fetchone()["c"]
    if int(rules_count) == 0:
        from backend.scripts.seed_disease_test_rules import _build_rules

        conn.executemany(
            """
            INSERT OR REPLACE INTO disease_test_rules(
                disease_name, test_name, priority, clinical_reason, guideline_reference
            ) VALUES (?, ?, ?, ?, ?)
            """,
            _build_rules(),
        )
    if int(pricing_count) == 0:
        from backend.scripts.seed_country_pricing import _build_pricing_rows

        conn.executemany(
            """
            INSERT OR REPLACE INTO country_test_pricing(
                country, city, test_name, price_usd, source_note
            ) VALUES (?, ?, ?, ?, ?)
            """,
            _build_pricing_rows(),
        )
    conn.commit()


def _serialize_patient(row) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "name": str(row["name"]),
        "age": int(row["age"]),
        "gender": str(row["gender"]),
        "phone": str(row["phone"] or ""),
        "medical_history": str(row["medical_history"] or ""),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


def _serialize_visit(row) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "patient_id": str(row["patient_id"] or ""),
        "chief_complaint": str(row["chief_complaint"] or row["clinical_summary"] or row["symptoms"] or ""),
        "notes": str(row["clinical_summary"] or ""),
        "status": str(row["status"] or "active"),
        "created_at": str(row["created_at"]),
    }


def _score_text_for_diseases(text: str) -> dict[str, float]:
    lowered = text.lower().replace("_", " ")
    keyword_weights = {
        "diabetes": {"polyuria": 0.26, "polydipsia": 0.26, "thirst": 0.18, "fatigue": 0.12, "glucose": 0.20},
        "cardiac": {"chest pain": 0.32, "pressure": 0.18, "shortness of breath": 0.16, "palpitations": 0.12},
        "pneumonia": {"cough": 0.22, "fever": 0.18, "sputum": 0.16, "shortness of breath": 0.14},
        "covid": {"fever": 0.15, "cough": 0.15, "loss of smell": 0.25, "shortness of breath": 0.10},
        "thyroid": {"weight loss": 0.22, "tremor": 0.20, "fatigue": 0.10, "heat intolerance": 0.18},
        "lung_cancer": {"hemoptysis": 0.28, "smoking": 0.24, "weight loss": 0.12, "cough": 0.12},
        "breast_cancer": {"breast lump": 0.35, "nipple discharge": 0.22, "breast pain": 0.12},
        "hepatitis_c": {"jaundice": 0.24, "iv drug": 0.22, "liver": 0.16, "fatigue": 0.08},
    }
    scores: dict[str, float] = {}
    for disease, weights in keyword_weights.items():
        score = sum(weight for keyword, weight in weights.items() if keyword in lowered)
        if score > 0:
            scores[disease] = min(0.95, 0.30 + score)
    if not scores:
        return {"diabetes": 0.32, "thyroid": 0.30, "cardiac": 0.28}
    return scores


def _upsert_rankings_for_visit(conn, visit_id: int, symptom_text: str, clinical_summary: str) -> None:
    model_scores = _score_text_for_diseases(f"{symptom_text} {clinical_summary}")
    rule_scores = {disease: min(score + 0.05, 1.0) for disease, score in model_scores.items()}
    retrieval_scores = {disease: score * 0.8 for disease, score in model_scores.items()}
    fused = fuse_disease_scores(
        model_scores=model_scores,
        rule_scores=rule_scores,
        retrieval_scores=retrieval_scores,
    )
    conn.execute("DELETE FROM disease_rankings WHERE visit_id = ?", (visit_id,))
    for row in fused[:5]:
        disease_name = str(row["disease_name"])
        confidence = float(row["confidence"])
        conn.execute(
            """
            INSERT INTO disease_rankings(
                visit_id, disease_name, confidence, supporting_symptoms, clinical_basis
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                visit_id,
                disease_name,
                confidence,
                symptom_text,
                "keyword-weighted clinical score fusion",
            ),
        )


def _visit_vitals(conn, visit_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT vital_name, value, unit, normal_min, normal_max
        FROM visit_vitals
        WHERE visit_id = ?
        """,
        (visit_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _recommendation_rows(conn, visit_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT test_name, priority, source_disease, disease_confidence, recommendation_reason, uncertainty_type
        FROM recommended_tests
        WHERE visit_id = ?
        ORDER BY priority ASC, disease_confidence DESC
        """,
        (visit_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _uncertainty_flags_for_visit(
    visit_id: int,
    *,
    predictions: list[dict[str, Any]] | None = None,
    recommendations: list[dict[str, Any]] | None = None,
    pricing_flags: list[str] | None = None,
) -> list[str]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        visit = conn.execute(
            "SELECT symptoms, clinical_summary FROM visits WHERE id = ?",
            (visit_id,),
        ).fetchone()
        ranking_rows = conn.execute(
            "SELECT disease_name, confidence FROM disease_rankings WHERE visit_id = ? ORDER BY confidence DESC",
            (visit_id,),
        ).fetchall()
        return detect_uncertainties(
            predictions=predictions or [dict(row) for row in ranking_rows],
            symptoms=str(visit["symptoms"] or "") if visit else "",
            clinical_summary=str(visit["clinical_summary"] or "") if visit else "",
            vitals=_visit_vitals(conn, visit_id),
            recommendations=recommendations or _recommendation_rows(conn, visit_id),
            pricing_flags=pricing_flags or [],
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/patients/")
@app.get("/api/v1/patients")
def list_patients() -> list[dict[str, Any]]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            "SELECT * FROM patients ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [_serialize_patient(row) for row in rows]


@app.get("/api/v1/patients/search")
def search_patients(q: str = "") -> list[dict[str, Any]]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            """
            SELECT *
            FROM patients
            WHERE LOWER(name) LIKE LOWER(?) OR phone LIKE ?
            ORDER BY created_at DESC, id DESC
            """,
            (f"%{q}%", f"%{q}%"),
        ).fetchall()
    return [_serialize_patient(row) for row in rows]


@app.post("/api/v1/patients/")
@app.post("/api/v1/patients")
def create_patient(payload: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        cursor = conn.execute(
            """
            INSERT INTO patients(name, age, gender, phone, medical_history)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(payload.get("name", "")).strip(),
                int(payload.get("age", 0)),
                str(payload.get("gender", "")).strip(),
                str(payload.get("phone", "") or ""),
                str(payload.get("medical_history", "") or ""),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _serialize_patient(row)


@app.get("/api/v1/patients/{patient_id}")
def get_patient(patient_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return _serialize_patient(row)


@app.get("/api/v1/patients/{patient_id}/visits")
def get_patient_visits(patient_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            """
            SELECT *
            FROM visits
            WHERE patient_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (patient_id,),
        ).fetchall()
    return [_serialize_visit(row) for row in rows]


@app.post("/api/v1/visits/")
@app.post("/api/v1/visits")
def create_visit(payload: dict[str, Any]) -> dict[str, Any]:
    patient_id = int(payload.get("patient_id") or payload.get("patientId") or 0)
    complaint = str(payload.get("chief_complaint") or payload.get("complaint") or "").strip()
    if not patient_id or not complaint:
        raise HTTPException(status_code=422, detail="patient_id and chief_complaint are required")
    with get_connection() as conn:
        ensure_core_tables(conn)
        _ensure_seed_data(conn)
        cursor = conn.execute(
            """
            INSERT INTO visits(patient_id, chief_complaint, symptoms, clinical_summary, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (patient_id, complaint, complaint, complaint),
        )
        visit_id = int(cursor.lastrowid)
        _upsert_rankings_for_visit(conn, visit_id, complaint, complaint)
        conn.commit()
        row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
    return _serialize_visit(row)


@app.get("/api/v1/visits/{visit_id}")
def get_visit(visit_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Visit not found")
    return _serialize_visit(row)


@app.post("/api/v1/vitals/")
@app.post("/api/v1/vitals")
def create_vitals(payload: dict[str, Any]) -> dict[str, Any]:
    visit_id = _payload_visit_id(payload)
    with get_connection() as conn:
        ensure_core_tables(conn)
        conn.execute("DELETE FROM visit_vitals WHERE visit_id = ?", (visit_id,))
        for key, (label, unit, normal_min, normal_max) in VITAL_INPUT_MAP.items():
            if payload.get(key) in (None, ""):
                continue
            conn.execute(
                """
                INSERT INTO visit_vitals(visit_id, vital_name, value, unit, normal_min, normal_max)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (visit_id, label, float(payload[key]), unit, normal_min, normal_max),
            )
        conn.commit()
    return {"visit_id": str(visit_id), "saved": True}


@app.get("/api/v1/symptoms/questions")
def get_symptom_questions(gender: str = "unknown") -> list[dict[str, Any]]:
    _ = gender
    return SYMPTOM_QUESTIONS


@app.post("/api/v1/visits/{visit_id}/symptoms")
def submit_symptoms(visit_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    selected = []
    notes = []
    for key, value in payload.items():
        if value is True:
            selected.append(key.replace("_", " "))
        elif value not in (False, None, ""):
            notes.append(f"{key.replace('_', ' ')}: {value}")
    symptom_text = ", ".join(selected + notes)
    with get_connection() as conn:
        ensure_core_tables(conn)
        _ensure_seed_data(conn)
        visit = conn.execute(
            "SELECT chief_complaint, clinical_summary FROM visits WHERE id = ?",
            (visit_id,),
        ).fetchone()
        if not visit:
            raise HTTPException(status_code=404, detail="Visit not found")
        summary = " ".join(
            item
            for item in [str(visit["chief_complaint"] or ""), symptom_text]
            if item
        )
        conn.execute(
            "UPDATE visits SET symptoms = ?, clinical_summary = ? WHERE id = ?",
            (symptom_text or str(visit["chief_complaint"] or ""), summary, visit_id),
        )
        _upsert_rankings_for_visit(conn, visit_id, symptom_text, summary)
        conn.commit()
    return {"visit_id": str(visit_id), "symptoms": symptom_text}


@app.post("/api/v1/recommend/tests/{visit_id}")
def recommend_tests(visit_id: int) -> dict[str, object]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        _ensure_seed_data(conn)
    recommendations = generate_test_recommendations(visit_id)
    return {
        "visit_id": visit_id,
        "count": len(recommendations),
        "recommendations": recommendations,
    }


@app.post("/api/v1/recommend/tests")
def recommend_tests_from_body(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = recommend_tests(_payload_visit_id(payload))
    return [
        {
            "test_name": str(item["test_name"]),
            "priority": int(item["priority"]),
            "reason": str(item.get("recommendation_reason") or item.get("clinical_reason") or ""),
        }
        for item in result["recommendations"]  # type: ignore[index]
    ]


@app.post("/api/v1/calculate/burden/{visit_id}")
def calculate_burden(
    visit_id: int,
    country: str = "US",
    city: str | None = None,
    insurance_coverage: float = 0.0,
) -> dict[str, object]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        _ensure_seed_data(conn)
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


@app.post("/api/v1/calculate/burden")
def calculate_burden_from_body(payload: dict[str, Any]) -> dict[str, Any]:
    visit_id = _payload_visit_id(payload)
    result = calculate_burden(
        visit_id=visit_id,
        country=str(payload.get("country", "US")),
        city=payload.get("city"),
        insurance_coverage=float(payload.get("insurance_coverage", 0.8)),
    )
    burden = result["burden_result"]  # type: ignore[index]
    ordering = result["ordering"]  # type: ignore[index]
    total = float(ordering["total_estimated_cost_usd"])  # type: ignore[index]
    coverage = float(result["insurance_coverage"])  # type: ignore[index]
    flags = _uncertainty_flags_for_visit(
        visit_id,
        recommendations=list(ordering.get("ordered_tests", [])),  # type: ignore[union-attr]
        pricing_flags=list(ordering.get("uncertainty_flags", [])),  # type: ignore[union-attr]
    )
    return {
        "level": burden["category"],  # type: ignore[index]
        "score": burden["normalized_score"],  # type: ignore[index]
        "uncertainty_flags": flags,
        "cost_breakdown": {
            "raw_cost": round(total / max(1.0 - coverage, 0.01), 2) if coverage else total,
            "insurance_reduction": round((total / max(1.0 - coverage, 0.01)) - total, 2) if coverage else 0.0,
            "net_cost": total,
        },
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


@app.post("/api/v1/override/")
@app.post("/api/v1/override")
def doctor_override_from_body(payload: dict[str, Any]) -> dict[str, Any]:
    visit_id = _payload_visit_id(payload)
    confirmed_disease = str(
        payload.get("confirmed_disease")
        or payload.get("alternative_diagnosis")
        or payload.get("diagnosis")
        or ""
    )
    confirmed_tests = [str(item) for item in payload.get("confirmed_tests", [])]
    if not confirmed_tests:
        with get_connection() as conn:
            ensure_core_tables(conn)
            rows = conn.execute(
                """
                SELECT test_name
                FROM recommended_tests
                WHERE visit_id = ?
                ORDER BY priority ASC, disease_confidence DESC
                LIMIT 2
                """,
                (visit_id,),
            ).fetchall()
        confirmed_tests = [str(row["test_name"]) for row in rows]
    return process_doctor_override(
        visit_id=visit_id,
        doctor_id=str(payload.get("doctor_id", "frontend-doctor")),
        confirmed_disease=confirmed_disease,
        confirmed_tests=confirmed_tests,
        notes=str(payload.get("notes") or payload.get("reason") or ""),
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


@app.get("/api/v1/dashboard/stats")
def dashboard_stats() -> dict[str, Any]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        patients = conn.execute("SELECT COUNT(*) AS c FROM patients").fetchone()["c"]
        active_visits = conn.execute("SELECT COUNT(*) AS c FROM visits WHERE status != 'completed'").fetchone()["c"]
        pending_tests = conn.execute("SELECT COUNT(*) AS c FROM recommended_tests WHERE doctor_confirmed = 0").fetchone()["c"]
        accuracy = conn.execute("SELECT COALESCE(AVG(composite_score), 0) AS score FROM ai_accuracy_tracking").fetchone()["score"]
    return {
        "total_patients": int(patients),
        "active_visits": int(active_visits),
        "average_accuracy": round(float(accuracy) * 100, 1),
        "pending_tests": int(pending_tests),
    }


@app.get("/api/v1/dashboard/disease-distribution")
def dashboard_disease_distribution() -> list[dict[str, Any]]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            """
            SELECT disease_name AS name, COUNT(*) AS value
            FROM disease_rankings
            GROUP BY disease_name
            ORDER BY value DESC
            LIMIT 8
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/v1/dashboard/pending-tests")
def dashboard_pending_tests() -> list[dict[str, Any]]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            """
            SELECT rt.test_name, rt.priority, COALESCE(p.name, 'Unknown') AS patient_name
            FROM recommended_tests rt
            LEFT JOIN visits v ON v.id = rt.visit_id
            LEFT JOIN patients p ON p.id = v.patient_id
            WHERE rt.doctor_confirmed = 0
            ORDER BY rt.priority ASC, rt.created_at DESC
            LIMIT 10
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/v1/dashboard/high-burden")
def dashboard_high_burden() -> list[dict[str, Any]]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            """
            SELECT COALESCE(p.name, 'Unknown') AS patient_name, b.total_cost AS net_cost, b.normalized_score AS score
            FROM burden_scores b
            LEFT JOIN visits v ON v.id = b.visit_id
            LEFT JOIN patients p ON p.id = v.patient_id
            ORDER BY b.normalized_score DESC, b.created_at DESC
            LIMIT 10
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/v1/dashboard/recent-overrides")
def dashboard_recent_overrides() -> list[dict[str, Any]]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            """
            SELECT
                confirmed_disease AS alternative_diagnosis,
                notes AS reason,
                created_at,
                (
                    SELECT disease_name
                    FROM disease_rankings dr
                    WHERE dr.visit_id = doctor_overrides.visit_id
                    ORDER BY confidence DESC
                    LIMIT 1
                ) AS original_prediction
            FROM doctor_overrides
            ORDER BY created_at DESC
            LIMIT 10
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/v1/accuracy/trend")
def dashboard_accuracy_trend() -> list[dict[str, Any]]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        rows = conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS date, ROUND(AVG(composite_score) * 100, 1) AS accuracy
            FROM ai_accuracy_tracking
            GROUP BY substr(created_at, 1, 10)
            ORDER BY date ASC
            LIMIT 30
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/predict/disease-ranking/{visit_id}")
@app.post("/api/v1/predict/disease-ranking/{visit_id}")
def predict_disease_ranking(visit_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        ensure_core_tables(conn)
        _ensure_seed_data(conn)
    predictions = get_disease_ranking_with_evidence(visit_id=visit_id)
    flags = _uncertainty_flags_for_visit(visit_id, predictions=predictions)
    return {
        "visit_id": visit_id,
        "predictions": [
            {
                **item,
                "disease": str(item["disease_name"]).replace("_", " ").title(),
                "confidence_percent": round(float(item["confidence"]) * 100),
            }
            for item in predictions
        ],
        "uncertainty_flags": flags,
    }


@app.post("/api/v1/predict/disease-ranking")
def predict_disease_ranking_from_body(payload: dict[str, Any]) -> dict[str, Any]:
    visit_id = _payload_visit_id(payload)
    result = predict_disease_ranking(visit_id)
    return {
        "visit_id": str(visit_id),
        "predictions": [
            {
                "disease": str(item.get("disease", item.get("disease_name", ""))),
                "disease_name": str(item.get("disease_name", "")),
                "confidence": int(item.get("confidence_percent", round(float(item.get("confidence", 0)) * 100))),
                "pubmed_evidence": [
                    str(ref.get("title") or ref.get("pmid") or ref)
                    for ref in item.get("pubmed_evidence", [])
                ],
            }
            for item in result["predictions"]
        ],
        "uncertainty_flags": result["uncertainty_flags"],
    }


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


@app.post("/api/v1/reports/generate/{visit_id}")
def generate_report(
    visit_id: int,
    country: str = "US",
    city: str | None = None,
    insurance_coverage: float = 0.0,
) -> dict[str, Any]:
    return generate_pdf_report(
        visit_id=visit_id,
        country=country,
        city=city,
        insurance_coverage=insurance_coverage,
    )


@app.post("/api/v1/reports/generate")
def generate_report_from_body(payload: dict[str, Any]) -> dict[str, Any]:
    return generate_report(
        visit_id=_payload_visit_id(payload),
        country=str(payload.get("country", "US")),
        city=payload.get("city"),
        insurance_coverage=float(payload.get("insurance_coverage", 0.8)),
    )


@app.get("/api/v1/reports/{visit_id}")
@app.get("/api/v1/reports/{visit_id}/download")
def get_report(visit_id: int):
    with get_connection() as conn:
        ensure_core_tables(conn)
        row = conn.execute(
            """
            SELECT report_path
            FROM report_history
            WHERE visit_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (visit_id,),
        ).fetchone()
    default_reports_dir = Path(os.getenv("CLINICALIQ_REPORTS_DIR") or Path(__file__).resolve().parents[1] / "clinicaliq" / "data" / "reports")
    path = Path(str(row["report_path"])) if row else (default_reports_dir / f"{visit_id}.pdf")
    if not path.exists():
        return {"visit_id": visit_id, "error": "Report not found"}
    return FileResponse(str(path), media_type="application/pdf", filename=f"{visit_id}.pdf")
