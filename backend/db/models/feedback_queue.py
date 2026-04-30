from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackQueueRecord:
    queue_id: str
    visit_id: int
    override_id: str
    feature_vector: str
    label_disease: str
    label_tests: str
    created_at: str
    consumed: bool
