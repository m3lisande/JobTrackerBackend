"""
Backblaze B2 (S3-compatible) storage for resume uploads.
Uses boto3 with a custom endpoint; works with minimal changes like S3.
"""
import mimetypes
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


def upload_resume(application_id: str, file_stream: BinaryIO, filename: str) -> str:
    """
    Upload a resume file to B2. Returns the object key (stored in Application.resume_key).
    """
    key = f"resumes/{application_id}/{filename}"
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    client = _client()
    client.upload_fileobj(
        file_stream,
        settings.b2_bucket_name,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def get_presigned_resume_url(resume_key: str, expires_in: int = 3600) -> str:
    """
    Return a presigned URL so the company (or user) can open/download the resume.
    Default expiry 1 hour.
    """
    client = _client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.b2_bucket_name, "Key": resume_key},
        ExpiresIn=expires_in,
    )
