import logging
from typing import Annotated
from fastapi import Depends
from api.config.config import Settings, get_settings
from api.config.model_loader import load_image_classifier_model
from mlflow.exceptions import RestException


def get_image_classifier_model(
    settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        return load_image_classifier_model(
            model_name=settings.MLFLOW_IMAGE_CLASSIFIER_MODEL_NAME,
            model_version=settings.MLFLOW_IMAGE_CLASSIFIER_MODEL_VERSION,
            mlflow_addr=settings.MLFLOW_ADDR,
        )
    except RestException as exc:
        error_msg = f"Impossible to load the image classifier model: {exc}"
        logging.error(error_msg)
        load_image_classifier_model.cache_clear()
        return None
