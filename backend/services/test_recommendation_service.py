from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from backend.db import ensure_core_tables, get_connection
from backend.ml.test_reasoning import (
    build_recommendation_reason,
    detect_tests_not_justified,
)


@dataclass(frozen=True)
class RankedDisease:
    disease_name: str
    confidence: float
    supporting_symptoms: str
    clinical_basis: str


@dataclass
class Recommendation:
    test_name: str
    priority: int
    source_disease: str
    disease_confidence: float
    clinical_reason: str
    guideline_reference: str
    recommendation_reason: str
    uncertainty_type: str | None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def _existing_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return [str(row["name"]) for row in rows]


def _resolve_column(columns: set[str], candidates: list[str], fallback: str = "''") -> str:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return fallback


def _fetch_visit_symptoms(conn: sqlite3.Connection, visit_id: int) -> str:
    tables = _existing_tables(conn)
    if "visits" not in tables:
        return ""
    columns = _table_columns(conn, "visits")
    id_col = _resolve_column(columns, ["id", "visit_id"], fallback="")
    symptoms_col = _resolve_column(columns, ["symptoms", "presenting_symptoms"], fallback="")
    if not id_col or not symptoms_col:
        return ""
    row = conn.execute(
        f"SELECT {symptoms_col} AS symptoms FROM visits WHERE {id_col} = ? LIMIT 1",
        (visit_id,),
    ).fetchone()
    return str(row["symptoms"]) if row and row["symptoms"] else ""


def _fetch_ranked_diseases(conn: sqlite3.Connection, visit_id: int) -> list[RankedDisease]:
    candidate_tables = [
        "disease_rankings",
        "ranked_diseases",
        "visit_disease_rankings",
        "diagnosis_rankings",
    ]
    tables = _existing_tables(conn)
    fallback_symptoms = _fetch_visit_symptoms(conn, visit_id)
    ranked: list[RankedDisease] = []

    for table_name in candidate_tables:
        if table_name not in tables:
            continue
        columns = _table_columns(conn, table_name)
        visit_col = _resolve_column(columns, ["visit_id", "visitId"], fallback="")
        disease_col = _resolve_column(columns, ["disease_name", "disease", "diagnosis"], fallback="")
        confidence_col = _resolve_column(columns, ["confidence", "score", "probability"], fallback="")
        symptoms_col = _resolve_column(
            columns,
            ["supporting_symptoms", "symptoms", "evidence_symptoms"],
            fallback="''",
        )
        basis_col = _resolve_column(columns, ["clinical_basis", "basis", "rationale"], fallback="''")
        if not visit_col or not disease_col or not confidence_col:
            continue

        rows = conn.execute(
            f"""
            SELECT
                {disease_col} AS disease_name,
                {confidence_col} AS confidence,
                {symptoms_col} AS supporting_symptoms,
                {basis_col} AS clinical_basis
            FROM {table_name}
            WHERE {visit_col} = ?
            ORDER BY confidence DESC
            """,
            (visit_id,),
        ).fetchall()
        for row in rows:
            ranked.append(
                RankedDisease(
                    disease_name=str(row["disease_name"]).strip(),
                    confidence=float(row["confidence"]),
                    supporting_symptoms=str(row["supporting_symptoms"] or fallback_symptoms),
                    clinical_basis=str(row["clinical_basis"] or ""),
                )
            )
        if ranked:
            break
    return ranked


