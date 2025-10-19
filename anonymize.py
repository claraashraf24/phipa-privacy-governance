# anonymize.py
from hashlib import sha256
from datetime import datetime

def _short_hash(value: str, length: int = 10) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:length]

def mask_name(name: str) -> str:
    # Convert real names to consistent pseudonyms
    return f"Patient-{_short_hash(name, 6)}"

def mask_user(name: str, role: str) -> str:
    return f"{role.title()}-{_short_hash(name, 6)}"

def generalize_dob(dob: str) -> str:
    """
    Accepts 'YYYY-MM-DD' or 'YYYY-MM' or 'YYYY'.
    Returns generalized DOB (year only). If parsing fails, returns 'Unknown'.
    """
    try:
        # try common formats
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                d = datetime.strptime(dob, fmt)
                return str(d.year)
            except ValueError:
                continue
    except Exception:
        pass
    return "Unknown"

def hash_record_id(record_id: str) -> str:
    return f"REC-{_short_hash(record_id, 8)}"

def summarize_incident(user_name: str, user_role: str, patient_name: str, action: str, reason: str, when_utc) -> str:
    ts = when_utc.strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"At {ts}, {user_role.title()} '{user_name}' attempted to {action} "
        f"the record of patient '{patient_name}' without sufficient consent. "
        f"System response: access denied. Reason: {reason}. "
        f"Notification: breach alert email sent to compliance officer."
    )
