from functools import lru_cache
from typing import Annotated
from api.config.config import Settings, get_settings
from fastapi import Depends
import mlflow

MODEL_NOT_FOUND_EXCEPTION_KEY = "RESOURCE_DOES_NOT_EXIST"


@lru_cache
def load_image_classifier_model(
    model_name: str,
    model_version: str,
    mlflow_addr: str,
):
    mlflow.set_tracking_uri(mlflow_addr)
    return mlflow.tensorflow.load_model(
        model_uri=f"models:/{model_name}/{model_version}"
    )
