from __future__ import annotations

from typing import Any

from backend.db import ensure_core_tables, get_connection
from backend.services.medcpt_service import fetch_pubmed_evidence


def get_disease_ranking_with_evidence(
    *,
    visit_id: int,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        visit_row = conn.execute(
            "SELECT symptoms FROM visits WHERE id = ?",
            (visit_id,),
        ).fetchone()
        symptom_text = str(visit_row["symptoms"]) if visit_row and visit_row["symptoms"] else ""

        top_test_row = conn.execute(
            """
            SELECT test_name
            FROM recommended_tests
            WHERE visit_id = ?
            ORDER BY priority ASC, disease_confidence DESC
            LIMIT 1
            """,
            (visit_id,),
        ).fetchone()
        top_test = str(top_test_row["test_name"]) if top_test_row else ""

        rows = conn.execute(
            """
            SELECT disease_name, confidence, supporting_symptoms, clinical_basis
            FROM disease_rankings
            WHERE visit_id = ?
            ORDER BY confidence DESC
            """,
            (visit_id,),
        ).fetchall()

    predictions: list[dict[str, Any]] = []
    for row in rows:
        disease_name = str(row["disease_name"])
        pubmed = fetch_pubmed_evidence(
            disease=disease_name,
            symptoms=str(row["supporting_symptoms"] or symptom_text),
            top_recommended_test=top_test,
            limit=3,
        )
        predictions.append(
            {
                "disease_name": disease_name,
                "confidence": float(row["confidence"]),
                "supporting_symptoms": str(row["supporting_symptoms"] or ""),
                "clinical_basis": str(row["clinical_basis"] or ""),
                "pubmed_evidence": pubmed,
            }
        )
    return predictions
