# alerts_utils.py
import logging
from datetime import datetime
from database import get_db
import models

# Log alert in the database
def log_alert(user_id: int, patient_id: int, reason: str, db=None):
    """Create an Alert record when a privacy breach occurs."""
    if db is None:
        from database import SessionLocal
        db = SessionLocal()

    alert = models.Alert(
        user_id=user_id,
        patient_id=patient_id,
        message=f"Unauthorized access by user {user_id}: {reason}",
        created_at=datetime.utcnow(),
        resolved=False
    )
    db.add(alert)
    db.commit()
    logging.warning(f"[ALERT] {alert.message}")
    return alert


# Send simulated email alert (for demo)
def send_breach_alert(user_name: str, patient_name: str, reason: str):
    """Send a breach alert notification (simulated)."""
    logging.warning(
        f"[EMAIL SENT] 🚨 Privacy breach: "
        f"User '{user_name}' attempted to access '{patient_name}'. Reason: {reason}"
    )
