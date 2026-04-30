from __future__ import annotations

import sys
from pathlib import Path

from qdrant_client.http import models

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from retrieval.collections import PUBMED_COLLECTION_NAME, ensure_retrieval_collections  # noqa: E402
from retrieval.medcpt_embedder import MedCPTEmbedder  # noqa: E402
from retrieval.pubmed_retrieval import retrieve_pubmed_evidence  # noqa: E402
from retrieval.qdrant_client import QdrantClientWrapper  # noqa: E402


def _build_pubmed_payloads() -> list[dict[str, str | int]]:
    return [
        {
            "title": "Diabetes Mellitus Symptoms and HbA1c Correlation",
            "abstract": "Fatigue, frequent urination, thirst and elevated HbA1c suggest diabetes progression.",
            "disease_tag": "diabetes",
            "pmid": "PMID-1001",
            "year": 2021,
        },
        {
            "title": "Cardiac Ischemia Early Warning Signals",
            "abstract": "Chest pain and dyspnea with elevated heart rate can indicate cardiac disease.",
            "disease_tag": "cardiac",
            "pmid": "PMID-1002",
            "year": 2020,
        },
        {
            "title": "Lung Cancer Screening with Imaging and Symptoms",
            "abstract": "Persistent cough, hemoptysis and weight loss may indicate lung cancer risk.",
            "disease_tag": "lung_cancer",
            "pmid": "PMID-1003",
            "year": 2019,
        },
        {
            "title": "Thyroid Dysfunction and Metabolic Fatigue Patterns",
            "abstract": "Weight fluctuation, fatigue, and TSH irregularity can suggest thyroid issues.",
            "disease_tag": "thyroid",
            "pmid": "PMID-1004",
            "year": 2022,
        },
        {
            "title": "COVID-19 Symptom Clusters in Clinical Triage",
            "abstract": "Fever, cough, breathlessness and oxygen desaturation align with COVID triage pathways.",
            "disease_tag": "covid",
            "pmid": "PMID-1005",
            "year": 2021,
        },
    ]


def main() -> None:
    ensure_retrieval_collections()
    embedder = MedCPTEmbedder()
    client = QdrantClientWrapper.get_client()

    payloads = _build_pubmed_payloads()
    texts = [f"{item['title']} {item['abstract']}" for item in payloads]
    vectors = embedder.embed_texts(texts)
    if not vectors:
        raise RuntimeError("Embedding generation returned no vectors.")
    if len(vectors[0]) != 768:
        raise RuntimeError(f"Embedding dimension mismatch: {len(vectors[0])}, expected 768.")

    points = [
        models.PointStruct(
            id=index + 1,
            vector=vectors[index],
            payload=payloads[index],
        )
        for index in range(len(payloads))
    ]
    client.upsert(
        collection_name=PUBMED_COLLECTION_NAME,
        points=points,
        wait=True,
    )

    results = retrieve_pubmed_evidence(
        "fatigue thirst frequent urination diabetes HbA1c",
        "diabetes",
        limit=5,
        score_threshold=0.0,
        embedder=embedder,
        client=client,
    )
    if not results:
        raise AssertionError("No PubMed retrieval results returned.")

    top_hit = results[0]
    top_score = float(top_hit["score"])
    top_tag = str(top_hit["payload"].get("disease_tag", ""))

    assert top_score > 0.7, f"Top score was {top_score}, expected > 0.7."
    assert top_tag == "diabetes", f"Top disease_tag was {top_tag}, expected diabetes."

    print("PASS")


if __name__ == "__main__":
    main()
