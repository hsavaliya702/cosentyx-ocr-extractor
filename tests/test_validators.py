"""Tests for field validators."""
import pytest
from src.validation.field_validators import FieldValidators


class TestFieldValidators:
    """Test field validation functions."""

    def test_validate_date_valid(self):
        """Test valid date formats."""
        is_valid, formatted, error = FieldValidators.validate_date("01/15/1980")
        assert is_valid
        assert formatted == "01/15/1980"
        assert error == ""

    def test_validate_date_various_formats(self):
        """Test various date formats are normalized."""
        test_cases = [
            ("1/15/80", "01/15/1980"),
            ("01-15-1980", "01/15/1980"),
            ("1980-01-15", "01/15/1980"),
        ]
        for input_date, expected in test_cases:
            is_valid, formatted, _ = FieldValidators.validate_date(input_date)
            assert is_valid
            assert formatted == expected

    def test_validate_date_invalid(self):
        """Test invalid date."""
        is_valid, _, error = FieldValidators.validate_date("invalid")
        assert not is_valid
        assert "Invalid date" in error

    def test_validate_phone_valid(self):
        """Test valid phone formats."""
        test_cases = [
            "5551234567",
            "(555) 123-4567",
            "555-123-4567",
        ]
        for phone in test_cases:
            is_valid, formatted, _ = FieldValidators.validate_phone(phone)
            assert is_valid
            assert formatted == "(555) 123-4567"

    def test_validate_phone_invalid(self):
        """Test invalid phone."""
        is_valid, _, error = FieldValidators.validate_phone("12345")
        assert not is_valid
        assert "10 digits" in error

    def test_validate_email_valid(self):
        """Test valid email."""
        is_valid, formatted, _ = FieldValidators.validate_email("test@example.com")
        assert is_valid
        assert formatted == "test@example.com"

    def test_validate_email_invalid(self):
        """Test invalid email."""
        is_valid, _, error = FieldValidators.validate_email("not-an-email")
        assert not is_valid
        assert "Invalid email" in error

    def test_validate_npi_valid(self):
        """Test valid NPI."""
        is_valid, formatted, _ = FieldValidators.validate_npi("1234567890")
        assert is_valid
        assert formatted == "1234567890"

    def test_validate_npi_with_formatting(self):
        """Test NPI with formatting characters."""
        is_valid, formatted, _ = FieldValidators.validate_npi("123-456-7890")
        assert is_valid
        assert formatted == "1234567890"

    def test_validate_npi_invalid(self):
        """Test invalid NPI."""
        is_valid, _, error = FieldValidators.validate_npi("12345")
        assert not is_valid
        assert "10 digits" in error

    def test_validate_state_valid(self):
        """Test valid state codes."""
        test_cases = ["MA", "ma", "Ca", "NY"]
        for state in test_cases:
            is_valid, formatted, _ = FieldValidators.validate_state(state)
            assert is_valid
            assert formatted == state.upper()

    def test_validate_state_invalid(self):
        """Test invalid state code."""
        is_valid, _, error = FieldValidators.validate_state("XX")
        assert not is_valid
        assert "Invalid state" in error

    def test_validate_zip_5_digit(self):
        """Test 5-digit ZIP."""
        is_valid, formatted, _ = FieldValidators.validate_zip("02101")
        assert is_valid
        assert formatted == "02101"

    def test_validate_zip_9_digit(self):
        """Test 9-digit ZIP."""
        is_valid, formatted, _ = FieldValidators.validate_zip("021011234")
        assert is_valid
        assert formatted == "02101-1234"

    def test_validate_zip_invalid(self):
        """Test invalid ZIP."""
        is_valid, _, error = FieldValidators.validate_zip("123")
        assert not is_valid
        assert "5 or 9 digits" in error

    def test_validate_gender_valid(self):
        """Test valid gender values."""
        test_cases = [
            ("M", "M"),
            ("male", "M"),
            ("F", "F"),
            ("female", "F"),
            ("Other", "Other"),
        ]
        for input_val, expected in test_cases:
            is_valid, formatted, _ = FieldValidators.validate_gender(input_val)
            assert is_valid
            assert formatted == expected

    def test_validate_gender_invalid(self):
        """Test invalid gender."""
        is_valid, _, error = FieldValidators.validate_gender("invalid")
        assert not is_valid
        assert "Invalid gender" in error

    def test_validate_required_field_valid(self):
        """Test required field with value."""
        is_valid, value, _ = FieldValidators.validate_required_field("test", "Field")
        assert is_valid
        assert value == "test"

    def test_validate_required_field_empty(self):
        """Test required field without value."""
        is_valid, _, error = FieldValidators.validate_required_field("", "Field")
        assert not is_valid
        assert "required" in error
