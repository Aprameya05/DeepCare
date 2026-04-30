from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer


def build_header(styles, visit: dict):
    return [
        Paragraph("NexioraDx AI-Assisted Clinical Report", styles["Title"]),
        Paragraph(f"Visit ID: {visit.get('id', 'N/A')}", styles["BodyText"]),
        Paragraph(f"Generated At: {visit.get('generated_at', 'N/A')}", styles["SmallMuted"]),
        Spacer(1, 8),
    ]
