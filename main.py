"""
Secure FHIR Patient API
Healthcare data service built with security-first principles.
Demonstrates DevSecOps pipeline for Microsoft Defender for Cloud integration.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Optional
from datetime import datetime

from models.patient import PatientResource, PatientBundle
from utils.auth import verify_token
from utils.audit import log_phi_access

# Structured logging (never log PHI)
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Secure FHIR Patient API",
    description="HIPAA-compliant FHIR R4 patient data service with DevSecOps pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS — restrict to known origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourhealthapp.com"],  # NEVER use "*" with PHI
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
async def health_check():
    """Liveness probe — no auth required, no PHI exposed."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/fhir/r4/Patient/{patient_id}", response_model=PatientResource)
async def get_patient(
    patient_id: str,
    authorization: Optional[str] = Header(None),
    x_request_id: Optional[str] = Header(None)
):
    """
    Retrieve a FHIR R4 Patient resource.
    
    Security controls:
    - Bearer token validation (simulated)
    - PHI access audit logging
    - Patient ID sanitisation
    - No PHI in error messages or logs
    """
    # Validate token
    caller = verify_token(authorization)
    
    # Sanitise patient_id — prevent injection
    if not patient_id.isalnum() or len(patient_id) > 64:
        logger.warning(f"Invalid patient_id format — possible injection attempt")
        raise HTTPException(status_code=400, detail="Invalid patient identifier format")

    # Audit log the PHI access (who, when, what — never the data itself)
    log_phi_access(
        caller=caller,
        resource_type="Patient",
        resource_id=patient_id,
        action="READ",
        request_id=x_request_id
    )

    # Simulated patient data (in prod: query Azure Health Data Services FHIR API)
    sample_patient = PatientResource(
        resourceType="Patient",
        id=patient_id,
        meta={"versionId": "1", "lastUpdated": datetime.utcnow().isoformat()},
        identifier=[{"system": "urn:oid:2.16.840.1.113883.4.1", "value": "[REDACTED]"}],
        name=[{"use": "official", "family": "Doe", "given": ["Jane"]}],
        gender="female",
        birthDate="1985-04-12",
        active=True
    )

    logger.info(f"Patient resource served — id_hash={hash(patient_id)}")
    return sample_patient


@app.get("/fhir/r4/Patient", response_model=PatientBundle)
async def search_patients(
    family: Optional[str] = None,
    birthdate: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Search FHIR Patient resources.
    Requires at least one search parameter — prevents full dataset exposure.
    """
    caller = verify_token(authorization)

    if not family and not birthdate:
        raise HTTPException(
            status_code=400,
            detail="At least one search parameter required (family or birthdate)"
        )

    log_phi_access(caller=caller, resource_type="Patient", resource_id="search", action="SEARCH")

    # Simulate bundle response
    bundle = PatientBundle(
        resourceType="Bundle",
        type="searchset",
        total=1,
        entry=[]
    )
    return bundle


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
