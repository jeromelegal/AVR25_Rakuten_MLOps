from functools import lru_cache
import os
from pydantic_settings import BaseSettings

DEFAULT_TOKEN_DURATION_IN_MINUTES = 60


class Settings(BaseSettings):
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", default="SERVICE_VERSION")
    SECRET_KEY: str = os.getenv("API_MINIO_SECRET_KEY", default="SECRET_KEY")
    INTERNAL_SECRET_KEY: str = os.getenv(
        "API_MINIO_INTERNAL_SECRET_KEY", default="INTERNAL_SECRET_KEY"
    )
    ALGORITHM: str = os.getenv("API_MINIO_ALGORITHM", default="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = (
        int(os.getenv("API_MINIO_ACCESS_TOKEN_EXPIRE_MINUTES"))
        if os.getenv("API_MINIO_ACCESS_TOKEN_EXPIRE_MINUTES")
        else DEFAULT_TOKEN_DURATION_IN_MINUTES
    )

    API_TEXT_PROCESSING_SERVICE_NAME: str = os.getenv(
        "API_TEXT_PROCESSING_SERVICE_NAME", default="API_TEXT_PROCESSING_SERVICE_NAME"
    )
    API_TEXT_PROCESSING_SERVICE_PORT: str = os.getenv(
        "API_TEXT_PROCESSING_SERVICE_PORT", default="API_TEXT_PROCESSING_SERVICE_PORT"
    )
    API_IMAGE_PROCESSING_SERVICE_NAME: str = os.getenv(
        "API_IMAGE_PROCESSING_SERVICE_NAME", default="API_IMAGE_PROCESSING_SERVICE_NAME"
    )
    API_IMAGE_PROCESSING_SERVICE_PORT: str = os.getenv(
        "API_IMAGE_PROCESSING_SERVICE_PORT", default="API_IMAGE_PROCESSING_SERVICE_PORT"
    )


settings = Settings()


@lru_cache
def get_settings():
    return Settings()
