"""Prescription data models."""

from typing import Optional, List
from pydantic import BaseModel, Field


class PrescriptionField(BaseModel):
    """Individual prescription field with metadata."""

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


class SinglePrescription(BaseModel):
    """Individual prescription entry (one product + form + dose type combination)."""

    product: PrescriptionField = Field(
        default_factory=PrescriptionField, description="Product name (e.g., COSENTYX 150mg)"
    )
    dosage: PrescriptionField = Field(
        default_factory=PrescriptionField, description="Dosage (e.g., 150mg, 300mg, 75mg)"
    )
    form: PrescriptionField = Field(
        default_factory=PrescriptionField, description="Drug form (Pen, Syringe, Unoready)"
    )
    dose_type: PrescriptionField = Field(
        default_factory=PrescriptionField, description="Dose type (Loading, Maintenance, Maintenance Increase)"
    )
    patient_type: PrescriptionField = Field(
        default_factory=PrescriptionField, description="Patient type (Adult, Pediatric)"
    )
    quantity: PrescriptionField = Field(default_factory=PrescriptionField)
    sig: PrescriptionField = Field(
        default_factory=PrescriptionField, description="Directions for use"
    )
    refills: PrescriptionField = Field(default_factory=PrescriptionField)

    def is_valid(self) -> bool:
        """Check if prescription has all required fields validated.

        Returns:
            bool: True if all mandatory fields are validated
        """
        return (
            self.product.validated
            and self.dosage.validated
            and self.form.validated
            and self.dose_type.validated
            and self.quantity.validated
            and self.sig.validated
        )

    def get_signature(self) -> str:
        """Get unique signature for duplicate detection.

        Returns:
            str: Unique signature (Product_Dosage_Form_DoseType)
        """
        product = self.product.value or ""
        dosage = self.dosage.value or ""
        form = self.form.value or ""
        dose_type = self.dose_type.value or ""
        return f"{product}_{dosage}_{form}_{dose_type}".lower()
    
    def get_display_name(self) -> str:
        """Get display name for the prescription.

        Returns:
            str: Display name (e.g., "COSENTYX 150mg Pen Loading")
        """
        product = self.product.value or "COSENTYX"
        dosage = self.dosage.value or ""
        form = self.form.value or ""
        dose_type = self.dose_type.value or ""
        return f"{product} {dosage} {form} {dose_type}".strip()


class PrescriptionInfo(BaseModel):
    """Container for multiple prescriptions extracted from the form."""

    prescriptions: List[SinglePrescription] = Field(
        default_factory=list, 
        description="List of all prescriptions (combinations of product, form, and dose type)"
    )

    def is_valid(self) -> bool:
        """Check if at least one prescription is valid.

        Returns:
            bool: True if at least one prescription is validated
        """
        return any(rx.is_valid() for rx in self.prescriptions)
    
    def get_valid_prescriptions(self) -> List[SinglePrescription]:
        """Get list of valid prescriptions.

        Returns:
            List[SinglePrescription]: Valid prescriptions
        """
        return [rx for rx in self.prescriptions if rx.is_valid()]
    
    def get_signatures(self) -> List[str]:
        """Get unique signatures for all prescriptions.

        Returns:
            List[str]: List of signatures
        """
        return [rx.get_signature() for rx in self.prescriptions]
