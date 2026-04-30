from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import models

from .qdrant_client import QdrantClientWrapper

PUBMED_COLLECTION_NAME = "pubmed_evidence"
CASES_COLLECTION_NAME = "patient_cases"
VECTOR_SIZE = 768


def _has_collection(client: QdrantClient, collection_name: str) -> bool:
    existing = client.get_collections().collections
    return any(item.name == collection_name for item in existing)


def _create_collection_if_missing(client: QdrantClient, collection_name: str) -> bool:
    if _has_collection(client, collection_name):
        return False

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )
    return True


def _configure_pubmed_payload_schema(client: QdrantClient) -> None:
    client.create_payload_index(
        collection_name=PUBMED_COLLECTION_NAME,
        field_name="disease_tag",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=PUBMED_COLLECTION_NAME,
        field_name="year",
        field_schema=models.PayloadSchemaType.INTEGER,
    )


def _configure_case_payload_schema(client: QdrantClient) -> None:
    client.create_payload_index(
        collection_name=CASES_COLLECTION_NAME,
        field_name="disease_tag",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=CASES_COLLECTION_NAME,
        field_name="case_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )


def ensure_retrieval_collections(client: QdrantClient | None = None) -> dict[str, bool]:
    qdrant = client or QdrantClientWrapper.get_client()
    pubmed_created = _create_collection_if_missing(qdrant, PUBMED_COLLECTION_NAME)
    cases_created = _create_collection_if_missing(qdrant, CASES_COLLECTION_NAME)

    _configure_pubmed_payload_schema(qdrant)
    _configure_case_payload_schema(qdrant)

    return {
        PUBMED_COLLECTION_NAME: pubmed_created,
        CASES_COLLECTION_NAME: cases_created,
    }
