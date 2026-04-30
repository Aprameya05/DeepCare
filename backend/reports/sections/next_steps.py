from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer


def build_next_steps(styles):
    return [
        Paragraph("Next Steps Timeline", styles["SectionTitle"]),
        Paragraph("0-24h: Validate high-priority tests and acute red flags.", styles["BodyText"]),
        Paragraph("24-72h: Review pending diagnostics and adjust test bundle if needed.", styles["BodyText"]),
        Paragraph("3-7 days: Reassess burden, disease ranking movement, and treatment planning.", styles["BodyText"]),
        Spacer(1, 8),
    ]
