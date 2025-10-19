# routers/metrics.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import func, case
import models
from database import get_db

router = APIRouter(prefix="", tags=["Metrics & Logs"])

# ------------------ Logs ------------------
@router.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    limit: int = 100,
    user_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    action: Optional[str] = None,
    since_minutes: int = 1440
):
    q = db.query(models.AccessLog)
    if user_id:
        q = q.filter(models.AccessLog.user_id == user_id)
    if patient_id:
        q = q.filter(models.AccessLog.patient_id == patient_id)
    if action:
        q = q.filter(models.AccessLog.action == action)
    since_ts = datetime.utcnow() - timedelta(minutes=since_minutes)
    q = q.filter(models.AccessLog.timestamp >= since_ts)
    q = q.order_by(models.AccessLog.timestamp.desc()).limit(limit)
    return q.all()


# ------------------ Alerts ------------------
@router.get("/alerts")
def get_alerts(
    db: Session = Depends(get_db),
    limit: int = 50,
    unresolved_only: bool = False
):
    q = db.query(models.Alert).order_by(models.Alert.created_at.desc())
    if unresolved_only:
        q = q.filter(models.Alert.resolved == False)
    return q.limit(limit).all()


# ------------------ Metrics Overview ------------------
@router.get("/metrics/overview")
def metrics_overview(
    db: Session = Depends(get_db),
    since_minutes: int = 1440
):
    since_ts = datetime.utcnow() - timedelta(minutes=since_minutes)
    total = db.query(models.AccessLog).filter(models.AccessLog.timestamp >= since_ts).count()
    authorized = db.query(models.AccessLog).filter(
        models.AccessLog.timestamp >= since_ts,
        models.AccessLog.is_authorized == True
    ).count()
    breaches = db.query(models.AccessLog).filter(
        models.AccessLog.timestamp >= since_ts,
        models.AccessLog.is_authorized == False
    ).count()
    alerts_open = db.query(models.Alert).filter(models.Alert.resolved == False).count()
    compliance = round((authorized / total) * 100, 2) if total else 100.0

    rows = db.query(
        func.strftime('%Y-%m-%d %H:00:00', models.AccessLog.timestamp).label("bucket"),
        func.sum(case((models.AccessLog.is_authorized == True, 1), else_=0)).label("authorized"),
        func.sum(case((models.AccessLog.is_authorized == False, 1), else_=0)).label("breaches")
    ).filter(models.AccessLog.timestamp >= since_ts
    ).group_by("bucket"
    ).order_by("bucket").all()

    series = [{"bucket": r[0], "authorized": int(r[1] or 0), "breaches": int(r[2] or 0)} for r in rows]

    return {
        "since_minutes": since_minutes,
        "total_accesses": total,
        "authorized_accesses": authorized,
        "breaches": breaches,
        "open_alerts": alerts_open,
        "compliance_pct": compliance,
        "series": series
    }


# ------------------ Consent Matrix ------------------
@router.get("/consent-matrix")
def consent_matrix(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    patients = db.query(models.Patient).all()
    consents = db.query(models.Consent).all()
    key = {(c.user_id, c.patient_id): c for c in consents}

    matrix = []
    for u in users:
        for p in patients:
            c = key.get((u.id, p.id))
            matrix.append({
                "user_id": u.id, "user_name": u.name, "role": u.role,
                "patient_id": p.id, "patient_name": p.name,
                "can_view": bool(c.can_view) if c else False,
                "can_edit": bool(c.can_edit) if c else False
            })
    return matrix
