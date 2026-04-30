from __future__ import annotations

from pathlib import Path


def test_pdf_generation_endpoint_persists_report_history(client, isolated_db_path: Path, seeded_visit: int) -> None:
    client.post(f"/api/v1/recommend/tests/{seeded_visit}")
    client.post(f"/api/v1/calculate/burden/{seeded_visit}?country=US&insurance_coverage=0.8")

    response = client.post(f"/api/v1/reports/generate/{seeded_visit}?country=US&insurance_coverage=0.8")
    assert response.status_code == 200
    report_path = Path(response.json()["report_path"])
    assert report_path.exists()
    assert report_path.read_bytes().startswith(b"%PDF")

    download = client.get(f"/api/v1/reports/{seeded_visit}/download")
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF")
