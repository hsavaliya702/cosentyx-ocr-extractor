# Single Pipeline Example

## Summary

The `examples/usage_example.py` file now contains a **single comprehensive example** that follows the complete architecture pipeline:

## Main Function: `example_complete_pipeline()`

This function demonstrates the entire pipeline following the architecture diagram:

### Pipeline Steps

```
STEP 0: PDF Document Input
   ↓
STEP 1: OCR Processing (AWS Textract)
   ↓
STEP 2: Document Classification (AWS Bedrock)
   ↓
STEP 3: Field Extraction
   ├─ 3a: Patient Extraction
   ├─ 3b: Prescriber Extraction
   ├─ 3c: Prescription Extraction (Multiple)
   └─ 3d: Attestation Extraction
   ↓
STEP 4: Validation
   ├─ Field-level validation
   └─ Business rules validation
   ↓
STEP 5: Routing Decision
   ├─ Create full profile
   ├─ Create patient only
   └─ Manual review
```

### Output Sections

The example provides detailed output for each step:

1. **Step 0-2**: Document input, OCR, and classification results
2. **Step 3a**: Patient information with source tracking and confidence scores
3. **Step 3b**: Prescriber information with validation status
4. **Step 3c**: Multiple prescriptions with all details (form, dose type, quantity, SIG, refills)
5. **Step 3d**: Attestation information
6. **Step 4**: Validation summary with warnings and errors
7. **Step 5**: Routing decision with logic explanation
8. **JSON Export**: Complete results saved to file
9. **Final Summary**: Processing time, costs, and status

### Features

✅ **Follows Architecture Diagram** - Each step clearly labeled  
✅ **Complete Pipeline** - Shows all stages from input to output  
✅ **Detailed Output** - Every field with metadata (source, confidence, validation)  
✅ **Multiple Prescriptions** - Shows extraction of all prescription combinations  
✅ **Validation Tracking** - Clear pass/fail status for each component  
✅ **Routing Logic** - Explains why a decision was made  
✅ **Cost Tracking** - AWS service cost estimates  
✅ **JSON Export** - Saves complete structured output  

### Other Examples

The following examples are **commented out** but still available in the file:
- `example_basic_processing()` - Original basic processing example
- `example_with_payload_data()` - Using supplemental data
- `example_filtering_prescriptions()` - Filtering multiple prescriptions
- `example_json_export()` - JSON export focus
- `example_error_handling()` - Error handling patterns
- `example_batch_processing()` - Processing multiple files

To run any of these, uncomment the relevant line in the `__main__` section.

## How to Run

```bash
python examples/usage_example.py
```

## Expected Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║               COSENTYX OCR EXTRACTOR - COMPLETE PIPELINE                     ║
║               Following Architecture Diagram Workflow                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
STEP 0: PDF DOCUMENT INPUT
================================================================================
✓ Document loaded: EMA-Start-Form_2.pdf
  File size: 123,456 bytes

================================================================================
INITIALIZING PROCESSOR
================================================================================
✓ CosentyxFormProcessor initialized
  Components:
    • AWS Textract Client (OCR)
    • AWS Bedrock Classifier (Claude 3.5 Sonnet)
    • Field Extractors (Patient, Prescriber, Prescription, Attestation)
    • Validators (Field + Business Rules)

... [complete pipeline output] ...

================================================================================
PIPELINE EXECUTION COMPLETE
================================================================================
✓ Document processed successfully in 15234ms
✓ Document classified as: ema_start_form
✓ Extracted 4 prescription(s)
✓ Validation status: complete
✓ Routing decision: create_full_profile
✓ Total cost: $0.0025
================================================================================
```

## Benefits

- **Educational**: Shows exactly how the pipeline works
- **Debugging**: Easy to see which step fails
- **Comprehensive**: Displays all extracted data
- **Production-Ready**: Demonstrates complete workflow
- **Well-Structured**: Clear separation of pipeline stages
