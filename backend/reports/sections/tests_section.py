from __future__ import annotations

from collections import defaultdict

from reportlab.platypus import Paragraph, Spacer


def build_tests_section(styles, tests: list[dict]):
    grouped: dict[int, list[str]] = defaultdict(list)
    for row in tests:
        grouped[int(row["priority"])].append(str(row["test_name"]))
    flowables = [Paragraph("Recommended Tests by Priority", styles["SectionTitle"])]
    for priority in (1, 2, 3):
        items = grouped.get(priority, [])
        text = ", ".join(items) if items else "None"
        flowables.append(Paragraph(f"<b>Priority {priority}:</b> {text}", styles["BodyText"]))
    flowables.append(Spacer(1, 8))
    return flowables
