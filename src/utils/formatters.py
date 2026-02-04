"""Data formatting utilities."""

import re
from datetime import datetime
from typing import Optional


def format_phone(phone: str) -> Optional[str]:
    """Format phone number to (XXX) XXX-XXXX format.

    Args:
        phone: Raw phone number string

    Returns:
        str: Formatted phone number or None if invalid
    """
    if not phone:
        return None

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    # Must be exactly 10 digits
    if len(digits) != 10:
        return None

    # Format as (XXX) XXX-XXXX
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def format_date(date_str: str) -> Optional[str]:
    """Format date to MM/DD/YYYY format.

    Args:
        date_str: Raw date string in various formats

    Returns:
        str: Formatted date as MM/DD/YYYY or None if invalid
    """
    if not date_str:
        return None

    # Try various date formats
    date_formats = [
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%m/%d/%y",
        "%m-%d-%y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str.strip(), fmt)
            return date_obj.strftime("%m/%d/%Y")
        except ValueError:
            continue

    return None


def format_npi(npi: str) -> Optional[str]:
    """Format and validate NPI (exactly 10 digits).

    Args:
        npi: Raw NPI string

    Returns:
        str: Formatted NPI or None if invalid
    """
    if not npi:
        return None

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", npi)

    # Must be exactly 10 digits
    if len(digits) != 10:
        return None

    return digits


def format_state(state: str) -> Optional[str]:
    """Format state code to uppercase 2-letter code.

    Args:
        state: Raw state string

    Returns:
        str: Uppercase 2-letter state code or None if invalid
    """
    if not state:
        return None

    state = state.strip().upper()

    # Valid US state codes
    valid_states = {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
        "PR",
        "VI",
        "GU",
        "AS",
        "MP",
    }

    if len(state) == 2 and state in valid_states:
        return state

    return None


def format_zip(zip_code: str) -> Optional[str]:
    """Format ZIP code (5 or 9 digits).

    Args:
        zip_code: Raw ZIP code string

    Returns:
        str: Formatted ZIP code or None if invalid
    """
    if not zip_code:
        return None

    # Remove all non-digit characters except hyphen
    cleaned = re.sub(r"[^\d-]", "", zip_code)

    # Extract digits only
    digits = re.sub(r"\D", "", cleaned)

    # 5 digit ZIP
    if len(digits) == 5:
        return digits

    # 9 digit ZIP (ZIP+4)
    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"

    return None
