from __future__ import annotations

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.platypus import Paragraph, Spacer


def build_burden_gauge(styles, burden: dict):
    score = float(burden.get("normalized_score", 0.0))
    category = burden.get("category", "Low")
    drawing = Drawing(520, 30)
    drawing.add(Rect(0, 10, 500, 12, strokeColor="#444444", fillColor="#FFFFFF"))
    drawing.add(Rect(0, 10, max(1.0, 500 * (score / 100.0)), 12, fillColor="#00A65A" if category == "Low" else "#E69500" if category == "Medium" else "#CC0000"))
    drawing.add(String(0, 0, f"Burden Score: {score:.2f}/100 ({category})", fontSize=10))
    return [Paragraph("Burden Gauge", styles["SectionTitle"]), drawing, Spacer(1, 8)]
