from functools import lru_cache
import os
from pydantic_settings import BaseSettings

DEFAULT_DELAY_BETWEEN_RETRIES_IN_SECONDS = 10
DEFAULT_TOKEN_DURATION_IN_MINUTES = 60
DEFAULT_DATA_DIRECTORY = "/app/data"


class Settings(BaseSettings):
    MINIO_SERVICE_NAME: str = os.getenv(
        "MINIO_SERVICE_NAME",
        default="minio",
    )
    MINIO_SERVICE_PORT: str = os.getenv(
        "MINIO_SERVICE_PORT",
        default="9010",
    )
    MINIO_USER: str = os.getenv(
        "MINIO_MLFLOW_USER",
        default="minio-user",
    )
    MINIO_PASSWORD: str = os.getenv(
        "MINIO_MLFLOW_PASSWORD",
        default="minio-password",
    )
    MINIO_RAW_MODEL_BUCKET_NAME: str = os.getenv(
        "MINIO_RAW_MODEL_BUCKET_NAME",
        default="raw-models",
    )
    MLFLOW_TRACKING_URI: str = os.getenv(
        "MLFLOW_TRACKING_URI",
        default="https://127.0.0.1:5000",
    )
    MLFLOW_IMAGE_CLASSIFIER_MODEL_NAME: str = os.getenv(
        "MLFLOW_IMAGE_CLASSIFIER_MODEL_NAME",
        default="image_classifier_model",
    )
    MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_NAME: str = os.getenv(
        "MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_NAME",
        default="f1_score",
    )
    MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_VALUE: float = float(
        (
            float(os.getenv("MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_VALUE"))
            if os.getenv("MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_VALUE")
            else 0.59
        ),
    )
    MLFLOW_IMAGE_CLASSIFIER_EXPERIMENT_NAME: str = os.getenv(
        "MLFLOW_IMAGE_CLASSIFIER_EXPERIMENT_NAME",
        default="Train image processing model",
    )
    MLFLOW_IMAGE_RUN_NAME: str = os.getenv(
        "MLFLOW_IMAGE_RUN_NAME",
        default="initial_run",
    )
    MLFLOW_TEXT_CLASSIFIER_MODEL_NAME: str = os.getenv(
        "MLFLOW_TEXT_CLASSIFIER_MODEL_NAME",
        default="text-classifier",
    )
    MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_NAME: str = os.getenv(
        "MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_NAME",
        default="f1_score",
    )
    MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_VALUE: float = float(
        (
            float(os.getenv("MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_VALUE"))
            if os.getenv("MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_VALUE")
            else 0.81
        ),
    )
    MLFLOW_TEXT_TRANSLATOR_MODEL_NAME: str = os.getenv(
        "MLFLOW_TEXT_TRANSLATOR_MODEL_NAME",
        default="text-translator",
    )
    MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME: str = os.getenv(
        "MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME",
        default="text-language-detector",
    )
    MLFLOW_TEXT_CLASSIFIER_EXPERIMENT_NAME: str = os.getenv(
        "MLFLOW_TEXT_CLASSIFIER_EXPERIMENT_NAME",
        default="Train text processing model",
    )
    MLFLOW_TEXT_RUN_NAME: str = os.getenv(
        "MLFLOW_TEXT_RUN_NAME",
        default="initial_run",
    )
    DELAY_BETWEEN_RETRIES_IN_SECONDS: int = (
        int(os.getenv("MLFLOW_DELAY_BETWEEN_RETRIES_IN_SECONDS"))
        if os.getenv("MLFLOW_DELAY_BETWEEN_RETRIES_IN_SECONDS")
        else DEFAULT_DELAY_BETWEEN_RETRIES_IN_SECONDS
    )
    DATA_DIRECTORY: str = os.getenv(
        "MLFLOW_DATA_DIRECTORY", default=DEFAULT_DATA_DIRECTORY
    )
    IMAGE_MODEL_DATA_DIRECTORY: str = os.getenv(
        "MLFLOW_IMAGE_MODEL_DATA_DIRECTORY", default="image_model"
    )
    TEXT_CLASSIFIER_MODEL_DATA_DIRECTORY: str = os.getenv(
        "MLFLOW_TEXT_CLASSIFIER_MODEL_DATA_DIRECTORY", default="text_classifier_model"
    )
    TEXT_TRANSLATOR_MODEL_DATA_DIRECTORY: str = os.getenv(
        "MLFLOW_TEXT_TRANSLATOR_MODEL_DATA_DIRECTORY", default="text_translator_model"
    )
    TEXT_LANGUAGE_DETECTOR_MODEL_DATA_DIRECTORY: str = os.getenv(
        "MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_DATA_DIRECTORY",
        default="text_language_detector_model",
    )


settings = Settings()


@lru_cache
def get_settings():
    return Settings()
