"""
Tests for test name normalization.
Verifies that common aliases are mapped to canonical names correctly.
"""
import pytest
from app.utils.normalization import normalize_test_name


class TestNormalizeTestName:
    """Test suite for the normalize_test_name utility function."""

    # ── Basic normalization ──────────────────────────────────────────

    def test_hemoglobin_aliases(self):
        """Common hemoglobin aliases should normalize correctly."""
        assert normalize_test_name("hb") == "Hemoglobin"
        assert normalize_test_name("hgb") == "Hemoglobin"
        assert normalize_test_name("haemoglobin") == "Hemoglobin"

    def test_glucose_fasting(self):
        """Fasting glucose aliases should normalize correctly."""
        assert normalize_test_name("fbs") == "Glucose (Fasting)"
        assert normalize_test_name("fasting blood sugar") == "Glucose (Fasting)"

    def test_cholesterol_variants(self):
        """Cholesterol test aliases should normalize correctly."""
        assert normalize_test_name("ldl") == "LDL Cholesterol"
        assert normalize_test_name("hdl") == "HDL Cholesterol"
        assert normalize_test_name("tg") == "Triglycerides"
        assert normalize_test_name("cholesterol") == "Total Cholesterol"

    def test_thyroid_panel(self):
        """Thyroid test aliases should normalize correctly."""
        assert normalize_test_name("tsh") == "TSH"
        assert normalize_test_name("free t4") == "Free T4"
        assert normalize_test_name("ft3") == "Free T3"

    def test_liver_panel(self):
        """Liver function test aliases should normalize correctly."""
        assert normalize_test_name("sgpt") == "ALT"
        assert normalize_test_name("sgot") == "AST"
        assert normalize_test_name("alp") == "ALP"

    def test_kidney_panel(self):
        """Kidney function test aliases should normalize correctly."""
        assert normalize_test_name("creatinine") == "Creatinine"
        assert normalize_test_name("bun") == "BUN"
        assert normalize_test_name("egfr") == "eGFR"

    def test_cbc_components(self):
        """CBC component aliases should normalize correctly."""
        assert normalize_test_name("wbc") == "WBC"
        assert normalize_test_name("rbc") == "RBC"
        assert normalize_test_name("platelet count") == "Platelets"
        assert normalize_test_name("mcv") == "MCV"

    def test_electrolytes(self):
        """Electrolyte test aliases should normalize correctly."""
        assert normalize_test_name("na") == "Sodium"
        assert normalize_test_name("k") == "Potassium"
        assert normalize_test_name("cl") == "Chloride"

    def test_vitamins(self):
        """Vitamin test aliases should normalize correctly."""
        assert normalize_test_name("vitamin b12") == "Vitamin B12"
        assert normalize_test_name("vitamin d") == "Vitamin D"
        assert normalize_test_name("folic acid") == "Folate"

    # ── Case insensitivity ───────────────────────────────────────────

    def test_case_insensitive(self):
        """Normalization should be case-insensitive."""
        assert normalize_test_name("HB") == "Hemoglobin"
        assert normalize_test_name("Hgb") == "Hemoglobin"
        assert normalize_test_name("TSH") == "TSH"

    def test_whitespace_handling(self):
        """Leading/trailing whitespace should be stripped."""
        assert normalize_test_name("  hb  ") == "Hemoglobin"
        assert normalize_test_name("  tsh ") == "TSH"

    # ── Unknown tests ────────────────────────────────────────────────

    def test_unknown_test_returns_none(self):
        """Unknown test names should return None."""
        assert normalize_test_name("random_unknown_test") is None
        assert normalize_test_name("xyz123") is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert normalize_test_name("") is None

    def test_none_input_returns_none(self):
        """None input should return None."""
        assert normalize_test_name(None) is None

    # ── Coagulation tests ────────────────────────────────────────────

    def test_coagulation_panel(self):
        """Coagulation test aliases should normalize correctly."""
        assert normalize_test_name("inr") == "INR"
        assert normalize_test_name("pt") == "PT"
        assert normalize_test_name("aptt") == "APTT"

    # ── Inflammatory markers ─────────────────────────────────────────

    def test_inflammatory_markers(self):
        """Inflammatory marker aliases should normalize correctly."""
        assert normalize_test_name("esr") == "ESR"
        assert normalize_test_name("crp") == "CRP"
        assert normalize_test_name("c-reactive protein") == "CRP"
