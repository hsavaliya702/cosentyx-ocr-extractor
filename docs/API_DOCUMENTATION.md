# API Documentation

## CosentyxFormProcessor

Main class for processing Cosentyx/EMA Start Forms.

### `__init__()`

Initialize the processor with all required components.

```python
processor = CosentyxFormProcessor()
```

### `process_document(document_bytes, payload_data=None)`

Process a document through the complete pipeline.

**Parameters**:
- `document_bytes` (bytes): PDF document content as bytes
- `payload_data` (Dict, optional): Supplemental data to enhance extraction

**Returns**:
- `ExtractionResult`: Complete extraction result with routing decision

**Example**:
```python
with open("form.pdf", "rb") as f:
    document_bytes = f.read()

payload_data = {
    "first_name": "John",
    "last_name": "Doe",
    "dob": "01/15/1980"
}

result = processor.process_document(document_bytes, payload_data)
```

## Data Models

### ExtractionResult

Complete extraction result with all extracted data and routing information.

**Fields**:
- `document_id` (str): Unique document identifier (UUID)
- `document_type` (str): Classified document type
- `classification_confidence` (float): Classification confidence (0.0-1.0)
- `extraction_timestamp` (str): ISO 8601 timestamp
- `validation_status` (str): "complete", "partial", or "failed"
- `patient` (PatientInfo): Patient information
- `prescriber` (PrescriberInfo): Prescriber information
- `prescription` (PrescriptionInfo): Prescription details
- `attestation` (AttestationInfo): Attestation/signature information
- `validation_errors` (List[str]): List of validation errors
- `warnings` (List[str]): List of warnings
- `routing` (RoutingDecision): Routing decision
- `metadata` (Metadata): Processing metadata

**Methods**:
- `determine_routing()`: Determine routing based on validation results

### PatientInfo

Patient demographic information.

**Fields**:
- `first_name` (PatientField): Patient first name
- `last_name` (PatientField): Patient last name
- `dob` (PatientField): Date of birth (MM/DD/YYYY)
- `gender` (PatientField): Gender (M/F/Other)
- `phone` (PatientField): Phone number (optional)
- `email` (PatientField): Email address (optional)
- `preferred_language` (PatientField): Preferred language (optional)

**Methods**:
- `is_valid()`: Check if all mandatory fields are validated
- `get_signature()`: Get unique signature for duplicate detection

### PrescriberInfo

Prescriber and practice information.

**Fields**:
- `first_name` (PrescriberField): Prescriber first name
- `last_name` (PrescriberField): Prescriber last name
- `npi` (PrescriberField): 10-digit NPI
- `address` (Address): Practice address
- `phone` (PrescriberField): Phone number
- `fax` (PrescriberField): Fax number

**Methods**:
- `is_valid()`: Check if all mandatory fields are validated (requires phone OR fax)

### PrescriptionInfo

Medication prescription details.

**Fields**:
- `product` (PrescriptionField): Product name (Cosentyx)
- `dosage` (PrescriptionField): Dosage (e.g., 150mg, 300mg)
- `quantity` (PrescriptionField): Quantity
- `sig` (PrescriptionField): Directions for use
- `refills` (PrescriptionField): Number of refills (defaults to 0)

**Methods**:
- `is_valid()`: Check if all mandatory fields are validated
- `get_signature()`: Get unique signature for duplicate detection

### AttestationInfo

Prescriber attestation and signature.

**Fields**:
- `signature_present` (bool): Whether signature was detected
- `signature_confidence` (float): Signature detection confidence
- `name` (AttestationField): Prescriber name on attestation
- `date` (AttestationField): Attestation date

**Methods**:
- `is_valid()`: Check if attestation is complete and valid

### Field Types

All field types include the following attributes:

**PatientField / PrescriberField / PrescriptionField / AttestationField**:
- `value` (str): Extracted/validated value
- `source` (str): "form" or "payload"
- `confidence` (float): OCR confidence score (0.0-1.0)
- `validated` (bool): Whether field passed validation
- `original_value` (str, optional): Original value before formatting

