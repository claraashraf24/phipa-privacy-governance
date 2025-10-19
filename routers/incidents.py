# routers/incidents.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
import models
from database import get_db
from anonymize import summarize_incident

router = APIRouter(prefix="", tags=["Incident Summaries"])

@router.get("/incidents/summaries")
def incident_summaries(db: Session = Depends(get_db), limit: int = 10):
    alerts = db.query(models.Alert).order_by(models.Alert.created_at.desc()).limit(limit).all()
    summaries = []
    for a in alerts:
        window_start = a.created_at - timedelta(minutes=5)
        window_end = a.created_at + timedelta(minutes=5)
        log = db.query(models.AccessLog).filter(
            models.AccessLog.timestamp >= window_start,
            models.AccessLog.timestamp <= window_end,
            models.AccessLog.is_authorized == False
        ).order_by(models.AccessLog.timestamp.desc()).first()

        if log:
            u = db.query(models.User).filter_by(id=log.user_id).first()
            p = db.query(models.Patient).filter_by(id=log.patient_id).first()
            summary = summarize_incident(
                user_name=(u.name if u else f"User #{log.user_id}"),
                user_role=(u.role if u else "user"),
                patient_name=(p.name if p else f"Patient #{log.patient_id}"),
                action=log.action,
                reason=a.message.replace("Unauthorized access by", "Reason for"),
                when_utc=log.timestamp
            )
        else:
            summary = f"Alert at {a.created_at.strftime('%Y-%m-%d %H:%M UTC')}: {a.message}"

        summaries.append({"created_at": a.created_at, "summary": summary, "resolved": a.resolved})
    return summaries


@router.patch("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.resolved = True
    db.commit()
    return {"message": "Alert resolved", "alert_id": alert_id}
