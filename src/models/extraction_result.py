"""Complete extraction result model."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from src.models.patient import PatientInfo
from src.models.prescriber import PrescriberInfo
from src.models.prescription import PrescriptionInfo
from src.models.attestation import AttestationInfo


class RoutingDecision(BaseModel):
    """Routing decision based on validation results."""

    action: str = Field(
        default="manual_review",
        description="Action to take: 'create_full_profile', 'create_patient_only', or 'manual_review'",
    )
    create_patient_profile: bool = Field(default=False)
    create_prescriber_profile: bool = Field(default=False)
    create_prescription: bool = Field(default=False)
    manual_review_required: bool = Field(default=False)
    review_reason: Optional[str] = Field(
        default=None, description="Reason for manual review if required"
    )


class Metadata(BaseModel):
    """Processing metadata."""

    processing_time_ms: int = Field(description="Processing time in milliseconds")
    textract_cost_estimate: float = Field(description="Estimated Textract cost")
    bedrock_cost_estimate: float = Field(description="Estimated Bedrock cost")


class ExtractionResult(BaseModel):
    """Complete extraction result."""

    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_type: str = Field(
        description="Document type classification", default="unknown"
    )
    classification_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extraction_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    validation_status: str = Field(
        default="pending", description="Status: 'complete', 'partial', or 'failed'"
    )

    patient: PatientInfo = Field(default_factory=PatientInfo)
    prescriber: PrescriberInfo = Field(default_factory=PrescriberInfo)
    prescription: PrescriptionInfo = Field(default_factory=PrescriptionInfo)
    attestation: AttestationInfo = Field(default_factory=AttestationInfo)

    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    routing: RoutingDecision = Field(default_factory=RoutingDecision)
    metadata: Metadata = Field(
        default_factory=lambda: Metadata(
            processing_time_ms=0, textract_cost_estimate=0.0, bedrock_cost_estimate=0.0
        )
    )

    def determine_routing(self) -> None:
        """Determine routing decision based on validation results."""
        patient_valid = self.patient.is_valid()
        prescriber_valid = self.prescriber.is_valid()
        prescription_valid = self.prescription.is_valid()  # At least one prescription is valid
        attestation_valid = self.attestation.is_valid()

        # Determine routing action
        if patient_valid:
            if prescriber_valid:
                if prescription_valid:
                    if attestation_valid:
                        # All valid - create full profile
                        self.routing = RoutingDecision(
                            action="create_full_profile",
                            create_patient_profile=True,
                            create_prescriber_profile=True,
                            create_prescription=True,
                            manual_review_required=False,
                            review_reason=None,
                        )
                        self.validation_status = "complete"
                    else:
                        # Missing attestation
                        self.routing = RoutingDecision(
                            action="manual_review",
                            create_patient_profile=True,
                            create_prescriber_profile=True,
                            create_prescription=True,
                            manual_review_required=True,
                            review_reason="Missing or invalid attestation",
                        )
                        self.validation_status = "partial"
                else:
                    # Missing prescription
                    self.routing = RoutingDecision(
                        action="create_patient_only",
                        create_patient_profile=True,
                        create_prescriber_profile=False,
                        create_prescription=False,
                        manual_review_required=True,
                        review_reason="Missing or invalid prescription information",
                    )
                    self.validation_status = "partial"
            else:
                # Missing prescriber
                self.routing = RoutingDecision(
                    action="create_patient_only",
                    create_patient_profile=True,
                    create_prescriber_profile=False,
                    create_prescription=False,
                    manual_review_required=True,
                    review_reason="Missing or invalid prescriber information",
                )
                self.validation_status = "partial"
        else:
            # Missing patient
            self.routing = RoutingDecision(
                action="manual_review",
                create_patient_profile=False,
                create_prescriber_profile=False,
                create_prescription=False,
                manual_review_required=True,
                review_reason="Missing or invalid patient information",
            )
            self.validation_status = "failed"
