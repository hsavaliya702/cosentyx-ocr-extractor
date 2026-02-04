"""Prescriber information extractor."""
from typing import Dict
from src.extraction.base_extractor import BaseExtractor
from src.models.prescriber import PrescriberInfo, PrescriberField, Address
from src.validation.field_validators import FieldValidators
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PrescriberExtractor(BaseExtractor):
    """Extract prescriber information from form data."""

    FIELD_MAPPINGS = {
        'first_name': [
            'prescriber first name', 'physician first name', 'doctor first name',
            'dr first name', 'prescriber fname', 'physician fname'
        ],
        'last_name': [
            'prescriber last name', 'physician last name', 'doctor last name',
            'dr last name', 'prescriber lname', 'physician lname'
        ],
        'npi': [
            'npi', 'npi number', 'prescriber npi', 'physician npi',
            'national provider identifier'
        ],
        'street': [
            'prescriber address', 'physician address', 'address', 'street address',
            'street', 'prescriber street', 'office address'
        ],
        'city': [
            'city', 'prescriber city', 'physician city', 'office city'
        ],
        'state': [
            'state', 'prescriber state', 'physician state', 'office state'
        ],
        'zip': [
            'zip', 'zip code', 'zipcode', 'postal code', 'prescriber zip',
            'physician zip'
        ],
        'phone': [
            'prescriber phone', 'physician phone', 'office phone', 'phone',
            'prescriber telephone', 'office telephone'
        ],
        'fax': [
            'fax', 'fax number', 'prescriber fax', 'physician fax', 'office fax'
        ]
    }

    def extract(self, textract_data: Dict, payload_data: Dict = None) -> PrescriberInfo:
        """Extract prescriber information.
        
        Args:
            textract_data: Parsed Textract data
            payload_data: Optional payload data
            
        Returns:
            PrescriberInfo: Extracted and validated prescriber information
        """
        logger.info("Extracting prescriber information")
        
        forms = textract_data.get("forms", {})
        prescriber_info = PrescriberInfo()
        
        # Extract basic info
        prescriber_info.first_name = self._extract_first_name(forms, payload_data)
        prescriber_info.last_name = self._extract_last_name(forms, payload_data)
        prescriber_info.npi = self._extract_npi(forms, payload_data)
        
        # Extract address
        prescriber_info.address = self._extract_address(forms, payload_data)
        
        # Extract contact info
        prescriber_info.phone = self._extract_phone(forms, payload_data)
        prescriber_info.fax = self._extract_fax(forms, payload_data)
        
        logger.info(f"Prescriber extraction complete. Valid: {prescriber_info.is_valid()}")
        return prescriber_info

    def _extract_first_name(self, forms: Dict, payload_data: Dict = None) -> PrescriberField:
        """Extract and validate prescriber first name."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['first_name'])
        source = "form"
        
        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ['prescriber_first_name'])
            if value:
                source = "payload"
                confidence = 1.0
        
        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "Prescriber first name"
        )
        
        return PrescriberField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid
        )

    def _extract_last_name(self, forms: Dict, payload_data: Dict = None) -> PrescriberField:
        """Extract and validate prescriber last name."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['last_name'])
        source = "form"
        
        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ['prescriber_last_name'])
            if value:
                source = "payload"
                confidence = 1.0
        
        # Validate
        is_valid, validated_value, error = FieldValidators.validate_required_field(
            value or "", "Prescriber last name"
        )
        
        return PrescriberField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid
        )

    def _extract_npi(self, forms: Dict, payload_data: Dict = None) -> PrescriberField:
        """Extract and validate NPI."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['npi'])
        source = "form"
        original_value = value
        
        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ['npi', 'prescriber_npi'])
            if value:
                source = "payload"
                confidence = 1.0
                original_value = value
        
        # Validate and format
        is_valid, validated_value, error = FieldValidators.validate_npi(value or "")
        
        return PrescriberField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=original_value if original_value != validated_value else None
        )

    def _extract_address(self, forms: Dict, payload_data: Dict = None) -> Address:
        """Extract and validate address."""
        address = Address()
        
        # Street
        street_value, street_conf = self.find_field(forms, self.FIELD_MAPPINGS['street'])
        street_source = "form"
        if not street_value and payload_data:
            street_value = self.get_from_payload(payload_data, ['prescriber_street', 'street'])
            if street_value:
                street_source = "payload"
                street_conf = 1.0
        
        street_valid, street_val, _ = FieldValidators.validate_required_field(
            street_value or "", "Street address"
        )
        address.street = PrescriberField(
            value=street_val if street_valid else street_value,
            source=street_source,
            confidence=street_conf,
            validated=street_valid
        )
        
        # City
        city_value, city_conf = self.find_field(forms, self.FIELD_MAPPINGS['city'])
        city_source = "form"
        if not city_value and payload_data:
            city_value = self.get_from_payload(payload_data, ['prescriber_city', 'city'])
            if city_value:
                city_source = "payload"
                city_conf = 1.0
        
        city_valid, city_val, _ = FieldValidators.validate_required_field(
            city_value or "", "City"
        )
        address.city = PrescriberField(
            value=city_val if city_valid else city_value,
            source=city_source,
            confidence=city_conf,
            validated=city_valid
        )
        
        # State
        state_value, state_conf = self.find_field(forms, self.FIELD_MAPPINGS['state'])
        state_source = "form"
        state_original = state_value
        if not state_value and payload_data:
            state_value = self.get_from_payload(payload_data, ['prescriber_state', 'state'])
            if state_value:
                state_source = "payload"
                state_conf = 1.0
                state_original = state_value
        
        state_valid, state_val, _ = FieldValidators.validate_state(state_value or "")
        address.state = PrescriberField(
            value=state_val if state_valid else state_value,
            source=state_source,
            confidence=state_conf,
            validated=state_valid,
            original_value=state_original if state_original != state_val else None
        )
        
        # ZIP
        zip_value, zip_conf = self.find_field(forms, self.FIELD_MAPPINGS['zip'])
        zip_source = "form"
        zip_original = zip_value
        if not zip_value and payload_data:
            zip_value = self.get_from_payload(payload_data, ['prescriber_zip', 'zip'])
            if zip_value:
                zip_source = "payload"
                zip_conf = 1.0
                zip_original = zip_value
        
        zip_valid, zip_val, _ = FieldValidators.validate_zip(zip_value or "")
        address.zip = PrescriberField(
            value=zip_val if zip_valid else zip_value,
            source=zip_source,
            confidence=zip_conf,
            validated=zip_valid,
            original_value=zip_original if zip_original != zip_val else None
        )
        
        return address

    def _extract_phone(self, forms: Dict, payload_data: Dict = None) -> PrescriberField:
        """Extract and validate phone."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['phone'])
        source = "form"
        original_value = value
        
        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ['prescriber_phone', 'phone'])
            if value:
                source = "payload"
                confidence = 1.0
                original_value = value
        
        # Validate and format (required if no fax)
        if value:
            is_valid, validated_value, error = FieldValidators.validate_phone(value)
        else:
            is_valid, validated_value = False, None
        
        return PrescriberField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=original_value if original_value != validated_value else None
        )

    def _extract_fax(self, forms: Dict, payload_data: Dict = None) -> PrescriberField:
        """Extract and validate fax."""
        value, confidence = self.find_field(forms, self.FIELD_MAPPINGS['fax'])
        source = "form"
        original_value = value
        
        # Try payload
        if not value and payload_data:
            value = self.get_from_payload(payload_data, ['prescriber_fax', 'fax'])
            if value:
                source = "payload"
                confidence = 1.0
                original_value = value
        
        # Validate and format (required if no phone)
        if value:
            is_valid, validated_value, error = FieldValidators.validate_phone(value)
        else:
            is_valid, validated_value = False, None
        
        return PrescriberField(
            value=validated_value if is_valid else value,
            source=source,
            confidence=confidence,
            validated=is_valid,
            original_value=original_value if original_value != validated_value else None
        )
