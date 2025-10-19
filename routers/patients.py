from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, schemas, crud
from database import get_db

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.post("/", response_model=schemas.PatientResponse)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    return crud.create_patient(db, patient)

@router.get("/", response_model=list[schemas.PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    return crud.get_patients(db)
