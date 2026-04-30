from __future__ import annotations

from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from backend.reports.templates.base_styles import WARNING_BG, WARNING_BORDER


def build_uncertainty_box(styles, flags: list[str]):
    flags_text = ", ".join(sorted(set(flags))) if flags else "None detected"
    tbl = Table(
        [[Paragraph(f"<b>Uncertainty Flags:</b> {flags_text}", styles["WarningText"])]],
        colWidths=[520],
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WARNING_BG),
                ("BOX", (0, 0), (-1, -1), 1.2, WARNING_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ]
        )
    )
    return [tbl, Spacer(1, 10)]
