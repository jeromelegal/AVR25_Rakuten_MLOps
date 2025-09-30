from typing import Annotated
import logging
from api.config.config import Settings, get_settings
from fastapi import Depends
from api.config.model_loader import load_classifier


def get_classifier(settings: Annotated[Settings, Depends(get_settings)]):
    text_api_url = (
        f"https://{settings.API_TEXT_PROCESSING_SERVICE_NAME}"
        "/api/internal/api-text-processing/predict"
    )
    image_api_url = (
        f"https://{settings.API_IMAGE_PROCESSING_SERVICE_NAME}"
        "/api/internal/api-image-processing/predict"
    )
    try:
        return load_classifier(text_api_url=text_api_url, image_api_url=image_api_url)
    except ValueError as exc:
        error_msg = f"Impossible to load the image classifier model: {exc}"
        logging.error(error_msg)
        load_classifier.cache_clear()
        return None
