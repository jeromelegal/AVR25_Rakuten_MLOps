from functools import lru_cache
from typing import Annotated
from api.config.config import Settings, get_settings
from api.processing.classifier import ImageTextClassifier
from fastapi import Depends


@lru_cache
def get_classifier(settings: Annotated[Settings, Depends(get_settings)]):
    text_api_url = (
        f"https://{settings.API_TEXT_PROCESSING_SERVICE_NAME}:"
        f"{settings.API_TEXT_PROCESSING_SERVICE_PORT}"
    )
    image_api_url = (
        f"https://{settings.API_IMAGE_PROCESSING_SERVICE_NAME}:"
        f"{settings.API_IMAGE_PROCESSING_SERVICE_PORT}"
    )
    clf = ImageTextClassifier(
        text_api_url=text_api_url,
        image_api_url=image_api_url,
    )
    return clf
