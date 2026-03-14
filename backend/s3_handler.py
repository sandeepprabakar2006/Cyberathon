"""
s3_handler.py
─────────────
Handles all AWS S3 interactions for the Adaptive Data Protection Engine.

Responsibilities:
  - Connect to S3 using boto3 (reads credentials from environment or IAM role)
  - Fetch file content from a configured S3 bucket
  - Raise structured S3FetchError on failure
"""

import os
import logging
import asyncio
from functools import partial

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

logger = logging.getLogger("ADPE.S3Handler")

# ─── Configuration ──────────────────────────────────────────────────────────────
# Set these via environment variables or AWS IAM role on EC2
S3_BUCKET_NAME: str = os.environ.get("S3_BUCKET_NAME", "adpe-secure-bucket")
AWS_REGION: str = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


class S3FetchError(Exception):
    """Raised when a file cannot be fetched from S3."""


def _get_s3_client():
    """
    Build and return a boto3 S3 client.
    Credentials are automatically resolved from:
      1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
      2. ~/.aws/credentials
      3. EC2 Instance Role (IAM)
    """
    return boto3.client("s3", region_name=AWS_REGION)


def _fetch_sync(file_name: str) -> str:
    """
    Synchronous helper that fetches an S3 object and returns its text content.
    Raises S3FetchError on any failure.
    """
    client = _get_s3_client()
    logger.debug("Fetching s3://%s/%s", S3_BUCKET_NAME, file_name)
    try:
        response = client.get_object(Bucket=S3_BUCKET_NAME, Key=file_name)
        content_bytes: bytes = response["Body"].read()
        text = content_bytes.decode("utf-8", errors="replace")
        logger.info("Fetched '%s' from S3 (%d bytes).", file_name, len(content_bytes))
        return text

    except client.exceptions.NoSuchKey:
        raise S3FetchError(f"File '{file_name}' not found in bucket '{S3_BUCKET_NAME}'.")

    except NoCredentialsError:
        raise S3FetchError(
            "AWS credentials not configured. "
            "Set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY or attach an IAM role."
        )

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        raise S3FetchError(f"S3 ClientError [{error_code}]: {exc.response['Error']['Message']}")

    except BotoCoreError as exc:
        raise S3FetchError(f"BotoCoreError while fetching '{file_name}': {exc}")


async def fetch_file_from_s3(file_name: str) -> str:
    """
    Async wrapper around the synchronous S3 fetch.
    Runs the blocking boto3 call in a thread pool to avoid blocking the event loop.

    Args:
        file_name: S3 object key (e.g. 'employee_records.csv')

    Returns:
        Decoded text content of the file.

    Raises:
        S3FetchError: If the file cannot be retrieved.
    """
    loop = asyncio.get_event_loop()
    # Offload blocking I/O to thread pool executor
    content = await loop.run_in_executor(None, partial(_fetch_sync, file_name))
    return content


def list_bucket_files(prefix: str = "") -> list[str]:
    """
    List all file keys in the configured S3 bucket, with optional prefix filter.

    Args:
        prefix: Filter keys beginning with this string.

    Returns:
        List of S3 object key strings.
    """
    client = _get_s3_client()
    try:
        paginator = client.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        logger.info("Listed %d files in bucket '%s' (prefix='%s').", len(keys), S3_BUCKET_NAME, prefix)
        return keys
    except (ClientError, BotoCoreError) as exc:
        logger.error("Failed to list bucket '%s': %s", S3_BUCKET_NAME, exc)
        return []
