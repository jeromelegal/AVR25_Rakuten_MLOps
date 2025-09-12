from functools import lru_cache
from typing import Annotated
from api.config.config import Settings, get_settings
from fastapi import Depends
import mlflow


@lru_cache
def get_image_classifier_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_IMAGE_CLASSIFIER_MODEL_NAME
    model_version = settings.MLFLOW_IMAGE_CLASSIFIER_MODEL_VERSION

    mlflow.set_tracking_uri(settings.MLFLOW_ADDR)
    return mlflow.tensorflow.load_model(
        model_uri=f"models:/{model_name}/{model_version}"
    )
