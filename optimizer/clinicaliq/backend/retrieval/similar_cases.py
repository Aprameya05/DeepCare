from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from .collections import CASES_COLLECTION_NAME
from .medcpt_embedder import MedCPTEmbedder
from .qdrant_client import QdrantClientWrapper


def retrieve_similar_cases(
    case_summary: str,
    disease_tag: str | None = None,
    limit: int = 5,
    score_threshold: float = 0.0,
    embedder: MedCPTEmbedder | None = None,
    client: QdrantClient | None = None,
) -> list[dict[str, Any]]:
    if not case_summary.strip():
        return []

    qdrant = client or QdrantClientWrapper.get_client()
    encoder = embedder or MedCPTEmbedder()
    query_vector = encoder.embed_text(case_summary)

    query_filter = None
    if disease_tag:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="disease_tag",
                    match=models.MatchValue(value=disease_tag),
                )
            ]
        )

    hits = qdrant.search(
        collection_name=CASES_COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=query_filter,
        with_payload=True,
        limit=limit,
        score_threshold=score_threshold,
    )

    return [
        {
            "id": hit.id,
            "score": hit.score,
            "payload": hit.payload or {},
        }
        for hit in hits
    ]
