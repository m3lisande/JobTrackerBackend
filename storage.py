"""
Backblaze B2 as S3-compatible storage for resumes. All upload and download via Python (boto3) on the backend.
"""
import mimetypes
import time
from typing import BinaryIO

from config import settings


def _client():
    if not settings.b2_configured:
        raise RuntimeError("B2 is not configured (set B2_KEY_ID, B2_APP_KEY, B2_BUCKET_NAME, B2_ENDPOINT)")
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url=settings.b2_endpoint,
        aws_access_key_id=settings.b2_key_id,
        aws_secret_access_key=settings.b2_app_key,
        region_name=settings.b2_region,
        config=Config(signature_version="s3v4"),
    )


def upload_resume(file_stream: BinaryIO, filename: str, user_id: str) -> str:
    """Upload resume to B2; returns the key to store and pass as resume_key when creating an application."""
    safe_name = filename or "resume.pdf"
    key = f"resumes/{user_id}-{int(time.time() * 1000)}-{safe_name}"
    content_type = mimetypes.guess_type(safe_name)[0] or "application/pdf"
    client = _client()
    client.upload_fileobj(
        file_stream,
        settings.b2_bucket_name,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def resume_key_exists(resume_key: str) -> bool:
    """Return True if the object exists in B2."""
    try:
        client = _client()
        client.head_object(Bucket=settings.b2_bucket_name, Key=resume_key)
        return True
    except Exception:
        return False


def get_presigned_resume_url(resume_key: str, expires_in: int = 300) -> str:
    """
    Return a short-lived presigned URL for downloading the resume (e.g. 5 minutes).
    Company clicks "View Resume" → backend returns this URL → secure and professional.
    """
    client = _client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.b2_bucket_name, "Key": resume_key},
        ExpiresIn=expires_in,
    )


def upload_image(file_stream: BinaryIO, filename: str, company_id: str) -> str:
    """Upload image to B2 under images/; returns the key to store as image_key on job_offer."""
    safe_name = filename or "image"
    key = f"images/{company_id}-{int(time.time() * 1000)}-{safe_name}"
    content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    client = _client()
    client.upload_fileobj(
        file_stream,
        settings.b2_bucket_name,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def image_key_exists(image_key: str) -> bool:
    """Return True if the object exists in B2."""
    try:
        client = _client()
        client.head_object(Bucket=settings.b2_bucket_name, Key=image_key)
        return True
    except Exception:
        return False


def get_presigned_image_url(image_key: str, expires_in: int = 300) -> str:
    """Return a short-lived presigned URL for the job offer image."""
    client = _client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.b2_bucket_name, "Key": image_key},
        ExpiresIn=expires_in,
    )
