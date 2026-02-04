"""Main orchestration class for Cosentyx form processing."""
import time
from typing import Dict, Optional

from src.ocr.textract_client import TextractClient
from src.ocr.textract_parser import TextractParser
from src.classification.bedrock_classifier import BedrockClassifier
from src.extraction.patient_extractor import PatientExtractor
from src.extraction.prescriber_extractor import PrescriberExtractor
from src.extraction.prescription_extractor import PrescriptionExtractor
from src.extraction.attestation_extractor import AttestationExtractor
from src.validation.business_rules import BusinessRules
from src.models.extraction_result import ExtractionResult, Metadata
from src.utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class CosentyxFormProcessor:
    """Main orchestration class for processing Cosentyx forms."""

    def __init__(self):
        """Initialize processor with all components."""
        logger.info("Initializing Cosentyx Form Processor")
        
        self.textract = TextractClient()
        self.parser = TextractParser()
        self.classifier = BedrockClassifier()
        self.business_rules = BusinessRules()
        
        self.extractors = {
            'patient': PatientExtractor(),
            'prescriber': PrescriberExtractor(),
            'prescription': PrescriptionExtractor(),
            'attestation': AttestationExtractor()
        }

    def process_document(
        self,
        document_bytes: bytes,
        payload_data: Optional[Dict] = None
    ) -> ExtractionResult:
        """Process a document through the complete pipeline.
        
        Args:
            document_bytes: Document content as bytes
            payload_data: Optional payload data to supplement extraction
            
        Returns:
            ExtractionResult: Complete extraction result with routing decision
        """
        start_time = time.time()
        
        try:
            logger.info("=" * 80)
            logger.info("Starting document processing pipeline")
            logger.info("=" * 80)
            
            # Step 1: OCR with Textract
            logger.info("Step 1: Performing OCR with AWS Textract")
            textract_response = self.textract.analyze_document(document_bytes)
            textract_data = self.parser.parse_response(textract_response)
            
            # Step 2: Classify document
            logger.info("Step 2: Classifying document with AWS Bedrock")
            doc_type, classification_confidence = self.classifier.classify_document(
                textract_data.get("raw_text", "")
            )
            
            # Step 3: Extract structured fields
            logger.info("Step 3: Extracting structured fields")
            result = ExtractionResult()
            result.document_type = doc_type
            result.classification_confidence = classification_confidence
            
            result.patient = self.extractors['patient'].extract(textract_data, payload_data)
            result.prescriber = self.extractors['prescriber'].extract(textract_data, payload_data)
            result.prescription = self.extractors['prescription'].extract(textract_data, payload_data)
            result.attestation = self.extractors['attestation'].extract(textract_data, payload_data)
            
            # Step 4: Apply business rules and determine routing
            logger.info("Step 4: Applying business rules and determining routing")
            self.business_rules.apply_routing_rules(result)
            
            # Step 5: Check for duplicates (if enabled)
            if settings.enable_duplicate_check:
                logger.info("Step 5: Checking for duplicates")
                is_duplicate, signature = self.business_rules.check_duplicate(result)
                if is_duplicate:
                    result.warnings.append(f"Potential duplicate submission: {signature}")
            
            # Calculate processing time and costs
            processing_time = int((time.time() - start_time) * 1000)
            
            # Estimate costs (rough approximation)
            # Textract: $1.50 per 1000 pages for forms
            # Bedrock: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
            textract_cost = 0.0015  # Per page
            bedrock_cost = 0.001  # Approximate for 2 API calls
            
            result.metadata = Metadata(
                processing_time_ms=processing_time,
                textract_cost_estimate=textract_cost,
                bedrock_cost_estimate=bedrock_cost
            )
            
            logger.info("=" * 80)
            logger.info(f"Document processing complete in {processing_time}ms")
            logger.info(f"Document Type: {doc_type}")
            logger.info(f"Validation Status: {result.validation_status}")
            logger.info(f"Routing Action: {result.routing.action}")
            logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}", exc_info=True)
            
            # Return error result
            error_result = ExtractionResult()
            error_result.document_type = "error"
            error_result.validation_status = "failed"
            error_result.validation_errors.append(f"Processing error: {str(e)}")
            error_result.routing.action = "manual_review"
            error_result.routing.manual_review_required = True
            error_result.routing.review_reason = f"Processing error: {str(e)}"
            
            processing_time = int((time.time() - start_time) * 1000)
            error_result.metadata = Metadata(
                processing_time_ms=processing_time,
                textract_cost_estimate=0.0,
                bedrock_cost_estimate=0.0
            )
            
            return error_result
