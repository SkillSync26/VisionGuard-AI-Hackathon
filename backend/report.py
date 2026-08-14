from pathlib import Path
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .database import get_detections, get_alerts, get_statistics

def create_csv(path: Path):
    rows = get_detections(limit=5000)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "timestamp", "object_class", "confidence",
            "source", "object_count", "track_id", "alert_status"
        ])
        writer.writeheader()
        writer.writerows(rows)
    return path

def create_pdf(path: Path):
    stats = get_statistics()
    alerts = get_alerts(limit=20)
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("AI Object Detection System Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Total detections: {stats['total_detections']}", styles["Normal"]),
        Paragraph(f"Average confidence: {stats['average_confidence']:.2%}", styles["Normal"]),
        Paragraph(f"Total alerts: {stats['total_alerts']}", styles["Normal"]),
        Spacer(1, 15),
        Paragraph("Detections by class", styles["Heading2"])
    ]

    data = [["Class", "Count"]]
    data += [[x["class"], x["count"]] for x in stats["by_class"]]
    table = Table(data, colWidths=[220, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 15))
    story.append(Paragraph("Recent alerts", styles["Heading2"]))

    alert_data = [["Time", "Type", "Message"]]
    alert_data += [
        [a["timestamp"], a["alert_type"], a["message"]] for a in alerts
    ]
    alert_table = Table(alert_data, colWidths=[100, 100, 260])
    alert_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(alert_table)
    doc.build(story)
    return path
