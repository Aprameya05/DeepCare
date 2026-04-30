from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer


def build_complaint(styles, visit: dict):
    symptoms = visit.get("symptoms") or "Not documented"
    summary = visit.get("clinical_summary") or "Not documented"
    return [
        Paragraph("Chief Complaint", styles["SectionTitle"]),
        Paragraph(f"<b>Symptoms:</b> {symptoms}", styles["BodyText"]),
        Paragraph(f"<b>Clinical Summary:</b> {summary}", styles["BodyText"]),
        Spacer(1, 8),
    ]
