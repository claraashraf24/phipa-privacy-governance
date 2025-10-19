# crud.py
from sqlalchemy.orm import Session
import models, schemas
from datetime import datetime

# ---------------- Users ----------------
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session):
    return db.query(models.User).all()


# ---------------- Patients ----------------
def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def get_patients(db: Session):
    return db.query(models.Patient).all()


# ---------------- Consents ----------------
def create_consent(db: Session, consent: schemas.ConsentCreate):
    db_consent = models.Consent(**consent.dict())
    db.add(db_consent)
    db.commit()
    db.refresh(db_consent)
    return db_consent

def get_consents(db: Session):
    return db.query(models.Consent).all()


# ---------------- Access Logs ----------------
def log_access(db: Session, log_data: schemas.AccessLogBase, authorized: bool):
    log = models.AccessLog(
        user_id=log_data.user_id,
        patient_id=log_data.patient_id,
        action=log_data.action,
        is_authorized=authorized,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
