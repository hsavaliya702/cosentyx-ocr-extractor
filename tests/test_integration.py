"""Integration tests for complete processing pipeline."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.processor import CosentyxFormProcessor
from src.models.extraction_result import ExtractionResult


class TestIntegration:
    """Integration tests for complete pipeline."""

    @patch("src.processor.TextractClient")
    @patch("src.processor.BedrockClassifier")
    def test_complete_pipeline_success(
        self,
        mock_classifier_class,
        mock_textract_class,
        sample_document_bytes,
        sample_forms_data,
    ):
        """Test complete processing pipeline with valid form."""
        # Setup mocks
        mock_textract = Mock()
        mock_textract.analyze_document.return_value = {"Blocks": []}
        mock_textract_class.return_value = mock_textract

        mock_classifier = Mock()
        mock_classifier.classify_document.return_value = ("ema_start_form", 0.95)
        mock_classifier_class.return_value = mock_classifier

        # Create processor
        processor = CosentyxFormProcessor()

        # Mock textract data
        with patch.object(processor.parser, "parse_response") as mock_parse:
            mock_parse.return_value = {
                "raw_text": "Sample form text",
                "forms": sample_forms_data,
                "tables": [],
                "checkboxes": {},
                "signatures": [{"confidence": 0.9}],
                "blocks": [],
            }

            # Process document
            result = processor.process_document(sample_document_bytes)

        # Assertions
        assert isinstance(result, ExtractionResult)
        assert result.document_type == "ema_start_form"
        assert result.classification_confidence == 0.95
        assert result.patient.first_name.value == "John"
        assert result.prescriber.first_name.value == "Jane"
        assert result.prescription.product.value == "Cosentyx"

    @patch("src.processor.TextractClient")
    @patch("src.processor.BedrockClassifier")
    def test_pipeline_with_invalid_document_type(
        self, mock_classifier_class, mock_textract_class, sample_document_bytes
    ):
        """Test pipeline with invalid document type."""
        # Setup mocks
        mock_textract = Mock()
        mock_textract.analyze_document.return_value = {"Blocks": []}
        mock_textract_class.return_value = mock_textract

        mock_classifier = Mock()
        mock_classifier.classify_document.return_value = ("cover_letter", 0.98)
        mock_classifier_class.return_value = mock_classifier

        # Create processor
        processor = CosentyxFormProcessor()

        # Mock textract data
        with patch.object(processor.parser, "parse_response") as mock_parse:
            mock_parse.return_value = {
                "raw_text": "Cover letter text",
                "forms": {},
                "tables": [],
                "checkboxes": {},
                "signatures": [],
                "blocks": [],
            }

            # Process document
            result = processor.process_document(sample_document_bytes)

        # Assertions
        assert result.document_type == "cover_letter"
        assert result.validation_status == "failed"
        assert result.routing.action == "manual_review"
        assert "Invalid document type" in result.routing.review_reason

    @patch("src.processor.TextractClient")
    @patch("src.processor.BedrockClassifier")
    def test_pipeline_with_missing_prescriber(
        self,
        mock_classifier_class,
        mock_textract_class,
        sample_document_bytes,
        sample_forms_data,
    ):
        """Test pipeline with missing prescriber info."""
        # Setup mocks
        mock_textract = Mock()
        mock_textract.analyze_document.return_value = {"Blocks": []}
        mock_textract_class.return_value = mock_textract

        mock_classifier = Mock()
        mock_classifier.classify_document.return_value = ("ema_start_form", 0.95)
        mock_classifier_class.return_value = mock_classifier

        # Create processor
        processor = CosentyxFormProcessor()

        # Remove prescriber data
        forms_data = sample_forms_data.copy()
        del forms_data["prescriber first name"]
        del forms_data["prescriber last name"]
        del forms_data["npi"]

        # Mock textract data
        with patch.object(processor.parser, "parse_response") as mock_parse:
            mock_parse.return_value = {
                "raw_text": "Sample form text",
                "forms": forms_data,
                "tables": [],
                "checkboxes": {},
                "signatures": [{"confidence": 0.9}],
                "blocks": [],
            }

            # Process document
            result = processor.process_document(sample_document_bytes)

        # Assertions
        assert result.routing.action == "create_patient_only"
        assert result.routing.create_patient_profile
        assert not result.routing.create_prescriber_profile
        assert result.routing.manual_review_required
        assert "prescriber" in result.routing.review_reason.lower()

    def test_routing_decision_logic(self):
        """Test routing decision logic."""
        result = ExtractionResult()
        result.document_type = "ema_start_form"

        # All valid
        result.patient.first_name.validated = True
        result.patient.last_name.validated = True
        result.patient.dob.validated = True
        result.patient.gender.validated = True

        result.prescriber.first_name.validated = True
        result.prescriber.last_name.validated = True
        result.prescriber.npi.validated = True
        result.prescriber.address.street.validated = True
        result.prescriber.address.city.validated = True
        result.prescriber.address.state.validated = True
        result.prescriber.address.zip.validated = True
        result.prescriber.phone.validated = True

        result.prescription.product.validated = True
        result.prescription.dosage.validated = True
        result.prescription.quantity.validated = True
        result.prescription.sig.validated = True

        result.attestation.signature_present = True
        result.attestation.name.validated = True
        result.attestation.date.validated = True

        result.determine_routing()

        assert result.routing.action == "create_full_profile"
        assert result.routing.create_patient_profile
        assert result.routing.create_prescriber_profile
        assert result.routing.create_prescription
        assert not result.routing.manual_review_required
        assert result.validation_status == "complete"
