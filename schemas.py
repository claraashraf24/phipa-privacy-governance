# schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ----------------- Alert Schemas -----------------
class AlertBase(BaseModel):
    user_id: int
    patient_id: int
    message: str


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    created_at: datetime
    resolved: bool

    class Config:
        from_attributes = True  # (was orm_mode=True in Pydantic v1)


class UserBase(BaseModel):
    name: str
    role: str
    email: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    class Config:
        orm_mode = True


class PatientBase(BaseModel):
    name: str
    dob: str
    record_id: str

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: int
    class Config:
        orm_mode = True


class ConsentBase(BaseModel):
    patient_id: int
    user_id: int
    can_view: bool = True
    can_edit: bool = False

class ConsentCreate(ConsentBase):
    pass

class ConsentResponse(ConsentBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True


class AccessLogBase(BaseModel):
    user_id: int
    patient_id: int
    action: str

class AccessLogResponse(AccessLogBase):
    id: int
    timestamp: datetime
    is_authorized: bool
    class Config:
        orm_mode = True
