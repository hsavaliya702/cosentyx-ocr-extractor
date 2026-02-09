"""Usage examples for Cosentyx OCR Extractor with Multiple Prescriptions Support."""
import json
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processor import CosentyxFormProcessor

# PDF filename constants - change these to test with different files
CosentyxStartForm = "CosentyxStartForm-7.pdf"

def example_complete_pipeline():
    """
    Complete pipeline example following the architecture diagram:
    
    Step 0: PDF Document Input
    Step 1: OCR Processing (AWS Textract)
    Step 2: Document Classification (AWS Bedrock)
    Step 3: Field Extraction (Patient, Prescriber, Prescriptions, Attestation)
    Step 4: Validation (Field validators + Business rules)
    Step 5: Routing Decision (Create full profile / patient only / manual review)
    """
    print("\n")
    print("+" + "="*78 + "+")
    print("|" + " "*15 + "COSENTYX OCR EXTRACTOR - COMPLETE PIPELINE" + " "*20 + "|")
    print("|" + " "*15 + "Following Architecture Diagram Workflow" + " "*23 + "|")
    print("+" + "="*78 + "+")
    
    # ============================================================================
    # STEP 0: PDF Document Input
    # ============================================================================
    print("\n" + "="*80)
    print("STEP 0: PDF DOCUMENT INPUT")
    print("="*80)
    
    pdf_path = Path(__file__).parent / "sample_forms" / CosentyxStartForm
    
    if not pdf_path.exists():
        print(f"❌ Error: Sample PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()
    
    print(f"[OK] Document loaded: {pdf_path.name}")
    print(f"  File size: {len(document_bytes):,} bytes")
    
    # ============================================================================
    # Initialize Processor (handles all pipeline steps internally)
    # ============================================================================
    print("\n" + "="*80)
    print("INITIALIZING PROCESSOR")
    print("="*80)
    print("[OK] CosentyxFormProcessor initialized")
    print("  Components:")
    print("    - AWS Textract Client (OCR)")
    print("    - AWS Bedrock Classifier (Claude 3.5 Sonnet)")
    print("    - Field Extractors (Patient, Prescriber, Prescription, Attestation)")
    print("    - Validators (Field + Business Rules)")
    
    processor = CosentyxFormProcessor()
    
    # ============================================================================
    # STEPS 1-5: Process Document (all pipeline steps)
    # ============================================================================
    print("\n" + "="*80)
    print("PROCESSING PIPELINE")
    print("="*80)
    print("[PROCESSING] Document through complete pipeline...")
    print("   Step 1: OCR with AWS Textract (extracting forms, tables, signatures)")
    print("   Step 2: Classification with AWS Bedrock (determining document type)")
    print("   Step 3: Field Extraction (patient, prescriber, prescriptions, attestation)")
    print("   Step 4: Validation (field-level + business rules)")
    print("   Step 5: Routing Decision (determining next action)")
    print("\n   This may take 10-30 seconds...\n")
    
    result = processor.process_document(document_bytes)
    
    # ============================================================================
    # PIPELINE RESULTS
    # ============================================================================
    print("="*80)
    print("PIPELINE RESULTS")
    print("="*80)
    
    # Document Information (from Steps 1-2)
    print("\n[DOC] STEP 1-2: OCR & CLASSIFICATION RESULTS")
    print("-" * 80)
    print(f"Document ID:                {result.document_id}")
    print(f"Document Type:              {result.document_type}")
    print(f"Classification Confidence:  {result.classification_confidence:.1%}")
    print(f"Processing Time:            {result.metadata.processing_time_ms}ms")
    print(f"Textract Cost Estimate:     ${result.metadata.textract_cost_estimate:.4f}")
    print(f"Bedrock Cost Estimate:      ${result.metadata.bedrock_cost_estimate:.4f}")
    print(f"Total Cost:                 ${result.metadata.textract_cost_estimate + result.metadata.bedrock_cost_estimate:.4f}")
    
    # Patient Information (from Step 3)
    print("\n[PATIENT] STEP 3a: PATIENT EXTRACTION")
    print("-" * 80)
    print(f"Name:        {result.patient.first_name.value or 'N/A'} {result.patient.last_name.value or 'N/A'}")
    print(f"  Source:    {result.patient.first_name.source}, {result.patient.last_name.source}")
    print(f"  Confidence: {result.patient.first_name.confidence:.1%}, {result.patient.last_name.confidence:.1%}")
    print(f"DOB:         {result.patient.dob.value or 'N/A'}")
    print(f"  Validated: {result.patient.dob.validated}")
    print(f"Gender:      {result.patient.gender.value or 'N/A'}")
    print(f"Phone:       {result.patient.phone.value or 'N/A'}")
    print(f"Email:       {result.patient.email.value or 'N/A'}")
    print(f"Language:    {result.patient.preferred_language.value or 'N/A'}")
    print(f"Valid:       {'[PASS]' if result.patient.is_valid() else '[FAIL]'}")
    
    # Prescriber Information (from Step 3)
    print("\n[PRESCRIBER] STEP 3b: PRESCRIBER EXTRACTION")
    print("-" * 80)
    print(f"Name:        {result.prescriber.first_name.value or 'N/A'} {result.prescriber.last_name.value or 'N/A'}")
    print(f"  Source:    {result.prescriber.first_name.source}, {result.prescriber.last_name.source}")
    print(f"NPI:         {result.prescriber.npi.value or 'N/A'}")
    print(f"  Validated: {result.prescriber.npi.validated}")
    print(f"Phone:       {result.prescriber.phone.value or 'N/A'}")
    print(f"Fax:         {result.prescriber.fax.value or 'N/A'}")
    print(f"Address:     {result.prescriber.address.street.value or 'N/A'}")
    if result.prescriber.address.city.value:
        print(f"             {result.prescriber.address.city.value} {result.prescriber.address.state.value or ''} {result.prescriber.address.zip.value or ''}")
    print(f"Valid:       {'[PASS]' if result.prescriber.is_valid() else '[FAIL]'}")
    
    # Prescription Information - Multiple Prescriptions (from Step 3)
    print("\n[RX] STEP 3c: PRESCRIPTION EXTRACTION (MULTIPLE PRESCRIPTIONS)")
    print("-" * 80)
    print(f"Total Prescriptions Detected: {len(result.prescription.prescriptions)}")
    print(f"Valid Prescriptions:          {len(result.prescription.get_valid_prescriptions())}")
    print(f"Overall Valid:                {'[PASS]' if result.prescription.is_valid() else '[FAIL]'}")
    
    if result.prescription.prescriptions:
        print("\n📋 Prescription Details:")
        for i, rx in enumerate(result.prescription.prescriptions, 1):
            print(f"\n   Prescription #{i}: {rx.get_display_name()}")
            print(f"   {'─'*76}")
            print(f"   Product:       {rx.product.value}")
            print(f"     Confidence:  {rx.product.confidence:.1%}")
            print(f"     Source:      {rx.product.source}")
            print(f"   Dosage:        {rx.dosage.value}")
            print(f"   Form:          {rx.form.value}")
            print(f"   Dose Type:     {rx.dose_type.value}")
            print(f"   Patient Type:  {rx.patient_type.value}")
            print(f"   Quantity:      {rx.quantity.value} units")
            print(f"   Refills:       {rx.refills.value}")
            print(f"   SIG:           {rx.sig.value[:80]}{'...' if len(rx.sig.value) > 80 else ''}")
            print(f"   Valid:         {'[PASS]' if rx.is_valid() else '[FAIL]'}")
    else:
        print("   ⚠️  No prescriptions extracted")
    
    # Attestation (from Step 3)
    print("\n[ATTESTATION] STEP 3d: ATTESTATION EXTRACTION")
    print("-" * 80)
    print(f"Signature Present:  {result.attestation.signature_present}")
    print(f"Name:               {result.attestation.name.value or 'N/A'}")
    print(f"Date:               {result.attestation.date.value or 'N/A'}")
    print(f"Valid:              {'[PASS]' if result.attestation.is_valid() else '[FAIL]'}")
    
    # Validation Summary (from Step 4)
    print("\n[VALIDATION] STEP 4: VALIDATION SUMMARY")
    print("-" * 80)
    print(f"Overall Validation Status: {result.validation_status.upper()}")
    print(f"Patient Valid:             {'[Y]' if result.patient.is_valid() else '[N]'}")
    print(f"Prescriber Valid:          {'[Y]' if result.prescriber.is_valid() else '[N]'}")
    print(f"Prescription Valid:        {'[Y]' if result.prescription.is_valid() else '[N]'}")
    print(f"Attestation Valid:         {'[Y]' if result.attestation.is_valid() else '[N]'}")
    
    # Warnings
    if result.warnings:
        print(f"\n[WARNING] Validation Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    # Errors
    if result.validation_errors:
        print(f"\n[ERROR] Validation Errors ({len(result.validation_errors)}):")
        for error in result.validation_errors:
            print(f"   - {error}")
    
    # Routing Decision (from Step 5)
    print("\n[ROUTING] STEP 5: ROUTING DECISION")
    print("-" * 80)
    print(f"Action:                    {result.routing.action.upper()}")
    print(f"Create Patient Profile:    {'[YES]' if result.routing.create_patient_profile else '[NO]'}")
    print(f"Create Prescriber Profile: {'[YES]' if result.routing.create_prescriber_profile else '[NO]'}")
    print(f"Create Prescription(s):    {'[YES]' if result.routing.create_prescription else '[NO]'}")
    if result.routing.create_prescription and result.prescription.prescriptions:
        print(f"  -> Will create {len(result.prescription.get_valid_prescriptions())} prescription(s)")
    print(f"Manual Review Required:    {'[YES]' if result.routing.manual_review_required else '[NO]'}")
    if result.routing.review_reason:
        print(f"Review Reason:             {result.routing.review_reason}")
    
    # Routing Logic Explanation
    print("\n[LOGIC] Routing Logic:")
    if result.routing.action == "create_full_profile":
        print("   [PASS] All components valid -> Creating complete patient profile with prescriptions")
    elif result.routing.action == "create_patient_only":
        print("   [WARNING] Patient valid but incomplete data -> Creating patient profile only")
    else:
        print("   [FAIL] Validation failed -> Sending to manual review")
    
    # JSON Export
    print("\n[EXPORT] OPTIONAL: JSON EXPORT")
    print("-" * 80)
    output_path = Path(__file__).parent / "pipeline_output.json"
    with open(output_path, "w") as f:
        f.write(result.model_dump_json(indent=2))
    print(f"[OK] Complete results exported to: {output_path}")
    print(f"  File contains all extracted data including {len(result.prescription.prescriptions)} prescription(s)")
    
    # Final Summary
    print("\n" + "="*80)
    print("PIPELINE EXECUTION COMPLETE")
    print("="*80)
    print(f"[OK] Document processed successfully in {result.metadata.processing_time_ms}ms")
    print(f"[OK] Document classified as: {result.document_type}")
    print(f"[OK] Extracted {len(result.prescription.prescriptions)} prescription(s)")
    print(f"[OK] Validation status: {result.validation_status}")
    print(f"[OK] Routing decision: {result.routing.action}")
    print(f"[OK] Total cost: ${result.metadata.textract_cost_estimate + result.metadata.bedrock_cost_estimate:.4f}")
    print("="*80 + "\n")


def example_basic_processing():
    """Example: Complete document processing showing all extracted fields."""
    print("=" * 80)
    print("Example 1: Complete Document Processing (All Fields)")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Load document
    pdf_path = Path(__file__).parent / "sample_forms" / DEFAULT_PDF_FORM_2
    
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()
    
    # Process document
    print("Processing document (this may take 10-30 seconds)...\n")
    result = processor.process_document(document_bytes)
    
    # ============================================================================
    # Document Information
    # ============================================================================
    print("📄 DOCUMENT INFORMATION")
    print("-" * 80)
    print(f"Document ID:                {result.document_id}")
    print(f"Document Type:              {result.document_type}")
    print(f"Classification Confidence:  {result.classification_confidence:.1%}")
    print(f"Validation Status:          {result.validation_status}")
    print(f"Processing Time:            {result.metadata.processing_time_ms}ms")
    print(f"Estimated Cost:             ${result.metadata.textract_cost_estimate + result.metadata.bedrock_cost_estimate:.4f}")
    
    # ============================================================================
    # Patient Information
    # ============================================================================
    print("\n👤 PATIENT INFORMATION")
    print("-" * 80)
    print(f"Name:        {result.patient.first_name.value or 'N/A'} {result.patient.last_name.value or 'N/A'}")
    print(f"DOB:         {result.patient.dob.value or 'N/A'}")
    print(f"Gender:      {result.patient.gender.value or 'N/A'}")
    print(f"Phone:       {result.patient.phone.value or 'N/A'}")
    print(f"Email:       {result.patient.email.value or 'N/A'}")
    print(f"Address:     {result.patient.address.street.value or 'N/A'}")
    print(f"             {result.patient.address.city.value or ''} {result.patient.address.state.value or ''} {result.patient.address.zip.value or ''}")
    print(f"Valid:       {'✓ Yes' if result.patient.is_valid() else '✗ No'}")
    
    # ============================================================================
    # Prescriber Information
    # ============================================================================
    print("\n👨‍⚕️ PRESCRIBER INFORMATION")
    print("-" * 80)
    print(f"Name:        {result.prescriber.first_name.value or 'N/A'} {result.prescriber.last_name.value or 'N/A'}")
    print(f"NPI:         {result.prescriber.npi.value or 'N/A'}")
    print(f"Phone:       {result.prescriber.phone.value or 'N/A'}")
    print(f"Fax:         {result.prescriber.fax.value or 'N/A'}")
    print(f"Address:     {result.prescriber.address.street.value or 'N/A'}")
    print(f"             {result.prescriber.address.city.value or ''} {result.prescriber.address.state.value or ''} {result.prescriber.address.zip.value or ''}")
    print(f"Valid:       {'✓ Yes' if result.prescriber.is_valid() else '✗ No'}")
    
    # ============================================================================
    # Prescription Information (Multiple Prescriptions)
    # ============================================================================
    print("\n💊 PRESCRIPTION INFORMATION")
    print("-" * 80)
    print(f"Total Prescriptions:  {len(result.prescription.prescriptions)}")
    print(f"Valid Prescriptions:  {len(result.prescription.get_valid_prescriptions())}")
    print(f"Overall Valid:        {'✓ Yes' if result.prescription.is_valid() else '✗ No'}")
    
    if result.prescription.prescriptions:
        print("\n📋 Prescription Details:")
        for i, rx in enumerate(result.prescription.prescriptions, 1):
            print(f"\n   Prescription #{i}: {rx.get_display_name()}")
            print(f"   {'─'*76}")
            print(f"   Product:       {rx.product.value} (confidence: {rx.product.confidence:.1%})")
            print(f"   Dosage:        {rx.dosage.value}")
            print(f"   Form:          {rx.form.value}")
            print(f"   Dose Type:     {rx.dose_type.value}")
            print(f"   Patient Type:  {rx.patient_type.value}")
            print(f"   Quantity:      {rx.quantity.value}")
            print(f"   Refills:       {rx.refills.value}")
            print(f"   SIG:           {rx.sig.value}")
            print(f"   Valid:         {'✓ Yes' if rx.is_valid() else '✗ No'}")
            print(f"   Source:        {rx.product.source}")
    else:
        print("   ⚠️  No prescriptions extracted")
    
    # ============================================================================
    # Attestation Information
    # ============================================================================
    print("\n✍️ ATTESTATION INFORMATION")
    print("-" * 80)
    print(f"Signature Present:  {result.attestation.signature_present}")
    print(f"Name:               {result.attestation.name.value or 'N/A'}")
    print(f"Date:               {result.attestation.date.value or 'N/A'}")
    print(f"Valid:              {'✓ Yes' if result.attestation.is_valid() else '✗ No'}")
    
    # ============================================================================
    # Routing Decision
    # ============================================================================
    print("\n🔀 ROUTING DECISION")
    print("-" * 80)
    print(f"Action:                    {result.routing.action.upper()}")
    print(f"Create Patient Profile:    {result.routing.create_patient_profile}")
    print(f"Create Prescriber Profile: {result.routing.create_prescriber_profile}")
    print(f"Create Prescription:       {result.routing.create_prescription}")
    print(f"Manual Review Required:    {result.routing.manual_review_required}")
    if result.routing.review_reason:
        print(f"Review Reason:             {result.routing.review_reason}")
    
    # ============================================================================
    # Warnings and Errors
    # ============================================================================
    if result.warnings:
        print(f"\n⚠️  WARNINGS ({len(result.warnings)})")
        print("-" * 80)
        for warning in result.warnings:
            print(f"   • {warning}")
    
    if result.validation_errors:
        print(f"\n❌ VALIDATION ERRORS ({len(result.validation_errors)})")
        print("-" * 80)
        for error in result.validation_errors:
            print(f"   • {error}")


def example_with_payload_data():
    """Example: Processing with supplemental payload data."""
    print("\n\n" + "=" * 80)
    print("Example 2: Processing with Payload Data")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Load document
    pdf_path = Path(__file__).parent / "sample_forms" / DEFAULT_PDF_FORM_3
    
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()
    
    # Supplemental payload data (e.g., from an existing patient record)
    payload_data = {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "01/15/1980",
        "gender": "M",
        "phone": "5551234567"
    }
    
    # Process document with payload
    print("Processing document with payload data...")
    result = processor.process_document(document_bytes, payload_data)
    
    # Show which fields came from payload vs form
    print("\nField Sources:")
    print(f"  First Name: {result.patient.first_name.value} (from {result.patient.first_name.source})")
    print(f"  Last Name: {result.patient.last_name.value} (from {result.patient.last_name.source})")
    print(f"  DOB: {result.patient.dob.value} (from {result.patient.dob.source})")
    
    # Show prescriptions
    print(f"\nExtracted {len(result.prescription.prescriptions)} prescription(s)")
    for i, rx in enumerate(result.prescription.prescriptions, 1):
        print(f"  {i}. {rx.get_display_name()}")


def example_filtering_prescriptions():
    """Example: Filtering and working with multiple prescriptions."""
    print("\n\n" + "=" * 80)
    print("Example 3: Filtering Multiple Prescriptions")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Load document
    pdf_path = Path(__file__).parent / "sample_forms" / DEFAULT_PDF_FORM_2
    
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()
    
    # Process document
    print("Processing document...\n")
    result = processor.process_document(document_bytes)
    
    # Get all prescriptions
    all_prescriptions = result.prescription.prescriptions
    print(f"Total prescriptions: {len(all_prescriptions)}")
    
    # Filter by dose type
    loading_doses = [rx for rx in all_prescriptions if rx.dose_type.value == "Loading"]
    maintenance_doses = [rx for rx in all_prescriptions if rx.dose_type.value == "Maintenance"]
    
    print(f"\nLoading Doses: {len(loading_doses)}")
    for rx in loading_doses:
        print(f"  • {rx.get_display_name()} - Qty: {rx.quantity.value}, Refills: {rx.refills.value}")
    
    print(f"\nMaintenance Doses: {len(maintenance_doses)}")
    for rx in maintenance_doses:
        print(f"  • {rx.get_display_name()} - Qty: {rx.quantity.value}, Refills: {rx.refills.value}")
    
    # Filter by form
    pen_prescriptions = [rx for rx in all_prescriptions if rx.form.value == "Pen"]
    syringe_prescriptions = [rx for rx in all_prescriptions if rx.form.value == "Syringe"]
    
    print(f"\nPen Prescriptions: {len(pen_prescriptions)}")
    print(f"Syringe Prescriptions: {len(syringe_prescriptions)}")
    
    # Get only valid prescriptions
    valid_prescriptions = result.prescription.get_valid_prescriptions()
    print(f"\nValid Prescriptions: {len(valid_prescriptions)}/{len(all_prescriptions)}")


def example_json_export():
    """Example: Export results to JSON."""
    print("\n\n" + "=" * 80)
    print("Example 4: Export to JSON")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Load document
    pdf_path = Path(__file__).parent / "sample_forms" / DEFAULT_PDF_FORM_2
    
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()
    
    # Process document
    print("Processing document...")
    result = processor.process_document(document_bytes)
    
    # Convert to JSON
    result_json = result.model_dump_json(indent=2)
    
    # Save to file
    output_path = Path(__file__).parent / "sample_output.json"
    with open(output_path, "w") as f:
        f.write(result_json)
    
    print(f"\nResults exported to: {output_path}")
    print(f"File size: {len(result_json):,} bytes")
    
    # Show prescription count in JSON
    result_dict = result.model_dump()
    prescription_count = len(result_dict["prescription"]["prescriptions"])
    print(f"Prescriptions in JSON: {prescription_count}")
    
    # Show sample prescription from JSON
    if prescription_count > 0:
        first_rx = result_dict["prescription"]["prescriptions"][0]
        print(f"\nFirst prescription:")
        print(f"  Product: {first_rx['product']['value']}")
        print(f"  Form: {first_rx['form']['value']}")
        print(f"  Dose Type: {first_rx['dose_type']['value']}")
        print(f"  Quantity: {first_rx['quantity']['value']}")


def example_error_handling():
    """Example: Error handling."""
    print("\n\n" + "=" * 80)
    print("Example 5: Error Handling")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Try processing invalid data
    try:
        result = processor.process_document(b"invalid pdf data")
        print(f"Validation Status: {result.validation_status}")
        print(f"Errors: {len(result.validation_errors)}")
        if result.validation_errors:
            for error in result.validation_errors:
                print(f"  • {error}")
        print(f"Routing: {result.routing.action}")
        print(f"Review Reason: {result.routing.review_reason}")
    except Exception as e:
        print(f"Error: {str(e)}")


# def example_batch_processing():
#     """Example: Batch processing multiple documents."""
#     print("\n\n" + "=" * 80)
#     print("Example 6: Batch Processing")
#     print("=" * 80)
    
#     # Initialize processor (reuse for all documents)
#     processor = CosentyxFormProcessor()
    
#     # Process multiple documents
#     sample_dir = Path(__file__).parent / "sample_forms"
#     pdf_files = list(sample_dir.glob("*.pdf"))
    
#     if not pdf_files:
#         print("No PDF files found in sample_forms directory")
#         return
    
#     results = []
    
#     for pdf_path in pdf_files:
#         print(f"\nProcessing: {pdf_path.name}")
        
#         with open(pdf_path, "rb") as f:
#             document_bytes = f.read()
        
#         result = processor.process_document(document_bytes)
        
#         # Count prescriptions
#         prescription_count = len(result.prescription.prescriptions)
#         valid_prescription_count = len(result.prescription.get_valid_prescriptions())
        
#         results.append({
#             "filename": pdf_path.name,
#             "document_type": result.document_type,
#             "validation_status": result.validation_status,
#             "routing_action": result.routing.action,
#             "processing_time_ms": result.metadata.processing_time_ms,
#             "total_prescriptions": prescription_count,
#             "valid_prescriptions": valid_prescription_count
#         })
        
#         print(f"  Status: {result.validation_status}")
#         print(f"  Prescriptions: {prescription_count} total, {valid_prescription_count} valid")
#         print(f"  Time: {result.metadata.processing_time_ms}ms")
    
#     # Summary
#     print("\n" + "-" * 80)
#     print("Batch Processing Summary")
#     print("-" * 80)
#     print(f"Total documents:        {len(results)}")
#     print(f"Successful:             {sum(1 for r in results if r['validation_status'] == 'complete')}")
#     print(f"Partial:                {sum(1 for r in results if r['validation_status'] == 'partial')}")
#     print(f"Failed:                 {sum(1 for r in results if r['validation_status'] == 'failed')}")
#     print(f"Total prescriptions:    {sum(r['total_prescriptions'] for r in results)}")
#     print(f"Valid prescriptions:    {sum(r['valid_prescriptions'] for r in results)}")
    
#     avg_time = sum(r['processing_time_ms'] for r in results) / len(results) if results else 0
#     print(f"Average processing time: {avg_time:.0f}ms")


if __name__ == "__main__":
    try:
        # Run the complete pipeline example (follows architecture diagram)
        example_complete_pipeline()
        
        # Other examples (commented out - uncomment to run individual examples)
        # example_basic_processing()
        # example_with_payload_data()
        # example_filtering_prescriptions()
        # example_json_export()
        # example_error_handling()
        # example_batch_processing()
        
        print("\n✓ Example completed successfully!")
        print("\nFor more information, see:")
        print("  - docs/MULTIPLE_PRESCRIPTIONS.md - Full documentation")
        print("  - docs/DOSING_REFERENCE.md - Dosing schedules")
        print("  - docs/ARCHITECTURE.md - System architecture")
        print("  - QUICK_REFERENCE.md - Quick code examples\n")
        
    except Exception as e:
        print(f"\n[ERROR] Error running example: {str(e)}")
        print("\nNote: This example requires:")
        print("  - AWS credentials configured")
        print("  - Access to AWS Textract and Bedrock services")
        print("  - Sample PDF files in examples/sample_forms/ directory")
        import traceback
        traceback.print_exc()
