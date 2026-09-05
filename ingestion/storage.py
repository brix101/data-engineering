import logging
import os
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_s3_client():
    """Build an S3 client pointed at MinIO (or real S3 via env vars)."""
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY", "minioadmin"),
        region_name=os.getenv("S3_REGION", "us-east-1"),
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket(client, bucket_name: str) -> None:
    try:
        client.head_bucket(Bucket=bucket_name)
    except ClientError as exc:
        error_code = exc.response["Error"].get("Code")

        if error_code in ("404", "NoSuchBucket"):
            client.create_bucket(Bucket=bucket_name)
            logger.info("Created bucket '%s'", bucket_name)
            return

        raise


def upload_file(
    client, bucket_name: str, file_path: str | Path, object_name: str
) -> None:
    """
    Upload a file to an S3-compatible bucket (MinIO by default).

    :param file_path: Path to the file to upload
    :param bucket_name: Name of the bucket to upload to
    :param object_name: Key of the object in the bucket
    """
    logger.info("Uploading %s -> s3://%s/%s", file_path, bucket_name, object_name)

    try:
        client.upload_file(str(file_path), bucket_name, object_name)
        logger.info("Uploaded %s -> s3://%s/%s", file_path, bucket_name, object_name)
    except ClientError:
        logger.exception("Failed to upload %s", file_path)
        raise


def object_exists(client, bucket_name: str, object_name: str) -> bool:
    """
    Check if an object exists in an S3-compatible bucket.

    :param bucket_name: Name of the bucket
    :param object_name: Key of the object in the bucket
    :return: True if the object exists, False otherwise
    """
    try:
        client.head_object(Bucket=bucket_name, Key=object_name)
        return True
    except ClientError as exc:
        error_code = exc.response["Error"].get("Code")
        if error_code in ("404", "NoSuchKey"):
            return False
        raise
