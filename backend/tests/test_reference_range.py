"""
Tests for reference range status calculation.
Tests the deterministic LOW/NORMAL/HIGH/UNKNOWN logic.
"""
import pytest
from app.utils.reference_range import calculate_status
from app.models.schemas import TestStatus


class TestCalculateStatus:
    """Test suite for the calculate_status utility function."""

    def test_normal_within_range(self):
        """Value within reference range should return NORMAL."""
        assert calculate_status(5.0, 3.0, 10.0) == TestStatus.normal

    def test_low_below_range(self):
        """Value below reference_low should return LOW."""
        assert calculate_status(2.0, 3.0, 10.0) == TestStatus.low

    def test_high_above_range(self):
        """Value above reference_high should return HIGH."""
        assert calculate_status(15.0, 3.0, 10.0) == TestStatus.high

    def test_value_at_lower_boundary(self):
        """Value exactly at reference_low should return NORMAL."""
        assert calculate_status(3.0, 3.0, 10.0) == TestStatus.normal

    def test_value_at_upper_boundary(self):
        """Value exactly at reference_high should return NORMAL."""
        assert calculate_status(10.0, 3.0, 10.0) == TestStatus.normal

    def test_none_value_returns_unknown(self):
        """None value should always return UNKNOWN."""
        assert calculate_status(None, 3.0, 10.0) == TestStatus.unknown

    def test_no_reference_bounds_returns_unknown(self):
        """Missing both reference bounds should return UNKNOWN."""
        assert calculate_status(5.0, None, None) == TestStatus.unknown

    def test_only_low_bound_value_below(self):
        """With only low bound, value below should return LOW."""
        assert calculate_status(2.0, 3.0, None) == TestStatus.low

    def test_only_low_bound_value_above(self):
        """With only low bound, value above should return NORMAL."""
        assert calculate_status(5.0, 3.0, None) == TestStatus.normal

    def test_only_high_bound_value_above(self):
        """With only high bound, value above should return HIGH."""
        assert calculate_status(15.0, None, 10.0) == TestStatus.high

    def test_only_high_bound_value_below(self):
        """With only high bound, value below should return NORMAL."""
        assert calculate_status(5.0, None, 10.0) == TestStatus.normal

    def test_zero_value_within_range(self):
        """Zero value within range should return NORMAL."""
        assert calculate_status(0.0, -1.0, 1.0) == TestStatus.normal

    def test_negative_values(self):
        """Negative values should be handled correctly."""
        assert calculate_status(-5.0, -3.0, 3.0) == TestStatus.low

    def test_large_values(self):
        """Very large values should return HIGH."""
        assert calculate_status(999999.0, 0.0, 100.0) == TestStatus.high

    def test_decimal_precision(self):
        """Decimal precision should be maintained."""
        assert calculate_status(4.51, 4.50, 5.00) == TestStatus.normal
        assert calculate_status(4.49, 4.50, 5.00) == TestStatus.low
