"""Application settings management using Pydantic."""
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # S3 Configuration
    s3_bucket_name: str = "cosentyx-forms"
    s3_processed_prefix: str = "processed/"
    s3_failed_prefix: str = "failed/"

    # Textract Configuration
    textract_confidence_threshold: float = 0.85
    textract_max_retries: int = 3

    # Bedrock Configuration
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_max_tokens: int = 4096
    bedrock_temperature: float = 0.1

    # Application Configuration
    log_level: str = "INFO"
    enable_duplicate_check: bool = True
    enable_bedrock_validation: bool = True

    # DynamoDB Configuration (optional)
    dynamodb_table_name: Optional[str] = "cosentyx-extractions"
    dynamodb_region: str = "us-east-1"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()
