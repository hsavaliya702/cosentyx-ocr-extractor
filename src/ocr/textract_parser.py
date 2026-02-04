"""Parser for Textract responses."""
from typing import Dict, List, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TextractParser:
    """Parse and structure Textract response data."""

    @staticmethod
    def parse_response(textract_response: Dict) -> Dict:
        """Parse Textract response into structured format.
        
        Args:
            textract_response: Raw Textract API response
            
        Returns:
            Dict: Structured extraction data
        """
        blocks = textract_response.get("Blocks", [])
        
        # Import here to avoid circular dependency
        from src.ocr.textract_client import TextractClient
        client = TextractClient()
        
        return {
            "raw_text": client.extract_text(blocks),
            "forms": client.extract_forms(blocks),
            "tables": client.extract_tables(blocks),
            "checkboxes": client.extract_checkboxes(blocks),
            "signatures": client.detect_signatures(blocks),
            "blocks": blocks
        }

    @staticmethod
    def find_field_value(
        forms: Dict[str, str],
        field_names: List[str],
        case_sensitive: bool = False
    ) -> Optional[str]:
        """Find field value by trying multiple field name variations.
        
        Args:
            forms: Dictionary of form key-value pairs
            field_names: List of possible field names to search
            case_sensitive: Whether to perform case-sensitive search
            
        Returns:
            str: Field value or None if not found
        """
        for field_name in field_names:
            # Try exact match
            if field_name in forms:
                return forms[field_name]
            
            # Try case-insensitive match
            if not case_sensitive:
                field_name_lower = field_name.lower()
                for key, value in forms.items():
                    if key.lower() == field_name_lower:
                        return value
            
            # Try partial match
            if not case_sensitive:
                field_name_lower = field_name.lower()
                for key, value in forms.items():
                    if field_name_lower in key.lower() or key.lower() in field_name_lower:
                        return value
        
        return None

    @staticmethod
    def extract_field_with_confidence(
        blocks: List[Dict],
        field_text: str
    ) -> tuple[Optional[str], float]:
        """Extract field value and confidence from blocks.
        
        Args:
            blocks: List of Textract blocks
            field_text: Text to search for
            
        Returns:
            tuple: (value, confidence)
        """
        for block in blocks:
            if block.get("BlockType") == "LINE":
                text = block.get("Text", "")
                if field_text.lower() in text.lower():
                    confidence = block.get("Confidence", 0) / 100.0
                    return text, confidence
        
        return None, 0.0
