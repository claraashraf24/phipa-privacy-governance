from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, schemas, crud
from database import get_db

router = APIRouter(prefix="/consents", tags=["Consents"])

@router.post("/", response_model=schemas.ConsentResponse)
def create_consent(consent: schemas.ConsentCreate, db: Session = Depends(get_db)):
    return crud.create_consent(db, consent)

@router.get("/", response_model=list[schemas.ConsentResponse])
def get_consents(db: Session = Depends(get_db)):
    return crud.get_consents(db)
