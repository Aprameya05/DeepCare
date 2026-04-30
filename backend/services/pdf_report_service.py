from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from backend.db import ensure_core_tables, get_connection
from backend.ml.disease_severity import DEFAULT_BURDEN_PROFILE, DISEASE_BURDEN_PROFILES
from backend.ml.uncertainty_engine import detect_uncertainties
from backend.reports.pdf_generator import generate_visit_pdf
from backend.services.burden_calculation_service import calculate_burden_score
from backend.services.disease_ranking_service import get_disease_ranking_with_evidence
from backend.services.test_ordering_service import optimize_test_ordering


def _reports_dir() -> Path:
    configured = os.getenv("CLINICALIQ_REPORTS_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "clinicaliq" / "data" / "reports"


def _fetch_vitals(conn, visit_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT vital_name, value, unit, normal_min, normal_max
        FROM visit_vitals
        WHERE visit_id = ?
        """,
        (visit_id,),
    ).fetchall()
    if rows:
        return [dict(row) for row in rows]
    return [
        {"vital_name": "Heart Rate", "value": 112, "unit": "bpm", "normal_min": 60, "normal_max": 100},
        {"vital_name": "SpO2", "value": 95, "unit": "%", "normal_min": 95, "normal_max": 100},
        {"vital_name": "Systolic BP", "value": 142, "unit": "mmHg", "normal_min": 90, "normal_max": 120},
        {"vital_name": "Temperature", "value": 37.8, "unit": "C", "normal_min": 36.1, "normal_max": 37.2},
    ]


def _latest_burden(conn, visit_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT normalized_score, category, explanation
        FROM burden_scores
        WHERE visit_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (visit_id,),
    ).fetchone()
    return dict(row) if row else None


def generate_pdf_report(
    *,
    visit_id: int,
    country: str = "US",
    city: str | None = None,
    insurance_coverage: float = 0.0,
    db_path: str | None = None,
) -> dict[str, Any]:
    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        visit_row = conn.execute(
            "SELECT id, symptoms, clinical_summary FROM visits WHERE id = ?",
            (visit_id,),
        ).fetchone()
        if not visit_row:
            raise ValueError(f"Visit {visit_id} not found.")
        visit = dict(visit_row)

    ordering = optimize_test_ordering(
        visit_id=visit_id,
        country=country,
        city=city,
        insurance_coverage=insurance_coverage,
        db_path=db_path,
    )
    rankings = get_disease_ranking_with_evidence(visit_id=visit_id, db_path=db_path)

    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        vitals = _fetch_vitals(conn, visit_id)
        overrides_rows = conn.execute(
            """
            SELECT override_id, doctor_id, confirmed_disease, confirmed_tests, notes, created_at
            FROM doctor_overrides
            WHERE visit_id = ?
            ORDER BY created_at DESC
            """,
            (visit_id,),
        ).fetchall()
        overrides: list[dict[str, Any]] = []
        for row in overrides_rows:
            record = dict(row)
            try:
                record["confirmed_tests"] = json.loads(str(record.get("confirmed_tests", "[]")))
            except json.JSONDecodeError:
                record["confirmed_tests"] = []
            overrides.append(record)

        accuracy_row = conn.execute(
            """
            SELECT top1_match, top3_match, test_overlap, severity_delta, burden_delta, composite_score
            FROM ai_accuracy_tracking
            WHERE visit_id = ?
            """,
            (visit_id,),
        ).fetchone()
        accuracy = dict(accuracy_row) if accuracy_row else None

        burden = _latest_burden(conn, visit_id)
        if burden is None:
            top = ordering["ordered_tests"][0] if ordering["ordered_tests"] else None
            disease_key = str(top["source_disease"]).strip().lower().replace(" ", "_") if top else ""
            profile = DISEASE_BURDEN_PROFILES.get(disease_key, DEFAULT_BURDEN_PROFILE)
            burden = calculate_burden_score(
                visit_id=visit_id,
                total_cost=float(ordering["total_estimated_cost_usd"]),
                duration_days=profile.duration_days,
                frequency_count=profile.frequency_count,
                severity_score=profile.severity_score,
                ordering_snapshot=ordering["ordered_tests"],
                db_path=db_path,
            )

    pubmed_refs = []
    for prediction in rankings:
        pubmed_refs.extend(prediction.get("pubmed_evidence", []))
    unique_refs = []
    seen_pmids = set()
    for ref in pubmed_refs:
        pmid = str(ref.get("pmid", ""))
        if pmid and pmid not in seen_pmids:
            seen_pmids.add(pmid)
            unique_refs.append(ref)

    report_path = _reports_dir() / f"{visit_id}.pdf"
    uncertainty_flags = detect_uncertainties(
        predictions=rankings,
        symptoms=str(visit.get("symptoms", "")),
        clinical_summary=str(visit.get("clinical_summary", "")),
        vitals=vitals,
        recommendations=ordering["ordered_tests"],
        pricing_flags=list(ordering.get("uncertainty_flags", [])),
    )
    generate_visit_pdf(
        output_path=report_path,
        visit=visit,
        uncertainty_flags=uncertainty_flags,
        vitals=vitals,
        disease_rankings=rankings,
        recommended_tests=ordering["ordered_tests"],
        total_cost=float(ordering["total_estimated_cost_usd"]),
        burden=burden,
        pubmed_refs=unique_refs[:3],
        overrides=overrides,
        accuracy=accuracy,
    )

    download_url = f"/api/v1/reports/{visit_id}"
    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        conn.execute(
            """
            INSERT INTO report_history (visit_id, report_path, download_url)
            VALUES (?, ?, ?)
            """,
            (visit_id, str(report_path), download_url),
        )
        conn.commit()

    return {
        "visit_id": visit_id,
        "report_path": str(report_path),
        "download_url": download_url,
    }
