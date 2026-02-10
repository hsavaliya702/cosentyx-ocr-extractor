"""AWS Lambda handler for Cosentyx form processing."""

import json
import base64
from typing import Dict, Any

from src.processor import CosentyxFormProcessor
from src.utils.logger import get_logger
from src.utils.s3_helper import S3Helper

logger = get_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point for processing Cosentyx forms.

    Expected event formats:

    1. S3 Event (triggered by S3 upload):
    {
        "Records": [{
            "s3": {
                "bucket": {"name": "bucket-name"},
                "object": {"key": "file-key"}
            }
        }]
    }

    2. Direct API invocation:
    {
        "document_base64": "<base64-encoded-document>",
        "payload_data": {
            "first_name": "John",
            "last_name": "Doe",
            ...
        }
    }

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Dict: API Gateway response or extraction result
    """
    try:
        logger.info("Lambda function invoked")
        logger.info(f"Event: {json.dumps(event, default=str)[:500]}")

        processor = CosentyxFormProcessor()
        s3_helper = S3Helper()

        document_bytes = None
        payload_data = None
        s3_key = None

        # Handle S3 event
        if "Records" in event and event["Records"]:
            record = event["Records"][0]
            if "s3" in record:
                bucket_name = record["s3"]["bucket"]["name"]
                s3_key = record["s3"]["object"]["key"]

                logger.info(f"Processing S3 object: s3://{bucket_name}/{s3_key}")

                # Download from S3
                document_bytes = s3_helper.download_file(s3_key)

                if not document_bytes:
                    return {
                        "statusCode": 500,
                        "body": json.dumps(
                            {"error": "Failed to download file from S3"}
                        ),
                    }

        # Handle direct API invocation
        elif "document_base64" in event:
            logger.info("Processing base64-encoded document")
            document_bytes = base64.b64decode(event["document_base64"])
            payload_data = event.get("payload_data")

        else:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Invalid event format. Expected S3 event or document_base64"
                    }
                ),
            }

        # Process document
        result = processor.process_document(document_bytes, payload_data)

        # Move file in S3 based on result
        if s3_key:
            if result.validation_status == "complete":
                s3_helper.move_to_processed(s3_key)
            elif result.validation_status == "failed":
                s3_helper.move_to_failed(s3_key)

        # Convert result to dict
        result_dict = result.model_dump()

        logger.info("Processing completed successfully")

        return {
            "statusCode": 200,
            "body": json.dumps(result_dict, default=str),
            "headers": {"Content-Type": "application/json"},
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)

        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
            "headers": {"Content-Type": "application/json"},
        }
