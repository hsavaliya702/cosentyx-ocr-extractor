"""Base extractor class for field extraction."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from src.ocr.textract_parser import TextractParser
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseExtractor(ABC):
    """Base class for field extractors."""

    def __init__(self):
        """Initialize base extractor."""
        self.parser = TextractParser()

    @abstractmethod
    def extract(self, textract_data: Dict, payload_data: Dict = None) -> Any:
        """Extract data from Textract response.

        Args:
            textract_data: Parsed Textract data
            payload_data: Optional payload data to supplement extraction

        Returns:
            Any: Extracted data model
        """
        pass

    def find_field(
        self, forms: Dict[str, str], field_names: List[str]
    ) -> tuple[Optional[str], float]:
        """Find field value from forms data.

        Args:
            forms: Dictionary of form key-value pairs
            field_names: List of possible field names

        Returns:
            tuple: (value, confidence)
        """
        value = self.parser.find_field_value(forms, field_names)

        # Default confidence if found, 0 if not found
        confidence = 0.9 if value else 0.0

        return value, confidence

    def get_from_payload(
        self, payload_data: Dict, field_names: List[str]
    ) -> Optional[str]:
        """Get field value from payload data.

        Args:
            payload_data: Payload dictionary
            field_names: List of possible field names

        Returns:
            str: Field value or None
        """
        if not payload_data:
            return None

        for field_name in field_names:
            if field_name in payload_data:
                return payload_data[field_name]

            # Try case-insensitive
            field_lower = field_name.lower()
            for key, value in payload_data.items():
                if key.lower() == field_lower:
                    return value

        return None

    def extract_from_text(
        self, raw_text: str, keywords: List[str], context_words: int = 5
    ) -> Optional[str]:
        """Extract field value from raw OCR text using keyword matching.

        Args:
            raw_text: Raw OCR extracted text
            keywords: List of keywords to search for
            context_words: Number of words to extract after keyword (default: 5)

        Returns:
            str: Extracted value or None
        """
        if not raw_text:
            return None

        import re

        raw_text_lower = raw_text.lower()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in raw_text_lower:
                # Find position and extract context
                pattern = rf"{re.escape(keyword_lower)}[:\s]*([^\n]{{0,100}})"
                match = re.search(pattern, raw_text_lower, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean up and limit to context_words
                    words = value.split()[:context_words]
                    result = " ".join(words).strip()
                    if result:
                        logger.debug(f"Extracted '{result}' from text using keyword '{keyword}'")
                        return result

        return None
