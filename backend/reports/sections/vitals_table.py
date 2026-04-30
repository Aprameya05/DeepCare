from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from backend.reports.templates.base_styles import ABNORMAL_RED


def build_vitals_table(styles, vitals: list[dict]):
    rows = [["Vital", "Value", "Range", "Status"]]
    for vital in vitals:
        val = float(vital["value"])
        mn = vital.get("normal_min")
        mx = vital.get("normal_max")
        abnormal = (mn is not None and val < float(mn)) or (mx is not None and val > float(mx))
        status = "Abnormal" if abnormal else "Normal"
        rows.append(
            [
                vital["vital_name"],
                f"{val:g} {vital['unit']}",
                f"{mn:g}-{mx:g} {vital['unit']}" if mn is not None and mx is not None else "N/A",
                status,
            ]
        )
    tbl = Table(rows, colWidths=[150, 120, 150, 80])
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, "black"),
        ("BACKGROUND", (0, 0), (-1, 0), "#EEEEEE"),
    ]
    for idx, vital in enumerate(vitals, start=1):
        val = float(vital["value"])
        mn = vital.get("normal_min")
        mx = vital.get("normal_max")
        abnormal = (mn is not None and val < float(mn)) or (mx is not None and val > float(mx))
        if abnormal:
            style.append(("TEXTCOLOR", (0, idx), (-1, idx), ABNORMAL_RED))
    tbl.setStyle(TableStyle(style))
    return [Paragraph("Vitals", styles["SectionTitle"]), tbl, Spacer(1, 8)]
