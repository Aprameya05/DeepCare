from __future__ import annotations

from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.platypus import Paragraph, Spacer


def _confidence_bar(label: str, confidence: float) -> Drawing:
    width = 360
    height = 16
    drawing = Drawing(width + 150, height + 8)
    drawing.add(String(0, 5, f"{label} ({confidence * 100:.0f}%)", fontSize=9))
    drawing.add(Rect(140, 3, width, 10, strokeColor=colors.gray, fillColor=colors.white))
    drawing.add(Rect(140, 3, width * max(0.0, min(1.0, confidence)), 10, fillColor=colors.HexColor("#0074D9")))
    return drawing


def build_disease_ranking(styles, rankings: list[dict]):
    flowables = [Paragraph("Disease Ranking", styles["SectionTitle"])]
    for row in rankings:
        flowables.append(_confidence_bar(row["disease_name"], float(row["confidence"])))
        flowables.append(Spacer(1, 3))
    flowables.append(Spacer(1, 8))
    return flowables
