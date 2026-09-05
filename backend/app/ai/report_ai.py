"""
Report AI — orchestrates the full extraction pipeline.

Flow:
1. Download file from Storage
2. Convert PDF pages to images if needed
3. Send to AI provider
4. Parse + validate JSON response
5. Normalize test names
6. Calculate status deterministically
7. Return ExtractionResult ready for DB write
"""
import io
import json
import logging
from typing import Optional
from datetime import date

from app.ai.groq_provider import get_groq_provider
from app.models.schemas import MedicalTestExtracted, ExtractionResult
from app.utils.normalization import normalize_test_name
from app.utils.reference_range import calculate_status

logger = logging.getLogger(__name__)


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw or raw == "null":
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(raw, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _clean_json_response(raw: str) -> str:
    """Strip markdown code fences if LLM wrapped the JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first and last lines (``` or ```json)
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return raw.strip()


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract embedded text directly from PDF pages using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages = []
        for i, page in enumerate(reader.pages[:6]):  # max 6 pages
            text = page.extract_text() or ""
            if text.strip():
                extracted_pages.append(f"--- Page {i+1} ---\n{text}")
        return "\n\n".join(extracted_pages)
    except Exception as e:
        logger.warning(f"pypdf text extraction error: {e}")
        return ""


async def extract_from_file(
    file_bytes: bytes,
    content_type: str,
    filename: str,
) -> ExtractionResult:
    """
    Main extraction pipeline for uploaded files.
    Handles PDF text extraction, AI call, validation, normalization.
    """
    provider = get_groq_provider()

    # If PDF, try direct text extraction first
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        pdf_text = _extract_text_from_pdf(file_bytes)
        if pdf_text and len(pdf_text.strip()) > 30:
            return await extract_from_text(pdf_text)

    # For text files, decode directly
    if content_type.startswith("text/") or filename.lower().endswith((".txt", ".csv")):
        try:
            text = file_bytes.decode("utf-8")
            return await extract_from_text(text)
        except Exception:
            pass

    # For images or scanned files, pass to vision/text
    pages_to_process: list[tuple[bytes, str]] = []

    if content_type == "application/pdf":
        image_pages = _pdf_to_images(file_bytes)
        if image_pages:
            for img_bytes in image_pages[:4]:
                pages_to_process.append((img_bytes, "image/jpeg"))
        else:
            # Fallback to whatever text was extractable
            pdf_text = _extract_text_from_pdf(file_bytes)
            if pdf_text:
                return await extract_from_text(pdf_text)
            raise ValueError("Could not read content from PDF file")
    else:
        pages_to_process.append((file_bytes, content_type))

    # Extract from each page and merge results
    all_tests: list[MedicalTestExtracted] = []
    report_date: Optional[date] = None
    source_texts: list[str] = []

    for page_bytes, page_type in pages_to_process:
        raw_response = await provider.extract_medical_report(page_bytes, page_type, filename)
        source_texts.append(raw_response)

        try:
            cleaned = _clean_json_response(raw_response)
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI JSON: {e}. Raw: {raw_response[:300]}")
            continue

        # Parse report date (use first found)
        if report_date is None:
            report_date = _parse_date(data.get("report_date"))

        # Parse and validate tests
        raw_tests = data.get("tests", [])
        for raw_test in raw_tests:
            try:
                test = MedicalTestExtracted(**raw_test)
                all_tests.append(test)
            except Exception as e:
                logger.warning(f"Skipping invalid test entry: {e} — data: {raw_test}")
                continue

    return ExtractionResult(
        tests=all_tests,
        report_date=report_date,
        source_text="\n\n---\n\n".join(source_texts)[:10000],  # cap stored text
        model_used=provider.model_name,
        raw_response=source_texts[0] if source_texts else None,
    )


async def extract_from_text(text: str) -> ExtractionResult:
    """Extraction pipeline for pasted report text."""
    provider = get_groq_provider()
    raw_response = await provider.extract_from_text(text)

    try:
        cleaned = _clean_json_response(raw_response)
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI text extraction JSON: {e}")
        raise ValueError("AI could not extract structured data from the provided text")

    all_tests: list[MedicalTestExtracted] = []
    for raw_test in data.get("tests", []):
        try:
            test = MedicalTestExtracted(**raw_test)
            all_tests.append(test)
        except Exception as e:
            logger.warning(f"Skipping invalid test: {e}")

    return ExtractionResult(
        tests=all_tests,
        report_date=_parse_date(data.get("report_date")),
        source_text=text[:10000],
        model_used=provider.model_name,
        raw_response=raw_response,
    )


def _pdf_to_images(pdf_bytes: bytes) -> list[bytes]:
    """Convert PDF pages to JPEG images for vision model processing."""
    try:
        import PyPDF2
        from PIL import Image
        import fitz  # PyMuPDF — faster and more reliable than pdf2image

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        for page_num in range(min(len(doc), 4)):  # max 4 pages
            page = doc.load_page(page_num)
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for readability
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("jpeg")
            images.append(img_bytes)
        doc.close()
        return images
    except ImportError:
        # Fallback: try pdf2image
        try:
            from pdf2image import convert_from_bytes
            images_pil = convert_from_bytes(pdf_bytes, dpi=200, first_page=1, last_page=4)
            result = []
            for img in images_pil:
                buf = io.BytesIO()
                img.convert("RGB").save(buf, format="JPEG", quality=90)
                result.append(buf.getvalue())
            return result
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            return []
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        return []


def build_db_test_record(
    test: MedicalTestExtracted,
    patient_id: str,
    report_id: str,
) -> dict:
    """
    Convert a validated MedicalTestExtracted into a DB-ready dict.
    Status is calculated deterministically here — never from the LLM.
    """
    normalized = normalize_test_name(test.test_name)
    status = calculate_status(test.value, test.reference_low, test.reference_high)

    return {
        "patient_id": patient_id,
        "report_id": report_id,
        "test_name": normalized or test.test_name,
        "value": test.value,
        "value_text": test.value_text,
        "unit": test.unit,
        "reference_low": test.reference_low,
        "reference_high": test.reference_high,
        "reference_text": test.reference_text,
        "status": status.value,
        "observation": test.observation,
        "source": "report",
        "source_location": test.source_location,
        "extraction_confidence": test.extraction_confidence,
        "verification_status": "pending",
        "original_extracted_value": str(test.value) if test.value is not None else test.value_text,
    }
