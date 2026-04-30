from __future__ import annotations

# Normalization cap for log-scaled burden score.
MAX_EXPECTED_BURDEN = 50_000.0

# Ordering threshold used by optimizer to separate "higher concern" tests.
PRIORITY2_THRESHOLD = 65.0

HIGH_BURDEN_SUFFIX = (
    " High burden indicates meaningful financial and follow-up strain; "
    "consider phased ordering, coverage confirmation, or alternative diagnostics."
)
