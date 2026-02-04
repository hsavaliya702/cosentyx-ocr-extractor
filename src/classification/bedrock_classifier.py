"""Document classification using AWS Bedrock (Claude)."""
import json
from typing import Dict, Tuple
from config.aws_config import get_bedrock_client
from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BedrockClassifier:
    """Use Claude 3.5 Sonnet for document classification."""

    def __init__(self):
        """Initialize Bedrock client."""
        self.client = get_bedrock_client()
        self.model_id = settings.bedrock_model_id
        self.confidence_score = 0.0

    def classify_document(self, text: str) -> Tuple[str, float]:
        """Classify document type using Claude.
        
        Args:
            text: Document text content
            
        Returns:
            Tuple[str, float]: (document_type, confidence_score)
        """
        try:
            logger.info("Starting document classification with Bedrock")
            
            prompt = self._build_classification_prompt(text)
            
            response = self._invoke_bedrock(prompt)
            
            # Parse response
            result = self._parse_classification_response(response)
            
            doc_type = result.get("document_type", "other")
            confidence = result.get("confidence", 0.0)
            
            self.confidence_score = confidence
            
            logger.info(f"Document classified as: {doc_type} (confidence: {confidence:.2f})")
            return doc_type, confidence
            
        except Exception as e:
            logger.error(f"Document classification failed: {str(e)}")
            return "other", 0.0

    def get_confidence_score(self) -> float:
        """Get confidence score of last classification.
        
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        return self.confidence_score

    def _build_classification_prompt(self, text: str) -> str:
        """Build classification prompt for Claude.
        
        Args:
            text: Document text
            
        Returns:
            str: Formatted prompt
        """
        return f"""You are a document classification expert. Classify the following medical document into one of these categories:

Categories:
1. "ema_start_form" - EMA (Enrollment/Medical Assistance) Start Form for Cosentyx
2. "cosentyx_start_form" - Cosentyx Prescription Start Form
3. "cover_letter" - Cover letter or transmittal document
4. "benefits_statement" - Insurance benefits or coverage statement
5. "clinical_info" - Clinical information or medical records
6. "other" - Any other document type

Document Text:
{text[:3000]}

Respond ONLY with a JSON object in this exact format:
{{
    "document_type": "<one of the categories above>",
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation>"
}}"""

    def _invoke_bedrock(self, prompt: str) -> str:
        """Invoke Bedrock API with Claude model.
        
        Args:
            prompt: Prompt text
            
        Returns:
            str: Model response
        """
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": settings.bedrock_max_tokens,
            "temperature": settings.bedrock_temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    def _parse_classification_response(self, response: str) -> Dict:
        """Parse Claude's classification response.
        
        Args:
            response: Raw response text
            
        Returns:
            Dict: Parsed classification result
        """
        try:
            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            
            # Fallback
            return {
                "document_type": "other",
                "confidence": 0.0,
                "reasoning": "Failed to parse response"
            }
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse classification response as JSON")
            return {
                "document_type": "other",
                "confidence": 0.0,
                "reasoning": "JSON parse error"
            }
