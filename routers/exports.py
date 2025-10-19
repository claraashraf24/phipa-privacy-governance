# routers/exports.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse
from io import StringIO
import csv
from database import get_db
import models
from anonymize import mask_name, mask_user, generalize_dob, hash_record_id

router = APIRouter(prefix="/export/anonymized", tags=["Anonymized Exports"])

@router.get("/patients")
def export_anonymized_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["patient_id", "pseudonym", "dob_year", "record_hash"])
    for p in patients:
        writer.writerow([
            p.id,
            mask_name(p.name),
            generalize_dob(p.dob or ""),
            hash_record_id(p.record_id or f"{p.id}")
        ])
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=anonymized_patients.csv"}
    )

@router.get("/logs")
def export_anonymized_logs(
    db: Session = Depends(get_db),
    since_minutes: int = 1440
):
    since_ts = datetime.utcnow() - timedelta(minutes=since_minutes)
    logs = db.query(models.AccessLog).filter(models.AccessLog.timestamp >= since_ts).order_by(models.AccessLog.timestamp.desc()).all()
    users = {u.id: u for u in db.query(models.User).all()}
    pats = {p.id: p for p in db.query(models.Patient).all()}

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp_utc", "user_pseudonym", "patient_pseudonym", "action", "authorized"])
    for lg in logs:
        u = users.get(lg.user_id)
        p = pats.get(lg.patient_id)
        user_pseudo = mask_user(u.name if u else f"User{lg.user_id}", u.role if u else "user")
        patient_pseudo = mask_name(p.name if p else f"Patient{lg.patient_id}")
        writer.writerow([
            lg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            user_pseudo,
            patient_pseudo,
            lg.action,
            "True" if lg.is_authorized else "False"
        ])
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=anonymized_access_logs.csv"}
    )
