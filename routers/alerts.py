# routers/alerts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas, crud
from database import get_db

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# ------------------ List Alerts ------------------
@router.get("/")
def get_alerts(
    db: Session = Depends(get_db),
    limit: int = 50,
    unresolved_only: bool = False
):
    """
    Returns a list of alerts (optionally unresolved only).
    """
    q = db.query(models.Alert).order_by(models.Alert.created_at.desc())
    if unresolved_only:
        q = q.filter(models.Alert.resolved == False)
    return q.limit(limit).all()


# ------------------ Create Alert (for testing/demo) ------------------
@router.post("/")
def create_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)):
    """
    Allows manual alert creation (for testing or demo purposes).
    """
    db_alert = models.Alert(
        user_id=alert.user_id,
        patient_id=alert.patient_id,
        message=alert.message,
        created_at=datetime.utcnow(),
        resolved=False
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


# ------------------ Resolve Alert ------------------
@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Marks a specific alert as resolved.
    """
    alert = db.query(models.Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.resolved = True
    db.commit()
    return {"message": "Alert resolved", "alert_id": alert_id}
