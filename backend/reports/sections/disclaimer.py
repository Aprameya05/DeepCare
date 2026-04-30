from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer

DISCLAIMER_TEXT = (
    "This report is AI-assisted clinical decision support. All disease rankings, "
    "test recommendations, and burden scores are advisory. Final clinical decisions "
    "rest with the attending physician."
)


def build_disclaimer(styles):
    return [
        Paragraph("Disclaimer", styles["SectionTitle"]),
        Paragraph(DISCLAIMER_TEXT, styles["BodyText"]),
        Spacer(1, 8),
    ]
