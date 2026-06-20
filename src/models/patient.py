"""
FHIR R4 Patient Resource Models
Pydantic models for data validation and serialisation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class PatientResource(BaseModel):
    resourceType: Literal["Patient"] = "Patient"
    id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    identifier: Optional[List[Dict[str, Any]]] = None
    name: Optional[List[Dict[str, Any]]] = None
    gender: Optional[str] = None
    birthDate: Optional[str] = None
    active: Optional[bool] = True

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Patient",
                "id": "example-patient-001",
                "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
                "gender": "female",
                "birthDate": "1985-04-12",
                "active": True
            }
        }


class BundleEntry(BaseModel):
    fullUrl: Optional[str] = None
    resource: Optional[PatientResource] = None


class PatientBundle(BaseModel):
    resourceType: Literal["Bundle"] = "Bundle"
    type: str = "searchset"
    total: int = 0
    entry: List[BundleEntry] = []
