# Testing Guide - Cosentyx OCR Extractor

## Understanding Sample Form Behavior

### Expected Validation Failures

The sample forms in `examples/sample_forms/` are **intentionally incomplete** and will trigger validation failures. This is **expected behavior** and demonstrates the system's validation and routing logic.

#### Common Validation Issues with Sample Forms:

1. **Missing or Empty Required Fields**
   - Forms may have blank patient information
   - Prescriber details might be incomplete
   - Prescription fields could be empty

2. **Manual Review Routing**
   - Incomplete forms will be routed to `manual_review`
   - This is the correct behavior for forms that don't meet business rules
   - System is working as designed when this occurs

3. **Limited Key-Value Pairs**
   - Forms using text layout (not fillable PDFs) may only extract 8-20 key-value pairs
   - Text-based forms require additional processing
   - This is a limitation of non-interactive PDF forms

### Routing Logic Explained

The system has three routing outcomes:

#### 1. `create_full_profile`
- **When**: All 4 extractors validate successfully
  - Patient information complete
  - Prescriber information complete
  - Prescription details complete
  - Attestation/signature present
- **Action**: Create complete patient profile in database

#### 2. `create_patient_only`
- **When**: Only patient information validates
  - Patient name, DOB, contact info present
  - Other sections incomplete or missing
- **Action**: Create patient record, flag for additional info

#### 3. `manual_review`
- **When**: Any of these conditions occur:
  - Document classified as rejected or unknown
  - Validation errors in any section
  - Business rules fail
  - Duplicate detection triggered
- **Action**: Route to human reviewer for manual processing

## Testing with Complete Forms

To test the full pipeline successfully, you need forms with:

### Required Patient Information
- First Name
- Last Name
- Date of Birth (MM/DD/YYYY format)
- Address
- City, State, ZIP
- Phone Number

### Required Prescriber Information
- Prescriber Name
- NPI (10 digits)
- Practice Name
- Practice Address
- Phone/Fax

### Required Prescription Information
- Product Name (e.g., "Cosentyx")
- Dosage
- Quantity
- SIG (directions)
- Refills

### Required Attestation
- Prescriber Signature (image or typed)
- Signature Date

## Testing Without AWS (Unit Tests)

The test suite uses mocked AWS responses and does not require credentials:

```powershell
# Run all tests
venv\Scripts\python.exe -m pytest tests/ -v

# Run specific test file
venv\Scripts\python.exe -m pytest tests/test_extractors.py -v

# Run with coverage
venv\Scripts\python.exe -m pytest tests/ --cov=src --cov-report=term-missing
```

### Unit Test Coverage

- **test_validators.py**: Field validation logic (dates, NPI, phones, etc.)
- **test_extractors.py**: Field extraction from mocked Textract data
- **test_integration.py**: End-to-end pipeline with mocked AWS services

All tests should pass regardless of sample form quality.

## Testing with AWS (Integration Tests)

### Option 1: Test with Real Forms

Create test forms with complete information and place them in `examples/sample_forms/`:

```powershell
venv\Scripts\python.exe examples\usage_example.py
```

### Option 2: Skip Validation for Testing

To test OCR extraction without validation failures, you can temporarily disable strict validation:

```python
# In your test script
from src.processor import CosentyxFormProcessor
from config.settings import get_settings

settings = get_settings()

# Process with lenient validation (for testing only)
processor = CosentyxFormProcessor()
result = processor.process_document(document_bytes)

# Check what was extracted (even if validation failed)
print(f"Patient Name: {result.patient_info.first_name.value} {result.patient_info.last_name.value}")
print(f"Product: {result.prescription_info.product.value}")
print(f"Validation Status: {result.validation_status}")
print(f"Routing Decision: {result.routing_decision}")
```

### Option 3: Use Payload Data

You can provide complete data via payload to override missing form fields:

```python
payload_data = {
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "01/15/1980",
    "prescriber_npi": "1234567890",
    "product": "Cosentyx"
}

result = processor.process_document(document_bytes, payload_data=payload_data)
```

## Understanding Textract Extraction

### What Textract Extracts:

1. **Raw Text** (raw_text)
   - All text content from document
   - Line by line OCR results
   - Used as fallback for field extraction

2. **Forms** (key-value pairs)
   - Field labels and values
   - Only works with fillable PDF forms or forms with clear labels
   - Limited to 8-20 pairs for text-based forms

3. **Tables** (structured data)
   - Detected table structures
   - Row/column organization
   - Not always present in forms

4. **Checkboxes** (selection states)
   - SELECTED or NOT_SELECTED
   - Confidence scores
   - Useful for yes/no fields

