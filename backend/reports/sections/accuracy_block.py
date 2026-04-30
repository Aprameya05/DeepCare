from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer


def build_accuracy_block(styles, accuracy: dict | None):
    flowables = [Paragraph("Accuracy Tracking", styles["SectionTitle"])]
    if not accuracy:
        flowables.append(Paragraph("No accuracy record available yet.", styles["BodyText"]))
    else:
        flowables.append(Paragraph(f"Composite Score: {float(accuracy.get('composite_score', 0.0)):.4f}", styles["BodyText"]))
        flowables.append(Paragraph(f"Top-1 Match: {float(accuracy.get('top1_match', 0.0)):.2f}", styles["BodyText"]))
        flowables.append(Paragraph(f"Top-3 Match: {float(accuracy.get('top3_match', 0.0)):.2f}", styles["BodyText"]))
        flowables.append(Paragraph(f"Test Overlap: {float(accuracy.get('test_overlap', 0.0)):.2f}", styles["BodyText"]))
    flowables.append(Spacer(1, 8))
    return flowables
