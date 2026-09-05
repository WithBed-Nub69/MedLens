"""
Reference range status calculation.
DETERMINISTIC Python logic — never trust LLM to decide LOW/NORMAL/HIGH.
"""
from typing import Optional
from app.models.schemas import TestStatus


def calculate_status(
    value: Optional[float],
    reference_low: Optional[float],
    reference_high: Optional[float],
) -> TestStatus:
    """
    Deterministically compute LOW / NORMAL / HIGH / UNKNOWN.

    Rules:
    - If value is missing → UNKNOWN
    - If both reference bounds are missing → UNKNOWN
    - If value < reference_low → LOW
    - If value > reference_high → HIGH
    - Otherwise → NORMAL

    Partial ranges are handled gracefully:
    - Only low bound: if value < low → LOW, else NORMAL
    - Only high bound: if value > high → HIGH, else NORMAL
    """
    if value is None:
        return TestStatus.unknown

    has_low = reference_low is not None
    has_high = reference_high is not None

    if not has_low and not has_high:
        return TestStatus.unknown

    if has_low and value < reference_low:
        return TestStatus.low

    if has_high and value > reference_high:
        return TestStatus.high

    return TestStatus.normal
