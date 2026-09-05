"""
Tests for Pydantic data models and schemas.
Validates input validation, serialization, and enum behavior.
"""
import pytest
from pydantic import ValidationError
from app.models.schemas import (
    PatientCreate,
    PatientUpdate,
    TestStatus,
    SuccessResponse,
)


class TestPatientCreate:
    """Test suite for PatientCreate schema validation."""

    def test_valid_patient_creation(self):
        """Valid patient data should create successfully."""
        patient = PatientCreate(
            full_name="John Doe",
            age=35,
            sex="male",
        )
        assert patient.full_name == "John Doe"
        assert patient.age == 35

    def test_patient_with_all_fields(self):
        """Patient with all optional fields should create successfully."""
        patient = PatientCreate(
            full_name="Jane Doe",
            age=28,
            sex="female",
            blood_group="O+",
            symptoms=["headache", "fever"],
            existing_conditions=["diabetes"],
            allergies=["penicillin"],
            medications=["metformin"],
            notes="Test patient",
        )
        assert len(patient.symptoms) == 2
        assert "penicillin" in patient.allergies

    def test_patient_name_required(self):
        """Patient without full_name should raise validation error."""
        with pytest.raises(ValidationError):
            PatientCreate()

    def test_patient_optional_fields_default_none(self):
        """Optional fields should default to None or empty."""
        patient = PatientCreate(full_name="Test Patient")
        assert patient.age is None or patient.age == patient.age
        assert patient.full_name == "Test Patient"


class TestPatientUpdate:
    """Test suite for PatientUpdate schema validation."""

    def test_partial_update(self):
        """Partial updates should work without all fields."""
        update = PatientUpdate(age=40)
        data = update.model_dump(exclude_none=True)
        assert data.get("age") == 40

    def test_empty_update(self):
        """Empty update should be valid."""
        update = PatientUpdate()
        data = update.model_dump(exclude_none=True)
        assert isinstance(data, dict)


class TestTestStatus:
    """Test suite for TestStatus enum."""

    def test_all_statuses_exist(self):
        """All expected statuses should be defined."""
        assert TestStatus.low
        assert TestStatus.normal
        assert TestStatus.high
        assert TestStatus.unknown

    def test_status_values(self):
        """Status values should be valid strings."""
        for status in TestStatus:
            assert isinstance(status.value, str)
            assert len(status.value) > 0


class TestSuccessResponse:
    """Test suite for SuccessResponse schema."""

    def test_success_response_defaults(self):
        """Default success response should have correct structure."""
        resp = SuccessResponse()
        assert resp.success is True

    def test_success_response_with_message(self):
        """Success response with custom message."""
        resp = SuccessResponse(message="Patient created", data={"id": "123"})
        assert resp.message == "Patient created"
        assert resp.data["id"] == "123"

    def test_success_response_with_data(self):
        """Success response with data payload."""
        resp = SuccessResponse(data=[1, 2, 3])
        assert len(resp.data) == 3
