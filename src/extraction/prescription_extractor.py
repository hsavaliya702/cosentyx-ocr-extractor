"""Prescription information extractor."""

from typing import Dict
from src.extraction.base_extractor import BaseExtractor
from src.models.prescription import PrescriptionInfo, PrescriptionField
from src.validation.field_validators import FieldValidators
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PrescriptionExtractor(BaseExtractor):
    """Extract prescription information from form data."""

    FIELD_MAPPINGS = {
        "product": [
            "product",
            "drug",
            "medication",
            "drug name",
            "product name",
            "cosentyx",
            "medicine",
        ],
        "dosage": ["dosage", "dose", "strength", "drug strength", "product strength"],
        "quantity": ["quantity", "qty", "amount", "number of units", "units"],
        "sig": [
            "sig",
            "directions",
            "instructions",
            "directions for use",
            "how to use",
            "administration",
        ],
        "refills": ["refills", "number of refills", "refill", "rx refills"],
    }

    def extract(
        self, textract_data: Dict, payload_data: Dict = None
    ) -> PrescriptionInfo:
        """Extract prescription information.

        Args:
            textract_data: Parsed Textract data
            payload_data: Optional payload data

        Returns:
            PrescriptionInfo: Extracted and validated prescription information
        """
        logger.info("Extracting prescription information")

        forms = textract_data.get("forms", {})
        prescription_info = PrescriptionInfo()

        # Extract fields
        prescription_info.product = self._extract_product(forms, payload_data)
        prescription_info.dosage = self._extract_dosage(forms, payload_data)
        prescription_info.quantity = self._extract_quantity(forms, payload_data)
        prescription_info.sig = self._extract_sig(forms, payload_data)
        prescription_info.refills = self._extract_refills(forms, payload_data)

        logger.info(
            f"Prescription extraction complete. Valid: {prescription_info.is_valid()}"
        )
        return prescription_info

    def _extract_product(
        self, forms: Dict, payload_data: Dict = None
    ) -> PrescriptionField:
        """Extract and validate product name."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS["product"])
        source = "form"

        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ["product", "drug_name"])
            if value:
                source = "payload"
                confidence = 1.0

        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "Product name"
        )

        return PrescriptionField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
        )

    def _extract_dosage(
        self, forms: Dict, payload_data: Dict = None
    ) -> PrescriptionField:
        """Extract and validate dosage."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS["dosage"])
        source = "form"

        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ["dosage", "dose", "strength"])
            if value:
                source = "payload"
                confidence = 1.0

        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "Dosage"
        )

        return PrescriptionField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
        )

    def _extract_quantity(
        self, forms: Dict, payload_data: Dict = None
    ) -> PrescriptionField:
        """Extract and validate quantity."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS["quantity"])
        source = "form"

        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ["quantity", "qty"])
            if value:
                source = "payload"
                confidence = 1.0

        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "Quantity"
        )

        return PrescriptionField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
        )

    def _extract_sig(self, forms: Dict, payload_data: Dict = None) -> PrescriptionField:
        """Extract and validate SIG (directions)."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS["sig"])
        source = "form"

        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(
                payload_data, ["sig", "directions", "instructions"]
            )
            if value:
                source = "payload"
                confidence = 1.0

        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "SIG"
        )

        return PrescriptionField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
        )

    def _extract_refills(
        self, forms: Dict, payload_data: Dict = None
    ) -> PrescriptionField:
        """Extract and validate refills (default to 0 if missing)."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS["refills"])
        source = "form"

        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ["refills", "refill"])
            if value:
                source = "payload"
                confidence = 1.0

        # Default to "0" if not found
        if not value:
            value = "0"
            confidence = 1.0

        # Always valid (defaulted)
        return PrescriptionField(
            value=value, source=source, confidence=confidence, validated=True
        )
