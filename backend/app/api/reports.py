"""
Medical Reports API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from typing import Optional
from datetime import date
from app.models.schemas import SuccessResponse
from app.services import report_service
from app.services.extraction_service import process_report, process_text_report
from app.utils.auth import get_current_user_id

router = APIRouter(tags=["reports"])


@router.post("/patients/{patient_id}/reports", response_model=SuccessResponse, status_code=201)
async def upload_report(
    patient_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    report_type: str = Form(default="other"),
    report_date: Optional[str] = Form(default=None),
    auto_process: bool = Form(default=True),
    user_id: str = Depends(get_current_user_id),
):
    """Upload a medical report file (PDF or image)."""
    from app.services.patient_service import assert_patient_ownership
    try:
        await assert_patient_ownership(user_id, patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Parse date if provided
    parsed_date = None
    if report_date:
        try:
            parsed_date = date.fromisoformat(report_date)
        except ValueError:
            pass

    try:
        report = await report_service.upload_report(
            user_id=user_id,
            patient_id=patient_id,
            file=file,
            report_type=report_type,
            report_date=parsed_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # Trigger AI processing in background
    if auto_process:
        background_tasks.add_task(
            _safe_process_report, user_id, report["id"]
        )

    return SuccessResponse(
        message="Report uploaded" + (" and processing started" if auto_process else ""),
        data=report,
    )


async def _safe_process_report(user_id: str, report_id: str):
    """Background task wrapper with error swallowing."""
    try:
        await process_report(user_id, report_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Background processing failed for {report_id}: {e}")


@router.post("/patients/{patient_id}/reports/text", response_model=SuccessResponse, status_code=201)
async def upload_text_report(
    patient_id: str,
    background_tasks: BackgroundTasks,
    text: str = Form(...),
    report_type: str = Form(default="lab"),
    report_date: Optional[str] = Form(default=None),
    user_id: str = Depends(get_current_user_id),
):
    """Create a report from pasted text and process it."""
    from app.services.patient_service import assert_patient_ownership
    try:
        await assert_patient_ownership(user_id, patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    parsed_date = None
    if report_date:
        try:
            parsed_date = date.fromisoformat(report_date)
        except ValueError:
            pass

    # Create a dummy upload object for text
    import io
    from fastapi import UploadFile as FUploadFile
    from starlette.datastructures import UploadFile as StarletteUpload

    # We'll store a placeholder file
    dummy_bytes = text.encode("utf-8")
    dummy_file = UploadFile(
        filename="pasted_report.txt",
        file=io.BytesIO(dummy_bytes),
    )
    dummy_file.content_type = "text/plain"

    from app.database.client import get_service_client
    import uuid
    report_id = str(uuid.uuid4())
    client = get_service_client()
    result = client.table("medical_reports").insert({
        "id": report_id,
        "patient_id": patient_id,
        "file_name": "pasted_report.txt",
        "file_path": f"{user_id}/{patient_id}/{report_id}/pasted_report.txt",
        "report_type": report_type,
        "report_date": parsed_date.isoformat() if parsed_date else None,
        "processing_status": "pending",
        "source_text": text[:10000],
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create report record")

    report = result.data[0]
    background_tasks.add_task(_safe_process_text_report, user_id, report_id, text)

    return SuccessResponse(message="Text report created and processing started", data=report)


async def _safe_process_text_report(user_id: str, report_id: str, text: str):
    try:
        await process_text_report(user_id, report_id, text)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Text processing failed for {report_id}: {e}")


@router.get("/patients/{patient_id}/reports", response_model=SuccessResponse)
async def list_reports(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        reports = await report_service.get_reports_for_patient(user_id, patient_id)
        return SuccessResponse(data=reports)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports/{report_id}", response_model=SuccessResponse)
async def get_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
):
    report = await report_service.get_report(user_id, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return SuccessResponse(data=report)


@router.post("/reports/{report_id}/process", response_model=SuccessResponse)
async def reprocess_report(
    report_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
):
    """Manually trigger (re)processing of a report."""
    report = await report_service.get_report(user_id, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    background_tasks.add_task(_safe_process_report, user_id, report_id)
    return SuccessResponse(message="Processing started")


@router.get("/reports/{report_id}/signed-url", response_model=SuccessResponse)
async def get_signed_url(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
):
    report = await report_service.get_report(user_id, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    url = await report_service.get_signed_url(report["file_path"])
    return SuccessResponse(data={"url": url})
