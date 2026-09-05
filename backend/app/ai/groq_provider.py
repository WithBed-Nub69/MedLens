"""
Groq AI provider implementation.
Uses llama-3.2-90b-vision-preview for multimodal medical report extraction.
Uses llama-3.3-70b-versatile for text generation (summary, clarifications).
"""
import base64
import json
import logging
from typing import Optional
from groq import AsyncGroq
from app.ai.provider import AIProvider
from app.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_MODEL = "qwen/qwen3.8-27b"
TEXT_MODEL = "qwen/qwen3.8-27b"

EXTRACTION_SYSTEM_PROMPT = """You are a precise medical report data extraction engine.

Your ONLY job is to extract structured data from medical laboratory reports and return valid JSON.

CRITICAL RULES — follow exactly:
1. NEVER invent, estimate, or fabricate medical values, units, or reference ranges.
2. If a value is not clearly present in the document, use null.
3. If a reference range is not in the document, use null for reference_low and reference_high.
4. Extract ONLY what is explicitly written in the document.
5. Do NOT add commentary, warnings, or explanations outside the JSON.
6. The "value" field must be numeric when the test has a numeric result.
7. If the result is text (e.g., "Positive", "Negative", "Reactive"), use value_text instead.

Return a JSON object with this exact structure:
{
  "report_date": "YYYY-MM-DD or null",
  "tests": [
    {
      "test_name": "exact name from document",
      "value": numeric or null,
      "value_text": "text result or null",
      "unit": "unit string or null",
      "reference_low": numeric or null,
      "reference_high": numeric or null,
      "reference_text": "original reference range text from document or null",
      "observation": "any observation/flag text from document or null",
      "source_location": "section/page where found or null",
      "extraction_confidence": 0.0 to 1.0
    }
  ]
}

Do not include any text before or after the JSON object."""

SUMMARY_SYSTEM_PROMPT = """You are a compassionate medical information assistant helping patients understand their health records.

CRITICAL RULES:
1. You MUST NOT diagnose any disease or condition.
2. You MUST NOT prescribe or recommend any medication.
3. You MUST NOT recommend dosage changes.
4. You MUST NOT claim certainty about any medical condition.
5. You are helping the patient UNDERSTAND their available information — not treating them.
6. Write in clear, simple language a non-medical person can understand.
7. For values outside reference ranges, note this factually without alarming language.
8. Always recommend consulting a healthcare professional for interpretation.
9. Keep the summary concise (150-300 words).
10. Structure: brief overview, notable findings (outside range or flagged), any gaps/missing info, closing note to consult a doctor."""

CLARIFICATION_SYSTEM_PROMPT = """You are a clinical intake assistant generating relevant clarification questions.

Generate 3-5 specific, relevant questions based on the patient's provided information to help complete their health record.

RULES:
1. Questions must be for INFORMATION GATHERING only — not advice.
2. Never ask questions that imply diagnosis or treatment.
3. Focus on: symptom timeline, frequency, severity, related context.
4. Keep questions short and clear.
5. Return a JSON array of question strings only.

Example output:
["When did the headaches first begin?", "How often do they occur?", "Have you noticed any triggers?"]"""


class GroqProvider(AIProvider):
    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    @property
    def model_name(self) -> str:
        return EXTRACTION_MODEL

    async def extract_medical_report(
        self,
        content: bytes,
        content_type: str,
        filename: str,
    ) -> str:
        """
        Send document to Groq vision model for structured extraction.
        For PDFs, caller should convert to images first.
        """
        # Encode as base64 data URI
        b64 = base64.standard_b64encode(content).decode("utf-8")
        data_uri = f"data:{content_type};base64,{b64}"

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Extract all medical test data from this report ({filename}). Return structured JSON only.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": data_uri},
                    },
                ],
            }
        ]

        response = await self._client.chat.completions.create(
            model=EXTRACTION_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                *messages,
            ],
            temperature=0.0,  # Deterministic extraction
            max_tokens=4096,
        )

        raw = response.choices[0].message.content or ""
        logger.debug(f"Groq extraction raw response: {raw[:500]}")
        return raw

    async def extract_from_text(self, text: str) -> str:
        """Extract structured data from pasted text."""
        response = await self._client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Extract all medical test data from this report text:\n\n{text}",
                },
            ],
            temperature=0.0,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    async def generate_summary(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    async def generate_clarifications(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": CLARIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=512,
        )
        return response.choices[0].message.content or ""


# Singleton
_groq_provider: Optional[GroqProvider] = None


def get_groq_provider() -> GroqProvider:
    global _groq_provider
    if _groq_provider is None:
        _groq_provider = GroqProvider()
    return _groq_provider
