"""Patient data models."""
from typing import Optional
from pydantic import BaseModel, Field


class PatientField(BaseModel):
    """Individual patient field with metadata."""
    
    value: Optional[str] = None
    source: str = Field(default="form", description="Source of the field: 'form' or 'payload'")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    validated: bool = Field(default=False, description="Whether field passed validation")
    original_value: Optional[str] = Field(default=None, description="Original value before formatting")


class PatientInfo(BaseModel):
    """Patient information model."""
    
    first_name: PatientField = Field(default_factory=PatientField)
    last_name: PatientField = Field(default_factory=PatientField)
    dob: PatientField = Field(default_factory=PatientField, description="Date of birth (MM/DD/YYYY)")
    gender: PatientField = Field(default_factory=PatientField, description="Gender (M/F/Other)")
    phone: PatientField = Field(default_factory=PatientField)
    email: PatientField = Field(default_factory=PatientField)
    preferred_language: PatientField = Field(default_factory=PatientField)

    def is_valid(self) -> bool:
        """Check if patient info has all required fields validated.
        
        Returns:
            bool: True if all mandatory fields are validated
        """
        return (
            self.first_name.validated
            and self.last_name.validated
            and self.dob.validated
            and self.gender.validated
        )

    def get_signature(self) -> str:
        """Get unique signature for duplicate detection.
        
        Returns:
            str: Unique signature (FirstName_LastName_DOB)
        """
        first = self.first_name.value or ""
        last = self.last_name.value or ""
        dob = self.dob.value or ""
        return f"{first}_{last}_{dob}".lower()
