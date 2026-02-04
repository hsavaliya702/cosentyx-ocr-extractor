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
        
        patient = extractor.extract(textract_data, sample_payload_data)
        
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
        textract_data = {"forms": sample_forms_data}
        
        prescription = extractor.extract(textract_data)
        
        assert prescription.product.value == "Cosentyx"
        assert prescription.dosage.value == "150mg"
        assert prescription.quantity.value == "2"
        assert prescription.sig.value == "Inject 1 pen weekly"
        assert prescription.refills.value == "3"

    def test_prescription_is_valid(self, sample_forms_data):
        """Test prescription validation."""
        extractor = PrescriptionExtractor()
        textract_data = {"forms": sample_forms_data}
        
        prescription = extractor.extract(textract_data)
        
        assert prescription.is_valid()

    def test_refills_default_to_zero(self):
        """Test that refills default to 0 when missing."""
        extractor = PrescriptionExtractor()
        textract_data = {"forms": {
            "product": "Cosentyx",
            "dosage": "150mg",
            "quantity": "2",
            "sig": "Inject 1 pen weekly"
        }}
        
        prescription = extractor.extract(textract_data)
        
        assert prescription.refills.value == "0"
        assert prescription.refills.validated
