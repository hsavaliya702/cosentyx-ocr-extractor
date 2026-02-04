"""Attestation extractor for prescriber signature and verification."""

from typing import Dict
from src.extraction.base_extractor import BaseExtractor
from src.models.attestation import AttestationInfo, AttestationField
from src.validation.field_validators import FieldValidators
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AttestationExtractor(BaseExtractor):
    """Extract prescriber attestation information."""

    FIELD_MAPPINGS = {
        "name": [
            "prescriber signature",
            "signature name",
            "signed by",
            "prescriber name",
            "physician name",
            "attestation name",
        ],
        "date": ["signature date", "date signed", "attestation date", "sign date"],
    }

    def extract(
        self, textract_data: Dict, payload_data: Dict = None
    ) -> AttestationInfo:
        """Extract attestation information.

        Args:
            textract_data: Parsed Textract data
            payload_data: Optional payload data

        Returns:
            AttestationInfo: Extracted and validated attestation information
        """
        logger.info("Extracting attestation information")

        forms = textract_data.get("forms", {})
        signatures = textract_data.get("signatures", [])
        attestation_info = AttestationInfo()

        # Detect signature presence
        if signatures:
            attestation_info.signature_present = True
            # Use highest confidence signature
            attestation_info.signature_confidence = max(
                sig.get("confidence", 0.0) for sig in signatures
            )
        else:
            attestation_info.signature_present = False
            attestation_info.signature_confidence = 0.0

        # Extract attestation name
        attestation_info.name = self._extract_name(forms, payload_data)

        # Extract attestation date
        attestation_info.date = self._extract_date(forms, payload_data)

        logger.info(
            f"Attestation extraction complete. Valid: {attestation_info.is_valid()}"
        )
        return attestation_info

    def _extract_name(self, forms: Dict, payload_data: Dict = None) -> AttestationField:
        """Extract and validate attestation name."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS["name"])
        source = "form"

        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(
                payload_data, ["attestation_name", "prescriber_name"]
            )
            if value:
                source = "payload"
                confidence = 1.0

        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "Attestation name"
        )

        return AttestationField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
        )

    def _extract_date(self, forms: Dict, payload_data: Dict = None) -> AttestationField:
        """Extract and validate attestation date."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS["date"])
        source = "form"
        original_value = value

        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(
                payload_data, ["attestation_date", "signature_date"]
            )
            if value:
                source = "payload"
                confidence = 1.0
                original_value = value

        # Validate and format
        is_valid, validated_value, error = FieldValidators.validate_date(value or "")

        return AttestationField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=(
                original_value if original_value != validated_value else None
            ),
        )
