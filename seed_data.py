# seed_data.py
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models

# -------------------------------------------------
# DATABASE SETUP
# -------------------------------------------------
DATABASE_URL = "sqlite:///./privacy_governance.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# -------------------------------------------------
# RECREATE SCHEMA
# -------------------------------------------------
print("Recreating database...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# -------------------------------------------------
# SEED USERS
# -------------------------------------------------
users = [
    models.User(name="Dr. Youssef", role="Doctor", email="youssef@hospital.ca"),
    models.User(name="Nurse Clara", role="Nurse", email="clara@hospital.ca"),
    models.User(name="Admin Omar", role="Admin", email="omar@hospital.ca"),
]
db.add_all(users)
db.commit()

# -------------------------------------------------
# SEED PATIENTS
# -------------------------------------------------
patients = [
    models.Patient(name="Ashraf Mo", dob="1990-05-20", record_id="REC1234"),
    models.Patient(name="John Doe", dob="1985-07-10", record_id="REC5678"),
]
db.add_all(patients)
db.commit()

# -------------------------------------------------
# SEED CONSENTS
# -------------------------------------------------
consents = [
    # Doctor Youssef can view but not edit Ashraf
    models.Consent(
        user_id=1, patient_id=1, can_view=True, can_edit=False,
        created_at=datetime.utcnow()
    ),
    # Nurse Clara can both view and edit John Doe
    models.Consent(
        user_id=2, patient_id=2, can_view=True, can_edit=True,
        created_at=datetime.utcnow()
    )
]
db.add_all(consents)
db.commit()

# -------------------------------------------------
# OPTIONAL: SEED SAMPLE LOGS (for metrics test)
# -------------------------------------------------
logs = [
    models.AccessLog(
        user_id=1, patient_id=1, action="view",
        timestamp=datetime.utcnow(), is_authorized=True
    ),
    models.AccessLog(
        user_id=1, patient_id=1, action="edit",
        timestamp=datetime.utcnow(), is_authorized=False
    ),
]
db.add_all(logs)
db.commit()

# -------------------------------------------------
# CONFIRMATION
# -------------------------------------------------
print("✅ Database seeded successfully!")
print("Users:", db.query(models.User).count())
print("Patients:", db.query(models.Patient).count())
print("Consents:", db.query(models.Consent).count())
print("Logs:", db.query(models.AccessLog).count())

db.close()
