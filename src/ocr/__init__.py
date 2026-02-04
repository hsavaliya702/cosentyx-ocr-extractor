"""OCR package for AWS Textract integration."""
from src.ocr.textract_client import TextractClient
from src.ocr.textract_parser import TextractParser

__all__ = ["TextractClient", "TextractParser"]
