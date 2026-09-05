"""
Report service — upload to Supabase Storage, record metadata, trigger processing.
Storage path: {user_id}/{patient_id}/{report_id}/{filename}
Bucket: medical-reports (private)
"""
import io
import uuid
from typing import Optional, List
from datetime import date
from fastapi import UploadFile
from app.database.client import get_service_client
from app.models.schemas import ReportType
import logging

logger = logging.getLogger(__name__)

BUCKET = "medical-reports"
ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
    "image/bmp",
}
MAX_FILE_SIZE_MB = 20


async def upload_report(
    user_id: str,
    patient_id: str,
    file: UploadFile,
    report_type: str = "other",
    report_date: Optional[date] = None,
) -> dict:
    """
    Upload a medical report to private Storage and insert a medical_reports row.
    Returns the created report record.
    """
    # Validate content type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise ValueError(
            f"Unsupported file type: {content_type}. "
            f"Allowed: PDF, JPEG, PNG, WEBP, TIFF, BMP"
        )

    # Read and size-check
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large ({size_mb:.1f} MB). Max allowed: {MAX_FILE_SIZE_MB} MB")

    report_id = str(uuid.uuid4())
    safe_filename = file.filename.replace(" ", "_") if file.filename else "report"
    storage_path = f"{user_id}/{patient_id}/{report_id}/{safe_filename}"

    client = get_service_client()

    # Upload to Storage
    client.storage.from_(BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "false"},
    )

    # Insert report record
    payload = {
        "id": report_id,
        "patient_id": patient_id,
        "file_name": safe_filename,
        "file_path": storage_path,
        "report_type": report_type,
        "report_date": report_date.isoformat() if report_date else None,
        "processing_status": "pending",
    }
    result = client.table("medical_reports").insert(payload).execute()
    if not result.data:
        raise RuntimeError("Failed to create report record")

    return result.data[0]


async def get_reports_for_patient(user_id: str, patient_id: str) -> List[dict]:
    """Fetch all reports for a patient. Ownership enforced via user_id."""
    from app.services.patient_service import assert_patient_ownership
    await assert_patient_ownership(user_id, patient_id)

    client = get_service_client()
    result = (
        client.table("medical_reports")
        .select("*")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def get_report(user_id: str, report_id: str) -> Optional[dict]:
    """Fetch a single report, verifying ownership via the patient relationship."""
    client = get_service_client()
    result = (
        client.table("medical_reports")
        .select("*, patients!inner(user_id)")
        .eq("id", report_id)
        .execute()
    )
    if not result.data:
        return None
    report = result.data[0]
    # Check ownership via nested patient
    if report.get("patients", {}).get("user_id") != user_id:
        return None
    # Clean up the nested patient data
    report.pop("patients", None)
    return report


async def update_report_status(report_id: str, status: str, source_text: Optional[str] = None, model: Optional[str] = None) -> None:
    client = get_service_client()
    payload: dict = {"processing_status": status}
    if source_text is not None:
        payload["source_text"] = source_text
    if model is not None:
        payload["extraction_model"] = model
        payload["extraction_version"] = "1.0"
    client.table("medical_reports").update(payload).eq("id", report_id).execute()


async def download_report_bytes(storage_path: str) -> bytes:
    """Download report file from private Storage using service-role client."""
    client = get_service_client()
    response = client.storage.from_(BUCKET).download(storage_path)
    return response


async def get_signed_url(storage_path: str, expires_in: int = 300) -> str:
    """Generate a short-lived signed URL for private bucket access."""
    client = get_service_client()
    result = client.storage.from_(BUCKET).create_signed_url(storage_path, expires_in)
    return result.get("signedURL", "")
