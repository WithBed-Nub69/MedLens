"""
Patient API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.schemas import PatientCreate, PatientUpdate, PatientResponse, SuccessResponse
from app.services import patient_service
from app.utils.auth import get_authenticated_user, AuthenticatedUser
from app.ai.summary_ai import generate_patient_summary, generate_clarification_questions
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        patient = await patient_service.create_patient(auth_user.user_id, data, client=auth_user.client)
        return SuccessResponse(message="Patient created", data=patient)
    except Exception as e:
        logger.error(f"Failed to create patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SuccessResponse)
async def list_patients(auth_user: AuthenticatedUser = Depends(get_authenticated_user)):
    patients = await patient_service.get_patients(auth_user.user_id, client=auth_user.client)
    return SuccessResponse(data=patients)


@router.get("/{patient_id}", response_model=SuccessResponse)
async def get_patient(
    patient_id: str,
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    patient = await patient_service.get_patient(auth_user.user_id, patient_id, client=auth_user.client)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return SuccessResponse(data=patient)


@router.put("/{patient_id}", response_model=SuccessResponse)
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    updated = await patient_service.update_patient(auth_user.user_id, patient_id, data, client=auth_user.client)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return SuccessResponse(message="Patient updated", data=updated)


@router.delete("/{patient_id}", response_model=SuccessResponse)
async def delete_patient(
    patient_id: str,
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    deleted = await patient_service.delete_patient(auth_user.user_id, patient_id, client=auth_user.client)
    if not deleted:
        raise HTTPException(status_code=404, detail="Patient not found")
    return SuccessResponse(message="Patient deleted successfully")


@router.get("/{patient_id}/tests", response_model=SuccessResponse)
async def get_patient_tests(
    patient_id: str,
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        await patient_service.assert_patient_ownership(auth_user.user_id, patient_id, client=auth_user.client)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    result = (
        auth_user.client.table("medical_tests")
        .select("*")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    return SuccessResponse(data=result.data or [])


@router.post("/{patient_id}/summary", response_model=SuccessResponse)
async def generate_summary(
    patient_id: str,
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        await patient_service.assert_patient_ownership(auth_user.user_id, patient_id, client=auth_user.client)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        summary = await generate_patient_summary(patient_id, client=auth_user.client)
        return SuccessResponse(message="Summary generated", data=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}/summary", response_model=SuccessResponse)
async def get_summary(
    patient_id: str,
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        await patient_service.assert_patient_ownership(auth_user.user_id, patient_id, client=auth_user.client)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    result = (
        auth_user.client.table("ai_summaries")
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
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        await patient_service.assert_patient_ownership(auth_user.user_id, patient_id, client=auth_user.client)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        questions = await generate_clarification_questions(patient_id, client=auth_user.client)
        return SuccessResponse(data=questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


