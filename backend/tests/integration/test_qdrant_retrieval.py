from __future__ import annotations

from backend.services import medcpt_service


def test_qdrant_pubmed_retrieval_endpoint_uses_retriever_when_available(client, monkeypatch) -> None:
    def fake_retrieve_pubmed(query, disease_tag=None, limit=5, score_threshold=0.0):
        return [
            {
                "id": "pubmed-1",
                "score": 0.91,
                "payload": {
                    "pmid": "12345",
                    "title": f"{disease_tag} evidence for {query}",
                    "year": 2024,
                    "disease_tag": disease_tag,
                },
            }
        ][:limit]

    monkeypatch.setattr(medcpt_service, "retrieve_pubmed_evidence", fake_retrieve_pubmed, raising=False)

    response = client.get("/api/v1/retrieval/pubmed?disease=diabetes&test=HbA1c&symptoms=polyuria")

    assert response.status_code == 200
    assert response.json()["results"][0]["pmid"] == "12345"
    assert response.json()["results"][0]["score"] == 0.91


def test_qdrant_similar_cases_endpoint_uses_retriever_when_available(client, seeded_visit: int, monkeypatch) -> None:
    def fake_retrieve_cases(summary, disease_tag=None, limit=5, score_threshold=0.0):
        return [
            {
                "id": "case-1",
                "score": 0.88,
                "payload": {
                    "case_id": "case-1",
                    "disease_tag": disease_tag,
                    "summary": summary,
                },
            }
        ][:limit]

    monkeypatch.setattr(medcpt_service, "retrieve_similar_cases", fake_retrieve_cases, raising=False)

    response = client.get(f"/api/v1/retrieval/similar-cases?visit_id={seeded_visit}")

    assert response.status_code == 200
    assert response.json()["results"][0]["case_id"] == "case-1"
    assert response.json()["results"][0]["score"] == 0.88
