# main.py
from fastapi import FastAPI
from routers import (
    users,
    patients,
    consents,
    access,
    metrics,
    reports,
    exports,
    alerts,
    incidents,
)

# ----------------------------------------------------------
#  FASTAPI APPLICATION SETUP
# ----------------------------------------------------------
app = FastAPI(
    title="PHIPA-Compliant Privacy Governance API",
    description="Healthcare privacy, consent, and audit system (PHIPA-ready).",
    version="2.0.0",
    contact={
        "name": "Privacy Compliance Team",
        "email": "compliance@demohealth.ca",
    },
)

# ----------------------------------------------------------
#  ROOT ENDPOINT
# ----------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "✅ Privacy Governance System is live.",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "2.0.0",
    }

# ----------------------------------------------------------
#  ROUTER REGISTRATION
# ----------------------------------------------------------
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(consents.router)
app.include_router(access.router)
app.include_router(metrics.router)
app.include_router(reports.router)
app.include_router(exports.router)
app.include_router(alerts.router)
app.include_router(incidents.router)

# ----------------------------------------------------------
#  HEALTH CHECK (for Docker or CI/CD)
# ----------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "uptime": "healthy"}
