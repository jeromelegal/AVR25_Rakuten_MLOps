from typing import Annotated
import boto3
from api.config.config import Settings, get_settings
from fastapi import Depends


def get_client(settings: Annotated[Settings, Depends(get_settings)]):
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.MINIO_SERVICE_NAME}:{settings.MINIO_SERVICE_PORT}",
        aws_access_key_id=settings.MINIO_USER,
        aws_secret_access_key=settings.MINIO_PASSWORD,
    )
    return s3
