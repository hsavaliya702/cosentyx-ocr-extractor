"""Prescriber data models."""
from typing import Optional
from pydantic import BaseModel, Field


class PrescriberField(BaseModel):
    """Individual prescriber field with metadata."""
    
    value: Optional[str] = None
    source: str = Field(default="form", description="Source of the field")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    validated: bool = Field(default=False, description="Whether field passed validation")
    original_value: Optional[str] = Field(default=None, description="Original value before formatting")


class Address(BaseModel):
    """Address information."""
    
    street: PrescriberField = Field(default_factory=PrescriberField)
    city: PrescriberField = Field(default_factory=PrescriberField)
    state: PrescriberField = Field(default_factory=PrescriberField)
    zip: PrescriberField = Field(default_factory=PrescriberField)

    def is_valid(self) -> bool:
        """Check if address has all required fields validated.
        
        Returns:
            bool: True if all fields are validated
        """
        return (
            self.street.validated
            and self.city.validated
            and self.state.validated
            and self.zip.validated
        )


class PrescriberInfo(BaseModel):
    """Prescriber information model."""
    
    first_name: PrescriberField = Field(default_factory=PrescriberField)
    last_name: PrescriberField = Field(default_factory=PrescriberField)
    npi: PrescriberField = Field(default_factory=PrescriberField, description="10-digit NPI")
    address: Address = Field(default_factory=Address)
    phone: PrescriberField = Field(default_factory=PrescriberField)
    fax: PrescriberField = Field(default_factory=PrescriberField)

    def is_valid(self) -> bool:
        """Check if prescriber info has all required fields validated.
        
        Returns:
            bool: True if all mandatory fields are validated
        """
        has_contact = self.phone.validated or self.fax.validated
        return (
            self.first_name.validated
            and self.last_name.validated
            and self.npi.validated
            and self.address.is_valid()
            and has_contact
        )
