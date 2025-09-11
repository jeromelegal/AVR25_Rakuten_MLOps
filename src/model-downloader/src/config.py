from functools import lru_cache
import os
from pydantic_settings import BaseSettings

DEFAULT_TOKEN_DURATION_IN_MINUTES = 60


class Settings(BaseSettings):
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", default="SERVICE_VERSION")
    MINIO_MODEL_DOWNLOADER_CA_PATH: str = os.getenv(
        "MINIO_MODEL_DOWNLOADER_CA_PATH", default="MINIO_MODEL_DOWNLOADER_CA_PATH"
    )
    MINIO_MODEL_DOWNLOADER_PEM_PATH: str = os.getenv(
        "MINIO_MODEL_DOWNLOADER_PEM_PATH", default="MINIO_MODEL_DOWNLOADER_PEM_PATH"
    )
    MINIO_SERVICE_PORT: str = os.getenv(
        "MINIO_SERVICE_PORT", default="MINIO_SERVICE_PORT"
    )
    MINIO_SERVICE_NAME: str = os.getenv(
        "MINIO_SERVICE_NAME", default="MINIO_SERVICE_NAME"
    )
    MINIO_MODEL_DOWNLOADER_USER: str = os.getenv(
        "MINIO_MODEL_DOWNLOADER_USER", default="MINIO_MODEL_DOWNLOADER_USER"
    )
    MINIO_MODEL_DOWNLOADER_PASSWORD: str = os.getenv(
        "MINIO_MODEL_DOWNLOADER_PASSWORD", default="MINIO_MODEL_DOWNLOADER_PASSWORD"
    )
    MINIO_MODEL_BUCKET_NAME: str = os.getenv(
        "MINIO_MODEL_BUCKET_NAME", default="MINIO_MODEL_BUCKET_NAME"
    )
    LOCAL_MODEL_DIRECTORY_PATH: str = os.getenv(
        "LOCAL_MODEL_DIRECTORY_PATH", default="LOCAL_MODEL_DIRECTORY_PATH"
    )


settings = Settings()


@lru_cache
def get_settings():
    return Settings()
