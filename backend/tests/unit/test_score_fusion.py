from __future__ import annotations

from backend.ml.score_fusion import fuse_disease_scores


def test_score_fusion_combines_sources_and_sorts_descending() -> None:
    fused = fuse_disease_scores(
        model_scores={"diabetes": 0.8, "cardiac": 0.4},
        rule_scores={"diabetes": 0.7, "thyroid": 0.5},
        retrieval_scores={"cardiac": 0.9},
    )

    assert fused[0]["disease_name"] == "diabetes"
    assert fused[0]["confidence"] > fused[1]["confidence"]
    assert {row["disease_name"] for row in fused} == {"diabetes", "cardiac", "thyroid"}


def test_score_fusion_clamps_invalid_scores() -> None:
    fused = fuse_disease_scores(
        model_scores={"diabetes": 2.0},
        rule_scores={"diabetes": -1.0},
        retrieval_scores={"diabetes": 1.0},
    )

    assert 0 <= fused[0]["confidence"] <= 1
