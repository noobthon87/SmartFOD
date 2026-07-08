"""Generate a printable FOD Clearance Record PDF."""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def build_clearance_pdf(record: dict, before_path: str, after_path: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("FOD Clearance Record", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))

    findings = record.get("findings", {})
    status = "CLEAR" if findings.get("clear") else "FLAGGED — REVIEW REQUIRED"
    status_color = colors.green if findings.get("clear") else colors.red

    meta_table = Table(
        [
            ["Job Card #", record.get("job_card", "")],
            ["Task Description", record.get("task_description", "")],
            ["Technician", record.get("technician", "")],
            ["Timestamp", record.get("timestamp", "")],
            ["Status", status],
        ],
        colWidths=[4 * cm, 12 * cm],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (1, 4), (1, 4), status_color),
                ("FONTNAME", (1, 4), (1, 4), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 0.75 * cm))

    story.append(Paragraph("AI Assessment Summary", styles["Heading2"]))
    story.append(Paragraph(findings.get("summary", "N/A"), styles["BodyText"]))
    story.append(Spacer(1, 0.5 * cm))

    flagged_items = findings.get("flagged_items", [])
    if flagged_items:
        story.append(Paragraph("Flagged Items", styles["Heading2"]))
        rows = [["Item", "Risk", "Location"]]
        for item in flagged_items:
            rows.append([item.get("item", ""), item.get("risk", ""), item.get("location", "")])
        items_table = Table(rows, colWidths=[7 * cm, 3 * cm, 6 * cm])
        items_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 0.5 * cm))
    else:
        story.append(Paragraph("No FOD items flagged.", styles["BodyText"]))
        story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Before / After Photos", styles["Heading2"]))
    try:
        img_table = Table(
            [[Image(before_path, width=7 * cm, height=5.25 * cm), Image(after_path, width=7 * cm, height=5.25 * cm)]],
        )
        story.append(img_table)
    except Exception:
        story.append(Paragraph("(Images unavailable)", styles["BodyText"]))

    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            f"Signed off by: {record.get('technician', '')} &nbsp;&nbsp;&nbsp; Date: {record.get('timestamp', '')}",
            styles["BodyText"],
        )
    )

    doc.build(story)
    return buffer.getvalue()
