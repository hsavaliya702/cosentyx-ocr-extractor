"""Business logic validation and rules."""

from typing import Dict, List, Tuple
from src.models.extraction_result import ExtractionResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BusinessRules:
    """Business logic validation and routing rules."""

    def __init__(self):
        """Initialize business rules."""
        self.duplicate_signatures = set()

    def check_duplicate(self, result: ExtractionResult) -> Tuple[bool, str]:
        """Check for duplicate submission.

        Args:
            result: Extraction result

        Returns:
            Tuple[bool, str]: (is_duplicate, signature)
        """
        # Create signature from patient + prescriptions
        patient_sig = result.patient.get_signature()
        prescription_sigs = result.prescription.get_signatures()

        # Combine patient signature with all prescription signatures
        combined_sig = f"{patient_sig}_{'_'.join(sorted(prescription_sigs))}"

        if combined_sig in self.duplicate_signatures:
            logger.warning(f"Duplicate detected: {combined_sig}")
            return True, combined_sig

        self.duplicate_signatures.add(combined_sig)
        return False, combined_sig

    def validate_document_type(self, document_type: str) -> bool:
        """Validate that document type is acceptable.

        Args:
            document_type: Document type from classifier

        Returns:
            bool: True if document type is acceptable
        """
        acceptable_types = ["ema_start_form", "cosentyx_start_form"]
        return document_type in acceptable_types

    def apply_routing_rules(self, result: ExtractionResult) -> None:
        """Apply business rules and determine routing.

        Args:
            result: Extraction result (modified in place)
        """
        # Check document type
        if not self.validate_document_type(result.document_type):
            result.validation_errors.append(
                f"Invalid document type: {result.document_type}"
            )
            result.validation_status = "failed"
            result.routing.action = "manual_review"
            result.routing.manual_review_required = True
            result.routing.review_reason = "Invalid document type"
            return

        # Apply routing logic based on validation results
        result.determine_routing()

        # Check for low confidence fields
        self._check_low_confidence_warnings(result)

    def _check_low_confidence_warnings(self, result: ExtractionResult) -> None:
        """Check for low confidence fields and add warnings.

        Args:
            result: Extraction result (modified in place)
        """
        low_confidence_threshold = 0.85

        # Check patient fields
        for field_name, field in [
            ("first_name", result.patient.first_name),
            ("last_name", result.patient.last_name),
            ("dob", result.patient.dob),
            ("gender", result.patient.gender),
            ("phone", result.patient.phone),
            ("email", result.patient.email),
        ]:
            if field.value and field.confidence < low_confidence_threshold:
                result.warnings.append(
                    f"Low confidence on patient.{field_name} field ({field.confidence:.2f})"
                )

        # Check prescriber fields
        for field_name, field in [
            ("first_name", result.prescriber.first_name),
            ("last_name", result.prescriber.last_name),
            ("npi", result.prescriber.npi),
            ("phone", result.prescriber.phone),
        ]:
            if field.value and field.confidence < low_confidence_threshold:
                result.warnings.append(
                    f"Low confidence on prescriber.{field_name} field ({field.confidence:.2f})"
                )

        # Check prescription fields (for each prescription)
        for i, prescription in enumerate(result.prescription.prescriptions):
            for field_name, field in [
                ("product", prescription.product),
                ("dosage", prescription.dosage),
                ("form", prescription.form),
                ("dose_type", prescription.dose_type),
                ("quantity", prescription.quantity),
            ]:
                if field.value and field.confidence < low_confidence_threshold:
                    result.warnings.append(
                        f"Low confidence on prescription[{i}].{field_name} field ({field.confidence:.2f})"
                    )
