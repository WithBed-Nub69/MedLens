"""
Patient API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.schemas import PatientCreate, PatientUpdate, PatientResponse, SuccessResponse
from app.services import patient_service
from app.utils.auth import get_current_user_id
from app.ai.summary_ai import generate_patient_summary, generate_clarification_questions

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        patient = await patient_service.create_patient(user_id, data)
        return SuccessResponse(message="Patient created", data=patient)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SuccessResponse)
async def list_patients(user_id: str = Depends(get_current_user_id)):
    patients = await patient_service.get_patients(user_id)
    return SuccessResponse(data=patients)


@router.get("/{patient_id}", response_model=SuccessResponse)
async def get_patient(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    patient = await patient_service.get_patient(user_id, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return SuccessResponse(data=patient)


@router.put("/{patient_id}", response_model=SuccessResponse)
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    user_id: str = Depends(get_current_user_id),
):
    updated = await patient_service.update_patient(user_id, patient_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return SuccessResponse(message="Patient updated", data=updated)


@router.get("/{patient_id}/tests", response_model=SuccessResponse)
async def get_patient_tests(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        await patient_service.assert_patient_ownership(user_id, patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    from app.database.client import get_service_client
    client = get_service_client()
    result = (
        client.table("medical_tests")
        .select("*")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    return SuccessResponse(data=result.data or [])


@router.post("/{patient_id}/summary", response_model=SuccessResponse)
async def generate_summary(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        await patient_service.assert_patient_ownership(user_id, patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        summary = await generate_patient_summary(patient_id)
        return SuccessResponse(message="Summary generated", data=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}/summary", response_model=SuccessResponse)
async def get_summary(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        await patient_service.assert_patient_ownership(user_id, patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    from app.database.client import get_service_client
    client = get_service_client()
    result = (
        client.table("ai_summaries")
        .select("*")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    summary = result.data[0] if result.data else None
    return SuccessResponse(data=summary)


@router.get("/{patient_id}/clarifications", response_model=SuccessResponse)
async def get_clarifications(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        await patient_service.assert_patient_ownership(user_id, patient_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    questions = await generate_clarification_questions(patient_id)
    return SuccessResponse(data=questions)
