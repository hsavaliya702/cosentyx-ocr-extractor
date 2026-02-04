"""LLM-based validation using AWS Bedrock."""

import json
from typing import Dict, Any
from config.aws_config import get_bedrock_client
from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BedrockValidator:
    """Use Claude for intelligent field validation and correction."""

    def __init__(self):
        """Initialize Bedrock validator."""
        self.client = get_bedrock_client()
        self.model_id = settings.bedrock_model_id

    def validate_and_correct(
        self, field_name: str, value: str, context: Dict
    ) -> Dict[str, Any]:
        """Validate and potentially correct a field value using Claude.

        Args:
            field_name: Name of the field being validated
            value: Current field value
            context: Additional context (e.g., other extracted fields, document text)

        Returns:
            Dict with validation result:
            {
                "valid": bool,
                "corrected_value": str,
                "confidence": float,
                "reason": str
            }
        """
        if not settings.enable_bedrock_validation:
            return {
                "valid": True,
                "corrected_value": value,
                "confidence": 1.0,
                "reason": "Bedrock validation disabled",
            }

        try:
            logger.info(f"Validating field '{field_name}' with Bedrock")

            prompt = self._build_validation_prompt(field_name, value, context)
            response = self._invoke_bedrock(prompt)
            result = self._parse_validation_response(response)

            logger.info(
                f"Field '{field_name}' validation complete: {result.get('valid')}"
            )
            return result

        except Exception as e:
            logger.error(f"Bedrock validation failed: {str(e)}")
            return {
                "valid": True,  # Fail open
                "corrected_value": value,
                "confidence": 0.5,
                "reason": f"Validation error: {str(e)}",
            }

    def _build_validation_prompt(
        self, field_name: str, value: str, context: Dict
    ) -> str:
        """Build validation prompt for Claude.

        Args:
            field_name: Field name
            value: Field value
            context: Additional context

        Returns:
            str: Formatted prompt
        """
        context_str = json.dumps(context, indent=2)[:1000]  # Limit context size

        return f"""You are a medical form validation expert. Validate and potentially correct the following field.

Field Name: {field_name}
Current Value: {value}

Context (nearby fields and document text):
{context_str}

Task:
1. Determine if the value is valid for this field type
2. If invalid or needs correction, provide the corrected value
3. Assign a confidence score (0.0 to 1.0)
4. Explain your reasoning

Respond ONLY with a JSON object in this exact format:
{{
    "valid": <true or false>,
    "corrected_value": "<corrected value or original if valid>",
    "confidence": <float between 0.0 and 1.0>,
    "reason": "<brief explanation>"
}}"""

    def _invoke_bedrock(self, prompt: str) -> str:
        """Invoke Bedrock API with Claude model.

        Args:
            prompt: Prompt text

        Returns:
            str: Model response
        """
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": settings.bedrock_max_tokens,
                "temperature": settings.bedrock_temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        )

        response = self.client.invoke_model(modelId=self.model_id, body=body)

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude's validation response.

        Args:
            response: Raw response text

        Returns:
            Dict: Parsed validation result
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
                "valid": True,
                "corrected_value": "",
                "confidence": 0.5,
                "reason": "Failed to parse response",
            }

        except json.JSONDecodeError:
            logger.warning("Failed to parse validation response as JSON")
            return {
                "valid": True,
                "corrected_value": "",
                "confidence": 0.5,
                "reason": "JSON parse error",
            }
