from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer


def build_pubmed_refs(styles, refs: list[dict]):
    flowables = [Paragraph("Top PubMed References", styles["SectionTitle"])]
    if not refs:
        flowables.append(Paragraph("No references available.", styles["BodyText"]))
    for idx, ref in enumerate(refs[:3], start=1):
        flowables.append(
            Paragraph(
                f"{idx}. {ref.get('title', 'Unknown')} "
                f"(PMID: {ref.get('pmid', 'N/A')}, Score: {float(ref.get('score', 0.0)):.2f})",
                styles["BodyText"],
            )
        )
    flowables.append(Spacer(1, 8))
    return flowables
