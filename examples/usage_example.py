"""Usage examples for Cosentyx OCR Extractor."""
import json
from pathlib import Path
from src.processor import CosentyxFormProcessor


def example_basic_processing():
    """Example: Basic document processing."""
    print("=" * 80)
    print("Example 1: Basic Document Processing")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Load document
    pdf_path = Path(__file__).parent / "sample_forms" / "EMA-Start-Form_1.pdf"
    
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()
    
    # Process document
    print("Processing document...")
    result = processor.process_document(document_bytes)
    
    # Display results
    print(f"\nDocument Type: {result.document_type}")
    print(f"Classification Confidence: {result.classification_confidence:.2f}")
    print(f"Validation Status: {result.validation_status}")
    print(f"Routing Action: {result.routing.action}")
    
    if result.patient.first_name.value:
        print(f"\nPatient: {result.patient.first_name.value} {result.patient.last_name.value}")
        print(f"DOB: {result.patient.dob.value}")
        print(f"Gender: {result.patient.gender.value}")
    
    if result.prescriber.first_name.value:
        print(f"\nPrescriber: {result.prescriber.first_name.value} {result.prescriber.last_name.value}")
        print(f"NPI: {result.prescriber.npi.value}")
    
    if result.prescription.product.value:
        print(f"\nPrescription: {result.prescription.product.value} {result.prescription.dosage.value}")
        print(f"Quantity: {result.prescription.quantity.value}")
    
    print(f"\nProcessing Time: {result.metadata.processing_time_ms}ms")
    print(f"Estimated Cost: ${result.metadata.textract_cost_estimate + result.metadata.bedrock_cost_estimate:.4f}")


def example_with_payload_data():
    """Example: Processing with supplemental payload data."""
    print("\n" + "=" * 80)
    print("Example 2: Processing with Payload Data")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Load document
    pdf_path = Path(__file__).parent / "sample_forms" / "EMA-Start-Form_1.pdf"
    
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


def example_json_export():
    """Example: Export results to JSON."""
    print("\n" + "=" * 80)
    print("Example 3: Export to JSON")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Load document
    pdf_path = Path(__file__).parent / "sample_forms" / "EMA-Start-Form_1.pdf"
    
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()
    
    # Process document
    result = processor.process_document(document_bytes)
    
    # Convert to JSON
    result_json = result.model_dump_json(indent=2)
    
    # Save to file
    output_path = Path(__file__).parent / "sample_output.json"
    with open(output_path, "w") as f:
        f.write(result_json)
    
    print(f"Results exported to: {output_path}")
    print(f"File size: {len(result_json)} bytes")


def example_error_handling():
    """Example: Error handling."""
    print("\n" + "=" * 80)
    print("Example 4: Error Handling")
    print("=" * 80)
    
    # Initialize processor
    processor = CosentyxFormProcessor()
    
    # Try processing invalid data
    try:
        result = processor.process_document(b"invalid pdf data")
        print(f"Validation Status: {result.validation_status}")
        print(f"Errors: {result.validation_errors}")
        print(f"Routing: {result.routing.action}")
        print(f"Review Reason: {result.routing.review_reason}")
    except Exception as e:
        print(f"Error: {str(e)}")


def example_batch_processing():
    """Example: Batch processing multiple documents."""
    print("\n" + "=" * 80)
    print("Example 5: Batch Processing")
    print("=" * 80)
    
    # Initialize processor (reuse for all documents)
    processor = CosentyxFormProcessor()
    
    # Process multiple documents
    sample_dir = Path(__file__).parent / "sample_forms"
    pdf_files = list(sample_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in sample_forms directory")
        return
    
    results = []
    
    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        
        with open(pdf_path, "rb") as f:
            document_bytes = f.read()
        
        result = processor.process_document(document_bytes)
        results.append({
            "filename": pdf_path.name,
            "document_type": result.document_type,
            "validation_status": result.validation_status,
            "routing_action": result.routing.action,
            "processing_time_ms": result.metadata.processing_time_ms
        })
    
    # Summary
    print("\n" + "-" * 80)
    print("Batch Processing Summary")
    print("-" * 80)
    print(f"Total documents: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['validation_status'] == 'complete')}")
    print(f"Partial: {sum(1 for r in results if r['validation_status'] == 'partial')}")
    print(f"Failed: {sum(1 for r in results if r['validation_status'] == 'failed')}")
    
    avg_time = sum(r['processing_time_ms'] for r in results) / len(results)
    print(f"Average processing time: {avg_time:.0f}ms")


if __name__ == "__main__":
    # Run all examples
    try:
        example_basic_processing()
        example_with_payload_data()
        example_json_export()
        example_error_handling()
        example_batch_processing()
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        print("Note: Examples require AWS credentials and access to Textract/Bedrock")
