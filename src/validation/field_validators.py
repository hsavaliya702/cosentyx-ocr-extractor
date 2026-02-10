"""Field-level validation functions."""

import re
from datetime import datetime
from typing import Tuple, Optional
from src.utils.formatters import (
    format_date,
    format_phone,
    format_npi,
    format_state,
    format_zip,
)


class FieldValidators:
    """Field-level validation functions."""

    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, str, str]:
        """Validate and format date.

        Args:
            date_str: Raw date string

        Returns:
            Tuple[bool, str, str]: (is_valid, formatted_value, error_message)
        """
        if not date_str:
            return False, "", "Date is required"

        formatted = format_date(date_str)
        if not formatted:
            return False, date_str, f"Invalid date format: {date_str}"

        # Check if date is reasonable (not in future for DOB)
        try:
            date_obj = datetime.strptime(formatted, "%m/%d/%Y")
            if date_obj > datetime.now():
                return False, formatted, "Date cannot be in the future"
        except ValueError:
            return False, formatted, "Invalid date"

        return True, formatted, ""

    @staticmethod
    def validate_phone(phone_str: str) -> Tuple[bool, str, str]:
        """Validate and format phone number.

        Args:
            phone_str: Raw phone string

        Returns:
            Tuple[bool, str, str]: (is_valid, formatted_value, error_message)
        """
        if not phone_str:
            return False, "", "Phone number is required"

        formatted = format_phone(phone_str)
        if not formatted:
            return (
                False,
                phone_str,
                f"Invalid phone format (must be 10 digits): {phone_str}",
            )

        return True, formatted, ""

    @staticmethod
    def validate_email(email_str: str) -> Tuple[bool, str, str]:
        """Validate email address.

        Args:
            email_str: Raw email string

        Returns:
            Tuple[bool, str, str]: (is_valid, formatted_value, error_message)
        """
        if not email_str:
            return False, "", "Email is required"

        # Basic email regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email_str.strip()):
            return False, email_str, f"Invalid email format: {email_str}"

        return True, email_str.strip().lower(), ""

    @staticmethod
    def validate_npi(npi_str: str) -> Tuple[bool, str, str]:
        """Validate NPI (exactly 10 digits).

        Args:
            npi_str: Raw NPI string

        Returns:
            Tuple[bool, str, str]: (is_valid, formatted_value, error_message)
        """
        if not npi_str:
            return False, "", "NPI is required"

        formatted = format_npi(npi_str)
        if not formatted:
            return False, npi_str, f"Invalid NPI (must be exactly 10 digits): {npi_str}"

        return True, formatted, ""

    @staticmethod
    def validate_state(state_str: str) -> Tuple[bool, str, str]:
        """Validate state code.

        Args:
            state_str: Raw state string

        Returns:
            Tuple[bool, str, str]: (is_valid, formatted_value, error_message)
        """
        if not state_str:
            return False, "", "State is required"

        formatted = format_state(state_str)
        if not formatted:
            return False, state_str, f"Invalid state code: {state_str}"

        return True, formatted, ""

    @staticmethod
    def validate_zip(zip_str: str) -> Tuple[bool, str, str]:
        """Validate ZIP code.

        Args:
            zip_str: Raw ZIP string

        Returns:
            Tuple[bool, str, str]: (is_valid, formatted_value, error_message)
        """
        if not zip_str:
            return False, "", "ZIP code is required"

        formatted = format_zip(zip_str)
        if not formatted:
            return (
                False,
                zip_str,
                f"Invalid ZIP code (must be 5 or 9 digits): {zip_str}",
            )

        return True, formatted, ""

    @staticmethod
    def validate_gender(gender_str: str) -> Tuple[bool, str, str]:
        """Validate gender field.

        Args:
            gender_str: Raw gender string

        Returns:
            Tuple[bool, str, str]: (is_valid, formatted_value, error_message)
        """
        if not gender_str:
            return False, "", "Gender is required"

        gender_upper = gender_str.strip().upper()

        # Map common variations
        gender_map = {
            "M": "M",
            "MALE": "M",
            "F": "F",
            "FEMALE": "F",
            "O": "Other",
            "OTHER": "Other",
            "X": "Other",
            "U": "Other",
            "UNKNOWN": "Other",
        }

        if gender_upper in gender_map:
            return True, gender_map[gender_upper], ""

        return False, gender_str, f"Invalid gender value: {gender_str}"

    @staticmethod
    def validate_required_field(value: str, field_name: str) -> Tuple[bool, str, str]:
        """Validate that a required field has a value.

        Args:
            value: Field value
            field_name: Name of the field

        Returns:
            Tuple[bool, str, str]: (is_valid, value, error_message)
        """
        if not value or not value.strip():
            return False, "", f"{field_name} is required"

        return True, value.strip(), ""
