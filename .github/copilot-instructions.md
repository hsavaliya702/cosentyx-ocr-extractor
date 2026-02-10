# Copilot Instructions for Cosentyx OCR Extractor

## Overview
This is a production-ready AWS-based OCR pipeline for extracting structured data from Cosentyx/EMA pharmaceutical Start Forms. The system uses AWS Textract for OCR and AWS Bedrock (Claude 3.5 Sonnet) for intelligent classification and validation.

## Architecture & Data Flow

### 5-Stage Pipeline (orchestrated by `src/processor.py`)
1. **OCR** → AWS Textract extracts raw text, form fields, tables, signatures
2. **Classification** → Bedrock LLM classifies document type (ema_start_form, cosentyx_start_form, or reject)
3. **Extraction** → Specialized extractors parse fields into Pydantic models
4. **Validation** → Multi-level validation (format, business rules, optional LLM validation)
5. **Routing** → Business logic determines action: `create_full_profile`, `create_patient_only`, or `manual_review`

### Key Components
- **Entry Points**: `src/lambda_handler.py` (AWS Lambda) or direct `CosentyxFormProcessor` API
- **Extractors** (`src/extraction/`): Inherit from `BaseExtractor`, implement fuzzy field matching with fallback to payload data
- **Models** (`src/models/`): Pydantic models where each field includes `value`, `source` (form/payload), `confidence`, `validated`, `original_value`
- **Validation**: `FieldValidators` (format validation), `BusinessRules` (routing logic), optional `BedrockValidator` (LLM validation)

## Critical Patterns

### Field Extraction Strategy
All extractors follow a **dual-source** pattern (see `base_extractor.py`):
```python
# 1. Try extracting from OCR form data (fuzzy matching on multiple field name variations)
value, confidence = self.find_field(forms, ["patient first name", "first name", "fname"])

# 2. Fallback to payload data if not found in form
if not value and payload_data:
    value = self.get_from_payload(payload_data, ["first_name", "fname"])
    confidence = 1.0
    source = "payload"
```

Field name variations are defined per field (see `docs/FIELD_MAPPING.md`). Matching is case-insensitive and partial.

### Pydantic Field Model Pattern
Every extracted field uses a consistent structure (example from `src/models/patient.py`):
```python
class PatientField(BaseModel):
    value: Optional[str] = None
    source: str = "form"  # "form" or "payload"
    confidence: float = 0.0  # OCR confidence 0.0-1.0
    validated: bool = False  # Passed validation?
    original_value: Optional[str] = None  # Pre-formatting value
```

### Validation & Routing
- **Format validators** (`src/validation/field_validators.py`): Return `(is_valid, formatted_value, error_message)`
- **Business rules** (`src/validation/business_rules.py`): Apply routing logic in `apply_routing_rules()` which calls `ExtractionResult.determine_routing()`
- **Routing outcomes**: System decides between three actions based on which extractors have valid data:
  - `create_full_profile`: All 4 extractors (patient, prescriber, prescription, attestation) validated
  - `create_patient_only`: Only patient info validated
  - `manual_review`: Document rejected, validation failed, or incomplete data

## Configuration

### Environment (`.env` + `config/settings.py`)
- **Pydantic Settings**: Uses `pydantic-settings` with `BaseSettings` for type-safe config
- **Cached singleton**: `get_settings()` is `@lru_cache()` decorated - import and call once
- **Key settings**: `bedrock_model_id`, `textract_confidence_threshold`, `enable_duplicate_check`, `enable_bedrock_validation`

### AWS Resources
- **Textract**: Uses `analyze_document` API with `FORMS` and `TABLES` features
- **Bedrock**: Model `anthropic.claude-3-5-sonnet-20241022-v2:0` (configurable)
- **S3**: Optional storage for processed/failed documents
- **Lambda deployment**: Handler `src.lambda_handler.lambda_handler`, 60s timeout, 512MB memory

## Development Workflows

### Testing (`pytest`)
```bash
pytest                    # Run all tests
pytest tests/test_validators.py -v  # Specific test file
pytest --cov=src         # With coverage
```
- **Fixtures**: `tests/conftest.py` provides mock Textract responses, sample data
- **Mock AWS**: Tests use mocked boto3 clients (see conftest.py fixtures)

### Local Development
```bash
pip install -e .         # Editable install
pip install -e ".[dev]"  # With dev dependencies

# Run example
python examples/usage_example.py

# Format code
black src/ tests/
isort src/ tests/
```

### Adding New Extractors
1. Inherit from `BaseExtractor` in `src/extraction/`
2. Define field name variations for fuzzy matching
3. Implement `extract(textract_data, payload_data)` returning Pydantic model
4. Add to `processor.py` extractors dict
5. Update `ExtractionResult` model in `src/models/extraction_result.py`

### Adding New Validators
1. Add static method to `FieldValidators` returning `(bool, formatted_str, error_msg)`
2. Create formatter in `src/utils/formatters.py` if needed
3. Update extractor to call validator and set `field.validated = True`

## Common Gotchas

- **Import paths**: Use absolute imports from `src/`, not relative (e.g., `from src.utils.logger import get_logger`)
- **Textract response structure**: Use `TextractParser.parse_response()` to get normalized dict with `forms`, `tables`, `raw_text`, etc.
- **Confidence thresholds**: Default is 0.85 (configurable), but extractors return 0.9 for found fields, 0.0 for missing
- **Duplicate detection**: Based on signature `FirstName_LastName_DOB` (lowercase), tracked in-memory in `BusinessRules`
- **Date formats**: Many input formats accepted, output always `MM/DD/YYYY` (see `formatters.format_date()`)
- **NPI validation**: Must be exactly 10 digits after formatting (see `formatters.format_npi()`)

## Documentation References

- `docs/ARCHITECTURE.md` - Detailed component descriptions
- `docs/FIELD_MAPPING.md` - Complete list of field name variations and validation rules
- `docs/API_DOCUMENTATION.md` - API usage patterns
- `docs/DEPLOYMENT.md` - AWS deployment guide
- `examples/usage_example.py` - Working code examples

## LLM Integration Points

The codebase uses AWS Bedrock Claude in two places:
1. **Classification** (`src/classification/bedrock_classifier.py`): Determines document type with confidence score
2. **Validation** (`src/validation/bedrock_validator.py`): Optional semantic validation (disabled by default via `settings.enable_bedrock_validation`)

Both use structured prompts with JSON response parsing. Temperature is 0.1 for deterministic outputs.
