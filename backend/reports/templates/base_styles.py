from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

PRIMARY = colors.HexColor("#0a0f1e")
ACCENT = colors.HexColor("#0074D9")
WARNING_BG = colors.HexColor("#FFF4CC")
WARNING_BORDER = colors.HexColor("#E69500")
ABNORMAL_RED = colors.HexColor("#CC0000")


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            textColor=PRIMARY,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.gray,
            leading=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="WarningText",
            parent=styles["BodyText"],
            fontSize=10,
            textColor=colors.black,
            leading=13,
        )
    )
    return styles
