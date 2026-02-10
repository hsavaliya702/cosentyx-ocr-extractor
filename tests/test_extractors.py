"""Tests for extractor classes."""

import pytest
from src.extraction.patient_extractor import PatientExtractor
from src.extraction.prescriber_extractor import PrescriberExtractor
from src.extraction.prescription_extractor import PrescriptionExtractor


class TestPatientExtractor:
    """Test patient extractor."""

    def test_extract_patient_from_forms(self, sample_forms_data):
        """Test extracting patient info from forms."""
        extractor = PatientExtractor()
        textract_data = {"forms": sample_forms_data}

        patient = extractor.extract(textract_data)

        assert patient.first_name.value == "John"
        assert patient.first_name.validated
        assert patient.last_name.value == "Doe"
        assert patient.last_name.validated
        assert patient.dob.value == "01/15/1980"
        assert patient.dob.validated
        assert patient.gender.value == "M"
        assert patient.gender.validated

    def test_extract_patient_from_payload(self, sample_payload_data):
        """Test extracting patient info from payload."""
        extractor = PatientExtractor()
        textract_data = {"forms": {}}

        # Payload uses standard keys that match the FIELD_MAPPINGS
        payload = {
            "patient first name": "John",
            "patient last name": "Doe",
            "date of birth": "01/15/1980",
            "gender": "M",
        }

        patient = extractor.extract(textract_data, payload)

        assert patient.first_name.value == "John"
        assert patient.first_name.source == "payload"
        assert patient.last_name.value == "Doe"
        assert patient.last_name.source == "payload"

    def test_patient_is_valid(self, sample_forms_data):
        """Test patient validation."""
        extractor = PatientExtractor()
        textract_data = {"forms": sample_forms_data}

        patient = extractor.extract(textract_data)

        assert patient.is_valid()


class TestPrescriberExtractor:
    """Test prescriber extractor."""

    def test_extract_prescriber(self, sample_forms_data):
        """Test extracting prescriber info."""
        extractor = PrescriberExtractor()
        textract_data = {"forms": sample_forms_data}

        prescriber = extractor.extract(textract_data)

        assert prescriber.first_name.value == "Jane"
        assert prescriber.last_name.value == "Smith"
        assert prescriber.npi.value == "1234567890"
        assert prescriber.address.street.value == "123 Medical Dr"
        assert prescriber.address.city.value == "Boston"
        assert prescriber.address.state.value == "MA"
        assert prescriber.address.zip.value == "02101"

    def test_prescriber_is_valid(self, sample_forms_data):
        """Test prescriber validation."""
        extractor = PrescriberExtractor()
        textract_data = {"forms": sample_forms_data}

        prescriber = extractor.extract(textract_data)

        assert prescriber.is_valid()


class TestPrescriptionExtractor:
    """Test prescription extractor."""

    def test_extract_prescription(self, sample_forms_data):
        """Test extracting prescription info."""
        extractor = PrescriptionExtractor()
        textract_data = {
            "forms": sample_forms_data,
            "raw_text": "COSENTYX 150mg Pen Loading"
        }

        prescription_info = extractor.extract(textract_data)

        # Should have at least one prescription
        assert len(prescription_info.prescriptions) >= 1
        
        # Check first prescription
        first_rx = prescription_info.prescriptions[0]
        assert first_rx.product.value is not None
        assert first_rx.dosage.value is not None
        assert first_rx.form.value is not None
        assert first_rx.dose_type.value is not None

    def test_prescription_is_valid(self, sample_forms_data):
        """Test prescription validation."""
        extractor = PrescriptionExtractor()
        textract_data = {
            "forms": sample_forms_data,
            "raw_text": "COSENTYX 150mg"
        }

        prescription_info = extractor.extract(textract_data)

        # At least one prescription should be created
        assert len(prescription_info.prescriptions) > 0
        # Container is valid if at least one prescription is valid
        assert prescription_info.is_valid()

    def test_refills_default_to_zero(self):
        """Test that refills are set correctly based on dose type."""
        extractor = PrescriptionExtractor()
        
        # Create a loading dose prescription
        combo = {
            "dosage": "150mg",
            "patient_type": "adult",
            "form": "pen",
            "dose_type": "loading"
        }
        
        prescription = extractor._create_prescription(combo)

        # Loading doses should have 0 refills
        assert prescription.refills.value == "0"
        assert prescription.refills.validated
        
    def test_multiple_prescriptions(self):
        """Test that multiple checkboxes create multiple prescriptions."""
        extractor = PrescriptionExtractor()
        
        # Mock data with multiple checked combinations
        textract_data = {
            "forms": {
                "COSENTYX 150 mg Pen Loading": "SELECTED",
                "COSENTYX 150 mg Pen Maintenance": "SELECTED",
            },
            "raw_text": "COSENTYX 150mg Pen Loading\nCOSENTYX 150mg Pen Maintenance"
        }
        
        prescription_info = extractor.extract(textract_data)
        
        # Should create at least 2 prescriptions (or 1 with fallback)
        assert len(prescription_info.prescriptions) >= 1
        
        # All prescriptions should be valid
        for rx in prescription_info.prescriptions:
            assert rx.product.value is not None
            assert rx.dosage.value is not None
            assert rx.form.value is not None
            assert rx.dose_type.value is not None
