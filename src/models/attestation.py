"""Attestation data models."""

from typing import Optional
from pydantic import BaseModel, Field


class AttestationField(BaseModel):
    """Individual attestation field with metadata."""

    value: Optional[str] = None
    source: str = Field(default="form", description="Source of the field")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score"
    )
    validated: bool = Field(
        default=False, description="Whether field passed validation"
    )
    original_value: Optional[str] = Field(
        default=None, description="Original value before formatting"
    )


class AttestationInfo(BaseModel):
    """Prescriber attestation model."""

    signature_present: bool = Field(
        default=False, description="Whether signature is present"
    )
    signature_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Signature detection confidence"
    )
    name: AttestationField = Field(
        default_factory=AttestationField, description="Prescriber name on attestation"
    )
    date: AttestationField = Field(
        default_factory=AttestationField, description="Attestation date"
    )

    def is_valid(self) -> bool:
        """Check if attestation is valid.

        Returns:
            bool: True if attestation is complete and valid
        """
        return self.signature_present and self.name.validated and self.date.validated
