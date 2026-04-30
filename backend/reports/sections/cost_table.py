from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


def build_cost_table(styles, tests: list[dict], total_cost: float):
    rows = [["Test", "Priority", "Net Cost (USD)"]]
    for row in tests:
        rows.append([row["test_name"], str(row["priority"]), f"{float(row.get('net_cost_usd', 0.0)):.2f}"])
    rows.append(["Total", "", f"{total_cost:.2f}"])
    tbl = Table(rows, colWidths=[280, 80, 120])
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, "black"),
                ("BACKGROUND", (0, 0), (-1, 0), "#EEEEEE"),
                ("BACKGROUND", (0, -1), (-1, -1), "#F5F5F5"),
            ]
        )
    )
    return [Paragraph("Cost Breakdown", styles["SectionTitle"]), tbl, Spacer(1, 8)]
