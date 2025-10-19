# routers/reports.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from fastapi.responses import StreamingResponse
import models
from database import get_db
from routers.metrics import metrics_overview

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/audit")
def generate_audit_report(db: Session = Depends(get_db)):
    since_minutes = 1440
    metrics = metrics_overview(db, since_minutes)
    alerts = db.query(models.Alert).order_by(models.Alert.created_at.desc()).limit(10).all()

    # Chart
    fig, ax = plt.subplots(figsize=(6, 3))
    if metrics["series"]:
        df = metrics["series"]
        buckets = [r["bucket"] for r in df]
        auth = [r["authorized"] for r in df]
        breach = [r["breaches"] for r in df]
        ax.plot(buckets, auth, label="Authorized", color="green", marker="o")
        ax.plot(buckets, breach, label="Breaches", color="red", marker="o")
        ax.legend()
        ax.set_xlabel("Time")
        ax.set_ylabel("Access Count")
        ax.set_title("Access Trend (Last 24h)")
    else:
        ax.text(0.5, 0.5, "No Data", ha='center', va='center')

    img_buf = BytesIO()
    plt.tight_layout()
    plt.savefig(img_buf, format="png")
    plt.close(fig)
    img_buf.seek(0)

    # PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>PHIPA Audit Summary Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    summary_data = [
        ["Generated On", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Time Window", "Last 24 Hours"],
        ["Compliance (%)", f"{metrics['compliance_pct']} %"],
        ["Total Accesses", metrics["total_accesses"]],
        ["Authorized Accesses", metrics["authorized_accesses"]],
        ["Breaches", metrics["breaches"]],
        ["Open Alerts", metrics["open_alerts"]],
    ]
    summary_table = Table(summary_data, colWidths=[150, 200])
    summary_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Access Trend</b>", styles["Heading2"]))
    chart_path = "trend_chart.png"
    with open(chart_path, "wb") as f:
        f.write(img_buf.getvalue())
    elements.append(Image(chart_path, width=400, height=200))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Recent Breach Alerts</b>", styles["Heading2"]))
    if alerts:
        alert_rows = [["Date", "Message", "Resolved"]]
        for a in alerts:
            alert_rows.append([
                a.created_at.strftime("%Y-%m-%d %H:%M"),
                a.message,
                "Yes" if a.resolved else "No"
            ])
        alert_table = Table(alert_rows, colWidths=[100, 280, 60])
        alert_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        elements.append(alert_table)
    else:
        elements.append(Paragraph("No breach alerts recorded.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=PHIPA_Audit_Report.pdf"}
    )
