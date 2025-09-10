from functools import lru_cache
from typing import Annotated
from api.config.config import Settings, get_settings
from fastapi import Depends
import mlflow


@lru_cache
def get_classifier_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_TEXT_CLASSIFIER_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_CLASSIFIER_MODEL_VERSION

    mlflow.set_tracking_uri(settings.MLFLOW_ADDR)
    return mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{model_version}")


@lru_cache
def get_translator_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_TEXT_TRANSLATOR_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_TRANSLATOR_MODEL_VERSION

    mlflow.set_tracking_uri(settings.MLFLOW_ADDR)

    mlflow.artifacts.download_artifacts(
        run_id=settings.MLFLOW_TEXT_TRANSLATOR_ARTIFACT_RUN_ID,
        artifact_path=settings.MLFLOW_TEXT_TRANSLATOR_CACHE_ARTIFACT_PATH,
        dst_path=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
    )

    return mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{model_version}")


@lru_cache
def get_language_detector_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_VERSION

    mlflow.set_tracking_uri(settings.MLFLOW_ADDR)

    mlflow.artifacts.download_artifacts(
        run_id=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_ARTIFACT_RUN_ID,
        artifact_path=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH,
        dst_path=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
    )

    return mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{model_version}")
