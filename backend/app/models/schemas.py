from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import date, datetime
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class Sex(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class ReportType(str, Enum):
    lab = "lab"
    prescription = "prescription"
    radiology = "radiology"
    discharge = "discharge"
    other = "other"


class ProcessingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    review = "review"
    verified = "verified"
    failed = "failed"


class TestStatus(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    unknown = "unknown"


class TestSource(str, Enum):
    user = "user"
    report = "report"
    ai = "ai"


class VerificationStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    corrected = "corrected"


# ── Patient ────────────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    age: Optional[int] = Field(None, ge=0, le=150)
    sex: Optional[Sex] = None
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    existing_conditions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    sex: Optional[Sex] = None
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None
    symptoms: Optional[List[str]] = None
    existing_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    notes: Optional[List[str]] = None


class PatientResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    age: Optional[int] = None
    sex: Optional[str] = None
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None
    symptoms: List[Any] = Field(default_factory=list)
    existing_conditions: List[Any] = Field(default_factory=list)
    allergies: List[Any] = Field(default_factory=list)
    medications: List[Any] = Field(default_factory=list)
    notes: List[Any] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── Medical Report ─────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    patient_id: str
    file_name: str
    file_path: str
    report_type: ReportType = ReportType.other
    report_date: Optional[date] = None


class ReportResponse(BaseModel):
    id: str
    patient_id: str
    file_name: str
    file_path: str
    report_type: str
    report_date: Optional[date] = None
    processing_status: str
    source_text: Optional[str] = None
    extraction_model: Optional[str] = None
    extraction_version: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── Medical Test (extracted value) ─────────────────────────────────────────────

class MedicalTestExtracted(BaseModel):
    """Validated structure from AI extraction — must pass safety checks before DB write."""
    test_name: str = Field(..., min_length=1)
    normalized_name: Optional[str] = None
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_text: Optional[str] = None
    observation: Optional[str] = None
    source_location: Optional[str] = None
    extraction_confidence: Optional[float] = Field(None, ge=0, le=1)

    @field_validator("reference_low", "reference_high", mode="before")
    @classmethod
    def coerce_range(cls, v):
        if v is None or v == "" or v == "null":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator("value", mode="before")
    @classmethod
    def coerce_value(cls, v):
        if v is None or v == "" or v == "null":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class MedicalTestResponse(BaseModel):
    id: str
    patient_id: str
    report_id: str
    test_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_text: Optional[str] = None
    status: str
    observation: Optional[str] = None
    source: str
    source_location: Optional[str] = None
    extraction_confidence: Optional[float] = None
    verification_status: str
    original_extracted_value: Optional[str] = None
    correction_note: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MedicalTestUpdate(BaseModel):
    """Fields the human reviewer can correct."""
    test_name: Optional[str] = None
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_text: Optional[str] = None
    observation: Optional[str] = None
    correction_note: Optional[str] = None


# ── AI Summary ─────────────────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    id: str
    patient_id: str
    summary_text: str
    model_name: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Extraction Result (internal pipeline) ─────────────────────────────────────

class ExtractionResult(BaseModel):
    tests: List[MedicalTestExtracted]
    report_date: Optional[date] = None
    source_text: Optional[str] = None
    model_used: str
    confidence_overall: Optional[float] = None
    raw_response: Optional[str] = None


# ── API Responses ──────────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[str] = None