### RoutingDecision

Routing decision based on validation results.

**Fields**:
- `action` (str): "create_full_profile", "create_patient_only", or "manual_review"
- `create_patient_profile` (bool): Whether to create patient profile
- `create_prescriber_profile` (bool): Whether to create prescriber profile
- `create_prescription` (bool): Whether to create prescription
- `manual_review_required` (bool): Whether manual review is needed
- `review_reason` (str, optional): Reason for manual review

## Validators

### FieldValidators

Static methods for field-level validation.

#### `validate_date(date_str)`

Validate and format date to MM/DD/YYYY.

**Returns**: `Tuple[bool, str, str]` - (is_valid, formatted_value, error_message)

**Example**:
```python
is_valid, formatted, error = FieldValidators.validate_date("1/15/80")
# Returns: (True, "01/15/1980", "")
```

#### `validate_phone(phone_str)`

Validate and format phone to (XXX) XXX-XXXX.

**Returns**: `Tuple[bool, str, str]`

#### `validate_email(email_str)`

Validate email address format.

**Returns**: `Tuple[bool, str, str]`

#### `validate_npi(npi_str)`

Validate NPI (exactly 10 digits).

**Returns**: `Tuple[bool, str, str]`

#### `validate_state(state_str)`

Validate 2-letter state code.

**Returns**: `Tuple[bool, str, str]`

#### `validate_zip(zip_str)`

Validate ZIP code (5 or 9 digits).

**Returns**: `Tuple[bool, str, str]`

#### `validate_gender(gender_str)`

Validate and normalize gender value.

**Returns**: `Tuple[bool, str, str]`

## Lambda Handler

### `lambda_handler(event, context)`

AWS Lambda entry point.

**Supported Event Types**:

1. **S3 Event**:
```json
{
  "Records": [{
    "s3": {
      "bucket": {"name": "bucket-name"},
      "object": {"key": "file-key"}
    }
  }]
}
```

2. **Direct Invocation**:
```json
{
  "document_base64": "<base64-encoded-pdf>",
  "payload_data": {
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "body": "<json-string-of-extraction-result>",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

## Configuration

### Settings

Configuration is managed via environment variables or `.env` file.

**Available Settings**:
- `aws_region` (str): AWS region (default: "us-east-1")
- `aws_access_key_id` (str, optional): AWS access key
- `aws_secret_access_key` (str, optional): AWS secret key
- `s3_bucket_name` (str): S3 bucket for documents
- `textract_confidence_threshold` (float): Minimum confidence (default: 0.85)
- `textract_max_retries` (int): Max retry attempts (default: 3)
- `bedrock_model_id` (str): Claude model ID
- `bedrock_max_tokens` (int): Max tokens for Bedrock (default: 4096)
- `bedrock_temperature` (float): Temperature for Bedrock (default: 0.1)
- `log_level` (str): Logging level (default: "INFO")
- `enable_duplicate_check` (bool): Enable duplicate detection (default: True)
- `enable_bedrock_validation` (bool): Enable LLM validation (default: True)

**Access Settings**:
```python
from config.settings import get_settings

settings = get_settings()
print(settings.aws_region)
```

## Error Handling

All API calls are wrapped in try-except blocks. Errors are logged and returned in a structured format.

**Error Response Example**:
```json
{
  "statusCode": 500,
  "body": {
    "error": "Internal server error",
    "message": "Textract API call failed: ..."
  }
}
```

## Cost Estimation

The `metadata` field in `ExtractionResult` includes cost estimates:

```json
{
  "metadata": {
    "processing_time_ms": 2350,
    "textract_cost_estimate": 0.0015,
    "bedrock_cost_estimate": 0.0008
  }
}
```

**Cost Breakdown**:
- Textract: $1.50 per 1,000 pages (Forms feature)
- Bedrock: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
