from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from typing import Any

from backend.db import ensure_core_tables, get_connection

RETRIEVAL_BACKEND_PATH = Path(__file__).resolve().parents[2] / "optimizer" / "clinicaliq" / "backend"
if str(RETRIEVAL_BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(RETRIEVAL_BACKEND_PATH))

with contextlib.suppress(Exception):
    from retrieval.pubmed_retrieval import retrieve_pubmed_evidence  # type: ignore
with contextlib.suppress(Exception):
    from retrieval.similar_cases import retrieve_similar_cases  # type: ignore

FALLBACK_PUBMED: dict[str, list[dict[str, Any]]] = {
    "diabetes": [
        {"pmid": "PMID-1001", "title": "Diabetes Mellitus Symptoms and HbA1c Correlation", "year": 2021},
    ],
    "cardiac": [
        {"pmid": "PMID-1002", "title": "Cardiac Ischemia Early Warning Signals", "year": 2020},
    ],
    "lung_cancer": [
        {"pmid": "PMID-1003", "title": "Lung Cancer Screening with Imaging and Symptoms", "year": 2019},
    ],
    "thyroid": [
        {"pmid": "PMID-1004", "title": "Thyroid Dysfunction and Metabolic Fatigue Patterns", "year": 2022},
    ],
    "covid": [
        {"pmid": "PMID-1005", "title": "COVID-19 Symptom Clusters in Clinical Triage", "year": 2021},
    ],
}


def _normalize_tag(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def fetch_pubmed_evidence(
    *,
    disease: str,
    symptoms: str,
    top_recommended_test: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    query = f"{symptoms} {disease} {top_recommended_test}".strip()
    disease_tag = _normalize_tag(disease)
    retriever = globals().get("retrieve_pubmed_evidence")
    if retriever is None:
        hits = []
    else:
        try:
            hits = retriever(query, disease_tag=disease_tag, limit=limit, score_threshold=0.0)
        except Exception:
            hits = []
    if hits:
        return [
        {
            "pmid": str(item.get("payload", {}).get("pmid", "")),
            "title": str(item.get("payload", {}).get("title", "")),
            "year": item.get("payload", {}).get("year"),
            "disease_tag": str(item.get("payload", {}).get("disease_tag", "")),
            "score": round(float(item.get("score", 0.0)), 6),
        }
        for item in hits[:limit]
        ]
    fallback = FALLBACK_PUBMED.get(disease_tag, [])
    return [
        {
            "pmid": item["pmid"],
            "title": item["title"],
            "year": item["year"],
            "disease_tag": disease_tag,
            "score": 0.0,
        }
        for item in fallback[:limit]
    ]


def get_similar_cases_for_visit(
    *,
    visit_id: int,
    limit: int = 5,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    retriever = globals().get("retrieve_similar_cases")
    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        visit_row = conn.execute(
            "SELECT symptoms, clinical_summary FROM visits WHERE id = ?",
            (visit_id,),
        ).fetchone()
        top_disease = conn.execute(
            """
            SELECT disease_name
            FROM disease_rankings
            WHERE visit_id = ?
            ORDER BY confidence DESC
            LIMIT 1
            """,
            (visit_id,),
        ).fetchone()
        fallback_rows = conn.execute(
            """
            SELECT v.id AS visit_id, v.clinical_summary, dr.disease_name, dr.confidence
            FROM visits v
            LEFT JOIN disease_rankings dr ON dr.visit_id = v.id
            WHERE v.id != ?
            ORDER BY dr.confidence DESC
            LIMIT 25
            """,
            (visit_id,),
        ).fetchall()
    if not visit_row:
        return []
    summary = str(visit_row["clinical_summary"] or visit_row["symptoms"] or "").strip()
    if not summary:
        return []
    disease_tag = _normalize_tag(str(top_disease["disease_name"])) if top_disease else None
    hits: list[dict[str, Any]] = []
    if retriever is not None:
        try:
            hits = retriever(summary, disease_tag=disease_tag, limit=limit, score_threshold=0.0)
        except Exception:
            hits = []
    if hits:
        return [
        {
            "case_id": str(item.get("payload", {}).get("case_id", item.get("id"))),
            "score": round(float(item.get("score", 0.0)), 6),
            "disease_tag": str(item.get("payload", {}).get("disease_tag", "")),
            "summary": str(item.get("payload", {}).get("summary", "")),
        }
        for item in hits[:limit]
        ]

    query_tokens = set(summary.lower().split())
    scored: list[dict[str, Any]] = []
    for row in fallback_rows:
        other_summary = str(row["clinical_summary"] or "").strip()
        if not other_summary:
            continue
        other_tokens = set(other_summary.lower().split())
        overlap = len(query_tokens & other_tokens)
        if overlap == 0:
            continue
        score = overlap / max(len(query_tokens), 1)
        scored.append(
            {
                "case_id": f"visit-{row['visit_id']}",
                "score": round(score, 6),
                "disease_tag": _normalize_tag(str(row["disease_name"] or "")),
                "summary": other_summary,
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]