def _fetch_rules_for_disease(conn: sqlite3.Connection, disease_name: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            disease_name,
            test_name,
            priority,
            clinical_reason,
            guideline_reference
        FROM disease_test_rules
        WHERE REPLACE(LOWER(disease_name), '_', ' ') = REPLACE(LOWER(?), '_', ' ')
        ORDER BY priority ASC, test_name ASC
        """,
        (disease_name,),
    ).fetchall()


def _upsert_recommendation(
    bucket: dict[str, Recommendation],
    candidate: Recommendation,
) -> None:
    existing = bucket.get(candidate.test_name.lower())
    if existing is None:
        bucket[candidate.test_name.lower()] = candidate
        return

    should_replace = False
    if candidate.priority < existing.priority:
        should_replace = True
    elif candidate.priority == existing.priority and candidate.disease_confidence > existing.disease_confidence:
        should_replace = True

    if should_replace:
        bucket[candidate.test_name.lower()] = candidate


def _persist_recommendations(
    conn: sqlite3.Connection,
    visit_id: int,
    recommendations: list[Recommendation],
) -> None:
    conn.execute("DELETE FROM recommended_tests WHERE visit_id = ?", (visit_id,))
    conn.executemany(
        """
        INSERT INTO recommended_tests (
            visit_id,
            test_name,
            priority,
            source_disease,
            disease_confidence,
            clinical_reason,
            guideline_reference,
            recommendation_reason,
            uncertainty_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                visit_id,
                item.test_name,
                item.priority,
                item.source_disease,
                item.disease_confidence,
                item.clinical_reason,
                item.guideline_reference,
                item.recommendation_reason,
                item.uncertainty_type,
            )
            for item in recommendations
        ],
    )
    conn.commit()


def generate_test_recommendations(
    visit_id: int,
    *,
    db_path: str | None = None,
    ranked_diseases: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        if ranked_diseases is None:
            ranking_objects = _fetch_ranked_diseases(conn, visit_id)
        else:
            ranking_objects = [
                RankedDisease(
                    disease_name=str(row.get("disease_name") or row.get("disease") or "").strip(),
                    confidence=float(row.get("confidence", row.get("score", 0.0))),
                    supporting_symptoms=str(row.get("supporting_symptoms", row.get("symptoms", ""))),
                    clinical_basis=str(row.get("clinical_basis", row.get("basis", ""))),
                )
                for row in ranked_diseases
            ]

        deduped: dict[str, Recommendation] = {}
        for disease in ranking_objects:
            if disease.confidence < 0.25 or not disease.disease_name:
                continue
            rules = _fetch_rules_for_disease(conn, disease.disease_name)
            for rule in rules:
                base_priority = int(rule["priority"])
                effective_priority = min(3, base_priority + (1 if disease.confidence < 0.45 else 0))
                reason = build_recommendation_reason(
                    disease_name=disease.disease_name,
                    disease_confidence=disease.confidence,
                    test_name=str(rule["test_name"]),
                    clinical_basis=disease.clinical_basis,
                    supporting_symptoms=disease.supporting_symptoms,
                    clinical_reason=str(rule["clinical_reason"]),
                    guideline_reference=str(rule["guideline_reference"]),
                    priority=effective_priority,
                )
                uncertainty_type = detect_tests_not_justified(
                    disease_confidence=disease.confidence,
                    supporting_symptoms=disease.supporting_symptoms,
                    clinical_basis=disease.clinical_basis,
                )
                _upsert_recommendation(
                    deduped,
                    Recommendation(
                        test_name=str(rule["test_name"]),
                        priority=effective_priority,
                        source_disease=disease.disease_name,
                        disease_confidence=disease.confidence,
                        clinical_reason=str(rule["clinical_reason"]),
                        guideline_reference=str(rule["guideline_reference"]),
                        recommendation_reason=reason,
                        uncertainty_type=uncertainty_type,
                    ),
                )

        ordered = sorted(
            deduped.values(),
            key=lambda item: (item.priority, -item.disease_confidence, item.test_name.lower()),
        )
        _persist_recommendations(conn, visit_id, ordered)
        return [
            {
                "test_name": item.test_name,
                "priority": item.priority,
                "source_disease": item.source_disease,
                "disease_confidence": item.disease_confidence,
                "clinical_reason": item.clinical_reason,
                "guideline_reference": item.guideline_reference,
                "recommendation_reason": item.recommendation_reason,
                "uncertainty_type": item.uncertainty_type,
            }
            for item in ordered
        ]
