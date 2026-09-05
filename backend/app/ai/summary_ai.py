"""
Summary AI — generates patient-friendly AI summaries from structured data.
Based on structured DB records, NOT raw documents.
"""
import json
import logging
from typing import Optional
from app.ai.groq_provider import get_groq_provider
from app.database.client import get_service_client

logger = logging.getLogger(__name__)


def _build_summary_prompt(patient: dict, tests: list[dict], reports: list[dict]) -> str:
    """Build a structured prompt from DB records — no raw document passed."""
    lines = []

    lines.append("PATIENT INFORMATION (Source: User Provided):")
    lines.append(f"  Name: {patient.get('full_name', 'Unknown')}")
    lines.append(f"  Age: {patient.get('age', 'Not provided')}")
    lines.append(f"  Sex: {patient.get('sex', 'Not provided')}")

    symptoms = patient.get("symptoms", [])
    if symptoms:
        lines.append(f"  Reported symptoms: {', '.join(symptoms)}")

    conditions = patient.get("existing_conditions", [])
    if conditions:
        lines.append(f"  Existing conditions: {', '.join(conditions)}")

    allergies = patient.get("allergies", [])
    if allergies:
        lines.append(f"  Allergies: {', '.join(allergies)}")

    medications = patient.get("medications", [])
    if medications:
        lines.append(f"  Current medications: {', '.join(medications)}")

    lines.append(f"\nREPORTS UPLOADED: {len(reports)}")

    if tests:
        lines.append("\nLABORATORY RESULTS (Source: Report Extracted):")
        for t in tests:
            value_str = f"{t.get('value')} {t.get('unit', '')}".strip() if t.get("value") is not None else t.get("value_text", "N/A")
            ref = t.get("reference_text") or (
                f"{t.get('reference_low')}–{t.get('reference_high')} {t.get('unit', '')}".strip()
                if t.get("reference_low") is not None
                else "No reference range available"
            )
            status = t.get("status", "unknown").upper()
            verified = "✓ Verified" if t.get("verification_status") == "verified" else "⏳ Pending verification"
            lines.append(f"  • {t.get('test_name')}: {value_str} | Reference: {ref} | Status: {status} | {verified}")
            if t.get("observation"):
                lines.append(f"    Observation: {t.get('observation')}")
    else:
        lines.append("\nNo laboratory results available yet.")

    lines.append("\n---")
    lines.append("Please generate a concise patient-friendly summary following your guidelines.")
    lines.append("IMPORTANT: Do NOT diagnose, prescribe, or claim certainty about any condition.")

    return "\n".join(lines)


async def generate_patient_summary(patient_id: str) -> dict:
    """
    Generate and upsert an AI summary for a patient.
    Returns the created/updated summary record.
    """
    client = get_service_client()

    # Fetch patient data
    patient_result = client.table("patients").select("*").eq("id", patient_id).single().execute()
    if not patient_result.data:
        raise ValueError(f"Patient {patient_id} not found")
    patient = patient_result.data

    # Fetch verified + pending tests
    tests_result = (
        client.table("medical_tests")
        .select("*")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    tests = tests_result.data or []

    # Fetch reports
    reports_result = (
        client.table("medical_reports")
        .select("id, file_name, report_type, report_date, processing_status")
        .eq("patient_id", patient_id)
        .execute()
    )
    reports = reports_result.data or []

    provider = get_groq_provider()
    prompt = _build_summary_prompt(patient, tests, reports)
    summary_text = await provider.generate_summary(prompt)

    # Upsert summary (delete old, insert new — table has no unique constraint on patient_id)
    client.table("ai_summaries").delete().eq("patient_id", patient_id).execute()

    result = client.table("ai_summaries").insert({
        "patient_id": patient_id,
        "summary_text": summary_text,
        "model_name": provider.model_name,
        "source_record_version": f"tests:{len(tests)},reports:{len(reports)}",
    }).execute()

    if not result.data:
        raise RuntimeError("Failed to save AI summary")

    return result.data[0]


async def generate_clarification_questions(patient_id: str) -> list[str]:
    """Generate 3-5 clarification questions based on patient info."""
    client = get_service_client()

    patient_result = client.table("patients").select("*").eq("id", patient_id).single().execute()
    if not patient_result.data:
        return []
    patient = patient_result.data

    symptoms = patient.get("symptoms", [])
    conditions = patient.get("existing_conditions", [])
    medications = patient.get("medications", [])

    if not symptoms and not conditions:
        return []

    prompt = f"""Patient information:
- Reported symptoms: {', '.join(symptoms) if symptoms else 'None reported'}
- Existing conditions: {', '.join(conditions) if conditions else 'None reported'}
- Current medications: {', '.join(medications) if medications else 'None reported'}
- Age: {patient.get('age', 'Unknown')}
- Sex: {patient.get('sex', 'Unknown')}

Generate 3-5 relevant clarification questions to help complete the health intake."""

    provider = get_groq_provider()
    raw = await provider.generate_clarifications(prompt)

    import json
    try:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])
        questions = json.loads(raw)
        if isinstance(questions, list):
            return [str(q) for q in questions[:5]]
    except Exception as e:
        logger.warning(f"Could not parse clarification questions: {e}")
        # Try to extract lines as questions
        lines = [l.strip().lstrip("-•123456789. ") for l in raw.split("\n") if l.strip() and "?" in l]
        return lines[:5]

    return []
