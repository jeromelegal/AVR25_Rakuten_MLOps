from functools import lru_cache
import os
from pydantic_settings import BaseSettings

DEFAULT_TOKEN_DURATION_IN_MINUTES = 60


class Settings(BaseSettings):
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", default="SERVICE_VERSION")
    API_GATEWAY_HOST: str = os.getenv("API_GATEWAY_HOST", default="API_GATEWAY_HOST")
    INTERNAL_ENDPOINT_URL: str = os.getenv(
        "API_MINIO_INTERNAL_ENDPOINT_URL", default="INTERNAL_ENDPOINT_URL"
    )
    PROTECTED_ENDPOINT_URL: str = os.getenv(
        "API_MINIO_PROTECTED_ENDPOINT_URL", default="PROTECTED_ENDPOINT_URL"
    )
    DATABASE_URL: str = os.getenv("API_MINIO_DATABASE_URL", default="DATABASE_URL")
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

    MINIO_API_MINIO_CA_PATH: str = os.getenv(
        "MINIO_API_MINIO_CA_PATH", default="MINIO_API_MINIO_CA_PATH"
    )
    MINIO_API_MINIO_PEM_PATH: str = os.getenv(
        "MINIO_API_MINIO_PEM_PATH", default="MINIO_API_MINIO_PEM_PATH"
    )
    MINIO_SERVICE_PORT: str = os.getenv(
        "MINIO_SERVICE_PORT", default="MINIO_SERVICE_PORT"
    )
    MINIO_SERVICE_NAME: str = os.getenv(
        "MINIO_SERVICE_NAME", default="MINIO_SERVICE_NAME"
    )
    MINIO_USER: str = os.getenv("MINIO_API_MINIO_USER", default="MINIO_USER")
    MINIO_PASSWORD: str = os.getenv(
        "MINIO_API_MINIO_PASSWORD", default="MINIO_PASSWORD"
    )
    MINIO_DATABASE: str = os.getenv(
        "MINIO_API_MINIO_DATABASE", default="MINIO_DATABASE"
    )


settings = Settings()


@lru_cache
def get_settings():
    return Settings()


# SERVICE_VERSION = os.getenv("SERVICE_VERSION")
# API_GATEWAY_HOST = os.getenv("API_GATEWAY_HOST")
# INTERNAL_ENDPOINT_URL = os.getenv("API_MINIO_INTERNAL_ENDPOINT_URL")
# PROTECTED_ENDPOINT_URL = os.getenv("API_MINIO_PROTECTED_ENDPOINT_URL")
# DATABASE_URL = os.getenv("API_MINIO_DATABASE_URL")
# SECRET_KEY = os.getenv("API_MINIO_SECRET_KEY")
# INTERNAL_SECRET_KEY = os.getenv("API_MINIO_INTERNAL_SECRET_KEY")
# ALGORITHM = os.getenv("API_MINIO_ALGORITHM")
# ACCESS_TOKEN_EXPIRE_MINUTES = (
#     int(os.getenv("API_MINIO_ACCESS_TOKEN_EXPIRE_MINUTES"))
#     if os.getenv("API_MINIO_ACCESS_TOKEN_EXPIRE_MINUTES")
#     else DEFAULT_TOKEN_DURATION_IN_MINUTES
# )

# MINIO_API_MINIO_CA_PATH = os.getenv("MINIO_API_MINIO_CA_PATH")
# MINIO_API_MINIO_PEM_PATH = os.getenv("MINIO_API_MINIO_PEM_PATH")

# MINIO_SERVICE_PORT = os.getenv("MINIO_SERVICE_PORT")
# MINIO_SERVICE_NAME = os.getenv("MINIO_SERVICE_NAME")
# MINIO_USER = os.getenv("MINIO_API_MINIO_USER")
# MINIO_PASSWORD = os.getenv("MINIO_API_MINIO_PASSWORD")
# MINIO_DATABASE = os.getenv("MINIO_API_MINIO_DATABASE")
