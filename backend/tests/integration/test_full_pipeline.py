from __future__ import annotations

from backend.tests.factories import PatientFactory, SymptomsFactory, VitalsFactory, VisitFactory


def test_full_pipeline_patient_visit_to_pdf(client) -> None:
    patient_response = client.post("/api/v1/patients/", json=PatientFactory())
    assert patient_response.status_code == 200
    patient_id = patient_response.json()["id"]

    visit_response = client.post(
        "/api/v1/visits/",
        json=VisitFactory(patient_id=patient_id),
    )
    assert visit_response.status_code == 200
    visit_id = visit_response.json()["id"]

    vitals = VitalsFactory(visit_id=visit_id)
    assert client.post("/api/v1/vitals/", json=vitals).status_code == 200
    assert client.post(f"/api/v1/visits/{visit_id}/symptoms", json=SymptomsFactory()).status_code == 200

    prediction = client.post(f"/api/v1/predict/disease-ranking/{visit_id}")
    assert prediction.status_code == 200
    assert prediction.json()["predictions"]

    tests = client.post(f"/api/v1/recommend/tests/{visit_id}")
    assert tests.status_code == 200
    assert tests.json()["recommendations"]

    burden = client.post(f"/api/v1/calculate/burden/{visit_id}?country=US&insurance_coverage=0.8")
    assert burden.status_code == 200
    assert burden.json()["burden_result"]["category"] in {"Low", "Medium", "High"}

    override = client.post(
        f"/api/v1/doctor/override/{visit_id}",
        json={
            "doctor_id": "dr-e2e",
            "confirmed_disease": "diabetes",
            "confirmed_tests": ["HbA1c", "Fasting Plasma Glucose"],
            "notes": "End-to-end confirmation.",
        },
    )
    assert override.status_code == 200
    assert override.json()["accuracy"]["composite_score"] > 0

    report = client.post(f"/api/v1/reports/generate/{visit_id}?country=US&insurance_coverage=0.8")
    assert report.status_code == 200
    assert report.json()["download_url"] == f"/api/v1/reports/{visit_id}"

    download = client.get(f"/api/v1/reports/{visit_id}")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/pdf")
    assert download.content.startswith(b"%PDF")
