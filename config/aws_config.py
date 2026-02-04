"""AWS service configuration and client initialization."""
import boto3
from botocore.config import Config as BotoConfig
from config.settings import get_settings

settings = get_settings()


def get_textract_client():
    """Get AWS Textract client.
    
    Returns:
        boto3.client: Textract client
    """
    boto_config = BotoConfig(
        region_name=settings.aws_region,
        retries={"max_attempts": settings.textract_max_retries, "mode": "standard"},
    )

    client_kwargs = {"config": boto_config}
    
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    return boto3.client("textract", **client_kwargs)


def get_bedrock_client():
    """Get AWS Bedrock Runtime client.
    
    Returns:
        boto3.client: Bedrock Runtime client
    """
    boto_config = BotoConfig(
        region_name=settings.aws_region,
        retries={"max_attempts": 3, "mode": "standard"},
    )

    client_kwargs = {"config": boto_config}
    
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    return boto3.client("bedrock-runtime", **client_kwargs)


def get_s3_client():
    """Get AWS S3 client.
    
    Returns:
        boto3.client: S3 client
    """
    boto_config = BotoConfig(region_name=settings.aws_region)

    client_kwargs = {"config": boto_config}
    
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    return boto3.client("s3", **client_kwargs)


def get_dynamodb_client():
    """Get AWS DynamoDB client.
    
    Returns:
        boto3.client: DynamoDB client
    """
    boto_config = BotoConfig(region_name=settings.dynamodb_region)

    client_kwargs = {"config": boto_config}
    
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    return boto3.client("dynamodb", **client_kwargs)
