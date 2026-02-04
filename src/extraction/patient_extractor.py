"""Patient information extractor."""
from typing import Dict, Optional
from src.extraction.base_extractor import BaseExtractor
from src.models.patient import PatientInfo, PatientField
from src.validation.field_validators import FieldValidators
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PatientExtractor(BaseExtractor):
    """Extract patient information from form data."""

    FIELD_MAPPINGS = {
        'first_name': [
            'patient first name', 'first name', 'fname', 'patient fname',
            'member first name', 'member fname'
        ],
        'last_name': [
            'patient last name', 'last name', 'lname', 'patient lname',
            'member last name', 'member lname'
        ],
        'dob': [
            'date of birth', 'dob', 'birth date', 'birthdate', 'patient dob',
            'member dob', 'date birth'
        ],
        'gender': [
            'sex', 'gender', 'patient gender', 'patient sex', 'member gender'
        ],
        'phone': [
            'phone', 'telephone', 'phone number', 'patient phone',
            'member phone', 'contact phone', 'tel'
        ],
        'email': [
            'email', 'email address', 'patient email', 'member email',
            'e-mail', 'e-mail address'
        ],
        'preferred_language': [
            'preferred language', 'language', 'language preference',
            'patient language'
        ]
    }

    def extract(self, textract_data: Dict, payload_data: Dict = None) -> PatientInfo:
        """Extract patient information.
        
        Args:
            textract_data: Parsed Textract data
            payload_data: Optional payload data
            
        Returns:
            PatientInfo: Extracted and validated patient information
        """
        logger.info("Extracting patient information")
        
        forms = textract_data.get("forms", {})
        patient_info = PatientInfo()
        
        # Extract first name
        patient_info.first_name = self._extract_first_name(forms, payload_data)
        
        # Extract last name
        patient_info.last_name = self._extract_last_name(forms, payload_data)
        
        # Extract date of birth
        patient_info.dob = self._extract_dob(forms, payload_data)
        
        # Extract gender
        patient_info.gender = self._extract_gender(forms, payload_data)
        
        # Extract phone (optional)
        patient_info.phone = self._extract_phone(forms, payload_data)
        
        # Extract email (optional)
        patient_info.email = self._extract_email(forms, payload_data)
        
        # Extract preferred language (optional)
        patient_info.preferred_language = self._extract_preferred_language(forms, payload_data)
        
        logger.info(f"Patient extraction complete. Valid: {patient_info.is_valid()}")
        return patient_info

    def _extract_first_name(self, forms: Dict, payload_data: Dict = None) -> PatientField:
        """Extract and validate first name."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['first_name'])
        source = "form"
        
        # Try payload if not found in form
        if not value and payload_data:
            value = self.get_from_payload(payload_data, self.FIELD_MAPPINGS['first_name'])
            if value:
                source = "payload"
                confidence = 1.0
        
        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "First name"
        )
        
        return PatientField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=None
        )

    def _extract_last_name(self, forms: Dict, payload_data: Dict = None) -> PatientField:
        """Extract and validate last name."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['last_name'])
        source = "form"
        
        # Try payload if not found in form
        if not value and payload_data:
            value = self.get_from_payload(payload_data, self.FIELD_MAPPINGS['last_name'])
            if value:
                source = "payload"
                confidence = 1.0
        
        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "Last name"
        )
        
        return PatientField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=None
        )

    def _extract_dob(self, forms: Dict, payload_data: Dict = None) -> PatientField:
        """Extract and validate date of birth."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['dob'])
        source = "form"
        original_value = value
        
        # Try payload if not found in form
        if not value and payload_data:
            value = self.get_from_payload(payload_data, self.FIELD_MAPPINGS['dob'])
            if value:
                source = "payload"
                confidence = 1.0
                original_value = value
        
        # Validate and format
        is_valid, validated_value, error = FieldValidators.validate_date(value or "")
        
        return PatientField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=original_value if original_value != validated_value else None
        )

    def _extract_gender(self, forms: Dict, payload_data: Dict = None) -> PatientField:
        """Extract and validate gender."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['gender'])
        source = "form"
        original_value = value
        
        # Try payload if not found in form
        if not value and payload_data:
            value = self.get_from_payload(payload_data, self.FIELD_MAPPINGS['gender'])
            if value:
                source = "payload"
                confidence = 1.0
                original_value = value
        
        # Validate and normalize
        is_valid, validated_value, error = FieldValidators.validate_gender(value or "")
        
        return PatientField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=original_value if original_value != validated_value else None
        )

    def _extract_phone(self, forms: Dict, payload_data: Dict = None) -> PatientField:
        """Extract and validate phone number (optional)."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['phone'])
        source = "form"
        original_value = value
        
        # Try payload if not found in form
        if not value and payload_data:
            value = self.get_from_payload(payload_data, self.FIELD_MAPPINGS['phone'])
            if value:
                source = "payload"
                confidence = 1.0
                original_value = value
        
        # Validate and format (optional field)
        if value:
            is_valid, validated_value, error = FieldValidators.validate_phone(value)
        else:
            is_valid, validated_value = True, None  # Optional field
        
        return PatientField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=original_value if original_value != validated_value else None
        )

    def _extract_email(self, forms: Dict, payload_data: Dict = None) -> PatientField:
        """Extract and validate email (optional)."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['email'])
        source = "form"
        
        # Try payload if not found in form
        if not value and payload_data:
            value = self.get_from_payload(payload_data, self.FIELD_MAPPINGS['email'])
            if value:
                source = "payload"
                confidence = 1.0
        
        # Validate (optional field)
        if value:
            is_valid, validated_value, error = FieldValidators.validate_email(value)
        else:
            is_valid, validated_value = True, None  # Optional field
        
        return PatientField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=None
        )

    def _extract_preferred_language(self, forms: Dict, payload_data: Dict = None) -> PatientField:
        """Extract preferred language (optional)."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['preferred_language'])
        source = "form"
        
        # Try payload if not found in form
        if not value and payload_data:
            value = self.get_from_payload(payload_data, self.FIELD_MAPPINGS['preferred_language'])
            if value:
                source = "payload"
                confidence = 1.0
        
        # Optional field - always valid
        return PatientField(
            value=value,
            source=source,
            confidence=confidence,
            validated=True,
            original_value=None
        )
