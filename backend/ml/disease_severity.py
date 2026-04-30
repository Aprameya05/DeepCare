from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiseaseBurdenProfile:
    duration_days: int
    frequency_count: int
    severity_score: float


# Chosen design: disease burden hints live in constants, separate from rule rows,
# to keep clinical test rules stable while allowing operational tuning independently.
DISEASE_BURDEN_PROFILES: dict[str, DiseaseBurdenProfile] = {
    "diabetes": DiseaseBurdenProfile(duration_days=14, frequency_count=2, severity_score=0.7),
    "cardiac": DiseaseBurdenProfile(duration_days=5, frequency_count=2, severity_score=0.9),
    "lung_cancer": DiseaseBurdenProfile(duration_days=21, frequency_count=3, severity_score=0.95),
    "thyroid": DiseaseBurdenProfile(duration_days=14, frequency_count=2, severity_score=0.55),
    "covid": DiseaseBurdenProfile(duration_days=10, frequency_count=1, severity_score=0.6),
    "pneumonia": DiseaseBurdenProfile(duration_days=10, frequency_count=2, severity_score=0.75),
    "breast_cancer": DiseaseBurdenProfile(duration_days=21, frequency_count=3, severity_score=0.9),
    "hepatitis_c": DiseaseBurdenProfile(duration_days=28, frequency_count=2, severity_score=0.8),
}

DEFAULT_BURDEN_PROFILE = DiseaseBurdenProfile(duration_days=14, frequency_count=1, severity_score=0.6)
