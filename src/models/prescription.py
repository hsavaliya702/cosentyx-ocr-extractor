"""Prescription data models."""
from typing import Optional
from pydantic import BaseModel, Field


class PrescriptionField(BaseModel):
    """Individual prescription field with metadata."""
    
    value: Optional[str] = None
    source: str = Field(default="form", description="Source of the field")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    validated: bool = Field(default=False, description="Whether field passed validation")
    original_value: Optional[str] = Field(default=None, description="Original value before formatting")


class PrescriptionInfo(BaseModel):
    """Prescription information model."""
    
    product: PrescriptionField = Field(default_factory=PrescriptionField, description="Product name (Cosentyx/variant)")
    dosage: PrescriptionField = Field(default_factory=PrescriptionField, description="Dosage (e.g., 150mg, 300mg)")
    quantity: PrescriptionField = Field(default_factory=PrescriptionField)
    sig: PrescriptionField = Field(default_factory=PrescriptionField, description="Directions for use")
    refills: PrescriptionField = Field(default_factory=PrescriptionField)

    def is_valid(self) -> bool:
        """Check if prescription info has all required fields validated.
        
        Returns:
            bool: True if all mandatory fields are validated
        """
        return (
            self.product.validated
            and self.dosage.validated
            and self.quantity.validated
            and self.sig.validated
        )

    def get_signature(self) -> str:
        """Get unique signature for duplicate detection.
        
        Returns:
            str: Unique signature (Product_Dosage)
        """
        product = self.product.value or ""
        dosage = self.dosage.value or ""
        return f"{product}_{dosage}".lower()
