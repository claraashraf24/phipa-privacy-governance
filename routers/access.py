from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, crud
from alerts_utils import send_breach_alert, log_alert


router = APIRouter(prefix="/access", tags=["Access Control"])

@router.post("/")
def access_patient_record(log: schemas.AccessLogBase, db: Session = Depends(get_db)):
    consent = db.query(models.Consent).filter_by(
        patient_id=log.patient_id, user_id=log.user_id
    ).first()

    authorized = False
    reason = ""

    if consent:
        if log.action == "view" and consent.can_view:
            authorized = True
        elif log.action == "edit" and consent.can_edit:
            authorized = True
        else:
            reason = "User lacks required permission."
    else:
        reason = "No consent exists for this user and patient."

    crud.log_access(db, log, authorized)

    if not authorized:
        user = db.query(models.User).filter_by(id=log.user_id).first()
        patient = db.query(models.Patient).filter_by(id=log.patient_id).first()
        log_alert(log.user_id, log.patient_id, reason, db=db)
        send_breach_alert(
            user_name=user.name if user else f"User #{log.user_id}",
            patient_name=patient.name if patient else f"Patient #{log.patient_id}",
            reason=reason
        )
        raise HTTPException(status_code=403, detail=f"Access denied. {reason}")

    return {"message": "Access granted", "authorized": True}
