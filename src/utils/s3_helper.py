"""S3 helper utilities for file operations."""

import io
from typing import Optional

from config.aws_config import get_s3_client
from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class S3Helper:
    """Helper class for S3 operations."""

    def __init__(self):
        """Initialize S3 helper with client."""
        self.client = get_s3_client()
        self.bucket_name = settings.s3_bucket_name

    def upload_file(
        self, file_bytes: bytes, key: str, content_type: str = "application/pdf"
    ) -> bool:
        """Upload file to S3.

        Args:
            file_bytes: File content as bytes
            key: S3 object key
            content_type: MIME type of the file

        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
            logger.info(f"Successfully uploaded file to s3://{self.bucket_name}/{key}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            return False

    def download_file(self, key: str) -> Optional[bytes]:
        """Download file from S3.

        Args:
            key: S3 object key

        Returns:
            bytes: File content or None if download fails
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            file_bytes = response["Body"].read()
            logger.info(
                f"Successfully downloaded file from s3://{self.bucket_name}/{key}"
            )
            return file_bytes
        except Exception as e:
            logger.error(f"Failed to download file from S3: {str(e)}")
            return None

    def move_to_processed(self, source_key: str) -> bool:
        """Move file to processed folder.

        Args:
            source_key: Source S3 object key

        Returns:
            bool: True if move successful, False otherwise
        """
        try:
            destination_key = (
                f"{settings.s3_processed_prefix}{source_key.split('/')[-1]}"
            )

            # Copy to destination
            self.client.copy_object(
                Bucket=self.bucket_name,
                CopySource={"Bucket": self.bucket_name, "Key": source_key},
                Key=destination_key,
            )

            # Delete source
            self.client.delete_object(Bucket=self.bucket_name, Key=source_key)

            logger.info(f"Moved file from {source_key} to {destination_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file: {str(e)}")
            return False

    def move_to_failed(self, source_key: str) -> bool:
        """Move file to failed folder.

        Args:
            source_key: Source S3 object key

        Returns:
            bool: True if move successful, False otherwise
        """
        try:
            destination_key = f"{settings.s3_failed_prefix}{source_key.split('/')[-1]}"

            # Copy to destination
            self.client.copy_object(
                Bucket=self.bucket_name,
                CopySource={"Bucket": self.bucket_name, "Key": source_key},
                Key=destination_key,
            )

            # Delete source
            self.client.delete_object(Bucket=self.bucket_name, Key=source_key)

            logger.info(f"Moved file from {source_key} to {destination_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file to failed folder: {str(e)}")
            return False
