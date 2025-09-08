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
    return mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{model_version}")


@lru_cache
def get_language_detector_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFL
    model_version = settings.MLFLOW_TEXT_TRANSLATOR_MODEL_VERSION

    mlflow.set_tracking_uri(settings.MLFLOW_ADDR)
    return mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{model_version}")
