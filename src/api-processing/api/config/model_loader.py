import logging
from functools import lru_cache
from api.processing.classifier import ImageTextClassifier


@lru_cache
def load_classifier(text_api_url: str, image_api_url: str):
    return ImageTextClassifier(
        text_api_url=text_api_url,
        image_api_url=image_api_url,
    )
