from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reportlab.platypus import Spacer

from backend.reports.sections import (
    build_accuracy_block,
    build_burden_gauge,
    build_complaint,
    build_cost_table,
    build_disclaimer,
    build_disease_ranking,
    build_header,
    build_next_steps,
    build_override_summary,
    build_pubmed_refs,
    build_tests_section,
    build_uncertainty_box,
    build_vitals_table,
)
from backend.reports.templates.base_styles import build_styles
from backend.reports.templates.report_layout import build_report


def generate_visit_pdf(
    *,
    output_path: Path,
    visit: dict[str, Any],
    uncertainty_flags: list[str],
    vitals: list[dict[str, Any]],
    disease_rankings: list[dict[str, Any]],
    recommended_tests: list[dict[str, Any]],
    total_cost: float,
    burden: dict[str, Any],
    pubmed_refs: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
    accuracy: dict[str, Any] | None,
) -> Path:
    styles = build_styles()
    visit_with_meta = dict(visit)
    visit_with_meta["generated_at"] = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    flowables = []
    # Ordered mandatory sections.
    flowables.extend(build_header(styles, visit_with_meta))
    flowables.extend(build_uncertainty_box(styles, uncertainty_flags))
    flowables.extend(build_complaint(styles, visit))
    flowables.extend(build_vitals_table(styles, vitals))
    flowables.extend(build_disease_ranking(styles, disease_rankings))
    flowables.extend(build_tests_section(styles, recommended_tests))
    flowables.extend(build_cost_table(styles, recommended_tests, total_cost))
    flowables.extend(build_burden_gauge(styles, burden))
    flowables.extend(build_pubmed_refs(styles, pubmed_refs))
    flowables.extend(build_override_summary(styles, overrides))
    flowables.extend(build_accuracy_block(styles, accuracy))
    flowables.extend(build_next_steps(styles))
    flowables.extend(build_disclaimer(styles))
    flowables.append(Spacer(1, 4))

    build_report(output_path, flowables)
    return output_path
