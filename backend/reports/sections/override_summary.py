from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer


def build_override_summary(styles, overrides: list[dict]):
    flowables = [Paragraph("Doctor Override Summary", styles["SectionTitle"])]
    if not overrides:
        flowables.append(Paragraph("No doctor override recorded.", styles["BodyText"]))
    else:
        latest = overrides[0]
        flowables.append(Paragraph(f"<b>Confirmed Disease:</b> {latest.get('confirmed_disease', '')}", styles["BodyText"]))
        flowables.append(Paragraph(f"<b>Confirmed Tests:</b> {', '.join(latest.get('confirmed_tests', []))}", styles["BodyText"]))
        flowables.append(Paragraph(f"<b>Notes:</b> {latest.get('notes', '') or 'None'}", styles["BodyText"]))
    flowables.append(Spacer(1, 8))
    return flowables
