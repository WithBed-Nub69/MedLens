"""
Medical Tests API — human verification and correction of extracted values.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from app.models.schemas import MedicalTestUpdate, SuccessResponse
from app.utils.auth import get_current_user_id
from app.utils.reference_range import calculate_status
from app.database.client import get_service_client

router = APIRouter(prefix="/tests", tags=["tests"])


async def _assert_test_ownership(user_id: str, test_id: str) -> dict:
    """Verify the user owns the patient this test belongs to."""
    client = get_service_client()
    result = (
        client.table("medical_tests")
        .select("*, patients!inner(user_id)")
        .eq("id", test_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Test not found")
    test = result.data[0]
    if test.get("patients", {}).get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    test.pop("patients", None)
    return test


@router.put("/{test_id}", response_model=SuccessResponse)
async def update_test(
    test_id: str,
    data: MedicalTestUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Human correction of an extracted medical test value."""
    original = await _assert_test_ownership(user_id, test_id)

    client = get_service_client()
    payload = {k: v for k, v in data.model_dump(exclude_none=True).items()}

    # Recalculate status if value or range is being updated
    new_value = payload.get("value", original.get("value"))
    new_ref_low = payload.get("reference_low", original.get("reference_low"))
    new_ref_high = payload.get("reference_high", original.get("reference_high"))
    payload["status"] = calculate_status(new_value, new_ref_low, new_ref_high).value

    # Track correction — preserve original extraction
    if "value" in payload and original.get("original_extracted_value") is None:
        payload["original_extracted_value"] = (
            str(original.get("value")) if original.get("value") is not None
            else original.get("value_text")
        )

    result = client.table("medical_tests").update(payload).eq("id", test_id).execute()
    return SuccessResponse(message="Test updated", data=result.data[0] if result.data else None)


@router.post("/{test_id}/verify", response_model=SuccessResponse)
async def verify_test(
    test_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Mark an extracted test as human-verified (no corrections needed)."""
    await _assert_test_ownership(user_id, test_id)

    client = get_service_client()
    payload = {
        "verification_status": "verified",
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    result = client.table("medical_tests").update(payload).eq("id", test_id).execute()
    return SuccessResponse(message="Test verified", data=result.data[0] if result.data else None)


@router.post("/{test_id}/correct", response_model=SuccessResponse)
async def correct_and_verify_test(
    test_id: str,
    data: MedicalTestUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Apply corrections and mark as corrected (not original) in one step."""
    original = await _assert_test_ownership(user_id, test_id)

    client = get_service_client()
    payload = {k: v for k, v in data.model_dump(exclude_none=True).items()}

    # Recalculate status deterministically
    new_value = payload.get("value", original.get("value"))
    new_ref_low = payload.get("reference_low", original.get("reference_low"))
    new_ref_high = payload.get("reference_high", original.get("reference_high"))
    payload["status"] = calculate_status(new_value, new_ref_low, new_ref_high).value

    # Preserve original extracted value for provenance
    if original.get("original_extracted_value") is None:
        payload["original_extracted_value"] = (
            str(original.get("value")) if original.get("value") is not None
            else original.get("value_text")
        )

    payload["verification_status"] = "corrected"
    payload["verified_at"] = datetime.now(timezone.utc).isoformat()

    result = client.table("medical_tests").update(payload).eq("id", test_id).execute()
    return SuccessResponse(message="Test corrected and verified", data=result.data[0] if result.data else None)
