"""
Abstract AI provider interface.
Swap providers by implementing this protocol.
"""
from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    """Base class for all AI providers."""

    @abstractmethod
    async def extract_medical_report(
        self,
        content: bytes,
        content_type: str,
        filename: str,
    ) -> str:
        """
        Extract structured medical data from a document.
        Returns raw JSON string from the model.
        """
        ...

    @abstractmethod
    async def generate_summary(self, prompt: str) -> str:
        """Generate a patient-friendly summary from structured data."""
        ...

    @abstractmethod
    async def generate_clarifications(self, prompt: str) -> str:
        """Generate clarification questions from patient context."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier string."""
        ...
