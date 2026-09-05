"""
Patient service — CRUD operations with ownership enforcement.
All writes go through the service-role client.
All ownership checks use user_id comparison before DB access.
"""
from typing import Optional, List
from datetime import date
from app.database.client import get_service_client
from app.models.schemas import PatientCreate, PatientUpdate
import logging

logger = logging.getLogger(__name__)


def _serialize_date(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


async def create_patient(user_id: str, data: PatientCreate) -> dict:
    client = get_service_client()
    payload = {
        "user_id": user_id,
        "full_name": data.full_name,
        "age": data.age,
        "sex": data.sex.value if data.sex else None,
        "date_of_birth": _serialize_date(data.date_of_birth),
        "blood_group": data.blood_group,
        "symptoms": data.symptoms,
        "existing_conditions": data.existing_conditions,
        "allergies": data.allergies,
        "medications": data.medications,
        "notes": data.notes,
    }
    result = client.table("patients").insert(payload).execute()
    if not result.data:
        raise RuntimeError("Failed to create patient")
    return result.data[0]


async def get_patients(user_id: str) -> List[dict]:
    client = get_service_client()
    result = (
        client.table("patients")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def get_patient(user_id: str, patient_id: str) -> Optional[dict]:
    client = get_service_client()
    result = (
        client.table("patients")
        .select("*")
        .eq("id", patient_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return result.data


async def update_patient(user_id: str, patient_id: str, data: PatientUpdate) -> Optional[dict]:
    # First verify ownership
    existing = await get_patient(user_id, patient_id)
    if not existing:
        return None

    client = get_service_client()
    payload = {k: v for k, v in data.model_dump(exclude_none=True).items()}

    if "sex" in payload and hasattr(payload["sex"], "value"):
        payload["sex"] = payload["sex"].value
    if "date_of_birth" in payload and isinstance(payload["date_of_birth"], date):
        payload["date_of_birth"] = payload["date_of_birth"].isoformat()

    if not payload:
        return existing

    result = (
        client.table("patients")
        .update(payload)
        .eq("id", patient_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else None


async def assert_patient_ownership(user_id: str, patient_id: str) -> dict:
    """Raises ValueError if user does not own this patient."""
    patient = await get_patient(user_id, patient_id)
    if not patient:
        raise ValueError(f"Patient {patient_id} not found or access denied")
    return patient
