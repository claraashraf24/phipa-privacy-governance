# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    alerts_user = relationship("Alert", back_populates="user", lazy="joined")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    dob = Column(String)
    record_id = Column(String, unique=True)

    alerts_patient = relationship("Alert", back_populates="patient", lazy="joined")


class Consent(Base):
    __tablename__ = "consents"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient")
    user = relationship("User")

class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    action = Column(String)  # view/edit/export
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_authorized = Column(Boolean, default=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

    # Optional relationships (for joined queries)
    user = relationship("User", back_populates="alerts_user", lazy="joined")
    patient = relationship("Patient", back_populates="alerts_patient", lazy="joined")
