from __future__ import annotations

from collections import defaultdict
from typing import Mapping

DEFAULT_WEIGHTS = {
    "model": 0.55,
    "rules": 0.30,
    "retrieval": 0.15,
}


def _clamp(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def fuse_disease_scores(
    *,
    model_scores: Mapping[str, float] | None = None,
    rule_scores: Mapping[str, float] | None = None,
    retrieval_scores: Mapping[str, float] | None = None,
    weights: Mapping[str, float] | None = None,
) -> list[dict[str, float | str]]:
    active_weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    buckets: dict[str, float] = defaultdict(float)
    sources = {
        "model": model_scores or {},
        "rules": rule_scores or {},
        "retrieval": retrieval_scores or {},
    }

    for source_name, scores in sources.items():
        source_weight = float(active_weights.get(source_name, 0.0))
        for disease, score in scores.items():
            normalized = str(disease).strip().lower().replace(" ", "_")
            if normalized:
                buckets[normalized] += _clamp(float(score)) * source_weight

    fused = [
        {"disease_name": disease, "confidence": round(_clamp(score), 6)}
        for disease, score in buckets.items()
    ]
    return sorted(fused, key=lambda row: (-float(row["confidence"]), str(row["disease_name"])))
