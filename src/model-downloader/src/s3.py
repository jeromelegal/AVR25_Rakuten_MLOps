import boto3
from config import Settings


def get_client(settings: Settings):
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.MINIO_SERVICE_NAME}",
        aws_access_key_id=settings.MINIO_MODEL_DOWNLOADER_USER,
        aws_secret_access_key=settings.MINIO_MODEL_DOWNLOADER_PASSWORD,
    )
    return s3
