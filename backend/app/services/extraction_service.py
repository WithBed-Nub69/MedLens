"""
Extraction service — full processing pipeline:
Download → Extract → Validate → Normalize → Status → Save to DB
"""
import logging
from app.ai.report_ai import extract_from_file, extract_from_text, build_db_test_record
from app.services.report_service import download_report_bytes, update_report_status, get_report
from app.database.client import get_service_client

logger = logging.getLogger(__name__)


async def process_report(user_id: str, report_id: str) -> dict:
    """
    Full processing pipeline for an uploaded report.
    Returns a summary of what was extracted.
    """
    # Fetch report and verify ownership
    report = await get_report(user_id, report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found or access denied")

    patient_id = report["patient_id"]
    storage_path = report["file_path"]
    content_type = _infer_content_type(report["file_name"])

    # Mark as processing
    await update_report_status(report_id, "processing")

    try:
        # Download from Storage
        file_bytes = await download_report_bytes(storage_path)

        # Run AI extraction
        extraction = await extract_from_file(file_bytes, content_type, report["file_name"])

        if not extraction.tests:
            await update_report_status(report_id, "failed")
            raise ValueError("No medical data could be extracted from this document")

        # Build DB records with deterministic status calculation
        db_records = [
            build_db_test_record(test, patient_id, report_id)
            for test in extraction.tests
        ]

        # Bulk insert into medical_tests
        client = get_service_client()
        result = client.table("medical_tests").insert(db_records).execute()

        # Update report status to review + store source text
        await update_report_status(
            report_id,
            "review",
            source_text=extraction.source_text,
            model=extraction.model_used,
        )

        if extraction.report_date:
            client.table("medical_reports").update(
                {"report_date": extraction.report_date.isoformat()}
            ).eq("id", report_id).execute()

        return {
            "report_id": report_id,
            "tests_extracted": len(db_records),
            "model_used": extraction.model_used,
            "report_date": extraction.report_date.isoformat() if extraction.report_date else None,
        }

    except Exception as e:
        await update_report_status(report_id, "failed")
        logger.error(f"Extraction failed for report {report_id}: {e}")
        raise


async def process_text_report(user_id: str, report_id: str, text: str) -> dict:
    """Process a pasted text report."""
    report = await get_report(user_id, report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found or access denied")

    patient_id = report["patient_id"]
    await update_report_status(report_id, "processing")

    try:
        extraction = await extract_from_text(text)

        if not extraction.tests:
            await update_report_status(report_id, "failed")
            raise ValueError("No medical data could be extracted from the provided text")

        db_records = [
            build_db_test_record(test, patient_id, report_id)
            for test in extraction.tests
        ]

        client = get_service_client()
        client.table("medical_tests").insert(db_records).execute()

        await update_report_status(
            report_id,
            "review",
            source_text=text[:10000],
            model=extraction.model_used,
        )

        return {
            "report_id": report_id,
            "tests_extracted": len(db_records),
            "model_used": extraction.model_used,
        }

    except Exception as e:
        await update_report_status(report_id, "failed")
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
