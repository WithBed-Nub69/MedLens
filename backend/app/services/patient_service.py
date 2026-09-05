"""
Patient service — CRUD operations with ownership enforcement.
User-initiated operations use the authenticated user's client, forwarding
their JWT so PostgreSQL RLS policies evaluate against role 'authenticated'.
Service-role client remains available as a fallback for internal tasks.
"""
from typing import Optional, List
from datetime import date
from supabase import Client
from app.database.client import get_service_client
from app.models.schemas import PatientCreate, PatientUpdate
import logging

logger = logging.getLogger(__name__)


def _serialize_date(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


async def create_patient(user_id: str, data: PatientCreate, client: Optional[Client] = None) -> dict:
    db = client or get_service_client()
    payload = {
        "user_id": user_id,  # taken from authenticated user's identity, NOT request body
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
    result = db.table("patients").insert(payload).execute()
    if not result.data:
        raise RuntimeError("Failed to create patient")
    return result.data[0]


async def get_patients(user_id: str, client: Optional[Client] = None) -> List[dict]:
    db = client or get_service_client()
    result = (
        db.table("patients")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def get_patient(user_id: str, patient_id: str, client: Optional[Client] = None) -> Optional[dict]:
    db = client or get_service_client()
    result = (
        db.table("patients")
        .select("*")
        .eq("id", patient_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else None


async def update_patient(user_id: str, patient_id: str, data: PatientUpdate, client: Optional[Client] = None) -> Optional[dict]:
    db = client or get_service_client()
    # First verify ownership
    existing = await get_patient(user_id, patient_id, client=db)
    if not existing:
        return None

    payload = {k: v for k, v in data.model_dump(exclude_none=True).items()}

    if "sex" in payload and hasattr(payload["sex"], "value"):
        payload["sex"] = payload["sex"].value
    if "date_of_birth" in payload and isinstance(payload["date_of_birth"], date):
        payload["date_of_birth"] = payload["date_of_birth"].isoformat()

    if not payload:
        return existing

    result = (
        db.table("patients")
        .update(payload)
        .eq("id", patient_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else None


async def delete_patient(user_id: str, patient_id: str, client: Optional[Client] = None) -> bool:
    db = client or get_service_client()
    existing = await get_patient(user_id, patient_id, client=db)
    if not existing:
        return False

    db.table("patients").delete().eq("id", patient_id).eq("user_id", user_id).execute()
    return True


async def assert_patient_ownership(user_id: str, patient_id: str, client: Optional[Client] = None) -> dict:
    """Raises ValueError if user does not own this patient."""
    patient = await get_patient(user_id, patient_id, client=client)
    if not patient:
        raise ValueError(f"Patient {patient_id} not found or access denied")
    return patient


