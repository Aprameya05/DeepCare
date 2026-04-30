from __future__ import annotations


def test_override_loop_records_feedback_accuracy_and_summary(client, seeded_visit: int) -> None:
    client.post(f"/api/v1/recommend/tests/{seeded_visit}")

    response = client.post(
        f"/api/v1/doctor/override/{seeded_visit}",
        json={
            "doctor_id": "dr-loop",
            "confirmed_disease": "diabetes",
            "confirmed_tests": ["HbA1c", "Lipid Panel"],
            "notes": "Confirmed by clinician.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["queue_id"]
    assert payload["accuracy"]["top1_match"] == 1.0

    overrides = client.get(f"/api/v1/doctor/overrides/{seeded_visit}").json()
    assert overrides["overrides"][0]["confirmed_disease"] == "diabetes"

    summary = client.get("/api/v1/accuracy/system/summary").json()
    assert summary["total_visits"] >= 1
    assert summary["avg_composite_score"] > 0
