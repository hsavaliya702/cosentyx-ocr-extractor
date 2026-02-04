"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List


@pytest.fixture
def sample_textract_response() -> Dict:
    """Sample Textract API response."""
    return {
        "Blocks": [
            {
                "BlockType": "LINE",
                "Id": "line-1",
                "Text": "Patient First Name: John",
                "Confidence": 95.5,
            },
            {
                "BlockType": "LINE",
                "Id": "line-2",
                "Text": "Patient Last Name: Doe",
                "Confidence": 96.2,
            },
            {
                "BlockType": "KEY_VALUE_SET",
                "Id": "kv-1",
                "EntityTypes": ["KEY"],
                "Relationships": [
                    {"Type": "VALUE", "Ids": ["kv-2"]},
                    {"Type": "CHILD", "Ids": ["word-1"]},
                ],
            },
            {
                "BlockType": "KEY_VALUE_SET",
                "Id": "kv-2",
                "EntityTypes": ["VALUE"],
                "Relationships": [{"Type": "CHILD", "Ids": ["word-2"]}],
            },
            {
                "BlockType": "WORD",
                "Id": "word-1",
                "Text": "patient first name",
                "Confidence": 95.0,
            },
            {"BlockType": "WORD", "Id": "word-2", "Text": "John", "Confidence": 96.0},
        ]
    }


@pytest.fixture
def sample_forms_data() -> Dict[str, str]:
    """Sample extracted form key-value pairs."""
    return {
        "patient first name": "John",
        "patient last name": "Doe",
        "date of birth": "01/15/1980",
        "gender": "M",
        "phone": "5551234567",
        "email": "john.doe@email.com",
        "prescriber first name": "Jane",
        "prescriber last name": "Smith",
        "npi": "1234567890",
        "prescriber address": "123 Medical Dr",
        "city": "Boston",
        "state": "MA",
        "zip": "02101",
        "prescriber phone": "5559876543",
        "product": "Cosentyx",
        "dosage": "150mg",
        "quantity": "2",
        "sig": "Inject 1 pen weekly",
        "refills": "3",
        "signature name": "Dr. Jane Smith",
        "signature date": "01/28/2024",
    }


@pytest.fixture
def sample_payload_data() -> Dict:
    """Sample payload data."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "01/15/1980",
        "gender": "M",
    }


@pytest.fixture
def mock_textract_client():
    """Mock Textract client."""
    client = Mock()
    client.analyze_document = Mock(return_value={"Blocks": []})
    return client


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client."""
    client = Mock()
    response_body = Mock()
    response_body.read = Mock(
        return_value=b'{"content": [{"text": "{\\"document_type\\": \\"ema_start_form\\", \\"confidence\\": 0.95}"}]}'
    )
    client.invoke_model = Mock(return_value={"body": response_body})
    return client


@pytest.fixture
def sample_document_bytes() -> bytes:
    """Sample document bytes (empty PDF header)."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