5. **Signatures** (SIGNATURE blocks)
   - Detected signature regions
   - Confidence scores
   - Geometry/position data

### Extraction Statistics (Sample Forms):

```
Blocks: 712-818 total blocks
Forms: 8-20 key-value pairs (limited due to text layout)
Tables: 2-3 tables detected
Checkboxes: 20-27 checkboxes
Signatures: 0-2 signatures (if present)
Processing Time: ~11-15 seconds per document
Cost: ~$0.0025 per document
```

## Debugging Extraction Issues

### Enable Debug Logging

Edit `.env` file:
```bash
LOG_LEVEL=DEBUG
```

### Check Extraction Details

```python
from src.processor import CosentyxFormProcessor

processor = CosentyxFormProcessor()
result = processor.process_document(document_bytes)

# Inspect extracted data
print("\n=== Patient Information ===")
for field_name in ["first_name", "last_name", "date_of_birth"]:
    field = getattr(result.patient_info, field_name)
    print(f"{field_name}:")
    print(f"  Value: {field.value}")
    print(f"  Source: {field.source}")
    print(f"  Confidence: {field.confidence}")
    print(f"  Validated: {field.validated}")

print("\n=== Prescription Information ===")
print(f"Product: {result.prescription_info.product.value}")
print(f"Source: {result.prescription_info.product.source}")

print("\n=== Classification ===")
print(f"Type: {result.document_type}")
print(f"Confidence: {result.classification_confidence}")
```

## Performance Testing

### Benchmark Script

Create `benchmark.py`:

```python
import time
import statistics
from pathlib import Path
from src.processor import CosentyxFormProcessor

processor = CosentyxFormProcessor()
forms_dir = Path("examples/sample_forms")
times = []

for pdf_file in forms_dir.glob("*.pdf"):
    with open(pdf_file, "rb") as f:
        document_bytes = f.read()
    
    start = time.time()
    result = processor.process_document(document_bytes)
    elapsed = time.time() - start
    
    times.append(elapsed)
    print(f"{pdf_file.name}: {elapsed:.2f}s - {result.routing_decision}")

print(f"\nAverage: {statistics.mean(times):.2f}s")
print(f"Median: {statistics.median(times):.2f}s")
print(f"Min: {min(times):.2f}s")
print(f"Max: {max(times):.2f}s")
```

### Expected Performance

- **Processing Time**: 10-15 seconds per document
- **Textract**: ~8-10 seconds
- **Bedrock Classification**: ~1-2 seconds
- **Extraction/Validation**: <1 second

## Common Issues and Solutions

### Issue #1: "Only 8 key-value pairs extracted"

**Cause**: Form uses text layout, not fillable PDF fields

**Solution**: 
- ✅ New text parsing fallback added to `base_extractor.py`
- ✅ Product extraction now searches raw OCR text
- System will automatically extract from raw text when form fields are limited

### Issue #2: "Product field shows support text"

**Cause**: Form field contained long descriptive text instead of product name

**Solution**:
- ✅ Added filter to reject values containing "support", "additional", or >50 chars
- ✅ Added fallback to search for "Cosentyx" in raw text
- Product extraction now more intelligent

### Issue #3: "No signatures detected"

**Cause**: Signature may not be present or format not supported by Textract

**Solution**:
- ✅ Enhanced signature detection to check both `signatures` list and `SIGNATURE` blocks
- ✅ Added fallback to detect signature blocks directly from Textract response
- System now checks multiple sources for signature detection

### Issue #4: "Validation always fails"

**Cause**: Sample forms have incomplete data (expected)

**Solution**:
- ✅ This is correct behavior - forms should be routed to `manual_review`
- ✅ Use payload data to supplement missing fields for testing
- ✅ Test with complete forms for full validation

### Issue #5: "Manual review routing"

**Cause**: Business rules require complete data for automatic processing

**Solution**:
- ✅ This is working as designed
- ✅ Manual review ensures data quality before database entry
- ✅ Document expected behavior (this guide)

## Next Steps

1. **Test with Complete Forms**: Obtain or create forms with all required fields filled
2. **Monitor Production**: Track routing decisions and validation failures
3. **Refine Field Mappings**: Update `FIELD_MAPPINGS` in extractors based on actual form variations
4. **Tune Confidence Thresholds**: Adjust `textract_confidence_threshold` in `.env` if needed
5. **Add Custom Validation**: Extend `BusinessRules` for organization-specific requirements

## Support

For issues or questions:
1. Check logs in console output (set `LOG_LEVEL=DEBUG`)
2. Review [FIELD_MAPPING.md](FIELD_MAPPING.md) for field name variations
3. See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
4. Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API usage
