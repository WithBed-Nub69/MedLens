"""
Extraction service — full processing pipeline:
Download → Extract → Validate → Normalize → Status → Save to DB
"""
import logging
from typing import Optional
from supabase import Client
from app.ai.report_ai import extract_from_file, extract_from_text, build_db_test_record
from app.services.report_service import download_report_bytes, update_report_status, get_report
from app.database.client import get_service_client

logger = logging.getLogger(__name__)


async def process_report(user_id: str, report_id: str, client: Optional[Client] = None) -> dict:
    """
    Full processing pipeline for an uploaded report.
    Returns a summary of what was extracted.
    """
    # Fetch report and verify ownership
    report = await get_report(user_id, report_id, client=client)
    if not report:
        raise ValueError(f"Report {report_id} not found or access denied")

    patient_id = report["patient_id"]
    storage_path = report["file_path"]
    content_type = _infer_content_type(report["file_name"])

    # Mark as processing
    await update_report_status(report_id, "processing", client=client)

    try:
        # Download from Storage
        file_bytes = await download_report_bytes(storage_path, client=client)

        # Run AI extraction
        extraction = await extract_from_file(file_bytes, content_type, report["file_name"])

        if not extraction.tests:
            await update_report_status(report_id, "failed", client=client)
            raise ValueError("No medical data could be extracted from this document")

        # Build DB records with deterministic status calculation
        db_records = [
            build_db_test_record(test, patient_id, report_id)
            for test in extraction.tests
        ]

        # Bulk insert into medical_tests
        db = client or get_service_client()
        result = db.table("medical_tests").insert(db_records).execute()

        # Update report status to review + store source text
        await update_report_status(
            report_id,
            "review",
            source_text=extraction.source_text,
            model=extraction.model_used,
            client=client,
        )

        if extraction.report_date:
            db.table("medical_reports").update(
                {"report_date": extraction.report_date.isoformat()}
            ).eq("id", report_id).execute()

        return {
            "report_id": report_id,
            "tests_extracted": len(db_records),
            "model_used": extraction.model_used,
            "report_date": extraction.report_date.isoformat() if extraction.report_date else None,
        }

    except Exception as e:
        await update_report_status(report_id, "failed", client=client)
        logger.error(f"Extraction failed for report {report_id}: {e}")
        raise


async def process_text_report(user_id: str, report_id: str, text: str, client: Optional[Client] = None) -> dict:
    """Process a pasted text report."""
    report = await get_report(user_id, report_id, client=client)
    if not report:
        raise ValueError(f"Report {report_id} not found or access denied")

    patient_id = report["patient_id"]
    await update_report_status(report_id, "processing", client=client)

    try:
        extraction = await extract_from_text(text)

        if not extraction.tests:
            await update_report_status(report_id, "failed", client=client)
            raise ValueError("No medical data could be extracted from the provided text")

        db_records = [
            build_db_test_record(test, patient_id, report_id)
            for test in extraction.tests
        ]

        db = client or get_service_client()
        db.table("medical_tests").insert(db_records).execute()

        await update_report_status(
            report_id,
            "review",
            source_text=text[:10000],
            model=extraction.model_used,
            client=client,
        )

        return {
            "report_id": report_id,
            "tests_extracted": len(db_records),
            "model_used": extraction.model_used,
        }

    except Exception as e:
        await update_report_status(report_id, "failed", client=client)
        logger.error(f"Text extraction failed for report {report_id}: {e}")
        raise


def _infer_content_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "tiff": "image/tiff",
        "bmp": "image/bmp",
    }.get(ext, "application/octet-stream")
